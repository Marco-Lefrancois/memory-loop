"""
herdr_panes.py - Workspace, pane, layout and notification primitives for HerdrAdapter.

Covers: create_workspace, split_pane, close_pane, run_pane_command,
wait_pane_output, capture_pane_logs, export_layout, apply_layout,
report_metadata, show_notification, explain_agent, plugin_invoke.
"""

import json
import os
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger("mloop.herdr_panes")


class HerdrPanesMixin:
    """Workspace, pane layout, notification and plugin primitives."""

    # --- Layout primitives ---

    def create_workspace(
        self, cwd: str, label: str = "mloop-worker", no_focus: bool = True
    ) -> Dict[str, Any]:
        """Creates a workspace. Returns JSON with .result.root_pane.pane_id."""
        args = ["workspace", "create", "--cwd", cwd, "--label", label]
        if no_focus:
            args.append("--no-focus")
        res = self._exec(args)
        if res.get("success") and isinstance(res.get("result"), dict):
            data = res["result"]
            root_pane = data.get("result", {}).get("root_pane", {}).get("pane_id") or data.get(
                "root_pane", {}
            ).get("pane_id")
            res["root_pane_id"] = root_pane
        return res

    def split_pane(
        self,
        target_pane_id: str,
        direction: str = "right",
        no_focus: bool = True,
    ) -> Dict[str, Any]:
        """Splits an existing pane in the specified direction."""
        args = ["pane", "split", target_pane_id, "--direction", direction]
        if no_focus:
            args.append("--no-focus")
        res = self._exec(args)
        if res.get("success") and isinstance(res.get("result"), dict):
            data = res["result"]
            new_pane = data.get("result", {}).get("pane", {}).get("pane_id") or data.get(
                "pane", {}
            ).get("pane_id")
            res["new_pane_id"] = new_pane
        return res

    def close_pane(self, pane_id: str) -> Dict[str, Any]:
        """Closes a Herdr terminal pane."""
        return self._exec(["pane", "close", pane_id])

    # --- Pane primitives ---

    def run_pane_command(self, pane_id: str, command_text: str) -> Dict[str, Any]:
        """Runs a raw shell command inside a terminal pane."""
        return self._exec(["pane", "run", pane_id, command_text])

    def wait_pane_output(
        self, pane_id: str, regex: str, timeout_ms: int = 120000
    ) -> Dict[str, Any]:
        """Waits for specific regex output in a pane's rendered terminal rows."""
        timeout_sec = max(5, timeout_ms // 1000)
        return self._exec(
            [
                "pane",
                "wait-output",
                pane_id,
                "--regex",
                regex,
                "--timeout",
                str(timeout_ms),
            ],
            timeout=timeout_sec + 5,
        )

    def capture_pane_logs(self, pane_id: str, lines: int = 100) -> Dict[str, Any]:
        """Captures recent lines of log output from a pane."""
        return self._exec(["pane", "capture", "-p", pane_id, "--lines", str(lines)])

    # --- Advanced layout (Herdr v0.8.2) ---

    def export_layout(
        self, tab_id: Optional[str] = None, pane_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Exports the portable BSP layout tree for a tab or pane."""
        args = ["layout", "export"]
        if tab_id:
            args.extend(["--tab", tab_id])
        elif pane_id:
            args.extend(["--pane", pane_id])
        return self._exec(args)

    def apply_layout(
        self,
        workspace_id: str,
        root_tree: Dict[str, Any],
        tab_label: str = "dev",
        focus: bool = False,
    ) -> Dict[str, Any]:
        """Applies a declarative BSP layout tree to create or replace a tab."""
        layout_payload = {
            "workspace_id": workspace_id,
            "tab_label": tab_label,
            "focus": focus,
            "root": root_tree,
        }
        args = ["layout", "apply", "--json", json.dumps(layout_payload)]
        return self._exec(args)

    # --- Metadata & notifications ---

    def report_metadata(
        self,
        pane_id: str,
        source: str = "mloop",
        title: Optional[str] = None,
        display_agent: Optional[str] = None,
        state_labels: Optional[Dict[str, str]] = None,
        tokens: Optional[Dict[str, str]] = None,
        ttl_ms: Optional[int] = None,
        seq: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Reports display-only metadata tokens for a pane sidebar."""
        args = ["pane", "report-metadata", pane_id, "--source", source]
        if title:
            args.extend(["--title", title[:80]])
        if display_agent:
            args.extend(["--display-agent", display_agent[:80]])
        if state_labels:
            for st, lbl in state_labels.items():
                args.extend(["--state-label", f"{st}={lbl[:80]}"])
        if tokens:
            for k, v in tokens.items():
                args.extend(["--token", f"{k}={str(v)[:80]}"])
        if ttl_ms:
            args.extend(["--ttl-ms", str(ttl_ms)])
        if seq is not None:
            args.extend(["--seq", str(seq)])
        return self._exec(args)

    def show_notification(
        self,
        title: str,
        body: Optional[str] = None,
        position: str = "bottom-right",
        sound: str = "none",
    ) -> Dict[str, Any]:
        """Displays a lightweight toast notification in Herdr UI."""
        if os.environ.get("HERDR_DISABLE_SOUND") == "1":
            sound = "none"
        args = ["notification", "show", title, "--position", position, "--sound", sound]
        if body:
            args.extend(["--body", body])
        return self._exec(args)

    # --- Agent explain & plugin ---

    def explain_agent(
        self,
        target: Optional[str] = None,
        file_path: Optional[str] = None,
        agent_label: Optional[str] = None,
        json_mode: bool = True,
        verbose: bool = False,
    ) -> Dict[str, Any]:
        """Explains rule matching and bottom-buffer classification for an agent."""
        args = ["agent", "explain"]
        if target:
            args.append(target)
        if file_path:
            args.extend(["--file", file_path])
        if agent_label:
            args.extend(["--agent", agent_label])
        if json_mode:
            args.append("--json")
        if verbose:
            args.append("--verbose")
        return self._exec(args)

    def plugin_invoke(self, action_id: str, plugin_id: Optional[str] = None) -> Dict[str, Any]:
        """Invokes an installed Herdr plugin action."""
        args = ["plugin", "action", "invoke", action_id]
        if plugin_id:
            args.extend(["--plugin", plugin_id])
        return self._exec(args)
