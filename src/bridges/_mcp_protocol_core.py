"""
_mcp_protocol_core.py — Registre unique et négociation de version MCP (MLOOP-210-BE).

Socle **réutilisable** par toutes les couches du transport (routage HTTP/SSE,
politique de repli, poignée de main stdio) : toute dérive entre le poignée de
main et les en-têtes est rendue impossible par construction (ADR-005 — 210-Q1).

Règles tranchées par le récit (SSOT) :
- Seule une version **absente du registre** déclenche un refus dur (-32600).
- L'absence de déclaration n'est jamais un rejet : client hérité sur la
  révision de base publiée.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Literal, Mapping

# ──────────────────────────────────────────────────────────────────────────
# REGISTRE UNIQUE — source de vérité unique (anti-dérive handshake / headers)
# ──────────────────────────────────────────────────────────────────────────

PROTOCOL_VERSION_TARGET: str = "2026-07-28"
PROTOCOL_VERSION_LEGACY: str = "2024-11-05"
SUPPORTED_PROTOCOL_VERSIONS: tuple[str, ...] = (
    "2026-07-28",
    "2025-11-25",
    "2024-11-05",
)

HEADER_PROTOCOL_VERSION: str = "MCP-Protocol-Version"
HEADER_METHOD: str = "MCP-Method"
HEADER_TOOL_NAME: str = "MCP-Tool-Name"
# SEP-2243 (spec 2026-07-28) : les en-têtes officiels sont `Mcp-Method` /
# `Mcp-Name` (le `Mcp-Tool-Name` a été fusionné dans `Mcp-Name`).
# HTTP étant insensible à la casse, `MCP-Method` / `MCP-Protocol-Version`
# coïncident déjà ; `Mcp-Name` est accepté en alias d'interop, le nom canonique
# du récit restant `MCP-Tool-Name` (écart consigné OQ-210-02).
HEADER_TOOL_NAME_ALIAS: str = "Mcp-Name"

JSONRPC_INVALID_REQUEST: int = -32600
ROUTING_META_KEY: str = "routing"
META_PROTOCOL_VERSION_KEY: str = "io.modelcontextprotocol/protocolVersion"

# Frontière active assumée (Admission of Limits, récit Out-of-Scope) :
# l'inventaire exhaustif des ponts exposé en réseau n'est pas clôturé et
# **aucun pont supplémentaire n'est présumé couvert**. Ce socle couvre
# strictement les 4 ponts nommés par ADR-005 ; l'ajout d'un pont à cette
# liste exige une décision d'architecture explicite (testé par la suite
# `test_mcp_protocol_socle`).
COVERED_BRIDGES: tuple[str, ...] = (
    "mcp_loop_mem",
    "mcp_sse_server",
    "mcp_proxy_router",
    "mcp_resilience_guard",
)

# Politique de repli unifiée (macro ADR-004 Q1) — publiée pour réutilisation
# par les extensions bâties sur ce socle (211-214).
FALLBACK_POLICY: dict[str, Any] = {
    "policy_id": "mloop.fallback.v1",
    "scope": "per_request",
    "process_local": True,
    "mode_when_degraded": "standard_sync",
    "never_rejects": True,
    "reusable_by": ("tasks", "mcp_apps", "elicitation", "skills"),
}

KNOWN_METHODS: set[str] = {
    "initialize",
    "server/discover",
    "tools/list",
    "tools/call",
    "resources/list",
    "resources/read",
    "resources/templates/list",
    "prompts/list",
    "prompts/get",
    "ping",
    "notifications/initialized",
    "notifications/cancelled",
    "notifications/roots/list_changed",
}


def register_known_method(method: str) -> None:
    """Ouvre le registre de méthodes à une extension aval (211-214)."""
    if method and method not in KNOWN_METHODS:
        KNOWN_METHODS.add(method)


# ──────────────────────────────────────────────────────────────────────────
# MODÈLE DE DÉCISION
# ──────────────────────────────────────────────────────────────────────────

VersionStatus = Literal["target", "obsolete", "absent", "unknown"]


@dataclass(frozen=True)
class VersionDecision:
    """Issue de la négociation face au registre unique."""

    status: VersionStatus
    requested: str | None
    negotiated: str | None
    accepted: bool

    @property
    def is_declared(self) -> bool:
        return self.status in ("target", "obsolete")


def negotiate_version(requested: str | None) -> VersionDecision:
    """
    Confronte la version souhaitée au registre unique.

    - absente          → client hérité, révision de base publiée (jamais rejet)
    - connue == cible  → révision 2026-07-28 retenue
    - connue != cible  → révision déclarée retenue + alerte d'obsolescence
    - inconnue         → inadmissible (refus -32600 par l'appelant)
    """
    if requested is None or not str(requested).strip():
        return VersionDecision("absent", None, PROTOCOL_VERSION_LEGACY, True)
    raw = str(requested).strip()
    if raw not in SUPPORTED_PROTOCOL_VERSIONS:
        return VersionDecision("unknown", raw, None, False)
    status: VersionStatus = "target" if raw == PROTOCOL_VERSION_TARGET else "obsolete"
    return VersionDecision(status, raw, raw, True)


def declared_version(
    params: Mapping[str, Any] | None,
    headers: Mapping[str, Any] | None = None,
) -> tuple[str | None, str]:
    """
    Extrait la version déclarée par le client.

    Priorité : en-tête HTTP (vérité de transport, récit §2) → `_meta`
    `io.modelcontextprotocol/protocolVersion` (spec 2026-07-28, utile en stdio
    où il n'existe aucun en-tête) → `params.protocolVersion` (poignée de main).
    Retourne `(version, source)` avec source ∈ {header, meta, params, absent}.
    """
    raw = header_get(headers, HEADER_PROTOCOL_VERSION)
    if raw:
        return raw, "header"
    meta = (params or {}).get("_meta")
    if isinstance(meta, dict):
        meta_version = meta.get(META_PROTOCOL_VERSION_KEY)
        if meta_version:
            return str(meta_version), "meta"
    params_version = (params or {}).get("protocolVersion")
    if params_version:
        return str(params_version), "params"
    return None, "absent"


def invalid_version_error(req_id: Any, requested: str | None) -> dict[str, Any]:
    """Refus dur réservé aux versions absentes du registre (JSON-RPC -32600)."""
    return {
        "jsonrpc": "2.0",
        "error": {
            "code": JSONRPC_INVALID_REQUEST,
            "message": "Unsupported protocol version",
            "data": {
                "supported": list(SUPPORTED_PROTOCOL_VERSIONS),
                "requested": requested,
            },
        },
        "id": req_id,
    }


# ──────────────────────────────────────────────────────────────────────────
# HELPERS D'EN-TÊTES
# ──────────────────────────────────────────────────────────────────────────


def flatten_headers(headers: Any) -> dict[str, str]:
    """Normalise un mapping d'en-têtes vers des clés minuscules (RFC 7230)."""
    if headers is None:
        return {}
    if hasattr(headers, "items"):
        items = headers.items()
    else:  # pragma: no cover - séquence de tuples
        items = headers
    flat: dict[str, str] = {}
    for key, value in items:
        flat[str(key).lower()] = str(value)
    return flat


def header_get(headers: Any, name: str) -> str | None:
    """Lit un en-tête sans tenir compte de la casse ; `None` si absent/vide."""
    if not headers:
        return None
    flat = flatten_headers(headers)
    value = flat.get(name.lower())
    return value if value else None


def headers_from_mapping(
    headers: Mapping[str, Any] | Iterable[tuple[str, str]] | None,
) -> dict[str, str]:
    """Copie aplatie d'un mapping d'en-têtes (utilisé par les couches HTTP)."""
    return flatten_headers(headers)
