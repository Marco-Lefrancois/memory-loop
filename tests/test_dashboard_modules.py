# -*- coding: utf-8 -*-
"""
tests/test_dashboard_modules.py — Tests des modules métiers et granularité backlog (ADR-0369/ADR-0370).
"""

from pathlib import Path
from fastapi.testclient import TestClient
from src.dashboard.server import app
from src.dashboard.module_utils import (
    discover_project_modules,
    get_story_module,
    match_module_entry,
)

client = TestClient(app)


def test_discover_modules_boire():
    mods = discover_project_modules("BoireFrere_Segment2")
    mod_ids = [m["id"] for m in mods]
    assert "01-reception" in mod_ids
    assert "02-incubation" in mod_ids
    assert "03-ventes" in mod_ids
    rec_mod = next(m for m in mods if m["id"] == "01-reception")
    assert rec_mod["has_stories"] is True
    assert rec_mod["stories_count"] >= 20
    assert "Réception" in rec_mod["label"]


def test_discover_modules_metro_food():
    mods = discover_project_modules("Metro_FOOD")
    mod_ids = [m["id"] for m in mods]
    assert "OneTrust_FOOD" in mod_ids
    assert "Metro_Food_Offers" in mod_ids
    assert "PAPERCUTS" in mod_ids
    assert "RBC_Avion" in mod_ids


def test_match_module_entry():
    assert match_module_entry("backlog/stories/01-reception/REC-001.md", "01-reception")
    assert match_module_entry("backlog/stories/01-reception/REC-001.md", "reception")
    assert match_module_entry("REC-008-BE.md", "reception")
    assert match_module_entry("backlog/stories/OneTrust_FOOD/MMA-4637.md", "OneTrust")
    assert match_module_entry("docs/PAPERCUTS/recommandation.md", "papercuts")
    assert not match_module_entry("backlog/stories/02-incubation/INC-001.md", "01-reception")


def test_get_story_module():
    p_root = Path("Projects/BoireFrere_Segment2")
    story_path = p_root / "backlog" / "stories" / "01-reception" / "REC-001.md"
    assert get_story_module(story_path, p_root) == "01-reception"


def test_api_projects_with_modules():
    res = client.get("/api/projects")
    assert res.status_code == 200
    data = res.json()
    assert "modules_by_project" in data
    assert "BoireFrere_Segment2" in data["modules_by_project"]
    bf_mods = [m["id"] for m in data["modules_by_project"]["BoireFrere_Segment2"]]
    assert "01-reception" in bf_mods


def test_api_modules_endpoint():
    res = client.get("/api/modules?project=BoireFrere_Segment2")
    assert res.status_code == 200
    data = res.json()
    assert data["project"] == "BoireFrere_Segment2"
    assert data["total_modules"] >= 3
    mod_ids = [m["id"] for m in data["modules"]]
    assert "01-reception" in mod_ids


def test_api_stories_module_filter():
    # 1. Toutes les stories Boire
    res_all = client.get("/api/stories?project=BoireFrere_Segment2")
    assert res_all.status_code == 200
    data_all = res_all.json()
    assert "by_module" in data_all
    assert "01-reception" in data_all["by_module"]
    assert data_all["total_stories"] >= 30

    # 2. Stories filtrées sur 01-reception
    res_rec = client.get("/api/stories?project=BoireFrere_Segment2&module=01-reception")
    assert res_rec.status_code == 200
    data_rec = res_rec.json()
    assert data_rec["total_stories"] >= 20
    assert all(s["module"] == "01-reception" for s in data_rec["stories"])


def test_api_ledger_module_filter():
    res = client.get("/api/ledger?project=Metro_COMMERCE&module=OneTrust")
    assert res.status_code == 200
    data = res.json()
    assert data["filtered_module"] == "OneTrust"


def test_html_module_selectors_and_backlog_tab():
    res = client.get("/")
    assert res.status_code == 200
    html = res.text
    assert "id=\"module-selector\"" in html
    assert "id=\"tab-btn-backlog\"" in html
    assert "id=\"tab-backlog\"" in html
    assert "id=\"overview-modules-container\"" in html
    assert "Ventilation par Module Métier" in html
    assert "OpenCode Desktop" in html


def test_api_ledger_by_module_breakdown():
    res = client.get("/api/ledger?project=BoireFrere_Segment2")
    assert res.status_code == 200
    data = res.json()
    assert "by_module" in data
    mod_ids = [m["id"] for m in data["by_module"]]
    assert "01-reception" in mod_ids
    assert "02-incubation" in mod_ids

    # Vérifier que 01-reception contient des tokens
    rec = next(m for m in data["by_module"] if m["id"] == "01-reception")
    assert rec["tokens"] > 0
    assert rec["calls"] > 0
    assert "opencode-desktop" in rec["by_source"]


def test_api_ledger_boire_reception_filter():
    res = client.get("/api/ledger?project=BoireFrere_Segment2&module=01-reception")
    assert res.status_code == 200
    data = res.json()
    assert data["filtered_module"] == "01-reception"
    assert data["total_entries"] >= 10
    # Vérifier qu'une entrée provient bien d'opencode-desktop
    sources = {e["source"] for e in data["entries"]}
    assert "opencode-desktop" in sources
    # Vérifier que le module de chaque entrée filtrée est bien 01-reception
    for e in data["entries"]:
        assert e["module"] == "01-reception"
        assert "Réception" in e["module_label"]

