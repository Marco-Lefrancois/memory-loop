# -*- coding: utf-8 -*-
"""Tests unitaires pour CanvasGenerator (ADR-0337)."""

import json
from pathlib import Path
from src.pipelines.canvas_generator import CanvasGenerator


def test_canvas_generator_lifecycle(tmp_path: Path):
    project_dir = tmp_path / "TestProject"
    project_dir.mkdir()
    backlog_dir = project_dir / "backlog"
    stories_dir = backlog_dir / "stories"
    stories_dir.mkdir(parents=True)

    # Créer deux stories factices
    story_1 = stories_dir / "US-01.md"
    story_1.write_text("""---
id: REC-001
jira_key: TEST-101
epic_key: EPIC-CART
title: Initialisation Panier
status: READY_FOR_DEV
layer: frontend
---
# [TEST-101] Initialisation Panier (REC-001)

> [!ABSTRACT] Fiche Exécutive
> - **Statut** : `READY_FOR_DEV` 🟢
""", encoding="utf-8")

    story_2 = stories_dir / "US-02.md"
    story_2.write_text("""---
id: REC-002
jira_key: TEST-102
epic_key: EPIC-CART
title: Validation Panier
status: IN_ANALYZE
layer: backend
---
# [TEST-102] Validation Panier (REC-002)
""", encoding="utf-8")

    generator = CanvasGenerator(project_dir)
    stories = generator.scan_stories()

    assert len(stories) == 2
    assert stories[0]["id"] == "REC-001"
    assert stories[0]["status"] == "READY_FOR_DEV"
    assert stories[1]["id"] == "REC-002"
    assert stories[1]["status"] == "IN_ANALYZE"

    res = generator.sync_all_canvases()

    assert "story_mapping" in res
    assert "sprint_dag" in res
    assert res["story_mapping"].exists()
    assert res["sprint_dag"].exists()

    # Valider le format JSON du story mapping canvas
    mapping_data = json.loads(res["story_mapping"].read_text(encoding="utf-8"))
    assert "nodes" in mapping_data
    assert len(mapping_data["nodes"]) >= 2
    group_nodes = [n for n in mapping_data["nodes"] if n["type"] == "group"]
    text_nodes = [n for n in mapping_data["nodes"] if n["type"] == "text"]
    assert len(group_nodes) == 1
    assert len(text_nodes) == 2
    assert text_nodes[0]["color"] == "4"  # 🟢 Vert
    assert text_nodes[1]["color"] == "3"  # 🟡 Jaune

    # Valider le format JSON du sprint DAG canvas
    dag_data = json.loads(res["sprint_dag"].read_text(encoding="utf-8"))
    assert "nodes" in dag_data
    assert "edges" in dag_data
    assert len(dag_data["nodes"]) == 2
    assert len(dag_data["edges"]) == 1
    assert dag_data["edges"][0]["fromNode"] == "node-dag-REC-001"
    assert dag_data["edges"][0]["toNode"] == "node-dag-REC-002"
