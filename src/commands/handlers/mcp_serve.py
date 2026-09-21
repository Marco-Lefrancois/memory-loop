"""
Handler CLI pour le serveur MCP SSE (MLOOP-103-BE).
"""

from src.cli import ZeroFluffConsole


def handle_mcp_serve(args, state, project_path):
    """Démarre le serveur MCP transport réseau SSE."""
    host = getattr(args, "host", "127.0.0.1")
    port = getattr(args, "port", 8380)

    ZeroFluffConsole.section("DÉMARRAGE DU SERVEUR MCP SSE (MLOOP-103-BE)")
    ZeroFluffConsole.info(f"Adresse : http://{host}:{port}")
    ZeroFluffConsole.info("Endpoints : GET /sse (flux SSE) | POST /messages (JSON-RPC)")
    ZeroFluffConsole.info("Ctrl+C pour arrêter.")

    from src.bridges.mcp_sse_server import run_server

    run_server(host=host, port=port)
    return 0
