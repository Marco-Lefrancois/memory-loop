import json
from pathlib import Path
from src.pipelines.evidence_pack import EvidencePackEngine


def test_evidence_pack_extraction(tmp_path):
    project_dir = tmp_path / "TestProject"
    project_dir.mkdir()
    stories_dir = project_dir / "backlog" / "stories"
    stories_dir.mkdir(parents=True)

    story_file = stories_dir / "US-01.md"
    story_file.write_text(
        """---
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
""",
        encoding="utf-8",
    )

    # Création d'une source physique factice pour valider le calcul SHA-256
    ingested_dir = project_dir / "docs" / "00-ingested"
    ingested_dir.mkdir(parents=True)
    (ingested_dir / "scan_test.md").write_text(
        "Données source de référence fact-search", encoding="utf-8"
    )

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
    assert (
        data["source_hashes_sha256"]["scan_test.md"]
        == evidence["source_hashes_sha256"]["scan_test.md"]
    )


def test_evidence_pack_visual_contract_from_ingested_mockup_frontmatter(tmp_path):
    """
    Phase 1 (AXE 1) : lorsqu'une story référence une maquette ingérée (docs/00-ingested/maquettes/*.md)
    portant un frontmatter is_vectorized/ocr_status (produit par svg_to_md.py), l'EvidencePack doit
    exposer un bloc `visual_contract` traçant si le Contrat Visuel a réellement été lu (OCR) ou non.
    """
    project_dir = tmp_path / "TestProjectVisual"
    project_dir.mkdir()
    stories_dir = project_dir / "backlog" / "stories"
    stories_dir.mkdir(parents=True)

    maquettes_dir = project_dir / "docs" / "00-ingested" / "maquettes"
    maquettes_dir.mkdir(parents=True)
    mockup_md = maquettes_dir / "confirmation_ecran.md"
    mockup_md.write_text(
        """---
title: "Spécification UI : Confirmation Ecran"
document_type: "ui_specification"
source_svg: "confirmation_ecran.svg"
is_vectorized: true
ocr_status: "UNAVAILABLE"
---
# Spécification UI Extraite
""",
        encoding="utf-8",
    )

    story_file = stories_dir / "US-02.md"
    story_file.write_text(
        """---
id: US-02-TEST
status: IN_ANALYZE
---
# US-02 : Test Story Visuelle

- **Ref**: [confirmation_ecran.md](../../docs/00-ingested/maquettes/confirmation_ecran.md)
""",
        encoding="utf-8",
    )

    engine = EvidencePackEngine(project_dir)
    evidence = engine.extract_evidence(story_file)

    assert "visual_contract" in evidence
    contracts = evidence["visual_contract"]
    assert len(contracts) == 1
    assert contracts[0]["mockup_path"].endswith("confirmation_ecran.md")
    assert contracts[0]["is_vectorized"] is True
    assert contracts[0]["ocr_status"] == "UNAVAILABLE"


def test_evidence_pack_visual_contract_empty_when_no_mockup_referenced(tmp_path):
    """Aucune maquette référencée -> visual_contract est une liste vide (pas d'invention de contrat)."""
    project_dir = tmp_path / "TestProjectNoVisual"
    project_dir.mkdir()
    stories_dir = project_dir / "backlog" / "stories"
    stories_dir.mkdir(parents=True)

    story_file = stories_dir / "US-03.md"
    story_file.write_text(
        """---
id: US-03-TEST
status: IN_ANALYZE
---
# US-03 : Story Sans Maquette
""",
        encoding="utf-8",
    )

    engine = EvidencePackEngine(project_dir)
    evidence = engine.extract_evidence(story_file)

    assert evidence["visual_contract"] == []


def test_evidence_pack_socle_factuel_defaults_to_unvalidated(tmp_path):
    """
    Phase 2.2 : par défaut (aucune mention explicite dans le récit), le socle factuel
    n'est PAS considéré comme validé par l'humain. Champ traçable pour élévation future
    en BLOCKING (cf. plan Phase 2.2 — non bloquant à ce stade).
    """
    project_dir = tmp_path / "TestProjectSocle"
    project_dir.mkdir()
    stories_dir = project_dir / "backlog" / "stories"
    stories_dir.mkdir(parents=True)

    story_file = stories_dir / "US-04.md"
    story_file.write_text(
        """---
id: US-04-TEST
status: READY_FOR_DEV
---
# US-04 : Story Sans Validation Explicite
""",
        encoding="utf-8",
    )

    engine = EvidencePackEngine(project_dir)
    evidence = engine.extract_evidence(story_file)

    assert evidence["socle_factuel_validated_by_human"] is False
    assert evidence["socle_factuel_validated_at"] is None


def test_evidence_pack_preserves_human_validation_on_regeneration(tmp_path):
    """
    BUG-WIKIFIX-03 (anti-régression) : lors d'une régénération (WikiFix/sync), les champs
    scellés par l'humain sur l'EvidencePack existant NE doivent PAS être écrasés par les
    valeurs par défaut. Merge non-destructif de socle_factuel_validated_by_human / _at.
    """
    project_dir = tmp_path / "TestProjectPreserve"
    project_dir.mkdir()
    stories_dir = project_dir / "backlog" / "stories"
    stories_dir.mkdir(parents=True)

    story_file = stories_dir / "US-05.md"
    story_file.write_text(
        """---
id: US-05-TEST
status: READY_FOR_GROOMING
---
# US-05 : Story avec socle validé humainement
""",
        encoding="utf-8",
    )

    engine = EvidencePackEngine(project_dir)

    # 1er passage : génère et sauvegarde le pack (socle non validé par défaut)
    pack1 = engine.extract_evidence(story_file)
    engine.save_evidence_pack(pack1)

    # L'humain scelle manuellement le socle dans le pack existant sur disque
    pack_path = project_dir / "memory" / "evidence" / "US-05-TEST_evidence.json"
    sealed = json.loads(pack_path.read_text(encoding="utf-8"))
    sealed["socle_factuel_validated_by_human"] = True
    sealed["socle_factuel_validated_at"] = "2026-09-10T10:52:00+00:00"
    pack_path.write_text(
        json.dumps(sealed, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    # 2e passage (régénération WikiFix) : DOIT préserver le scellé humain
    pack2 = engine.extract_evidence(story_file)

    assert pack2["socle_factuel_validated_by_human"] is True, (
        "La régénération ne doit pas écraser la validation humaine existante."
    )
    assert pack2["socle_factuel_validated_at"] == "2026-09-10T10:52:00+00:00"
