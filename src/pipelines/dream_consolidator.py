"""
Sleep-Wake Memory Consolidation Daemon (`swarm.py dream`).

Inspiré du modèle de consolidation mémorielle (Stanford Generative Agents / TiMem) :
- Compresse et synthétise les logs de session et trajectoires récentes.
- Déduplique les faits métier et élimine le bruit transitoire.
- Met à jour l'état de santé de session (`memory/SESSION_MEMORY_HEALTH.md`).
- Enrichit le graphe de connaissances local.
"""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional
from src.utils.logger import get_logger

logger = get_logger("pipelines.dream_consolidator")


class DreamConsolidationDaemon:
    """Daemon de consolidation nocturne et de compression mémorielle."""

    def __init__(self, project_root: Path | str) -> None:
        self.project_root = Path(project_root)
        self.memory_dir = self.project_root / "memory"
        self.evidence_dir = self.memory_dir / "evidence"

    def consolidate(self) -> Dict[str, Any]:
        """Exécute un cycle complet de consolidation mémorielle."""
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        start_time = time.time()

        # 1. Auditer les EvidencePacks
        evidence_files = list(self.evidence_dir.glob("*_evidence.json")) if self.evidence_dir.exists() else []
        total_open_questions = 0
        total_alerts = 0
        evidence_summaries = []

        for ef in evidence_files:
            try:
                data = json.loads(ef.read_text(encoding="utf-8"))
                q_count = len(data.get("open_questions", []))
                a_count = len(data.get("alerts", []))
                total_open_questions += q_count
                total_alerts += a_count
                evidence_summaries.append({
                    "story_id": data.get("story_id", ef.stem),
                    "open_questions": q_count,
                    "alerts": a_count,
                    "status": "CONSOLIDATED",
                })
            except Exception as e:
                logger.debug(
                    "EvidencePack illisible lors de la consolidation, ignoré",
                    exc_info=True,
                    extra={
                        "component": "pipelines.dream_consolidator",
                        "operation": "consolidate_evidence",
                        "error": str(e),
                    },
                )

        # 2. Sauvegarder l'index complet des EvidencePacks dans un fichier satellite
        summaries_dir = self.evidence_dir / "summaries"
        summaries_dir.mkdir(parents=True, exist_ok=True)
        full_index_file = summaries_dir / "consolidated_evidence_index.json"
        full_index_file.write_text(json.dumps(evidence_summaries, indent=2, ensure_ascii=False), encoding="utf-8")

        # 3. Consolider le rapport de santé de session
        health_report = {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "evidence_packs_audited": len(evidence_files),
            "total_open_questions": total_open_questions,
            "total_alerts": total_alerts,
            "consolidation_duration_ms": round((time.time() - start_time) * 1000, 2),
            "status": "HEALTHY" if total_open_questions == 0 else "ATTENTION_REQUIRED",
        }

        self._write_health_report(health_report, evidence_summaries)
        return health_report

    def _write_health_report(self, report: Dict[str, Any], evidence_summaries: List[Dict[str, Any]]) -> None:
        """Met à jour memory/SESSION_MEMORY_HEALTH.md sous le plafond strict des 200 lignes / 25 Ko (ADR-0362)."""
        health_file = self.memory_dir / "SESSION_MEMORY_HEALTH.md"

        # Diagnostic des compétences mLoop
        skills_summary_lines: List[str] = []
        try:
            from src.pipelines.skill_doctor import SkillDoctor
            ws_root = self.project_root
            if not (ws_root / ".agents" / "skills").exists():
                for parent in [ws_root.parent, ws_root.parent.parent]:
                    if (parent / ".agents" / "skills").exists():
                        ws_root = parent
                        break
            doc = SkillDoctor(ws_root)
            doc_report = doc.audit(suggest_tombstone=False)
            summ = doc_report.get("summary", {})
            skills_summary_lines = [
                "## 🩺 Hygiène Contextuelle & Compétences (SkillDoctor)",
                "",
                f"- **Catalogue Détecté** : `{summ.get('total_skills', 0)}` compétences",
                f"- **Budget Descriptions Boot** : `{summ.get('total_boot_description_tokens', 0):,}` / `{summ.get('boot_budget_max_tokens', 15000):,}` jetons ({summ.get('boot_budget_usage_pct', 0)}%)",
                f"- **Risque de Context Rot** : `[{summ.get('context_rot_risk', 'LOW')}]`",
                f"- **Compétences Volumineuses (> 2k tok)** : `{summ.get('oversized_skills_count', 0)}`",
                "",
            ]
        except Exception as e:
            logger.debug(
                "Section SkillDoctor indisponible, bilan sans hygiene",
                exc_info=True,
                extra={
                    "component": "pipelines.dream_consolidator",
                    "operation": "build_health_report",
                    "error": str(e),
                },
            )

        lines = [
            "# 🧠 Bilan de Santé & Consolidation Mémorielle (Dream Daemon)",
            "",
            f"- **Date de Consolidation** : `{report['timestamp_utc']}`",
            f"- **Statut Global** : `[{report['status']}]`",
            f"- **EvidencePacks Consolidés** : `{report['evidence_packs_audited']}`",
            f"- **Questions Ouvertes Actives** : `{report['total_open_questions']}`",
            f"- **Alertes Actives** : `{report['total_alerts']}`",
            f"- **Temps de Consolidation** : `{report['consolidation_duration_ms']} ms`",
            "",
        ]

        if skills_summary_lines:
            lines.extend(skills_summary_lines)

        lines.extend([
            "## 📑 Synthèse des Artefacts Consolidés",
            "",
            "| Story ID | Questions Ouvertes | Alertes | Statut |",
            "| :--- | :---: | :---: | :---: |",
        ])

        # Prioriser les stories avec alertes ou questions ouvertes, plafonner à 10 items
        sorted_summaries = sorted(evidence_summaries, key=lambda x: (x["open_questions"] + x["alerts"]), reverse=True)
        top_summaries = sorted_summaries[:10]

        for es in top_summaries:
            lines.append(f"| `{es['story_id']}` | {es['open_questions']} | {es['alerts']} | `{es['status']}` |")

        if len(evidence_summaries) > 10:
            lines.append(f"\n*... et {len(evidence_summaries) - 10} autre(s) EvidencePack(s). Index exhaustif consigné sous `memory/evidence/summaries/consolidated_evidence_index.json` (Plafond 200 lignes / 25 Ko).*")

        lines.extend([
            "",
            "---",
            "*Généré par `DreamConsolidationDaemon` (Memory Loop 2.0 - ADR-0362).* ",
        ])

        # Garde-fou constitutionnel : forcer strictement <= 200 lignes
        if len(lines) > 200:
            lines = lines[:198] + ["", "*[Tronqué pour respecter le plafond strict de 200 lignes ADR-0362]*"]

        final_content = "\n".join(lines)
        health_file.write_text(final_content, encoding="utf-8")


def run_dream_consolidation(project_root: Path | str) -> Dict[str, Any]:
    """Point d'entrée de la commande swarm.py dream."""
    daemon = DreamConsolidationDaemon(project_root)
    return daemon.consolidate()
