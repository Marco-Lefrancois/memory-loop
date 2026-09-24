"""
Tests unitaires pour MLOOP-233-BE : Nettoyage Automatique & Rétention des Artefacts de Session.

Valide la politique de nettoyage de memory/scratch/ et memory/compaction/history/ :
- Purge conditionnelle selon l'âge (older_than_hours) ou mode --all
- Hook de transition de cycle de vie sur DONE_TESTED / SHIPPED
- Plafonnement FIFO strict à 10 checkpoints
- Sanctuarisation absolue de memory/evidence/ et memory/plan/
Conforme ADR-0003, ADR-015, ADR-0202, ADR-0369.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import time

import pytest

from src.commands.handlers.scratch_prune import (
    DEFAULT_OLDER_THAN_HOURS,
    handle_scratch,
    on_story_status_transition,
    prune_compaction_checkpoints,
    prune_scratch_artifacts,
)


@pytest.fixture
def tmp_session_env(tmp_path: Path):
    """Crée l'environnement de test scratch, tmp, evidence, plan, compaction/history."""
    mem_dir = tmp_path / "memory"
    scratch_dir = mem_dir / "scratch"
    tmp_dir = mem_dir / "tmp"
    evidence_dir = mem_dir / "evidence"
    plan_dir = mem_dir / "plan"
    history_dir = mem_dir / "compaction" / "history"

    for d in (scratch_dir, tmp_dir, evidence_dir, plan_dir, history_dir):
        d.mkdir(parents=True, exist_ok=True)

    return tmp_path, scratch_dir, tmp_dir, evidence_dir, plan_dir, history_dir


class TestScratchPruneNominal:
    """Pilier 1 : Scénarios nominaux d'élagage des artefacts temporaires."""

    def test_prune_scratch_older_than_hours(self, tmp_session_env):
        tmp_path, scratch_dir, _, _, _, _ = tmp_session_env

        # Fichier ancien (60h > 48h)
        old_file = scratch_dir / "worker_old_prompt.md"
        old_file.write_text("old prompt", encoding="utf-8")
        past_60h = time.time() - (60 * 3600)
        os.utime(old_file, (past_60h, past_60h))

        # Fichier récent (12h < 48h)
        recent_file = scratch_dir / "worker_recent_prompt.md"
        recent_file.write_text("recent prompt", encoding="utf-8")
        past_12h = time.time() - (12 * 3600)
        os.utime(recent_file, (past_12h, past_12h))

        summary = prune_scratch_artifacts(base_dir=tmp_path, older_than_hours=48, purge_all=False)

        assert summary["pruned_files_count"] == 1
        assert not old_file.exists()
        assert recent_file.exists()

    def test_prune_all_scratch_and_tmp_files(self, tmp_session_env):
        tmp_path, scratch_dir, tmp_dir, _, _, _ = tmp_session_env

        (scratch_dir / "test1.py").write_text("import os", encoding="utf-8")
        (tmp_dir / "temp_calc.json").write_text("{}", encoding="utf-8")

        summary = prune_scratch_artifacts(base_dir=tmp_path, purge_all=True)

        assert summary["pruned_files_count"] == 2
        assert len(list(scratch_dir.iterdir())) == 0
        assert len(list(tmp_dir.iterdir())) == 0


class TestScratchPruneExceptions:
    """Pilier 2 : Sanctuarisation des preuves et validation CLI."""

    def test_sanctuary_evidence_and_plan_never_deleted(self, tmp_session_env):
        tmp_path, scratch_dir, _, evidence_dir, plan_dir, _ = tmp_session_env

        # Fichiers sacrés dans evidence et plan
        fact_dossier = evidence_dir / "MLOOP-233-BE_fact_dossier.md"
        fact_dossier.write_text("Fact dossier content", encoding="utf-8")
        plan_doc = plan_dir / "architecture_plan.md"
        plan_doc.write_text("Architecture plan", encoding="utf-8")

        # Fichier scratch jetable
        scratch_file = scratch_dir / "throwaway.txt"
        scratch_file.write_text("to delete", encoding="utf-8")

        summary = prune_scratch_artifacts(base_dir=tmp_path, purge_all=True)

        assert summary["pruned_files_count"] == 1
        assert not scratch_file.exists()
        assert fact_dossier.exists()
        assert plan_doc.exists()

    def test_handle_scratch_cli_invalid_action(self, tmp_session_env):
        tmp_path, _, _, _, _, _ = tmp_session_env
        args = argparse.Namespace(action="unknown", older_than_hours=48, all=False)
        exit_code = handle_scratch(args, state=None, project_path=tmp_path)
        assert exit_code == 1

    def test_handle_scratch_cli_invalid_hours(self, tmp_session_env):
        tmp_path, _, _, _, _, _ = tmp_session_env
        args = argparse.Namespace(action="prune", older_than_hours=-10, all=False)
        exit_code = handle_scratch(args, state=None, project_path=tmp_path)
        assert exit_code == 1


class TestScratchPruneResilience:
    """Pilier 3 : Bornage des checkpoints et hook de transition de cycle de vie."""

    def test_compaction_checkpoints_bounded_to_10(self, tmp_session_env):
        tmp_path, _, _, _, _, history_dir = tmp_session_env

        # Création de 15 checkpoints ordonnés par timestamp
        created_files = []
        base_time = time.time() - 3600
        for i in range(15):
            cp_file = history_dir / f"checkpoint_{i:02d}.json"
            cp_file.write_text(f'{{"index": {i}}}', encoding="utf-8")
            ts = base_time + (i * 60)
            os.utime(cp_file, (ts, ts))
            created_files.append(cp_file)

        assert len(list(history_dir.glob("*.json"))) == 15

        pruned = prune_compaction_checkpoints(history_dir=history_dir, max_keep=10)

        remaining = sorted(list(history_dir.glob("*.json")))
        assert len(remaining) == 10
        assert len(pruned) == 5
        # Les 5 plus anciens (00 à 04) doivent avoir été purgés
        for i in range(5):
            assert created_files[i] in pruned
            assert not created_files[i].exists()
        # Les 10 plus récents (05 à 14) doivent subsister
        for i in range(5, 15):
            assert created_files[i].exists()

    def test_story_status_transition_hook_purges_story_scratch(self, tmp_session_env):
        tmp_path, scratch_dir, _, _, _, _ = tmp_session_env

        # Fichiers temporaires pour MLOOP-999-BE
        p1 = scratch_dir / "worker_MLOOP-999-BE_prompt.md"
        r1 = scratch_dir / "worker_MLOOP-999-BE_report.md"
        p1.write_text("prompt", encoding="utf-8")
        r1.write_text("report", encoding="utf-8")

        # Fichier temporaire pour une autre story en cours
        other = scratch_dir / "worker_MLOOP-111-BE_prompt.md"
        other.write_text("unrelated prompt", encoding="utf-8")

        # Déclenchement du hook lors du passage à DONE_TESTED
        res = on_story_status_transition(
            story_id="MLOOP-999-BE",
            new_status="DONE_TESTED",
            base_dir=tmp_path,
        )

        assert res["hook_executed"] is True
        assert res["pruned_count"] == 2
        assert not p1.exists()
        assert not r1.exists()
        assert other.exists()

    def test_story_status_transition_hook_noop_on_in_dev(self, tmp_session_env):
        tmp_path, scratch_dir, _, _, _, _ = tmp_session_env
        p = scratch_dir / "worker_MLOOP-999-BE_prompt.md"
        p.write_text("prompt", encoding="utf-8")

        res = on_story_status_transition(
            story_id="MLOOP-999-BE",
            new_status="IN_DEV",
            base_dir=tmp_path,
        )

        assert res["hook_executed"] is False
        assert p.exists()


class TestScratchPruneObservability:
    """Pilier 4 : UX et exécution CLI."""

    def test_handle_scratch_cli_nominal(self, tmp_session_env):
        tmp_path, scratch_dir, _, _, _, _ = tmp_session_env
        (scratch_dir / "old_script.py").write_text("print(1)", encoding="utf-8")

        args = argparse.Namespace(action="prune", older_than_hours=0, all=True)
        exit_code = handle_scratch(args, state=None, project_path=tmp_path)

        assert exit_code == 0
        assert len(list(scratch_dir.iterdir())) == 0
