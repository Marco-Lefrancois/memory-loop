"""
mLoop App-Server Daemon.
Inspiré du codex-app-server d'OpenAI Codex.

Fournit une interface JSON-RPC 2.0 asynchrone (sur stdio ou socket)
pour orchestrer les sessions mLoop, piloter les turns et émettre des notifications d'événements.
"""

import sys
import json
import uuid
import time
from typing import Dict, Any, Optional, List


class AppServerProtocol:
    """
    Gestionnaire du protocole JSON-RPC 2.0 pour mLoop.
    """

    def __init__(self):
        self.threads: Dict[str, Dict[str, Any]] = {}
        self.active_turns: Dict[str, Dict[str, Any]] = {}

    def handle_request(self, request_json: str) -> str:
        try:
            req = json.loads(request_json)
        except Exception as e:
            return json.dumps({"error": {"code": -32700, "message": f"Parse error: {e}"}, "id": None})

        req_id = req.get("id")
        method = req.get("method")
        params = req.get("params", {})

        try:
            result = self._dispatch(method, params)
            return json.dumps({"result": result, "id": req_id})
        except Exception as e:
            return json.dumps({"error": {"code": -32603, "message": str(e)}, "id": req_id})

    def _dispatch(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if method == "initialize":
            return {
                "serverInfo": {"name": "mloop_app_server", "version": "1.0.0"},
                "capabilities": {"threads": True, "turns": True, "guardian": True, "hooks": True}
            }

        elif method == "thread/start":
            thread_id = f"mloop-th-{uuid.uuid4().hex[:8]}"
            project = params.get("project", "default")
            self.threads[thread_id] = {
                "id": thread_id,
                "project": project,
                "created_at": time.time(),
                "status": "idle"
            }
            return {"threadId": thread_id, "project": project, "status": "idle"}

        elif method == "turn/start":
            thread_id = params.get("threadId")
            if thread_id not in self.threads:
                raise ValueError(f"Thread '{thread_id}' introuvable.")
            
            turn_id = f"turn-{uuid.uuid4().hex[:6]}"
            user_input = params.get("input", "")
            
            turn_data = {
                "turnId": turn_id,
                "threadId": thread_id,
                "input": user_input,
                "status": "completed",
                "completed_at": time.time()
            }
            self.active_turns[turn_id] = turn_data
            return turn_data

        elif method == "guardian/status":
            from src.engine.guardian import GuardianAutoReviewer
            reviewer = GuardianAutoReviewer()
            return {
                "consecutive_denials": reviewer.circuit_breaker.consecutive_denials,
                "rolling_denials_count": len([d for d in reviewer.circuit_breaker.denials_history if d]),
                "audit_log_size": len(reviewer.audit_log)
            }

        elif method == "roles/list":
            from pathlib import Path
            try:
                import tomllib
            except ImportError:
                import toml as tomllib
            agents_dir = Path("standards/agents")
            roles = []
            if agents_dir.exists():
                for f in agents_dir.glob("*.toml"):
                    try:
                        data = tomllib.loads(f.read_text(encoding="utf-8"))
                        roles.append(data)
                    except Exception:
                        pass
            return {"roles": roles}

        else:
            raise ValueError(f"Méthode JSON-RPC '{method}' non supportée.")

    def run_stdio(self):
        """Boucle de lecture stdin / stdout pour le mode daemon stdio."""
        for line in sys.stdin:
            line_str = line.strip()
            if not line_str:
                continue
            response_str = self.handle_request(line_str)
            sys.stdout.write(response_str + "\n")
            sys.stdout.flush()
