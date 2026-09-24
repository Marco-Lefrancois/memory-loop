"""
_sync_run.py — Sous-module Sync : orchestrateur run_sync.

Responsabilités :
  - run_sync : point d'entrée principal du pipeline de synchronisation complet.

Imports lazy (dans le corps de run_sync) :
  - src.loop_mem.db           : sync_project_lexicon_from_disk, index_project_docs_to_fts5
  - src.pipelines.struct_checker : StructCheckEngine

ADR-0202 (RULE-AST-01) : ≤ 300 L / 15 Ko.
ADR-0369              : aucun appel réseau direct — délégué aux sous-modules.
Q5 (Grill)            : from src.state import LoopState, JournalEntry top-level (dépend du shim 173).
                        db lazy L480 (dépend du shim 178). ZÉRO import lifecycle.

Note logger : run_sync utilise sys.modules["src.pipelines.sync"].logger pour garantir
que patch.object(sync, "logger") dans test_sync_logging.py intercepte tous les appels
(compatibilité MLOOP-141-BE sans modifier les tests existants).
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

from src.state import LoopState, JournalEntry  # top-level — dépend du shim MLOOP-173-BE
from src.pipelines.wikifix import WikiFixAgent
from src.pipelines.graphify.agent import GraphifyAgent
from src.cli import ZeroFluffConsole
from src.utils.logger import get_logger

from src.pipelines.sync._sync_docs import (
    sync_project_directives,
    sync_open_questions,
    sync_sprint_backlog,
)
from src.pipelines.sync._sync_graph import (
    sync_live_reference_wikis,
    sync_hypergraph,
)

# Logger propre au sous-module (utilisé pour les imports et le nom canonique)
logger = get_logger("pipelines.sync")


def _get_logger():
    """
    Retourne le logger effectif en résolvant dynamiquement src.pipelines.sync.logger.

    Cela garantit que patch.object(sync, "logger") dans test_sync_logging.py
    sera honoré — le Mock remplace l'attribut dans __init__.py, et cette fonction
    le retrouve via sys.modules au moment de l'appel.
    """
    sync_mod = sys.modules.get("src.pipelines.sync")
    if sync_mod is not None:
        return getattr(sync_mod, "logger", logger)
    return logger


def run_sync(
    project_name: str,
    state: LoopState,
    project_path: Path,
    details_msg: str | None = None,
    fast_mode: bool = False,
    verbose: bool = False,
    incremental: bool = False,
    story_filter: str | None = None,
) -> LoopState:
    """
    Orchestrateur principal du pipeline de synchronisation mLoop.

    Séquence :
      1. Live Git-Sync wikis (référence/)
      2. Directives projet (ADRs → business.md)
      3. Sprint backlog SSOT
      4. Questions ouvertes → wayfinder + déblocage stories
      5. Hypergraphe (ADR-0343)
      6. Struct-check consultatif (ADR-0338)
      7. Fact-Search FTS5 (import lazy → dépend du shim MLOOP-178-BE)
      8. WikiFix audit sémantique
      9. Graphify (si pas fast_mode)
     10. Sauvegarde audit session
    """
    _log = _get_logger()

    ZeroFluffConsole.section(f"Synchronisation et Validation - {project_name}")
    t_total = time.perf_counter()
    _log.info(
        f"[SYNC] Début de la synchronisation pour '{project_name}'.",
        extra={
            "subsystem": "orchestrator",
            "project": project_name,
            "fast_mode": fast_mode,
        },
    )

    # [1] Live Git-Sync wikis
    sync_live_reference_wikis(project_name, project_path)

    # [2] Directives
    sync_project_directives(project_name, project_path)

    # [3] Sprint backlog
    sync_sprint_backlog(project_name, project_path)

    # [4] Questions ouvertes
    sync_open_questions(project_name, project_path)

    # [5] Hypergraphe
    sync_hypergraph(project_name, project_path, incremental=incremental, verbose=verbose)

    # [6] Struct-check consultatif (ADR-0338 — non-bloquant)
    try:
        from src.pipelines.struct_checker import StructCheckEngine

        struct_engine = StructCheckEngine(project_path)
        story_files = sorted(project_path.glob("backlog/stories/**/*.md"))
        struct_violations_found = False
        for sf in story_files:
            if story_filter and story_filter not in sf.name:
                continue
            report = struct_engine.check_file(sf, strict=False)
            for v in report.violations:
                if v.severity == "BLOCKING":
                    ZeroFluffConsole.warning(
                        f"[struct-check] {sf.name} : [{v.check_id}] {v.message}"
                    )
                    struct_violations_found = True
        if struct_violations_found:
            ZeroFluffConsole.warning(
                "[struct-check] Violations structurelles détectées."
                " Exécuter 'python src/swarm.py struct-check --verbose' pour le détail."
            )
    except Exception as _struct_err:
        ZeroFluffConsole.warning(f"[struct-check] Ignoré (erreur non-bloquante) : {_struct_err}")
        _log.error(
            "Erreur non-bloquante lors du struct-check consultatif.",
            exc_info=True,
            extra={"subsystem": "struct", "project": project_name},
        )

    # [7] Fact-Search FTS5 — import lazy (dépend du shim MLOOP-178-BE)
    try:
        from src.loop_mem.db import sync_project_lexicon_from_disk, index_project_docs_to_fts5

        lex_count = sync_project_lexicon_from_disk(project_name)
        chunks_count = index_project_docs_to_fts5(project_name)
        if verbose or not fast_mode:
            ZeroFluffConsole.info(
                f"[Fact-Search FTS5] {chunks_count} chunks documentaires"
                f" et {lex_count} termes du lexique indexés."
            )
    except Exception as _fs_err:
        ZeroFluffConsole.warning(f"[Fact-Search FTS5] Indexation ignorée : {_fs_err}")
        _log.error(
            "Erreur non-bloquante lors de l'indexation FTS5.",
            exc_info=True,
            extra={"subsystem": "fts5", "project": project_name},
        )

    # [8] WikiFix
    try:
        wf_kwargs: dict = {"verbose": verbose}
        if story_filter is not None:
            wf_kwargs["story_filter"] = story_filter
        state = WikiFixAgent().execute(state, **wf_kwargs)
    except Exception as _wf_err:
        ZeroFluffConsole.warning(f"[WikiFix] Erreur non-bloquante lors de l'audit : {_wf_err}")
        _log.error(
            "Erreur non-bloquante lors de l'audit WikiFix.",
            exc_info=True,
            extra={"subsystem": "wikifix", "project": project_name},
        )

    # [9] Graphify (hors fast_mode)
    if not fast_mode:
        try:
            state = GraphifyAgent().execute(state)
        except Exception as _gf_err:
            ZeroFluffConsole.warning(
                f"[Graphify] Erreur non-bloquante lors de la modélisation : {_gf_err}"
            )
            _log.error(
                "Erreur non-bloquante lors de la modélisation Graphify.",
                exc_info=True,
                extra={"subsystem": "graphify", "project": project_name},
            )

    # [10] Audit session
    try:
        state.save_to_audit(project_path)
    except Exception as _audit_err:
        ZeroFluffConsole.warning(f"[Audit] Impossible de sauvegarder l'audit : {_audit_err}")
        _log.error(
            "Impossible de sauvegarder l'audit de session (save_to_audit).",
            exc_info=True,
            extra={"subsystem": "audit", "project": project_name},
        )

    # [11] Cline Memory Bank & Rules Mirror Sync (MLOOP-260-BE, MLOOP-261-BE)
    try:
        from src.bridges.cline.memory_bank_bridge import MemoryBankBridge
        from src.bridges.cline.rules_mirror import ClineRulesMirror

        ws_root = project_path.resolve()
        while ws_root.parent != ws_root and not (ws_root / "Projects").exists() and not (ws_root / "standards").exists():
            ws_root = ws_root.parent

        MemoryBankBridge(workspace_root=ws_root).sync_all()
        ClineRulesMirror(workspace_root=ws_root).sync()
    except Exception as _cline_err:
        _log.debug("Synchronisation Cline pass-through ignorée : %s", _cline_err)

    duration_ms = round((time.perf_counter() - t_total) * 1000, 2)
    _log.info(
        f"[SYNC] Fin de la synchronisation pour '{project_name}'.",
        extra={
            "subsystem": "orchestrator",
            "project": project_name,
            "duration_ms": duration_ms,
            "fast_mode": fast_mode,
        },
    )

    return state
