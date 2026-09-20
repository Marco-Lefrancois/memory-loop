# -*- coding: utf-8 -*-
"""
Harnais de performance — Rénovation Modulaire des Utilitaires (MLOOP-101-BE / Arbitrage #4).

Vérifie deux garanties déterministes :
1. Latence : temps de réponse unitaire moyen < 5 ms pour resolve_project_alias
   et resolve_story_query.
2. Plafonds structurels : chaque module du périmètre est ≤ 300 lignes physiques
   et ≤ 15 Ko (ADR-0202).
"""

from __future__ import annotations

import time
from pathlib import Path

import pytest


# ─────────────────────────────────────────────────────────────────────────────
# 1. Modules périmètre MLOOP-101-BE (plafonds ADR-0202)
# ─────────────────────────────────────────────────────────────────────────────

PERIMETRE_MODULES = [
    "src/utils/lexicon_resolver.py",
    "src/utils/lexicon/__init__.py",
    "src/utils/lexicon/entity_matcher.py",
    "src/utils/lexicon/project_resolver.py",
    "src/utils/token_ledger/__init__.py",
    "src/utils/token_ledger/reporting.py",
    "src/utils/token_ledger/key_info.py",
    "src/utils/file_lock.py",
    "src/utils/context_guard.py",
    "src/utils/opencode_meter.py",
    "src/utils/context_monitor.py",
    "src/utils/lexical_guard.py",
    "src/utils/antigravity_meter.py",
]

MAX_LINES = 300
MAX_BYTES = 15_360  # 15 Ko


@pytest.mark.parametrize("rel_path", PERIMETRE_MODULES)
def test_module_line_and_size_ceiling(rel_path: str) -> None:
    """Garantit que chaque module du périmètre respecte ≤ 300 lignes et ≤ 15 Ko (ADR-0202)."""
    repo_root = Path(__file__).parent.parent.parent
    module_path = repo_root / rel_path

    assert module_path.exists(), f"Module introuvable : {rel_path}"

    content = module_path.read_text(encoding="utf-8")
    line_count = len(content.splitlines())
    byte_size = len(content.encode("utf-8"))

    assert line_count <= MAX_LINES, (
        f"{rel_path} dépasse le plafond de {MAX_LINES} lignes ({line_count} lignes)"
    )
    assert byte_size <= MAX_BYTES, (
        f"{rel_path} dépasse le plafond de {MAX_BYTES} octets ({byte_size} octets)"
    )


# ─────────────────────────────────────────────────────────────────────────────
# 2. Latence — resolve_project_alias < 5 ms (moyenne sur 20 appels)
# ─────────────────────────────────────────────────────────────────────────────

LATENCY_THRESHOLD_MS = 5.0
WARMUP_RUNS = 3
MEASURE_RUNS = 20


def test_resolve_project_alias_latency(tmp_path: Path) -> None:
    """
    Vérifie que resolve_project_alias produit un temps de réponse moyen < 5 ms
    sur 20 appels consécutifs avec un répertoire de projets synthétique minimal.
    """
    from src.utils.lexicon_resolver import SemanticLexiconResolver

    # Construire 3 projets synthétiques avec structure SSOT minimale
    base = tmp_path / "Projects"
    base.mkdir()
    for name in ["Alpha_Widget", "Beta_Widget", "Gamma_Widget"]:
        proj = base / name
        (proj / "backlog").mkdir(parents=True)
        (proj / "backlog" / "sprint_backlog.md").write_text("# Sprint", encoding="utf-8")

    # Chauffe
    for _ in range(WARMUP_RUNS):
        SemanticLexiconResolver.resolve_project_alias("Alpha_Widget", base_dir=str(base))

    # Mesure
    durations_ms: list[float] = []
    for _ in range(MEASURE_RUNS):
        t0 = time.perf_counter()
        SemanticLexiconResolver.resolve_project_alias("Alpha_Widget", base_dir=str(base))
        t1 = time.perf_counter()
        durations_ms.append((t1 - t0) * 1000.0)

    avg_ms = sum(durations_ms) / len(durations_ms)
    assert avg_ms < LATENCY_THRESHOLD_MS, (
        f"resolve_project_alias : latence moyenne {avg_ms:.3f} ms dépasse le seuil de {LATENCY_THRESHOLD_MS} ms"
    )


def test_resolve_story_query_latency(tmp_path: Path) -> None:
    """
    Vérifie que resolve_story_query produit un temps de réponse moyen < 5 ms
    sur 20 appels consécutifs avec un backlog synthétique minimal.
    """
    from src.utils.lexicon_resolver import SemanticLexiconResolver

    stories_dir = tmp_path / "backlog" / "stories"
    stories_dir.mkdir(parents=True)

    # Créer 5 stories synthétiques
    for i in range(1, 6):
        story_file = stories_dir / f"MLOOP-{i:03d}-BE.md"
        story_file.write_text(
            f"""---
id: MLOOP-{i:03d}-BE
jira_key: '-'
status: READY_FOR_DEV
title: Story Test {i}
tags:
- test
- performance
---
# Story Test {i}

## Description
Story de test numéro {i} pour le harnais de performance.
""",
            encoding="utf-8",
        )

    # Chauffe
    for _ in range(WARMUP_RUNS):
        SemanticLexiconResolver.resolve_story_query("MLOOP-003-BE", stories_dir)

    # Mesure
    durations_ms: list[float] = []
    for _ in range(MEASURE_RUNS):
        t0 = time.perf_counter()
        SemanticLexiconResolver.resolve_story_query("MLOOP-003-BE", stories_dir)
        t1 = time.perf_counter()
        durations_ms.append((t1 - t0) * 1000.0)

    avg_ms = sum(durations_ms) / len(durations_ms)
    assert avg_ms < LATENCY_THRESHOLD_MS, (
        f"resolve_story_query : latence moyenne {avg_ms:.3f} ms dépasse le seuil de {LATENCY_THRESHOLD_MS} ms"
    )
