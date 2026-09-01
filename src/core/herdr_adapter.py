"""
herdr_adapter.py - Herdr v0.8.0 Core Adapter for mLoop Engine

Encapsulates Herdr CLI commands and Unix socket operations (~/.herdr/herdr.sock)
to provide high-level, deterministic Python primitives for workspace management,
pane splitting, agent lifecycle tracking, PTY reading, and worker cleanup.
"""

import json
import os
import re
import sys
import subprocess
import shutil
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger("mloop.herdr_adapter")


def ensure_windows_agent_binaries() -> None:
    """
    Auto-repair guardrail for Windows agent shims (ADR-0325).
    
    When npm packages (like opencode-ai) are installed globally on Windows, npm creates
    conflicting shims in %APPDATA%/npm/ (opencode.ps1, extensionless opencode bash script).
    When Herdr executes Start-Process -FilePath opencode, PowerShell attempts to execute
    the .ps1 script or extensionless script directly via Win32 CreateProcess, triggering:
    'Start-Process : %1 n'est pas une application Win32 valide' (ERROR_BAD_EXE_FORMAT).
    
    This function automatically copies the real compiled opencode.exe into %APPDATA%/npm/
    and neutralizes conflicting shims so Herdr agent start succeeds instantly.
    """
    if sys.platform != "win32":
        return

    appdata = os.environ.get("APPDATA")
    if not appdata:
        return

    npm_dir = Path(appdata) / "npm"
    if not npm_dir.exists():
        return

    # 1. Resolve and install real opencode.exe
    opencode_real_exe = npm_dir / "node_modules" / "opencode-ai" / "bin" / "opencode.exe"
    target_exe = npm_dir / "opencode.exe"

    if opencode_real_exe.exists():
        try:
            if not target_exe.exists() or target_exe.stat().st_size != opencode_real_exe.stat().st_size:
                shutil.copy2(str(opencode_real_exe), str(target_exe))
                logger.info(f"Auto-healed opencode.exe into {target_exe}")
        except Exception as e:
            logger.debug(f"Could not copy opencode.exe: {e}")

    # 2. Neutralize conflicting non-PE shims in %APPDATA%/npm
    conflicting_shims = [
        npm_dir / "opencode",       # Extensionless Unix shell script
        npm_dir / "opencode.ps1",   # PowerShell wrapper prioritized over .exe by Start-Process
    ]
    for shim in conflicting_shims:
        if shim.exists():
            try:
                bak_file = shim.with_name(f"{shim.name}.bak")
                if not bak_file.exists():
                    shim.rename(bak_file)
                else:
                    shim.unlink()
                logger.info(f"Neutralized conflicting shim {shim.name}")
            except Exception as e:
                logger.debug(f"Could not neutralize shim {shim.name}: {e}")


class HerdrAdapter:
    """Core interface for controlling Herdr v0.8.0 daemon via CLI and JSON output."""

    def __init__(self, herdr_bin: Optional[str] = None):
        self.herdr_bin = herdr_bin or shutil.which("herdr") or "herdr"
        ensure_windows_agent_binaries()

    def _exec(self, args: List[str], timeout: Optional[int] = 30) -> Dict[str, Any]:
        """Executes a herdr command and parses its JSON output."""
        cmd = [self.herdr_bin] + args
        logger.debug(f"Executing Herdr command: {' '.join(cmd)}")
        try:
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding="utf-8"
            )
            if res.returncode != 0:
                logger.error(f"Herdr command failed (code {res.returncode}): {res.stderr}")
                return {
                    "success": False,
                    "exit_code": res.returncode,
                    "stderr": res.stderr.strip(),
                    "stdout": res.stdout.strip()
                }

            stdout_str = res.stdout.strip()
            if not stdout_str:
                return {"success": True, "raw_output": ""}

            try:
                parsed = json.loads(stdout_str)
                return {"success": True, "result": parsed}
            except json.JSONDecodeError:
                return {"success": True, "raw_output": stdout_str}

        except subprocess.TimeoutExpired:
            logger.error(f"Herdr command timed out after {timeout}s: {' '.join(cmd)}")
            return {"success": False, "error": "timeout", "timeout_sec": timeout}
        except Exception as e:
            logger.error(f"Exception executing Herdr command: {str(e)}")
            return {"success": False, "error": str(e)}

    # --- 1. LAYOUT PRIMITIVES ---

    def create_workspace(self, cwd: str, label: str = "mloop-worker", no_focus: bool = True) -> Dict[str, Any]:
        """
        Creates a workspace. Returns JSON containing .result.workspace, .result.tab, .result.root_pane.
        """
        args = ["workspace", "create", "--cwd", cwd, "--label", label]
        if no_focus:
            args.append("--no-focus")
        res = self._exec(args)
        if res.get("success") and isinstance(res.get("result"), dict):
            data = res["result"]
            root_pane = data.get("result", {}).get("root_pane", {}).get("pane_id") or data.get("root_pane", {}).get("pane_id")
            res["root_pane_id"] = root_pane
        return res

    def split_pane(self, target_pane_id: str, direction: str = "right", no_focus: bool = True) -> Dict[str, Any]:
        """
        Splits an existing pane in the specified direction ('right' or 'down').
        Returns JSON containing .result.pane.pane_id.
        """
        args = ["pane", "split", target_pane_id, "--direction", direction]
        if no_focus:
            args.append("--no-focus")
        res = self._exec(args)
        if res.get("success") and isinstance(res.get("result"), dict):
            data = res["result"]
            new_pane = data.get("result", {}).get("pane", {}).get("pane_id") or data.get("pane", {}).get("pane_id")
            res["new_pane_id"] = new_pane
        return res

    def close_pane(self, pane_id: str) -> Dict[str, Any]:
        """Closes a Herdr terminal pane."""
        return self._exec(["pane", "close", pane_id])

    # --- 2. PANE PRIMITIVES ---

    def run_pane_command(self, pane_id: str, command_text: str) -> Dict[str, Any]:
        """Runs a raw shell command inside a terminal pane."""
        return self._exec(["pane", "run", pane_id, command_text])

    def wait_pane_output(self, pane_id: str, regex: str, timeout_ms: int = 120000) -> Dict[str, Any]:
        """Waits for specific regex output in a pane's rendered terminal rows."""
        timeout_sec = max(5, timeout_ms // 1000)
        return self._exec(
            ["pane", "wait-output", pane_id, "--regex", regex, "--timeout", str(timeout_ms)],
            timeout=timeout_sec + 5
        )

    def capture_pane_logs(self, pane_id: str, lines: int = 100) -> Dict[str, Any]:
        """Captures recent lines of log output from a pane."""
        return self._exec(["pane", "capture", "-p", pane_id, "--lines", str(lines)])

    # --- 3. AGENT PRIMITIVES ---

    def start_agent(
        self,
        agent_name: str,
        kind: str,
        pane_id: str,
        extra_args: Optional[List[str]] = None,
        timeout_ms: int = 30000
    ) -> Dict[str, Any]:
        """
        Launches a recognized coding agent (claude, opencode, codex, gemini, etc.) in an existing pane.
        """
        args = [
            "agent", "start", agent_name,
            "--kind", kind,
            "--pane", pane_id,
            "--timeout", str(timeout_ms)
        ]
        if extra_args:
            args.append("--")
            args.extend(extra_args)

        timeout_sec = max(10, timeout_ms // 1000 + 5)
        res = self._exec(args, timeout=timeout_sec)

        # Sur Windows, si opencode est un script .cmd/.ps1, herdr agent start échoue avec
        # "Start-Process : %1 n'est pas une application Win32 valide". On effectue un fallback via pane run.
        if not res.get("success"):
            # Résoudre le chemin absolu vers le .exe réel pour éviter que Windows résolve opencode.cmd
            resolved_bin = kind
            if sys.platform == "win32" and kind == "opencode":
                appdata = os.environ.get("APPDATA", "")
                exe_candidate = Path(appdata) / "npm" / "opencode.exe"
                if exe_candidate.exists():
                    resolved_bin = str(exe_candidate)
                    logger.info(f"Windows fallback: résolution vers exe absolu '{resolved_bin}'")
                else:
                    # Dernier recours : shutil.which avec extension forcée
                    found = shutil.which("opencode.exe") or shutil.which("opencode")
                    if found and found.endswith(".exe"):
                        resolved_bin = found

            cmd_str = f'& "{resolved_bin}" {" ".join(extra_args or [])}'.strip() if sys.platform == "win32" else f"{resolved_bin} {' '.join(extra_args or [])}".strip()
            logger.info(f"Fallback vers pane run: '{cmd_str}' sur le volet {pane_id}")
            self.run_pane_command(pane_id, cmd_str)
            try:
                self._exec(["agent", "rename", pane_id, agent_name])
            except Exception:
                pass
            return {"success": True, "fallback": "pane_run", "pane_id": pane_id, "agent_name": agent_name}

        return res

    def prompt_agent(
        self,
        agent_name_or_pane: str,
        prompt_text: str,
        wait: bool = True,
        timeout_ms: int = 300000
    ) -> Dict[str, Any]:
        """
        Submits a prompt to a running agent and optionally waits for completion.
        """
        args = ["agent", "prompt", agent_name_or_pane, prompt_text]
        if wait:
            args.append("--wait")
            args.extend(["--timeout", str(timeout_ms)])

        timeout_sec = max(10, timeout_ms // 1000 + 10) if wait else 15
        return self._exec(args, timeout=timeout_sec)

    def wait_agent(
        self,
        agent_name_or_pane: str,
        until_states: Optional[List[str]] = None,
        timeout_ms: int = 300000
    ) -> Dict[str, Any]:
        """
        Waits for an agent to reach specific lifecycle states (working, blocked, idle, done, unknown).
        """
        args = ["agent", "wait", agent_name_or_pane]
        states = until_states or ["idle", "done", "blocked"]
        for s in states:
            args.extend(["--until", s])
        args.extend(["--timeout", str(timeout_ms)])

        timeout_sec = max(10, timeout_ms // 1000 + 10)
        return self._exec(args, timeout=timeout_sec)

    def read_agent_output(
        self,
        agent_name_or_pane: str,
        lines: int = 120,
        source: str = "recent-unwrapped"
    ) -> Dict[str, Any]:
        """
        Reads terminal output from an agent, using alternate-screen scrolling when required
        (ideal for full-screen CLI agents like Claude Code or OpenCode).
        """
        return self._exec([
            "agent", "read", agent_name_or_pane,
            "--source", source,
            "--lines", str(lines)
        ])

    # --- 4. HIGH-LEVEL WORKER & CONTEXT ISOLATION PRIMITIVES ---

    @staticmethod
    def filter_terminal_bloat(raw_text: str) -> str:
        """
        Filters ANSI escape sequences, spinner artifacts, and noisy progress bars
        to yield clean, deterministic execution logs (Anti-Bloat / Pruning).
        """
        if not raw_text:
            return ""
        # Remove ANSI escape sequences
        ansi_regex = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        cleaned = ansi_regex.sub('', raw_text)
        # Remove carriage return artifacts
        cleaned = cleaned.replace('\r\n', '\n').replace('\r', '\n')
        # Filter repetitive spinner or loading lines
        spinners = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏", "◐", "◓", "◑", "◒"]
        lines = []
        for line in cleaned.splitlines():
            line_str = line.strip()
            if not line_str:
                continue
            # Skip lines starting with spinner glyphs or pure loading tokens
            if any(line_str.startswith(s) for s in spinners):
                continue
            if line_str in ["Loading...", "Working...", "Compiling..."]:
                continue
            lines.append(line)
        return "\n".join(lines)

    def list_agents(self) -> Dict[str, Any]:
        """Lists all registered Herdr agents and their statuses."""
        return self._exec(["agent", "list"])

    TASK_MODEL_MAP = {
        "deepening": "nmedia_cloud/claude-opus-4.8",
        "validation": "nmedia_cloud/gpt-5.6-terra-thinking",
        "deepsearch": "nmedia_cloud/claude-sonnet-5",
        "build": "nmedia_cloud/claude-sonnet-4.6",
        "compaction": "nmedia_cloud/gemini-3.5-flash-lite",
    }

    def spawn_story_worker(
        self,
        project_name: str,
        story_id: str,
        kind: str = "opencode",
        model: Optional[str] = None,
        task_type: Optional[str] = None,
        root_dir: Optional[str] = None,
        extra_args: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Spawns a clean-slate worker pane dedicated to a specific User Story.
        Ensures strict context isolation, selects the best LiteLLM model for the mission,
        and passes a focused, minimal instruction pointer.
        """
        cwd = root_dir or os.getcwd()
        clean_id = re.sub(r'[^a-zA-Z0-9_]', '_', story_id).lower()
        worker_name = f"worker_{clean_id}"[:32]
        logger.info(f"Spawning Herdr story worker '{worker_name}' for project '{project_name}'...")

        # 1. Resolve optimal model based on task_type or explicit override
        target_model = model or (self.TASK_MODEL_MAP.get(task_type.lower()) if task_type else None)

        # 2. Guardrail: redirect unauthenticated standalone Claude Code to OpenCode + Claude on LiteLLM
        if kind == "claude":
            logger.warning("Standalone Claude Code is not authenticated for enterprise proxy. Redirecting to OpenCode with Claude on LiteLLM.")
            kind = "opencode"
            if not target_model:
                target_model = "nmedia_cloud/claude-opus-4.8"

        # 3. Create a workspace or split pane
        split_res = self._exec(["pane", "split", "--direction", "right", "--no-focus"])
        pane_id = None
        if split_res.get("success"):
            data = split_res.get("result", {})
            pane_id = data.get("result", {}).get("pane", {}).get("pane_id") or data.get("pane", {}).get("pane_id")

        if not pane_id:
            # Fallback to workspace create
            ws_res = self.create_workspace(cwd=cwd, label=f"mloop-{story_id}", no_focus=True)
            pane_id = ws_res.get("root_pane_id")

        if not pane_id:
            pane_id = "p_fallback_1"
            logger.warning(f"Could not retrieve pane_id from Herdr, using fallback '{pane_id}'")

        # 4. Configure agent flags with resolved model
        flags = list(extra_args) if extra_args else (["--yolo"] if kind == "opencode" else ["--dangerously-skip-permissions"])
        if target_model:
            if kind == "opencode" and "--model" not in flags and "-m" not in flags:
                flags.extend(["--model", target_model])
            elif kind in ["pi", "omp"] and "--model" not in flags:
                flags.extend(["--model", target_model])

        start_res = self.start_agent(
            agent_name=worker_name,
            kind=kind,
            pane_id=str(pane_id),
            extra_args=flags
        )

        # 5. Délai d'initialisation — attendre que OpenCode soit idle/ready
        # avant d'envoyer le prompt (Fix: prompt perdu si envoyé trop tôt)
        import time
        time.sleep(3)  # Délai fixe minimal pour laisser OpenCode démarrer son UI
        # Tentative de wait_agent pour confirmer l'état idle (non-bloquant si timeout)
        try:
            self.wait_agent(worker_name, until_states=["idle", "done", "blocked"], timeout_ms=5000)
        except Exception:
            logger.debug(f"wait_agent timeout pour '{worker_name}' — envoi du prompt quand même.")

        # 6. Formulate enriched self-contained prompt (Fix: worker clean-slate sans contexte projet)
        clean_target = str(story_id).replace("\\", "/").replace("Projects/", "").replace(f"{project_name}/", "")
        if clean_target.startswith("backlog/stories/"):
            clean_target = clean_target[len("backlog/stories/"):]
        elif clean_target.startswith("backlog/"):
            clean_target = clean_target[len("backlog/"):]
        if clean_target.endswith(".md"):
            clean_target = clean_target[:-3]
        
        if clean_target in ["sprint_backlog", "backlog"]:
            story_file_rel = f"Projects/{project_name}/backlog/sprint_backlog.md"
        else:
            story_file_rel = f"Projects/{project_name}/backlog/stories/{clean_target}.md"

        task_label = (task_type or "build").upper()
        prompt_text = (
            f"## Mission Worker mLoop — {clean_target} [{task_label}]\n\n"
            f"**Projet** : {project_name}\n"
            f"**Récit cible** : `{story_file_rel}`\n"
            f"**Répertoire de travail** : `{cwd}`\n\n"
            f"### Contexte de démarrage\n"
            f"Tu es un agent Worker isolé (session vierge). Tu n'as aucun contexte projet préchargé.\n"
            f"Ta première action OBLIGATOIRE est :\n"
            f"1. `python src/swarm.py resume --project {project_name}` — restaure l'état\n"
            f"2. Lire le fichier `{story_file_rel}` pour comprendre la tâche\n"
            f"3. Exécuter la mission de type '{task_label}' décrite dans ce fichier\n\n"
            f"### Règles strictes\n"
            f"- Respecte le gabarit Gold Standard (story_template.md) et les 4 Piliers Gherkin\n"
            f"- Arrêt STRICT de la story après '## Scénarios de test' (ZÉRO section de traçabilité, ZÉRO note IA dans le .md)\n"
            f"- La traçabilité réside exclusivement dans `memory/evidence/<STORY_ID>_evidence.json`\n"
            f"- Écris tes livrables uniquement sous `Projects/{project_name}/`\n"
            f"- Termine par `python src/swarm.py sync --project {project_name}` pour persister\n"
            f"- En cas de doute ou blocage, écris une note dans "
            f"`Projects/{project_name}/memory/worker_{story_id}_notes.md` et arrête-toi\n"
        )

        prompt_res = self.prompt_agent(worker_name, prompt_text, wait=False)

        return {
            "success": True,
            "worker_name": worker_name,
            "pane_id": pane_id,
            "story_id": story_id,
            "project": project_name,
            "kind": kind,
            "model": target_model,
            "task_type": task_type,
            "start_result": start_res,
            "prompt_result": prompt_res
        }

    def harvest_story_evidence(
        self,
        project_name: str,
        story_id: str,
        project_path: Optional[str] = None,
        lines: int = 150
    ) -> Dict[str, Any]:
        """
        Extracts execution logs from the worker's PTY, filters terminal bloat,
        and saves the harvested evidence into memory/evidence/<STORY_ID>_evidence.json.
        """
        clean_id = re.sub(r'[^a-zA-Z0-9_]', '_', story_id).lower()
        worker_name = f"worker_{clean_id}"[:32]
        read_res = self.read_agent_output(worker_name, lines=lines, source="recent-unwrapped")
        raw_output = read_res.get("raw_output") or ""
        if isinstance(read_res.get("result"), dict):
            raw_output = read_res["result"].get("content") or raw_output

        cleaned_output = self.filter_terminal_bloat(raw_output)

        # Update evidence file if project path available
        proj_dir = Path(project_path) if project_path else Path.cwd() / "Projects" / project_name
        if not proj_dir.exists() and (Path.cwd() / "backlog").exists():
            proj_dir = Path.cwd()

        evidence_dir = proj_dir / "memory" / "evidence"
        evidence_dir.mkdir(parents=True, exist_ok=True)
        evidence_file = evidence_dir / f"{story_id}_evidence.json"

        existing_data = {}
        if evidence_file.exists():
            try:
                existing_data = json.loads(evidence_file.read_text(encoding="utf-8"))
            except Exception:
                existing_data = {}

        existing_data["story_id"] = story_id
        existing_data["herdr_worker"] = worker_name
        existing_data["execution_summary"] = cleaned_output[-2000:] if len(cleaned_output) > 2000 else cleaned_output
        existing_data["harvest_status"] = "COMPLETED"

        evidence_file.write_text(json.dumps(existing_data, indent=2, ensure_ascii=False), encoding="utf-8")

        return {
            "success": True,
            "story_id": story_id,
            "worker_name": worker_name,
            "evidence_file": str(evidence_file),
            "cleaned_lines": len(cleaned_output.splitlines()),
            "summary_preview": existing_data["execution_summary"][:300]
        }

    def cleanup_worker(self, story_id_or_pane: str) -> Dict[str, Any]:
        """Closes a worker pane and cleans up its resources."""
        pane_id = story_id_or_pane
        if ":" not in pane_id:
            agents_res = self.list_agents()
            if agents_res.get("success"):
                agents_data = agents_res.get("result", {})
                inner = agents_data.get("result", {}) if isinstance(agents_data, dict) else {}
                agents_list = inner.get("agents", []) if isinstance(inner, dict) else []
                if not agents_list and isinstance(agents_data, dict):
                    agents_list = agents_data.get("agents", [])
                clean_target = re.sub(r'[^a-zA-Z0-9_]', '_', story_id_or_pane).lower()
                for ag in agents_list:
                    ag_name = (ag.get("name") or "").lower()
                    if ag_name == clean_target or clean_target in ag_name or f"worker_{clean_target}" in ag_name:
                        target_pane = ag.get("pane_id")
                        if target_pane:
                            pane_id = target_pane
                            break
        return self.close_pane(pane_id)


# Singleton instance helper
herdr = HerdrAdapter()

