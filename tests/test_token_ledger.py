# -*- coding: utf-8 -*-
"""Unit tests for TokenLedger and Key-Project Binding Guardrail (ADR-0329)."""

import pytest
import json
from pathlib import Path
from src.utils.token_ledger import TokenLedger
from src.pipelines.vibe_check import run_vibe_check


def test_token_ledger_record_and_query(tmp_path: Path):
    """Vérifie l'enregistrement et le calcul des coûts/tokens."""
    entry = TokenLedger.record_interaction(
        project_name="TestProject",
        action="rubber-duck",
        model="gemini-3-flash-preview-thinking",
        prompt_tokens=10_000,
        completion_tokens=1_000,
        target="TEST-001.md",
        context_contributors=["docs/index.md"],
        root_dir=tmp_path,
    )

    assert entry["project"] == "TestProject"
    assert entry["total_tokens_est"] == 11_000
    assert entry["cost_usd_est"] > 0.0

    entries = TokenLedger.load_entries(project_name="TestProject", root_dir=tmp_path)
    assert len(entries) == 1
    assert entries[0]["target"] == "TEST-001.md"

    report = TokenLedger.generate_report(project_name="TestProject", root_dir=tmp_path)
    assert "TestProject" in report
    assert "TEST-001.md" in report


def test_vibe_check_key_alignment(monkeypatch):
    """Vérifie le contrôle d'alignement clé LiteLLM vs projet (ADR-0329)."""
    # 1. Avec clé alignée pour Boire
    monkeypatch.setattr(
        TokenLedger,
        "resolve_active_key_info",
        classmethod(lambda cls: {"key_label": "Boire et Frère", "key_masked": "sk-o2o1...", "key_raw": "sk-o2o1"}),
    )
    res_boire = run_vibe_check(project_name="BoireFrere_Segment2")
    check_item = next(c for c in res_boire["checks"] if "Alignement Projet" in c["check"])
    assert check_item["status"] == "PASS"

    # 2. Avec clé alignée pour Metro
    monkeypatch.setattr(
        TokenLedger,
        "resolve_active_key_info",
        classmethod(lambda cls: {"key_label": "Metro", "key_masked": "sk-m3N2...", "key_raw": "sk-m3N2"}),
    )
    res_metro = run_vibe_check(project_name="Metro_FOOD")
    check_metro = next(c for c in res_metro["checks"] if "Alignement Projet" in c["check"])
    assert check_metro["status"] == "PASS"
