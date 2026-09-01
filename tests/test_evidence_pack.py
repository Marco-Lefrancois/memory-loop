import json
from pathlib import Path
from src.pipelines.evidence_pack import EvidencePackEngine


def test_evidence_pack_extraction(tmp_path):
    project_dir = tmp_path / "TestProject"
    project_dir.mkdir()
    stories_dir = project_dir / "backlog" / "stories"
    stories_dir.mkdir(parents=True)

    story_file = stories_dir / "US-01.md"
    story_file.write_text("""---
id: US-01-TEST
status: IN_ANALYZE
---
# US-01 : Test Story

> [!NOTE]
> Trace Note

> [!CAUTION]
> Caution Alert

> [!WARNING]
> Warning Alert

- **Ref**: Q-001, QD-002
- **Source**: scan_test.md
""", encoding="utf-8")

    # Création d'une source physique factice pour valider le calcul SHA-256
    ingested_dir = project_dir / "docs" / "00-ingested"
    ingested_dir.mkdir(parents=True)
    (ingested_dir / "scan_test.md").write_text("Données source de référence fact-search", encoding="utf-8")

    engine = EvidencePackEngine(project_dir)
    evidence = engine.extract_evidence(story_file)

    assert evidence["story_id"] == "US-01-TEST"
    assert len(evidence["alerts"]) == 3
    assert set(evidence["open_questions"]) == {"Q-001", "QD-002"}
    assert "scan_test.md" in evidence["sources_consulted"]
    assert "scan_test.md" in evidence.get("source_hashes_sha256", {})
    assert len(evidence["source_hashes_sha256"]["scan_test.md"]) == 64
    assert "epistemic_audit" in evidence
    assert "what_it_actually_proves" in evidence["epistemic_audit"]
    assert "claim_boundaries" in evidence["epistemic_audit"]

    saved_path = engine.save_evidence_pack(evidence)
    assert saved_path.exists()

    data = json.loads(saved_path.read_text(encoding="utf-8"))
    assert data["story_id"] == "US-01-TEST"
    assert data["source_hashes_sha256"]["scan_test.md"] == evidence["source_hashes_sha256"]["scan_test.md"]

