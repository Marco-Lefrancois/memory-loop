"""
Harnais de tests d'intégration EPIC-30 — Multimodal Artifact Harness (MLOOP-304-FULL).

Couvre les 4 modules cœur du harnais :
  - artifact_gate (MLOOP-300-BE)          : porte déterministe anti-raster-paste.
  - connector_validator (MLOOP-301-BE)    : intégrité topologique des connecteurs.
  - audit_decoupler (MLOOP-303-BE)        : score composite à barrière multiplicative.
  - orbit_caption_harvester (MLOOP-302-BE): moisson contextuelle ORBIT des figures.

Tous les tests sont hermétiques (tmp_path), sans effet de bord disque hors sandbox.
Conforme ADR-0369 (Failure Contract via pytest.raises).
"""

from __future__ import annotations

import pytest

from src.pipelines.artifact_gate import (
    evaluate_artifact_gate,
    REASON_CONFORME,
    REASON_RASTER_PASTE,
    REASON_CORRUPT,
)
from src.pipelines.connector_validator import (
    validate_connector_integrity,
    ERR_INTEGRITY_FAIL,
    ERR_COLLAPSE,
)
from src.pipelines.audit_decoupler import (
    calculate_decoupled_architecture_score,
    ScoreOutOfBoundsError,
    ERR_CAUSAL_INVERSION,
)
from src.pipelines.orbit_caption_harvester import (
    harvest_orbit_figures,
    STATUS_ANCHORED,
    STATUS_DECORATIVE,
)


# ─────────────────────────── Fixtures utilitaires ───────────────────────────
def _write(tmp_path, name: str, content: str):
    """Écrit un fichier d'artefact dans la sandbox et renvoie son chemin."""
    path = tmp_path / name
    path.write_text(content, encoding="utf-8")
    return path


_VALID_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <rect x="0" y="0" width="20" height="10"/>
  <circle cx="50" cy="50" r="5"/>
  <path d="M10 10 L90 90"/>
  <line x1="0" y1="0" x2="100" y2="100"/>
  <polygon points="0,0 10,0 10,10"/>
</svg>"""

_RASTER_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <image x="0" y="0" width="98" height="97" href="data:image/png;base64,AAAA"/>
</svg>"""

_CORRUPT_SVG = """<svg viewBox="0 0 100 100"><rect width="10" height="10"</svg>"""


# ─────────────────────── MLOOP-300-BE : artifact_gate ───────────────────────
def test_artifact_gate_valid_svg(tmp_path):
    """SVG vectoriel pur (5 éléments, 0 raster) → PASS."""
    path = _write(tmp_path, "arch.svg", _VALID_SVG)
    result = evaluate_artifact_gate(path)
    assert result.is_valid is True
    assert result.reason == REASON_CONFORME
    assert result.raster_ratio < 0.80
    assert result.vector_elements_count == 5
    assert len(result.checksum) == 64


def test_artifact_gate_raster_paste(tmp_path):
    """SVG avec image couvrant ~95 % du viewBox et < 3 vecteurs → RASTER_PASTE_DETECTED."""
    path = _write(tmp_path, "fake.svg", _RASTER_SVG)
    result = evaluate_artifact_gate(path)
    assert result.is_valid is False
    assert result.reason == REASON_RASTER_PASTE
    assert result.raster_ratio > 0.80
    assert result.vector_elements_count < 3


def test_artifact_gate_corrupt(tmp_path):
    """XML mal formé → CORRUPT_ARTIFACT sans exception non gérée."""
    path = _write(tmp_path, "broken.svg", _CORRUPT_SVG)
    result = evaluate_artifact_gate(path)
    assert result.is_valid is False
    assert result.reason == REASON_CORRUPT


def test_artifact_gate_missing_file(tmp_path):
    """Fichier inexistant → CORRUPT_ARTIFACT (Zero Crash Policy)."""
    result = evaluate_artifact_gate(tmp_path / "ghost.svg")
    assert result.is_valid is False
    assert result.reason == REASON_CORRUPT


# ────────────────────── MLOOP-301-BE : connector_validator ──────────────────
def test_connector_validator_valid_graph():
    """4 nœuds + 3 arêtes valablement reliées → PASS, graphe fermé."""
    diagram = {
        "nodes": [{"id": "a"}, {"id": "b"}, {"id": "c"}, {"id": "d"}],
        "edges": [
            {"from": "a", "to": "b", "direction": "forward"},
            {"from": "b", "to": "c"},
            {"from": "c", "to": "d"},
        ],
    }
    result = validate_connector_integrity(diagram)
    assert result.is_valid is True
    assert result.errors == []
    assert result.node_count == 4
    assert result.edge_count == 3


def test_connector_validator_orphan_edge():
    """Arête vers un nœud inexistant → CONNECTOR_INTEGRITY_FAIL."""
    diagram = {
        "nodes": [{"id": "a"}, {"id": "b"}],
        "edges": [{"from": "a", "to": "node_inconnu"}],
    }
    result = validate_connector_integrity(diagram)
    assert result.is_valid is False
    assert any(ERR_INTEGRITY_FAIL in e for e in result.errors)
    assert any("node_inconnu" in e for e in result.errors)


def test_connector_validator_jsoncanvas_convention():
    """Format Obsidian JSONCanvas (fromNode/toNode) → reconnu et validé → PASS."""
    diagram = {
        "nodes": [{"id": "n1"}, {"id": "n2"}, {"id": "n3"}, {"id": "n4"}],
        "edges": [
            {"id": "e1", "fromNode": "n1", "toNode": "n2"},
            {"id": "e2", "fromNode": "n2", "toNode": "n3"},
            {"id": "e3", "fromNode": "n3", "toNode": "n4"},
        ],
    }
    result = validate_connector_integrity(diagram)
    assert result.is_valid is True
    assert result.errors == []
    assert result.edge_count == 3


def test_connector_collapse():
    """5 nœuds, 0 arête → CONNECTOR_COLLAPSE_DETECTED."""
    diagram = {
        "nodes": [{"id": f"n{i}"} for i in range(5)],
        "edges": [],
    }
    result = validate_connector_integrity(diagram)
    assert result.is_valid is False
    assert any(ERR_COLLAPSE in e for e in result.errors)
    assert result.node_count == 5
    assert result.edge_count == 0


# ─────────────────────── MLOOP-303-BE : audit_decoupler ─────────────────────
def test_audit_decoupler_nominal():
    """topo=1.0, visual=0.9 → 0.97, approuvé."""
    result = calculate_decoupled_architecture_score(1.0, 0.9)
    assert result.composite_score == pytest.approx(0.97)
    assert result.is_approved is True
    assert result.topological_penalty == pytest.approx(0.0)


def test_audit_decoupler_barrier():
    """topo=0.4 (déficit), visual=1.0 → 0.40, rejeté par barrière multiplicative."""
    result = calculate_decoupled_architecture_score(0.4, 1.0)
    assert result.composite_score == pytest.approx(0.40)
    assert result.is_approved is False


def test_audit_decoupler_causal_inversion():
    """Inversion causale → S_topo forcé à 0.0 → score 0.0, diagnostic dédié."""
    result = calculate_decoupled_architecture_score(1.0, 1.0, causal_inversion=True)
    assert result.composite_score == pytest.approx(0.0)
    assert result.is_approved is False
    assert result.details["diagnostic"] == ERR_CAUSAL_INVERSION
    assert result.topological_penalty == pytest.approx(1.0)


def test_audit_decoupler_out_of_bounds():
    """Note hors bornes [0,1] → ScoreOutOfBoundsError (Failure Contract)."""
    with pytest.raises(ScoreOutOfBoundsError):
        calculate_decoupled_architecture_score(1.5, 0.5)


# ────────────────── MLOOP-302-BE : orbit_caption_harvester ──────────────────
def test_orbit_harvester_figure_extraction(tmp_path):
    """Figure avec légende + paragraphes d'appel → fiche d'ancrage FIGURE_ANCHORED."""
    doc = _write(
        tmp_path,
        "brief.md",
        "Figure 3 : Architecture Microservices\n\n"
        "Le système repose sur une passerelle. cf. Figure 3 pour le détail. "
        "Comme illustré sur la Figure 3, les services communiquent en asynchrone.",
    )
    figures = [{"id": "img_003", "caption": "Figure 3 : Architecture Microservices"}]
    cards = harvest_orbit_figures(doc, figures)
    assert len(cards) == 1
    card = cards[0]
    assert card["status"] == STATUS_ANCHORED
    assert card["figure_ref"] == "figure_3"
    assert card["context_count"] >= 1
    assert len(card["sha256"]) == 64


def test_orbit_harvester_decorative_skip(tmp_path):
    """Logo/bannière sans légende ni référence → DECORATIVE_FIGURE_SKIPPED."""
    doc = _write(tmp_path, "brief.md", "Bienvenue dans le document technique.")
    figures = [{"id": "logo_header", "decorative": True}]
    cards = harvest_orbit_figures(doc, figures)
    assert len(cards) == 1
    assert cards[0]["status"] == STATUS_DECORATIVE
