"""
Sous-module vibe_check/_vc_frontend.py
Check lié à l'ancrage visuel des récits Frontend (ADR-0384).

Checks inclus :
  - check_21_visual_anchor : Ancrage visuel des récits frontend / Contrat Visuel Premier (Check 21)
"""

from pathlib import Path

from src.utils.logger import get_logger

logger = get_logger("pipelines.vibe_check._vc_frontend")


def check_21_visual_anchor(
    project_dir: Path, project_name: str, lifecycle_mode: str, stage_label: str
) -> dict:
    """
    Check 21 (ADR-0384 — Ancrage Visuel des Récits Frontend / Contrat Visuel Premier) :
    Matérialise le principe universel «Maquettes = SSOT». Pour tout récit
    `layer: frontend` ou `layer: fullstack` en Phase ≥ 2 (mode RUN), produit un WARNING
    si aucune référence de maquette n'est détectée dans le corps du récit.
    Les récits backend sont exclus de ce contrôle.
    """
    visual_anchor_status = "PASS"
    unanchored_stories: list[str] = []

    if project_dir.exists() and lifecycle_mode == "RUN":
        stories_dir = project_dir / "backlog" / "stories"
        if stories_dir.exists():
            for sf in stories_dir.glob("**/*.md"):
                if sf.name.lower() == "readme.md":
                    continue
                try:
                    stext = sf.read_text(encoding="utf-8", errors="replace")
                except Exception:
                    logger.error(
                        f"Erreur de lecture du récit '{sf}' (Check 21 ancrage visuel).",
                        exc_info=True,
                        extra={
                            "check_name": "visual_anchor",
                            "violation_type": "story_read_error",
                            "file_path": str(sf),
                        },
                    )
                    continue
                if not stext.startswith("---"):
                    continue
                fm_parts = stext.split("---", 2)
                if len(fm_parts) < 3:
                    continue
                fm_text = fm_parts[1]
                is_frontend = "layer: frontend" in fm_text or "layer: fullstack" in fm_text
                if not is_frontend:
                    continue
                body = fm_parts[2]
                has_anchor = (
                    "docs/05-assets" in body
                    or "figma.com" in body.lower()
                    or "Maquettes SSOT" in body
                    or "Maquette Validée" in body
                )
                if not has_anchor:
                    unanchored_stories.append(sf.stem)

    if unanchored_stories:
        visual_anchor_status = "WARNING"
        visual_anchor_msg = (
            "Ancrage Visuel des Récits Frontend "
            f"(Récits sans maquette : {', '.join(unanchored_stories[:5])}"
            f"{'...' if len(unanchored_stories) > 5 else ''})"
        )
    else:
        visual_anchor_msg = "Ancrage Visuel des Récits Frontend (Contrat Visuel Premier)"

    return {"check": visual_anchor_msg, "status": visual_anchor_status}
