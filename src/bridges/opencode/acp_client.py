# -*- coding: utf-8 -*-
"""
acp_client.py - Adaptateur Client pour l'Agent Client Protocol (ACP) OpenCode (MLOOP-253-BE).

Implémente le dialogue JSON-RPC 2.0 typé sur flux standard avec opencode acp.
Gère le handshake des capacités, l'auto-approbation confinée et les timeouts adaptatifs.
Conforme ADR-0202 (<=300L), ADR-0377 (Runtimes Aval) et ADR-0369.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
import subprocess
from typing import Any, Dict, Optional

logger = logging.getLogger("mloop.bridges.opencode.acp_client")

SUPPORTED_PROTOCOL_VERSIONS = {"2024-11-05", "1.0", "1.1"}
DEFAULT_TIMEOUT_STANDARD = 180.0
DEFAULT_TIMEOUT_THINKING = 480.0


class AcpProtocolError(Exception):
    """Exception levée en cas de dysfonctionnement du protocole ACP."""


class AcpTimeoutError(AcpProtocolError):
    """Exception levée lors de l'expiration du délai de réponse ACP."""


class SubprocessAcpTransport:
    """Transport standard par sous-processus stdin/stdout pour 'opencode acp'."""

    def __init__(self, bin_path: str, cwd: Path) -> None:
        self.proc = subprocess.Popen(  # noqa: RULE-AST-03 (processus ACP stdio — durée de vie = session client)
            [bin_path, "acp"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=cwd,
            text=True,
            bufsize=1,
        )

    def send(self, message: Dict[str, Any], timeout: float = 30.0) -> Dict[str, Any]:
        """Émet un message JSON-RPC et attend la réponse."""
        if not self.proc.stdin or not self.proc.stdout:
            raise AcpProtocolError("Flux sous-processus non disponibles.")

        payload = json.dumps(message) + "\n"
        self.proc.stdin.write(payload)
        self.proc.stdin.flush()

        line = self.proc.stdout.readline()
        if not line:
            stderr = self.proc.stderr.read() if self.proc.stderr else ""
            raise AcpProtocolError(f"Le serveur ACP a fermé la connexion : {stderr}")

        return json.loads(line)

    def close(self) -> None:
        """Termine le sous-processus proprement."""
        if self.proc:
            try:
                self.proc.terminate()
                self.proc.wait(timeout=2.0)
            except Exception:
                self.proc.kill()


class OpenCodeAcpClient:
    """Client JSON-RPC de haut niveau pour l'Agent Client Protocol (ACP)."""

    def __init__(
        self,
        workspace_root: Optional[Path] = None,
        transport: Optional[Any] = None,
        bin_path: str = "opencode",
    ) -> None:
        self.root = Path(workspace_root).resolve() if workspace_root else Path.cwd().resolve()
        self.bin_path = bin_path
        self._transport = transport
        self._msg_id = 0
        self.is_initialized = False
        self.is_connected = False
        self.server_info: Dict[str, Any] = {}

    def _next_id(self) -> int:
        self._msg_id += 1
        return self._msg_id

    def _get_transport(self) -> Any:
        if self._transport is None:
            self._transport = SubprocessAcpTransport(self.bin_path, self.root)
            self.is_connected = True
        return self._transport

    def calculate_timeout(self, timeout: Optional[float] = None, thinking: bool = False) -> float:
        """Calcule le délai de garde selon le type de modèle (ADR-0377)."""
        if timeout is not None:
            return float(timeout)
        return DEFAULT_TIMEOUT_THINKING if thinking else DEFAULT_TIMEOUT_STANDARD

    def evaluate_permission_request(self, action: str, params: Dict[str, Any]) -> str:
        """Auto-approbation sécurisée confinée aux limites du workspace_root."""
        target_path_raw = params.get("path") or params.get("file")
        if not target_path_raw:
            return "allow" if action in {"terminal/read", "session/status"} else "deny"

        try:
            target_path = Path(target_path_raw).resolve()
            # Vérification du confinement : target_path doit être sous self.root
            target_path.relative_to(self.root)
            return "allow"
        except (ValueError, RuntimeError):
            logger.warning(f"[ACP Guard] Tentative d'accès hors workspace refusée : {target_path_raw}")
            return "deny"

    def initialize(self) -> Dict[str, Any]:
        """Exécute le handshake initial ACP et négocie les capacités."""
        transport = self._get_transport()
        req = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "clientInfo": {"name": "mloop-swarm", "version": "1.0.0"},
                "capabilities": {"workspaceBoundary": str(self.root)},
            },
        }

        resp = transport.send(req)
        if "error" in resp:
            raise AcpProtocolError(f"Erreur handshake ACP : {resp['error']}")

        res = resp.get("result", {})
        proto_ver = res.get("protocolVersion")
        if proto_ver not in SUPPORTED_PROTOCOL_VERSIONS:
            raise AcpProtocolError(f"Version ACP incompatible : reçu '{proto_ver}', supportées {SUPPORTED_PROTOCOL_VERSIONS}")

        self.server_info = res
        self.is_initialized = True
        self.is_connected = True
        logger.info(f"[ACP] Handshake réussi avec {res.get('serverInfo', {}).get('name')}")
        return res

    def create_session(self, model: Optional[str] = None) -> str:
        """Crée une nouvelle session d'agent via ACP."""
        if not self.is_initialized:
            self.initialize()

        transport = self._get_transport()
        req = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "session/create",
            "params": {
                "workspaceRoot": str(self.root),
                "model": model or "claude-3-5-sonnet",
            },
        }

        resp = transport.send(req)
        if "error" in resp:
            raise AcpProtocolError(f"Erreur création session ACP : {resp['error']}")

        sess_id = resp.get("result", {}).get("sessionId")
        if not sess_id:
            raise AcpProtocolError("Identifiant de session manquant dans la réponse ACP.")
        return sess_id

    def send_prompt(
        self,
        session_id: str,
        prompt: str,
        timeout: Optional[float] = None,
        thinking: bool = False,
    ) -> Dict[str, Any]:
        """Transmet une consigne au worker et attend la complétion du tour."""
        if not self.is_initialized:
            self.initialize()

        effective_timeout = self.calculate_timeout(timeout=timeout, thinking=thinking)
        transport = self._get_transport()

        req = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "session/prompt",
            "params": {"sessionId": session_id, "prompt": prompt, "timeout": effective_timeout},
        }

        resp = transport.send(req)
        if "error" in resp:
            raise AcpProtocolError(f"Erreur lors du prompt ACP : {resp['error']}")

        return resp.get("result", {})

    def close(self) -> None:
        """Ferme la session et termine le transport sous-jacent."""
        if self._transport and hasattr(self._transport, "close"):
            self._transport.close()
        self.is_connected = False
        self.is_initialized = False
