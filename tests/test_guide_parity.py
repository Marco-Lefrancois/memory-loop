"""
Tests automatisés de la Gouvernance Anti-Drift du Guide CLI SSOT (ADR-0370).
Valide la parité 100% stricte entre _registry.py et CLI_PIPELINE_GUIDE.md,
ainsi que le mécanisme d'auto-healing de vibe-check.
"""

import pytest
from pathlib import Path
from src.commands._registry import COMMANDS
from src.pipelines.guide_generator import (
    GUIDE_PATH,
    PHASE_MAPPING,
    check_guide_parity,
    generate_guide_markdown,
    sync_cli_guide,
)
from src.pipelines.vibe_check import run_vibe_check


class TestGuideParity:
    """Suite de tests ADR-0370."""

    def test_all_commands_mapped_in_phase_mapping(self):
        """Vérifie que chaque commande dans _registry.py est mappée dans une phase de guide_generator."""
        unmapped = [cmd for cmd in COMMANDS if cmd not in PHASE_MAPPING]
        assert unmapped == [], f"Commandes non mappées dans PHASE_MAPPING : {unmapped}"

    def test_current_guide_in_perfect_parity(self):
        """Vérifie que CLI_PIPELINE_GUIDE.md actuel est en parfaite parité (103/103)."""
        is_in_sync, total_reg, total_in_guide, missing = check_guide_parity()
        assert is_in_sync is True, f"Désynchronisation détectée : {missing}"
        assert total_reg == len(COMMANDS)
        assert total_in_guide == len(COMMANDS)
        assert len(missing) == 0

    def test_generate_guide_markdown_contains_all_commands(self):
        """Vérifie que le générateur inclut chaque commande CLI."""
        md = generate_guide_markdown()
        for cmd in COMMANDS.keys():
            assert f"`python src/swarm.py {cmd}`" in md, f"Commande manquante dans le markdown : {cmd}"
        assert f"**Commandes Actives** : {len(COMMANDS)}" in md

    def test_auto_healing_restores_drift(self, tmp_path, monkeypatch):
        """Vérifie que la détection d'une dérive puis sync_cli_guide restaure immédiatement la parité."""
        # Simuler un guide incomplet
        original_content = GUIDE_PATH.read_text(encoding="utf-8")
        try:
            # Tronquer le guide
            truncated = "# Guide Tronqué\n**Commandes Actives** : 1\n`python src/swarm.py init`\n"
            GUIDE_PATH.write_text(truncated, encoding="utf-8")

            is_sync, total_reg, total_in_guide, missing = check_guide_parity()
            assert is_sync is False
            assert len(missing) > 50

            # Déclencher la synchronisation (auto-healing)
            ok, msg = sync_cli_guide()
            assert ok is True

            is_sync_after, total_reg_after, total_in_g_after, missing_after = check_guide_parity()
            assert is_sync_after is True
            assert missing_after == []
        finally:
            GUIDE_PATH.write_text(original_content, encoding="utf-8")

    def test_vibe_check_passes_with_check_15(self):
        """Vérifie que vibe-check valide le 17e contrôle (Check 15) sans encombre."""
        res = run_vibe_check("Memory Loop")
        guide_check = [c for c in res["checks"] if "Parité SSOT du Guide CLI" in c["check"]]
        assert len(guide_check) == 1
        assert guide_check[0]["status"] == "PASS"
        assert f"{len(COMMANDS)}/{len(COMMANDS)} commandes" in guide_check[0]["check"]
