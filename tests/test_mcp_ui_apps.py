"""
Tests d'integration MLOOP-212-FE : Extension MCP Apps ui:// (SEP-1865).

Couvre les 7 scenarios Gherkin du recit (affichage nominal, sans-support,
adresse hors registre, banniere 320 px, isolement reseau, mise a jour en place,
etats/Tracabilite) + la negotiation de capacite (absente / conforme / mimeTypes
incorrect), l'annonce serveur `capabilities.extensions` et la notification SSE
de changement de projet.
"""

import asyncio
import logging

import pytest
from unittest.mock import patch

from src.bridges._mcp_ui_shell import (
    UI_MIN_WIDTH_PX,
    _UI_CSS,
    _UI_JS,
    resolve_archify_artifact,
    strip_external_assets,
)
from src.bridges.mcp_event_bus import MCPEventBus
from src.bridges.mcp_loop_mem import handle_initialize, handle_server_discover
from src.bridges.mcp_resources import handle_resources_list, handle_resources_read
from src.bridges.mcp_tools import handle_tools_call, handle_tools_list
from src.bridges.mcp_ui import (
    UI_APP_MIME_TYPE,
    UI_EXTENSION_ID,
    UI_URI_ARCHIFY,
    UI_URI_DRAWDB,
    client_supports_ui,
    list_ui_resources,
    local_url_for,
    note_client_capabilities,
    notify_ui_project_changed,
    read_ui_resource,
    reset_ui_state,
    ui_result,
)


def _supported_caps() -> dict:
    return {"extensions": {UI_EXTENSION_ID: {"mimeTypes": [UI_APP_MIME_TYPE]}}}


def _read(uri: str, project: str = "mLoop") -> dict:
    """Lit une ressource ui:// en exigant un succes (helper de test)."""
    out = read_ui_resource(uri, project)
    assert out is not None and out.get("ok"), out
    return out["content"]


class TestAffichageNominal:
    """Scenario 1 : Affichage nominal des deux ressources ui:// dans l'IDE."""

    def setup_method(self):
        reset_ui_state()
        note_client_capabilities(_supported_caps())

    def test_initialize_annonce_capabilities_extensions(self):
        res = handle_initialize(1, {"capabilities": _supported_caps()})
        caps = res["result"]["capabilities"]
        assert UI_EXTENSION_ID in caps["extensions"]
        assert caps["extensions"][UI_EXTENSION_ID] == {"mimeTypes": [UI_APP_MIME_TYPE]}

    def test_server_discover_en_parity(self):
        res = handle_server_discover(2)
        assert UI_EXTENSION_ID in res["result"]["capabilities"]["extensions"]

    def test_resources_list_declare_les_deux_ui(self):
        resources = handle_resources_list(3, "mLoop")["result"]["resources"]
        by_uri = {r["uri"]: r for r in resources if r["uri"].startswith("ui://")}
        assert set(by_uri) == {UI_URI_ARCHIFY, UI_URI_DRAWDB}
        for entry in by_uri.values():
            assert entry["mimeType"] == UI_APP_MIME_TYPE
            assert entry["_meta"]["ui"]["csp"] == {"connectDomains": [], "resourceDomains": []}

    def test_resources_read_livre_html5_autocontenu(self):
        res = handle_resources_read(4, {"uri": f"{UI_URI_ARCHIFY}?project=mLoop"}, "mLoop")
        content = res["result"]["contents"][0]
        assert content["mimeType"] == UI_APP_MIME_TYPE
        html = content["text"]
        assert html.lstrip().lower().startswith("<!doctype html") or "<html" in html[:300].lower()
        assert "window.__MLOOP_UI__" in html
        assert '"project": "mLoop"' in html
        assert "mloop-project-badge" in html

    def test_resources_read_schema_drawdb(self):
        res = handle_resources_read(5, {"uri": UI_URI_DRAWDB}, "mLoop")
        html = res["result"]["contents"][0]["text"]
        assert "mloop-fallback-banner" in html
        assert '"zoomTarget": "#schema-container"' in html

    def test_tools_list_attache_meta_ui(self):
        tools = handle_tools_list(6, {})["result"]["tools"]
        by_name = {t["name"]: t for t in tools}
        assert by_name["show_architecture"]["_meta"]["ui"]["resourceUri"] == UI_URI_ARCHIFY
        assert by_name["show_database_schema"]["_meta"]["ui"]["resourceUri"] == UI_URI_DRAWDB
        assert "phase" not in by_name["show_architecture"]

    def test_tools_call_avec_capacite_attache_resource_uri(self):
        res, project = handle_tools_call(
            7, {"name": "show_architecture", "arguments": {"project": "mLoop"}}, None
        )
        meta_uri = res["result"]["_meta"]["ui"]["resourceUri"]
        assert meta_uri.startswith(f"{UI_URI_ARCHIFY}?project=mLoop")
        assert "isError" not in res["result"]
        assert project is None  # l'appel n'entraine pas la session


class TestClientSansSupport:
    """Scenario 2 : Appel d'outil sur client hote sans support de l'extension ui://."""

    def setup_method(self):
        reset_ui_state()

    def test_sans_capacite_repli_local_sans_meta(self):
        res, _ = handle_tools_call(
            1, {"name": "show_architecture", "arguments": {"project": "mLoop"}}, "mLoop"
        )
        assert "isError" not in res["result"]
        text = res["result"]["content"][0]["text"]
        assert "localhost" in text
        assert "_meta" not in res["result"]

    def test_capacite_partielle_sans_mime_types_rejetee(self):
        note_client_capabilities({"extensions": {UI_EXTENSION_ID: {}}})
        assert client_supports_ui() is False

    def test_capacite_avec_mime_type_incorrect_rejetee(self):
        note_client_capabilities({"extensions": {UI_EXTENSION_ID: {"mimeTypes": ["text/html"]}}})
        assert client_supports_ui() is False

    def test_capacite_hors_extensions_rejetee(self):
        note_client_capabilities({"sampling": {}, "roots": {"listChanged": True}})
        assert client_supports_ui() is False

    def test_capacite_non_dictionnaire_rejetee(self):
        note_client_capabilities("oui")
        note_client_capabilities(None)
        assert client_supports_ui() is False

    def test_ressources_toujours_listees_sans_capacite(self):
        resources = handle_resources_list(8, "mLoop")["result"]["resources"]
        assert any(r["uri"] == UI_URI_DRAWDB for r in resources)


class TestAdresseHorsRegistre:
    """Scenario 3 : Adresse de ressource hors registre des adresses officielles."""

    def test_read_ui_hors_registre_refusee_non_conforme(self):
        res = handle_resources_read(1, {"uri": "ui://evil/payload"}, "mLoop")
        assert res["result"]["isError"] is True
        assert "hors registre" in res["result"]["content"][0]["text"]

    def test_read_ui_sous_ressource_inconnue_refusee(self):
        out = read_ui_resource("ui://drawdb/unknown-subresource", "mLoop")
        assert out is not None and out["ok"] is False
        assert "hors registre" in out["message"]

    def test_liste_ne_jamais_exposer_adresse_hors_registre(self):
        uris = [r["uri"] for r in list_ui_resources()]
        assert uris == [UI_URI_ARCHIFY, UI_URI_DRAWDB]

    def test_ressource_non_ui_ne_prend_pas_le_relais(self):
        assert read_ui_resource("skill://triage", "mLoop") is None


class TestBanniereRepliSeuil:
    """Scenario 4 : Repli par banniere lorsque la largeur passe sous le seuil."""

    def test_seuil_partage_ui_min_width_px(self):
        assert UI_MIN_WIDTH_PX == 320

    def test_html_livre_banniere_cachee_par_defaut(self):
        html = _read(UI_URI_ARCHIFY)["text"]
        banner_line = next(
            line for line in html.splitlines() if "mloop-fallback-banner" in line and "<div" in line
        )
        assert "hidden" in banner_line

    def test_shell_compare_la_largeur_au_seuil(self):
        assert '"minWidthPx": 320' in _read(UI_URI_DRAWDB)["text"]
        assert "width < MIN_W" in _UI_JS

    def test_etats_lien_default_hover_focus_active(self):
        for state in ("a:hover", "a:focus-visible", "a:active"):
            assert state in _UI_CSS

    def test_banniere_non_bloquante_et_journalisee(self):
        assert 'role="status"' in _read(UI_URI_DRAWDB)["text"]
        assert "bannière de repli activée" in _UI_JS
        assert "console.info" in _UI_JS


class TestIsolementReseau:
    """Scenario 5 : Isolement reseau preserve a l'interieur du cadre."""

    def test_csp_restrictive_connect_src_none(self):
        html = _read(UI_URI_DRAWDB)["text"]
        assert "default-src 'none'" in html
        assert "connect-src 'none'" in html
        assert "object-src 'none'" in html

    def test_zero_actif_externe_servi(self):
        html = _read(f"{UI_URI_ARCHIFY}?project=mLoop")["text"]
        lowered = html.lower()
        assert '<script src="http' not in lowered and "<script src='http" not in lowered
        assert "fonts.googleapis.com" not in lowered
        assert "@import url(http" not in lowered

    def test_strip_external_assets_retrait_des_fontes_cdn(self):
        raw = '<link href="https://fonts.googleapis.com/css2" rel="stylesheet"><p>ok</p>'
        cleaned, count = strip_external_assets(raw)
        assert count == 1 and "fonts.googleapis.com" not in cleaned

    def test_shell_rejette_source_non_parent(self):
        assert "event.source !== window.parent" in _UI_JS

    def test_shell_sans_storage_ni_cookie(self):
        assert "localStorage" not in _UI_JS
        assert "document.cookie" not in _UI_JS

    def test_artefact_archify_resolu_sans_cdn(self):
        path = resolve_archify_artifact("mLoop")
        assert path is not None
        html, count = strip_external_assets(path.read_text(encoding="utf-8", errors="ignore"))
        assert count >= 1, "les 3 liens Google Fonts du showcase doivent etre stripes"
        assert "fonts.googleapis.com" not in html


class TestMiseAJourEnPlace:
    """Scenario 6 : Mise a jour en place lors d'un changement de projet."""

    def test_shell_recoit_project_changed(self):
        assert 'data.type === "project_changed"' in _UI_JS

    def test_zero_rechargement(self):
        assert "location.reload" not in _UI_JS
        assert "window.location" not in _UI_JS

    def test_mise_a_jour_badge_et_titre_en_place(self):
        assert "badge.textContent = project" in _UI_JS
        assert "document.title" in _UI_JS

    def test_actualisation_tables_conserve_zoom(self):
        assert "window.renderSchema(payload.tables)" in _UI_JS
        assert "zoom/déplacement conservés" in _UI_JS

    @pytest.mark.asyncio
    async def test_notification_sse_changement_de_projet(self):
        bus = MCPEventBus(max_clients=8, heartbeat_interval=15.0)
        queue = await bus.subscribe("client-ui")
        with patch("src.bridges.mcp_event_bus.get_event_bus", return_value=bus):
            notify_ui_project_changed("mLoop")
            await asyncio.sleep(0.05)
        frames = []
        while not queue.empty():
            frames.append(queue.get_nowait())
        assert len(frames) == 2
        assert all("notifications/resources/updated" in f for f in frames)
        assert any(UI_URI_ARCHIFY in f for f in frames)
        assert any(UI_URI_DRAWDB in f for f in frames)

    @pytest.mark.asyncio
    async def test_changement_projet_sur_run_mcp_loop_mem(self):
        # loop_mem_set_project declenche la notification (hors boucle SSE : garde silencieuse OK).
        with patch("src.bridges.mcp_event_bus.get_event_bus", return_value=MCPEventBus()):
            res, project = handle_tools_call(
                1, {"name": "loop_mem_set_project", "arguments": {"project": "mLoop"}}, None
            )
            assert project == "mLoop"
            assert "isError" not in res["result"]
            await asyncio.sleep(0.05)


class TestEtatsEtTracabilite:
    """Scenario 7 : Indicateurs de progression, etats de surface et Tracabilite du repli."""

    def test_handshake_ui_initialise(self):
        assert '"ui/initialize"' in _UI_JS
        assert '"ui/notifications/initialized"' in _UI_JS

    def test_notification_size_changed(self):
        assert '"ui/notifications/size-changed"' in _UI_JS

    def test_lien_declaratif_vers_adresse_locale(self):
        assert "mloop-open-local" in _read(f"{UI_URI_ARCHIFY}?project=mLoop")["text"]
        assert "ui/open-link" in _UI_JS

    def test_adresses_locale_de_repli_tracables(self):
        assert local_url_for(UI_URI_DRAWDB, "mLoop") == "http://localhost:8081/"
        archify = local_url_for(UI_URI_ARCHIFY, "mLoop")
        assert archify.startswith("http://localhost:8080/api/archify/html")
        assert "project=mLoop" in archify

    def test_degradation_repli_journalisee(self):
        reset_ui_state()
        with patch.object(logging.getLogger("src.bridges.mcp_ui"), "debug") as mock_debug:
            text, meta = ui_result("show_architecture", "mLoop")
        assert meta is None
        assert any("ui_fallback_local" in str(call) for call in mock_debug.call_args_list)

    def test_ui_result_sans_capacite_ne_jamais_erreur(self):
        reset_ui_state()
        text, meta = ui_result("show_database_schema", "mLoop")
        assert meta is None
        assert "http://localhost:8081/" in text

    def test_ordre_etat_surface_badge_visible(self):
        html = _read(f"{UI_URI_DRAWDB}?project=mLoop")["text"]
        chip = html.index('<div id="mloop-ui-chip"')
        banner = html.index('<div id="mloop-fallback-banner"')
        assert chip < banner
