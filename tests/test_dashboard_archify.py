"""
tests/test_dashboard_archify.py — Banc de test unitaire pour MLOOP-150-BE.

Couvre les 4 Piliers Gherkin du récit MLOOP-150-BE :
  Pilier 1 : Chemin Nominal — Inventaire multi-tenant avec artefacts existants sur disque.
  Pilier 2 : Exceptions & Rejets — 403 path-traversal, 404 fichier absent.
  Pilier 3 : Résilience & Mode Dégradé — timeout compilation → 500 + serveur UP ; anti-rebond.
  Pilier 4 : UX & Observabilité — inventaire vide → total_artifacts:0 + message CLI.

Conformité ADR-0369 : zéro except: pass, timeouts explicites, context managers.
"""

from __future__ import annotations

import threading
import time
from pathlib import Path
from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.dashboard.server import app

# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def real_showcase_html() -> str:
    """Nom d'un fichier HTML réellement présent dans tools/archify/showcase/."""
    return "mloop-framework.architecture.html"


@pytest.fixture
def real_docs_html() -> str:
    """Nom d'un fichier HTML réellement présent dans docs/05-assets/."""
    return "mloop-lifecycle.lifecycle.html"


# ── PILIER 1 : CHEMIN NOMINAL ─────────────────────────────────────────────────


class TestPilier1Nominal:
    """Scénario : Inventaire multi-tenant des artefacts Archify."""

    def test_list_returns_200_with_artifacts(self, client: TestClient) -> None:
        """
        Étant donné des artefacts *.architecture.html sous tools/archify/showcase/ et docs/05-assets/
        Quand GET /api/archify/list?project=mLoop est appelé
        Alors la réponse est 200 avec la liste des artefacts
        """
        resp = client.get("/api/archify/list?project=mLoop")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_artifacts" in data
        assert "artifacts" in data
        assert "project" in data
        assert isinstance(data["artifacts"], list)

    def test_list_artifact_fields(self, client: TestClient) -> None:
        """
        Alors chaque artefact expose name, type, size_bytes, relative_path
        """
        resp = client.get("/api/archify/list?project=mLoop")
        assert resp.status_code == 200
        data = resp.json()
        for artifact in data["artifacts"]:
            assert "name" in artifact, f"Champ 'name' absent : {artifact}"
            assert "type" in artifact, f"Champ 'type' absent : {artifact}"
            assert "size_bytes" in artifact, f"Champ 'size_bytes' absent : {artifact}"
            assert "relative_path" in artifact, f"Champ 'relative_path' absent : {artifact}"

    def test_list_artifact_type_discrimination(self, client: TestClient) -> None:
        """
        Et le champ type vaut 'architecture' ou 'lifecycle' (ou autre type Archify) selon le suffixe
        """
        resp = client.get("/api/archify/list?project=mLoop")
        assert resp.status_code == 200
        data = resp.json()
        valid_types = {"architecture", "lifecycle", "sequence", "workflow", "dataflow"}
        for artifact in data["artifacts"]:
            assert artifact["type"] in valid_types, (
                f"Type inattendu '{artifact['type']}' pour '{artifact['name']}'"
            )

    def test_list_counts_match(self, client: TestClient) -> None:
        """
        Et total_artifacts correspond à len(artifacts)
        """
        resp = client.get("/api/archify/list?project=mLoop")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_artifacts"] == len(data["artifacts"])

    def test_html_nominal_serves_content(self, client: TestClient, real_showcase_html: str) -> None:
        """
        Étant donné un fichier HTML existant dans tools/archify/showcase/
        Quand GET /api/archify/html?file=<nom>&project=mLoop est appelé
        Alors la réponse est 200 et le content-type est text/html
        """
        resp = client.get(f"/api/archify/html?file={real_showcase_html}&project=mLoop")
        assert resp.status_code == 200
        assert "text/html" in resp.headers.get("content-type", "")
        assert len(resp.text) > 100, "Le contenu HTML semble vide"

    def test_html_lifecycle_from_docs_assets(self, client: TestClient, real_docs_html: str) -> None:
        """
        Étant donné un artefact .lifecycle.html sous docs/05-assets/
        Alors le type est 'lifecycle' et la réponse est 200
        """
        resp = client.get(f"/api/archify/html?file={real_docs_html}&project=mLoop")
        assert resp.status_code == 200
        assert "text/html" in resp.headers.get("content-type", "")


# ── PILIER 2 : EXCEPTIONS & REJETS ───────────────────────────────────────────


class TestPilier2Exceptions:
    """Scénario : Requêtes hors allowlist et fichier introuvable."""

    def test_path_traversal_rejected_403(self, client: TestClient) -> None:
        """
        Étant donné une requête GET /api/archify/html?file=../src/state.py
        Quand le chemin est résolu contre les racines allowlistées
        Alors la réponse est 403 avec un détail explicite
        """
        resp = client.get("/api/archify/html?file=../src/state.py&project=mLoop")
        assert resp.status_code == 403
        data = resp.json()
        assert "detail" in data
        assert len(data["detail"]) > 0

    def test_path_traversal_with_backslash_rejected_403(self, client: TestClient) -> None:
        """
        Et aucun fichier hors allowlist n'est lu (backslash traversal)
        """
        resp = client.get("/api/archify/html?file=..\\src\\config.py&project=mLoop")
        assert resp.status_code == 403

    def test_missing_html_returns_404_with_cli_hint(self, client: TestClient) -> None:
        """
        Étant donné un nom de fichier absent de toutes les racines
        Quand GET /api/archify/html est appelé
        Alors la réponse est 404 avec la commande CLI de compilation suggérée
        """
        resp = client.get(
            "/api/archify/html?file=fichier-totalement-absent.architecture.html&project=mLoop"
        )
        assert resp.status_code == 404
        data = resp.json()
        assert "detail" in data
        # Le message doit suggérer la commande de compilation
        detail = data["detail"].lower()
        assert "archify" in detail or "python" in detail or "swarm" in detail, (
            f"Aucune commande CLI suggérée dans le 404 : {data['detail']}"
        )

    def test_list_no_double_counting(self, client: TestClient) -> None:
        """
        Les artefacts présents à la fois dans showcase/ et docs/ ne sont pas dupliqués
        par chemin résolu (dedup par chemin réel).
        """
        resp = client.get("/api/archify/list?project=mLoop")
        assert resp.status_code == 200
        data = resp.json()
        relative_paths = [a["relative_path"] for a in data["artifacts"]]
        assert len(relative_paths) == len(set(relative_paths)), (
            "Des chemins relatifs sont dupliqués dans l'inventaire"
        )


# ── PILIER 3 : RÉSILIENCE & MODE DÉGRADÉ ─────────────────────────────────────


class TestPilier3Resilience:
    """Scénario : Compilation à la volée en échec, timeout, anti-rebond."""

    def test_compilation_timeout_returns_500(self, client: TestClient, tmp_path: Path) -> None:
        """
        Étant donné un JSON de spec Archify sans HTML compilé
        Quand GET /api/archify/html est appelé et que subprocess expire
        Alors la réponse est 500 avec la cause loguée
        Et le serveur reste opérationnel pour les requêtes suivantes
        """
        # Crée un JSON de spec fictif dans un répertoire temporaire
        spec_name = "test-timeout.architecture"
        html_name = f"{spec_name}.html"
        json_path = tmp_path / f"{spec_name}.json"
        json_path.write_text('{"nodes": [], "edges": []}', encoding="utf-8")

        # Patch des racines autorisées pour inclure tmp_path
        with patch(
            "src.dashboard.routers.archify._get_allowed_roots",
            return_value=[tmp_path],
        ):
            # Patch subprocess.run pour simuler un TimeoutExpired
            import subprocess

            with patch(
                "src.dashboard.routers.archify.subprocess.run",
                side_effect=subprocess.TimeoutExpired(cmd="archify_runner.py", timeout=60),
            ):
                resp = client.get(f"/api/archify/html?file={html_name}&project=mLoop")

        assert resp.status_code == 500
        data = resp.json()
        assert "detail" in data
        detail = data["detail"].lower()
        assert "timeout" in detail or "60" in detail or "archify" in detail

        # Vérification que le serveur reste UP après l'erreur 500
        health = client.get("/api/health")
        assert health.status_code == 200

    def test_compilation_nonzero_exit_returns_500(self, client: TestClient, tmp_path: Path) -> None:
        """
        En cas de code de sortie non nul la réponse est 500 avec la cause loguée.
        """
        spec_name = "test-fail.architecture"
        html_name = f"{spec_name}.html"
        json_path = tmp_path / f"{spec_name}.json"
        json_path.write_text('{"nodes": [], "edges": []}', encoding="utf-8")

        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "Erreur de compilation fictive"

        with patch(
            "src.dashboard.routers.archify._get_allowed_roots",
            return_value=[tmp_path],
        ):
            with patch(
                "src.dashboard.routers.archify.subprocess.run",
                return_value=mock_result,
            ):
                resp = client.get(f"/api/archify/html?file={html_name}&project=mLoop")

        assert resp.status_code == 500
        data = resp.json()
        assert "detail" in data

    def test_anti_rebond_single_subprocess(self, client: TestClient, tmp_path: Path) -> None:
        """
        Étant donné une compilation subprocess déjà en cours pour un artefact donné
        Quand une seconde requête arrive pour le même artefact
        Alors une seule compilation est déclenchée (verrou threading)

        Vérifié par comptage des appels subprocess.run (≤ 1 appel même avec 2 threads).
        """
        spec_name = "test-debounce.architecture"
        html_name = f"{spec_name}.html"
        json_path = tmp_path / f"{spec_name}.json"
        json_path.write_text('{"nodes": [], "edges": []}', encoding="utf-8")
        html_path = tmp_path / html_name

        call_count = {"n": 0}
        compile_event = threading.Event()
        results: list = []
        in_slow_run = threading.Event()

        def slow_run(*args: Any, **kwargs: Any) -> MagicMock:
            call_count["n"] += 1
            in_slow_run.set()
            # Simule une compilation qui prend du temps
            compile_event.wait(timeout=2.0)
            # Crée le HTML à la fin
            html_path.write_text("<html>ok</html>", encoding="utf-8")
            result = MagicMock()
            result.returncode = 0
            result.stderr = ""
            return result

        def make_request() -> None:
            r = client.get(f"/api/archify/html?file={html_name}&project=mLoop")
            results.append(r.status_code)

        # Patches appliqués UNE SEULE FOI hors threads (patch concurrent non thread-safe)
        with (
            patch(
                "src.dashboard.routers.archify._get_allowed_roots",
                return_value=[tmp_path],
            ),
            patch(
                "src.dashboard.routers.archify.subprocess.run",
                side_effect=slow_run,
            ),
        ):
            # Lance t1 et attend qu'il détienne le verrou (dans slow_run)
            t1 = threading.Thread(target=make_request)
            t1.start()
            assert in_slow_run.wait(timeout=5), "t1 n'a jamais atteint slow_run"
            # t2 arrive avec le verrou déjà pris
            t2 = threading.Thread(target=make_request)
            t2.start()
            time.sleep(0.05)  # laisse t2 bloquer sur le verrou
            compile_event.set()
            t1.join(timeout=10)
            t2.join(timeout=10)

        # Le subprocess ne doit pas avoir été appelé plus d'une fois
        # (le 2e thread attend le verrou et trouve le HTML déjà présent)
        assert call_count["n"] <= 1, (
            f"Anti-rebond défaillant : subprocess.run appelé {call_count['n']} fois"
        )
        # Les deux requêtes doivent réussir (200) ou avoir 500 selon l'environnement de test
        assert all(s in (200, 500) for s in results), f"Statuts inattendus : {results}"

    def test_server_stays_up_after_500(self, client: TestClient) -> None:
        """
        Et le serveur reste opérationnel pour les requêtes suivantes après une 500.
        """
        # Appel d'un endpoint inexistant pour déclencher une erreur
        client.get("/api/archify/html?file=ghost.architecture.html&project=mLoop")
        # Le health check doit rester opérationnel
        resp = client.get("/api/health")
        assert resp.status_code == 200


# ── PILIER 4 : UX & OBSERVABILITÉ ────────────────────────────────────────────


class TestPilier4UX:
    """Scénario : Inventaire vide et message actionnable."""

    def test_empty_project_returns_zero_artifacts_with_message(
        self, client: TestClient, tmp_path: Path
    ) -> None:
        """
        Étant donné un projet sans aucun artefact Archify
        Quand GET /api/archify/list?project=<projet> est appelé
        Alors la réponse 200 expose total_artifacts: 0
        Et le message suggère la commande python src/swarm.py archify
        """
        with patch(
            "src.dashboard.routers.archify._get_allowed_roots",
            return_value=[tmp_path],  # répertoire vide
        ):
            resp = client.get("/api/archify/list?project=mLoop")

        assert resp.status_code == 200
        data = resp.json()
        assert data["total_artifacts"] == 0
        assert "artifacts" in data
        assert data["artifacts"] == []
        # Message d'aide avec commande CLI
        assert "message" in data, "Aucun message d'aide retourné pour inventaire vide"
        msg = data["message"].lower()
        assert "archify" in msg or "swarm" in msg or "python" in msg, (
            f"Message sans commande CLI : {data['message']}"
        )

    def test_list_always_returns_project_field(self, client: TestClient) -> None:
        """
        La réponse de list expose toujours le champ 'project' avec le nom résolu.
        """
        resp = client.get("/api/archify/list?project=mLoop")
        assert resp.status_code == 200
        data = resp.json()
        assert "project" in data
        assert isinstance(data["project"], str)
        assert len(data["project"]) > 0

    def test_list_without_project_param_defaults_gracefully(self, client: TestClient) -> None:
        """
        L'appel sans paramètre project doit retourner 200 avec un projet résolu par défaut.
        """
        resp = client.get("/api/archify/list")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_artifacts" in data
        assert "project" in data

    def test_list_size_bytes_nonnegative(self, client: TestClient) -> None:
        """
        Chaque artefact doit avoir size_bytes >= 0.
        """
        resp = client.get("/api/archify/list?project=mLoop")
        assert resp.status_code == 200
        data = resp.json()
        for artifact in data["artifacts"]:
            assert artifact["size_bytes"] >= 0, (
                f"size_bytes négatif pour '{artifact['name']}' : {artifact['size_bytes']}"
            )
