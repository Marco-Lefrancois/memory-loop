"""
herdr_worker.py - Worker lifecycle, evidence harvesting and zombie management.

Covers: spawn_story_worker, harvest_story_evidence, cleanup_worker,
audit_and_reap_zombies, detect_stalled_agents, reap_zombie_workers,
filter_terminal_bloat, list_agents, TASK_MODEL_MAP.

Refactored: Core worker logic split into herdr_worker_core.py (ADR-0202 <=300L).
"""

import json
import os
import re
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("mloop.herdr_worker")


class HerdrWorkerMixin:
    """Worker lifecycle, evidence harvesting and zombie management."""

    TASK_MODEL_MAP = {
        "deepening": "nmedia_cloud/claude-opus-4.8",
        "validation": "nmedia_cloud/gpt-5.6-terra-thinking",
        "deepsearch": "nmedia_cloud/claude-sonnet-5",
        # Free tier natif OpenCode (ADR-0388) : facilite dev/build sans coût LiteLLM.
        # Portes qualité (deepening/validation/deepsearch/compaction) inchangées.
        "build": "opencode/mimo-v2.6-flash-free",
        "compaction": "nmedia_cloud/gemini-3.8-flash",
    }

    @staticmethod
    def filter_terminal_bloat(raw_text: str) -> str:
        """Filters ANSI escape sequences, spinners, and noisy progress bars."""
        if not raw_text:
            return ""
        ansi_regex = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
        cleaned = ansi_regex.sub("", raw_text).replace("\r\n", "\n").replace("\r", "\n")
        spinners = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏", "◐", "◓", "◑", "◒"]
        skip_tokens = {"Loading...", "Working...", "Compiling..."}
        lines = []
        for line in cleaned.splitlines():
            s = line.strip()
            if not s or any(s.startswith(sp) for sp in spinners) or s in skip_tokens:
                continue
            lines.append(line)
        return "\n".join(lines)

    def spawn_story_worker(
        self,
        project_name: str,
        story_id: str,
        kind: str = "opencode",
        model: Optional[str] = None,
        task_type: Optional[str] = None,
        root_dir: Optional[str] = None,
        extra_args: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Spawns a clean-slate worker pane dedicated to a User Story."""
        from src.core.herdr_worker_core import spawn_story_worker_impl

        return spawn_story_worker_impl(
            self, project_name, story_id, kind, model, task_type, root_dir, extra_args
        )

    def harvest_story_evidence(
        self,
        project_name: str,
        story_id: str,
        project_path: Optional[str] = None,
        lines: int = 150,
    ) -> Dict[str, Any]:
        """Extracts execution logs, filters bloat, saves to evidence JSON."""
        from src.core.herdr_worker_core import harvest_story_evidence_impl

        return harvest_story_evidence_impl(self, project_name, story_id, project_path, lines)

    def cleanup_worker(self, story_id_or_pane: str) -> Dict[str, Any]:
        """Closes a worker pane and cleans up its resources."""
        from src.core.herdr_worker_core import cleanup_worker_impl

        return cleanup_worker_impl(self, story_id_or_pane)

    def _extract_agents_list(self, agents_data: Any) -> List[Dict[str, Any]]:
        """Extracts agents list from Herdr response (v0.8.x nesting)."""
        from src.core.herdr_worker_core import extract_agents_list_impl

        return extract_agents_list_impl(agents_data)

    def audit_and_reap_zombies(self, project_name: Optional[str] = None) -> Dict[str, Any]:
        """Teardown Gate (Zero Zombie Policy - ADR-0306 / ADR-0345)."""
        from src.core.herdr_worker_core import audit_and_reap_zombies_impl

        return audit_and_reap_zombies_impl(self, project_name)

    def detect_stalled_agents(self, timeout_sec: int = 300) -> List[Dict[str, Any]]:
        """Detects inactive agents (idle, stopped, blocked or no state)."""
        from src.core.herdr_worker_core import detect_stalled_agents_impl

        return detect_stalled_agents_impl(self, timeout_sec)

    def reap_zombie_workers(self, timeout_sec: int = 300, force: bool = False) -> Dict[str, Any]:
        """Ferme automatiquement les volets/agents orphelins (Zéro Zombie)."""
        from src.core.herdr_worker_core import reap_zombie_workers_impl

        return reap_zombie_workers_impl(self, timeout_sec, force)
