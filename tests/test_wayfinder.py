from pathlib import Path
import pytest
from src.pipelines.wayfinder import WayfinderEngine
from src.pipelines.graph_router import RiskLevel


def test_wayfinder_init_map(tmp_path: Path):
    engine = WayfinderEngine(tmp_path)
    map_file = engine.init_map("Initiative-Alpha")
    assert map_file.exists()
    content = map_file.read_text(encoding="utf-8")
    assert "Initiative-Alpha" in content
    assert "Wayfinder Map" in content

    # Test de non-écrasement (idempotence)
    map_file.write_text("CUSTOM_CONTENT", encoding="utf-8")
    engine.init_map("Initiative-Alpha")
    assert map_file.read_text(encoding="utf-8") == "CUSTOM_CONTENT"


def test_wayfinder_to_dag_empty(tmp_path: Path):
    engine = WayfinderEngine(tmp_path)
    router = engine.to_dag("TestEmpty")
    assert router is not None
    assert len(router.nodes) == 0


def test_wayfinder_to_dag_with_tickets(tmp_path: Path):
    engine = WayfinderEngine(tmp_path)
    engine.init_map("Initiative-Beta")

    ticket_text = """
### [DT-001] Choix de l'ADR de Stockage
- **Statut** : OPEN
- **Blocked By** : Aucun
- **Description** : Arbitrer entre SQLite et PostgreSQL.

### [DT-002] Schéma de Tables
- **Statut** : OPEN
- **Blocked By** : DT-001
- **Description** : Définir les clés primaires et index.

"""
    engine.map_file.write_text(ticket_text, encoding="utf-8")
    router = engine.to_dag("Initiative-Beta")

    assert len(router.nodes) == 2
    n1 = router.nodes["DT-001"]
    n2 = router.nodes["DT-002"]

    assert n1.id == "DT-001"
    assert n1.risk_level == RiskLevel.HIGH  # Car 'ADR' dans le titre
    assert len(n1.blocked_by) == 0

    assert n2.id == "DT-002"
    assert n2.risk_level == RiskLevel.MEDIUM
    assert n2.blocked_by == ["DT-001"]
