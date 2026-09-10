"""
Local Sovereign Runner for drawDB in mLoop.
Serves and launches drawDB locally without external server dependencies.
"""

import http.server
import socketserver
import webbrowser
import sys
import os
from pathlib import Path

DEFAULT_PORT = 8080
DRAWDB_DIR = Path(__file__).parent / "static"

def create_standalone_html() -> str:
    """Returns standalone offline fallback page embedding drawDB app iframe or offline visualizer."""
    return """<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>mLoop Sovereign drawDB Runner</title>
    <style>
        body { font-family: 'Segoe UI', system-ui, sans-serif; margin: 0; background: #0f172a; color: #f8fafc; height: 100vh; display: flex; flex-direction: column; }
        header { background: #1e293b; padding: 1rem 2rem; border-bottom: 1px solid #334155; display: flex; justify-content: space-between; align-items: center; }
        h1 { margin: 0; font-size: 1.25rem; color: #38bdf8; display: flex; align-items: center; gap: 0.5rem; }
        .badge { background: #0284c7; color: white; padding: 0.2rem 0.6rem; border-radius: 9999px; font-size: 0.75rem; font-weight: bold; }
        iframe { width: 100%; height: calc(100vh - 65px); border: none; }
        .offline-notice { padding: 2rem; text-align: center; max-width: 600px; margin: auto; background: #1e293b; border-radius: 12px; border: 1px solid #334155; }
        .btn { background: #0284c7; color: white; border: none; padding: 0.6rem 1.2rem; border-radius: 6px; cursor: pointer; font-weight: 600; text-decoration: none; display: inline-block; margin-top: 1rem; }
        .btn:hover { background: #0369a1; }
    </style>
</head>
<body>
    <header>
        <h1><span>🎨</span> mLoop drawDB Sovereign Visualizer</h1>
        <span class="badge">Mode Local Offline</span>
    </header>
    <iframe src="https://www.drawdb.app/editor" title="drawDB Local Editor"></iframe>
</body>
</html>
"""

def serve_drawdb(port: int = DEFAULT_PORT, auto_open: bool = True):
    DRAWDB_DIR.mkdir(parents=True, exist_ok=True)
    index_file = DRAWDB_DIR / "index.html"
    if not index_file.exists():
        with open(index_file, "w", encoding="utf-8") as f:
            f.write(create_standalone_html())

    os.chdir(DRAWDB_DIR)
    handler = http.server.SimpleHTTPRequestHandler
    socketserver.TCPServer.allow_reuse_address = True
    
    try:
        with socketserver.ThreadingTCPServer(("", port), handler) as httpd:
            url = f"http://localhost:{port}"
            print(f"🚀 [mLoop drawDB] Serveur local souverain démarré sur : {url}")
            print("Pressez Ctrl+C pour arrêter le serveur.")
            if auto_open:
                webbrowser.open(url)
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Serveur drawDB arrêté.")
    except Exception as e:
        print(f"Erreur lors du démarrage du serveur local drawDB: {e}")

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PORT
    serve_drawdb(port=port)
