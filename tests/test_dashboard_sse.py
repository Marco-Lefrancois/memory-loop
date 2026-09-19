# tests/test_dashboard_sse.py
import pytest
from fastapi.testclient import TestClient

from src.dashboard.server import app

client = TestClient(app)


def test_dashboard_html_contains_new_tabs_and_drawer():
    response = client.get("/")
    assert response.status_code == 200
    html = response.text
    assert "tab-events" in html
    assert "tab-groundtruth" in html
    assert "tab-btn-events" in html
    assert "tab-btn-groundtruth" in html
    assert "backlog-drawer" in html
    assert "backlog-drawer-backdrop" in html
    assert "initEventBusSSE" in html
    assert "openBacklogDrawer" in html
    assert "loadGroundTruth" in html
    assert "renderRhoRules" in html


@pytest.mark.asyncio
async def test_stream_events_generator():
    """Vérifie que le générateur SSE produit bien l'événement initial avec les données."""
    from src.dashboard.server import stream_events
    response = await stream_events(project="ALL", event_type=None)
    assert response.status_code == 200
    assert "text/event-stream" in response.headers.get("content-type", "")

    # Consomme le premier chunk du générateur
    gen = response.body_iterator
    first_chunk = await gen.__anext__()
    assert "event: initial" in first_chunk
    assert "data:" in first_chunk


def test_backlog_project_listing():
    response = client.get("/api/backlog/mLoop-Dashboard")
    assert response.status_code == 200
    data = response.json()
    assert "stories" in data
    assert "total_stories" in data
    assert data["total_stories"] >= 1
    assert data["project"] == "mLoop-Dashboard"

    first_story = data["stories"][0]
    assert "id" in first_story
    assert "title" in first_story
    assert "status" in first_story
    assert "type" in first_story
    assert "scenario_count" in first_story


def test_backlog_story_detail():
    response = client.get("/api/backlog/mLoop-Dashboard/ST-101")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "ST-101"
    assert "scenarios" in data
    assert "business_rules" in data
    assert "file_path" in data
    assert len(data["scenarios"]) >= 1

    scenario = data["scenarios"][0]
    assert "name" in scenario
    assert "steps" in scenario
    assert len(scenario["steps"]) > 0


def test_backlog_story_not_found():
    response = client.get("/api/backlog/mLoop-Dashboard/ST-NONEXISTENT-999")
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data


def test_rho_rules_inventory():
    response = client.get("/api/rho-rules?project=mLoop-Dashboard")
    assert response.status_code == 200
    data = response.json()
    assert "global_rules" in data
    assert "local_rules" in data
    assert "global_rules_count" in data
    assert "local_rules_count" in data
    assert isinstance(data["global_rules"], list)
    assert isinstance(data["local_rules"], list)
