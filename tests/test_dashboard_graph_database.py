"""
tests/test_dashboard_graph_database.py — Banc de test unitaire pour MLOOP-075-FULL.

Couvre les 4 Piliers Gherkin du récit MLOOP-075-FULL :
1. Pilier 1 : Chemin Nominal (Accès au graphe Graphify compilé et métadonnées)
2. Pilier 2 : Exceptions & Rejets Métier (Projet sans graphe compilé -> 404 propre sans plantage)
3. Pilier 3 : Résilience & Sécurité Read-Only (Refus 403 hors périmètre, injection SQLite impossible)
4. Pilier 4 : UX & Observabilité (Inspection des tables et enregistrements paginés standards_graph.db)
"""
import pytest
from fastapi.testclient import TestClient

from src.dashboard.server import app


@pytest.fixture
def client():
    return TestClient(app)


# ── PILIER 1 : CHEMIN NOMINAL (GRAPHE GRAPHIFY & MÉTADONNÉES) ─────────────────

def test_graph_metadata_nominal(client):
    """Vérifie la récupération des métadonnées du graphe Graphify (mLoop)."""
    resp = client.get("/api/graph/metadata?project=mLoop")
    assert resp.status_code == 200
    data = resp.json()
    assert "project" in data
    assert "has_graph" in data
    assert "nodes_count" in data
    assert "edges_count" in data
    assert "god_nodes" in data
    assert isinstance(data["god_nodes"], list)


def test_graph_html_nominal_if_present(client):
    """Vérifie la restitution du fichier HTML du graphe s'il est compilé."""
    resp = client.get("/api/graph/html?project=mLoop")
    # Si graph.html existe sur disque, status 200 et type text/html
    if resp.status_code == 200:
        assert "text/html" in resp.headers.get("content-type", "")
        assert len(resp.text) > 100
    else:
        assert resp.status_code == 404


# ── PILIER 2 : EXCEPTIONS & REJETS MÉTIER (PROJET SANS GRAPHE) ────────────────

def test_graph_html_missing_returns_404(client):
    """Vérifie le retour 404 propre lorsqu'un projet ne possède pas de graph.html."""
    resp = client.get("/api/graph/html?project=App_Sante")
    assert resp.status_code == 404
    data = resp.json()
    assert "detail" in data
    assert "non trouvé" in data["detail"].lower() or "not found" in data["detail"].lower()


# ── PILIER 3 : RÉSILIENCE & SÉCURITÉ SQLITE (READ-ONLY & 403 REJECT) ─────────

def test_database_tables_rejects_path_traversal(client):
    """Vérifie le rejet 403 strict en cas de tentative de path traversal."""
    resp = client.get("/api/database/tables?db=../../windows/system32/cmd.exe")
    assert resp.status_code == 403
    data = resp.json()
    assert "non autorisée" in data["detail"].lower() or "interdit" in data["detail"].lower()


def test_database_tables_rejects_non_whitelisted_db(client):
    """Vérifie le rejet d'une base non autorisée ou arbitraire."""
    resp = client.get("/api/database/tables?db=secret_passwords.db")
    assert resp.status_code in (403, 404)


def test_database_records_rejects_sql_injection(client):
    """Vérifie le rejet de toute tentative d'injection SQL dans le nom de table."""
    resp = client.get("/api/database/records?db=standards_graph.db&table=standards_nodes;DROP%20TABLE%20users")
    assert resp.status_code in (400, 403)


# ── PILIER 4 : UX & OBSERVABILITÉ (TABLES & ENREGISTREMENTS PAGINÉS) ──────────

def test_database_list_databases_nominal(client):
    """Vérifie la découverte des bases SQLite autorisées."""
    resp = client.get("/api/database/list?project=mLoop")
    assert resp.status_code == 200
    data = resp.json()
    assert "databases" in data
    assert isinstance(data["databases"], list)
    assert any("standards_graph.db" in db["name"] for db in data["databases"])


def test_database_tables_inspection_nominal(client):
    """Vérifie l'inspection des tables de standards_graph.db."""
    resp = client.get("/api/database/tables?db=standards_graph.db")
    assert resp.status_code == 200
    data = resp.json()
    assert "database" in data
    assert "tables" in data
    table_names = [t["name"] for t in data["tables"]]
    assert "standards_nodes" in table_names
    assert "standards_edges" in table_names


def test_database_records_pagination_nominal(client):
    """Vérifie la lecture paginée en mode lecture seule."""
    resp = client.get("/api/database/records?db=standards_graph.db&table=standards_nodes&page=1&page_size=10")
    assert resp.status_code == 200
    data = resp.json()
    assert "table" in data
    assert data["table"] == "standards_nodes"
    assert "columns" in data
    assert "id" in data["columns"]
    assert "records" in data
    assert "total_records" in data
    assert "total_pages" in data
    assert "current_page" in data
    assert data["current_page"] == 1
    assert len(data["records"]) <= 10
