"""
Pont MCP Léger pour OpenViking Context Database (ADR-0335).
Permet aux agents mLoop d'interroger et de naviguer dans les bases de contexte OpenViking (viking://).
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional


class OpenVikingBridgeClient:
    """Client HTTP léger pour interagir avec une instance OpenViking locale ou distante."""

    def __init__(self, endpoint_url: Optional[str] = None, api_key: Optional[str] = None):
        self.endpoint_url = (endpoint_url or os.getenv("OPENVIKING_API_URL", "http://127.0.0.1:18383")).rstrip("/")
        self.api_key = api_key or os.getenv("OPENVIKING_API_KEY", "")

    def _request(self, path: str, method: str = "GET", payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = f"{self.endpoint_url}/{path.lstrip('/')}"
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        data = json.dumps(payload).encode("utf-8") if payload else None
        req = urllib.request.Request(url, data=data, headers=headers, method=method)

        try:
            with urllib.request.urlopen(req, timeout=5) as response:
                body = response.read().decode("utf-8")
                return json.loads(body) if body else {}
        except urllib.error.URLError as e:
            return {
                "error": True,
                "status": "UNAVAILABLE",
                "message": f"Serveur OpenViking non accessible à {self.endpoint_url} ({e.reason})"
            }
        except Exception as e:
            return {
                "error": True,
                "status": "ERROR",
                "message": f"Erreur lors de la requête OpenViking : {e}"
            }

    def status(self) -> Dict[str, Any]:
        """Vérifie l'état de santé du serveur OpenViking."""
        return self._request("api/v1/health")

    def find(self, query: str, target_uri: str = "viking://resources/") -> Dict[str, Any]:
        """Recherche sémantique ciblée dans une arborescence viking://."""
        return self._request("api/v1/context/find", method="POST", payload={
            "query": query,
            "target_uri": target_uri
        })

    def tree(self, uri: str = "viking://resources/", depth: int = 2) -> Dict[str, Any]:
        """Affiche l'arborescence des répertoires et ressources."""
        return self._request("api/v1/context/tree", method="POST", payload={
            "uri": uri,
            "depth": depth
        })

    def overview(self, uri: str) -> Dict[str, Any]:
        """Récupère la vue d'ensemble L1 d'un répertoire."""
        return self._request("api/v1/context/overview", method="POST", payload={"uri": uri})

    def abstract(self, uri: str) -> Dict[str, Any]:
        """Récupère le résumé L0 d'un répertoire."""
        return self._request("api/v1/context/abstract", method="POST", payload={"uri": uri})

    def read(self, uri: str) -> Dict[str, Any]:
        """Lit le contenu L2 intégral d'une ressource."""
        return self._request("api/v1/context/read", method="POST", payload={"uri": uri})


def handle_initialize(req_id: Any) -> Dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "result": {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {"listChanged": True}
            },
            "serverInfo": {
                "name": "mloop-openviking-bridge-mcp",
                "version": "1.0.0"
            }
        },
        "id": req_id
    }


def handle_tools_list(req_id: Any) -> Dict[str, Any]:
    tools = [
        {
            "name": "openviking_status",
            "description": "Vérifie si le serveur OpenViking Context Database est actif et joignable.",
            "inputSchema": {"type": "object", "properties": {}}
        },
        {
            "name": "openviking_find",
            "description": "Recherche sémantique d'un contexte dans OpenViking sous viking://.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Terme ou intention de recherche."},
                    "target_uri": {"type": "string", "description": "URI racine viking:// (ex: viking://resources/)."}
                },
                "required": ["query"]
            }
        },
        {
            "name": "openviking_tree",
            "description": "Affiche l'arborescence hiérarchique d'une URI viking://.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "uri": {"type": "string", "description": "URI cible (ex: viking://resources/)."},
                    "depth": {"type": "integer", "description": "Profondeur maximale (défaut: 2)."}
                }
            }
        },
        {
            "name": "openviking_overview",
            "description": "Lit la vue d'ensemble L1 (.overview.md) d'un dossier sous viking://.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "uri": {"type": "string", "description": "URI du dossier viking://."}
                },
                "required": ["uri"]
            }
        },
        {
            "name": "openviking_read",
            "description": "Lit le contenu L2 complet d'un fichier sous viking://.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "uri": {"type": "string", "description": "URI complète du fichier viking://."}
                },
                "required": ["uri"]
            }
        }
    ]
    return {
        "jsonrpc": "2.0",
        "result": {"tools": tools},
        "id": req_id
    }


def handle_tools_call(req_id: Any, params: Dict[str, Any]) -> Dict[str, Any]:
    name = params.get("name")
    args = params.get("arguments", {})
    client = OpenVikingBridgeClient()

    if name == "openviking_status":
        res = client.status()
        text = json.dumps(res, indent=2, ensure_ascii=False)
    elif name == "openviking_find":
        res = client.find(query=args.get("query", ""), target_uri=args.get("target_uri", "viking://resources/"))
        text = json.dumps(res, indent=2, ensure_ascii=False)
    elif name == "openviking_tree":
        res = client.tree(uri=args.get("uri", "viking://resources/"), depth=args.get("depth", 2))
        text = json.dumps(res, indent=2, ensure_ascii=False)
    elif name == "openviking_overview":
        res = client.overview(uri=args.get("uri", ""))
        text = json.dumps(res, indent=2, ensure_ascii=False)
    elif name == "openviking_read":
        res = client.read(uri=args.get("uri", ""))
        text = json.dumps(res, indent=2, ensure_ascii=False)
    else:
        text = f"Outil inconnu : {name}"

    return {
        "jsonrpc": "2.0",
        "result": {
            "content": [{"type": "text", "text": text}]
        },
        "id": req_id
    }


def main():
    """Boucle standard JSON-RPC stdio pour serveur MCP."""
    for line in sys.stdin:
        line_str = line.strip()
        if not line_str:
            continue
        try:
            req = json.loads(line_str)
            method = req.get("method")
            req_id = req.get("id")

            if method == "initialize":
                resp = handle_initialize(req_id)
            elif method == "tools/list":
                resp = handle_tools_list(req_id)
            elif method == "tools/call":
                resp = handle_tools_call(req_id, req.get("params", {}))
            else:
                resp = {
                    "jsonrpc": "2.0",
                    "error": {"code": -32601, "message": f"Method not found: {method}"},
                    "id": req_id
                }

            sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
            sys.stdout.flush()
        except Exception as e:
            err_resp = {
                "jsonrpc": "2.0",
                "error": {"code": -32603, "message": f"Internal error: {e}"},
                "id": None
            }
            sys.stdout.write(json.dumps(err_resp) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
