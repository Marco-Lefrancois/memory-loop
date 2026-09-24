"""
tools/drawdb/runner.py — Serveur DrawDB Souverain 100% Local (MLOOP-152-BE)

Point d'entrée CLI + gestionnaire HTTP. La logique est décomposée en sous-modules
pour respecter ADR-0202 (≤300 lignes / module) :
  - _discovery.py : découverte récursive des *.dbml
  - _page.py      : rendu HTML du visualiseur ERD

Convention de ports : DrawDB sur 8081 (configurable --port), Dashboard sur 8080.
ADR-0369 : timeout explicite, context managers, jamais except:pass, logger structuré.
"""

from __future__ import annotations

import http.server
import json
import logging
import socketserver
import sys
import urllib.parse
import webbrowser
from typing import Any, Optional

from tools.drawdb._discovery import REPO_ROOT, find_dbml_files, read_active_project
from tools.drawdb._page import render_schema_page

# Re-exports rétrocompatibles (ADR-0202)
__all__ = ["DEFAULT_PORT", "DrawDBHandler", "find_dbml_files", "serve_drawdb"]

logger = logging.getLogger("drawdb.runner")

DEFAULT_PORT: int = 8081


class DrawDBHandler(http.server.BaseHTTPRequestHandler):
    """
    Gestionnaire HTTP local souverain du visualiseur DrawDB.
    Routes :
      GET /          → Page ERD (avec ?schema=N pour sélectionner le fichier)
      GET /api/dbml  → JSON des fichiers DBML disponibles
    Zéro ressource externe : toutes les réponses sont générées en mémoire locale.
    """

    _project_name: Optional[str] = None  # Injecté à l'instanciation via serve_drawdb()

    def log_message(self, fmt: str, *args: Any) -> None:  # type: ignore[override]
        logger.debug(
            "HTTP %s",
            fmt % args,
            extra={"component": "drawdb", "operation": "http_request"},
        )

    def _send_response(self, status: int, content_type: str, body: str) -> None:
        encoded = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("X-Sovereign", "mLoop-Local")
        # Politique de sécurité stricte — aucune ressource externe autorisée
        self.send_header(
            "Content-Security-Policy", "default-src 'self' 'unsafe-inline'; connect-src 'none'"
        )
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urllib.parse.urlparse(self.path)
        qs = urllib.parse.parse_qs(parsed.query)

        if parsed.path == "/api/dbml":
            dbml_files = find_dbml_files(self.__class__._project_name)
            payload = [
                {
                    "index": i,
                    "name": f.name,
                    "parent": f.parent.name,
                    "path": str(f.relative_to(REPO_ROOT))
                    if f.is_relative_to(REPO_ROOT)
                    else f.name,
                }
                for i, f in enumerate(dbml_files)
            ]
            self._send_response(200, "application/json", json.dumps(payload, ensure_ascii=False))
            return

        if parsed.path == "/":
            dbml_files = find_dbml_files(self.__class__._project_name)
            schema_idx = 0
            if "schema" in qs:
                try:
                    schema_idx = int(qs["schema"][0])
                except (ValueError, IndexError):
                    schema_idx = 0
            html = render_schema_page(dbml_files, schema_idx)
            self._send_response(200, "text/html", html)
            return

        self._send_response(404, "text/plain", "Not Found")


def serve_drawdb(
    port: int = DEFAULT_PORT, auto_open: bool = True, project_name: Optional[str] = None
) -> None:
    """
    Lance le serveur DrawDB souverain sur le port spécifié.
    Injecte le nom du projet pour la découverte DBML ciblée.
    """
    # Injection du projet dans le handler (classe-level pour ThreadingTCPServer)
    DrawDBHandler._project_name = project_name or read_active_project()

    socketserver.TCPServer.allow_reuse_address = True

    try:
        with socketserver.ThreadingTCPServer(("", port), DrawDBHandler) as httpd:
            url = f"http://localhost:{port}"
            print(f"🚀 [mLoop DrawDB] Visualiseur ERD souverain démarré sur : {url}")
            print(f"   Port : {port} | Projet : {DrawDBHandler._project_name or 'auto'}")
            print("   Zéro dépendance externe — 100% local souverain")
            print("   Pressez Ctrl+C pour arrêter.")
            if auto_open:
                webbrowser.open(url)
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Serveur DrawDB arrêté.")
    except OSError as exc:
        logger.error(
            "Impossible de démarrer le serveur DrawDB (port occupé ?)",
            exc_info=True,
            extra={
                "component": "drawdb",
                "operation": "serve_drawdb",
                "port": port,
                "error": str(exc),
            },
        )
        print(f"❌ Erreur démarrage DrawDB sur le port {port} : {exc}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        logger.error(
            "Erreur inattendue lors du démarrage DrawDB",
            exc_info=True,
            extra={
                "component": "drawdb",
                "operation": "serve_drawdb",
                "port": port,
                "error": str(exc),
            },
        )
        print(f"❌ Erreur inattendue : {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    _port = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PORT
    _project = sys.argv[2] if len(sys.argv) > 2 else None
    serve_drawdb(port=_port, project_name=_project)
