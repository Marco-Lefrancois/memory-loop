"""
Skill Doctor Pipeline — Moteur Déterministe d'Hygiène Contextuelle & Anti-Context Rot.

Inspiré du /skill-doctor de Claude Code (v2.1.261) et du framework WikiSkill (ADR-0348) :
- Audite les manifestes .agents/skills/*/SKILL.md de l'écosystème mLoop.
- Mesure le poids en jetons (Frontmatter, Description de démarrage, Corps).
- Contrôle le budget global des descriptions de démarrage (seuil de vigilance 15 000 jetons).
- Croise l'activité avec les journaux de session (token_ledger.jsonl, events.jsonl) pour détecter les compétences dormantes.
- Évalue le score de risque de « Context Rot » et propose le passage en TOMBSTONE des règles et compétences obsolètes.
"""
from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Dict, List, Any, Optional

from src.cli import ZeroFluffConsole


class SkillDoctor:
    """Moteur déterministe de diagnostic d'hygiène mémorielle et de coût en jetons des compétences."""

    def __init__(
        self,
        workspace_root: Path | str,
        individual_threshold: int = 2000,
        description_budget_threshold: int = 15000,
    ) -> None:
        self.workspace_root = Path(workspace_root)
        self.skills_dir = self.workspace_root / ".agents" / "skills"
        self.memory_dir = self.workspace_root / "memory"
        self.token_ledger_path = self.memory_dir / "token_ledger.jsonl"
        self.events_path = self.memory_dir / "events.jsonl"
        self.individual_threshold = individual_threshold
        self.description_budget_threshold = description_budget_threshold

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """
        Estime avec précision le nombre de jetons d'une chaîne de texte.
        Utilise tiktoken si présent, sinon une formule heuristique pondérée pour Markdown bilingue (~3.7 car/token).
        """
        if not text or not text.strip():
            return 0
        try:
            import tiktoken  # type: ignore
            enc = tiktoken.get_encoding("cl100k_base")
            return len(enc.encode(text))
        except Exception:
            # Heuristique robuste : 1 token pour ~3.7 caractères en Markdown/code mixte
            cleaned = text.strip()
            return max(1, int(len(cleaned) / 3.7))

    @staticmethod
    def compute_lexical_similarity(text1: str, text2: str) -> float:
        """Calcule la similarité cosinus lexicale entre deux descriptions de compétences (sac de mots normalisé)."""
        words1 = re.findall(r"\b[a-zA-Z0-9_\-]{3,}\b", text1.lower())
        words2 = re.findall(r"\b[a-zA-Z0-9_\-]{3,}\b", text2.lower())
        if not words1 or not words2:
            return 0.0

        freq1: Dict[str, int] = {}
        for w in words1:
            freq1[w] = freq1.get(w, 0) + 1

        freq2: Dict[str, int] = {}
        for w in words2:
            freq2[w] = freq2.get(w, 0) + 1

        common_words = set(freq1.keys()) & set(freq2.keys())
        dot_product = sum(freq1[w] * freq2[w] for w in common_words)

        norm1 = math.sqrt(sum(v * v for v in freq1.values()))
        norm2 = math.sqrt(sum(v * v for v in freq2.values()))

        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot_product / (norm1 * norm2)

    def parse_skill_manifest(self, skill_file: Path) -> Dict[str, Any]:
        """Parse le fichier SKILL.md et extrait les sections avec leurs jetons respectifs."""
        try:
            content = skill_file.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            return {
                "name": skill_file.parent.name,
                "error": f"Erreur de lecture : {e}",
                "valid": False,
                "total_tokens": 0,
            }

        frontmatter_raw = ""
        body_raw = content
        metadata: Dict[str, Any] = {}

        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                frontmatter_raw = parts[1].strip()
                body_raw = parts[2].strip()
                for line in frontmatter_raw.splitlines():
                    line = line.strip()
                    if ":" in line and not line.startswith("#"):
                        k, v = line.split(":", 1)
                        metadata[k.strip()] = v.strip().strip('"\'')

        name = metadata.get("name", skill_file.parent.name)
        description = metadata.get("description", "")
        disable_model_invocation = metadata.get("disable-model-invocation", "false").lower() == "true"

        desc_tokens = self.estimate_tokens(description)
        frontmatter_tokens = self.estimate_tokens(frontmatter_raw)
        body_tokens = self.estimate_tokens(body_raw)
        total_tokens = self.estimate_tokens(content)

        return {
            "name": name,
            "dir_name": skill_file.parent.name,
            "file_path": str(skill_file.relative_to(self.workspace_root) if skill_file.is_relative_to(self.workspace_root) else skill_file),
            "description": description,
            "disable_model_invocation": disable_model_invocation,
            "description_tokens": desc_tokens,
            "frontmatter_tokens": frontmatter_tokens,
            "body_tokens": body_tokens,
            "total_tokens": total_tokens,
            "valid": True,
        }

    def collect_usage_statistics(self) -> Dict[str, int]:
        """Collecte la fréquence d'utilisation des compétences depuis les journaux récents."""
        usage_counts: Dict[str, int] = {}

        # 1. Analyse du ledger de jetons
        if self.token_ledger_path.exists():
            try:
                for line in self.token_ledger_path.read_text(encoding="utf-8", errors="ignore").splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                        skill = entry.get("skill") or entry.get("skill_name") or entry.get("operation")
                        if skill and isinstance(skill, str):
                            usage_counts[skill] = usage_counts.get(skill, 0) + 1
                    except Exception:
                        continue
            except Exception:
                pass

        # 2. Analyse des événements
        if self.events_path.exists():
            try:
                for line in self.events_path.read_text(encoding="utf-8", errors="ignore").splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        event = json.loads(line)
                        payload = event.get("payload", {})
                        action = event.get("event", "") or payload.get("action", "")
                        for s_name in usage_counts:
                            if s_name in action:
                                usage_counts[s_name] = usage_counts.get(s_name, 0) + 1
                    except Exception:
                        continue
            except Exception:
                pass

        return usage_counts

    def audit(self, suggest_tombstone: bool = True) -> Dict[str, Any]:
        """Exécute un audit complet d'hygiène sur le catalogue de compétences."""
        if not self.skills_dir.exists():
            return {
                "success": False,
                "error": f"Répertoire des compétences introuvable : {self.skills_dir}",
                "skills": [],
                "summary": {},
            }

        skill_files = list(self.skills_dir.glob("*/SKILL.md"))
        skills_report: List[Dict[str, Any]] = []
        usage_stats = self.collect_usage_statistics()

        total_catalog_tokens = 0
        total_boot_description_tokens = 0
        oversized_skills: List[str] = []
        dormant_skills: List[str] = []
        tombstone_candidates: List[str] = []

        for sf in sorted(skill_files, key=lambda p: p.parent.name):
            parsed = self.parse_skill_manifest(sf)
            if not parsed.get("valid"):
                continue

            name = parsed["name"]
            total_tokens = parsed["total_tokens"]
            desc_tokens = parsed["description_tokens"]
            is_disabled_auto = parsed["disable_model_invocation"]

            total_catalog_tokens += total_tokens
            # Les descriptions entrent dans le contexte de démarrage uniquement si disable-model-invocation est faux
            if not is_disabled_auto:
                total_boot_description_tokens += desc_tokens

            invocations = usage_stats.get(name, 0) + usage_stats.get(parsed["dir_name"], 0)
            parsed["invocation_count"] = invocations

            flags: List[str] = []
            if total_tokens > self.individual_threshold:
                flags.append(f"OVERSIZED ({total_tokens} > {self.individual_threshold} tok)")
                oversized_skills.append(name)

            if desc_tokens > 200:
                flags.append(f"LONG_DESC ({desc_tokens} tok)")

            if invocations == 0:
                flags.append("DORMANT (0 invocation recensée)")
                dormant_skills.append(name)

            if not parsed["description"]:
                flags.append("MISSING_DESCRIPTION")
            elif not is_disabled_auto and "use when" not in parsed["description"].lower():
                flags.append("MISSING_TRIGGER ('Use when...')")

            # Candidat au tombstone si dormant ET volumineux ou redondant
            if suggest_tombstone and invocations == 0 and (total_tokens > self.individual_threshold or "thinking-" in name):
                tombstone_candidates.append(name)

            parsed["flags"] = flags
            skills_report.append(parsed)

        # Détection des collisions lexicales de routing (> 75% similarité cosinus - ADR-0365)
        collisions: List[Dict[str, Any]] = []
        active_skills = [s for s in skills_report if not s["disable_model_invocation"] and s["description"]]
        for i in range(len(active_skills)):
            for j in range(i + 1, len(active_skills)):
                s1 = active_skills[i]
                s2 = active_skills[j]
                sim = self.compute_lexical_similarity(s1["description"], s2["description"])
                if sim >= 0.75:
                    collisions.append({
                        "skill_a": s1["name"],
                        "skill_b": s2["name"],
                        "similarity": round(sim, 2),
                    })

        # Calcul du score de risque de Context Rot (ADR-0362 & ADR-0365)
        # La fenêtre d'attention au démarrage est directement impactée par le budget des descriptions injectées
        context_rot_risk = "LOW"
        if total_boot_description_tokens > self.description_budget_threshold:
            context_rot_risk = "HIGH"
        elif total_boot_description_tokens > (self.description_budget_threshold * 0.7) or len(collisions) >= 3:
            context_rot_risk = "MEDIUM"

        summary = {
            "total_skills": len(skills_report),
            "total_catalog_tokens": total_catalog_tokens,
            "total_boot_description_tokens": total_boot_description_tokens,
            "boot_budget_max_tokens": self.description_budget_threshold,
            "boot_budget_usage_pct": round((total_boot_description_tokens / max(1, self.description_budget_threshold)) * 100, 1),
            "oversized_skills_count": len(oversized_skills),
            "dormant_skills_count": len(dormant_skills),
            "tombstone_candidates_count": len(tombstone_candidates),
            "collisions_count": len(collisions),
            "context_rot_risk": context_rot_risk,
        }

        return {
            "success": True,
            "summary": summary,
            "oversized_skills": oversized_skills,
            "dormant_skills": dormant_skills,
            "tombstone_candidates": tombstone_candidates,
            "collisions": collisions,
            "skills": skills_report,
        }

    def render_console_report(self, result: Dict[str, Any]) -> None:
        """Affiche le bilan d'hygiène sous forme de diagnostic clair et sans superflu."""
        if not result.get("success"):
            ZeroFluffConsole.error(f"Échec de l'audit SkillDoctor : {result.get('error')}")
            return

        summary = result["summary"]
        risk = summary["context_rot_risk"]
        risk_icon = "🟢" if risk == "LOW" else ("🟡" if risk == "MEDIUM" else "🔴")

        ZeroFluffConsole.section("🩺 Bilan d'Hygiène Contextuelle & Diagnostic des Compétences (Skill-Doctor)")
        print(f"• Compétences Détectées : {summary['total_skills']}")
        print(f"• Empreinte Totale du Catalogue : ~{summary['total_catalog_tokens']:,} jetons")
        print(f"• Poids Descriptions de Démarrage : ~{summary['total_boot_description_tokens']:,} / {summary['boot_budget_max_tokens']:,} jetons ({summary['boot_budget_usage_pct']}%)")
        print(f"• Risque de Context Rot : {risk_icon} [{risk}]")
        print(f"• Compétences de Référence (> {self.individual_threshold} tok) : {summary['oversized_skills_count']}")
        print(f"• Collisions Lexicales (> 75%) : {summary.get('collisions_count', 0)}")
        print(f"• Compétences Dormantes (0 appel tracé) : {summary['dormant_skills_count']}")

        if result.get("collisions"):
            collision_str = ", ".join([f"{c['skill_a']} <-> {c['skill_b']} ({int(c['similarity']*100)}%)" for c in result["collisions"][:5]])
            ZeroFluffConsole.warning(f"Collisions de routing potentielles : {collision_str}")

        if result.get("oversized_skills"):
            ZeroFluffConsole.info(f"Compétences de référence volumineuses : {', '.join(result['oversized_skills'][:10])}")

        if result.get("tombstone_candidates"):
            ZeroFluffConsole.info(f"Candidats recommandés au Tombstone (ADR-0348) : {', '.join(result['tombstone_candidates'][:10])}")

        print("\nTop 5 des compétences les plus lourdes :")
        sorted_by_size = sorted(result.get("skills", []), key=lambda x: x.get("total_tokens", 0), reverse=True)[:5]
        for s in sorted_by_size:
            flags_str = f" [{', '.join(s['flags'])}]" if s.get("flags") else ""
            print(f"  - `{s['name']}` : ~{s['total_tokens']:,} jetons (Desc: {s['description_tokens']} tok, Appels: {s.get('invocation_count', 0)}){flags_str}")


def run_skill_doctor(
    workspace_root: Path | str,
    threshold: int = 2000,
    suggest_tombstone: bool = True,
    output_json: bool = False,
) -> Dict[str, Any]:
    """Point d'entrée principal pour la commande CLI swarm.py doctor --skills."""
    doctor = SkillDoctor(workspace_root=workspace_root, individual_threshold=threshold)
    report = doctor.audit(suggest_tombstone=suggest_tombstone)

    if output_json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        doctor.render_console_report(report)

    return report
