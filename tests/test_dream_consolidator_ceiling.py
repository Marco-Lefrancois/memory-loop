from pathlib import Path
import json
import pytest
from src.pipelines.dream_consolidator import DreamConsolidationDaemon, run_dream_consolidation


def test_dream_consolidation_ceiling_and_satellite(tmp_path: Path):
    # Set up mock project structure
    project_root = tmp_path / "mock_project"
    project_root.mkdir()
    evidence_dir = project_root / "memory" / "evidence"
    evidence_dir.mkdir(parents=True)
    
    # Create 25 mock evidence pack files
    for i in range(25):
        pack = {
            "story_id": f"STORY-{i:03d}",
            "open_questions": [{"id": f"Q{j}", "text": f"Question {j}"} for j in range(i % 3)],
            "alerts": [{"type": "WARN", "msg": f"Alert {k}"} for k in range(i % 2)],
        }
        (evidence_dir / f"STORY_{i:03d}_evidence.json").write_text(json.dumps(pack), encoding="utf-8")
        
    daemon = DreamConsolidationDaemon(project_root)
    report = daemon.consolidate()
    
    assert report["evidence_packs_audited"] == 25
    assert report["total_open_questions"] > 0
    assert report["status"] == "ATTENTION_REQUIRED"
    
    # 1. Verify satellite index
    satellite_index = evidence_dir / "summaries" / "consolidated_evidence_index.json"
    assert satellite_index.exists()
    index_data = json.loads(satellite_index.read_text(encoding="utf-8"))
    assert len(index_data) == 25
    
    # 2. Verify SESSION_MEMORY_HEALTH.md ceiling
    health_file = project_root / "memory" / "SESSION_MEMORY_HEALTH.md"
    assert health_file.exists()
    content = health_file.read_text(encoding="utf-8")
    lines = content.splitlines()
    
    # Strictly <= 200 lines and <= 25KB
    assert len(lines) <= 200
    assert len(content.encode("utf-8")) <= 25600
    
    # Verify top summaries table and satellite note
    assert "| Story ID | Questions Ouvertes | Alertes | Statut |" in content
    assert "consolidated_evidence_index.json" in content
    assert "ADR-0362" in content


def test_dream_consolidation_forced_truncation(tmp_path: Path):
    project_root = tmp_path / "overflow_project"
    project_root.mkdir()
    daemon = DreamConsolidationDaemon(project_root)
    
    # Artificial report with 300 items
    huge_summaries = [
        {"story_id": f"BIG-{i}", "open_questions": 1, "alerts": 1, "status": "PENDING"}
        for i in range(300)
    ]
    report = {
        "timestamp_utc": "2026-09-10T12:00:00Z",
        "evidence_packs_audited": 300,
        "total_open_questions": 300,
        "total_alerts": 300,
        "consolidation_duration_ms": 12.5,
        "status": "ATTENTION_REQUIRED",
    }
    
    daemon.memory_dir.mkdir(parents=True, exist_ok=True)
    daemon._write_health_report(report, huge_summaries)
    
    health_file = project_root / "memory" / "SESSION_MEMORY_HEALTH.md"
    assert health_file.exists()
    lines = health_file.read_text(encoding="utf-8").splitlines()
    assert len(lines) <= 200
