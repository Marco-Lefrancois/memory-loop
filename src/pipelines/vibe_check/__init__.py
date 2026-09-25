"""
Package vibe_check/__init__.py — Orchestrateur du Guardrail Vibe-Check Pré-Vol (MLOOP-170-BE).

Expose les deux symboles publics gelés (ADR-0202) :
  - run_vibe_check(project_name, target_file=None, stage=None) -> dict
  - detect_project_lifecycle_stage(project_dir, explicit_stage=None) -> tuple[str, str]

Délègue chaque check à son sous-module (imports explicites, zéro auto-découverte).
Verdict tri-état PASS / WARNING / FAIL (ADR-0384).
"""

import time
from pathlib import Path

from src.cli import ZeroFluffConsole
from src.utils.logger import get_logger
from src.pipelines.vibe_check._vc_agents import (
    check_01_agent_parity,
    check_16_agent_probe,
    check_19_standards_graph,
    check_23_skills_health,
)
from src.pipelines.vibe_check._vc_ssot import (
    check_04_ssot_backlog,
    check_15_guide_parity,
    check_20_directives_ssot,
)
from src.pipelines.vibe_check._vc_security import check_07_secret_leak, check_08_litellm_key
from src.pipelines.vibe_check._vc_project import (
    check_02_boundary,
    check_05_hygiene,
    check_09_lod_freshness,
)
from src.pipelines.vibe_check._vc_governance import (
    check_10_visual_contract,
    check_11_rule_engine,
    check_12_sow_granularity,
    check_13_phase_gate,
    check_25_story_state_lock,
)
from src.pipelines.vibe_check._vc_build import (
    check_03_fts5,
    check_06_lexical_guard,
    check_14_python_senior,
    check_17_qa_cert,
)
from src.pipelines.vibe_check._vc_frontend import check_21_visual_anchor
from src.pipelines.vibe_check._vc_extraction import check_22_extraction_protocol
from src.pipelines.vibe_check._vc_storage import check_24_storage_hygiene

logger = get_logger("pipelines.vibe_check")

# Alias pour la résolution de stage depuis les valeurs normalisées
_STAGE_MAP: dict[str, tuple[str, str]] = {
    "init": ("INIT", "STAGE_INIT"),
    "stage_init": ("INIT", "STAGE_INIT"),
    "inception": ("INIT", "STAGE_INIT"),
    "tshirt": ("INIT", "STAGE_INIT"),
    "t_shirt": ("INIT", "STAGE_INIT"),
    "t_shirt_size": ("INIT", "STAGE_INIT"),
    "stage_tshirt_size": ("INIT", "STAGE_INIT"),
    "sow": ("INIT", "STAGE_SOW"),
    "stage_sow": ("INIT", "STAGE_SOW"),
    "spec": ("INIT", "STAGE_SPEC"),
    "stage_spec": ("INIT", "STAGE_SPEC"),
    "ingest": ("INIT", "STAGE_SPEC"),
    "ingestion": ("INIT", "STAGE_SPEC"),
    "plan": ("RUN", "STAGE_PLAN_GRILL"),
    "stage_plan": ("RUN", "STAGE_PLAN_GRILL"),
    "grill": ("RUN", "STAGE_PLAN_GRILL"),
    "stage_plan_grill": ("RUN", "STAGE_PLAN_GRILL"),
    "build": ("RUN", "STAGE_BUILD"),
    "stage_build": ("RUN", "STAGE_BUILD"),
    "dev": ("RUN", "STAGE_BUILD"),
    "validate": ("RUN", "STAGE_VALIDATE"),
    "stage_validate": ("RUN", "STAGE_VALIDATE"),
    "qa": ("RUN", "STAGE_VALIDATE"),
    "ship": ("RUN", "STAGE_SHIP_SYNC"),
    "stage_ship": ("RUN", "STAGE_SHIP_SYNC"),
    "sync": ("RUN", "STAGE_SHIP_SYNC"),
    "stage_ship_sync": ("RUN", "STAGE_SHIP_SYNC"),
    "run": ("RUN", "STAGE_RUN"),
    "stage_run": ("RUN", "STAGE_RUN"),
    "active": ("RUN", "STAGE_RUN"),
}


def detect_project_lifecycle_stage(
    project_dir: Path, explicit_stage: str = None
) -> tuple[str, str]:
    """
    Détermine le mode du cycle de vie (INIT vs RUN) et la phase détaillée du projet (ADR-0339).

    Returns:
        tuple (mode, stage_label) : ('INIT'|'RUN', 'STAGE_INIT'|'STAGE_SOW'|'STAGE_PLAN_GRILL'|...)
    """
    if explicit_stage:
        norm = explicit_stage.strip().lower().replace("-", "_").replace(" ", "_")
        if norm in _STAGE_MAP:
            return _STAGE_MAP[norm]

    if not project_dir or not project_dir.exists():
        return "INIT", "STAGE_INIT"

    # Vérification prioritaire de l'état persistant officiel SSOT (ADR-0339)
    from src.core.lifecycle import ProjectLifecycleManager, ProjectLifecycleStage

    state_file = project_dir / "memory" / "lifecycle_state.json"
    if state_file.exists():
        l_state = ProjectLifecycleManager.get_state(project_dir)
        stage_name = l_state.current_stage.value
        mode = "INIT" if l_state.canonical_stage == ProjectLifecycleStage.STAGE_1_INGEST else "RUN"
        return mode, stage_name

    return _detect_from_filesystem(project_dir)


def _detect_from_filesystem(project_dir: Path) -> tuple[str, str]:
    """Détecte la phase du cycle de vie à partir des marqueurs du système de fichiers."""
    backlog_file = project_dir / "backlog" / "sprint_backlog.md"
    stories_dir = project_dir / "backlog" / "stories"
    stories = (
        [s for s in stories_dir.glob("*.md") if s.name != "README.md"]
        if stories_dir.exists()
        else []
    )

    has_active_stories = len(stories) > 0
    has_engaged_stories = False
    if backlog_file.exists():
        try:
            content = backlog_file.read_text(encoding="utf-8")
            table_rows = [
                line
                for line in content.splitlines()
                if line.strip().startswith("|")
                and not line.strip().startswith("| :---")
                and not line.strip().startswith("| ID")
                and not line.strip().startswith("| #")
                and not line.strip().startswith("| Métrique")
            ]
            # Récits engagés au-delà du simple statut OPEN/BACKLOG (Gate 2 Plan/Grill franchie)
            engaged_keywords = [
                "IN_ANALYZE",
                "READY_FOR_GROOMING",
                "READY_FOR_DEV",
                "IN_DEV",
                "DONE",
                "CLOSED",
                "ON-HOLD",
            ]
            for row in table_rows:
                if any(kw in row.upper() for kw in engaged_keywords):
                    has_engaged_stories = True
                    break
        except Exception:
            logger.error(
                "Erreur de lecture du sprint_backlog.md lors de la détection de phase.",
                exc_info=True,
                extra={
                    "check_name": "detect_project_lifecycle_stage",
                    "violation_type": "backlog_read_error",
                    "file_path": str(backlog_file),
                },
            )

    if has_active_stories or has_engaged_stories:
        return "RUN", "STAGE_PLAN_GRILL"

    arch_dir = project_dir / "docs" / "01-architecture"
    if arch_dir.exists() and list(arch_dir.glob("SOW_*.md")):
        return "INIT", "STAGE_SOW"

    ingested_dir = project_dir / "docs" / "00-ingested"
    ref_dir = project_dir / "reference"
    if (ingested_dir.exists() and list(ingested_dir.glob("*.md"))) or (
        ref_dir.exists() and list(ref_dir.glob("*"))
    ):
        return "INIT", "STAGE_SPEC"

    return "INIT", "STAGE_INIT"


def run_vibe_check(project_name: str, target_file: str = None, stage: str = None) -> dict:
    """
    Axe 2 Joe Njenga / Vibe Code Common Sense (ADR-0310) : Guardrail Vibe-Check Pré-Vol.
    Exécute une vérification déterministe d'intégrité avant modification de code
    avec gouvernance des étapes (ADR-0339).
    """
    project_dir = Path("Projects") / project_name
    if not project_dir.exists():
        if (
            project_name.lower() in ["mloop", "memory loop", "root"]
            and (Path("Projects") / "mLoop").exists()
        ):
            project_dir = Path("Projects") / "mLoop"
        elif (Path("Projects") / project_name.replace(" ", "_")).exists():
            project_dir = Path("Projects") / project_name.replace(" ", "_")

    t0 = time.perf_counter()
    lifecycle_mode, stage_label = detect_project_lifecycle_stage(project_dir, explicit_stage=stage)
    logger.info(
        f"[VIBE-CHECK] Début du guardrail pré-vol pour '{project_name}'.",
        extra={"phase": stage_label, "project": project_name},
    )
    ZeroFluffConsole.section(
        f"Guardrail Vibe-Check Pré-Vol - mLoop ({project_name}) [Mode: {lifecycle_mode} | {stage_label}]"
    )

    ctx = (project_dir, project_name, lifecycle_mode, stage_label)
    checks: list[dict] = []

    checks.extend(check_01_agent_parity(*ctx))  # Check 1 : parité miroir AGENTS/GEMINI/CLAUDE
    checks.append(check_02_boundary(*ctx))  # Check 2 : boundary terrain de jeu
    checks.append(check_03_fts5(*ctx))  # Check 3 : Fact-Search FTS5
    checks.append(check_04_ssot_backlog(*ctx))  # Check 4 : alignement SSOT backlog
    checks.append(check_05_hygiene(*ctx))  # Check 5 : hygiène sous-READMEs
    checks.append(check_06_lexical_guard(*ctx))  # Check 6 : intégrité lexicale Canary
    checks.append(check_07_secret_leak(*ctx))  # Check 7 : zero-leak secrets
    checks.append(check_08_litellm_key(*ctx))  # Check 8 : alignement clé LiteLLM
    checks.append(check_09_lod_freshness(*ctx))  # Check 9 : fraîcheur LOD .overview.md
    checks.append(check_10_visual_contract(*ctx))  # Check 10 : contrat visuel OCR
    checks.append(check_11_rule_engine(*ctx))  # Check 11 : RuleEngine dynamique ADR-0328
    checks.append(check_12_sow_granularity(*ctx))  # Check 12 : granularité SOW ADR-0331
    checks.append(check_13_phase_gate(*ctx))  # Check 13 : interdiction saut de phase
    checks.append(check_14_python_senior(*ctx))  # Check 14 : standards Python Senior ADR-0369
    checks.append(check_15_guide_parity(*ctx))  # Check 15 : parité Guide CLI ADR-0370
    checks.append(check_16_agent_probe(*ctx))  # Check 16 : runtimes agents ADR-0377
    checks.append(check_17_qa_cert(*ctx))  # Check 17 : certification QA Sprint
    checks.append(check_19_standards_graph(*ctx))  # Check 19 : StandardsGraph ADR-0379
    checks.append(check_20_directives_ssot(*ctx))  # Check 20 : directives projet ADR-0384
    checks.append(check_21_visual_anchor(*ctx))  # Check 21 : ancrage visuel frontend
    checks.append(check_22_extraction_protocol(*ctx))  # Check 22 : protocole extraction modulaire
    checks.append(
        check_23_skills_health(*ctx)
    )  # Check 23 : Intégrité & Santé des Compétences ADR-0389
    checks.append(check_24_storage_hygiene(*ctx))  # Check 24 : Hygiène & Plafond Stockage ADR-015
    checks.append(check_25_story_state_lock(*ctx))  # Check 25 : Verrou anti-promotion MLOOP-270-BE

    passed_count = sum(1 for c in checks if c["status"] == "PASS")
    warning_count = sum(1 for c in checks if c["status"] == "WARNING")
    fail_count = sum(1 for c in checks if c["status"] == "FAIL")
    total_count = len(checks)

    for c in checks:
        if c["status"] == "PASS":
            ZeroFluffConsole.success(f"{c['check']} : PASS")
        elif c["status"] == "WARNING":
            ZeroFluffConsole.warning(f"{c['check']} : WARNING")
        else:
            ZeroFluffConsole.error(f"{c['check']} : FAIL")

    # Verdict tri-état (ADR-0384) : FAIL bloquant, WARNING non bloquant.
    is_valid = fail_count == 0
    ZeroFluffConsole.info(
        f"Résultat Vibe-Check : {passed_count} PASS / {warning_count} WARNING / "
        f"{fail_count} FAIL (sur {total_count} contrôles)."
    )

    duration_ms = round((time.perf_counter() - t0) * 1000, 2)
    logger.info(
        f"[VIBE-CHECK] Fin du guardrail pré-vol pour '{project_name}' : "
        f"{passed_count}P/{warning_count}W/{fail_count}F.",
        extra={
            "phase": stage_label,
            "project": project_name,
            "score": f"{passed_count}/{total_count}",
            "warning_count": warning_count,
            "fail_count": fail_count,
            "duration_ms": duration_ms,
        },
    )

    return {
        "status": "PASS" if is_valid else "FAIL",
        "checks": checks,
        "score": f"{passed_count}/{total_count}",
        "passed_count": passed_count,
        "warning_count": warning_count,
        "fail_count": fail_count,
        "lifecycle_mode": lifecycle_mode,
        "stage": stage_label,
    }


__all__ = ["run_vibe_check", "detect_project_lifecycle_stage"]
