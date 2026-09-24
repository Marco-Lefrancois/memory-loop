"""
Tests du socle protocolaire MCP 2026-07-28 - MLOOP-210-BE (ADR-0387).

Scenarios 1 a 3 du recit Gherkin : negociation et routage nominal d'un client
2026-07-28 sur transport HTTP/SSE, rejet dur d'une version inconnue du
registre (-32600), version obsolete admise avec alerte structuree et repli
sans rejet.

(Scenarios 4 a 7 : `tests/test_mcp_protocol_routage.py`.)
"""

import json
from unittest.mock import patch

import httpx
import pytest

import src.bridges.mcp_loop_mem as mcp_loop_mem
from src.bridges._mcp_protocol import (
    FALLBACK_POLICY,
    PROTOCOL_VERSION_LEGACY,
    PROTOCOL_VERSION_TARGET,
    SUPPORTED_PROTOCOL_VERSIONS,
    apply_fallback_policy,
    get_fallback_journal,
    get_obsolete_alerts,
    negotiate_version,
    reset_protocol_observability,
    response_headers,
    route_from_headers,
)
from src.bridges.mcp_event_bus import MCPEventBus
from src.bridges.mcp_loop_mem import handle_initialize, process_message
from src.bridges.mcp_sse_server import _create_app

# En-tetes d'un appel d'outil correctement renseigne (210-Q2).
MODERN_HEADERS = {
    "MCP-Protocol-Version": PROTOCOL_VERSION_TARGET,
    "MCP-Method": "tools/call",
    "MCP-Tool-Name": "loop_mem_search",
}

INIT_HEADERS = {
    "MCP-Protocol-Version": PROTOCOL_VERSION_TARGET,
    "MCP-Method": "initialize",
}


async def _post_raw(content: str, headers: dict | None = None) -> httpx.Response:
    """POST /messages : l'envoi brut permet de controler le corps transmis."""
    app = _create_app(MCPEventBus(max_clients=8))
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.post("/messages", content=content, headers=headers or {})


async def _post(payload: dict, headers: dict | None = None) -> httpx.Response:
    return await _post_raw(json.dumps(payload), headers)


@pytest.fixture(autouse=True)
def _fresh_observability():
    """Isole chaque scenario : compteurs et journaux a zero."""
    reset_protocol_observability()
    yield
    reset_protocol_observability()


# ──────────────────────────────────────────────────────────────────────────
# 1. CHEMIN NOMINAL - client 2026-07-28 sur transport HTTP/SSE
# ──────────────────────────────────────────────────────────────────────────


class TestNominaleHTTP:
    """Scenario Gherkin 1 : negociation et routage nominal."""

    @pytest.mark.asyncio
    async def test_reponse_d_initialisation_publie_revision_et_registre(self):
        resp = await _post(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {"protocolVersion": PROTOCOL_VERSION_TARGET},
            },
            headers=INIT_HEADERS,
        )
        assert resp.status_code == 200
        assert resp.headers["MCP-Protocol-Version"] == PROTOCOL_VERSION_TARGET
        result = resp.json()["result"]
        assert result["protocolVersion"] == PROTOCOL_VERSION_TARGET
        assert result["supportedVersions"] == list(SUPPORTED_PROTOCOL_VERSIONS)

    @pytest.mark.asyncio
    async def test_appel_outil_routage_complet_sans_relecture_du_corps(self):
        fake_result = {"jsonrpc": "2.0", "id": 7, "result": {"content": []}}
        with patch(
            "src.bridges.mcp_loop_mem.handle_tools_call", return_value=(fake_result, None)
        ) as mocked:
            resp = await _post(
                {
                    "jsonrpc": "2.0",
                    "id": 7,
                    "method": "tools/call",
                    "params": {"name": "loop_mem_search", "arguments": {"query": "socle"}},
                },
                headers=MODERN_HEADERS,
            )
        assert resp.status_code == 200
        # La passerelle echoie la route resolue depuis les seuls entetes.
        assert resp.headers["MCP-Protocol-Version"] == PROTOCOL_VERSION_TARGET
        assert resp.headers["MCP-Method"] == "tools/call"
        assert resp.headers["MCP-Tool-Name"] == "loop_mem_search"
        mocked.assert_called_once()
        assert resp.json()["result"]["content"] == []

    def test_le_routage_ne_consulte_que_les_entetes(self):
        route = route_from_headers(MODERN_HEADERS)
        assert route.accepted is True
        assert route.header_present is True
        assert route.method == "tools/call"
        assert route.tool_name == "loop_mem_search"
        assert route.nonconformities == ()

    def test_entetes_de_reponse_echoient_l_appel_sans_outil_hors_appel(self):
        assert response_headers(PROTOCOL_VERSION_TARGET, "tools/call", "loop_mem_search") == {
            "MCP-Protocol-Version": PROTOCOL_VERSION_TARGET,
            "MCP-Method": "tools/call",
            "MCP-Tool-Name": "loop_mem_search",
        }
        reflected = response_headers(PROTOCOL_VERSION_TARGET, "tools/list", "loop_mem_search")
        assert reflected["MCP-Protocol-Version"] == PROTOCOL_VERSION_TARGET
        assert reflected["MCP-Method"] == "tools/list"
        assert "MCP-Tool-Name" not in reflected


# ──────────────────────────────────────────────────────────────────────────
# 2. EXCEPTIONS & REJETS METIER - version inconnue du registre
# ──────────────────────────────────────────────────────────────────────────


class TestRejetDurVersionInconnue:
    """Scenario Gherkin 2 : refus -32600 reserve aux versions hors registre."""

    def test_negotiation_confronte_le_registre_unique(self):
        decision = negotiate_version("1999-01-01")
        assert decision.accepted is False
        assert decision.status == "unknown"
        assert decision.negotiated is None

    def test_reponse_d_initialisation_refusee_sans_mutation_de_session(self):
        mcp_loop_mem._SESSION_PROTOCOL_VERSION = PROTOCOL_VERSION_TARGET
        res = handle_initialize(9, {"protocolVersion": "1999-01-01"})
        assert res["error"]["code"] == -32600
        assert res["error"]["data"]["requested"] == "1999-01-01"
        assert res["error"]["data"]["supported"] == list(SUPPORTED_PROTOCOL_VERSIONS)
        # Aucune mutation : la session conserve la version deja retenue.
        assert mcp_loop_mem._SESSION_PROTOCOL_VERSION == PROTOCOL_VERSION_TARGET

    def test_process_message_stdio_refuse_la_version_inconnue(self):
        raw = process_message(
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "initialize",
                    "params": {"protocolVersion": "1999-01-01"},
                }
            )
        )
        assert raw is not None, "Le pont n'a emis aucune reponse JSON-RPC"
        payload = json.loads(raw)
        assert payload["error"]["code"] == -32600
        assert "result" not in payload

    @pytest.mark.asyncio
    async def test_http_rejette_avant_toute_lecture_du_corps(self):
        # Corps vide : le refus doit preceder toute lecture ou analyse JSON.
        resp = await _post_raw(
            "",
            headers={
                "MCP-Protocol-Version": "1999-01-01",
                "MCP-Method": "tools/call",
                "MCP-Tool-Name": "loop_mem_search",
            },
        )
        assert resp.status_code == 400
        payload = resp.json()
        assert payload["error"]["code"] == -32600
        assert payload["id"] is None


# ──────────────────────────────────────────────────────────────────────────
# 3. VERSION OBSOLETE - alerte + repli, jamais de rejet
# ──────────────────────────────────────────────────────────────────────────


class TestVersionObsoleteAvecRepli:
    """Scenario Gherkin 3 : version connue mais non cible, admise sans refus."""

    def test_le_registre_admet_toutes_les_revisions_publiees(self):
        assert negotiate_version(PROTOCOL_VERSION_TARGET).status == "target"
        for version in SUPPORTED_PROTOCOL_VERSIONS:
            decision = negotiate_version(version)
            assert decision.accepted is True
            assert decision.negotiated == version

    @pytest.mark.asyncio
    async def test_version_obsolete_aboutit_et_alimente_l_alerte(self):
        resp = await _post(
            {"jsonrpc": "2.0", "id": 5, "method": "tools/list", "params": {}},
            headers={
                "MCP-Protocol-Version": PROTOCOL_VERSION_LEGACY,
                "MCP-Method": "tools/list",
            },
        )
        assert resp.status_code == 200
        assert resp.headers["MCP-Protocol-Version"] == PROTOCOL_VERSION_LEGACY

        alerts = get_obsolete_alerts()
        assert [alert["event"] for alert in alerts] == ["protocol_version_obsolete"]
        assert alerts[0]["declaredVersion"] == PROTOCOL_VERSION_LEGACY
        assert alerts[0]["targetVersion"] == PROTOCOL_VERSION_TARGET
        assert alerts[0]["negotiatedVersion"] == PROTOCOL_VERSION_LEGACY

        entries = get_fallback_journal()
        assert entries, "La politique de repli doit etre journalisee"
        assert entries[0]["reasons"] == ["obsolete_version"]
        assert entries[0]["transport"] == "http_sse"
        assert entries[0]["policy_id"] == FALLBACK_POLICY["policy_id"]

    def test_le_repli_ne_rejette_jamais(self):
        assert FALLBACK_POLICY["never_rejects"] is True
        assert FALLBACK_POLICY["scope"] == "per_request"
        assert FALLBACK_POLICY["mode_when_degraded"] == "standard_sync"
        # Une version hors registre n'active aucun repli : le refus prime seul.
        outcome = apply_fallback_policy(
            negotiate_version("1999-01-01"), transport="stdio", method="initialize"
        )
        assert outcome.armed is False
        assert get_fallback_journal() == []
