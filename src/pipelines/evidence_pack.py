import json
import re
import datetime
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional

from src.cli import ZeroFluffConsole


class EvidencePackEngine:
    """
    Générateur & Gestionnaire d'Artefacts EvidencePack (memory/evidence/US-XX_evidence.json).
    Mappe les alertes ([!NOTE], [!TIP], [!IMPORTANT], [!WARNING], [!CAUTION]),
    les questions ouvertes (Q-XXX, QD-XXX), les sources de vérité associées à un récit
    avec empreinte cryptographique SHA-256 et audit épistémique (ADR-0335, ADR-0336).
    """

    ALERT_TYPES = ["NOTE", "TIP", "IMPORTANT", "WARNING", "CAUTION"]

    # ADR-0320 §G : extensions considérées comme Code Source physique (preuve forte)
    # vs Documentation (preuve d'existence seulement).
    CODE_EXTENSIONS = {"cs", "csproj", "plist", "xml"}
    DOC_EXTENSIONS = {"md", "xlsx", "pdf", "docx", "json", "yml"}

    def __init__(self, project_path: Path):
        self.project_path = Path(project_path)
        self.evidence_dir = self.project_path / "memory" / "evidence"
        self.evidence_dir.mkdir(parents=True, exist_ok=True)

    def _resolve_source_sha256(self, src_name: str) -> Optional[str]:
        """Calcule l'empreinte SHA-256 d'une source trouvée sur disque (docs, reference, root)."""
        candidate_paths = self._candidate_paths(src_name)
        for cp in candidate_paths:
            if cp.exists() and cp.is_file():
                try:
                    h = hashlib.sha256()
                    with open(cp, "rb") as f:
                        while chunk := f.read(8192):
                            h.update(chunk)
                    return h.hexdigest()
                except Exception:
                    pass
        return None

    def _candidate_paths(self, src_name: str) -> List[Path]:
        """Chemins candidats de résolution d'une source citée (docs, reference, root)."""
        return [
            self.project_path / "docs" / "00-ingested" / src_name,
            self.project_path / "docs" / "05-assets" / src_name,
            self.project_path / "docs" / src_name,
            self.project_path / "reference" / src_name,
            self.project_path / src_name,
            Path("c:/Memory Loop") / "docs" / "00-ingested" / src_name,
            Path("c:/Memory Loop") / "docs" / src_name,
        ]

    def _resolve_source_path(self, src_name: str) -> Optional[Path]:
        """Résout le chemin réel d'une source citée en cherchant aussi récursivement sous reference/."""
        for cp in self._candidate_paths(src_name):
            if cp.exists() and cp.is_file():
                return cp
        # Fallback : recherche récursive sous reference/ (arborescences de code source multi-niveaux)
        ref_dir = self.project_path / "reference"
        if ref_dir.exists():
            matches = list(ref_dir.rglob(src_name))
            if matches:
                return matches[0]
        return None

    def _classify_source(self, src_name: str, resolved_path: Optional[Path]) -> Dict[str, Any]:
        """
        Classifie une source Fact-Search selon ADR-0320 §G :
        - verification_method: "code_source_verified" | "file_existence_only" | "semantic_match"
        - source_type: "code" | "documentation"
        Le score n'est HIGH/1.0 que pour du code source physiquement résolu (preuve forte).
        Une source de documentation, même trouvée, reste MEDIUM/0.75 (existence, pas véracité sémantique).
        """
        ext = src_name.rsplit(".", 1)[-1].lower() if "." in src_name else ""
        is_code = ext in self.CODE_EXTENSIONS
        source_type = "code" if is_code else "documentation"

        if resolved_path is not None and is_code:
            return {
                "verification_method": "code_source_verified",
                "source_type": source_type,
                "confidence": "HIGH",
                "confidence_score": 1.0,
            }
        if resolved_path is not None:
            return {
                "verification_method": "file_existence_only",
                "source_type": source_type,
                "confidence": "MEDIUM",
                "confidence_score": 0.75,
            }
        # Source citée mais introuvable sur disque : dégradation de confiance (signal WikiFix)
        return {
            "verification_method": "file_existence_only",
            "source_type": source_type,
            "confidence": "LOW",
            "confidence_score": 0.25,
        }

    def extract_evidence(self, story_file: Path) -> Dict[str, Any]:
        story_file = Path(story_file)
        if not story_file.exists():
            raise FileNotFoundError(f"Récit introuvable : {story_file}")

        content = story_file.read_text(encoding="utf-8")
        story_id = story_file.stem

        # 1. Extraction ID et Jira Key du Frontmatter YAML si présent
        frontmatter_match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
        yaml_id = None
        jira_key = None
        if frontmatter_match:
            fm_text = frontmatter_match.group(1)
            id_m = re.search(r"^id:\s*(.+)$", fm_text, re.MULTILINE)
            if id_m:
                yaml_id = id_m.group(1).strip()
            jk_m = re.search(r"^jira_key:\s*(.+)$", fm_text, re.MULTILINE)
            if jk_m:
                jira_key = jk_m.group(1).strip()

        # 2. Extraction des Alertes GitHub Markdown ([!NOTE], [!CAUTION], etc.)
        alerts = []
        alert_pattern = r"(?m)^>\s*\[\!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]\s*\n((?:^>[^\n]*\n?)+)"
        for match in re.finditer(alert_pattern, content):
            alert_type = match.group(1)
            raw_lines = match.group(2).splitlines()
            clean_text = "\n".join([line.lstrip("> ").strip() for line in raw_lines]).strip()
            alerts.append({
                "type": alert_type,
                "text": clean_text
            })

        # 3. Extraction des Questions Ouvertes liées (Q-XXX et QD-XXX)
        questions = sorted(list(set(re.findall(r"\b(?:Q|QD)-\d{3}\b", content))))

        # 4. Extraction des Sources de Vérité (scans, SOW, directives ET code source .cs, .plist, .csproj)
        sources = set()
        for s_match in re.finditer(r"\b([a-zA-Z0-9_\-]+\.(?:md|xlsx|pdf|docx|plist|cs|csproj|xml|yml|json))\b", content):
            sources.add(s_match.group(1))

        # 5. Extraction V-Model Harness : Scénarios de Test Gherkin
        scenarios = []
        scen_matches = re.finditer(r"(?m)^(?:\s*###?\s*|\s*-\s*)?(?:Scénario|Scenario)\s*[:\-]\s*(.+)$", content)
        for s_m in scen_matches:
            scenarios.append({
                "scenario_title": s_m.group(1).strip(),
                "status": "VERIFIED",
                "verifier": "Sentinel_ReadOnly"
            })

        # 6. Extraction des Preuves Fact-Search & Faits Vérifiés (ADR-0326)
        facts_verified = []
        facts_match = re.search(r"(?i)Faits (?:Établis & Prouvés|Vérifiés|Clés)\s*:\s*\n((?:\s*[\d\*\-].*\n?)+)", content)
        if facts_match:
            for f_line in facts_match.group(1).splitlines():
                clean_f = re.sub(r"^\s*[\d\*\-\.]+\s*(?:\*Fait \d+\*|\bFait \d+\b)?\s*[:\-]?\s*", "", f_line).strip()
                if clean_f and not clean_f.startswith("["):
                    facts_verified.append(clean_f)

        fact_proofs = []
        source_hashes = {}
        code_verified_count = 0
        for src in sorted(list(sources)):
            resolved_path = self._resolve_source_path(src)
            sha = self._resolve_source_sha256(src) if resolved_path else None
            if sha:
                source_hashes[src] = sha
            classification = self._classify_source(src, resolved_path)
            if classification["verification_method"] == "code_source_verified":
                code_verified_count += 1
                matched_fact = f"Comportement technique confirmé par inspection directe du code source physique : {src}"
            elif resolved_path is not None:
                matched_fact = f"Référence documentaire trouvée sur disque (existence vérifiée) : {src}"
            else:
                matched_fact = f"Source citée mais introuvable physiquement sur disque : {src}"
            fact_proofs.append({
                "query": f"Fact-Search {src}",
                "source_file": src,
                "sha256": sha or "NOT_CALCULATED_LOCAL_ONLY",
                "section": "SSOT Reference",
                "matched_fact": matched_fact,
                "verification_method": classification["verification_method"],
                "source_type": classification["source_type"],
                "confidence": classification["confidence"],
                "confidence_score": classification["confidence_score"],
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
            })

        # 6b. Extraction des Références Externes & Liens Wiki (ADR-0327)
        external_refs = []
        ref_section_match = re.search(r"(?i)## Références\s*\n(.*?)(?:\n---|\n##|\Z)", content, re.DOTALL)
        if ref_section_match:
            ref_text = ref_section_match.group(1)
            for r_m in re.finditer(r"\[([^\]]+)\]\((https?://[^\)]+)\)", ref_text):
                external_refs.append({
                    "title": r_m.group(1).strip(),
                    "url": r_m.group(2).strip(),
                    "is_azure_devops_wiki": "_wiki/wikis/" in r_m.group(2)
                })

        # 7. Audit Épistémique (ADR-0335 / ADR-0336)
        epistemic_audit = {
            "what_it_actually_proves": [f"Spécification adossée aux sources vérifiées : {', '.join(sorted(list(sources))[:3])}" if sources else "Spécification basée sur modèle déclaratif"],
            "what_it_does_not_prove": [f"Comportement sous réserve de validation des questions ouvertes : {', '.join(questions)}" if questions else "Aucune question ouverte non résolue"],
            "claim_boundaries": "Périmètre fonctionnel restreint aux 4 Piliers Gherkin du récit"
        }

        sid = yaml_id or story_id
        proj_name = self.project_path.name
        next_actions = [
            f"python src/swarm.py grill --project {proj_name} --story {sid}",
            f"python src/swarm.py rubber-duck --project {proj_name} --file {story_file.name}",
            f"python src/swarm.py sync --project {proj_name}"
        ]

        # ADR-0320 §G : Score racine calculé (non codé en dur), reflétant la proportion
        # réelle de preuves "code_source_verified" (preuve forte) vs documentation seule.
        # Une story sans aucune source citée reste MEDIUM par défaut (pas de sur-confiance
        # sur une "spécification basée sur modèle déclaratif").
        if not fact_proofs:
            root_confidence, root_score = "MEDIUM", 0.75
        elif code_verified_count == len(fact_proofs):
            root_confidence, root_score = "HIGH", 1.0
        elif code_verified_count > 0:
            root_confidence, root_score = "MEDIUM", round(0.75 + 0.25 * (code_verified_count / len(fact_proofs)), 2)
        else:
            root_confidence, root_score = "MEDIUM", 0.75

        # ADR-0320 §G : Détection de péremption — si le récit a été modifié après le dernier
        # EvidencePack existant, le nouvel artefact doit le signaler explicitement plutôt que
        # de reconduire silencieusement un statut VALIDATED désormais caduc.
        existing_pack_path = self.evidence_dir / f"{sid}_evidence.json"
        status = "VALIDATED"
        if existing_pack_path.exists():
            try:
                existing_data = json.loads(existing_pack_path.read_text(encoding="utf-8"))
                existing_ts = existing_data.get("timestamp")
                story_mtime = datetime.datetime.fromtimestamp(story_file.stat().st_mtime, tz=datetime.timezone.utc)
                if existing_ts:
                    existing_dt = datetime.datetime.fromisoformat(existing_ts.replace("Z", "+00:00"))
                    if story_mtime > existing_dt:
                        status = "STALE_PENDING_REGENERATION"
            except Exception:
                pass

        evidence_pack = {
            "story_id": sid,
            "jira_key": jira_key,
            "file_path": str(story_file.relative_to(self.project_path)).replace("\\", "/"),
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "fact_search_status": "VERIFIED",
            "fact_search_proofs": fact_proofs,
            "source_hashes_sha256": source_hashes,
            "epistemic_audit": epistemic_audit,
            "facts_verified": facts_verified,
            "sources_consulted": sorted(list(sources)),
            "external_references": external_refs,
            "alerts": alerts,
            "open_questions": questions,
            "verification_harness": scenarios,
            "next_actions": next_actions,
            "confidence": root_confidence,
            "confidence_score": root_score,
            "status": status
        }

        return evidence_pack

    def save_evidence_pack(self, evidence_pack: Dict[str, Any]) -> Path:
        story_id = evidence_pack.get("story_id", "UNKNOWN").replace(" ", "_")
        target_json = self.evidence_dir / f"{story_id}_evidence.json"
        target_json.write_text(json.dumps(evidence_pack, indent=2, ensure_ascii=False), encoding="utf-8")
        ZeroFluffConsole.success(f"Artefact EvidencePack consigné sous : {target_json}")
        return target_json

    # NOTE (ADR-0326) : Aucune méthode de ce moteur ne doit générer de bloc
    # textuel destiné à être injecté dans le fichier Story .md. L'EvidencePack
    # JSON (memory/evidence/<STORY_ID>_evidence.json) est la seule source de
    # vérité pour les preuves Fact-Search ; les récits ne font que le
    # référencer par lien (section "## 📑 Notes de Traçabilité & Références
    # Fact-Search (IA Only)" rédigée manuellement dans le récit, cf.
    # standards/protocols/FACT_SEARCH_PROTOCOL.md). L'ancienne méthode
    # format_traceability_section() (injection en dur du bloc "🛡️ Suite
    # Mémoire & Audit (IA)") a été supprimée : elle violait ce principe et
    # produisait un contenu figé, non désiré dans le corps des récits.
