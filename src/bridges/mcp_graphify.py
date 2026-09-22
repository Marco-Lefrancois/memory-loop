import sys
import json
import traceback
from pathlib import Path

# Activer l'import depuis la racine du projet
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.utils.logger import get_logger

logger = get_logger("bridges.mcp_graphify")


def log_error(msg: str):
    """Écrit les logs sur stderr pour ne pas polluer stdout (utilisé par JSON-RPC)."""
    sys.stderr.write(f"[mcp_graphify] {msg}\n")
    sys.stderr.flush()


import datetime

# Cache Singleton en mémoire pour éviter les relectures disques répétitives
_GRAPH_CACHE: dict[str, tuple[float, dict]] = {}


def load_knowledge_graph(project: str = None) -> tuple[dict, Path]:
    """Charge les métadonnées du graphe Graphify ou knowledge_graph.json pour un projet avec cache mémoire."""
    if not project:
        try:
            from src.loop_mem.db import get_active_project

            project = get_active_project()
        except Exception as e:
            logger.debug(
                "Résolution projet actif échouée, fallback 'mLoop'",
                exc_info=True,
                extra={
                    "component": "bridges.mcp_graphify",
                    "operation": "get_active_project",
                    "error": str(e),
                },
            )
    target_project = project or "mLoop"

    # Priorité absolue au projet actif (17 Ko vs racine)
    possible_paths = []
    if target_project.lower() != "global":
        possible_paths.extend(
            [
                Path("Projects") / target_project / "memory" / "knowledge_graph.json",
                Path("Projects") / target_project / "graphify-out" / "graph.json",
            ]
        )
    possible_paths.append(Path("graphify-out") / "graph.json")

    for gpath in possible_paths:
        if gpath.exists():
            try:
                resolved_key = str(gpath.resolve())
                mtime = gpath.stat().st_mtime
                if resolved_key in _GRAPH_CACHE:
                    cached_mtime, cached_data = _GRAPH_CACHE[resolved_key]
                    if cached_mtime == mtime:
                        return cached_data, gpath

                data = json.loads(gpath.read_text(encoding="utf-8"))
                _GRAPH_CACHE[resolved_key] = (mtime, data)
                return data, gpath
            except Exception as e:
                log_error(f"Erreur de lecture du graphe sur {gpath}: {e}")
                logger.warning(
                    "Lecture du fichier de graphe échouée, tentative du chemin suivant",
                    exc_info=True,
                    extra={
                        "component": "bridges.mcp_graphify",
                        "operation": "load_knowledge_graph",
                        "graph_path": str(gpath),
                        "error": str(e),
                    },
                )

    return {"nodes": [], "edges": []}, None


def handle_initialize(req_id):
    return {
        "jsonrpc": "2.0",
        "result": {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "mloop-graphify-mcp", "version": "2.0.0"},
        },
        "id": req_id,
    }


# handle_tools_list : extrait vers src/bridges/_mcp_graphify_schemas.py (ADR-0202).
from src.bridges._mcp_graphify_schemas import handle_tools_list  # noqa: E402,F401


def _get_node_desc(node: dict) -> str:
    """Extrait la description d'un nœud qu'elle soit directe ou imbriquée dans properties."""
    desc = node.get("description")
    if not desc and isinstance(node.get("properties"), dict):
        desc = node["properties"].get("description") or node["properties"].get("summary")
    return desc or "N/A"


def handle_tools_call(req_id, params):
    name = params.get("name")
    arguments = params.get("arguments", {})
    project = arguments.get("project")

    graph_data, graph_path = load_knowledge_graph(project)
    nodes = graph_data.get("nodes", [])
    edges = graph_data.get("links", graph_data.get("edges", []))

    if name == "graph_query":
        query = arguments.get("query", "").lower()
        matching_nodes = []

        for n in nodes:
            nid = str(n.get("id", "")).lower()
            label = str(n.get("label", n.get("name", ""))).lower()
            desc = _get_node_desc(n).lower()
            if query in nid or query in label or query in desc:
                matching_nodes.append(n)

        matching_nodes = matching_nodes[:10]

        res_blocks = []
        for mn in matching_nodes:
            nid = mn.get("id") or mn.get("name")
            label = mn.get("label") or mn.get("name") or nid
            res_blocks.append(
                f"📌 Nœud: **{label}** (`{nid}`)\n   Description: {_get_node_desc(mn)}"
            )

        res_text = (
            "\n\n".join(res_blocks)
            if res_blocks
            else f"Aucun nœud correspondant à '{query}' dans le graphe ({graph_path or 'Introuvable'})."
        )

        return {
            "jsonrpc": "2.0",
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": f"### Graphify Query Results ({len(matching_nodes)} nœuds)\n\n{res_text[:4000]}",
                    }
                ]
            },
            "id": req_id,
        }

    elif name == "graph_blast_radius":
        target = arguments.get("target", "")
        try:
            from src.pipelines.blast_radius import calculate_blast_radius, BlastRadiusEngine

            engine = BlastRadiusEngine(project_root=Path("Projects") / (project or "mLoop"))
            engine.knowledge_graph = graph_data
            blast_res = engine.compute_blast_radius(target)
            report = engine.format_markdown_report(blast_res)
            return {
                "jsonrpc": "2.0",
                "result": {"content": [{"type": "text", "text": report}]},
                "id": req_id,
            }
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "result": {
                    "content": [{"type": "text", "text": f"Erreur calcul blast radius: {e}"}]
                },
                "id": req_id,
            }

    elif name == "graph_edge_search":
        src = arguments.get("source", "").lower()
        tgt = arguments.get("target", "").lower()

        rel_edges = []
        for e in edges:
            s = str(e.get("source", "")).lower()
            t = str(e.get("target", "")).lower()
            if (src in s and tgt in t) or (src in t and tgt in s):
                rel_edges.append(
                    f"`{e.get('source')}` ──[{e.get('label', 'REL')}]──> `{e.get('target')}`"
                )

        res_text = (
            "\n".join(rel_edges)
            if rel_edges
            else f"Aucun lien direct trouvé entre '{src}' et '{tgt}'."
        )
        return {
            "jsonrpc": "2.0",
            "result": {
                "content": [
                    {"type": "text", "text": f"### Graphify Edge Search\n\n{res_text[:4000]}"}
                ]
            },
            "id": req_id,
        }

    elif name == "graph_explain":
        concept = arguments.get("concept", "").lower()
        target_node = None
        for n in nodes:
            nid = str(n.get("id", "")).lower()
            label = str(n.get("label", n.get("name", ""))).lower()
            if concept in nid or concept in label:
                target_node = n
                break

        if not target_node:
            res_text = f"Nœud '{concept}' introuvable dans le graphe."
        else:
            nid = target_node.get("id") or target_node.get("name")
            label = target_node.get("label") or target_node.get("name") or nid
            neighbors = []
            for e in edges:
                if str(e.get("source")).lower() == str(nid).lower():
                    neighbors.append(f"-> ({e.get('label', 'rel')}) -> `{e.get('target')}`")
                elif str(e.get("target")).lower() == str(nid).lower():
                    neighbors.append(f"<- ({e.get('label', 'rel')}) <- `{e.get('source')}`")

            res_text = (
                f"### Nœud : {label} (`{nid}`)\n"
                f"**Description** : {_get_node_desc(target_node)}\n"
                f"**Voisins 1-Hop** :\n"
                + ("\n".join(neighbors[:15]) if neighbors else "Aucun voisin direct.")
            )

        return {
            "jsonrpc": "2.0",
            "result": {"content": [{"type": "text", "text": res_text[:4000]}]},
            "id": req_id,
        }

    elif name == "graph_status":
        size_kb = (graph_path.stat().st_size / 1024) if graph_path and graph_path.exists() else 0.0
        mtime_str = (
            datetime.datetime.fromtimestamp(graph_path.stat().st_mtime).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            if graph_path and graph_path.exists()
            else "N/A"
        )
        status_text = (
            f"### Graphify Knowledge Graph Status\n\n"
            f"- **Fichier Source** : `{graph_path or 'Introuvable'}`\n"
            f"- **Taille** : `{size_kb:.1f} Ko`\n"
            f"- **Dernière Modification** : `{mtime_str}`\n"
            f"- **Nombre de Nœuds** : `{len(nodes)}`\n"
            f"- **Nombre de Liens** : `{len(edges)}`\n"
            f"- **Projet Cible** : `{project or 'Actif / Résolu'}`\n"
        )
        return {
            "jsonrpc": "2.0",
            "result": {"content": [{"type": "text", "text": status_text}]},
            "id": req_id,
        }

    else:
        return {
            "jsonrpc": "2.0",
            "result": {
                "isError": True,
                "content": [{"type": "text", "text": f"Outil MCP inconnu: {name}"}],
            },
            "id": req_id,
        }


def main():
    log_error("Démarrage du serveur MCP stdio mLoop Graphify...")
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            req = json.loads(line)
            method = req.get("method")
            req_id = req.get("id")
            params = req.get("params", {})

            if method == "initialize":
                res = handle_initialize(req_id)
            elif method == "tools/list":
                res = handle_tools_list(req_id)
            elif method == "tools/call":
                res = handle_tools_call(req_id, params)
            else:
                if req_id is not None:
                    res = {
                        "jsonrpc": "2.0",
                        "error": {"code": -32601, "message": "Non géré"},
                        "id": req_id,
                    }
                else:
                    continue

            sys.stdout.write(json.dumps(res) + "\n")
            sys.stdout.flush()
        except Exception as e:
            log_error(f"Erreur stdio : {e}")
            logger.error(
                "Erreur stdio serveur MCP Graphify",
                exc_info=True,
                extra={
                    "component": "bridges.mcp_graphify",
                    "operation": "stdio_loop",
                    "error": str(e),
                },
            )


if __name__ == "__main__":
    main()
