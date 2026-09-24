"""
Tests unitaires pour MLOOP-231-BE : Middleware de Rotation & Archivage Rotatif des Journaux.

Valide la rotation des fichiers de traçabilité (events.jsonl, traces.json, etc.) :
- Seuil de déclenchement (5.0 Mo ou --force)
- Compression gzip (.gz) vers memory/logs/archive/
- Élagage glissant automatique des archives de plus de 30 jours
- Résilience aux écritures concurrentes et intégrité des données
Conforme ADR-0003, ADR-015, ADR-0202, ADR-0369.
"""

from __future__ import annotations

import argparse
import gzip
import os
from pathlib import Path
import threading
import time
from typing import List

import pytest

from src.commands.handlers.log_rotation import (
    DEFAULT_MAX_BYTES,
    DEFAULT_RETENTION_DAYS,
    handle_logs,
    prune_log_archives,
    rotate_all_logs,
    rotate_single_log,
)


@pytest.fixture
def tmp_memory_env(tmp_path: Path):
    """Crée une arborescence de test memory/ et memory/logs/archive."""
    mem_dir = tmp_path / "memory"
    mem_dir.mkdir(parents=True, exist_ok=True)
    logs_dir = mem_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    archive_dir = logs_dir / "archive"
    archive_dir.mkdir(parents=True, exist_ok=True)
    return tmp_path, mem_dir, archive_dir


class TestLogRotationNominal:
    """Pilier 1 : Scénarios nominaux de rotation et compression gzip."""

    def test_rotate_single_log_threshold_exceeded(self, tmp_memory_env):
        tmp_path, mem_dir, archive_dir = tmp_memory_env
        log_file = mem_dir / "events.jsonl"
        
        # Écriture de 200 Ko de fausses données avec un seuil abaissé à 100 Ko pour le test
        dummy_line = '{"event": "test_span", "index": 42}\n'
        log_file.write_text(dummy_line * 5000, encoding="utf-8")
        original_size = log_file.stat().st_size
        assert original_size > 100 * 1024

        archive_path = rotate_single_log(
            log_file,
            max_bytes=100 * 1024,
            force=False,
            archive_dir=archive_dir,
        )

        assert archive_path is not None
        assert archive_path.exists()
        assert archive_path.name.endswith(".jsonl.gz")
        assert archive_dir in archive_path.parents

        # Vérification du fichier d'origine réinitialisé
        assert log_file.exists()
        assert log_file.stat().st_size == 0

        # Vérification du contenu compressé (gzip valide)
        with gzip.open(archive_path, "rt", encoding="utf-8") as gz_f:
            decompressed_content = gz_f.read()
        assert decompressed_content == dummy_line * 5000

    def test_rotate_all_logs_multiple_candidates(self, tmp_memory_env):
        tmp_path, mem_dir, archive_dir = tmp_memory_env
        events_file = mem_dir / "events.jsonl"
        traces_file = mem_dir / "global_execution_traces.json"
        
        events_file.write_text('{"event": "e1"}\n' * 5000, encoding="utf-8")
        traces_file.write_text('{"trace": "t1"}\n' * 5000, encoding="utf-8")

        summary = rotate_all_logs(
            base_dir=tmp_path,
            max_bytes=50 * 1024,
            force=False,
            retention_days=30,
        )

        assert summary["rotated_count"] == 2
        assert len(summary["archives_created"]) == 2
        assert events_file.stat().st_size == 0
        assert traces_file.stat().st_size == 0


class TestLogRotationExceptions:
    """Pilier 2 : Exceptions, seuils et rejets d'arguments."""

    def test_rotate_skips_when_below_threshold_unless_force(self, tmp_memory_env):
        tmp_path, mem_dir, archive_dir = tmp_memory_env
        log_file = mem_dir / "events.jsonl"
        log_file.write_text('{"event": "tiny"}\n', encoding="utf-8")

        # Sans force : ignoré car taille < DEFAULT_MAX_BYTES (5 Mo)
        res = rotate_single_log(log_file, max_bytes=DEFAULT_MAX_BYTES, force=False, archive_dir=archive_dir)
        assert res is None
        assert log_file.stat().st_size > 0

        # Avec force : la rotation s'exécute
        res_forced = rotate_single_log(log_file, max_bytes=DEFAULT_MAX_BYTES, force=True, archive_dir=archive_dir)
        assert res_forced is not None
        assert res_forced.exists()
        assert log_file.stat().st_size == 0

    def test_handle_logs_cli_invalid_action(self):
        args = argparse.Namespace(action="invalid_action", force=False)
        exit_code = handle_logs(args, state=None, project_path=None)
        assert exit_code == 1


class TestLogRotationResilience:
    """Pilier 3 : Résilience, concurrence et rétention 30 jours."""

    def test_prune_log_archives_older_than_30_days(self, tmp_memory_env):
        tmp_path, mem_dir, archive_dir = tmp_memory_env

        # 1. Archive vieille de 35 jours (éligible à l'élagage)
        old_archive = archive_dir / "events.20260815_120000.jsonl.gz"
        with gzip.open(old_archive, "wt", encoding="utf-8") as f:
            f.write("old data")
        past_time = time.time() - (35 * 86400)
        os.utime(old_archive, (past_time, past_time))

        # 2. Archive récente de 5 jours (doit être conservée)
        recent_archive = archive_dir / "events.20260919_120000.jsonl.gz"
        with gzip.open(recent_archive, "wt", encoding="utf-8") as f:
            f.write("recent data")
        recent_time = time.time() - (5 * 86400)
        os.utime(recent_archive, (recent_time, recent_time))

        pruned = prune_log_archives(archive_dir, retention_days=30)

        assert old_archive in pruned
        assert not old_archive.exists()
        assert recent_archive.exists()

    def test_concurrent_writes_and_rotation(self, tmp_memory_env):
        tmp_path, mem_dir, archive_dir = tmp_memory_env
        log_file = mem_dir / "events.jsonl"
        log_file.write_text('{"init": true}\n', encoding="utf-8")

        stop_event = threading.Event()
        write_errors: List[Exception] = []

        def worker_writer():
            while not stop_event.is_set():
                try:
                    with open(log_file, "a", encoding="utf-8") as f:
                        f.write('{"event": "stream"}\n')
                    time.sleep(0.001)
                except Exception as exc:
                    write_errors.append(exc)

        # Lancer 3 threads d'écriture continue
        threads = [threading.Thread(target=worker_writer) for _ in range(3)]
        for t in threads:
            t.start()

        # Effectuer une rotation concurrente
        time.sleep(0.05)
        archive_path = rotate_single_log(
            log_file,
            max_bytes=10,
            force=True,
            archive_dir=archive_dir,
        )

        stop_event.set()
        for t in threads:
            t.join()

        assert archive_path is not None
        assert archive_path.exists()
        assert len(write_errors) == 0


class TestLogRotationObservability:
    """Pilier 4 : UX, CLI et Observabilité."""

    def test_handle_logs_cli_nominal(self, tmp_memory_env, monkeypatch):
        tmp_path, mem_dir, archive_dir = tmp_memory_env
        log_file = mem_dir / "events.jsonl"
        log_file.write_text('{"event": "cli_test"}\n' * 50, encoding="utf-8")

        monkeypatch.chdir(tmp_path)
        args = argparse.Namespace(action="rotate", force=True)
        exit_code = handle_logs(args, state=None, project_path=tmp_path)

        assert exit_code == 0
        assert log_file.stat().st_size == 0
        archives = list(archive_dir.glob("*.gz"))
        assert len(archives) == 1

    def test_event_logger_auto_rotates_when_threshold_exceeded(self, tmp_path, monkeypatch):
        from src.utils.event_logger import EventLogger
        logger = EventLogger(project_name="TestProj", base_dir=tmp_path)
        
        # Simuler un fichier events.jsonl préexistant de 5.2 Mo
        large_content = b'{"event": "fill"}\n' + (b" " * (5 * 1024 * 1024 + 1000))
        logger.global_log_file.write_bytes(large_content)
        assert logger.global_log_file.stat().st_size > 5 * 1024 * 1024

        # Émission d'un nouvel événement : doit déclencher l'auto-rotation
        logger.log_event("TOOL", "agent_auto_rot", {"status": "ok"})

        archive_dir = tmp_path / "memory" / "logs" / "archive"
        assert archive_dir.exists()
        archives = list(archive_dir.glob("events.*.jsonl.gz"))
        assert len(archives) >= 1
        # Le fichier global_log_file ne contient que le nouvel événement
        assert logger.global_log_file.stat().st_size < 1000

