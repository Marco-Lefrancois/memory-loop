"""
herdr_core.py - CLI executor & Windows shim guardrail for HerdrAdapter.

Provides _exec (deterministic CLI→JSON bridge with ADR-0369 timeout
and context-manager-safe error handling) and ensure_windows_agent_binaries
(ADR-0325 auto-heal for npm shim conflicts on Windows).
"""

import json
import os
import shutil
import subprocess
import sys
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("mloop.herdr_core")


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

    opencode_real_exe = npm_dir / "node_modules" / "opencode-ai" / "bin" / "opencode.exe"
    target_exe = npm_dir / "opencode.exe"

    if opencode_real_exe.exists():
        try:
            if (
                not target_exe.exists()
                or target_exe.stat().st_size != opencode_real_exe.stat().st_size
            ):
                shutil.copy2(str(opencode_real_exe), str(target_exe))
                logger.info(f"Auto-healed opencode.exe into {target_exe}")
        except Exception as e:
            logger.debug(f"Could not copy opencode.exe: {e}")

    conflicting_shims = [
        npm_dir / "opencode",
        npm_dir / "opencode.ps1",
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


class HerdrCoreMixin:
    """CLI executor and Windows shim guardrail (ADR-0325 / ADR-0369)."""

    def __init__(self, herdr_bin: Optional[str] = None) -> None:
        self.herdr_bin = herdr_bin or shutil.which("herdr") or "herdr"
        ensure_windows_agent_binaries()

    def _exec(self, args: List[str], timeout: Optional[int] = 30) -> Dict[str, Any]:
        """Executes a herdr command and parses its JSON output.

        ADR-0369: timeout explicite obligatoire sur tout appel subprocess.
        """
        cmd = [self.herdr_bin] + args
        logger.debug(f"Executing Herdr command: {' '.join(cmd)}")
        try:
            res = subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout, encoding="utf-8"
            )
            if res.returncode != 0:
                logger.error(f"Herdr command failed (code {res.returncode}): {res.stderr}")
                return {
                    "success": False,
                    "exit_code": res.returncode,
                    "stderr": res.stderr.strip(),
                    "stdout": res.stdout.strip(),
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
            logger.error(
                f"Herdr command timed out after {timeout}s: {' '.join(cmd)}",
                exc_info=True,
                extra={"herdr_bin": self.herdr_bin, "cmd": " ".join(cmd), "timeout_sec": timeout},
            )
            return {"success": False, "error": "timeout", "timeout_sec": timeout}
        except Exception as e:
            logger.error(
                f"Exception executing Herdr command: {str(e)}",
                exc_info=True,
                extra={"herdr_bin": self.herdr_bin, "cmd": " ".join(cmd), "error": str(e)},
            )
            return {"success": False, "error": str(e)}
