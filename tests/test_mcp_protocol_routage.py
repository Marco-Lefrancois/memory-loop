"""
Tests du socle protocolaire MCP 2026-07-28 - MLOOP-210-BE (ADR-0387).

Scenarios 4 a 7 du recit Gherkin : repli gracieux du client sans entete
moderne, exposition honnete de `_meta.routing` en transport stdio, frontiere
active de l'inventaire des ponts, et observabilite (alertes / repli /
adoption des entetes).

(Scenarios 1 a 3 : `tests/test_mcp_protocol_socle.py`.)
"""

import ast
import json
from pathlib import Path
from unittest.mock import patch

import httpx
import pytest

from src.bridges._mcp_protocol import (
    COVERED_BRIDGES,
    FALLBACK_POLICY,
    PROTOCOL_VERSION_LEGACY,
    PROTOCOL_VERSION_TARGET,
    apply_fallback_policy,
    build_routing_meta,
    get_adoption_metrics,
    get_fallback_journal,
    get_obsolete_alerts,
    negotiate_version,
    reset_protocol_observability,
    route_from_headers,
)
import src.bridges.mcp_loop_mem as mcp_loop_mem
from src.bridges.mcp_event_bus import MCPEventBus
from src.bridges.mcp_loop_mem import process_message
from src.bridges.mcp_sse_server import _create_app

BRIDGES_DIR = Path("src") / "bridges"


def _dispatch(payload: dict) -> str:
    """Emet une requete cote serveur stdio et retourne la trame de reponse."""
    raw = process_message(json.dumps(payload))
    assert raw is not None, "Le pont n'a emis aucune reponse JSON-RPC"
    return raw


async def _post(payload: dict, headers: dict | None = None) -> httpx.Response:
    app = _create_app(MCPEventBus(max_clients=8))
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.post("/messages", content=json.dumps(payload), headers=headers or {})


@pytest.fixture(autouse=True)
def _fresh_observability():
    """Isole chaque scenario : compteurs et journaux a zero."""
    reset_protocol_observability()
    yield
    reset_protocol_observability()


# ──────────────────────────────────────────────────────────────────────────
# 4. RESILIENCE - client sans entete moderne
# ──────────────────────────────────────────────────────────────────────────


class TestRepliClientHeritage:
    """Scenario Gherkin 4 : repli gracieux, jamais de rejet."""

    @pytest.mark.asyncio
    async def test_requete_sans_entete_de_version_aboutit_sans_rejet(self):
        resp = await _post({"jsonrpc": "2.0", "id": 4, "method": "tools/list", "params": {}})
        assert resp.status_code == 200
        assert resp.headers["MCP-Protocol-Version"] == PROTOCOL_VERSION_LEGACY
        assert resp.json()["result"]

        entries = get_fallback_journal()
        assert entries, "La decision de repli doit etre journalisee"
        assert entries[0]["reasons"] == ["legacy_client"]
        assert entries[0]["nonconformities"] == []
        assert entries[0]["policy_id"] == FALLBACK_POLICY["policy_id"]

        metrics = get_adoption_metrics()
        assert metrics["legacy"] == 1
        assert metrics["modern"] == 0
        assert get_obsolete_alerts() == []

    def test_l_absence_d_entete_n_est_jamais_un_rejet(self):
        route = route_from_headers({})
        assert route.accepted is True
        assert route.header_present is False
        assert route.nonconformities == ()
        assert negotiate_version(None).status == "absent"
        assert negotiate_version("").status == "absent"


# ──────────────────────────────────────────────────────────────────────────
# 5. TRANSPORT STDIO - exposition honnete via `_meta.routing`
# ──────────────────────────────────────────────────────────────────────────


class TestRoutageStdioHonnete:
    """Scenario Gherkin 5 : metadonnees de routage, zero entete HTTP fabrique."""

    def test_meta_routing_porte_version_et_methode(self):
        # Poignee de main stdio : le client declare sa version dans les params.
        init = json.loads(
            _dispatch(
                {
                    "jsonrpc": "2.0",
                    "id": 0,
                    "method": "initialize",
                    "params": {"protocolVersion": PROTOCOL_VERSION_LEGACY},
                }
            )
        )
        assert init["result"]["protocolVersion"] == PROTOCOL_VERSION_LEGACY

        payload = json.loads(_dispatch({"jsonrpc": "2.0", "id": 1, "method": "tools/list"}))
        assert set(payload["result"]["_meta"]) == {"routing"}
        routing = payload["result"]["_meta"]["routing"]
        assert routing["method"] == "tools/list"
        assert routing["protocolVersion"] == PROTOCOL_VERSION_LEGACY
        assert "toolName" not in routing

        dumped = json.dumps(payload)
        assert "MCP-Protocol-Version" not in dumped
        assert "MCP-Method" not in dumped
        # Le compteur d'adoption est reserve aux transports HTTP/SSE.
        assert get_adoption_metrics()["total"] == 0

    def test_meta_routing_porte_le_nom_doutil_sur_appel(self):
        # Session stdio deja negociee sur la revision publiee la plus ancienne.
        mcp_loop_mem._SESSION_PROTOCOL_VERSION = PROTOCOL_VERSION_LEGACY
        fake_result = {"jsonrpc": "2.0", "id": 12, "result": {"content": []}}
        with patch("src.bridges.mcp_loop_mem.handle_tools_call", return_value=(fake_result, None)):
            payload = json.loads(
                _dispatch(
                    {
                        "jsonrpc": "2.0",
                        "id": 12,
                        "method": "tools/call",
                        "params": {"name": "loop_mem_search", "arguments": {"query": "socle"}},
                    }
                )
            )
        assert payload["result"]["_meta"]["routing"] == {
            "protocolVersion": PROTOCOL_VERSION_LEGACY,
            "method": "tools/call",
            "toolName": "loop_mem_search",
        }

    def test_le_nom_doutil_n_accompagne_que_les_appels_doutils(self):
        tool_meta = build_routing_meta(
            protocol_version=PROTOCOL_VERSION_TARGET,
            method="tools/call",
            tool_name="loop_mem_search",
        )["routing"]
        assert tool_meta["toolName"] == "loop_mem_search"

        list_meta = build_routing_meta(
            protocol_version=PROTOCOL_VERSION_TARGET,
            method="tools/list",
            tool_name="loop_mem_search",
        )["routing"]
        assert "toolName" not in list_meta


# ──────────────────────────────────────────────────────────────────────────
# 6. FRONTIERE ACTIVE - inventaire des ponts non cloture
# ──────────────────────────────────────────────────────────────────────────


class TestFrontiereActivePonts:
    """Scenario Gherkin 6 : aucun pont supplimentaire n'est presume couvert."""

    def test_le_socle_couvre_strictement_les_quatre_ponts_de_l_adr_005(self):
        assert COVERED_BRIDGES == (
            "mcp_loop_mem",
            "mcp_sse_server",
            "mcp_proxy_router",
            "mcp_resilience_guard",
        )

    def test_aucun_pont_hors_inventaire_ne_consomme_le_socle(self):
        importeurs: set[str] = set()
        for path in sorted(BRIDGES_DIR.glob("**/*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            modules = {node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)}
            modules |= {
                alias.name
                for node in ast.walk(tree)
                if isinstance(node, ast.Import)
                for alias in node.names
            }
            if "src.bridges._mcp_protocol" in modules:
                importeurs.add(path.stem)
        assert importeurs == set(COVERED_BRIDGES)

    def test_l_inventaire_des_transports_reste_ouvert(self):
        # Admission of Limits (récit Out-of-Scope / OQ-210-01) : l'inventaire
        # n'est pas cloture, aucun autre pont n'est presume couvert, et couvrir
        # un pont exige une decision d'architecture explicite (ADR-005 / 210-Q2).
        hors_inventaire = sorted(
            {path.stem for path in BRIDGES_DIR.glob("mcp_*.py")} - set(COVERED_BRIDGES)
        )
        assert hors_inventaire, "L'inventaire des ponts HTTP devrait rester ouvert"
        assert "mcp_graphify" in hors_inventaire
        assert "mcp_herdr" in hors_inventaire


# ──────────────────────────────────────────────────────────────────────────
# 7. OBSERVABILITE - alertes, journal de repli, metrique d'adoption
# ──────────────────────────────────────────────────────────────────────────


class TestObservabiliteProtocolaire:
    """Scenario Gherkin 7 : observabilite de l'obsolescence et de l'adoption."""

    @pytest.mark.asyncio
    async def test_jeu_de_requetes_melees(self):
        # 1. client moderne : en-tete porte la revision cible.
        await _post(
            {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}},
            headers={"MCP-Protocol-Version": PROTOCOL_VERSION_TARGET, "MCP-Method": "tools/list"},
        )
        # 2. client obsolète : en-tete porte une revision connue non cible.
        await _post(
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
            headers={"MCP-Protocol-Version": PROTOCOL_VERSION_LEGACY, "MCP-Method": "tools/list"},
        )
        # 3. client herite : aucun en-tete de version.
        await _post({"jsonrpc": "2.0", "id": 3, "method": "tools/list", "params": {}})

        # La metrique mesure l'adoption de l'en-tete : deux requetes en portent
        # un (dont la revision obsolete), une seule est heritee.
        adoption = get_adoption_metrics()
        assert adoption["modern"] == 2
        assert adoption["legacy"] == 1
        assert adoption["adoption_ratio"] == round(2 / 3, 4)
        assert adoption["header"] == "MCP-Protocol-Version"
        assert adoption["target_version"] == PROTOCOL_VERSION_TARGET

        alerts = get_obsolete_alerts()
        assert len(alerts) == 1
        assert alerts[0]["event"] == "protocol_version_obsolete"
        assert alerts[0]["declaredVersion"] == PROTOCOL_VERSION_LEGACY

        journal = get_fallback_journal()
        assert len(journal) == 2
        assert any(entry["reasons"] == ["obsolete_version"] for entry in journal)
        assert any(entry["reasons"] == ["legacy_client"] for entry in journal)

    def test_journal_de_repli_tranche_par_transport(self):
        apply_fallback_policy(
            negotiate_version(PROTOCOL_VERSION_LEGACY),
            transport="stdio",
            method="tools/call",
            tool_name="loop_mem_search",
            declared_in_message=True,
        )
        entries = get_fallback_journal()
        assert len(entries) == 1
        assert entries[0]["transport"] == "stdio"
        assert entries[0]["method"] == "tools/call"
        assert entries[0]["toolName"] == "loop_mem_search"
        assert entries[0]["reasons"] == ["obsolete_version"]
        assert entries[0]["policy_id"] == FALLBACK_POLICY["policy_id"]

    def test_les_compteurs_ne_sont_alimentes_que_par_les_transports_http(self):
        _dispatch({"jsonrpc": "2.0", "id": 9, "method": "tools/list", "params": {}})
        assert get_adoption_metrics()["total"] == 0
        assert get_obsolete_alerts() == []
