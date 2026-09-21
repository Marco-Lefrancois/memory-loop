"""
herdr_adapter.py - Herdr v0.8.0 Core Adapter for mLoop Engine (Thin Facade)

Encapsulates Herdr CLI commands and Unix socket operations (~/.herdr/herdr.sock)
to provide high-level, deterministic Python primitives for workspace management,
pane splitting, agent lifecycle tracking, PTY reading, and worker cleanup.

Modular decomposition (ADR-0202 ≤ 300 lines per module):
  - herdr_core.py       : CLI executor & Windows shim guardrail (ADR-0325 / ADR-0369)
  - herdr_daemon.py     : Daemon lifecycle & auto-heal (Zero-Fail Carryover)
  - herdr_panes.py      : Workspace, pane, layout & notification primitives
  - herdr_agents.py     : Agent lifecycle (start, prompt, wait, read)
  - herdr_worker.py     : Worker spawn, evidence, zombie management
"""

from typing import Dict, Any, List, Optional

from src.core.herdr_core import HerdrCoreMixin
from src.core.herdr_daemon import HerdrDaemonMixin
from src.core.herdr_panes import HerdrPanesMixin
from src.core.herdr_agents import HerdrAgentsMixin
from src.core.herdr_worker import HerdrWorkerMixin


class HerdrAdapter(
    HerdrCoreMixin,
    HerdrDaemonMixin,
    HerdrPanesMixin,
    HerdrAgentsMixin,
    HerdrWorkerMixin,
):
    """
    Core interface for controlling Herdr v0.8.0 daemon via CLI and JSON output.

    Composes all mixin modules into a single coherent API surface.
    Backward-compatible: all existing `from src.core.herdr_adapter import HerdrAdapter`
    imports continue to work unchanged.
    """

    pass


# Singleton instance helper (backward-compatible)
herdr = HerdrAdapter()
