"""
Tests unitaires pour MLOOP-313-BE :
Harmonisation Multi-Couches des Consommateurs (_sync_backlog, wikifix, scratch_prune, Dashboard)
"""

from pathlib import Path
import re
import pytest
from src.pipelines.sync._sync_backlog_parser import parse_backlog_status_maps, STATUS_VOCAB_RE
from src.commands.handlers.scratch_prune import on_story_status_transition
from src.dashboard.routers.backlog import STATUS_ORDER


def test_parse_backlog_status_maps_extracts_5_phase_statuses(tmp_path):
    """CA-1 : Extraction exacte de READY_FOR_QA et QA_CERTIFIED sans troncature."""
    backlog_content = """# Sprint Backlog
## MODULE : TEST

| État | Récit | Clé Jira | Composant | Titre | Grill-me | Statut | Responsable |
| :---: | :--- | :---: | :--- | :--- | :---: | :--- | :--- |
| [ ] | **MLOOP-901-BE** | - | Core | Test QA | `✅ DONE` | 🟡 `READY_FOR_QA` | Dev |
| [ ] | **MLOOP-902-BE** | - | Core | Test Cert | `✅ DONE` | 🟢 `QA_CERTIFIED` | QA |
| [ ] | **MLOOP-903-BE** | - | Core | Test Ship | `✅ DONE` | 🚀 `READY_TO_SHIP` | Lead |
| [ ] | **MLOOP-904-BE** | - | Core | Test Done | `✅ DONE` | 🟣 `DONE` | Release |
"""
    backlog_file = tmp_path / "sprint_backlog.md"
    backlog_file.write_text(backlog_content, encoding="utf-8")

    direct_map, cat_map = parse_backlog_status_maps(backlog_file)
    assert direct_map.get("MLOOP-901-BE") == "READY_FOR_QA"
    assert direct_map.get("MLOOP-902-BE") == "QA_CERTIFIED"
    assert direct_map.get("MLOOP-903-BE") == "READY_TO_SHIP"
    assert direct_map.get("MLOOP-904-BE") == "DONE"


def test_status_vocab_re_no_prefix_shadowing():
    """Vérifie que les statuts longs ne sont pas tronqués par des préfixes courts."""
    assert STATUS_VOCAB_RE.search("READY_FOR_QA").group(1) == "READY_FOR_QA"
    assert STATUS_VOCAB_RE.search("READY_FOR_DEV").group(1) == "READY_FOR_DEV"
    assert STATUS_VOCAB_RE.search("QA_CERTIFIED").group(1) == "QA_CERTIFIED"
    assert STATUS_VOCAB_RE.search("READY_TO_SHIP").group(1) == "READY_TO_SHIP"
    assert STATUS_VOCAB_RE.search("DONE_TESTED").group(1) == "DONE_TESTED"
    assert STATUS_VOCAB_RE.search("DONE").group(1) == "DONE"


def test_wikifix_tolerates_ready_for_qa_and_qa_certified():
    """CA-2 : wikifix_core intègre READY_FOR_QA et QA_CERTIFIED dans _tolerated."""
    code = Path("src/pipelines/wikifix_core.py").read_text(encoding="utf-8")
    m = re.search(r'_tolerated\s*=\s*r"([^"]+)"', code)
    assert m is not None, "_tolerated regex not found in wikifix_core.py"
    pattern = m.group(1)
    assert "READY_FOR_QA" in pattern
    assert "QA_CERTIFIED" in pattern
    assert "READY_TO_SHIP" in pattern


def test_scratch_prune_triggers_on_done_and_qa_certified(tmp_path):
    """CA-3 : scratch_prune détecte DONE comme terminal et exécute le hook."""
    res_done = on_story_status_transition("MLOOP-999-BE", "DONE", base_dir=tmp_path)
    assert res_done["hook_executed"] is True

    res_qa = on_story_status_transition("MLOOP-999-BE", "QA_CERTIFIED", base_dir=tmp_path)
    assert res_qa["hook_executed"] is True

    res_in_dev = on_story_status_transition("MLOOP-999-BE", "IN_DEV", base_dir=tmp_path)
    assert res_in_dev["hook_executed"] is False
    assert res_in_dev["reason"] == "status_not_terminal"


def test_dashboard_status_order_5_phases():
    """CA-4 : STATUS_ORDER organise selon la chaîne canonique des 5 phases."""
    order = [
        "DRAFT",
        "IN_ANALYZE",
        "READY_FOR_GROOMING",
        "READY_FOR_DEV",
        "IN_DEV",
        "READY_FOR_QA",
        "QA_CERTIFIED",
        "DONE",
    ]
    for i in range(len(order) - 1):
        assert STATUS_ORDER[order[i]] < STATUS_ORDER[order[i + 1]], f"{order[i]} should precede {order[i+1]}"
