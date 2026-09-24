"""
Tests unitaires et d'intégration E2E pour Grilling mLoop v2 (EPIC-29 / ADR-0389 / ADR-013).
Valide les Frontier Rounds, le Handoff Pattern zéro-build, Context Health et le pilote Metro FOOD.
"""
import argparse
from pathlib import Path
import pytest

from src.pipelines.grill import (
    check_context_health,
    detect_ungrillable_signals,
    execute_grill_cli,
    format_frontier_round,
    inspect_session_health,
    promote_prototype,
    stage_prototype,
)
from src.state import LoopState


@pytest.fixture
def temp_metro_food(tmp_path):
    """Crée une arborescence représentative pour le pilote Metro FOOD."""
    metro_dir = tmp_path / "Metro_FOOD"
    metro_dir.mkdir(parents=True)
    (metro_dir / "docs" / "01-architecture").mkdir(parents=True)
    (metro_dir / "docs" / "05-assets" / "mockups").mkdir(parents=True)
    (metro_dir / "backlog" / "stories").mkdir(parents=True)
    (metro_dir / "memory").mkdir(parents=True)

    sprint = metro_dir / "backlog" / "sprint_backlog.md"
    sprint.write_text("# Sprint Backlog Metro FOOD\n| ID | Titre | Statut |\n", encoding="utf-8")

    health_file = metro_dir / "memory" / "SESSION_MEMORY_HEALTH.md"
    health_file.write_text("Session logs " * 5000, encoding="utf-8")  # ~65k chars -> ~16k tokens

    return metro_dir


def test_stage_and_promote_prototype_html(temp_metro_food):
    """Vérifie la création zéro-build d'un prototype HTML5 et sa promotion."""
    proto = stage_prototype(
        project_path=temp_metro_food,
        story_id="METRO-101-FE",
        subject="filtre_allergenes",
        content="<section>Panneau de filtres</section>",
        kind="html",
    )

    assert proto.exists()
    assert proto.name == "proto_METRO-101-FE_filtre_allergenes.html"
    content = proto.read_text(encoding="utf-8")
    assert "cdn.tailwindcss.com" in content
    assert "METRO-101-FE" in content
    assert "Panneau de filtres" in content

    # Promotion vers docs/05-assets/mockups/
    promoted = promote_prototype(proto)
    assert promoted.exists()
    assert promoted.parent == temp_metro_food / "docs" / "05-assets" / "mockups"


def test_stage_prototype_svg(temp_metro_food):
    """Vérifie la génération d'une maquette SVG autonome vectorielle."""
    proto = stage_prototype(
        project_path=temp_metro_food,
        story_id="METRO-102-FE",
        subject="hierarchie_substituts",
        content='<circle cx="50" cy="50" r="40" fill="green" />',
        kind="svg",
    )

    assert proto.exists()
    assert proto.suffix == ".svg"
    content = proto.read_text(encoding="utf-8")
    assert "<svg" in content
    assert "METRO-102-FE" in content
    assert "<circle" in content


def test_check_context_health_zones(tmp_path):
    """Vérifie les seuils déterministes Smart Zone, Warning Zone et Dumb Zone."""
    # Smart Zone < 80k
    h_smart = check_context_health(token_count=50000)
    assert h_smart["zone"] == "SMART_ZONE"
    assert h_smart["status"] == "HEALTHY"
    assert not h_smart["alert"]

    # Warning Zone 80k-120k
    h_warn = check_context_health(token_count=95000)
    assert h_warn["zone"] == "WARNING_ZONE"
    assert h_warn["status"] == "WARNING"
    assert h_warn["alert"]

    # Dumb Zone > 120k
    h_dumb = check_context_health(token_count=135000)
    assert h_dumb["zone"] == "DUMB_ZONE"
    assert h_dumb["status"] == "CRITICAL"
    assert h_dumb["alert"]
    assert "Interdiction de purge" in h_dumb["message"]

    # Via fichier transcript
    f_log = tmp_path / "transcript.log"
    f_log.write_text("a" * 400000, encoding="utf-8")  # 100k tokens -> Warning
    h_file = check_context_health(transcript_path=f_log)
    assert h_file["zone"] == "WARNING_ZONE"
    assert h_file["tokens"] == 100000


def test_format_frontier_round_and_heuristics():
    """Vérifie la détection d'ungrillables et le formatage de rounds orthogonaux."""
    # Détection ungrillable
    signal = detect_ungrillable_signals("Doit-on faire un wizard ou un drawer avec accordéon ?")
    assert signal["is_ungrillable"]
    assert "spatial_layout" in signal["categories"]
    assert signal["recommended_action"] == "HANDOFF_PROTOTYPE"

    # Détection question classique
    clean_signal = detect_ungrillable_signals("Faut-il utiliser Redis ou Postgres pour le cache ?")
    assert not clean_signal["is_ungrillable"]
    assert clean_signal["recommended_action"] == "CONTINUE_GRILL"

    # Formatage de Round
    questions = [
        {"title": "Choix S3", "guess": "Bucket standard", "recommendation": "S3 standard"},
        {"title": "Type Auth", "guess": "JWT RSA", "recommendation": "OIDC Gateway"},
    ]
    round_md = format_frontier_round(questions, round_num=1, theme="Infra")
    assert "Round de Frontière #1 (Infra)" in round_md
    assert "Q1. Choix S3" in round_md
    assert "Q2. Type Auth" in round_md
    assert "GUESS" in round_md


def test_cli_execution_health_and_modes(temp_metro_food, monkeypatch):
    """Vérifie l'orchestration CLI pour inspect_session_health et execute_grill_cli."""
    state = LoopState(project_name="Metro_FOOD")

    # Test inspection santé
    ret = inspect_session_health(temp_metro_food)
    assert ret == 0

    # Test CLI avec option --health
    args_health = argparse.Namespace(project="Metro_FOOD", health=True)
    assert execute_grill_cli(args_health, state, temp_metro_food) == 0

    # Mock run_sync pour éviter dépendance FTS5 complète lors du test CLI
    monkeypatch.setattr("src.pipelines.sync.run_sync", lambda p, s, path: None)

    # Test Macro avec mode round par défaut
    args_macro = argparse.Namespace(
        project="Metro_FOOD",
        health=False,
        story=None,
        mode=None,
        query=None,
        title="Architecture Initiale",
        context="Cadrage macro Metro FOOD",
        decision="Rounds v2 adoptés",
        positives="Gain de temps",
        negatives="N/A",
    )
    assert execute_grill_cli(args_macro, state, temp_metro_food) == 0
    adrs = list((temp_metro_food / "docs" / "01-architecture").glob("ADR-*.md"))
    assert len(adrs) == 1
