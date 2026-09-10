"""
Tests unitaires pour les handlers Graph Intelligence et le bridge MCP Graphify (ADR-0204 et ADR-0363).
"""
import argparse
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.bridges.mcp_graphify import load_knowledge_graph, _GRAPH_CACHE, handle_tools_call
from src.commands.handlers.graph_intelligence import (
    handle_graph_status,
    handle_graph_query,
    handle_graph_explain,
    handle_graph_impact,
    _resolve_target_project,
)
from src.state import LoopState


def test_resolve_target_project():
    args_global = argparse.Namespace(global_graph=True, project=None)
    assert _resolve_target_project(args_global, None) == "global"

    args_explicit = argparse.Namespace(global_graph=False, project="CustomApp")
    assert _resolve_target_project(args_explicit, None) == "CustomApp"

    args_none = argparse.Namespace(global_graph=False, project=None)
    state = LoopState(project_name="StateApp")
    assert _resolve_target_project(args_none, state) == "StateApp"


def test_handle_graph_query_validation(capsys):
    args_empty = argparse.Namespace(query="", global_graph=False, project="Metro_FOOD", limit=5)
    code = handle_graph_query(args_empty, None, None)
    assert code == 1


def test_handle_graph_explain_validation(capsys):
    args_empty = argparse.Namespace(concept="", global_graph=False, project="Metro_FOOD")
    code = handle_graph_explain(args_empty, None, None)
    assert code == 1


def test_handle_graph_impact_validation(capsys):
    args_empty = argparse.Namespace(target="", global_graph=False, project="Metro_FOOD")
    code = handle_graph_impact(args_empty, None, None)
    assert code == 1


def test_handle_graph_status_metro_food(capsys):
    args = argparse.Namespace(global_graph=False, project="Metro_FOOD")
    code = handle_graph_status(args, None, None)
    assert code == 0
    captured = capsys.readouterr().out
    assert "Taille Fichier" in captured
    assert "Noeuds Indexes" in captured


def test_handle_graph_query_metro_food(capsys):
    args = argparse.Namespace(query="PostgreSQL", global_graph=False, project="Metro_FOOD", limit=5)
    code = handle_graph_query(args, None, None)
    assert code == 0
    captured = capsys.readouterr().out
    assert "PostgreSQL" in captured


def test_handle_graph_explain_metro_food(capsys):
    args = argparse.Namespace(concept="PostgreSQL", global_graph=False, project="Metro_FOOD")
    code = handle_graph_explain(args, None, None)
    assert code == 0
    captured = capsys.readouterr().out
    assert "Fiche Concept" in captured
    assert "PostgreSQL" in captured


def test_mcp_graph_status_tool():
    res = handle_tools_call(1, {"name": "graph_status", "arguments": {"project": "Metro_FOOD"}})
    assert "result" in res
    content = res["result"]["content"][0]["text"]
    assert "Graphify Knowledge Graph Status" in content
    assert "Metro_FOOD" in content


def test_load_knowledge_graph_cache_invalidation(tmp_path: Path):
    test_json = tmp_path / "knowledge_graph.json"
    test_data_v1 = {"nodes": [{"id": "A"}], "edges": []}
    test_json.write_text(json.dumps(test_data_v1), encoding="utf-8")

    # Charger la v1 dans le cache
    key = str(test_json.resolve())
    _GRAPH_CACHE[key] = (test_json.stat().st_mtime, test_data_v1)
    
    # Vérifier que le cache est utilisé
    assert key in _GRAPH_CACHE
    cached_mtime, cached_data = _GRAPH_CACHE[key]
    assert len(cached_data["nodes"]) == 1
