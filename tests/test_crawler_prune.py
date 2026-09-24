"""
Tests unitaires pour MLOOP-232-BE : Gestionnaire de Cycle de Vie & TTL du Cache Crawler.

Valide la politique de rétention du cache crawler :
- TTL 60 jours sur les Markdown Twins
- Immunité absolue pour les métadonnées 'pinned: true' ou 'source: permanent'
- Mode --dry-run sans effet de bord
- Détection et purge des dépôts Git orphelins hors source_manifest.json
Conforme ADR-0003, ADR-015, ADR-0202, ADR-0369.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import time

import pytest

from src.commands.handlers.crawler_prune import (
    DEFAULT_TTL_DAYS,
    handle_crawler,
    is_pinned_or_permanent,
    prune_crawler_cache,
)


@pytest.fixture
def tmp_crawler_env(tmp_path: Path):
    """Crée un environnement complet de test pour le cache et les dépôts du crawler."""
    crawler_dir = tmp_path / "memory" / "crawler"
    cache_dir = crawler_dir / "cache"
    repos_dir = crawler_dir / "repos"
    cache_dir.mkdir(parents=True, exist_ok=True)
    repos_dir.mkdir(parents=True, exist_ok=True)

    manifests_dir = tmp_path / "docs" / "00-ingested"
    manifests_dir.mkdir(parents=True, exist_ok=True)
    manifest_file = manifests_dir / "source_manifest.json"
    manifest_file.write_text(
        json.dumps({
            "manifest_version": "1.0.0",
            "sources": [
                {"repo": "manifested_repo", "filepath": "docs/manifested_repo/README.md"}
            ]
        }),
        encoding="utf-8",
    )

    return tmp_path, cache_dir, repos_dir, manifest_file


class TestCrawlerPruneNominal:
    """Pilier 1 : Scénarios nominaux d'élagage et immunité pinned."""

    def test_prune_expired_files_and_preserves_pinned(self, tmp_crawler_env):
        tmp_path, cache_dir, repos_dir, _ = tmp_crawler_env

        # 1. Page expirée (75 jours) sans marqueur
        old_page = cache_dir / "page_old.md"
        old_page.write_text("# Old page content\nNo special markers", encoding="utf-8")
        past_75d = time.time() - (75 * 86400)
        os.utime(old_page, (past_75d, past_75d))

        # 2. Page ancienne (90 jours) avec 'pinned: true' -> Immunité absolue
        pinned_page = cache_dir / "page_pinned.md"
        pinned_page.write_text(
            "---\ntitle: Pinned Page\npinned: true\n---\n# Important content",
            encoding="utf-8",
        )
        past_90d = time.time() - (90 * 86400)
        os.utime(pinned_page, (past_90d, past_90d))

        # 3. Page ancienne (90 jours) avec 'source: permanent' -> Immunité absolue
        perm_page = cache_dir / "page_perm.md"
        perm_page.write_text(
            "---\nsource: permanent\n---\n# Permanent reference",
            encoding="utf-8",
        )
        os.utime(perm_page, (past_90d, past_90d))

        # 4. Page récente (10 jours)
        recent_page = cache_dir / "page_recent.md"
        recent_page.write_text("# Recent content", encoding="utf-8")
        past_10d = time.time() - (10 * 86400)
        os.utime(recent_page, (past_10d, past_10d))

        summary = prune_crawler_cache(base_dir=tmp_path, ttl_days=60, dry_run=False)

        assert summary["pruned_cache_files_count"] == 1
        assert not old_page.exists()
        assert pinned_page.exists()
        assert perm_page.exists()
        assert recent_page.exists()
        assert summary["pinned_protected_count"] >= 2

    def test_is_pinned_or_permanent_detection(self, tmp_path):
        f1 = tmp_path / "f1.md"
        f1.write_text("---\npinned: true\n---\nHello", encoding="utf-8")
        assert is_pinned_or_permanent(f1) is True

        f2 = tmp_path / "f2.md"
        f2.write_text("---\nsource: permanent\n---\nHello", encoding="utf-8")
        assert is_pinned_or_permanent(f2) is True

        f3 = tmp_path / "f3.md"
        f3.write_text("---\npinned: false\n---\nHello", encoding="utf-8")
        assert is_pinned_or_permanent(f3) is False

        f4 = tmp_path / "f4.md"
        f4.write_text("# Just regular markdown without frontmatter", encoding="utf-8")
        assert is_pinned_or_permanent(f4) is False


class TestCrawlerPruneExceptions:
    """Pilier 2 : Mode dry-run et validation des paramètres."""

    def test_dry_run_leaves_disk_untouched(self, tmp_crawler_env):
        tmp_path, cache_dir, repos_dir, _ = tmp_crawler_env

        old_page = cache_dir / "page_old.md"
        old_page.write_text("# Expired twin", encoding="utf-8")
        past_75d = time.time() - (75 * 86400)
        os.utime(old_page, (past_75d, past_75d))

        summary = prune_crawler_cache(base_dir=tmp_path, ttl_days=60, dry_run=True)

        assert summary["dry_run"] is True
        assert summary["pruned_cache_files_count"] == 1
        # En mode dry-run, le fichier physique doit encore exister
        assert old_page.exists()

    def test_handle_crawler_cli_invalid_ttl(self, tmp_crawler_env):
        tmp_path, _, _, _ = tmp_crawler_env
        args = argparse.Namespace(action="prune", ttl_days=-5, dry_run=False)
        exit_code = handle_crawler(args, state=None, project_path=tmp_path)
        assert exit_code == 1

    def test_handle_crawler_cli_invalid_action(self, tmp_crawler_env):
        tmp_path, _, _, _ = tmp_crawler_env
        args = argparse.Namespace(action="invalid", ttl_days=60, dry_run=False)
        exit_code = handle_crawler(args, state=None, project_path=tmp_path)
        assert exit_code == 1


class TestCrawlerPruneResilience:
    """Pilier 3 : Dépôts clonés orphelins et résilience."""

    def test_prune_orphan_cloned_repos(self, tmp_crawler_env):
        tmp_path, _, repos_dir, _ = tmp_crawler_env

        # Dépôt orphelin non présent dans source_manifest.json
        orphan_repo = repos_dir / "openai_codex"
        orphan_repo.mkdir(parents=True, exist_ok=True)
        (orphan_repo / "codex_sample.py").write_text("print('hello')", encoding="utf-8")

        # Dépôt légitime présent dans source_manifest.json
        legit_repo = repos_dir / "manifested_repo"
        legit_repo.mkdir(parents=True, exist_ok=True)
        (legit_repo / "main.py").write_text("print('valid')", encoding="utf-8")

        summary = prune_crawler_cache(base_dir=tmp_path, ttl_days=60, dry_run=False)

        assert not orphan_repo.exists()
        assert legit_repo.exists()
        assert summary["pruned_repos_count"] == 1


class TestCrawlerPruneObservability:
    """Pilier 4 : UX, CLI et restitution chiffrée."""

    def test_handle_crawler_cli_nominal(self, tmp_crawler_env):
        tmp_path, cache_dir, _, _ = tmp_crawler_env
        page = cache_dir / "old_doc.md"
        page.write_text("Old documentation", encoding="utf-8")
        past_100d = time.time() - (100 * 86400)
        os.utime(page, (past_100d, past_100d))

        args = argparse.Namespace(action="prune", ttl_days=60, dry_run=False)
        exit_code = handle_crawler(args, state=None, project_path=tmp_path)

        assert exit_code == 0
        assert not page.exists()
