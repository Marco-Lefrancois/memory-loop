"""
src/bridges/_mcp_elicitation.py — Négociation de capacité et enveloppe
JSON-RPC de l'élicitation Form Mode (MLOOP-213-BE).

Pilier 3 de l'ADR-0387 : le protocole contradictoire *Grill-with-Docs* publie
ses arbitrages par l'extension officielle d'élicitation en **Form Mode**
(spécification MCP du 2026-07-28, falsifiée le 2026-09-24 — OQ-213-01) :

- capacité serveur : ``capabilities.extensions["io.modelcontextprotocol/elicitation"]`` ;
- capacité client : ``capabilities.elicitation`` — le sous-objet ``form`` est
  implicite dès que l'extension est déclarée (*mode form par défaut*) ;
- requête ``elicitation/create`` (serveur → client) : ``mode``, ``message``
  (requis), ``requestedSchema`` (requis, objet plat, champs primitifs) ;
- retour de l'échange : ``{"id": <id>, "result": {"action": "accept" |
  "decline" | "cancel", "content": {...}}}``.

Le mode **URL** de la spécification est hors périmètre (Out-of-Scope du récit)
et n'est jamais servi. Toute la règle métier vit dans
``src/pipelines/grill/_elicitation*.py`` : ce module se contente de négocier la
capacité, de router l'enveloppe et de traduire un refus en erreur JSON-RPC
explicite. Un retour de l'échange conforme clôt l'échange sans écho — le
serveur ne répond jamais à une réponse.
"""

from __future__ import annotations

import logging
from typing import Any, Mapping, Optional

from src.bridges._mcp_protocol_core import register_known_method
from src.pipelines.grill._elicitation import ElicitationError
from src.pipelines.grill._elicitation_flow import (
    answer_elicitation,
    create_elicitation,
)

logger = logging.getLogger(__name__)

ELICITATION_METHOD = "elicitation/create"
ELICITATION_EXTENSION_ID = "io.modelcontextprotocol/elicitation"
ELICITATION_MODE_FORM = "form"
ERROR_INVALID_PARAMS = -32602

# Couture 210 : la méthode doit figurer au registre pour être acheminée.
register_known_method(ELICITATION_METHOD)

_CLIENT_SUPPORTS_FORM = False


def reset_elicitation_state() -> None:
    """Réinitialise la négociation de capacité (nouvelle session)."""
    global _CLIENT_SUPPORTS_FORM
    _CLIENT_SUPPORTS_FORM = False


def note_elicitation_capabilities(capabilities: Any) -> None:
    """Note la capacité d'élicitation du client.

    Deux conventions cohabitent : ``capabilities.elicitation`` (spécification)
    et ``capabilities.extensions[<extension>]`` (symétrie de l'extension MCP
    Apps servie par le même pont). Le sous-objet ``form`` est implicite dès que
    l'extension est déclarée ; sans aucune déclaration, aucun formulaire.
    """
    global _CLIENT_SUPPORTS_FORM
    declared: Any = None
    if isinstance(capabilities, Mapping):
        declared = capabilities.get("elicitation")
        if declared is None:
            extensions = capabilities.get("extensions")
            if isinstance(extensions, Mapping):
                declared = extensions.get(ELICITATION_EXTENSION_ID)
    if declared is None:
        _CLIENT_SUPPORTS_FORM = False
    elif isinstance(declared, Mapping):
        form = declared.get("form", {})
        _CLIENT_SUPPORTS_FORM = form is None or isinstance(form, Mapping)
    else:
        _CLIENT_SUPPORTS_FORM = bool(declared)
    logger.debug(
        "elicitation_capability_negotiated",
        extra={
            "component": "bridges.mcp_elicitation",
            "operation": "note_elicitation_capabilities",
            "supported": _CLIENT_SUPPORTS_FORM,
        },
    )


def client_supports_form_mode() -> bool:
    """Capacité négociée pour la session en cours."""
    return _CLIENT_SUPPORTS_FORM


def elicitation_capabilities() -> dict[str, Any]:
    """Annonce **serveur** de l'extension, à fusionner dans ``capabilities.extensions``."""
    return {ELICITATION_EXTENSION_ID: {"modes": [ELICITATION_MODE_FORM]}}


def _refusal(req_id: Any, reasons: list[str]) -> dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {
            "code": ERROR_INVALID_PARAMS,
            "message": "Échange d'élicitation refusé.",
            "data": {"reasons": reasons},
        },
    }


def handle_elicitation_message(
    req_id: Any,
    request: Mapping[str, Any],
    session_project: Optional[str] = None,
) -> Optional[dict[str, Any]]:
    """Route un échange JSON-RPC d'élicitation (requête ou retour de l'échange).

    Retourne ``None`` lorsque l'échange est clos sans réponse à émettre ; un
    refus est rendu explicite par une erreur JSON-RPC portant ses motifs.
    """
    if request.get("error"):
        # L'environnement n'a pas pu traiter la demande : l'attente subsiste.
        logger.debug(
            "elicitation_create_refusee_par_l_hote",
            extra={
                "component": "bridges.mcp_elicitation",
                "operation": "handle_elicitation_message",
                "id": req_id,
            },
        )
        return None
    try:
        if request.get("method") == ELICITATION_METHOD:
            result = create_elicitation(
                request.get("params"),
                project=session_project,
                form_mode=client_supports_form_mode(),
            )
            return {"jsonrpc": "2.0", "id": req_id, "result": result}
        outcome = answer_elicitation(request, project=session_project)
    except ElicitationError as exc:
        logger.debug(
            "elicitation_refusee",
            exc_info=True,
            extra={
                "component": "bridges.mcp_elicitation",
                "operation": "handle_elicitation_message",
                "id": req_id,
                "reasons": exc.reasons,
            },
        )
        return _refusal(req_id, exc.reasons)
    logger.debug(
        "elicitation_reponse_traitee",
        extra={
            "component": "bridges.mcp_elicitation",
            "operation": "handle_elicitation_message",
            "id": req_id,
            "accepted": outcome.get("accepted"),
            "recorded": outcome.get("recorded"),
        },
    )
    return None
