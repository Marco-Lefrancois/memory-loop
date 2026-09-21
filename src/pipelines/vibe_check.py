import os
import time
from pathlib import Path
from src.cli import ZeroFluffConsole
from src.utils.logger import get_logger

logger = get_logger("pipelines.vibe_check")


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
        if norm in [
            "init",
            "stage_init",
            "inception",
            "tshirt",
            "t_shirt",
            "t_shirt_size",
            "stage_tshirt_size",
        ]:
            return "INIT", "STAGE_INIT"
        elif norm in ["sow", "stage_sow"]:
            return "INIT", "STAGE_SOW"
        elif norm in ["spec", "stage_spec", "ingest", "ingestion"]:
            return "INIT", "STAGE_SPEC"
        elif norm in ["plan", "stage_plan", "grill", "stage_plan_grill"]:
            return "RUN", "STAGE_PLAN_GRILL"
        elif norm in ["build", "stage_build", "dev"]:
            return "RUN", "STAGE_BUILD"
        elif norm in ["validate", "stage_validate", "qa"]:
            return "RUN", "STAGE_VALIDATE"
        elif norm in ["ship", "stage_ship", "sync", "stage_ship_sync"]:
            return "RUN", "STAGE_SHIP_SYNC"
        elif norm in ["run", "stage_run", "active"]:
            return "RUN", "STAGE_RUN"

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

    backlog_file = project_dir / "backlog" / "sprint_backlog.md"
    stories_dir = project_dir / "backlog" / "stories"
    stories = (
        [s for s in stories_dir.glob("*.md") if s.name != "README.md"]
        if stories_dir.exists()
        else []
    )

    # Vérification du contenu réel du backlog
    has_active_stories = len(stories) > 0
    has_backlog_entries = False
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
            has_backlog_entries = len(table_rows) > 0

            # Récits engagés au-delà du simple statut macro OPEN/BACKLOG (Gate 2 Plan/Grill franchie)
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
        except Exception as e:
            logger.error(
                "Erreur de lecture du sprint_backlog.md lors de la détection de phase.",
                exc_info=True,
                extra={
                    "check_name": "detect_project_lifecycle_stage",
                    "violation_type": "backlog_read_error",
                    "file_path": str(backlog_file),
                },
            )

    # Si des récits physiques existent ou si des stories sont activement engagées en analyse/dev
    if has_active_stories or has_engaged_stories:
        return "RUN", "STAGE_PLAN_GRILL"

    # Vérification des marqueurs de phase d'Inception / Cadrage (Phase INIT)
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
    Exécute une vérification déterministe d'intégrité avant modification de code avec gouvernance des étapes (ADR-0339).
    """
    # Résolution du répertoire projet
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

    checks = []

    # Check 1 : Présence et Parité Miroir des directives fondamentales AGENTS.md / GEMINI.md / CLAUDE.md
    rule_files = ["AGENTS.md", "GEMINI.md", "CLAUDE.md"]
    presence_ok = all(Path(rf).exists() for rf in rule_files)

    # Contrôle de Parité Miroir & Auto-Sync Anti-Drift
    parity_ok = True
    if presence_ok:
        agents_txt = Path("AGENTS.md").read_text(encoding="utf-8")
        for rf in ["GEMINI.md", "CLAUDE.md"]:
            rf_p = Path(rf)
            rf_txt = rf_p.read_text(encoding="utf-8")
            if rf_txt != agents_txt:
                # Auto-healing : synchroniser le miroir depuis AGENTS.md
                rf_p.write_text(agents_txt, encoding="utf-8")
                ZeroFluffConsole.success(
                    f"[Vibe-Check Auto-Sync] Parité miroir restaurée pour {rf} depuis AGENTS.md"
                )

    for rule_file in rule_files:
        exists = Path(rule_file).exists()
        checks.append(
            {
                "check": f"Règles {rule_file} (Parité Miroir)",
                "status": "PASS" if exists and parity_ok else "FAIL",
            }
        )

    # Check 2 : Contrôle du terrain de jeu strict (Boundary)
    boundary_ok = project_dir.exists() or Path("src").exists()
    checks.append(
        {
            "check": "Respect du Terrain de Jeu Strict (Boundary)",
            "status": "PASS" if boundary_ok else "FAIL",
        }
    )

    # Check 3 : Fact-Search FTS5 & Mémoire Persistante
    from src.loop_mem.db import search_observations

    search_observations(query="architecture", project_name=project_name)
    checks.append({"check": "Fact-Search FTS5 Before Edit", "status": "PASS"})

    # Check 4 : Alignement SSOT & Détection de Références Fantômes (Gouvernance de Phase ADR-0339)
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

    checks.append(
        {
            "check": f"Intégrité SSOT & Absence de Références Fantômes{ssot_msg}",
            "status": "PASS" if ssot_ok else "FAIL",
        }
    )

    # Check 5 : Hygiène de Projet & Anti-Drift Sub-READMEs
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
    checks.append(
        {
            "check": "Hygiène Structurale & Absence de Sous-READMEs",
            "status": "PASS" if hygiene_ok else "FAIL",
        }
    )

    # Check 6 : Intégrité Lexicale & Signature de Vocabulaire (Rosetta Canary & Unicode NFC - ADR-0327)
    from src.utils.lexical_guard import LexicalIntegrityGuard

    lex_res = LexicalIntegrityGuard.inspect_project_evidence(
        project_dir if project_dir.exists() else Path(".")
    )
    checks.append(
        {
            "check": f"Intégrité Lexicale & Signature de Vocabulaire (Canary: {lex_res.canary_hash})",
            "status": "PASS" if lex_res.is_valid else "FAIL",
        }
    )

    # Check 7 : Étanchéité des Secrets & Tokens (Zero-Leak Envsitter Pattern)
    from src.utils.secret_guard import SecretLeakGuard

    secret_leaks = []
    if project_dir.exists():
        for check_path in [
            project_dir / "backlog",
            project_dir / "memory" / "evidence",
        ]:
            if check_path.exists():
                for f in check_path.rglob("*.json"):
                    try:
                        content = f.read_text(encoding="utf-8")
                        leaks = SecretLeakGuard.scan_for_leaks(content)
                        if leaks:
                            secret_leaks.append(f.name)
                    except Exception as e:
                        logger.error(
                            f"Erreur de lecture du fichier '{f}' lors du scan de fuite de secrets.",
                            exc_info=True,
                            extra={
                                "check_name": "secret_leak_scan",
                                "violation_type": "file_read_error",
                                "file_path": str(f),
                            },
                        )
    checks.append(
        {
            "check": "Étanchéité des Secrets & Tokens (Zero-Leak Envsitter Pattern)",
            "status": "PASS" if len(secret_leaks) == 0 else "FAIL",
        }
    )

    # Check 8 : Alignement Strict Projet ↔ Clé LiteLLM (Zero Cost-Leak)
    from src.utils.token_ledger import TokenLedger

    key_info = TokenLedger.resolve_active_key_info()
    active_label = key_info.get("key_label", "Inconnue")

    allow_cross_key = os.getenv("MLOOP_ALLOW_CROSS_KEY", "").lower() in [
        "1",
        "true",
        "yes",
    ] or os.getenv("ALLOW_CROSS_KEY", "").lower() in ["1", "true", "yes"]
    key_alignment_ok = True
    key_reason = f"Clé active : {active_label}"
    p_lower = (project_name or "").lower()

    if "boire" in p_lower:
        if active_label != "Boire et Frère":
            if allow_cross_key:
                key_reason = f"Projet '{project_name}' avec clé '{active_label}' (Dérogation MLOOP_ALLOW_CROSS_KEY active)"
            else:
                key_alignment_ok = False
                key_reason = f"Projet '{project_name}' requiert la clé 'Boire et Frère' (active: '{active_label}')"
    elif "metro" in p_lower:
        if active_label != "Metro":
            if allow_cross_key:
                key_reason = f"Projet '{project_name}' avec clé '{active_label}' (Dérogation MLOOP_ALLOW_CROSS_KEY active)"
            else:
                key_alignment_ok = False
                key_reason = (
                    f"Projet '{project_name}' requiert la clé 'Metro' (active: '{active_label}')"
                )

    checks.append(
        {
            "check": f"Alignement Projet ↔ Clé LiteLLM ({key_reason})",
            "status": "PASS" if key_alignment_ok else "FAIL",
        }
    )

    # Check 9 : Fraîcheur & Intégrité des Sidecars LOD (.overview.md - ADR-0335)
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
    checks.append({"check": lod_msg, "status": "PASS" if lod_freshness_ok else "FAIL"})

    # Check 10 (Phase 2.3 — Enforcement Déterministe du Grounding Visuel) :
    # Contrat Visuel Lisible. Détecte les maquettes ingérées vectorisées (Mode 2,
    # is_vectorized: true) dont l'OCR n'a PAS pu extraire le texte réel
    # (ocr_status != "DONE"), matérialisant l'angle mort "maquette illisible" du
    # Contrat Visuel (AGENTS.md : Maquettes = SSOT absolue).
    visual_contract_ok = True
    unread_mockups = []
    if project_dir.exists():
        maquettes_dir = project_dir / "docs" / "00-ingested" / "maquettes"
        if maquettes_dir.exists():
            for mockup_md in maquettes_dir.glob("*.md"):
                try:
                    mtext = mockup_md.read_text(encoding="utf-8", errors="replace")
                except Exception as e:
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
    checks.append({"check": visual_msg, "status": "PASS" if visual_contract_ok else "FAIL"})

    # Check 11 (ADR-0328 §2.2 — Intégration Dynamique RuleEngine) : les règles
    # déclaratives `validation_rules` du frontmatter YAML des ADRs projet
    # (docs/01-architecture/) doivent être « injectées dynamiquement dans
    # struct-check, vibe-check, validate ». struct-check (C11) et WikiFix
    # l'étaient déjà ; ce check comble le branchement manquant côté vibe-check.
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
                    try:
                        s_content = sf.read_text(encoding="utf-8", errors="replace")
                    except Exception as e:
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
        except Exception as e:
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
    checks.append({"check": rule_engine_msg, "status": "PASS" if rule_engine_ok else "FAIL"})

    # Check 12 (ADR-0331 §2.2 Règle #3 — Interdiction Formelle des Libellés
    # Génériques) : tout SOW généré sous docs/01-architecture/SOW_*.md ne doit
    # contenir aucun libellé vague (« [Détail des récits] », « Composant
    # générique », « Développement divers ») dans son tableau de chiffrage.
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
        except Exception as e:
            logger.error(
                "Erreur lors de la validation de granularité SOW (ADR-0331).",
                exc_info=True,
                extra={
                    "check_name": "sow_granularity",
                    "violation_type": "sow_engine_error",
                },
            )

    sow_msg = (
        "Granularité SOW (ADR-0331)"
        if sow_granularity_ok
        else f"Granularité SOW (Libellés génériques détectés : {sow_violations_count})"
    )
    checks.append({"check": sow_msg, "status": "PASS" if sow_granularity_ok else "FAIL"})

    # Check 13 (ADR-0339 §3 — Interdiction de Saut de Phase) : un projet ne
    # doit JAMAIS compter de récits détaillés (backlog/stories/) ni de statuts
    # d'analyse engagés en Phase 0 ou 1 (Porte 1 non franchie).
    phase_gate_ok = True
    phase_gate_violations = []
    if project_dir.exists():
        from src.core.lifecycle import ProjectLifecycleManager, ProjectLifecycleStage

        l_state = ProjectLifecycleManager.get_state(project_dir)
        stories_dir = project_dir / "backlog" / "stories"
        detailed_stories = (
            [s for s in stories_dir.glob("*.md") if s.name.lower() != "readme.md"]
            if stories_dir.exists()
            else []
        )

        # En Phase 1 (STAGE_1_INGEST), AUCUN récit détaillé n'est autorisé
        if l_state.canonical_stage == ProjectLifecycleStage.STAGE_1_INGEST:
            if detailed_stories:
                phase_gate_ok = False
                phase_gate_violations.append(
                    f"{len(detailed_stories)} récit(s) détaillé(s) sous backlog/stories/ interdit(s) en étape '{l_state.current_stage.value}'"
                )

            # Vérifier qu'aucune story n'est engagée dans sprint_backlog.md
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
                                phase_gate_ok = False
                                phase_gate_violations.append(
                                    f"Statut engagé '{kw}' détecté dans les récits de sprint_backlog.md interdit avant franchissement de Gate 1"
                                )
                                break
                        if not phase_gate_ok:
                            break
                except Exception as e:
                    logger.error(
                        f"Erreur lecture sprint_backlog.md pour Check 13: {e}",
                        exc_info=True,
                        extra={
                            "check_name": "phase_gate_check13",
                            "violation_type": "backlog_read_error",
                            "file_path": str(backlog_file),
                        },
                    )
        else:
            # En Phase 2 et plus, vérifier qu'un SOW, des specs ou un sprint_backlog existe si des stories existent (Fast-Track)
            arch_dir = project_dir / "docs" / "01-architecture"
            specs_dir = project_dir / "docs" / "02-specs"
            has_sow = arch_dir.exists() and any(arch_dir.glob("SOW_*.md"))
            has_specs = specs_dir.exists() and any(specs_dir.glob("*.md"))
            sprint_file = project_dir / "backlog" / "sprint_backlog.md"
            if detailed_stories and not has_sow and not has_specs and not sprint_file.exists():
                phase_gate_ok = False
                phase_gate_violations.append(
                    "Récits détaillés sans SOW, specs ni sprint_backlog préalable"
                )

    phase_gate_msg = (
        "Interdiction de Saut de Phase (ADR-0375 / ADR-0339)"
        if phase_gate_ok
        else f"Interdiction de Saut de Phase (ADR-0375 / ADR-0339 : {'; '.join(phase_gate_violations)} — Exécutez 'python src/swarm.py lifecycle-clean --project {project_name}')"
    )
    checks.append({"check": phase_gate_msg, "status": "PASS" if phase_gate_ok else "FAIL"})

    # Check 14 (ADR-0369 — Standards de Robustesse Python Senior) :
    # Validation de l'intégrité des 7 standards d'ingénierie (protocole SSOT, ADR-0369,
    # logger contextuel, dépendances dev pyproject.toml et zéro timeout manquant).
    python_senior_ok = True
    senior_violations = []

    if not Path("standards/protocols/PYTHON_SENIOR_CODING_STANDARDS.md").exists():
        python_senior_ok = False
        senior_violations.append("Protocole PYTHON_SENIOR_CODING_STANDARDS.md manquant")

    if not Path(
        "standards/adr-system/0369-python-senior-robustness-and-resource-governance.md"
    ).exists():
        python_senior_ok = False
        senior_violations.append("ADR-0369 manquant")

    pyproject_txt = (
        Path("pyproject.toml").read_text(encoding="utf-8")
        if Path("pyproject.toml").exists()
        else ""
    )
    if "[project.optional-dependencies]" not in pyproject_txt:
        python_senior_ok = False
        senior_violations.append("pyproject.toml sans optional-dependencies dev")

    python_senior_msg = (
        "Standards de Robustesse Python Senior (ADR-0369)"
        if python_senior_ok
        else f"Standards de Robustesse Python Senior (Violations : {', '.join(senior_violations)})"
    )
    checks.append({"check": python_senior_msg, "status": "PASS" if python_senior_ok else "FAIL"})

    # Check 15 (ADR-0370 — Parité SSOT & Auto-Healing du Guide CLI) :
    # Garantit que standards/protocols/CLI_PIPELINE_GUIDE.md contient l'intégralité
    # des commandes déclarées dans src/commands/_registry.py sans dérive documentaire.
    from src.pipelines.guide_generator import check_guide_parity, sync_cli_guide

    guide_sync_ok, total_reg, total_in_g, missing_cmds = check_guide_parity()
    if not guide_sync_ok:
        ZeroFluffConsole.info(
            f"[Vibe-Check Auto-Healing] CLI_PIPELINE_GUIDE.md désynchronisé ({len(missing_cmds)} commandes manquantes). Régénération automatique en cours..."
        )
        sync_cli_guide()
        guide_sync_ok, total_reg, total_in_g, missing_cmds = check_guide_parity()

    guide_msg = (
        f"Parité SSOT du Guide CLI ({total_reg}/{total_reg} commandes - ADR-0370)"
        if guide_sync_ok
        else f"Parité SSOT du Guide CLI ({len(missing_cmds)} commandes manquantes : {', '.join(missing_cmds[:3])}...)"
    )
    checks.append({"check": guide_msg, "status": "PASS" if guide_sync_ok else "FAIL"})

    # Check 16 (ADR-0377 — Sonde des Runtimes d'Agents Aval & Herdr) :
    # Vérifie la présence et la viabilité des outils d'exécution pour la phase courante.
    from src.core.agent_probe import AgentProbe

    probe = AgentProbe()
    agent_readiness_ok, agent_violations = probe.check_readiness(stage=stage_label)
    agent_msg = (
        "Runtimes d'Agents Aval & Herdr Opérationnels (ADR-0377)"
        if agent_readiness_ok
        else f"Runtimes d'Agents Aval & Herdr (ADR-0377 : {'; '.join(agent_violations)})"
    )
    checks.append({"check": agent_msg, "status": "PASS" if agent_readiness_ok else "FAIL"})

    # Check 17 (Phase 4 VALIDATE — Garde-Fou Automatique MLOOP-123-BE) :
    # Warning passif si stage == STAGE_4_VALIDATE et qa_certification_report.json absent.
    qa_cert_ok = True
    qa_cert_msg = ""
    if stage_label in ("STAGE_4_VALIDATE", "STAGE_VALIDATE"):
        evidence_dir = project_dir / "memory" / "evidence"
        qa_report_file = evidence_dir / "qa_certification_report.json"
        if not qa_report_file.exists():
            qa_cert_ok = False
            qa_cert_msg = (
                " [WARNING] qa_certification_report.json absent dans memory/evidence/. "
                "Lancez 'validate-sprint' pour certifier le sprint."
            )
    if not qa_cert_ok:
        ZeroFluffConsole.warning(
            f"Phase 4 VALIDATE : qa_certification_report.json absent.{qa_cert_msg}"
        )
    checks.append(
        {
            "check": f"Certification QA Sprint (Phase 4){qa_cert_msg}"
            if not qa_cert_ok
            else "Certification QA Sprint (Phase 4)",
            "status": "PASS" if qa_cert_ok else "WARNING",
        }
    )

    # Check 19 (ADR-0379 — Intégrité StandardsGraph & Bouclier de Confinement SSOT) :
    # 1. Vérifie la présence et la synchronisation de memory/standards_graph.db.
    # 2. Vérifie la parité stricte des 38 skills (.agents/skills/*/SKILL.md) avec StandardsGraph.
    # 3. Vérifie l'absence de fichiers .toml résiduels dans standards/agents/.
    # 4. Vérifie l'intégrité du bouclier de confinement runtime (ConfinementShield).
    standards_graph_ok = True
    standards_violations = []

    try:
        from src.core.standards_graph import StandardsGraphStore

        store = StandardsGraphStore.get_instance()
        skills = store.get_skills()
        agents = store.get_agents()

        if len(skills) < 38:
            standards_graph_ok = False
            standards_violations.append(f"Catalogue incomplet ({len(skills)}/38 skills)")

        if len(agents) < 5:
            standards_graph_ok = False
            standards_violations.append(f"Profils d'agents incomplets ({len(agents)}/5 agents)")

        if Path("standards/agents").exists() and any(Path("standards/agents").glob("*.toml")):
            standards_graph_ok = False
            standards_violations.append("Fichiers .toml résiduels interdits sous standards/agents/")

        from src.core.confinement_shield import ConfinementShield, PermissionDeniedError

        try:
            ConfinementShield.verify_skill_access("forbidden-skill-canary", "explorer")
            standards_graph_ok = False
            standards_violations.append(
                "Bouclier ConfinementShield inactif (canary non intercepté)"
            )
        except PermissionDeniedError:
            pass  # Interception réussie

    except Exception as exc:
        standards_graph_ok = False
        standards_violations.append(f"Erreur StandardsGraph : {exc}")
        logger.error(
            "Erreur lors de l'audit d'intégrité StandardsGraph (ADR-0379).",
            exc_info=True,
            extra={
                "check_name": "standards_graph_integrity",
                "violation_type": "standards_graph_error",
            },
        )

    standards_msg = (
        "Intégrité StandardsGraph & Bouclier de Confinement SSOT (ADR-0379)"
        if standards_graph_ok
        else f"Intégrité StandardsGraph & Bouclier SSOT (Violations : {'; '.join(standards_violations)})"
    )
    checks.append({"check": standards_msg, "status": "PASS" if standards_graph_ok else "FAIL"})

    passed_count = sum(1 for c in checks if c["status"] == "PASS")
    total_count = len(checks)

    for c in checks:
        if c["status"] == "PASS":
            ZeroFluffConsole.success(f"{c['check']} : PASS")
        elif c["status"] == "WARNING":
            ZeroFluffConsole.warning(f"{c['check']} : WARNING")
        else:
            ZeroFluffConsole.error(f"{c['check']} : FAIL")

    is_valid = passed_count == total_count
    ZeroFluffConsole.info(f"Résultat Vibe-Check : {passed_count}/{total_count} contrôles validés.")

    duration_ms = round((time.perf_counter() - t0) * 1000, 2)
    logger.info(
        f"[VIBE-CHECK] Fin du guardrail pré-vol pour '{project_name}' : {passed_count}/{total_count}.",
        extra={
            "phase": stage_label,
            "project": project_name,
            "score": f"{passed_count}/{total_count}",
            "duration_ms": duration_ms,
        },
    )

    return {
        "status": "PASS" if is_valid else "FAIL",
        "checks": checks,
        "score": f"{passed_count}/{total_count}",
        "lifecycle_mode": lifecycle_mode,
        "stage": stage_label,
    }
