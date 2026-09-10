"""
Tests unitaires pour l'OpaqueArtifactBus (ADR-0354).
"""

import shutil
from pathlib import Path
import pytest

from src.engine.artifacts.bus import OpaqueArtifactBus, ArtifactHandle
from src.bridges.context_pruner import ContextPruningEngine


@pytest.fixture
def temp_bus(tmp_path):
    bus_dir = tmp_path / "memory" / "artifacts"
    return OpaqueArtifactBus(base_dir=bus_dir)


def test_store_and_retrieve_artifact(temp_bus):
    content = "Ligne 1: Initialisation\nLigne 2: Exécution\nLigne 3: Clôture\n"
    handle = temp_bus.store(content, summary="Test artefact basique", schema_type="text/plain")

    assert handle.handle_id.startswith("mloop://artifacts/")
    assert len(handle.sha256) == 64
    assert handle.line_count == 3
    assert handle.size_bytes == len(content.encode("utf-8"))

    # Récupération de métadonnées
    loaded_handle = temp_bus.get_handle(handle.sha256)
    assert loaded_handle is not None
    assert loaded_handle.summary == "Test artefact basique"

    # Récupération du contenu
    retrieved_content = temp_bus.get_content(handle.handle_id)
    assert retrieved_content == content


def test_get_slice_projection(temp_bus):
    lines = [f"Ligne {i}: Donnée test {i}" for i in range(1, 51)]
    content = "\n".join(lines)
    handle = temp_bus.store(content, summary="Artefact 50 lignes")

    # Projection lignes 10 à 15 inclusivement
    slice_text = temp_bus.get_slice(handle.handle_id, start_line=10, end_line=15)
    slice_lines = slice_text.splitlines()

    assert len(slice_lines) == 6
    assert slice_lines[0] == "Ligne 10: Donnée test 10"
    assert slice_lines[-1] == "Ligne 15: Donnée test 15"


def test_to_prompt_descriptor(temp_bus):
    lines = [f"Ligne {i}" for i in range(1, 40)]
    content = "\n".join(lines)
    handle = temp_bus.store(content, summary="Grand fichier de test")

    descriptor = temp_bus.to_prompt_descriptor(handle, preview_lines=3)
    assert "[OPAQUE-ARTIFACT:" in descriptor
    assert handle.handle_id in descriptor
    assert "Ligne 1" in descriptor
    assert "Ligne 39" in descriptor
    assert "lignes omises pour protéger le contexte" in descriptor


def test_offload_if_exceeds(temp_bus):
    small_text = "Court texte."
    offloaded, out_desc, handle = temp_bus.offload_if_exceeds(small_text, max_chars=50, max_lines=5)
    assert not offloaded
    assert out_desc == small_text
    assert handle is None

    big_text = "Ligne\n" * 60
    offloaded, out_desc, handle = temp_bus.offload_if_exceeds(big_text, max_chars=50, max_lines=5)
    assert offloaded
    assert handle is not None
    assert "[OPAQUE-ARTIFACT:" in out_desc


def test_context_pruner_integration(tmp_path, monkeypatch):
    bus_dir = tmp_path / "memory" / "artifacts"
    bus = OpaqueArtifactBus(base_dir=bus_dir)
    monkeypatch.setattr(ContextPruningEngine, "_bus", bus)

    # Petit contenu -> inchangé
    assert ContextPruningEngine.prune_tool_output("view_file", "123") == "123"

    # Gros contenu -> offloading dans l'OpaqueArtifactBus
    huge_content = "X" * 3000
    pruned = ContextPruningEngine.prune_tool_output("run_command", huge_content)
    assert "[OPAQUE-ARTIFACT: mloop://artifacts/" in pruned
    assert "Taille: 3000 octets" in pruned
