"""
Sous-module vibe_check/_vc_ssot.py
Checks liés à la cohérence SSOT, au backlog sprint et au guide CLI (ADR-0339, ADR-0370, ADR-0384).

Checks inclus :
  - check_04_ssot_backlog    : Alignement SSOT & détection de références fantômes (Check 4)
  - check_15_guide_parity    : Parité SSOT & auto-healing du Guide CLI (Check 15)
  - check_20_directives_ssot : Intégrité des directives projet & SSOT canonique (Check 20)
"""

from pathlib import Path

from src.cli import ZeroFluffConsole
from src.utils.logger import get_logger

logger = get_logger("pipelines.vibe_check._vc_ssot")


def check_04_ssot_backlog(
    project_dir: Path, project_name: str, lifecycle_mode: str, stage_label: str
) -> dict:
    """
    Check 4 : Alignement SSOT & détection de références fantômes avec gouvernance de phase
    (ADR-0339). En mode INIT, le sprint_backlog.md n'est pas requis. En mode RUN,
    il est strictement obligatoire si AGENTS.md le déclare.
    """
    agents_md = Path("AGENTS.md")
    ssot_ok = True
    ssot_msg = ""
    backlog_file = project_dir / "backlog" / "sprint_backlog.md"

    if lifecycle_mode == "INIT":
        # En mode INIT, sprint_backlog.md n'est pas requis (projet en genèse / SOW / Ingestion)
        if backlog_file.exists():
            ssot_msg = f" (Phase {lifecycle_mode} : Backlog initialisé)"
        else:
            ssot_msg = f" (Phase {lifecycle_mode} : Backlog en attente de découpage)"
        ssot_ok = True
    else:
        # En mode RUN, sprint_backlog.md est strictement obligatoire
        if agents_md.exists():
            content = agents_md.read_text(encoding="utf-8")
            if "sprint_backlog.md" in content and not backlog_file.exists():
                ssot_ok = False
                ssot_msg = " (sprint_backlog.md requis en phase RUN)"
            else:
                ssot_msg = f" (Phase {lifecycle_mode} : Backlog vérifié)"

    return {
        "check": f"Intégrité SSOT & Absence de Références Fantômes{ssot_msg}",
        "status": "PASS" if ssot_ok else "FAIL",
    }


def check_15_guide_parity(
    project_dir: Path, project_name: str, lifecycle_mode: str, stage_label: str
) -> dict:
    """
    Check 15 : Parité SSOT & auto-healing du Guide CLI (ADR-0370).
    Garantit que standards/protocols/CLI_PIPELINE_GUIDE.md contient l'intégralité
    des commandes déclarées dans src/commands/_registry.py sans dérive documentaire.
    Auto-healing déclenché si désynchronisation détectée.
    """
    from src.pipelines.guide_generator import check_guide_parity, sync_cli_guide

    guide_sync_ok, total_reg, total_in_g, missing_cmds = check_guide_parity()
    if not guide_sync_ok:
        ZeroFluffConsole.info(
            f"[Vibe-Check Auto-Healing] CLI_PIPELINE_GUIDE.md désynchronisé "
            f"({len(missing_cmds)} commandes manquantes). Régénération automatique en cours..."
        )
        sync_cli_guide()
        guide_sync_ok, total_reg, total_in_g, missing_cmds = check_guide_parity()

    guide_msg = (
        f"Parité SSOT du Guide CLI ({total_reg}/{total_reg} commandes - ADR-0370)"
        if guide_sync_ok
        else f"Parité SSOT du Guide CLI ({len(missing_cmds)} commandes manquantes : {', '.join(missing_cmds[:3])}...)"
    )
    return {"check": guide_msg, "status": "PASS" if guide_sync_ok else "FAIL"}


def check_20_directives_ssot(
    project_dir: Path, project_name: str, lifecycle_mode: str, stage_label: str
) -> dict:
    """
    Check 20 : Intégrité des directives projet & SSOT canonique (ADR-0384).
    Contrôle CONDITIONNEL et NON BLOQUANT. Si le projet ne déclare pas de répertoire
    `directives/`, le contrôle réussit immédiatement (zéro régression pour les projets
    sans ce standard). S'il en déclare un, il vérifie que tech.md et business.md
    existent, sont non vides, que CONTEXT.md est présent, et qu'au moins une mention
    de SSOT canonique (docs/03-models/) ou de hiérarchie est déclarée.
    Toute non-conformité produit un WARNING.
    """
    directives_status = "PASS"
    directives_msg = "Intégrité Directives Projet & SSOT Canonique (non applicable)"

    if not project_dir.exists():
        return {"check": directives_msg, "status": directives_status}

    directives_dir = project_dir / "directives"
    if not directives_dir.exists():
        return {"check": directives_msg, "status": directives_status}

    directives_violations = []
    tech_file = directives_dir / "tech.md"
    business_file = directives_dir / "business.md"
    context_file = project_dir / "CONTEXT.md"

    ssot_declared = False
    for df in (tech_file, business_file):
        if not df.exists():
            directives_violations.append(f"{df.name} manquant")
            continue
        try:
            dtext = df.read_text(encoding="utf-8", errors="replace")
        except Exception as exc:
            logger.error(
                f"Erreur de lecture de la directive '{df}' (Check 20 SSOT).",
                exc_info=True,
                extra={
                    "check_name": "directives_ssot_integrity",
                    "violation_type": "directive_read_error",
                    "file_path": str(df),
                },
            )
            directives_violations.append(f"{df.name} illisible")
            continue
        if not dtext.strip():
            directives_violations.append(f"{df.name} vide")
        if (
            "docs/03-models" in dtext
            or "SSOT" in dtext
            or "source de vérité canonique" in dtext.lower()
        ):
            ssot_declared = True

    if not context_file.exists():
        directives_violations.append("CONTEXT.md manquant")
    if not ssot_declared:
        directives_violations.append("aucune source de vérité canonique déclarée")

    if directives_violations:
        directives_status = "WARNING"
        directives_msg = (
            "Intégrité Directives Projet & SSOT Canonique "
            f"(Avertissements : {', '.join(directives_violations)})"
        )
    else:
        directives_msg = "Intégrité Directives Projet & SSOT Canonique (conforme)"

    return {"check": directives_msg, "status": directives_status}
