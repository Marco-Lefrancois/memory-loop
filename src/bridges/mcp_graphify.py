import sys
import json
import traceback
from pathlib import Path

# Activer l'import depuis la racine du projet
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

def log_error(msg: str):
    """Écrit les logs sur stderr pour ne pas polluer stdout (utilisé par JSON-RPC)."""
    sys.stderr.write(f"[mcp_graphify] {msg}\n")
    sys.stderr.flush()

def load_knowledge_graph(project: str = None) -> tuple[dict, Path]:
    """Charge les métadonnées du graphe Graphify ou knowledge_graph.json pour un projet."""
    if not project:
        try:
            from src.loop_mem.db import get_active_project
            project = get_active_project()
        except Exception:
            pass
    target_project = project or "mLoop"
    
    # Préférer graphify-out/graph.json à la racine du projet ou global
    possible_paths = [
        Path("graphify-out") / "graph.json",
        Path("Projects") / target_project / "memory" / "knowledge_graph.json",
        Path("Projects") / target_project / "graphify-out" / "graph.json"
    ]
    
    for gpath in possible_paths:
        if gpath.exists():
            try:
                data = json.loads(gpath.read_text(encoding="utf-8"))
                return data, gpath
            except Exception as e:
                log_error(f"Erreur de lecture du graphe sur {gpath}: {e}")
                
    return {"nodes": [], "edges": []}, None

def handle_initialize(req_id):
    return {
        "jsonrpc": "2.0",
        "result": {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {}
            },
            "serverInfo": {
                "name": "mloop-graphify-mcp",
                "version": "2.0.0"
            }
        },
        "id": req_id
    }

def handle_tools_list(req_id):
    return {
        "jsonrpc": "2.0",
        "result": {
            "tools": [
                {
                    "name": "graph_query",
                    "description": "Interroge le sous-graphe de connaissances autour d'un concept métier (RM-XXX), d'une ADR ou d'un composant.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Mot-clé ou concept recherché (ex: 'RM-001' ou 'Ingestion MarkItDown')."
                            },
                            "project": {
                                "type": "string",
                                "description": "Nom optionnel du projet."
                            }
                        },
                        "required": ["query"]
                    }
                },
                {
                    "name": "graph_path",
                    "description": "Calcule le chemin de dépendances direct entre deux concepts ou composants d'architecture.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "source": {
                                "type": "string",
                                "description": "Nœud source (ex: 'ADR-0101')."
                            },
                            "target": {
                                "type": "string",
                                "description": "Nœud cible (ex: 'docs/00-ingested')."
                            },
                            "project": {
                                "type": "string",
                                "description": "Nom optionnel du projet."
                            }
                        },
                        "required": ["source", "target"]
                    }
                },
                {
                    "name": "graph_explain",
                    "description": "Génère une explication détaillée d'un nœud d'architecture et de ses 1-hop voisins dans le graphe.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "concept": {
                                "type": "string",
                                "description": "Identifiant ou titre du nœud."
                            },
                            "project": {
                                "type": "string",
                                "description": "Nom optionnel du projet."
                            }
                        },
                        "required": ["concept"]
                    }
                },
                {
                    "name": "graph_blast_radius",
                    "description": "Calcule le rayon d'impact (Blast Radius) ascendant et descendant pour un fichier, un concept ou un modèle.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "target": {
                                "type": "string",
                                "description": "Chemin du fichier ou nom du concept cible (ex: 'US-01' ou 'OneTrustSDK')."
                            },
                            "project": {
                                "type": "string",
                                "description": "Nom optionnel du projet."
                            }
                        },
                        "required": ["target"]
                    }
                }
            ]
        },
        "id": req_id
    }

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
            desc = str(n.get("description", "")).lower()
            if query in nid or query in label or query in desc:
                matching_nodes.append(n)

        matching_nodes = matching_nodes[:10]
        
        res_blocks = []
        for mn in matching_nodes:
            nid = mn.get("id") or mn.get("name")
            label = mn.get("label") or mn.get("name") or nid
            res_blocks.append(f"📌 Nœud: **{label}** (`{nid}`)\n   Description: {mn.get('description', 'N/A')}")

        res_text = "\n\n".join(res_blocks) if res_blocks else f"Aucun nœud correspondant à '{query}' dans le graphe ({graph_path or 'Introuvable'})."
        
        return {
            "jsonrpc": "2.0",
            "result": {
                "content": [{"type": "text", "text": f"### Graphify Query Results ({len(matching_nodes)} nœuds)\n\n{res_text[:4000]}"}]
            },
            "id": req_id
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
                "result": {
                    "content": [{"type": "text", "text": report}]
                },
                "id": req_id
            }
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "result": {
                    "content": [{"type": "text", "text": f"Erreur calcul blast radius: {e}"}]
                },
                "id": req_id
            }

    elif name == "graph_edge_search":
        src = arguments.get("source", "").lower()
        tgt = arguments.get("target", "").lower()
        
        rel_edges = []
        for e in edges:
            s = str(e.get("source", "")).lower()
            t = str(e.get("target", "")).lower()
            if (src in s and tgt in t) or (src in t and tgt in s):
                rel_edges.append(f"`{e.get('source')}` ──[{e.get('label', 'REL')}]──> `{e.get('target')}`")
                
        res_text = "\n".join(rel_edges) if rel_edges else f"Aucun lien direct trouvé entre '{src}' et '{tgt}'."
        return {
            "jsonrpc": "2.0",
            "result": {
                "content": [{"type": "text", "text": f"### Graphify Edge Search\n\n{res_text[:4000]}"}]
            },
            "id": req_id
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
            label = target_node.get("label") or target_node.get("name")
            neighbors = []
            for e in edges:
                if str(e.get("source")).lower() == str(nid).lower():
                    neighbors.append(f"-> ({e.get('label', 'rel')}) -> `{e.get('target')}`")
                elif str(e.get("target")).lower() == str(nid).lower():
                    neighbors.append(f"<- ({e.get('label', 'rel')}) <- `{e.get('source')}`")
                    
            res_text = (
                f"### Nœud : {label} (`{nid}`)\n"
                f"**Description** : {target_node.get('description', 'N/A')}\n"
                f"**Voisins 1-Hop** :\n" + ("\n".join(neighbors[:15]) if neighbors else "Aucun voisin direct.")
            )

        return {
            "jsonrpc": "2.0",
            "result": {
                "content": [{"type": "text", "text": res_text[:4000]}]
            },
            "id": req_id
        }

    else:
        return {
            "jsonrpc": "2.0",
            "result": {
                "isError": True,
                "content": [{"type": "text", "text": f"Outil MCP inconnu: {name}"}]
            },
            "id": req_id
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
                    res = {"jsonrpc": "2.0", "error": {"code": -32601, "message": "Non géré"}, "id": req_id}
                else:
                    continue

            sys.stdout.write(json.dumps(res) + "\n")
            sys.stdout.flush()
        except Exception as e:
            log_error(f"Erreur stdio : {e}")

if __name__ == "__main__":
    main()
