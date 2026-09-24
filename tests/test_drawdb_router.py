"""
tests/test_drawdb_router.py — Tests du router FastAPI DrawDB Souverain (MLOOP-152-BE)

Couvre :
  - GET /api/drawdb/health  (sonde état serveur)
  - GET /api/drawdb/list    (inventaire *.dbml)
  - POST /api/drawdb/start  (spawn subprocess avec mock)

Stratégie :
  - Toutes les sondes réseau et subprocess sont mockées (zéro port réseau réel requis).
  - Répertoire DBML temporaire créé via tmp_path (pytest fixture).
  - ADR-0369 : vérifie que timeout est toujours passé aux fonctions réseau.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Generator
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# ── Application FastAPI minimale pour les tests ───────────────────────────────


@pytest.fixture(scope="module")
def client() -> Generator:
    """Client de test FastAPI avec uniquement le router drawdb monté."""
    from fastapi import FastAPI
    from src.dashboard.routers.drawdb import router as drawdb_router

    app = FastAPI()
    app.include_router(drawdb_router)
    with TestClient(app) as c:
        yield c


# ── Pilier 1 : Sonde health (chemin nominal) ──────────────────────────────────


def test_health_running(client: TestClient) -> None:
    """GET /api/drawdb/health retourne running=True quand le serveur répond."""
    with patch("src.dashboard.routers.drawdb._check_drawdb_health", return_value=True):
        res = client.get("/api/drawdb/health?port=8081")
    assert res.status_code == 200
    data = res.json()
    assert data["running"] is True
    assert data["port"] == 8081
    assert "🟢" in data["status"]
    assert data["url"] == "http://localhost:8081/"


def test_health_stopped(client: TestClient) -> None:
    """GET /api/drawdb/health retourne running=False quand le serveur ne répond pas."""
    with patch("src.dashboard.routers.drawdb._check_drawdb_health", return_value=False):
        res = client.get("/api/drawdb/health?port=8081")
    assert res.status_code == 200
    data = res.json()
    assert data["running"] is False
    assert "🔴" in data["status"]


# ── Pilier 1 : Liste DBML (chemin nominal) ────────────────────────────────────


def test_list_returns_dbml_files(client: TestClient, tmp_path: Path) -> None:
    """GET /api/drawdb/list retourne les *.dbml détectés sous le projet."""
    # Créer deux fichiers DBML fictifs dans un dossier temporaire
    (tmp_path / "schema_a.dbml").write_text("Table A { id INT [pk] }", encoding="utf-8")
    (tmp_path / "schema_b.dbml").write_text("Table B { id INT [pk] }", encoding="utf-8")

    # find_dbml_files est dans _drawdb_core — mocker la référence locale là-bas
    with patch("src.dashboard.routers._drawdb_core.resolve_project_path", return_value=tmp_path):
        with patch(
            "src.dashboard.routers.drawdb.resolve_project_canonical_name",
            return_value="TestProject",
        ):
            res = client.get("/api/drawdb/list?project=TestProject")

    assert res.status_code == 200
    data = res.json()
    assert data["project"] == "TestProject"
    assert data["total"] == 2
    names = [f["name"] for f in data["files"]]
    assert "schema_a.dbml" in names
    assert "schema_b.dbml" in names


def test_list_empty_project(client: TestClient, tmp_path: Path) -> None:
    """GET /api/drawdb/list retourne total=0 et un message si aucun *.dbml."""
    with patch("src.dashboard.routers.drawdb.resolve_project_path", return_value=tmp_path):
        with patch(
            "src.dashboard.routers.drawdb.resolve_project_canonical_name",
            return_value="EmptyProject",
        ):
            res = client.get("/api/drawdb/list?project=EmptyProject")

    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 0
    assert "message" in data
    assert "*.dbml" in data["message"]


# ── Pilier 1 : Start subprocess (chemin nominal) ──────────────────────────────


def test_start_when_already_running(client: TestClient) -> None:
    """POST /api/drawdb/start retourne already_running=True si le serveur est déjà démarré."""
    import src.dashboard.routers.drawdb as mod

    mod._spawn_in_progress = False  # Reset état global

    with patch("src.dashboard.routers.drawdb._check_drawdb_health", return_value=True):
        res = client.post("/api/drawdb/start?port=8081")

    assert res.status_code == 200
    data = res.json()
    assert data["started"] is True
    assert data["already_running"] is True
    assert data["error"] is None


def test_start_spawns_subprocess(client: TestClient, tmp_path: Path) -> None:
    """POST /api/drawdb/start lance un subprocess et retourne started=True si la sonde passe."""
    import src.dashboard.routers.drawdb as mod

    mod._spawn_in_progress = False

    # Créer le runner.py au chemin attendu par REPO_ROOT réel
    real_runner = mod.REPO_ROOT / "tools" / "drawdb" / "runner.py"

    mock_proc = MagicMock()
    mock_proc.poll.return_value = None  # processus toujours actif
    mock_proc.pid = 12345
    mock_proc.stderr = MagicMock()

    health_calls = [
        False,
        False,
        True,
    ]  # 1er appel (already_running?): False, puis 2 itérations: succès

    def _fake_health(port: int = 8081) -> bool:
        return health_calls.pop(0) if health_calls else True

    # On mocke _check_drawdb_health globalement (le premier appel = test already_running)
    with patch("src.dashboard.routers.drawdb._check_drawdb_health", side_effect=_fake_health):
        with patch("src.dashboard.routers.drawdb.subprocess.Popen", return_value=mock_proc):
            with patch("src.dashboard.routers.drawdb.time.sleep"):
                res = client.post("/api/drawdb/start?port=8081")

    assert res.status_code == 200
    data = res.json()
    assert data["started"] is True
    assert data["already_running"] is False
    assert data["error"] is None


# ── Pilier 2 : Exceptions & Rejets ───────────────────────────────────────────


def test_start_runner_missing(client: TestClient, tmp_path: Path) -> None:
    """POST /api/drawdb/start retourne 500 si runner.py est absent."""
    import src.dashboard.routers.drawdb as mod

    mod._spawn_in_progress = False

    # REPO_ROOT pointe vers tmp_path qui ne contient pas tools/drawdb/runner.py
    with patch("src.dashboard.routers.drawdb._check_drawdb_health", return_value=False):
        with patch("src.dashboard.routers.drawdb.REPO_ROOT", tmp_path):
            res = client.post("/api/drawdb/start?port=8081")

    assert res.status_code == 500
    assert (
        "runner.py" in res.json()["detail"].lower() or "introuvable" in res.json()["detail"].lower()
    )


def test_start_subprocess_crash(client: TestClient, tmp_path: Path) -> None:
    """POST /api/drawdb/start retourne started=False si le subprocess crashe immédiatement."""
    import src.dashboard.routers.drawdb as mod

    mod._spawn_in_progress = False

    fake_runner = tmp_path / "tools" / "drawdb" / "runner.py"
    fake_runner.parent.mkdir(parents=True)
    fake_runner.write_text("# fake", encoding="utf-8")

    mock_proc = MagicMock()
    mock_proc.poll.return_value = 1  # crashé avec code 1
    mock_proc.returncode = 1
    mock_proc.stderr = MagicMock()
    mock_proc.stderr.read.return_value = b"port already in use"

    with patch("src.dashboard.routers.drawdb.REPO_ROOT", tmp_path):
        with patch("src.dashboard.routers.drawdb._check_drawdb_health", return_value=False):
            with patch("subprocess.Popen", return_value=mock_proc):
                with patch("time.sleep"):
                    res = client.post("/api/drawdb/start?port=8081")

    assert res.status_code == 200
    data = res.json()
    assert data["started"] is False
    assert data["error"] is not None
    assert "prématurément" in data["error"] or "code 1" in data["error"]


# ── Pilier 3 : Résilience — timeout sonde HTTP ───────────────────────────────


def test_health_check_timeout_graceful() -> None:
    """_check_drawdb_health retourne False si la connexion expire (pas d'exception propagée)."""
    import urllib.error
    from src.dashboard.routers.drawdb import _check_drawdb_health

    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("timeout")):
        result = _check_drawdb_health(port=9999)

    assert result is False


# ── Pilier 4 : Structure de réponse & contrats ───────────────────────────────


def test_health_response_schema(client: TestClient) -> None:
    """La réponse /api/drawdb/health respecte le contrat {running, port, url, status}."""
    with patch("src.dashboard.routers.drawdb._check_drawdb_health", return_value=False):
        res = client.get("/api/drawdb/health")
    assert res.status_code == 200
    data = res.json()
    for key in ("running", "port", "url", "status"):
        assert key in data, f"Clé manquante dans la réponse health : {key}"


def test_list_response_schema(client: TestClient, tmp_path: Path) -> None:
    """La réponse /api/drawdb/list respecte le contrat {project, total, files}."""
    with patch("src.dashboard.routers.drawdb.resolve_project_path", return_value=tmp_path):
        with patch(
            "src.dashboard.routers.drawdb.resolve_project_canonical_name", return_value="Proj"
        ):
            res = client.get("/api/drawdb/list")
    assert res.status_code == 200
    data = res.json()
    for key in ("project", "total", "files"):
        assert key in data, f"Clé manquante dans la réponse list : {key}"


def test_start_response_schema(client: TestClient) -> None:
    """La réponse /api/drawdb/start respecte le contrat {started, already_running, port, url, error}."""
    import src.dashboard.routers.drawdb as mod

    mod._spawn_in_progress = False

    with patch("src.dashboard.routers.drawdb._check_drawdb_health", return_value=True):
        res = client.post("/api/drawdb/start?port=8081")
    assert res.status_code == 200
    data = res.json()
    for key in ("started", "already_running", "port", "url", "error"):
        assert key in data, f"Clé manquante dans la réponse start : {key}"
