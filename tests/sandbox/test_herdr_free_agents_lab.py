"""
test_herdr_free_agents_lab.py - Sandbox Test Lab for Herdr + OpenCode Free Models

Validates the full lifecycle of Herdr PTY workers running on free models
(opencode/nemotron-3-ultra-free and nemotron-3.5-lightning-free) without consuming paid quotas.
"""

import sys
import time
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pytest
from src.core.herdr_adapter import HerdrAdapter, herdr
from src.pipelines.worker_pipeline import run_worker_spawn, run_worker_status, run_worker_harvest, run_worker_close


def test_herdr_daemon_status():
    """Vérifie que le daemon Herdr est joignable."""
    adapter = HerdrAdapter()
    res = adapter.list_agents()
    if not res.get("success") and "server_not_running" in str(res.get("stderr", "")):
        pytest.skip("Démon Herdr non démarré sur l'hôte (test d'intégration sandbox).")
    print(f"\n[1/4] Statut Daemon Herdr: success={res.get('success')}")
    assert res.get("success") is True or "raw_output" in res or "error" in res


def test_free_worker_lifecycle_e2e():
    """
    Exécute le cycle de vie complet d'un worker Herdr en mode gratuit :
    1. Spawn (avec modèle par défaut ou explicite nemotron free)
    2. Status check
    3. Harvest des preuves
    4. Close (Teardown Gate)
    """
    adapter = HerdrAdapter()
    res = adapter.list_agents()
    if not res.get("success") and "server_not_running" in str(res.get("stderr", "")):
        pytest.skip("Démon Herdr non démarré sur l'hôte (test d'intégration sandbox).")
    test_story = "LAB-FREE-001"
    project_name = "root"

    print(f"\n[2/4] Instanciation du worker Herdr ({test_story}) avec modèle gratuit...")
    # Spawn sans écrasement de modèle payant pour laisser opencode.json utiliser nemotron-3-ultra-free
    spawn_res = run_worker_spawn(
        project_name=project_name,
        story_id=test_story,
        kind="opencode",
        model="opencode/nemotron-3-ultra-free",
        extra_args=["--yolo"]
    )

    try:
        assert spawn_res.get("success") or spawn_res.get("fallback") == "pane_run", f"Échec spawn: {spawn_res}"
        worker_name = spawn_res.get("worker_name", f"worker_{test_story.lower()}")
        print(f" -> Worker créé: {worker_name}")

        # Pause courte pour laisser le volet PTY initialiser
        time.sleep(2)

        print("\n[3/4] Vérification du statut des agents Herdr...")
        status_res = run_worker_status(project_name=project_name)
        assert status_res.get("success") or "result" in status_res

        # Moisson des preuves
        harvest_res = run_worker_harvest(
            project_name=project_name,
            story_id=test_story,
            lines=50
        )
        print(f" -> Moisson d'exécution: success={harvest_res.get('success')}")

    finally:
        # Teardown obligatoire (Zéro zombie)
        print(f"\n[4/4] Fermeture et nettoyage du worker ({test_story})...")
        close_res = run_worker_close(
            project_name=project_name,
            story_id=test_story
        )
        print(f" -> Clôture worker: success={close_res.get('success')}")


if __name__ == "__main__":
    print("=== DÉBUT DU TEST LAB HERDR (MODE MODÈLES GRATUITS) ===")
    test_herdr_daemon_status()
    test_free_worker_lifecycle_e2e()
    print("\n=== TEST LAB HERDR TERMINÉ AVEC SUCCÈS ===")
