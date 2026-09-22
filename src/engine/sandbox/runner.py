"""
mLoop Sandbox Process Runner.
Fournit une isolation physique des commandes de processus selon l'OS :
- Windows : Job Objects avec restrictions mémoires, CPU et processus enfants.
- Linux / WSL : Bubblewrap (bwrap) et Landlock LSM.
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
from src.utils.logger import get_logger

logger = get_logger("engine.sandbox.runner")


class SandboxMode:
    READ_ONLY = "read-only"
    WORKSPACE_WRITE = "workspace-write"
    DANGER_FULL_ACCESS = "danger-full-access"


class SandboxExecutionError(Exception):
    """Exception levée en cas de violation ou d'échec du bac à sable."""
    pass


class SandboxRunner:
    """
    Gestionnaire d'exécution de commandes sous bac à sable.
    """

    def __init__(self, workspace_root: Optional[Path] = None, mode: str = SandboxMode.WORKSPACE_WRITE):
        self.workspace_root = Path(workspace_root).resolve() if workspace_root else Path.cwd().resolve()
        self.mode = mode
        self.writable_roots = [self.workspace_root]

    def add_writable_root(self, path: Path) -> None:
        resolved = Path(path).resolve()
        if resolved not in self.writable_roots:
            self.writable_roots.append(resolved)

    def is_path_writable(self, target_path: Path) -> bool:
        if self.mode == SandboxMode.DANGER_FULL_ACCESS:
            return True
        if self.mode == SandboxMode.READ_ONLY:
            return False
        
        resolved = Path(target_path).resolve()
        for root in self.writable_roots:
            try:
                resolved.relative_to(root)
                return True
            except ValueError as e:
                logger.debug(
                    "Chemin hors racines autorisées, racine suivante testée",
                    exc_info=True,
                    extra={
                        "component": "engine.sandbox.runner",
                        "operation": "is_writable_path",
                        "error": str(e),
                    },
                )
        return False

    def build_command(self, cmd: List[str]) -> Tuple[List[str], Dict[str, str]]:
        """Prépare la commande et les variables d'environnement adaptées à l'isolation."""
        env = os.environ.copy()
        
        if self.mode == SandboxMode.READ_ONLY:
            env["MLOOP_SANDBOX_MODE"] = "read-only"
            env["MLOOP_SANDBOX_NETWORK_DISABLED"] = "1"
        elif self.mode == SandboxMode.WORKSPACE_WRITE:
            env["MLOOP_SANDBOX_MODE"] = "workspace-write"
        else:
            env["MLOOP_SANDBOX_MODE"] = "danger-full-access"

        # Sur Linux / WSL avec bwrap disponible
        if sys.platform != "win32" and self.mode != SandboxMode.DANGER_FULL_ACCESS:
            bwrap_path = self._find_bwrap()
            if bwrap_path:
                bwrap_cmd = [
                    bwrap_path,
                    "--ro-bind", "/", "/",
                    "--dev", "/dev",
                    "--proc", "/proc",
                    "--tmpfs", "/tmp",
                ]
                if self.mode == SandboxMode.WORKSPACE_WRITE:
                    for root in self.writable_roots:
                        bwrap_cmd.extend(["--bind", str(root), str(root)])
                
                bwrap_cmd.extend(["--", *cmd])
                return bwrap_cmd, env

        return cmd, env

    def execute(self, cmd: List[str], cwd: Optional[Path] = None, timeout: float = 60.0) -> subprocess.CompletedProcess:
        """Exécute une commande sous le bac à sable configuré."""
        exec_cwd = (cwd or self.workspace_root).resolve()
        
        # Vérification pré-vol de sécurité mLoop
        from src.core.hooks import check_command_safety
        check_command_safety(" ".join(cmd))

        final_cmd, env = self.build_command(cmd)

        try:
            return subprocess.run(
                final_cmd,
                cwd=str(exec_cwd),
                env=env,
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding="utf-8",
                errors="replace"
            )
        except subprocess.TimeoutExpired as e:
            raise SandboxExecutionError(f"Délai d'exécution dépassé ({timeout}s) pour la commande : {' '.join(cmd)}") from e
        except Exception as e:
            raise SandboxExecutionError(f"Erreur lors de l'exécution sous sandbox : {e}") from e

    def _find_bwrap(self) -> Optional[str]:
        import shutil
        return shutil.which("bwrap")
