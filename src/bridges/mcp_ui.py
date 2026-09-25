"""
src/bridges/mcp_ui.py — Pont MCP Apps `ui://` (MLOOP-212-FE).

Registre partagé de l'extension officielle ``io.modelcontextprotocol/ui``
(SEP-1865, spec 2026-01-26) : capacité client stricte (``mimeTypes`` REQUIRED),
annonces serveur, lecture des 2 ressources mLoop (Archify Cockpit, DrawDB ERD),
liaison outil $\rightarrow$ ressource via ``_meta.ui.resourceUri`` et résultat
d'outil conforme (texte toujours significatif ; repli local journalisé quand
l'extension n'est pas négociée — jamais ``isError``).

Importé par les ponts Tier A : ``mcp_loop_mem`` (négociation/capacités),
``mcp_tools`` (outils ``show_*``), ``mcp_resources`` (list/read ``ui://``).
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Optional
from urllib.parse import parse_qs, quote, urlsplit

from src.bridges._mcp_ui_shell import UI_MIN_WIDTH_PX, build_ui_page, resolve_archify_artifact

logger = logging.getLogger(__name__)

# ── Registre partagé (SSOT unique, plan §3) ──────────────────────────────────
UI_EXTENSION_ID = "io.modelcontextprotocol/ui"
UI_APP_MIME_TYPE = "text/html;profile=mcp-app"
UI_URI_ARCHIFY = "ui://archify/cockpit"
UI_URI_DRAWDB = "ui://drawdb/schema"
UI_KNOWN_URIS = (UI_URI_ARCHIFY, UI_URI_DRAWDB)

_UI_REGISTRY: dict[str, dict[str, str]] = {
    UI_URI_ARCHIFY: {
        "kind": "cockpit",
        "name": "Archify Cockpit",
        "title": "Cockpit d'architecture Archify",
        "description": "Visualisation interactive auto-contenue de l'architecture du projet (lecture seule).",
    },
    UI_URI_DRAWDB: {
        "kind": "schema",
        "name": "DrawDB ERD",
        "title": "Schéma relationnel DrawDB",
        "description": "Instantané HTML autonome du schéma relationnel du projet (lecture seule).",
    },
}

# État de négociation mémoire de session (annulé à chaque initialize).
_CLIENT_SUPPORTS_UI = False


def reset_ui_state() -> None:
    """Remet à zéro l'état de négociation (appelé avant chaque note de capacité)."""
    global _CLIENT_SUPPORTS_UI
    _CLIENT_SUPPORTS_UI = False


def note_client_capabilities(capabilities: Any) -> None:
    """
    Note la capacité client avec le test strict SEP-1865 : l'extension compte
    uniquement si ``capabilities.extensions[UI_EXTENSION_ID].mimeTypes``
    contient ``text/html;profile=mcp-app`` (« a client that omits it does not count »).
    """
    global _CLIENT_SUPPORTS_UI
    mime_types: list[str] = []
    if isinstance(capabilities, dict):
        extensions = capabilities.get("extensions")
        ui = extensions.get(UI_EXTENSION_ID) if isinstance(extensions, dict) else None
        declared = ui.get("mimeTypes") if isinstance(ui, dict) else None
        if isinstance(declared, list):
            mime_types = [str(m) for m in declared]
    _CLIENT_SUPPORTS_UI = UI_APP_MIME_TYPE in mime_types
    logger.debug(
        "ui_capability_negotiated",
        extra={
            "component": "bridges.mcp_ui",
            "operation": "note_client_capabilities",
            "supported": _CLIENT_SUPPORTS_UI,
            "mimeTypes": mime_types,
        },
    )


def client_supports_ui() -> bool:
    """True uniquement si la capacité a été négociée avec le mime type requis."""
    return _CLIENT_SUPPORTS_UI


def ui_server_capabilities() -> dict[str, Any]:
    """Annonce serveur symétrique (revoyable sans changement de contrat, plan §2)."""
    return {UI_EXTENSION_ID: {"mimeTypes": [UI_APP_MIME_TYPE]}}


def is_ui_uri(uri: Any) -> bool:
    """True si l'adresse appartient au schéma ui:// (avant tout autre handler)."""
    return isinstance(uri, str) and uri.startswith("ui://")


def strip_ui_uri(uri: str) -> str:
    """Retire le paramètre d'état ``?project=`` de l'adresse lue."""
    return uri.split("?", 1)[0]


def project_from_uri(uri: str, session_project: Optional[str] = None) -> str:
    """Résout le projet : paramètre d'adresse (état initial) > état pont > actif."""
    values = parse_qs(urlsplit(uri).query).get("project")
    return (values[0] if values else "") or session_project or "mLoop"


def local_url_for(uri: str, project: str) -> str:
    """Adresse locale de repli (bannière, hôte sans extension)."""
    if strip_ui_uri(uri) == UI_URI_DRAWDB:
        return "http://localhost:8081/"
    artifact = resolve_archify_artifact(project)
    suffix = (
        f"?file={quote(artifact.name)}&project={quote(project)}"
        if artifact
        else f"?project={quote(project)}"
    )
    return "http://localhost:8080/api/archify/html" + suffix


def list_ui_resources() -> list[dict]:
    """Les 2 ressources pré-déclarées (mime type de profil, CSP à connexions vides)."""
    return [
        {
            "uri": uri,
            "name": meta["name"],
            "title": meta["title"],
            "mimeType": UI_APP_MIME_TYPE,
            "description": meta["description"],
            "_meta": {"ui": {"csp": {"connectDomains": [], "resourceDomains": []}}},
        }
        for uri, meta in _UI_REGISTRY.items()
    ]


def read_ui_resource(uri: Any, session_project: Optional[str] = None) -> Optional[dict]:
    """
    Lit une ressource ``ui://``. Retourne :
    - ``None`` : ce n'est pas une adresse ``ui://`` (un autre handler prend le relais) ;
    - ``{"ok": True, "content": {...}}`` : HTML servi via ``resources/read`` ;
    - ``{"ok": False, "message": ...}`` : adresse hors registre (refus non conforme).
    """
    if not is_ui_uri(uri):
        return None
    base = strip_ui_uri(uri)
    registry = _UI_REGISTRY.get(base)
    if registry is None:
        logger.debug(
            "ui_unknown_uri_refused",
            extra={"component": "bridges.mcp_ui", "operation": "read_ui_resource", "uri": uri},
        )
        return {
            "ok": False,
            "message": f"Adresse ui:// hors registre des adresses officielles : {uri}",
        }
    project = project_from_uri(uri, session_project)
    html = build_ui_page(
        registry["kind"],
        uri,
        project,
        local_url_for(base, project),
        UI_MIN_WIDTH_PX,
    )
    return {"ok": True, "content": {"uri": uri, "mimeType": UI_APP_MIME_TYPE, "text": html}}


_TOOL_UI_URIS: dict[str, str] = {
    "show_architecture": UI_URI_ARCHIFY,
    "show_database_schema": UI_URI_DRAWDB,
}


def attach_ui_meta(tools: list[dict]) -> list[dict]:
    """Attache ``_meta.ui.resourceUri`` aux outils ``show_*`` (liaison outil $\rightarrow$ ressource)."""
    for tool in tools:
        resource_uri = _TOOL_UI_URIS.get(tool.get("name", ""))
        if resource_uri:
            tool.setdefault("_meta", {})["ui"] = {"resourceUri": resource_uri}
    return tools


def ui_result(tool_name: str, project: Optional[str] = None) -> tuple[str, Optional[dict]]:
    """
    Résultat d'outil SEP-1865 : le texte est **toujours** significatif.
    - Capacité négociée : texte nominal + ``_meta.ui.resourceUri`` (avec état ``?project=``).
    - Sinon : texte nominal + adresse locale de repli, dégradation journalisée (jamais ``isError``).
    """
    resource_uri = _TOOL_UI_URIS.get(tool_name, UI_URI_DRAWDB)
    resolved = project or "mLoop"
    if client_supports_ui():
        headline = f"Cadre MCP Apps {resource_uri} affiché dans l'IDE — projet : {resolved}."
        meta = {"ui": {"resourceUri": f"{resource_uri}?project={quote(resolved)}"}}
        return headline, meta
    local_url = local_url_for(resource_uri, resolved)
    logger.debug(
        "ui_fallback_local",
        extra={
            "component": "bridges.mcp_ui",
            "operation": "ui_result",
            "tool": tool_name,
            "project": resolved,
            "local_url": local_url,
        },
    )
    return (
        f"Cadre MCP Apps non pris en charge par cet hôte — ouverture locale de repli : {local_url}",
        None,
    )


def notify_ui_project_changed(project: Optional[str] = None) -> None:
    """Notifie SSE ``resources/updated`` sur les 2 ressources ``ui://`` (garde de boucle asynchrone)."""
    from src.bridges.mcp_event_bus import get_event_bus  # import différé (anti-circularité)

    bus = get_event_bus()
    try:
        loop = asyncio.get_running_loop()
        for uri in UI_KNOWN_URIS:
            loop.create_task(bus.notify_resource_updated(uri=uri, session_id=project))
    except RuntimeError as exc:
        logger.debug(
            "ui_project_changed_notification_omitted",
            exc_info=True,
            extra={
                "component": "bridges.mcp_ui",
                "operation": "notify_ui_project_changed",
                "project": project,
                "error": str(exc),
            },
        )
