"""Handlers Architecture — Facade de réexportation (découpage ADR-0202)."""
from __future__ import annotations

# Core (grill, to-tshirt, wayfinder, to-spec, to-tickets, graph-run)
from src.commands.handlers.archify_core import (  # noqa: F401
    handle_grill,
    handle_to_tshirt,
    handle_wayfinder,
    handle_to_spec,
    handle_to_tickets,
    handle_graph_run,
)

# Analysis (deepen, diagnose, goal-cascade, to-sow)
from src.commands.handlers.archify_analysis import (  # noqa: F401
    handle_deepen,
    handle_diagnose,
    handle_goal_cascade,
    handle_to_sow,
)

__all__ = [
    # Core
    "handle_grill",
    "handle_to_tshirt",
    "handle_wayfinder",
    "handle_to_spec",
    "handle_to_tickets",
    "handle_graph_run",
    # Analysis
    "handle_deepen",
    "handle_diagnose",
    "handle_goal_cascade",
    "handle_to_sow",
]
