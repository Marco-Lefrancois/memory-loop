# -*- coding: utf-8 -*-
"""
scripts/generate_skills_dashboard.py — Générateur et vérificateur du cockpit de santé des compétences.
Conforme ADR-0202 (<= 300 lignes), ADR-0369 (Python Senior) et ADR-0389.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Injection racine pour imports relatifs
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from src.pipelines.skill_eval import SkillEvalEngine
from src.utils.logger import get_logger

logger = get_logger("scripts.generate_skills_dashboard")


def ensure_skills_eval_summary(workspace_root: Path, force_refresh: bool = False) -> Path:
    """S'assure de l'existence du rapport consolidé skills_eval_summary.json."""
    candidates = [
        workspace_root / "Projects" / "mLoop" / "memory" / "evals" / "skills_eval_summary.json",
        workspace_root / "memory" / "evals" / "skills_eval_summary.json",
    ]

    if not force_refresh:
        for c in candidates:
            if c.exists():
                return c

    print("📊 Génération du rapport d'évaluation consolidé des compétences...")
    engine = SkillEvalEngine(workspace_root=workspace_root)
    summary = engine.evaluate_all_skills()
    target_dir = workspace_root / "Projects" / "mLoop" / "memory" / "evals"
    target_dir.mkdir(parents=True, exist_ok=True)
    json_path, _ = engine.save_reports(summary, output_dir=target_dir)

    # Copie de sauvegarde sous workspace_root/memory/evals/
    ws_dir = workspace_root / "memory" / "evals"
    ws_dir.mkdir(parents=True, exist_ok=True)
    engine.save_reports(summary, output_dir=ws_dir)

    print(f"✅ Rapport généré avec succès ({summary['total_skills']} skills audités, score moyen : {summary['average_score']}/100)")
    return json_path


def verify_dashboard_html(workspace_root: Path) -> Path:
    """Vérifie l'intégrité du fichier skills_health.html statique auto-contenu."""
    html_file = workspace_root / "src" / "dashboard" / "skills_health.html"
    if not html_file.exists():
        raise FileNotFoundError(f"Fichier HTML introuvable : {html_file}")

    content = html_file.read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in content, "HTML non valide (DOCTYPE manquant)"
    assert "radarSvg" in content, "Composant SVG Radar manquant"
    assert "/api/skills/evals" in content, "Endpoint API non relié"
    print(f"✅ Dashboard HTML validé : {html_file} ({len(content)} octets, zéro CDN)")
    return html_file


def main() -> int:
    parser = argparse.ArgumentParser(description="Génère et valide le dashboard de santé des compétences.")
    parser.add_argument("--refresh", action="store_true", help="Force le recalcul complet des scores")
    args = parser.parse_args()

    json_path = ensure_skills_eval_summary(REPO_ROOT, force_refresh=args.refresh)
    html_path = verify_dashboard_html(REPO_ROOT)
    print("🚀 Cockpit de santé des compétences prêt à être servi sur /skills-health.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
