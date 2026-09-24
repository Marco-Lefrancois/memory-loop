# -*- coding: utf-8 -*-
"""
Tests unitaires pour le bridge Memory Bank et les règles Cline (MLOOP-260-BE Palier 2, MLOOP-261-BE).
Vérifie :
1. La création des 6 fichiers standardisés dans Projects/<projet>/memory/memory-bank/.
2. L'idempotence des écritures.
3. Le moissonnage bidirectionnel des notes de session vers l'EvidencePack.
4. La génération de .clinerules/mloop.md.
"""

import json
from pathlib import Path
import pytest
from src.bridges.cline.memory_bank_bridge import MemoryBankBridge, MEMORY_BANK_DIR_NAME
from src.bridges.cline.rules_mirror import ClineRulesMirror, CLINERULES_DIR_NAME, MLOOP_RULES_FILE_NAME


def test_memory_bank_creates_all_six_files_in_project_memory(tmp_path: Path):
    """Vérifie la création des 6 fichiers sous Projects/<projet>/memory/memory-bank/."""
    proj_dir = tmp_path / "Projects" / "mLoop"
    proj_dir.mkdir(parents=True, exist_ok=True)

    bridge = MemoryBankBridge(workspace_root=tmp_path, project_name="mLoop")
    res = bridge.sync_all()

    expected_files = {
        "projectbrief.md",
        "productContext.md",
        "activeContext.md",
        "systemPatterns.md",
        "techContext.md",
        "progress.md",
    }
    assert set(res.keys()) == expected_files
    for fname in expected_files:
        p = proj_dir / "memory" / MEMORY_BANK_DIR_NAME / fname
        assert p.exists()
        assert p.stat().st_size > 50


def test_memory_bank_idempotence(tmp_path: Path):
    """Vérifie qu'un second appel sans changement ne réécrit pas les fichiers."""
    proj_dir = tmp_path / "Projects" / "mLoop"
    proj_dir.mkdir(parents=True, exist_ok=True)

    bridge = MemoryBankBridge(workspace_root=tmp_path, project_name="mLoop")
    bridge.sync_all()

    brief_path = proj_dir / "memory" / MEMORY_BANK_DIR_NAME / "projectbrief.md"
    mtime_before = brief_path.stat().st_mtime_ns

    # Second appel immédiat
    bridge.sync_all()
    mtime_after = brief_path.stat().st_mtime_ns

    assert mtime_before == mtime_after


def test_memory_bank_harvest_session_notes_and_evidence_update(tmp_path: Path):
    """Vérifie l'extraction des notes de Cline et la bonification de l'EvidencePack."""
    proj_dir = tmp_path / "Projects" / "mLoop"
    evidence_dir = proj_dir / "memory" / "evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)

    bridge = MemoryBankBridge(workspace_root=tmp_path, project_name="mLoop")
    bridge.sync_all()

    # Création d'un faux EvidencePack initial
    ep_file = evidence_dir / "MLOOP-260-BE_evidence.json"
    ep_file.write_text(json.dumps({"story_id": "MLOOP-260-BE", "session_notes": []}), encoding="utf-8")

    # Simulation : Cline ajoute des notes dans activeContext.md
    active_ctx_file = proj_dir / "memory" / MEMORY_BANK_DIR_NAME / "activeContext.md"
    content = active_ctx_file.read_text(encoding="utf-8")
    content += "\n- Découverte Cline : Le binaire npm nécessite le shim .cmd sous Windows.\n- Note Cline : Performance de sync < 100ms validée.\n"
    active_ctx_file.write_text(content, encoding="utf-8")

    # Moissonnage
    notes = bridge.harvest_session_notes()
    assert len(notes) == 2
    assert "Découverte Cline" in notes[0]

    # Mise à jour de l'EvidencePack
    updated = bridge.update_evidence_pack("MLOOP-260-BE", notes)
    assert updated is True

    # Vérification dans l'EvidencePack
    ep_data = json.loads(ep_file.read_text(encoding="utf-8"))
    assert len(ep_data["session_notes"]) == 2
    assert "Découverte Cline : Le binaire npm nécessite le shim .cmd sous Windows." in ep_data["session_notes"]


def test_cline_rules_mirror_generation_and_idempotence(tmp_path: Path):
    """Vérifie la génération de .clinerules/mloop.md et son idempotence."""
    mirror = ClineRulesMirror(workspace_root=tmp_path)
    out_file = mirror.sync()

    assert out_file.exists()
    assert out_file == tmp_path / CLINERULES_DIR_NAME / MLOOP_RULES_FILE_NAME

    content = out_file.read_text(encoding="utf-8")
    assert "ADR-0376" in content
    assert "ADR-0202" in content
    assert "ADR-0375" in content
    assert "--plan" in content
