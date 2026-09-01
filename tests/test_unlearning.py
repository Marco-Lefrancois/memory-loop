import pytest
import json
import yaml
from pathlib import Path
from src.pipelines.unlearn import run_unlearn
from src.bridges.mcp_loop_mem import _PRELOAD_CACHE, preload_story_context

def test_unlearn_pipeline(tmp_path, monkeypatch):
    # Setup temporary project structure
    project_name = "test_unlearn_proj"
    proj_dir = tmp_path / "Projects" / project_name
    mem_dir = proj_dir / "memory"
    mem_dir.mkdir(parents=True, exist_ok=True)
    
    # Create fake knowledge graph
    graph_data = {
        "nodes": [
            {"id": "node1", "name": "obsolete_auth"},
            {"id": "node2", "name": "valid_feature"}
        ],
        "edges": [
            {"source": "node1", "target": "node2"}
        ]
    }
    with open(mem_dir / "knowledge_graph.json", "w", encoding="utf-8") as f:
        json.dump(graph_data, f)
        
    # Create fake RHO rules
    rho_data = {
        "rules": [
            {"keyword": "obsolete_auth", "msg": "Old rule"},
            {"keyword": "valid_feature", "msg": "Keep rule"}
        ]
    }
    with open(mem_dir / "rho_rules.yaml", "w", encoding="utf-8") as f:
        yaml.dump(rho_data, f)
        
    # Change working dir in Path for the pipeline or monkeypatch Path
    monkeypatch.chdir(tmp_path)
    
    res = run_unlearn(project_name, "obsolete_auth")
    
    assert res["status"] == "unlearned"
    assert res["concept"] == "obsolete_auth"
    assert res["nodes_removed"] == 1
    assert res["rho_rules_disabled"] == 1
    
    # Verify graph content
    with open(mem_dir / "knowledge_graph.json", "r", encoding="utf-8") as f:
        updated_graph = json.load(f)
    assert len(updated_graph["nodes"]) == 1
    assert updated_graph["nodes"][0]["name"] == "valid_feature"
    assert len(updated_graph["edges"]) == 0
    
    # Verify RHO content
    with open(mem_dir / "rho_rules.yaml", "r", encoding="utf-8") as f:
        updated_rho = yaml.safe_load(f)
    assert len(updated_rho["rules"]) == 1
    assert updated_rho["rules"][0]["keyword"] == "valid_feature"
