# -*- coding: utf-8 -*-
"""
Tests unitaires pour MLOOP-253-BE : Adaptateur Protocolaire OpenCode ACP (JSON-RPC).
Conforme ADR-0202 (<=300L) et 4 Piliers Gherkin.
"""

from pathlib import Path
import pytest
from src.bridges.opencode.acp_client import (
    AcpProtocolError,
    AcpTimeoutError,
    OpenCodeAcpClient,
)


class MockAcpTransport:
    """Simulateur de transport JSON-RPC pour opencode acp."""

    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root
        self.responses = []
        self.sent_messages = []
        self.is_closed = False

    def send(self, message: dict) -> dict:
        self.sent_messages.append(message)
        method = message.get("method")
        msg_id = message.get("id")

        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "serverInfo": {"name": "opencode-acp", "version": "1.18.30"},
                    "capabilities": {"sessions": True, "streaming": True},
                },
            }
        elif method == "session/create":
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {"sessionId": "acp-sess-42"},
            }
        elif method == "session/prompt":
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "turnId": "turn-001",
                    "content": "Code implémenté avec succès.",
                    "status": "COMPLETED",
                },
            }
        return {"jsonrpc": "2.0", "id": msg_id, "error": {"code": -32601, "message": "Method not found"}}

    def close(self):
        self.is_closed = True


def test_handshake_nominal(tmp_path: Path):
    """Pilier 1 - Nominal : Handshake ACP v1 réussi."""
    transport = MockAcpTransport(workspace_root=tmp_path)
    client = OpenCodeAcpClient(workspace_root=tmp_path, transport=transport)

    info = client.initialize()
    assert info["protocolVersion"] == "2024-11-05"
    assert info["serverInfo"]["name"] == "opencode-acp"
    assert client.is_initialized is True


def test_session_creation_and_prompt(tmp_path: Path):
    """Pilier 1 - Nominal : Création de session et envoi de prompt."""
    transport = MockAcpTransport(workspace_root=tmp_path)
    client = OpenCodeAcpClient(workspace_root=tmp_path, transport=transport)
    client.initialize()

    sess_id = client.create_session()
    assert sess_id == "acp-sess-42"

    reply = client.send_prompt(sess_id, "Implémente la fonction fibonacci")
    assert reply["status"] == "COMPLETED"
    assert "Code implémenté" in reply["content"]


def test_permission_guard_workspace_boundary(tmp_path: Path):
    """Pilier 3 - Résilience : Confinement des permissions au workspace."""
    client = OpenCodeAcpClient(workspace_root=tmp_path)

    # Chemin intérieur au workspace -> autorisé
    inside_path = tmp_path / "src" / "code.py"
    perm_inside = client.evaluate_permission_request("fs/write", {"path": str(inside_path)})
    assert perm_inside == "allow"

    # Chemin extérieur -> refusé
    outside_path = Path("C:/Windows/System32/calc.exe")
    perm_outside = client.evaluate_permission_request("fs/write", {"path": str(outside_path)})
    assert perm_outside == "deny"


def test_adaptive_timeout_calculation():
    """Pilier 3 - Résilience : Calcul adaptatif des timeouts (thinking models)."""
    client = OpenCodeAcpClient(Path.cwd())

    # Standard
    assert client.calculate_timeout(thinking=False) == 180.0

    # Thinking model
    assert client.calculate_timeout(thinking=True) == 480.0

    # Custom override
    assert client.calculate_timeout(timeout=250.0) == 250.0


def test_incompatible_version_raises_protocol_error(tmp_path: Path):
    """Pilier 2 - Exception : Rejet d'une version de protocole incompatible."""

    class IncompatibleTransport(MockAcpTransport):
        def send(self, message: dict) -> dict:
            return {
                "jsonrpc": "2.0",
                "id": message.get("id"),
                "result": {"protocolVersion": "1999-01-01"},
            }

    client = OpenCodeAcpClient(workspace_root=tmp_path, transport=IncompatibleTransport(tmp_path))
    with pytest.raises(AcpProtocolError) as exc:
        client.initialize()
    assert "Version ACP incompatible" in str(exc.value)


def test_client_clean_disconnect(tmp_path: Path):
    """Pilier 4 - UX & Propreté : fermeture ordonnée du client."""
    transport = MockAcpTransport(workspace_root=tmp_path)
    client = OpenCodeAcpClient(workspace_root=tmp_path, transport=transport)
    client.initialize()

    client.close()
    assert transport.is_closed is True
    assert client.is_connected is False
