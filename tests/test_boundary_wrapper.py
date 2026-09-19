"""
Tests Déterministes du Boundary Tracing Wrapper (ADR-0380 / MLOOP-071-BE).
Couverture rigoureuse des 4 Piliers Gherkin et des 7 Standards Python Senior (ADR-0369) :
1. Nominal : Déportation automatique des sorties > 2 000 car. ou > 30 lignes.
2. Rejets & Limites : Sorties courtes transparentes, @pytest.mark.parametrize aux frontières, timeouts typés.
3. Résilience : Lecture fenêtrée get_artifact_slice, bornes invalides, handles inexistants.
4. UX / Observabilité : Traçabilité événementielle et calcul du gain de tokens.
"""
import time
import pytest
from pathlib import Path

from src.engine.artifacts.boundary_wrapper import (
    boundary_trace,
    offload_if_exceeds,
    get_artifact_slice,
    BoundaryToolTimeoutError,
    ArtifactBusProtocol,
)
from src.engine.artifacts.bus import OpaqueArtifactBus


@pytest.fixture
def temp_artifact_bus(tmp_path: Path) -> OpaqueArtifactBus:
    """Fixture fournissant une instance isolée d'OpaqueArtifactBus dans tmp_path."""
    return OpaqueArtifactBus(base_dir=tmp_path / "artifacts")


# ─── PILIER 1 : CHEMIN NOMINAL (Happy Path & Déportation Automatique) ───

def test_boundary_trace_large_output_auto_offload(temp_artifact_bus: OpaqueArtifactBus):
    """Vérifie qu'une sortie de 5 000 caractères et 120 lignes est déportée sous SHA-256."""
    lines = [f"Line {i:03d} : Payload text with data and parameters" for i in range(120)]
    large_output = "\n".join(lines)
    assert len(large_output) > 2000
    assert len(lines) > 30

    @boundary_trace(bus=temp_artifact_bus, tool_name="scanner")
    def sample_heavy_tool() -> str:
        """Sample docstring."""
        return large_output

    result = sample_heavy_tool()

    # Invariants vérifiés
    assert "mloop://artifacts/" in result
    assert "OPAQUE-ARTIFACT:" in result
    assert "scanner" in result
    assert len(result) < len(large_output)
    assert len(result.splitlines()) < 30


def test_boundary_trace_preserves_function_signature():
    """Vérifie que le décorateur préserve le nom et la docstring (__name__, __doc__)."""
    @boundary_trace(tool_name="auditor")
    def inspect_system(target: str) -> str:
        """Inspection déterministe."""
        return f"OK {target}"

    assert inspect_system.__name__ == "inspect_system"
    assert inspect_system.__doc__ == "Inspection déterministe."
    assert inspect_system("db") == "OK db"


# ─── PILIER 2 : REJETS, LIMITES MÉTIER & TIMEOUTS ───

def test_boundary_trace_small_output_passes_transparently(temp_artifact_bus: OpaqueArtifactBus):
    """Vérifie qu'une sortie courte passe brute sans création d'artefact."""
    short_output = "Statut OK : 3 workers actifs."

    @boundary_trace(bus=temp_artifact_bus, tool_name="status_checker")
    def quick_tool() -> str:
        return short_output

    result = quick_tool()
    assert result == short_output
    assert "mloop://artifacts/" not in result


@pytest.mark.parametrize(
    "char_count,line_count,expected_offload",
    [
        (1999, 10, False),  # Sous la limite de caractères et de lignes
        (2001, 10, True),   # Excède la limite de caractères
        (500, 29, False),   # Sous la limite de caractères et de lignes
        (500, 31, True),    # Excède la limite de lignes
        (2000, 30, False),  # Exactement aux plafonds (inclusif)
    ],
)
def test_offload_thresholds_parametrize(
    temp_artifact_bus: OpaqueArtifactBus,
    char_count: int,
    line_count: int,
    expected_offload: bool,
):
    """Validation paramétrée aux frontières exactes (ADR-0369 Standard 5)."""
    # Génère du contenu calibré
    base_line = "A" * (char_count // max(1, line_count))
    lines = [base_line for _ in range(line_count)]
    content = "\n".join(lines)
    # Ajustement fin de la taille totale
    if len(content) < char_count:
        content += "X" * (char_count - len(content))
    elif len(content) > char_count and not expected_offload:
        content = content[:char_count]

    result, is_offloaded = offload_if_exceeds(
        output=content,
        max_chars=2000,
        max_lines=30,
        bus=temp_artifact_bus,
        tool_name="param_tool",
    )
    assert is_offloaded == expected_offload
    if expected_offload:
        assert "mloop://artifacts/" in result
    else:
        assert result == content


def test_boundary_trace_tool_exception_propagates():
    """Vérifie que les exceptions métier de l'outil callable sont propagées sans altération."""
    @boundary_trace(tool_name="faulty_tool")
    def faulty_tool():
        raise KeyError("Clé obligatoire manquante")

    with pytest.raises(KeyError, match="Clé obligatoire manquante"):
        faulty_tool()


def test_boundary_trace_timeout_raises_typed_error():
    """Vérifie qu'un outil bloqué déclenche BoundaryToolTimeoutError (ADR-0369 Standard 3)."""
    @boundary_trace(timeout_seconds=0.1, tool_name="infinite_tool")
    def slow_tool():
        time.sleep(0.5)
        return "late"

    with pytest.raises(BoundaryToolTimeoutError) as exc_info:
        slow_tool()

    assert "infinite_tool" in str(exc_info.value)
    assert "0.1s" in str(exc_info.value)


# ─── PILIER 3 : RÉSILIENCE TECHNIQUE & EXTRACTION FENÊTRÉE ───

def test_get_artifact_slice_extracts_exact_lines(temp_artifact_bus: OpaqueArtifactBus):
    """Vérifie la projection fenêtrée des lignes 10 à 25 d'un artefact volumineux."""
    lines = [f"LOG_ENTRY_ROW_{i:04d}" for i in range(1, 101)]
    content = "\n".join(lines)

    handle = temp_artifact_bus.store(content, summary="Big Log")
    slice_text = get_artifact_slice(handle.handle_id, start_line=10, end_line=25, bus=temp_artifact_bus)

    slice_lines = slice_text.splitlines()
    assert len(slice_lines) == 16  # 25 - 10 + 1
    assert slice_lines[0] == "LOG_ENTRY_ROW_0010"
    assert slice_lines[-1] == "LOG_ENTRY_ROW_0025"


def test_get_artifact_slice_invalid_bounds_raises(temp_artifact_bus: OpaqueArtifactBus):
    """Vérifie le rejet strict des bornes négatives ou inversées."""
    with pytest.raises(ValueError, match="start_line doit être >= 1"):
        get_artifact_slice("mloop://artifacts/fake", start_line=0, end_line=10, bus=temp_artifact_bus)

    with pytest.raises(ValueError, match="end_line .* doit être >= start_line"):
        get_artifact_slice("mloop://artifacts/fake", start_line=20, end_line=10, bus=temp_artifact_bus)


def test_get_artifact_slice_nonexistent_handle_raises_file_not_found(temp_artifact_bus: OpaqueArtifactBus):
    """Vérifie la levée de FileNotFoundError sur un handle inexistant."""
    fake_handle = "mloop://artifacts/0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
    with pytest.raises(FileNotFoundError):
        get_artifact_slice(fake_handle, start_line=1, end_line=5, bus=temp_artifact_bus)


def test_boundary_trace_handles_none_and_empty_gracefully(temp_artifact_bus: OpaqueArtifactBus):
    """Vérifie le traitement fail-safe de None et chaînes vides."""
    res_none, off_none = offload_if_exceeds(None, bus=temp_artifact_bus)
    assert res_none == ""
    assert off_none is False

    res_empty, off_empty = offload_if_exceeds("   \n   ", bus=temp_artifact_bus)
    assert res_empty == "   \n   "
    assert off_empty is False


# ─── PILIER 4 : UX & OBSERVABILITÉ (Événement et Gain Tokens) ───

def test_boundary_trace_emits_event_on_offload(monkeypatch, temp_artifact_bus: OpaqueArtifactBus):
    """Vérifie l'émission de l'événement artifact_persisted avec calcul du gain de tokens."""
    emitted_events = []

    from src.utils import event_logger
    monkeypatch.setattr(
        event_logger.EventLogger,
        "log_event",
        lambda event_type, payload: emitted_events.append((event_type, payload)),
    )

    huge_text = "DUMP_DATA_CHUNK_" * 200  # ~3200 chars
    res, is_off = offload_if_exceeds(huge_text, bus=temp_artifact_bus, tool_name="db_dump")

    assert is_off is True
    assert len(emitted_events) == 1
    event_type, payload = emitted_events[0]
    assert event_type == "artifact_persisted"
    assert payload["tool"] == "db_dump"
    assert payload["tokens_saved"] > 500
    assert "sha256" in payload
