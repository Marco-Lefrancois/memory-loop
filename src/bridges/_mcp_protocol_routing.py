"""
_mcp_protocol_routing.py — Routage par en-têtes (HTTP/SSE) et métadonnées stdio.

La décision de route est prise sur les **seuls en-têtes** de la requête :
`route_from_headers()` ne lit jamais le corps JSON-RPC. Le corps reste
l'autorité de l'enveloppe (`id` / `params`) — toute divergence en-tête/corps est
journalisée comme non-conformité puis ignorée, jamais rejetée.

Frontière active assumée (Admission of Limits) : la passerelle HTTP et le
processeur de messages sont colocalisés dans ce process.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from src.bridges._mcp_protocol_core import (
    HEADER_METHOD,
    HEADER_PROTOCOL_VERSION,
    HEADER_TOOL_NAME,
    HEADER_TOOL_NAME_ALIAS,
    KNOWN_METHODS,
    PROTOCOL_VERSION_LEGACY,
    ROUTING_META_KEY,
    SUPPORTED_PROTOCOL_VERSIONS,
    VersionDecision,
    flatten_headers,
    negotiate_version,
)


@dataclass(frozen=True)
class HeaderRoute:
    """Route résolue uniquement à partir des en-têtes de la requête."""

    decision: VersionDecision
    method: str | None
    tool_name: str | None
    header_present: bool
    nonconformities: tuple[str, ...]

    @property
    def accepted(self) -> bool:
        return self.decision.accepted

    @property
    def method_usable(self) -> bool:
        return bool(self.method) and "method_out_of_registry" not in self.nonconformities


def route_from_headers(headers: Mapping[str, Any] | Iterable[tuple[str, str]]) -> HeaderRoute:
    """
    Achemine la requête à partir des seuls en-têtes (récit §2, 210-Q2).

    Contrôles d'admissibilité :
    - version    : registre unique → inconnue = refus dur par l'appelant ;
    - méthode    : doit accompagner toute requête et figurer au registre ;
    - nom d'outil: uniquement sur `tools/call` (omis ailleurs).

    Un client sans en-tête de version est un client hérité : aucun contrôle
    d'en-tête moderne ne lui est applicable (l'absence n'est jamais un rejet).
    """
    flat = flatten_headers(headers)
    raw_version = flat.get(HEADER_PROTOCOL_VERSION.lower())
    decision = negotiate_version(raw_version)

    if not raw_version:
        return HeaderRoute(decision, None, None, False, ())

    nonconformities: list[str] = []
    method = flat.get(HEADER_METHOD.lower())
    if not method:
        nonconformities.append("method_header_missing")
        method = None
    elif method not in KNOWN_METHODS:
        nonconformities.append("method_out_of_registry")

    tool_name = flat.get(HEADER_TOOL_NAME.lower()) or flat.get(HEADER_TOOL_NAME_ALIAS.lower())
    if tool_name:
        if method == "tools/call":
            pass
        elif method is None:
            # Portée indéterminable sans méthode : non-conformité déjà posée.
            tool_name = None
        else:
            # Toute autre méthode exclut le nom d'outil → ignoré, jamais rejeté.
            nonconformities.append("tool_name_out_of_scope")
            tool_name = None
    elif method == "tools/call":
        nonconformities.append("tool_name_missing_on_tool_call")

    return HeaderRoute(
        decision=decision,
        method=method,
        tool_name=tool_name,
        header_present=True,
        nonconformities=tuple(nonconformities),
    )


def response_headers(
    negotiated: str,
    method: str | None = None,
    tool_name: str | None = None,
) -> dict[str, str]:
    """En-têtes de réponse : version toujours, méthode toujours, outil si appel."""
    headers = {HEADER_PROTOCOL_VERSION: negotiated}
    if method:
        headers[HEADER_METHOD] = method
    if method == "tools/call" and tool_name:
        headers[HEADER_TOOL_NAME] = tool_name
    return headers


# ──────────────────────────────────────────────────────────────────────────
# MÉTADONNÉES DE ROUTAGE (stdio) & ENVELOPPE D'INITIALISATION
# ──────────────────────────────────────────────────────────────────────────


def build_routing_meta(
    *,
    protocol_version: str,
    method: str | None,
    tool_name: str | None = None,
) -> dict[str, dict[str, str]]:
    """Construit `_meta.routing = {protocolVersion, method, toolName?}` (stdio)."""
    routing: dict[str, str] = {
        "protocolVersion": protocol_version or PROTOCOL_VERSION_LEGACY,
        "method": method or "",
    }
    # Le nom d'outil n'accompagne que les appels d'outils (jamais les
    # notifications ni les autres méthodes).
    if method == "tools/call" and tool_name:
        routing["toolName"] = tool_name
    return {ROUTING_META_KEY: routing}


def attach_routing_meta(
    response: Any,
    *,
    protocol_version: str,
    method: str | None,
    tool_name: str | None = None,
) -> Any:
    """Injecte les métadonnées de routage dans le `result` d'une réponse JSON-RPC."""
    if not isinstance(response, dict):
        return response
    container = response.get("result")
    if not isinstance(container, dict):
        return response
    meta = container.get("_meta")
    merged = dict(meta) if isinstance(meta, dict) else {}
    merged.update(
        build_routing_meta(protocol_version=protocol_version, method=method, tool_name=tool_name)
    )
    container["_meta"] = merged
    return response


def enrich_initialize_result(
    result: Mapping[str, Any], decision: VersionDecision
) -> dict[str, Any]:
    """Publie la révision retenue + le registre unique des versions supportées."""
    enriched = dict(result)
    enriched["protocolVersion"] = decision.negotiated or PROTOCOL_VERSION_LEGACY
    enriched["supportedVersions"] = list(SUPPORTED_PROTOCOL_VERSIONS)
    return enriched
