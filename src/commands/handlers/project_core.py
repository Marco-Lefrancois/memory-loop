"""Handlers Projet — Core (init, resume, focus, vibe-check, install-hooks)."""
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
