# -*- coding: utf-8 -*-
"""
src/dashboard/routers/skills.py — Routeur FastAPI pour la Santé des Compétences Agentiques (MLOOP-243-FE).
Expose l'endpoint de données /api/skills/evals et l'onglet visuel /skills-health.
Conforme ADR-0202 (<= 300 lignes), ADR-0369 (Python Senior) et ADR-0389.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse

from src.pipelines.skill_eval import SkillEvalEngine
from src.utils.logger import get_logger

logger = get_logger("dashboard.routers.skills")

router = APIRouter(tags=["Skills Health"])

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
HTML_FILE = Path(__file__).resolve().parent.parent / "skills_health.html"


def get_skills_eval_data(workspace_root: Optional[Path] = None) -> Dict[str, Any]:
    """Charge les données d'évaluation des compétences depuis le rapport consolidé ou calcule à la volée."""
    root = workspace_root or REPO_ROOT
    candidates = [
        root / "Projects" / "mLoop" / "memory" / "evals" / "skills_eval_summary.json",
        root / "memory" / "evals" / "skills_eval_summary.json",
        root / "Projects" / "mLoop" / "memory" / "evals" / "skills_eval_report.json",
        root / "memory" / "evals" / "skills_eval_report.json",
    ]
    for c in candidates:
        if c.exists():
            try:
                data = json.loads(c.read_text(encoding="utf-8"))
                if isinstance(data, dict) and data.get("total_skills", 0) >= 30:
                    return data
            except Exception as e:
                logger.warning(f"Rapport d'évaluation corrompu sur {c} : {e}")

    # Calcul dynamique à la volée en cas d'absence de rapport pré-généré
    engine = SkillEvalEngine(workspace_root=root)
    summary = engine.evaluate_all_skills()
    try:
        engine.save_reports(summary)
    except Exception as e:
        logger.warning(f"Impossible de sauvegarder le rapport calculé : {e}")
    return summary


@router.get("/api/skills/evals", response_class=JSONResponse)
def get_skills_evals() -> Dict[str, Any]:
    """Retourne la matrice complète d'évaluation des 39 compétences avec métriques radar."""
    return get_skills_eval_data()


@router.get("/skills-health", response_class=HTMLResponse)
def get_skills_health_page() -> Any:
    """Sert l'interface HTML statique auto-contenue du cockpit de santé des compétences."""
    if HTML_FILE.exists():
        return FileResponse(HTML_FILE)
    return HTMLResponse(
        "<h1>Onglet /skills-health : fichier skills_health.html introuvable.</h1>"
        "<p>Exécutez 'python scripts/generate_skills_dashboard.py' pour le générer.</p>",
        status_code=404,
    )
