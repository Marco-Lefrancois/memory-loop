"""
herdr_agents.py - Agent lifecycle primitives for HerdrAdapter.

Covers: start_agent, _runtime_needs_pane_run, prompt_agent, wait_agent,
read_agent_output. Includes Windows fallback to pane run (ADR-0346).
"""

import logging
import sys
from typing import Any, Dict, List, Optional

logger = logging.getLogger("mloop.herdr_agents")


class HerdrAgentsMixin:
    """Agent lifecycle primitives (start, prompt, wait, read)."""

    def start_agent(
        self,
        agent_name: str,
        kind: str,
        pane_id: str,
        extra_args: Optional[List[str]] = None,
        timeout_ms: int = 30000,
    ) -> Dict[str, Any]:
        """
        Launches a recognized coding agent in an existing pane.
        Falls back to pane run on Windows when Herdr cannot handle npm shims.
        """
        args = [
            "agent",
            "start",
            agent_name,
            "--kind",
            kind,
            "--pane",
            pane_id,
            "--timeout",
            str(timeout_ms),
        ]
        if extra_args:
            args.append("--")
            args.extend(extra_args)

        timeout_sec = max(10, timeout_ms // 1000 + 5)
        res = self._exec(args, timeout=timeout_sec)

        if not res.get("success") or self._runtime_needs_pane_run(kind):
            resolved_bin = kind
            if sys.platform == "win32":
                try:
                    from src.core.worker_runtimes import get_worker_runtime

                    runtime_spec = get_worker_runtime(kind)
                except (ImportError, KeyError) as exc:
                    logger.debug(
                        "Registre worker_runtimes indisponible pour ce kind.",
                        exc_info=True,
                        extra={"kind": kind, "error": str(exc)},
                    )
                    runtime_spec = None
                if runtime_spec is not None:
                    resolved = runtime_spec.resolve_binary()
                    if resolved:
                        resolved_bin = resolved
                        logger.info(
                            f"Windows fallback: résolution vers exe absolu '{resolved_bin}'"
                        )

            cmd_str = (
                f'& "{resolved_bin}" {" ".join(extra_args or [])}'.strip()
                if sys.platform == "win32"
                else f"{resolved_bin} {' '.join(extra_args or [])}".strip()
            )
            logger.info(f"Fallback vers pane run: '{cmd_str}' sur le volet {pane_id}")
            self.run_pane_command(pane_id, cmd_str)
            try:
                self._exec(["agent", "rename", pane_id, agent_name])
            except Exception as exc:
                logger.debug(
                    "Renommage post-fallback du worker échoué.",
                    exc_info=True,
                    extra={"pane_id": pane_id, "agent_name": agent_name, "error": str(exc)},
                )
            return {
                "success": True,
                "fallback": "pane_run",
                "pane_id": pane_id,
                "agent_name": agent_name,
            }

        return res

    def _runtime_needs_pane_run(self, kind: str) -> bool:
        """True si le runtime exige le fallback pane run (shim npm, ADR-0346)."""
        if sys.platform != "win32":
            return False
        try:
            from src.core.worker_runtimes import get_worker_runtime

            return get_worker_runtime(kind).needs_pane_run_fallback()
        except (ImportError, KeyError) as exc:
            logger.debug(
                "Registre worker_runtimes indisponible pour la décision pane-run.",
                exc_info=True,
                extra={"kind": kind, "error": str(exc)},
            )
            return False

    def prompt_agent(
        self,
        agent_name_or_pane: str,
        prompt_text: str,
        wait: bool = False,
        timeout_ms: int = 10000,
    ) -> Dict[str, Any]:
        """
        Submits a prompt to a running agent and optionally waits for completion.
        Defaults to wait=False (fire-and-acknowledge) to prevent blocking MCP transports.
        """
        args = ["agent", "prompt", agent_name_or_pane, prompt_text]
        if wait:
            args.append("--wait")
            args.extend(["--timeout", str(timeout_ms)])

        timeout_sec = max(5, timeout_ms // 1000 + 5) if wait else 10
        res = self._exec(args, timeout=timeout_sec)
        if res.get("success"):
            res["delivery_status"] = "DELIVERED"
            res["agent"] = agent_name_or_pane
        return res

    def wait_agent(
        self,
        agent_name_or_pane: str,
        until_states: Optional[List[str]] = None,
        timeout_ms: int = 10000,
    ) -> Dict[str, Any]:
        """
        Waits for an agent to reach specific lifecycle states.
        Gracefully handles timeouts as 'still working'.
        """
        args = ["agent", "wait", agent_name_or_pane]
        states = until_states or ["idle", "done", "blocked"]
        for s in states:
            args.extend(["--until", s])
        args.extend(["--timeout", str(timeout_ms)])

        timeout_sec = max(5, timeout_ms // 1000 + 5)
        res = self._exec(args, timeout=timeout_sec)
        if not res.get("success") and res.get("error") == "timeout":
            return {
                "success": True,
                "agent_status": "working",
                "completed": False,
                "timed_out": True,
                "message": f"Agent '{agent_name_or_pane}' is still executing (poll again).",
            }
        return res

    def read_agent_output(
        self,
        agent_name_or_pane: str,
        lines: int = 120,
        source: str = "recent-unwrapped",
    ) -> Dict[str, Any]:
        """
        Reads terminal output from an agent. Falls back to 'visible' source
        when 'recent-unwrapped' fails because the agent is still working.
        """
        res = self._exec(
            [
                "agent",
                "read",
                agent_name_or_pane,
                "--source",
                source,
                "--lines",
                str(lines),
            ]
        )
        if not res.get("success") and source == "recent-unwrapped":
            err_msg = str(res.get("stderr", "")) + str(res.get("error", ""))
            if "agent_not_idle" in err_msg or "cannot read while working" in err_msg:
                logger.debug(
                    f"Agent '{agent_name_or_pane}' is working. "
                    f"Falling back to 'visible' read source.",
                    extra={"agent": agent_name_or_pane, "requested_source": source},
                )
                res = self._exec(
                    [
                        "agent",
                        "read",
                        agent_name_or_pane,
                        "--source",
                        "visible",
                        "--lines",
                        str(lines),
                    ]
                )
                if res.get("success"):
                    res["source_fallback"] = "visible"
                    res["worker_was_active"] = True
        return res

    def list_agents(self) -> Dict[str, Any]:
        """Lists all registered Herdr agents and their statuses."""
        return self._exec(["agent", "list"])
