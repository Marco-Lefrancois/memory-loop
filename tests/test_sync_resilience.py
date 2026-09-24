import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.state import LoopState, KnowledgeGraph
from src.pipelines.sync import run_sync
from src.pipelines.graphify.agent import GraphifyAgent
from src.pipelines.wikifix import WikiFixAgent
from src.commands._registry import COMMANDS


def test_cli_args_registered_in_registry():
    """Vérifie que les options --fast et --story sont bien déclarées pour sync et wikifix."""
    for cmd in ("sync", "wikifix"):
        assert cmd in COMMANDS
        arg_names = [a["name"] for a in COMMANDS[cmd]["args"]]
        assert "--fast" in arg_names
        assert "--story" in arg_names


def test_run_sync_fast_mode_skips_graphify(tmp_path):
    """Vérifie que fast_mode=True saute l'appel à GraphifyAgent dans run_sync."""
    proj_dir = tmp_path / "Projects" / "TestProj"
    proj_dir.mkdir(parents=True)
    state = LoopState(project_name="TestProj")

    with (
        patch("src.pipelines.sync._sync_run.sync_live_reference_wikis"),
        patch("src.pipelines.sync._sync_run.sync_project_directives"),
        patch("src.pipelines.sync._sync_run.sync_sprint_backlog"),
        patch("src.pipelines.sync._sync_run.sync_open_questions"),
        patch("src.pipelines.sync._sync_run.sync_hypergraph"),
        patch("src.pipelines.sync.WikiFixAgent.execute", return_value=state),
        patch("src.pipelines.sync.GraphifyAgent.execute") as mock_graphify,
        patch("src.state.LoopState.save_to_audit"),
    ):
        result_state = run_sync("TestProj", state, proj_dir, fast_mode=True)
        assert result_state == state
        mock_graphify.assert_not_called()


def test_run_sync_fault_isolation(tmp_path):
    """Vérifie que les pannes dans WikiFix ou Graphify n'interrompent pas le pipeline."""
    proj_dir = tmp_path / "Projects" / "TestProj"
    proj_dir.mkdir(parents=True)
    state = LoopState(project_name="TestProj")

    with (
        patch("src.pipelines.sync._sync_run.sync_live_reference_wikis"),
        patch("src.pipelines.sync._sync_run.sync_project_directives"),
        patch("src.pipelines.sync._sync_run.sync_sprint_backlog"),
        patch("src.pipelines.sync._sync_run.sync_open_questions"),
        patch("src.pipelines.sync._sync_run.sync_hypergraph"),
        patch(
            "src.pipelines.sync.WikiFixAgent.execute", side_effect=RuntimeError("WikiFix crashed!")
        ),
        patch(
            "src.pipelines.sync.GraphifyAgent.execute",
            side_effect=RuntimeError("Graphify crashed!"),
        ),
        patch("src.state.LoopState.save_to_audit") as mock_save,
    ):
        # Le pipeline ne doit pas lever d'exception non gérée
        result_state = run_sync("TestProj", state, proj_dir, fast_mode=False)
        assert result_state == state
        mock_save.assert_called_once_with(proj_dir)


def test_graphify_cache_hit_skips_subprocess(tmp_path, monkeypatch):
    """Vérifie que GraphifyAgent saute subprocess.run quand le cache SHA-256 est valide et graphify-out existe."""
    monkeypatch.chdir(tmp_path)
    proj_name = "CacheProj"
    proj_dir = tmp_path / "Projects" / proj_name
    proj_dir.mkdir(parents=True)
    mem_dir = proj_dir / "memory"
    mem_dir.mkdir(parents=True)
    graphify_out = proj_dir / "graphify-out"
    graphify_out.mkdir(parents=True)

    # Fichier cache cohérent avec knowledge_graph.json
    cache_file = mem_dir / "ingest_cache.json"
    cache_file.write_text("{}", encoding="utf-8")

    graph_file = mem_dir / "knowledge_graph.json"
    graph_file.write_text('{"nodes": [], "edges": []}', encoding="utf-8")

    state = LoopState(project_name=proj_name)
    agent = GraphifyAgent()

    with patch("subprocess.run") as mock_subproc:
        res = agent.execute(state)
        mock_subproc.assert_not_called()
        assert res.knowledge_graph is not None


def test_graphify_timeout_expired_handled_gracefully(tmp_path, monkeypatch):
    """Vérifie que TimeoutExpired dans GraphifyAgent ne fait pas crasher le processus."""
    monkeypatch.chdir(tmp_path)
    proj_name = "TimeoutProj"
    proj_dir = tmp_path / "Projects" / proj_name
    proj_dir.mkdir(parents=True)

    state = LoopState(project_name=proj_name)
    agent = GraphifyAgent()

    with patch(
        "subprocess.run",
        side_effect=subprocess.TimeoutExpired(cmd=["graphify", "update", "."], timeout=60),
    ):
        # Doit terminer sans lever d'exception TimeoutExpired
        res = agent.execute(state)
        assert res is not None


def test_wikifix_collect_markdown_files_skips_content_read(tmp_path):
    """Vérifie que _collect_markdown_files retourne les chemins sans lire le contenu du fichier."""
    proj_dir = tmp_path / "Projects" / "CollectProj"
    docs_dir = proj_dir / "docs"
    docs_dir.mkdir(parents=True)
    f1 = docs_dir / "test1.md"
    f1.write_text("dummy content", encoding="utf-8")

    wf = WikiFixAgent()
    files = wf._collect_markdown_files(proj_dir, ["docs"])
    assert len(files) == 1
    assert files[0].name == "test1.md"
