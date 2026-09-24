"""
Sous-module vibe_check/_vc_project.py
Checks liés à la structure et à l'hygiène de projet.

Checks inclus :
  - check_02_boundary    : Respect du terrain de jeu strict (Boundary) (Check 2)
  - check_05_hygiene     : Hygiène structurale & absence de sous-READMEs (Check 5)
  - check_09_lod_freshness: Fraîcheur & intégrité des sidecars LOD .overview.md (Check 9)

Les checks de gouvernance de phase (10-13) sont dans _vc_governance.py.
"""

from pathlib import Path

from src.utils.logger import get_logger

logger = get_logger("pipelines.vibe_check._vc_project")


def check_02_boundary(
    project_dir: Path, project_name: str, lifecycle_mode: str, stage_label: str
) -> dict:
    """
    Check 2 : Contrôle du terrain de jeu strict (Boundary).
    Vérifie que le répertoire projet ou le répertoire src existent pour valider
    que l'agent opère dans un environnement balisé.
    """
    boundary_ok = project_dir.exists() or Path("src").exists()
    return {
        "check": "Respect du Terrain de Jeu Strict (Boundary)",
        "status": "PASS" if boundary_ok else "FAIL",
    }


def check_05_hygiene(
    project_dir: Path, project_name: str, lifecycle_mode: str, stage_label: str
) -> dict:
    """
    Check 5 : Hygiène structurale & anti-drift des sous-READMEs.
    Détecte les README.md parasites dans les sous-répertoires du projet (hors répertoire
    reference/ et node_modules/.git).
    """
    hygiene_ok = True
    if project_dir.exists():
        sub_readmes = [
            p
            for p in project_dir.rglob("README.md")
            if p != project_dir / "README.md"
            and not str(p.relative_to(project_dir)).startswith("reference")
            and "node_modules" not in str(p)
            and ".git" not in str(p)
        ]
        if sub_readmes:
            hygiene_ok = False
    return {
        "check": "Hygiène Structurale & Absence de Sous-READMEs",
        "status": "PASS" if hygiene_ok else "FAIL",
    }


def check_09_lod_freshness(
    project_dir: Path, project_name: str, lifecycle_mode: str, stage_label: str
) -> dict:
    """
    Check 9 : Fraîcheur & intégrité des sidecars LOD (.overview.md — ADR-0335).
    Détecte les répertoires docs/ dont le .overview.md est marqué OUTDATED par le LODGenerator.
    """
    from src.core.lod_generator import LODGenerator

    lod_freshness_ok = True
    outdated_dirs = []
    if project_dir.exists():
        docs_p = project_dir / "docs"
        if docs_p.exists():
            for ov_file in docs_p.rglob(".overview.md"):
                p_dir = ov_file.parent
                res = LODGenerator.check_directory_freshness(p_dir)
                if res.get("status") == "OUTDATED":
                    lod_freshness_ok = False
                    outdated_dirs.append(p_dir.name)

    lod_msg = (
        "Fraîcheur & Intégrité des Sidecars LOD (.overview.md)"
        if lod_freshness_ok
        else f"Fraîcheur des Sidecars LOD (Obsolètes : {', '.join(outdated_dirs)})"
    )
    return {"check": lod_msg, "status": "PASS" if lod_freshness_ok else "FAIL"}
