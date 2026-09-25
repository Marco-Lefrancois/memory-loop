"""
_mcp_notifications.py — Poussee SSE apres un `tools/call` (MLOOP-211-BE).

Extraction mecanique du carrefour `mcp_loop_mem` (ADR-0202, plafond des 300
lignes) : le pont ne fait plus qu'importer et appeler `emit_tool_notifications`,
la logique de selection des notifications pertinentes reste strictement
identique.

Le rendu reste 100% local : aucune donnee n'est exfiltree, seul le bus
d'evenements du pont est alimente en flux continu (SSE) lorsque des clients
sont abonnes.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)


def emit_tool_notifications(bus: Any, params: dict, session_project: str | None) -> None:
    """Emet les notifications SSE pertinentes apres un tools/call."""
    tool_name = params.get("name", "")

    if tool_name == "set_phase":
        _schedule(
            lambda: bus.notify_tools_list_changed(session_id=session_project),
            component="bridges.mcp_loop_mem",
            operation="notify_set_phase",
        )

    if tool_name in ("loop_mem_search", "loop_mem_code_rag", "loop_mem_timeline"):
        _schedule(
            lambda: bus.notify_resource_updated(
                uri=f"mloop://project/{session_project or 'mLoop'}/observation/latest",
                session_id=session_project,
            ),
            component="bridges.mcp_loop_mem",
            operation="notify_observation_updated",
            tool=tool_name,
        )


def _schedule(
    factory: Callable[[], Any], *, component: str, operation: str, tool: str | None = None
) -> None:
    """Planifie une coroutine SSE ; boucle absente = omission tracee, jamais d'erreur."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError as exc:
        logger.debug(
            "Boucle asyncio non disponible, notification SSE omise",
            exc_info=True,
            extra={
                "component": component,
                "operation": operation,
                "tool": tool,
                "error": str(exc),
            },
        )
        return
    loop.create_task(factory())
