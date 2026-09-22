"""Collecte d'usage et rendu console Skill Doctor (MLOOP-145-BE — extraction ADR-0202)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from src.cli import ZeroFluffConsole
from src.utils.logger import get_logger

logger = get_logger("pipelines.skill_doctor_report")


class SkillDoctorReportMixin:
    """Statistiques d'usage et rapport console — dépend de self.token_ledger_path / self.events_path / self.individual_threshold."""

    token_ledger_path: Path
    events_path: Path
    individual_threshold: int

    def collect_usage_statistics(self) -> Dict[str, int]:
        """Collecte la fréquence d'utilisation des compétences depuis les journaux récents."""
        usage_counts: Dict[str, int] = {}

        # 1. Analyse du ledger de jetons
        if self.token_ledger_path.exists():
            try:
                for line in self.token_ledger_path.read_text(
                    encoding="utf-8", errors="ignore"
                ).splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                        skill = (
                            entry.get("skill") or entry.get("skill_name") or entry.get("operation")
                        )
                        if skill and isinstance(skill, str):
                            usage_counts[skill] = usage_counts.get(skill, 0) + 1
                    except Exception as e:
                        logger.debug(
                            "Ligne JSONL illisible dans token_ledger, ligne ignorée",
                            exc_info=True,
                            extra={
                                "component": "pipelines.skill_doctor_report",
                                "operation": "collect_usage_statistics",
                                "source": "token_ledger",
                                "error": str(e),
                            },
                        )
                        continue
            except Exception as e:
                logger.warning(
                    "Lecture de token_ledger échouée, statistiques d'usage incomplètes",
                    exc_info=True,
                    extra={
                        "component": "pipelines.skill_doctor_report",
                        "operation": "collect_usage_statistics",
                        "path": str(self.token_ledger_path),
                        "error": str(e),
                    },
                )

        # 2. Analyse des événements
        if self.events_path.exists():
            try:
                for line in self.events_path.read_text(
                    encoding="utf-8", errors="ignore"
                ).splitlines():
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
                    except Exception as e:
                        logger.debug(
                            "Événement JSONL illisible, ligne ignorée",
                            exc_info=True,
                            extra={
                                "component": "pipelines.skill_doctor_report",
                                "operation": "collect_usage_statistics",
                                "source": "events",
                                "error": str(e),
                            },
                        )
                        continue
            except Exception as e:
                logger.warning(
                    "Lecture des événements échouée, statistiques d'usage incomplètes",
                    exc_info=True,
                    extra={
                        "component": "pipelines.skill_doctor_report",
                        "operation": "collect_usage_statistics",
                        "path": str(self.events_path),
                        "error": str(e),
                    },
                )

        return usage_counts

    def render_console_report(self, result: Dict[str, Any]) -> None:
        """Affiche le bilan d'hygiène sous forme de diagnostic clair et sans superflu."""
        if not result.get("success"):
            ZeroFluffConsole.error(f"Échec de l'audit SkillDoctor : {result.get('error')}")
            return

        summary = result["summary"]
        risk = summary["context_rot_risk"]
        risk_icon = "🟢" if risk == "LOW" else ("🟡" if risk == "MEDIUM" else "🔴")

        ZeroFluffConsole.section(
            "🩺 Bilan d'Hygiène Contextuelle & Diagnostic des Compétences (Skill-Doctor)"
        )
        print(f"• Compétences Détectées : {summary['total_skills']}")
        print(f"• Empreinte Totale du Catalogue : ~{summary['total_catalog_tokens']:,} jetons")
        print(
            f"• Poids Descriptions de Démarrage : ~{summary['total_boot_description_tokens']:,} / {summary['boot_budget_max_tokens']:,} jetons ({summary['boot_budget_usage_pct']}%)"
        )
        print(f"• Risque de Context Rot : {risk_icon} [{risk}]")
        print(
            f"• Compétences de Référence (> {self.individual_threshold} tok) : {summary['oversized_skills_count']}"
        )
        print(f"• Collisions Lexicales (> 75%) : {summary.get('collisions_count', 0)}")
        print(f"• Compétences Dormantes (0 appel tracé) : {summary['dormant_skills_count']}")

        if result.get("collisions"):
            collision_str = ", ".join(
                [
                    f"{c['skill_a']} <-> {c['skill_b']} ({int(c['similarity'] * 100)}%)"
                    for c in result["collisions"][:5]
                ]
            )
            ZeroFluffConsole.warning(f"Collisions de routing potentielles : {collision_str}")

        if result.get("oversized_skills"):
            ZeroFluffConsole.info(
                f"Compétences de référence volumineuses : {', '.join(result['oversized_skills'][:10])}"
            )

        if result.get("tombstone_candidates"):
            ZeroFluffConsole.info(
                f"Candidats recommandés au Tombstone (ADR-0348) : {', '.join(result['tombstone_candidates'][:10])}"
            )

        print("\nTop 5 des compétences les plus lourdes :")
        sorted_by_size = sorted(
            result.get("skills", []), key=lambda x: x.get("total_tokens", 0), reverse=True
        )[:5]
        for s in sorted_by_size:
            flags_str = f" [{', '.join(s['flags'])}]" if s.get("flags") else ""
            print(
                f"  - `{s['name']}` : ~{s['total_tokens']:,} jetons (Desc: {s['description_tokens']} tok, Appels: {s.get('invocation_count', 0)}){flags_str}"
            )
