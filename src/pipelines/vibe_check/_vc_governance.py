"""
Sous-module vibe_check/_vc_governance.py
Checks liés à la gouvernance de phase et à la conformité des artefacts projet.

Checks inclus :
  - check_10_visual_contract: Contrat visuel lisible (maquettes OCR SSOT) (Check 10)
  - check_11_rule_engine    : Intégrité RuleEngine dynamique (ADR-0328) (Check 11)
  - check_12_sow_granularity: Granularité SOW (ADR-0331) (Check 12)
  - check_13_phase_gate     : Interdiction de saut de phase (ADR-0375 / ADR-0339) (Check 13)
  - check_25_story_state_lock: Verrou anti-promotion & journal des transitions (Check 25)
"""

from pathlib import Path

from src.utils.logger import get_logger

logger = get_logger("pipelines.vibe_check._vc_governance")


def check_10_visual_contract(
    project_dir: Path, project_name: str, lifecycle_mode: str, stage_label: str
) -> dict:
    """
    Check 10 (Phase 2.3 — Enforcement déterministe du grounding visuel) :
    Contrat Visuel Lisible. Détecte les maquettes ingérées vectorisées (Mode 2,
    is_vectorized: true) dont l'OCR n'a PAS pu extraire le texte réel
    (ocr_status != "DONE"), matérialisant l'angle mort «maquette illisible» du
    Contrat Visuel (AGENTS.md : Maquettes = SSOT absolue).
    """
    visual_contract_ok = True
    unread_mockups = []
    if project_dir.exists():
        maquettes_dir = project_dir / "docs" / "00-ingested" / "maquettes"
        if maquettes_dir.exists():
            for mockup_md in maquettes_dir.glob("*.md"):
                try:
                    mtext = mockup_md.read_text(encoding="utf-8", errors="replace")
                except Exception:
                    logger.error(
                        f"Erreur de lecture de la maquette '{mockup_md}' (Contrat Visuel).",
                        exc_info=True,
                        extra={
                            "check_name": "visual_contract_ocr",
                            "violation_type": "mockup_read_error",
                            "file_path": str(mockup_md),
                        },
                    )
                    continue
                if not mtext.startswith("---"):
                    continue
                fm_match = mtext.split("---", 2)
                if len(fm_match) < 3:
                    continue
                fm_text = fm_match[1]
                is_vect = "is_vectorized: true" in fm_text
                ocr_done = 'ocr_status: "DONE"' in fm_text
                if is_vect and not ocr_done:
                    visual_contract_ok = False
                    unread_mockups.append(mockup_md.stem)

    visual_msg = (
        "Contrat Visuel Lisible (Maquettes SSOT)"
        if visual_contract_ok
        else f"Contrat Visuel Lisible (Maquettes vectorisées non lues par OCR : {', '.join(unread_mockups)})"
    )
    return {"check": visual_msg, "status": "PASS" if visual_contract_ok else "FAIL"}


def check_11_rule_engine(
    project_dir: Path, project_name: str, lifecycle_mode: str, stage_label: str
) -> dict:
    """
    Check 11 (ADR-0328 §2.2 — Intégration dynamique RuleEngine) :
    Les règles déclaratives `validation_rules` du frontmatter YAML des ADRs projet
    (docs/01-architecture/) sont injectées dynamiquement et validées contre les
    récits du backlog/stories/. Toute violation BLOCKING produit un FAIL.
    """
    rule_engine_ok = True
    rule_engine_violations = []
    if project_dir.exists():
        try:
            from src.core.rule_engine import RuleEngine

            arch_dir = project_dir / "docs" / "01-architecture"
            stories_dir = project_dir / "backlog" / "stories"
            if arch_dir.exists() and stories_dir.exists():
                rule_engine = RuleEngine()
                rule_engine.load_from_adr_dir(arch_dir)
                for sf in stories_dir.glob("**/*.md"):
                    if any(
                        p in ("archive", "_archive", "archive_deprecated", "reference")
                        for p in sf.parts
                    ):
                        continue
                    try:
                        s_content = sf.read_text(encoding="utf-8", errors="replace")
                    except Exception:
                        logger.error(
                            f"Erreur de lecture du récit '{sf}' lors de la validation RuleEngine.",
                            exc_info=True,
                            extra={
                                "check_name": "rule_engine_validation",
                                "violation_type": "story_read_error",
                                "file_path": str(sf),
                            },
                        )
                        continue
                    for v in rule_engine.validate_all(s_content, target="backlog_stories"):
                        if v.severity == "BLOCKING":
                            rule_engine_ok = False
                            rule_engine_violations.append(f"{sf.name}:[{v.check_id}]")
        except Exception:
            logger.error(
                "Erreur lors du chargement ou de l'exécution du RuleEngine dynamique (ADR-0328).",
                exc_info=True,
                extra={
                    "check_name": "rule_engine_validation",
                    "violation_type": "rule_engine_load_error",
                },
            )

    rule_engine_msg = (
        "Intégrité RuleEngine Dynamique (ADR-0328)"
        if rule_engine_ok
        else f"Intégrité RuleEngine Dynamique (Violations BLOCKING : {', '.join(rule_engine_violations)})"
    )
    return {"check": rule_engine_msg, "status": "PASS" if rule_engine_ok else "FAIL"}


def check_12_sow_granularity(
    project_dir: Path, project_name: str, lifecycle_mode: str, stage_label: str
) -> dict:
    """
    Check 12 (ADR-0331 §2.2 Règle #3 — Interdiction formelle des libellés génériques) :
    Tout SOW généré sous docs/01-architecture/SOW_*.md ne doit contenir aucun libellé
    vague (« [Détail des récits] », « Composant générique », « Développement divers »)
    dans son tableau de chiffrage.
    """
    sow_granularity_ok = True
    sow_violations_count = 0
    if project_dir.exists():
        try:
            from src.pipelines.sow_engine import SOWEngine

            arch_dir = project_dir / "docs" / "01-architecture"
            if arch_dir.exists():
                sow_engine = SOWEngine(project_dir)
                for sow_file in arch_dir.glob("SOW_*.md"):
                    v = sow_engine.validate_task_granularity(sow_file)
                    if v:
                        sow_granularity_ok = False
                        sow_violations_count += len(v)
        except Exception:
            logger.error(
                "Erreur lors de la validation de granularité SOW (ADR-0331).",
                exc_info=True,
                extra={"check_name": "sow_granularity", "violation_type": "sow_engine_error"},
            )

    sow_msg = (
        "Granularité SOW (ADR-0331)"
        if sow_granularity_ok
        else f"Granularité SOW (Libellés génériques détectés : {sow_violations_count})"
    )
    return {"check": sow_msg, "status": "PASS" if sow_granularity_ok else "FAIL"}


def check_13_phase_gate(
    project_dir: Path, project_name: str, lifecycle_mode: str, stage_label: str
) -> dict:
    """
    Check 13 (ADR-0339 §3 — Interdiction de saut de phase) :
    Un projet ne doit JAMAIS compter de récits détaillés (backlog/stories/) ni de statuts
    d'analyse engagés en Phase 0 ou 1 (Porte 1 non franchie). En Phase 2+, vérifie qu'un SOW,
    des specs ou un sprint_backlog existe si des stories existent (Fast-Track).
    """
    phase_gate_ok = True
    phase_gate_violations = []
    if not project_dir.exists():
        return {
            "check": "Interdiction de Saut de Phase (ADR-0375 / ADR-0339)",
            "status": "PASS",
        }

    from src.core.lifecycle import ProjectLifecycleManager, ProjectLifecycleStage

    l_state = ProjectLifecycleManager.get_state(project_dir)
    stories_dir = project_dir / "backlog" / "stories"
    detailed_stories = (
        [s for s in stories_dir.glob("*.md") if s.name.lower() != "readme.md"]
        if stories_dir.exists()
        else []
    )

    if l_state.canonical_stage == ProjectLifecycleStage.STAGE_1_INGEST:
        phase_gate_ok, phase_gate_violations = _check_phase1_gate(
            project_dir, detailed_stories, l_state, phase_gate_violations
        )
    else:
        phase_gate_ok, phase_gate_violations = _check_phase2plus_gate(
            project_dir, detailed_stories, phase_gate_violations
        )

    phase_gate_msg = (
        "Interdiction de Saut de Phase (ADR-0375 / ADR-0339)"
        if phase_gate_ok
        else (
            f"Interdiction de Saut de Phase (ADR-0375 / ADR-0339 : "
            f"{'; '.join(phase_gate_violations)} — "
            f"Exécutez 'python src/swarm.py lifecycle-clean --project {project_name}')"
        )
    )
    return {"check": phase_gate_msg, "status": "PASS" if phase_gate_ok else "FAIL"}


def _check_phase1_gate(project_dir, detailed_stories, l_state, violations):
    """Sous-routine : contrôle de la porte de phase 1 (STAGE_1_INGEST)."""
    ok = True
    if detailed_stories:
        ok = False
        violations.append(
            f"{len(detailed_stories)} récit(s) détaillé(s) sous backlog/stories/ "
            f"interdit(s) en étape '{l_state.current_stage.value}'"
        )

    backlog_file = project_dir / "backlog" / "sprint_backlog.md"
    if backlog_file.exists():
        try:
            b_lines = backlog_file.read_text(encoding="utf-8", errors="ignore").splitlines()
            table_rows = [
                line
                for line in b_lines
                if line.strip().startswith("|")
                and not line.strip().startswith("| :---")
                and not line.strip().startswith("| ID")
                and not line.strip().startswith("| #")
                and not line.strip().startswith("| Métrique")
            ]
            for row in table_rows:
                for kw in ["IN_ANALYZE", "READY_FOR_GROOMING", "READY_FOR_DEV", "IN_DEV"]:
                    if kw in row.upper():
                        ok = False
                        violations.append(
                            f"Statut engagé '{kw}' détecté dans les récits de "
                            "sprint_backlog.md interdit avant franchissement de Gate 1"
                        )
                        break
                if not ok:
                    break
        except Exception:
            logger = __import__("src.utils.logger", fromlist=["get_logger"]).get_logger(
                "pipelines.vibe_check._vc_governance"
            )
            logger.error(
                "Erreur lecture sprint_backlog.md pour Check 13.",
                exc_info=True,
                extra={
                    "check_name": "phase_gate_check13",
                    "violation_type": "backlog_read_error",
                    "file_path": str(backlog_file),
                },
            )
    return ok, violations


def _check_phase2plus_gate(project_dir, detailed_stories, violations):
    """Sous-routine : contrôle Fast-Track pour phases 2+ (SOW/specs/backlog requis)."""
    ok = True
    arch_dir = project_dir / "docs" / "01-architecture"
    specs_dir = project_dir / "docs" / "02-specs"
    has_sow = arch_dir.exists() and any(arch_dir.glob("SOW_*.md"))
    has_specs = specs_dir.exists() and any(specs_dir.glob("*.md"))
    sprint_file = project_dir / "backlog" / "sprint_backlog.md"
    if detailed_stories and not has_sow and not has_specs and not sprint_file.exists():
        ok = False
        violations.append("Récits détaillés sans SOW, specs ni sprint_backlog préalable")
    return ok, violations


def check_25_story_state_lock(
    project_dir: Path, project_name: str, lifecycle_mode: str, stage_label: str
) -> dict:
    """
    Check 25 (MLOOP-270-BE / ADR-011 — Verrou Anti-Promotion & Journal des
    Transitions) : confronte la ligne d'état de chaque récit au journal
    append-only `memory/story_transitions.jsonl` et à la preuve d'approbation
    humaine (`validated_by` / `validated_at`).

    FAIL si revendication CA-4 non corroborée par un artefact sur disque, ou si
    un écart BLOCKING subsiste sur un projet rétro-équipé (`origin: backfill`).
    Corps des règles partagé avec le struct-check C13 : `_struct_c13.py`.
    Lecture seule (scan `apply_sanctions=False`) — jamais d'écriture dans `backlog/`.
    """
    from src.pipelines._struct_c13 import summarize_project_state_lock

    return summarize_project_state_lock(project_dir)
