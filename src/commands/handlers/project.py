"""Handlers Projet : init, resume, focus, vibe-check."""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from src.cli import ZeroFluffConsole
from src.state import ProjectLayout
from src.utils.blueprints import BlueprintLoader

if TYPE_CHECKING:
    import argparse
    from src.state import LoopState


def handle_init(args: argparse.Namespace, state: LoopState, project_path: Path) -> int:
    """Initialise l'arborescence d'un nouveau projet (Loi des 3 Piliers & ADR-0375)."""
    p = project_path if project_path else (Path("Projects") / state.project_name)
    (p / ProjectLayout.REFERENCE).mkdir(parents=True, exist_ok=True)
    for subdir in ProjectLayout.DOCS_SUBDIRS:
        (p / ProjectLayout.DOCS / subdir).mkdir(parents=True, exist_ok=True)

    idx = p / ProjectLayout.DOCS / "index.md"
    if not idx.exists():
        content = BlueprintLoader.render("project_index_template.md", {"PROJECT_NAME": state.project_name})
        with open(idx, "w", encoding="utf-8") as f:
            f.write(content)

    (p / ProjectLayout.BACKLOG / "stories").mkdir(parents=True, exist_ok=True)
    sb = p / ProjectLayout.BACKLOG / ProjectLayout.SPRINT_BACKLOG_FILE
    if not sb.exists():
        content = BlueprintLoader.render("project_sprint_backlog_template.md", {"PROJECT_NAME": state.project_name})
        with open(sb, "w", encoding="utf-8") as f:
            f.write(content)

    oq_client = p / ProjectLayout.DOCS / "04-transverse" / "00-questions-ouvertes-client.md"
    if not oq_client.exists():
        content = BlueprintLoader.render(
            "project_open_questions_template.md",
            {
                "TARGET_AUDIENCE": "Client / LÃ©gal",
                "PROJECT_NAME": state.project_name,
                "DESCRIPTION": "Ce document regroupe exclusivement les points d'arbitrage d'affaires et lÃ©gaux.",
            },
        )
        with open(oq_client, "w", encoding="utf-8") as f:
            f.write(content)

    oq_dev = p / ProjectLayout.DOCS / "04-transverse" / "00-questions-ouvertes-devteam.md"
    if not oq_dev.exists():
        content = BlueprintLoader.render(
            "project_open_questions_template.md",
            {
                "TARGET_AUDIENCE": "Ã‰quipe Dev",
                "PROJECT_NAME": state.project_name,
                "DESCRIPTION": "Ce document regroupe exclusivement les dÃ©fis et verrous techniques.",
            },
        )
        with open(oq_dev, "w", encoding="utf-8") as f:
            f.write(content)

    (p / ProjectLayout.MEMORY).mkdir(parents=True, exist_ok=True)

    # 1. README.md racine
    readme_path = p / "README.md"
    if not readme_path.exists():
        content = BlueprintLoader.render("project_readme_template.md", {"PROJECT_NAME": state.project_name})
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(content)

    # 2. AGENTS.md racine (100% Agnostique & OrientÃ© DÃ©veloppeur / Assistant IA)
    agents_path = p / "AGENTS.md"
    if not agents_path.exists():
        content = BlueprintLoader.render("project_agents_template.md", {"PROJECT_NAME": state.project_name})
        with open(agents_path, "w", encoding="utf-8") as f:
            f.write(content)

    # 3. opencode.json racine (100% Agnostique & Propre)
    opencode_path = p / "opencode.json"
    if not opencode_path.exists():
        content = BlueprintLoader.render("project_opencode_template.json", {"PROJECT_NAME": state.project_name})
        with open(opencode_path, "w", encoding="utf-8") as f:
            f.write(content)

    # 4. .gitignore racine
    gitignore_path = p / ".gitignore"
    if not gitignore_path.exists():
        content = BlueprintLoader.render("project_gitignore_template.gitignore")
        with open(gitignore_path, "w", encoding="utf-8") as f:
            f.write(content)

    # Initialisation dÃ©terministe du cycle de vie projet (ADR-0375 / ADR-0378)
    from src.core.lifecycle import ProjectLifecycleManager, ProjectLifecycleStage
    ProjectLifecycleManager.init_lifecycle(p, initial_stage=ProjectLifecycleStage.STAGE_1_INGEST)

    print("\n" + "=" * 80)
    print(f"ðŸš€ INITIALISATION DU PROJET : {state.project_name} (ADR-0100 & ADR-0375)")
    print("=" * 80)
    print(f"âœ” Arborescence des 3 Piliers initialisÃ©e sous Projects/{state.project_name}/ :")
    print(f"  ðŸ“ {ProjectLayout.REFERENCE}/                     âž” Staging brut local (exclu de Git, prÃªt pour dÃ©pÃ´t)")
    print(f"  ðŸ“ {ProjectLayout.DOCS}/                          âž” SSOT Documentaire Markdown (ADR-0102 & ADR-0332) :")
    print(f"     â”œâ”€â”€ {ProjectLayout.DOCS_INGESTED}/               âž” Destination de la conversion MarkItDown")
    print(f"     â”œâ”€â”€ {ProjectLayout.DOCS_ARCHITECTURE}/           âž” Futurs SOW / T-Shirt / ADRs (Phase 2+)")
    print(f"     â”œâ”€â”€ {ProjectLayout.DOCS_RULES}/         âž” RÃ¨gles d'affaires atomiques RM-XXX")
    print(f"     â”œâ”€â”€ {ProjectLayout.DOCS_MODELS}/                 âž” ModÃ¨les de donnÃ©es DDD et entitÃ©s")
    print(f"     â”œâ”€â”€ {ProjectLayout.DOCS_TRANSVERSE}/             âž” Questions ouvertes client / dev")
    print(f"     â””â”€â”€ {ProjectLayout.DOCS_ASSETS}/                 âž” Maquettes SVG & schÃ©mas versionnÃ©s (ADR-0332)")
    print(f"  ðŸ“ {ProjectLayout.BACKLOG}/                       âž” Backlog Agile (verrouillÃ© en Phase 1 - Check 13)")
    print(f"  ðŸ“ {ProjectLayout.MEMORY}/                        âž” TraÃ§abilitÃ© & Machine Ã  Ã©tats du cycle de vie")
    print(f"\nâœ” Fichiers agnostiques prÃªts : README.md, AGENTS.md, opencode.json, .gitignore")
    print(f"âœ” Cycle de vie initialisÃ© : Ã‰tape active = STAGE_1_INGEST (Phase 1 : INGEST & EXPLORE)")
    print("\n" + "-" * 80)
    print("ðŸ‘‰ INTERVENTION HUMAINE REQUISE (Prochaine action) :")
    print("-" * 80)
    print(f"1. DÃ©posez vos documents bruts clients (PDF, Word, Excel, Maquettes SVG...) dans :")
    print(f"   ðŸ“‚ Projects/{state.project_name}/reference/")
    print(f"\n2. DÃ¨s vos fichiers dÃ©posÃ©s, lancez l'ingestion normalisÃ©e :")
    print(f"   âš¡ python src/swarm.py ingest --project {state.project_name}")
    print(f"\n3. AprÃ¨s ingestion, validez la Porte 1 pour dÃ©bloquer la Phase 2 :")
    print(f"   ðŸšª python src/swarm.py gate-approve --project {state.project_name} --gate 1 --approver \"<Votre Nom>\"")
    print("=" * 80 + "\n")
    return 0


def handle_resume(args: argparse.Namespace, state: LoopState, project_path: Path) -> int:
    """Restaure la session anti-amnÃ©sie."""
    from src.pipelines.session_resume import run_session_resume
    run_session_resume(state.project_name)
    return 0


def handle_focus(args: argparse.Namespace, state: LoopState, project_path: Path) -> int:
    """Verrouille l'attention sur un rÃ©cit spÃ©cifique."""
    from src.pipelines.focus import set_focus
    from src.pipelines.sync import run_sync
    set_focus(args.project, args.story)
    run_sync(
        args.project,
        state,
        project_path,
        fast_mode=True,
        story_filter=getattr(args, "story", None),
        verbose=getattr(args, "verbose", False),
    )
    return 0


def handle_vibe_check(args: argparse.Namespace, state: LoopState, project_path: Path) -> int:
    """Guardrail prÃ©-vol de la session (gouvernance de phase ADR-0339)."""
    from src.pipelines.vibe_check import run_vibe_check
    stage = getattr(args, "stage", None) or getattr(args, "phase", None)
    res = run_vibe_check(state.project_name, stage=stage)
    return 0 if res.get("status") == "PASS" else 1


_HOOK_MANAGED_MARKER = "mLoop Git Pre-Commit Hook"

# Racine du framework mLoop (â€¦/src/commands/handlers/project.py âž” racine).
_FRAMEWORK_ROOT = Path(__file__).resolve().parents[3]


def _resolve_git_root(project_path: Path) -> Path | None:
    """RÃ©sout la racine du dÃ©pÃ´t Git cible : projet client s'il est versionnÃ©,
    sinon la racine du framework (auto-dÃ©veloppement mLoop, MLOOP-105-BE)."""
    if (project_path / ".git").exists():
        return project_path
    if (_FRAMEWORK_ROOT / ".git").exists():
        return _FRAMEWORK_ROOT
    return None


def handle_install_hooks(args: argparse.Namespace, state: LoopState, project_path: Path) -> int:
    """Installe ou dÃ©sinstalle le hook Git pre-commit dÃ©terministe (MLOOP-105-BE).

    Le hook gÃ©nÃ©rÃ© filtre les fichiers indexÃ©s (``git diff --cached``) et
    dÃ©clenche ``code-check`` sur les sources Python ainsi que ``struct-check``
    sur les rÃ©cits Markdown, avec bypass souverain via ``MLOOP_SKIP_HOOKS``.
    """
    uninstall = getattr(args, "uninstall", False)
    git_root = _resolve_git_root(project_path)
    if git_root is None:
        ZeroFluffConsole.warning(
            f"Ni le projet '{state.project_name}' ni le framework mLoop ne sont des dÃ©pÃ´ts Git (.git introuvable)."
        )
        return 1
    hooks_dir = git_root / ".git" / "hooks"
    pre_commit_file = hooks_dir / "pre-commit"

    if uninstall:
        return _uninstall_hook(pre_commit_file)

    swarm_py = _FRAMEWORK_ROOT / "src" / "swarm.py"
    hook_content = BlueprintLoader.render(
        "git_pre_commit_hook.sh",
        {
            "ROOT_DIR": git_root.as_posix(),
            "SWARM_PY": swarm_py.as_posix(),
            "PROJECT_NAME": state.project_name,
        },
    )

    if pre_commit_file.exists():
        existing = pre_commit_file.read_text(encoding="utf-8")
        if _HOOK_MANAGED_MARKER not in existing:
            ZeroFluffConsole.warning(
                f"Un hook pre-commit Ã©tranger existe dÃ©jÃ  ({pre_commit_file}). "
                "Sauvegardez-le ou retirez-le manuellement avant installation."
            )
            return 1
        if existing == hook_content:
            ZeroFluffConsole.success(f"Hook Git pre-commit dÃ©jÃ  Ã  jour et opÃ©rationnel : {pre_commit_file}")
            return 0

    hooks_dir.mkdir(parents=True, exist_ok=True)
    with open(pre_commit_file, "w", encoding="utf-8", newline="\n") as f:
        f.write(hook_content)
    ZeroFluffConsole.success(f"Hook Git pre-commit installÃ© et opÃ©rationnel : {pre_commit_file}")
    return 0


def _uninstall_hook(pre_commit_file: Path) -> int:
    """Retire le hook gÃ©rÃ© par mLoop, sans jamais toucher un hook Ã©tranger."""
    if not pre_commit_file.exists():
        ZeroFluffConsole.success("Aucun hook pre-commit installÃ© â€” rien Ã  dÃ©sinstaller.")
        return 0
    existing = pre_commit_file.read_text(encoding="utf-8")
    if _HOOK_MANAGED_MARKER not in existing:
        ZeroFluffConsole.warning(
            f"Le hook pre-commit prÃ©sent ({pre_commit_file}) n'est pas gÃ©rÃ© par mLoop. "
            "DÃ©sinstallation refusÃ©e par sÃ©curitÃ©."
        )
        return 1
    pre_commit_file.unlink()
    ZeroFluffConsole.success(f"Hook Git pre-commit mLoop dÃ©sinstallÃ© : {pre_commit_file}")
    return 0


def handle_guide(args: argparse.Namespace, state: LoopState | None, project_path: Path | None) -> int:
    """Affiche le guide d'utilisation du pipeline CLI mLoop par phase ou synchronise le guide SSOT."""
    if getattr(args, "sync", False):
        from src.pipelines.guide_generator import sync_cli_guide
        ok, msg = sync_cli_guide()
        if ok:
            ZeroFluffConsole.success(msg)
            return 0
        else:
            ZeroFluffConsole.error(msg)
            return 1

    ZeroFluffConsole.section("GUIDE D'UTILISATION DU PIPELINE CLI â€” MEMORY LOOP (mLoop)")

    phases_data = {
        "ingest": {
            "title": "ðŸŸ  Phase 1 : INGEST & EXPLORE (Ingestion & Exploration Documentaire)",
            "commands": [
                ("ingest", "IngÃ©rer les briefs et documents initiaux sous docs/00-ingested/"),
                ("research", "Recherche et analyse documentaire prÃ©liminaire"),
                ("crawl", "Web Crawler automatique avec dÃ©tection Markdown Twin"),
                ("markitdown_convert", "Conversion multi-formats (PDF, Office, etc.) vers Markdown"),
                ("extract", "Extraction dÃ©clarative YAML vers Knowledge Abstracts (ADR-0342)"),
                ("agentic-extract", "Extraction sÃ©mantique de rÃ¨gles mÃ©tier (RM-XXX)"),
                ("code-init", "Initialisation de l'indexation AST CodeGraph"),
            ]
        },
        "plan": {
            "title": "ðŸ”µ Phase 2 : PLAN & ANALYSE (Planification, Architecture, Grill & DÃ©coupage)",
            "commands": [
                ("to-tshirt", "GÃ©nÃ©rer un Dimensionnement BudgÃ©taire d'avant-projet (T-Shirt Size)"),
                ("to-sow", "GÃ©nÃ©rer l'Ã‰noncÃ© des Travaux (SOW) contractuel sous docs/01-architecture/"),
                ("grill-project", "Cadrage contradictoire macro d'avant-projet (Loi 25, SSO, exclusions)"),
                ("focus", "Verrouiller l'attention sur une User Story (--story <ID>)"),
                ("grill", "Entrevue interactive ciblÃ©e Grill-with-Docs & enregistrement d'ADRs"),
                ("to-spec", "Distiller une discussion en spÃ©cification d'architecture"),
                ("to-tickets", "DÃ©couper une spec en Ã©bauches de rÃ©cits verticaux (Palier 1 DRAFT)"),
                ("wayfinder", "Meta-Orchestration (carte de dÃ©cisions dans le brouillard)"),
                ("chunk", "DÃ©coupage sÃ©mantique d'un document massif (ADR-0323)"),
                ("hyper-query", "Interroger l'hypergraphe pour une User Story ou un concept (ADR-0343)"),
                ("archify", "GÃ©nÃ©ration et validation de diagrammes d'architecture interactifs vectoriels"),
            ]
        },
        "build": {
            "title": "ðŸŸ¢ Phase 3 : BUILD / DEV (DÃ©veloppement & Workers Multi-Agents)",
            "commands": [
                ("self-dev", "Auto-Ã©volution du framework mLoop (TDD Red-Green-Refactor)"),
                ("confidence", "Ã‰valuation du score de confiance prÃ©-Ã©dition (Confidence Gate)"),
                ("worker-spawn", "Instanciation d'un sous-agent Herdr isolÃ© (Clean Slate)"),
                ("worker-status", "Affichage du statut des workers Herdr actifs"),
                ("worker-close", "Fermeture propre et libÃ©ration des ressources d'un worker"),
                ("code-impact", "Calcul du rayon d'impact (Blast Radius) d'un symbole"),
                ("code-affected", "Identification des tests unitaires affectÃ©s par un changement"),
            ]
        },
        "validate": {
            "title": "ðŸŸ£ Phase 4 : VALIDATE / QA (Validation SÃ©mantique & Guardrails)",
            "commands": [
                ("wikifix", "Audit de cohÃ©rence SSOT, rÃ¨gles mÃ©tier et intÃ©gritÃ© INVEST"),
                ("struct-check", "Gatekeeper structurel Read-Only prÃ©-Sentinel (hiÃ©rarchie H2/H3/H4, format listes, Gold Standard diff)"),
                ("rubber-duck", "Audit contradictoire Sentinel en lecture seule (4 Piliers Gherkin)"),
                ("audit-loop", "Validation dÃ©terministe des 3 couches de guardrails"),
                ("aoep", "Ã‰valuation de la gouvernance d'Ã©tat persistant AOEP-v0"),
                ("eval", "ExÃ©cution de la suite d'Ã©valuations agentiques"),
                ("worker-harvest", "Moisson synchrone des livrables Ã©crits par un worker"),
            ]
        },
        "ship": {
            "title": "ðŸ”´ Phase 5 : SHIP & SYNC (Synchronisation & Distribution)",
            "commands": [
                ("sync", "Synchronisation globale (WikiFix + Graphify + Hypergraphe + SQLite FTS5)"),
                ("export-obsidian", "Exporter l'hypergraphe en coffre Obsidian avec wikilinks (ADR-0343)"),
                ("jira_sync", "Synchronisation bidirectionnelle avec Jira Cloud"),
                ("cycle-status", "Bilan de santÃ© et statut d'avancement des 5 phases"),
                ("calibrate", "Auto-Ã©talonnage continu de l'Ã©cosystÃ¨me mLoop (8 axes)"),
                ("plugin-validate", "Validation de conformitÃ© Agent Plugins 1.0"),
                ("plugin-export", "Empaquetage portable du plugin mLoop pour distribution"),
            ]
        }
    }

    target_phase = getattr(args, "phase", None)
    # Mapping d'alias pour les anciens noms
    if target_phase in ("sow", "spec"):
        target_phase = "ingest" if target_phase == "spec" else "plan"
    selected_phases = [target_phase] if target_phase and target_phase in phases_data else list(phases_data.keys())

    print("\nCommandes universelles de dÃ©marrage (Boot Sequence) :")
    print("  1. python src/swarm.py resume --project <nom_projet>")
    print("  2. python src/swarm.py vibe-check --project <nom_projet>")
    print("  3. python src/swarm.py focus --project <nom_projet> --story <story_id>\n")

    for pkey in selected_phases:
        pinfo = phases_data[pkey]
        print(f"\n{pinfo['title']}")
        print("â”€" * 70)
        for cmd, desc in pinfo["commands"]:
            print(f"  â€¢ python src/swarm.py {cmd:<18} : {desc}")

    print("\n" + "â•" * 70)
    print("ðŸ“– Guide normatif complet : standards/protocols/CLI_PIPELINE_GUIDE.md")
    print("âŒ¨ï¸  OpenCode Dispatcher   : /loop <action> [arguments] (ex: /loop sync)")
    print("â•" * 70 + "\n")
    return 0


def handle_sync_antigravity(args: argparse.Namespace, state: LoopState, project_path: Path) -> int:
    """Synchronise les tokens et interactions de l'IDE Antigravity vers le Token Ledger."""
    from src.utils.antigravity_meter import AntigravityMeter
    ZeroFluffConsole.info("Synchronisation des sessions Antigravity (Google DeepMind)...")
    conv_id = getattr(args, "conversation_id", None)
    all_convs = getattr(args, "all", False)
    res = AntigravityMeter.sync(conversation_id=conv_id, all_conversations=all_convs)
    ZeroFluffConsole.success(
        f"Synchronisation terminÃ©e : {res.get('synced_turns', 0)} tour(s) synchronisÃ©(s) "
        f"({res.get('total_tokens', 0):,} tokens, ${res.get('total_cost_usd', 0.0):.4f} USD)."
    )
    return 0


def handle_gate_approve(args: argparse.Namespace, state: LoopState, project_path: Path) -> int:
    """Valide formellement le passage d'une Porte de Gouvernance (Gate 0 Ã  5)."""
    from src.core.lifecycle import ProjectLifecycleManager, GATE_DEFINITIONS
    gate_num = getattr(args, "gate", None)
    if gate_num is None:
        ZeroFluffConsole.error("Le paramÃ¨tre --gate <0..5> est obligatoire.")
        return 1

    try:
        gate_num = int(gate_num)
    except ValueError:
        ZeroFluffConsole.error(f"NumÃ©ro de porte invalide : '{gate_num}'. Doit Ãªtre un entier entre 0 et 5.")
        return 1

    approver = getattr(args, "approver", None) or "User"
    notes = getattr(args, "notes", "") or ""

    try:
        new_state = ProjectLifecycleManager.approve_gate(
            project_path=project_path,
            gate_number=gate_num,
            approver=approver,
            notes=notes,
        )
        gate_info = GATE_DEFINITIONS.get(gate_num, {})
        ZeroFluffConsole.success(
            f"Porte franchie avec succÃ¨s : {gate_info.get('name', f'Gate {gate_num}')} !"
        )
        ZeroFluffConsole.info(
            f"Nouvelle Ã©tape active : {new_state.current_stage.value} pour le projet '{project_path.name}'."
        )
        return 0
    except ValueError as e:
        ZeroFluffConsole.error(f"[GATE ERROR] {e}")
        return 1


def handle_lifecycle_status(args: argparse.Namespace, state: LoopState, project_path: Path) -> int:
    """Affiche le statut d'Ã©tape et l'historique des portes du cycle de vie projet (ADR-0339, ADR-0375, ADR-0378)."""
    from src.core.lifecycle import ProjectLifecycleManager, STAGE_NAMES, GATE_DEFINITIONS, ProjectLifecycleStage
    l_state = ProjectLifecycleManager.get_state(project_path)

    ZeroFluffConsole.section(f"Cycle de Vie Projet : {project_path.name} (ADR-0339 & ADR-0375)")
    stage_desc = STAGE_NAMES.get(l_state.current_stage, l_state.current_stage.value)
    ZeroFluffConsole.info(f"Ã‰tape Active : {l_state.current_stage.value} ({stage_desc})")

    # MÃ©tadonnÃ©es dÃ©taillÃ©es Phase 1 (ADR-0378)
    if l_state.canonical_stage == ProjectLifecycleStage.STAGE_1_INGEST:
        ref_dir = project_path / ProjectLayout.REFERENCE
        raw_count = len([f for f in ref_dir.rglob("*") if f.is_file()]) if ref_dir.exists() else 0
        ingested_dir = project_path / ProjectLayout.DOCS / ProjectLayout.DOCS_INGESTED
        ingested_count = len(list(ingested_dir.glob("*.md"))) if ingested_dir.exists() else 0
        assets_dir = project_path / ProjectLayout.DOCS / ProjectLayout.DOCS_ASSETS
        assets_count = len([f for f in assets_dir.rglob("*") if f.is_file()]) if assets_dir.exists() else 0

        stories_dir = project_path / ProjectLayout.BACKLOG / "stories"
        premature_stories = [f.name for f in stories_dir.glob("*.md") if f.name.lower() != "readme.md"] if stories_dir.exists() else []
        c13_status = "PASS (0 story)" if not premature_stories else f"WARN ({len(premature_stories)} story(ies) prÃ©maturÃ©e(s) dÃ©tectÃ©e(s))"

        print("\nðŸ“Š MÃ©tadonnÃ©es Phase 1 (INGEST & EXPLORE) :")
        print(f"  ðŸ“ Fichiers bruts dÃ©posÃ©s (reference/) : {raw_count}")
        print(f"  ðŸ“„ Documents Markdown normalisÃ©s (docs/00-ingested/) : {ingested_count}")
        print(f"  ðŸŽ¨ Actifs visuels & maquettes (docs/05-assets/) : {assets_count}")
        print(f"  ðŸ›¡ï¸ Check 13 Anti-Ghost-Bias (backlog/stories/) : {c13_status}")

    print("\nðŸšª Historique des Portes de Gouvernance :")
    for g_num, g_def in sorted(GATE_DEFINITIONS.items()):
        rec = l_state.gates.get(str(g_num))
        if rec:
            print(f"  âœ” [APPROUVÃ‰E] {g_def['name']} â€” par {rec.approver} le {rec.approved_at_utc[:19]} ({rec.notes or 'Sans note'})")
        else:
            is_next = (g_def["from_stage"] == l_state.current_stage)
            badge = "â³ [EN COURS]" if is_next else "âšª [VERROUILLÃ‰E]"
            print(f"  {badge} {g_def['name']} â€” {g_def['description']}")

    return 0


def handle_lifecycle_clean(args: argparse.Namespace, state: LoopState, project_path: Path) -> int:
    """Archive de maniÃ¨re rÃ©versible les stories orphelines crÃ©Ã©es prÃ©maturÃ©ment (ZÃ©ro Ghost Bias / L-08)."""
    from src.core.lifecycle import ProjectLifecycleManager
    confirm = getattr(args, "confirm", False)
    if not confirm:
        ZeroFluffConsole.warning(
            "OpÃ©ration refusÃ©e : le flag --confirm est requis pour archiver les stories prÃ©maturÃ©es.\n"
            "ExÃ©cutez : python src/swarm.py lifecycle-clean --confirm"
        )
        return 1
    res = ProjectLifecycleManager.clean_premature_stories(project_path, confirm=True)
    archive_dir = res.get("archive_dir")
    if res.get("deleted_stories"):
        ZeroFluffConsole.success(
            f"Archivage terminÃ© : {len(res['deleted_stories'])} story(ies) archivÃ©e(s) : {res['deleted_stories']}"
        )
    if res.get("deleted_evidence"):
        ZeroFluffConsole.success(
            f"EvidencePacks archivÃ©s : {len(res['deleted_evidence'])} fichier(s)."
        )
    if archive_dir:
        ZeroFluffConsole.info(f"Dossier d'archive sÃ©curisÃ© : {archive_dir}")
    ZeroFluffConsole.info(res.get("message", "Nettoyage complÃ©tÃ©."))
    return 0



