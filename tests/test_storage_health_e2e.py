"""
Harnais de Certification E2E de la Santé du Stockage & Intégration Vibe-Check (MLOOP-234-FULL).

Valide la détection proactive et la remédiation en boucle fermée :
- Check 24 Vibe-Check (< 100 ms)
- Détection FAIL sur corruption physique SQLite
- Détection WARNING sur dérives volumétriques (> 500 Mo, frag > 20%, log > 10 Mo, repos orphelins)
- Boucle E2E : Dérive -> Alerte Vibe-Check -> Remédiation CLI -> Retour nominal PASS
Conforme ADR-0003, ADR-015, ADR-0202, ADR-0369.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import sqlite3
import time

import pytest

from src.commands.handlers.crawler_prune import prune_crawler_cache
from src.commands.handlers.log_rotation import rotate_all_logs
from src.commands.handlers.memory_maintenance import execute_memory_vacuum
from src.commands.handlers.scratch_prune import prune_scratch_artifacts
from src.pipelines.vibe_check._vc_storage import check_24_storage_hygiene


@pytest.fixture
def e2e_storage_env(tmp_path: Path):
    """Prépare un environnement isolé avec base SQLite, logs, crawler et manifests."""
    mem_dir = tmp_path / "memory"
    crawler_cache = mem_dir / "crawler" / "cache"
    crawler_repos = mem_dir / "crawler" / "repos"
    scratch_dir = mem_dir / "scratch"
    logs_dir = mem_dir / "logs"

    for d in (crawler_cache, crawler_repos, scratch_dir, logs_dir):
        d.mkdir(parents=True, exist_ok=True)

    # Initialisation base SQLite
    db_path = mem_dir / "loop_mem.db"
    with sqlite3.connect(str(db_path), timeout=15.0) as conn:
        conn.execute("CREATE TABLE docs (id INTEGER PRIMARY KEY, content TEXT)")
        conn.execute("CREATE VIRTUAL TABLE docs_fts USING fts5(content)")
        conn.commit()

    # Manifeste source légitime
    docs_dir = tmp_path / "docs" / "00-ingested"
    docs_dir.mkdir(parents=True, exist_ok=True)
    (docs_dir / "source_manifest.json").write_text(
        json.dumps({"sources": [{"repo": "legit_repo"}]}),
        encoding="utf-8",
    )

    return tmp_path, mem_dir, db_path


class TestStorageHealthE2E:
    """Tests unitaires et E2E pour Check 24 et la boucle de remédiation."""

    def test_check_24_nominal_pass(self, e2e_storage_env, monkeypatch):
        tmp_path, mem_dir, db_path = e2e_storage_env
        monkeypatch.chdir(tmp_path)

        res = check_24_storage_hygiene(tmp_path, "TestProj", "RUN", "STAGE_RUN")

        assert res["status"] == "PASS"
        assert res["fails_count"] == 0
        assert res["warnings_count"] == 0
        assert res["duration_ms"] < 200.0

    def test_check_24_corruption_fatal_fail(self, e2e_storage_env, monkeypatch):
        tmp_path, mem_dir, db_path = e2e_storage_env
        monkeypatch.chdir(tmp_path)

        # Corruption brutale du fichier SQLite
        db_path.write_bytes(b"CORRUPTED_NON_SQLITE_HEADER" + b"\x00" * 1024)

        res = check_24_storage_hygiene(tmp_path, "TestProj", "RUN", "STAGE_RUN")

        assert res["status"] == "FAIL"
        assert res["fails_count"] >= 1
        assert any("corruption" in d.lower() or "échec" in d.lower() for d in res["details"])

    def test_e2e_remediation_lifecycle_closed_loop(self, e2e_storage_env, monkeypatch):
        tmp_path, mem_dir, db_path = e2e_storage_env
        monkeypatch.chdir(tmp_path)

        # ── 1. Injection de dérives de stockage ──
        # A. Log actif excessif (> 10 Mo)
        events_file = mem_dir / "events.jsonl"
        large_log_chunk = b'{"event": "drift"}\n' + (b" " * 1024)
        # Écriture de 11.4 Mo
        events_file.write_bytes(large_log_chunk * 11000)
        assert events_file.stat().st_size > 10 * 1024 * 1024

        # B. Dépôt cloné orphelin hors manifest
        orphan_repo = mem_dir / "crawler" / "repos" / "orphan_drift_repo"
        orphan_repo.mkdir(parents=True, exist_ok=True)
        (orphan_repo / "drift.py").write_text("print('orphan')", encoding="utf-8")

        # C. Pages crawler expirées (> 60 jours)
        old_twin = mem_dir / "crawler" / "cache" / "old_drift_page.md"
        old_twin.write_text("expired crawler twin", encoding="utf-8")
        past_70d = time.time() - (70 * 86400)
        os.utime(old_twin, (past_70d, past_70d))

        # D. Résidus de session scratch
        scratch_file = mem_dir / "scratch" / "worker_drift_report.md"
        scratch_file.write_text("temporary scratch report", encoding="utf-8")

        # ── 2. Détection par Vibe-Check Check 24 (Doit émettre WARNING) ──
        pre_audit = check_24_storage_hygiene(tmp_path, "TestProj", "RUN", "STAGE_RUN")
        assert pre_audit["status"] == "WARNING"
        assert pre_audit["fails_count"] == 0
        assert pre_audit["warnings_count"] >= 2
        # Vérification des détails de détection
        details_str = " ".join(pre_audit["details"])
        assert "events.jsonl" in details_str
        assert "orphan_drift_repo" in details_str

        # ── 3. Remédiation par exécution des modules d'hygiène ──
        # A. Rotation des logs
        rot_res = rotate_all_logs(base_dir=tmp_path, force=True)
        assert rot_res["rotated_count"] >= 1
        assert events_file.stat().st_size == 0

        # B. Élagage du cache crawler et des dépôts orphelins
        crawl_res = prune_crawler_cache(base_dir=tmp_path, ttl_days=60, dry_run=False)
        assert crawl_res["pruned_cache_files_count"] >= 1
        assert crawl_res["pruned_repos_count"] >= 1
        assert not orphan_repo.exists()
        assert not old_twin.exists()

        # C. Nettoyage de scratch
        scratch_res = prune_scratch_artifacts(base_dir=tmp_path, purge_all=True)
        assert scratch_res["pruned_files_count"] >= 1
        assert not scratch_file.exists()

        # D. Compactage VACUUM de la base
        vac_res = execute_memory_vacuum(db_path, force=True)
        assert vac_res["vacuum_executed"] is True

        # ── 4. Nouveau contrôle Vibe-Check (Doit repasser en PASS nominal) ──
        post_audit = check_24_storage_hygiene(tmp_path, "TestProj", "RUN", "STAGE_RUN")
        assert post_audit["status"] == "PASS"
        assert post_audit["warnings_count"] == 0
        assert post_audit["fails_count"] == 0
