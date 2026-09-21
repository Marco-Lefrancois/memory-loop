"""
Tests d'acceptation — MLOOP-144-BE : Instrumentation Logging Jira Sync.

Vérifie que les 4 modules Jira Sync émettent des logs structurés (`extra={...}`)
sur les chemins d'échec/succès, conformément à ADR-0369 (Observabilité, Zero-Silent-Pass)
et aux arbitrages Grill-Me de la story :
  - Payload ADF → hash SHA-256 (16 car.) + champs non-sensibles uniquement.
  - Rate-limit 429 → WARNING avec retry_after.
  - Divergence / échec écriture → ERROR (Fail-Closed).
  - Contexte identité → story_id ET jira_key.

CONTRAINTE CRITIQUE : Zéro appel HTTP réel vers Jira (client entièrement mocké).
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from unittest.mock import MagicMock

import httpx
import pytest

from src.state import SprintBacklogItem, StoryStatus, LoopState
from src.pipelines.jira.jira_item_sync import _update_existing_story, _adf_hash
from src.pipelines.jira.jira_reader import read_jira_issue
from src.pipelines.jira.sync_engine import build_sync_preview
from src.pipelines.jira.jira_report import _write_markdown_report


# ─────────────────────────────────────────────────────────────────────────────
# Helpers / Fixtures
# ─────────────────────────────────────────────────────────────────────────────

_HEX16 = re.compile(r"^[0-9a-f]{16}$")

_SECRET_TOKEN = "SECRET_TOKEN_ABC123"
_SECRET_EMAIL = "secret.user@example.com"
_SECRET_ADF_TEXT = "TEXTE_ADF_CONFIDENTIEL_XYZ"


def _make_item(
    story_id: str = "US-01",
    jira_key: str = "MMA-9001",
    title: str = "Story de test",
) -> SprintBacklogItem:
    return SprintBacklogItem(
        id=story_id,
        title=title,
        description=f"stories/{story_id}.md",
        jira_key=jira_key,
        status=StoryStatus.READY_FOR_DEV,
    )


def _make_state() -> LoopState:
    state = MagicMock(spec=LoopState)
    state.project_name = "TestProjet"
    state.jira_project_key = "MMA"
    state.jira_epic_key = "MMA-1000"
    state.jira_default_subtasks = []
    state.jira_subtask_mapping = {}
    state.jira_default_component_id = None
    state.jira_default_billing_id = None
    return state


def _mock_response(status_code: int, headers: dict | None = None) -> MagicMock:
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = status_code
    resp.headers = headers or {}
    resp.text = "erreur simulée"
    return resp


def _adf_payload() -> dict:
    return {
        "type": "doc",
        "version": 1,
        "content": [{"type": "paragraph", "content": [{"type": "text", "text": _SECRET_ADF_TEXT}]}],
    }


def _call_update(client: httpx.Client, item: SprintBacklogItem, state: LoopState) -> None:
    _update_existing_story(
        client=client,
        story_key=item.jira_key,
        clean_story_title=item.title,
        adf_description=_adf_payload(),
        story_epic_key="MMA-1000",
        subtasks_to_sync=[],
        item=item,
        state=state,
        allowed_subtasks={},
        actions_log=[],
        current_billing_id="",
        current_components=[],
        manifest_id="test-manifest",
    )


# ─────────────────────────────────────────────────────────────────────────────
# 0. Helper _adf_hash
# ─────────────────────────────────────────────────────────────────────────────


def test_adf_hash_is_16_hex_chars_and_deterministic():
    h1 = _adf_hash(_adf_payload())
    h2 = _adf_hash(_adf_payload())
    assert _HEX16.match(h1), f"Hash ADF doit être 16 caractères hex, obtenu: {h1}"
    assert h1 == h2, "Le hash ADF doit être déterministe pour un même payload"


# ─────────────────────────────────────────────────────────────────────────────
# 1. jira_reader — HTTP 401 → ERROR structuré
# ─────────────────────────────────────────────────────────────────────────────


def test_reader_http_401_logs_error(monkeypatch, caplog):
    monkeypatch.setenv("JIRA_URL", "https://example.atlassian.net")
    monkeypatch.setenv("JIRA_EMAIL", _SECRET_EMAIL)
    monkeypatch.setenv("JIRA_API_TOKEN", _SECRET_TOKEN)

    def _boom(*_a, **_k):
        raise httpx.HTTPStatusError("401", request=MagicMock(), response=_mock_response(401))

    monkeypatch.setattr("httpx.Client.get", _boom)

    with caplog.at_level(logging.ERROR, logger="src.pipelines.jira.jira_reader"):
        result = read_jira_issue("MMA-9001")

    assert result is None
    rec = next(r for r in caplog.records if r.message == "jira.read.http_error")
    assert rec.http_status == 401
    assert rec.jira_key == "MMA-9001"
    assert rec.fields_requested == "summary,status,description"


# ─────────────────────────────────────────────────────────────────────────────
# 2. jira_reader — HTTP 429 → WARNING avec retry_after
# ─────────────────────────────────────────────────────────────────────────────


def test_reader_429_logs_warning_with_retry_after(monkeypatch, caplog):
    monkeypatch.setenv("JIRA_URL", "https://example.atlassian.net")
    monkeypatch.setenv("JIRA_EMAIL", _SECRET_EMAIL)
    monkeypatch.setenv("JIRA_API_TOKEN", _SECRET_TOKEN)

    def _boom(*_a, **_k):
        raise httpx.HTTPStatusError(
            "429",
            request=MagicMock(),
            response=_mock_response(429, headers={"Retry-After": "42"}),
        )

    monkeypatch.setattr("httpx.Client.get", _boom)

    with caplog.at_level(logging.WARNING, logger="src.pipelines.jira.jira_reader"):
        result = read_jira_issue("MMA-9001")

    assert result is None
    rec = next(r for r in caplog.records if r.message == "jira.read.rate_limited")
    assert rec.levelno == logging.WARNING
    assert rec.http_status == 429
    assert rec.retry_after == "42"


# ─────────────────────────────────────────────────────────────────────────────
# 3. jira_item_sync — MAJ 500 → ERROR avec hash ADF, aucun corps brut
# ─────────────────────────────────────────────────────────────────────────────


def test_item_update_500_logs_error_with_adf_hash(caplog):
    client = MagicMock(spec=httpx.Client)
    client.put.return_value = _mock_response(500)
    item = _make_item()
    state = _make_state()

    with caplog.at_level(logging.ERROR, logger="src.pipelines.jira.jira_item_sync"):
        _call_update(client, item, state)

    rec = next(r for r in caplog.records if r.message == "jira.item.update_failed")
    assert rec.http_status == 500
    assert rec.story_id == "US-01"
    assert rec.jira_key == "MMA-9001"
    assert rec.action == "MISE_A_JOUR"
    assert _HEX16.match(rec.adf_payload_hash), "adf_payload_hash doit être un SHA-256 16 car."
    # Sécurité : le texte ADF confidentiel ne doit jamais apparaître dans le record
    assert _SECRET_ADF_TEXT not in str(rec.__dict__)


# ─────────────────────────────────────────────────────────────────────────────
# 4. jira_item_sync — MAJ 200 → INFO succès
# ─────────────────────────────────────────────────────────────────────────────


def test_item_update_success_logs_info(caplog):
    client = MagicMock(spec=httpx.Client)
    client.put.return_value = _mock_response(200)
    item = _make_item()
    state = _make_state()

    with caplog.at_level(logging.INFO, logger="src.pipelines.jira.jira_item_sync"):
        _call_update(client, item, state)

    rec = next(r for r in caplog.records if r.message == "jira.item.updated")
    assert rec.levelno == logging.INFO
    assert rec.http_status == 200
    assert rec.story_id == "US-01"
    assert rec.jira_key == "MMA-9001"
    assert rec.issuetype == "Story"
    assert _HEX16.match(rec.adf_payload_hash)


# ─────────────────────────────────────────────────────────────────────────────
# 4b. jira_item_sync — MAJ 429 → WARNING avec retry_after
# ─────────────────────────────────────────────────────────────────────────────


def test_item_update_429_logs_warning_with_retry_after(caplog):
    client = MagicMock(spec=httpx.Client)
    client.put.return_value = _mock_response(429, headers={"Retry-After": "17"})
    item = _make_item()
    state = _make_state()

    with caplog.at_level(logging.WARNING, logger="src.pipelines.jira.jira_item_sync"):
        _call_update(client, item, state)

    rec = next(r for r in caplog.records if r.message == "jira.item.rate_limited")
    assert rec.levelno == logging.WARNING
    assert rec.http_status == 429
    assert rec.retry_after == "17"


# ─────────────────────────────────────────────────────────────────────────────
# 5. jira_report — échec écriture rapport → ERROR
# ─────────────────────────────────────────────────────────────────────────────


def test_report_write_failure_logs_error(tmp_path, monkeypatch, caplog):
    project_path = tmp_path / "Projects" / "TestProjet"
    (project_path / "memory").mkdir(parents=True)
    actions_log = [
        {"type": "Story", "id": "MMA-9001", "title": "T", "action": "MAJ", "details": "ok"}
    ]

    original_write_text = Path.write_text

    def _fail_report(self: Path, *a, **k):
        if self.name == "jira_sync_report.md":
            raise OSError("disque plein simulé")
        return original_write_text(self, *a, **k)

    monkeypatch.setattr(Path, "write_text", _fail_report)

    with caplog.at_level(logging.ERROR, logger="src.pipelines.jira.jira_report"):
        _write_markdown_report(project_path, "TestProjet", actions_log)

    rec = next(r for r in caplog.records if r.message == "jira.report.write_failed")
    assert rec.stories_synced == 1
    assert rec.report_path.endswith("jira_sync_report.md")


# ─────────────────────────────────────────────────────────────────────────────
# 6. sync_engine — échec écriture manifeste SHA-256 → ERROR (Fail-Closed)
# ─────────────────────────────────────────────────────────────────────────────


def test_preview_manifest_write_failure_logs_error(tmp_path, monkeypatch, caplog):
    project_path = tmp_path / "Projects" / "TestProjet"
    (project_path / "backlog" / "stories").mkdir(parents=True)
    state = _make_state()
    item = _make_item()

    def _fail_manifest(self: Path, *a, **k):
        raise OSError("écriture manifeste refusée")

    monkeypatch.setattr(Path, "write_text", _fail_manifest)

    with caplog.at_level(logging.ERROR, logger="src.pipelines.jira.sync_engine"):
        preview = build_sync_preview(project_path, state, [item], [], ["MMA-9001"])

    # Le manifeste retourné reste cohérent malgré l'échec d'écriture disque
    assert preview["manifest_id"]
    rec = next(r for r in caplog.records if r.message == "jira.sync.preview.manifest_write_failed")
    assert rec.eligible_count == 1
    assert rec.target_keys == ["MMA-9001"]
    assert rec.dry_run is True


# ─────────────────────────────────────────────────────────────────────────────
# 7. Sécurité globale — aucun secret ne fuit dans les logs
# ─────────────────────────────────────────────────────────────────────────────


def test_no_secret_leaked_in_logs(caplog):
    client = MagicMock(spec=httpx.Client)
    client.put.return_value = _mock_response(500)
    item = _make_item()
    state = _make_state()

    with caplog.at_level(logging.DEBUG):
        _call_update(client, item, state)

    for rec in caplog.records:
        blob = str(rec.__dict__)
        assert _SECRET_TOKEN not in blob, "Le token Jira ne doit jamais être logué"
        assert _SECRET_EMAIL not in blob, "L'email Jira ne doit jamais être logué"
        assert _SECRET_ADF_TEXT not in blob, "Le corps ADF brut ne doit jamais être logué"
