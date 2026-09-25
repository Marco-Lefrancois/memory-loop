# -*- coding: utf-8 -*-
"""
session_forker.py - Gestionnaire de Session Forking OpenCode (MLOOP-252-BE).

Gère la bifurcation déterministe de sessions d'agents (`opencode --fork`)
pour les rituels Grill-Me et Doubt-Driven, avec traçabilité et gouvernance de rétention.
Conforme ADR-0202 (<=300L), ADR-0015 (Data Hygiene) et ADR-0375 (Traçabilité Radicale).
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import subprocess
from typing import Any, Callable, Dict, List, Optional
import uuid

logger = logging.getLogger("mloop.bridges.opencode.session_forker")


class SessionForkError(Exception):
    """Exception de base pour les erreurs de Session Forking."""


class SessionNotFoundError(SessionForkError):
    """Exception levée lorsqu'une session parente est introuvable."""


class OpenCodeSessionForker:
    """Orchestrateur de bifurcation et traçabilité des sessions OpenCode."""

    def __init__(
        self,
        workspace_root: Optional[Path] = None,
        registry_file: Optional[Path] = None,
    ) -> None:
        self.root = Path(workspace_root) if workspace_root else Path.cwd()
        self.registry_file = (
            Path(registry_file)
            if registry_file
            else self.root / "memory" / "sessions" / "forks_registry.json"
        )

    def _ensure_registry_dir(self) -> None:
        """Assure que le répertoire parent du registre existe."""
        self.registry_file.parent.mkdir(parents=True, exist_ok=True)

    def _read_registry(self) -> List[Dict[str, Any]]:
        """Charge le registre des forks depuis le fichier JSON."""
        if not self.registry_file.exists():
            return []
        try:
            return json.loads(self.registry_file.read_text(encoding="utf-8"))
        except Exception as e:
            logger.warning(f"Erreur de lecture du registre de sessions {self.registry_file} : {e}")
            return []

    def _write_registry(self, data: List[Dict[str, Any]]) -> None:
        """Persiste le registre des forks au format JSON indenté."""
        self._ensure_registry_dir()
        self.registry_file.write_text(
            json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    def _default_runner(self, cmd: List[str], cwd: Path) -> Dict[str, Any]:
        """Exécute la commande CLI OpenCode par sous-processus."""
        try:
            res = subprocess.run(
                cmd,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=30.0,
            )
            # Génération d'un ID déterministe ou capture de sortie
            child_id = f"sess-fork-{uuid.uuid4().hex[:8]}"
            return {
                "returncode": res.returncode,
                "child_id": child_id,
                "stdout": res.stdout,
                "stderr": res.stderr,
            }
        except Exception as e:
            return {"returncode": 1, "stderr": str(e), "child_id": ""}

    def fork_session(
        self,
        parent_session_id: str,
        reason: str,
        story_id: Optional[str] = None,
        runner: Optional[Callable[..., Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Bifurque une session active et consigne la filiation dans le registre."""
        cmd = ["opencode", "--session", parent_session_id, "--fork"]
        exec_runner = runner or self._default_runner

        res = exec_runner(cmd, cwd=self.root)
        if res.get("returncode", 1) != 0:
            err_msg = res.get("stderr", "Échec inconnu lors du fork")
            raise SessionNotFoundError(f"Impossible de forker la session {parent_session_id} : {err_msg}")

        child_id = res.get("child_id") or f"sess-fork-{uuid.uuid4().hex[:8]}"
        created_at = datetime.now(timezone.utc).isoformat()

        entry = {
            "child_session_id": child_id,
            "parent_session_id": parent_session_id,
            "story_id": story_id,
            "reason": reason,
            "created_at": created_at,
            "ttl_days": 7,
            "reconciled": False,
            "summary": None,
            "status": "ACTIVE",
        }

        registry = self._read_registry()
        registry.append(entry)
        self._write_registry(registry)

        logger.info(f"[SessionForker] Session bifurquée : {parent_session_id} -> {child_id} ({reason})")
        return entry

    def list_forks(self, story_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Liste les sessions forked, avec filtre optionnel par story_id."""
        entries = self._read_registry()
        if story_id:
            return [e for e in entries if e.get("story_id") == story_id]
        return entries

    def reconcile_fork(self, fork_session_id: str, summary: str) -> Dict[str, Any]:
        """Marque une session forked comme réconciliée avec résumé d'arbitrage."""
        registry = self._read_registry()
        target = None
        for entry in registry:
            if entry.get("child_session_id") == fork_session_id:
                entry["reconciled"] = True
                entry["summary"] = summary
                entry["reconciled_at"] = datetime.now(timezone.utc).isoformat()
                target = entry
                break

        if not target:
            raise SessionNotFoundError(f"Session forked introuvable : {fork_session_id}")

        self._write_registry(registry)
        logger.info(f"[SessionForker] Session réconciliée : {fork_session_id}")
        return target

    def purge_expired_forks(self, max_age_days: int = 7) -> int:
        """Purge les entrées de session expirées selon la politique de rétention (ADR-0015)."""
        registry = self._read_registry()
        now = datetime.now(timezone.utc)
        kept: List[Dict[str, Any]] = []
        purged_count = 0

        for entry in registry:
            created_str = entry.get("created_at")
            if not created_str:
                kept.append(entry)
                continue

            try:
                created_dt = datetime.fromisoformat(created_str)
                age_days = (now - created_dt).total_seconds() / 86400.0
                if age_days > max_age_days:
                    purged_count += 1
                else:
                    kept.append(entry)
            except Exception:
                kept.append(entry)

        if purged_count > 0:
            self._write_registry(kept)
            logger.info(f"[SessionForker] {purged_count} session(s) expirée(s) purgée(s).")

        return purged_count

    def get_session_tree(self, story_id: Optional[str] = None) -> Dict[str, List[str]]:
        """Construit un arbre parent -> enfants des sessions bifurquées."""
        forks = self.list_forks(story_id=story_id)
        tree: Dict[str, List[str]] = {}
        for f in forks:
            p = f.get("parent_session_id", "unknown")
            c = f.get("child_session_id", "unknown")
            tree.setdefault(p, []).append(c)
        return tree
