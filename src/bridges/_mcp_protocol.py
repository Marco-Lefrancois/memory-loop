"""
_mcp_protocol.py — Socle Protocolaire MCP 2026-07-28 (MLOOP-210-BE / ADR-0387).

Déclaration **unique** du registre de versions, des noms d'en-têtes et de la
politique de repli protocolaire, partagée par :
- la négociation à l'initialisation (poignée de main),
- le routage par en-têtes (transports HTTP / SSE),
- l'exposition `_meta.routing` (transport stdio).

Le registre est réutilisable par les extensions aval (211 Tasks, 212 MCP Apps,
213 Elicitation, 214 Skills) — voir ``register_known_method``.

Ce module est une **façade de ré-export** : l'implémentation est découpée
selon ADR-0202 (plafond modulaire) :
- ``_mcp_protocol_core``    : registre, négociation, extraction de version ;
- ``_mcp_protocol_routing`` : route par en-têtes, en-têtes de réponse,
                              ``_meta.routing``, enveloppe d'initialisation ;
- ``_mcp_protocol_fallback``: politique de repli macro Q1 + observabilité.
"""

from __future__ import annotations

from src.bridges._mcp_protocol_core import (
    COVERED_BRIDGES,
    FALLBACK_POLICY,
    HEADER_METHOD,
    HEADER_PROTOCOL_VERSION,
    HEADER_TOOL_NAME,
    HEADER_TOOL_NAME_ALIAS,
    JSONRPC_INVALID_REQUEST,
    KNOWN_METHODS,
    META_PROTOCOL_VERSION_KEY,
    PROTOCOL_VERSION_LEGACY,
    PROTOCOL_VERSION_TARGET,
    ROUTING_META_KEY,
    SUPPORTED_PROTOCOL_VERSIONS,
    VersionDecision,
    VersionStatus,
    declared_version,
    flatten_headers,
    header_get,
    invalid_version_error,
    negotiate_version,
    register_known_method,
)
from src.bridges._mcp_protocol_fallback import (
    FallbackOutcome,
    apply_fallback_policy,
    get_adoption_metrics,
    get_fallback_journal,
    get_obsolete_alerts,
    reset_protocol_observability,
)
from src.bridges._mcp_protocol_routing import (
    HeaderRoute,
    attach_routing_meta,
    build_routing_meta,
    enrich_initialize_result,
    response_headers,
    route_from_headers,
)

# Rétrocompatibilité des helpers privés (usage interne historique).
_flatten_headers = flatten_headers
_header_get = header_get

__all__ = [
    "COVERED_BRIDGES",
    "FALLBACK_POLICY",
    "HEADER_METHOD",
    "HEADER_PROTOCOL_VERSION",
    "HEADER_TOOL_NAME",
    "HEADER_TOOL_NAME_ALIAS",
    "JSONRPC_INVALID_REQUEST",
    "KNOWN_METHODS",
    "META_PROTOCOL_VERSION_KEY",
    "PROTOCOL_VERSION_LEGACY",
    "PROTOCOL_VERSION_TARGET",
    "ROUTING_META_KEY",
    "SUPPORTED_PROTOCOL_VERSIONS",
    "FallbackOutcome",
    "HeaderRoute",
    "VersionDecision",
    "VersionStatus",
    "apply_fallback_policy",
    "attach_routing_meta",
    "build_routing_meta",
    "declared_version",
    "enrich_initialize_result",
    "flatten_headers",
    "get_adoption_metrics",
    "get_fallback_journal",
    "get_obsolete_alerts",
    "header_get",
    "invalid_version_error",
    "negotiate_version",
    "register_known_method",
    "reset_protocol_observability",
    "response_headers",
    "route_from_headers",
]
