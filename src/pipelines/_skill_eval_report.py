# -*- coding: utf-8 -*-
"""
_skill_eval_report.py — Génération et persistance des rapports d'évaluation des compétences.
Conforme ADR-0202 (<= 300 lignes) et ADR-0369 (Python Senior).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple


def format_summary_markdown(summary: Dict[str, Any]) -> str:
    """Produit le rapport Markdown exécutif avec matrice détaillée et Golden Dataset."""
    lines = [
        "# 🧪 Rapport Exécutif d'Évaluation des Compétences (.agents/skills/*)",
        "",
        f"- **Date de Certification :** {summary.get('certified_at', datetime.now(timezone.utc).isoformat())}",
        f"- **Score Moyen Global :** **{summary.get('average_score', 0.0)} / 100** (Seuil requis : {summary.get('pass_threshold', 80.0)})",
        f"- **Volume Audité :** {summary.get('total_skills', 0)} compétences",
        f"- **Statut :** ✅ {summary.get('passed', 0)} PASS · ⚠️ {summary.get('warning', 0)} WARNING · 🛑 {summary.get('failed', 0)} FAIL",
        "",
        "## 📊 Matrice d'Évaluation Complète",
        "",
        "| Compétence | Statut | Note (/100) | Déclencheur (/25) | Règles (/25) | Ancrage (/25) | Résilience (/25) | Golden (/100) | Lignes |",
        "| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |",
    ]

    for r in summary.get("results", []):
        icon = "✅ PASS" if r["verdict"] == "PASS" else ("⚠️ WARN" if r["verdict"] == "WARNING" else "🛑 FAIL")
        b = r.get("scores_breakdown", {})
        golden_val = b.get("golden_dataset")
        golden_str = f"{golden_val:.1f}" if isinstance(golden_val, (int, float)) else "N/A"
        lines.append(
            f"| `{r['skill_name']}` | {icon} | **{r['total_score']}** | "
            f"{b.get('trigger_clarity', 0.0)} | {b.get('rule_determinism', 0.0)} | "
            f"{b.get('ground_truth_anchoring', 0.0)} | {b.get('resilience_and_confinement', 0.0)} | "
            f"{golden_str} | {r.get('token_stats', {}).get('line_count', 0)} |"
        )

    lines.extend(["", "## 🛑 Défauts Bloquants & Actions Correctives", ""])
    has_issues = False
    for r in summary.get("results", []):
        if r.get("blocking_flaws") or (r.get("verdict") != "PASS" and r.get("recommendations")):
            has_issues = True
            lines.append(f"### `{r['skill_name']}` ({r['verdict']} — {r['total_score']}/100)")
            for flaw in r.get("blocking_flaws", []):
                lines.append(f"- 🛑 **Bloquant** : {flaw}")
            for rec in r.get("recommendations", []):
                lines.append(f"- 💡 **Action** : {rec}")
            lines.append("")

    if not has_issues:
        lines.append("✅ Aucune anomalie bloquante détectée. Toutes les compétences auditées sont conformes.")
        lines.append("")

    return "\n".join(lines)


def persist_reports(
    summary: Dict[str, Any],
    output_dir: Path,
) -> Tuple[Path, Path, Path, Path]:
    """
    Sauvegarde les rapports JSON et Markdown sous format summary et legacy.
    Retourne (summary_json, summary_md, report_json, report_md).
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    if "certified_at" not in summary:
        summary["certified_at"] = datetime.now(timezone.utc).isoformat()

    json_str = json.dumps(summary, indent=2, ensure_ascii=False)
    md_str = format_summary_markdown(summary)

    # 1. Noms SSOT canoniques (ADR-0389)
    summary_json_path = output_dir / "skills_eval_summary.json"
    summary_md_path = output_dir / "skills_eval_summary.md"
    summary_json_path.write_text(json_str, encoding="utf-8")
    summary_md_path.write_text(md_str, encoding="utf-8")

    # 2. Alias de rétrocompatibilité historique
    legacy_json_path = output_dir / "skills_eval_report.json"
    legacy_md_path = output_dir / "skills_eval_report.md"
    legacy_json_path.write_text(json_str, encoding="utf-8")
    legacy_md_path.write_text(md_str, encoding="utf-8")

    return summary_json_path, summary_md_path, legacy_json_path, legacy_md_path
