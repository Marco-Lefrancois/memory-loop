import sys
import json
import uuid
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional

# S'assurer d'inclure le chemin racine dans sys.path pour les résolutions
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.loop_mem.db import (
    search_observations,
    get_session_timeline,
    get_observation_by_id,
    get_active_project,
    search_in_memory
)

# ── Stateful Session Server pattern ──────────────────────────────────────────
# Persist active project across tool calls within a single MCP session.
# This eliminates the need for the LLM to pass `project` on every call.
_SESSION_ID: str = str(uuid.uuid4())[:8]
_SESSION_PROJECT: str | None = None  # set on first use or via set_project tool
_PRELOAD_CACHE: dict = {}

def auto_recall_passive_memory(story_id: str = None, query: str = None, project: str = None) -> list:
    """
    Axe 1 jcode (ADR-0308) : Auto-Recall Sémantique Passif.
    Calcule et extrait automatiquement les 5 engrammes de mémoire les plus pertinents 
    basés sur le story_id ou les mots-clés de dérive contextuelle, sans nécessiter 
    d'appel d'outil explicite de la part du LLM.
    """
    proj = project or _SESSION_PROJECT or get_active_project() or "mLoop"
    recalled_items = []
    
    # 1. Vérification dans le cache RAM préchargé
    if story_id and story_id in _PRELOAD_CACHE:
        cached_data = _PRELOAD_CACHE[story_id]
        nodes = cached_data.get("nodes", [])[:3]
        for n in nodes:
            name = n.get("name") if isinstance(n, dict) else str(n)
            recalled_items.append({"source": "RAM_Cache", "type": "engramme_graphe", "summary": f"Nœud sémantique: {name}"})
            
    # 2. Recherche automatique FTS5 dans la base SQLite d'observations mLoop
    search_term = query or story_id or "architecture"
    try:
        obs_matches = search_observations(query=search_term, project_name=proj) or []
        for obs in obs_matches[:3]:
            recalled_items.append({
                "source": "Memory_SQLite",
                "type": obs.get("type", "observation"),
                "id": obs.get("id"),
                "summary": obs.get("content", "")[:120] + "..."
            })
    except Exception as e:
        log_error(f"Erreur lors de l'Auto-Recall sémantique passif: {e}")
        
    return recalled_items[:5]

def preload_story_context(story_id: str, project: str = None) -> dict:
    global _PRELOAD_CACHE
    proj = project or _SESSION_PROJECT or get_active_project() or "mLoop"
    graph_path = Path("Projects") / proj / "memory" / "knowledge_graph.json"
    
    nodes_cached = 0
    if graph_path.exists():
        try:
            with open(graph_path, "r", encoding="utf-8") as f:
                graph_data = json.load(f)
            nodes = graph_data.get("nodes", [])
            edges = graph_data.get("edges", [])
            
            relevant_nodes = [n for n in nodes if story_id.lower() in str(n).lower()]
            if not relevant_nodes:
                relevant_nodes = nodes[:10]  # Fallback to top nodes
                
            _PRELOAD_CACHE[story_id] = {
                "story_id": story_id,
                "project": proj,
                "nodes": relevant_nodes,
                "edges": edges,
                "timestamp": str(uuid.uuid4())
            }
            nodes_cached = len(relevant_nodes)
        except Exception as e:
            log_error(f"Erreur lors du préchargement de {story_id}: {e}")
            
    # Auto-Recall Passif automatique au préchargement
    passive_engrams = auto_recall_passive_memory(story_id=story_id, project=proj)
    
    return {
        "status": "preloaded",
        "story_id": story_id,
        "nodes_cached": nodes_cached,
        "auto_recall_engrams": len(passive_engrams),
        "memory_used_kb": len(json.dumps(_PRELOAD_CACHE.get(story_id, {}))) // 1024
    }

def clear_preloaded_context(story_id: str = None) -> dict:
    global _PRELOAD_CACHE
    if story_id:
        _PRELOAD_CACHE.pop(story_id, None)
    else:
        _PRELOAD_CACHE.clear()
    return {"status": "cleared", "remaining_keys": list(_PRELOAD_CACHE.keys())}


def log_error(msg: str):
    """Écrit les logs d'erreurs sur stderr pour ne pas polluer stdout (réservé à MCP JSON-RPC)."""
    sys.stderr.write(f"[MCP LOOP-MEM] {msg}\n")
    sys.stderr.flush()

def handle_initialize(req_id, params=None):
    _meta = (params or {}).get("_meta", {})
    traceparent = _meta.get("traceparent", "")
    if traceparent:
        log_error(f"OpenTelemetry Trace Context: {traceparent}")
    return {
        "jsonrpc": "2.0",
        "result": {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {"listChanged": True},
                "resources": {"subscribe": True, "listChanged": True},
                "extensions": {
                    "io.modelcontextprotocol/tasks": {"version": "1.0"},
                    "io.modelcontextprotocol/mrtr": {"version": "1.0"}
                }
            },
            "serverInfo": {
                "name": "memory-loop-session-memory-mcp",
                "version": "2.0.0",
                "sessionId": _SESSION_ID
            }
        },
        "id": req_id
    }

def handle_server_discover(req_id, params=None):
    """RPC officiel MCP 2026-07-28 pour l'annonce des capacités et versions (Stateless)."""
    return {
        "jsonrpc": "2.0",
        "result": {
            "protocolVersion": "2024-11-05",
            "supportedVersions": ["2026-07-28", "2025-11-25", "2024-11-05"],
            "capabilities": {
                "tools": {"listChanged": True},
                "resources": {"subscribe": True, "listChanged": True},
                "extensions": {
                    "io.modelcontextprotocol/tasks": {"version": "1.0"},
                    "io.modelcontextprotocol/mrtr": {"version": "1.0"}
                }
            },
            "serverInfo": {
                "name": "memory-loop-session-memory-mcp",
                "version": "2.0.0",
            }
        },
        "id": req_id
    }


def make_input_required_result(req_id: Any, input_requests: list) -> dict:
    """
    Génère une réponse InputRequiredResult selon la spécification MRTR MCP 2026-07-28 (ADR-0307).
    Permet l'interrogatoire Grilling (/grill-me) sans rupture de contexte.
    """
    return {
        "jsonrpc": "2.0",
        "result": {
            "resultType": "input_required",
            "inputRequests": input_requests
        },
        "id": req_id
    }


def handle_resources_list(req_id):
    """Expose session observations, Graphify nodes, and ADRs as MCP Resources (Resource Gateway pattern)."""
    project = _SESSION_PROJECT or get_active_project()
    resources = []
    if project:
        observations = search_observations(query="", project_name=project) or []
        for obs in observations[:20]:  # cap at 20 for context budget
            resources.append({
                "uri": f"mloop://project/{project}/observation/{obs['id']}",
                "name": f"[{obs['type'].upper()}] {obs['content'][:60]}...",
                "mimeType": "text/plain",
                "description": f"Observation #{obs['id']} du projet {project} ({obs['timestamp']})"
            })
    
    # Exposer le graphe de connaissances comme ressource
    graph_file = Path("graphify-out/graph.json")
    if graph_file.exists():
        resources.append({
            "uri": "graphify://graph/summary",
            "name": "Graphify Knowledge Graph Summary",
            "mimeType": "application/json",
            "description": "Résumé du graphe de connaissances d'architecture Graphify"
        })
        
    return {
        "jsonrpc": "2.0",
        "result": {"resources": resources},
        "id": req_id
    }


def handle_resources_read(req_id, params):
    """Fetch full content of a single observation or Graphify/ADR/Story via its Resource URI."""
    uri = params.get("uri", "")

    if uri.startswith("graphify://node/"):
        node_name = uri.replace("graphify://node/", "")
        graph_file = Path("graphify-out/graph.json")
        if not graph_file.exists():
            return {
                "jsonrpc": "2.0",
                "result": {"isError": True, "content": [{"type": "text", "text": "Le graphe de connaissances 'graphify-out/graph.json' n'a pas encore été généré. Lancez 'python src/swarm.py sync' pour le créer."}]},
                "id": req_id
            }
        try:
            data = json.loads(graph_file.read_text(encoding="utf-8"))
            nodes = data.get("nodes", [])
            matched = None
            if isinstance(nodes, dict):
                matched = nodes.get(node_name)
            elif isinstance(nodes, list):
                for n in nodes:
                    if isinstance(n, dict) and str(n.get("name", "")).lower() == node_name.lower():
                        matched = n
                        break
            if matched:
                return {
                    "jsonrpc": "2.0",
                    "result": {"contents": [{"uri": uri, "mimeType": "application/json", "text": json.dumps(matched, indent=2, ensure_ascii=False)}]},
                    "id": req_id
                }
            return {
                "jsonrpc": "2.0",
                "result": {"isError": True, "content": [{"type": "text", "text": f"Nœud Graphify '{node_name}' introuvable dans le graphe."}]},
                "id": req_id
            }
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "result": {"isError": True, "content": [{"type": "text", "text": f"Erreur de lecture Graphify : {e}"}]},
                "id": req_id
            }

    elif uri.startswith("loopmem://adr/"):
        adr_id = uri.replace("loopmem://adr/", "")
        adr_dir = Path("docs/01-architecture")
        matches = list(adr_dir.glob(f"*{adr_id}*.md")) if adr_dir.exists() else []
        if matches:
            content = matches[0].read_text(encoding="utf-8")
            return {
                "jsonrpc": "2.0",
                "result": {"contents": [{"uri": uri, "mimeType": "text/markdown", "text": content}]},
                "id": req_id
            }
        return {
            "jsonrpc": "2.0",
            "result": {"isError": True, "content": [{"type": "text", "text": f"ADR #{adr_id} introuvable sous docs/01-architecture/."}]},
            "id": req_id
        }

    elif uri.startswith("loopmem://story/"):
        story_id = uri.replace("loopmem://story/", "")
        project = _SESSION_PROJECT or get_active_project() or "mLoop"
        story_dir = Path("Projects") / project / "backlog" / "stories"
        matches = list(story_dir.glob(f"*{story_id}*.md")) if story_dir.exists() else []
        if matches:
            content = matches[0].read_text(encoding="utf-8")
            return {
                "jsonrpc": "2.0",
                "result": {"contents": [{"uri": uri, "mimeType": "text/markdown", "text": content}]},
                "id": req_id
            }
        return {
            "jsonrpc": "2.0",
            "result": {"isError": True, "content": [{"type": "text", "text": f"Récit #{story_id} introuvable sous Projects/{project}/backlog/stories/."}]},
            "id": req_id
        }

    # Format par défaut : mloop://project/<name>/observation/<id>
    try:
        parts = uri.replace("mloop://project/", "").split("/observation/")
        obs_id = int(parts[-1])
    except (ValueError, IndexError):
        return {
            "jsonrpc": "2.0",
            "result": {"isError": True, "content": [{"type": "text", "text": f"URI non reconnue : {uri}"}]},
            "id": req_id
        }
    obs = get_observation_by_id(obs_id)
    if not obs:
        return {
            "jsonrpc": "2.0",
            "result": {"isError": True, "content": [{"type": "text", "text": f"Observation #{obs_id} introuvable."}]},
            "id": req_id
        }
    file_scope_str = f"\nFichiers : {obs['file_scope']}" if obs['file_scope'] else ""
    content = (
        f"OBSERVATION #{obs['id']} ({obs['type'].upper()})\n"
        f"Projet : {obs['project_name']} | Date : {obs['timestamp']}{file_scope_str}\n"
        f"{'='*50}\n"
        f"{obs['content']}"
    )
    return {
        "jsonrpc": "2.0",
        "result": {"contents": [{"uri": uri, "mimeType": "text/plain", "text": content}]},
        "id": req_id
    }


def _load_tools_yaml_manifest():
    """Charge le manifeste déclaratif tools.yaml s'il existe à la racine (ADR-0309)."""
    manifest_path = Path("tools.yaml")
    if not manifest_path.exists():
        return {}
    try:
        import yaml
        content = manifest_path.read_text(encoding="utf-8")
        data = yaml.safe_load(content)
        if isinstance(data, dict):
            toolsets = {}
            for ts in data.get("toolsets", []):
                if isinstance(ts, dict) and "name" in ts and "tools" in ts:
                    toolsets[ts["name"].upper()] = ts["tools"]
            return toolsets
    except Exception as e:
        log_error(f"Erreur chargement tools.yaml : {e}")
    return {}


def handle_tools_list(req_id, params=None):
    params = params or {}
    _meta = params.get("_meta", {})
    phase_filter = (params.get("phase") or _meta.get("phase") or "").upper()
    manifest_toolsets = _load_tools_yaml_manifest()
    
    tools = [
        {
            "name": "loop_mem_search",
            "phase": "PLAN",
            "description": (
                "Recherche dans la mémoire persistante de session du framework Memory Loop. "
                "Renvoie un index condensé de correspondances (IDs, types, résumés, dates) "
                "pour économiser le budget de jetons (tokens)."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Terme ou phrase de recherche textuelle FTS5 (ex: 'bug d'authentification')."
                    },
                    "project": {
                        "type": "string",
                        "description": "Optionnel. Filtre par nom de projet cible (ex: 'ReviewSenseCloud')."
                    },
                    "type": {
                        "type": "string",
                        "enum": ["decision", "bugfix", "feature", "discovery"],
                        "description": "Optionnel. Filtre par type d'observation."
                    },
                    "stateHandle": {
                        "type": "string",
                        "description": "Optionnel (MCP 2026-07-28). Handle d'état de session explicite."
                    }
                },
                "required": ["query"]
            }
        },
        {
            "name": "loop_mem_timeline",
            "phase": "PLAN",
            "description": (
                "Récupère la timeline chronologique condensée de toutes les observations enregistrées "
                "pour un projet spécifique. Très utile au démarrage d'une session pour comprendre le contexte récent."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "project": {
                        "type": "string",
                        "description": "Le nom du projet cible."
                    }
                },
                "required": ["project"]
            }
        },
        {
            "name": "loop_mem_get_observations",
            "phase": "PLAN",
            "description": (
                "Récupère le contenu détaillé (Markdown complet) pour une liste d'observations spécifiées par leurs identifiants. "
                "À appeler après avoir repéré des IDs pertinents via 'loop_mem_search' ou 'loop_mem_timeline'."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "ids": {
                        "type": "array",
                        "items": {
                            "type": "integer"
                        },
                        "description": "Tableau d'identifiants numériques des observations à récupérer (ex: [12, 15])."
                    }
                },
                "required": ["ids"]
            }
        },
        {
            "name": "loop_mem_code_rag",
            "phase": "BUILD",
            "description": (
                "Recherche sémantique (RAG inversé) pour le code source. "
                "Renvoie le contenu intégral (jusqu'à 2 fichiers maximum) des fichiers les plus pertinents "
                "dans l'index Graphify. Idéal pour injecter des exemples 'Few-Shot' en contexte avant d'écrire."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Description du composant recherché (ex: 'hook auth react')."
                    }
                },
                "required": ["query"]
            }
        },
        {
            "name": "loop_mem_rho_search",
            "phase": "VALIDATE",
            "description": (
                "Recherche dans la mémoire d'erreurs RHO (Chaos Testing) via modèle local (Ollama). "
                "Trouve les solutions documentées pour des traces d'erreurs similaires."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "error_trace": {
                        "type": "string",
                        "description": "La trace d'erreur ou le log de compilation."
                    }
                },
                "required": ["error_trace"]
            }
        },
        {
            "name": "loop_mem_set_project",
            "phase": "SPEC",
            "description": (
                "Définit le projet actif pour la session MCP courante (Stateful Session). "
                "Évite d'avoir à spécifier le projet à chaque appel d'outil."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "project": {
                        "type": "string",
                        "description": "Nom du projet à activer (ex: 'mLoop')."
                    }
                },
                "required": ["project"]
            }
        },
        {
            "name": "loop_mem_preload_context",
            "phase": "PLAN",
            "description": (
                "Précharge de manière asynchrone les engrammes sémantiques 1-hop en RAM pour une story donnée. "
                "Annule la latence d'accès disque lors des recherches."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "story_id": {
                        "type": "string",
                        "description": "Identifiant de la story (ex: 'MLOOP-013-BE')."
                    },
                    "project": {
                        "type": "string",
                        "description": "Optionnel. Nom du projet cible."
                    }
                },
                "required": ["story_id"]
            }
        },
        {
            "name": "loop_mem_clear_preloaded_context",
            "phase": "PLAN",
            "description": (
                "Purge le cache RAM des engrammes préchargés pour une story donnée ou pour toute la session."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "story_id": {
                        "type": "string",
                        "description": "Optionnel. Identifiant de la story à purger. Si omis, purge tout le cache."
                    }
                }
            }
        },
        {
            "name": "check_story_compliance",
            "phase": "VALIDATE",
            "description": (
                "Vérifie en temps réel la conformité d'un récit (Story Markdown) par rapport à l'ADR-0301 "
                "(4 Piliers Gherkin : Nominal, Exceptions, Résilience, UX) et l'isolation technique."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "Le contenu Markdown du récit à auditer."
                    }
                },
                "required": ["content"]
            }
        },
        {
            "name": "loop_hypergraph_query",
            "phase": "PLAN",
            "description": (
                "Interroge l'hypergraphe du projet pour obtenir le Knowledge Abstract complet et typé "
                "d'une User Story ou d'un concept métier (ADR-0343). Retourne l'hyper-arête et ses nœuds reliés."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "story_id": {
                        "type": "string",
                        "description": "Identifiant de la User Story cible (ex: 'REC-001', 'COUVBOIRE-990')."
                    },
                    "concept": {
                        "type": "string",
                        "description": "Identifiant ou nom de concept à explorer dans l'hypergraphe."
                    },
                    "project": {
                        "type": "string",
                        "description": "Optionnel. Nom du projet cible."
                    }
                }
            }
        }
    ]
    
    # Axe 2 Google MCP Toolbox : Filtrage dynamique par Phase d'exécution mLoop (ADR-0309)
    if phase_filter:
        allowed_names = manifest_toolsets.get(phase_filter, [])
        if allowed_names:
            tools = [t for t in tools if t.get("name") in allowed_names or t.get("phase") == phase_filter]
        else:
            tools = [t for t in tools if t.get("phase") == phase_filter]
        
    # Nettoyage des clés internes avant d'émettre
    for t in tools:
        t.pop("phase", None)
        
    # RÈGLE MCP 2026-07-28 : Ordre déterministe pour maximiser le taux de hit des Prompt Caches LLM
    tools.sort(key=lambda t: t["name"])
    return {
        "jsonrpc": "2.0",
        "result": {
            "tools": tools,
            "ttlMs": 300000,
            "cacheScope": "private"
        },
        "id": req_id
    }

def handle_tools_call(req_id, params):
    global _SESSION_PROJECT
    name = params.get("name")
    arguments = params.get("arguments", {})

    try:
        # ── Stateful Session: set_project tool ───────────────────────────────
        if name == "loop_mem_set_project":
            _SESSION_PROJECT = arguments.get("project")
            return {
                "jsonrpc": "2.0",
                "result": {
                    "content": [{"type": "text", "text": f"✅ Projet actif de session : **{_SESSION_PROJECT}** (session #{_SESSION_ID})"}]
                },
                "id": req_id
            }

        elif name == "loop_mem_preload_context":
            s_id = arguments.get("story_id")
            proj = arguments.get("project")
            res = preload_story_context(s_id, proj)
            return {
                "jsonrpc": "2.0",
                "result": {
                    "content": [{"type": "text", "text": f"✅ Context preloaded in RAM for story {s_id}: {res['nodes_cached']} nodes cached ({res['memory_used_kb']} KB)."}]
                },
                "id": req_id
            }

        elif name == "loop_mem_clear_preloaded_context":
            s_id = arguments.get("story_id")
            res = clear_preloaded_context(s_id)
            return {
                "jsonrpc": "2.0",
                "result": {
                    "content": [{"type": "text", "text": f"🧹 Cache RAM purgé. Clés restantes : {res['remaining_keys']}"}]
                },
                "id": req_id
            }

        elif name == "check_story_compliance":
            content = arguments.get("content", "")
            import re
            
            issues = []
            warnings = []
            
            # 1. Verification des 4 Piliers Gherkin (ADR-0301)
            scenarios = re.findall(r"(?:Scénario|Scenario)\s*:", content, re.IGNORECASE)
            if len(scenarios) < 4:
                issues.append(f"❌ [ADR-0301] Gherkin 4-Piliers incomplet : {len(scenarios)}/4 scénarios détectés (Exigés : Nominal, Exceptions, Résilience, UX/Observabilité).")
            else:
                warnings.append(f"✅ [ADR-0301] Gherkin 4-Piliers : {len(scenarios)} scénarios détectés.")

            # 2. Verification des sections requises (INVEST)
            if not re.search(r"## Scénarios de test", content, re.IGNORECASE):
                issues.append("❌ Section '## Scénarios de test' manquante.")
            if not re.search(r"## Règles d", content, re.IGNORECASE):
                issues.append("❌ Section '## Règles d'affaires' manquante.")

            # 3. Detection des fuites techniques
            tech_keywords = ["npm install", "yarn add", "expo install", "import {", "```typescript", "```javascript", "zustand", "redux", "axios"]
            for kw in tech_keywords:
                if kw in content.lower():
                    issues.append(f"⚠️ Fuite technique détectée dans le récits fonctionnel : `{kw}`.")

            status_symbol = "🟢 CONFORME" if not issues else "🔴 NON CONFORME"
            report_text = f"### Rapport de Conformité Story ({status_symbol})\n\n"
            if issues:
                report_text += "#### Problèmes à corriger :\n" + "\n".join([f"- {iss}" for iss in issues]) + "\n\n"
            if warnings:
                report_text += "#### Points validés :\n" + "\n".join([f"- {w}" for w in warnings])

            return {
                "jsonrpc": "2.0",
                "result": {
                    "content": [{"type": "text", "text": report_text}]
                },
                "id": req_id
            }

        if name == "loop_mem_search":
            query = arguments.get("query")
            # Use session project as fallback if not specified
            project = arguments.get("project") or _SESSION_PROJECT
            obs_type = arguments.get("type")
            
            # --- TRACKING EVENT BUS ---
            if project:
                try:
                    from src.state import LoopState
                    st = LoopState(project_name=project)
                    p_path = Path("Projects") / project
                    st.load_from_audit(p_path)
                    st.add_to_journal("MCP_SEARCH", f"Agent a recherché: '{query}'", ["Graphify"])
                    st.save_to_audit(p_path)
                except Exception as e:
                    log_error(f"Failed to track MCP_SEARCH: {e}")
            # ---------------------------

            results = search_observations(query=query, project_name=project, obs_type=obs_type)
            
            # Formatage d'index condensé pour économiser les tokens
            output_lines = []
            for r in results:
                file_scope_str = f" [{r['file_scope']}]" if r['file_scope'] else ""
                # Tronquer le contenu pour l'index
                short_content = r['content'][:120].replace('\n', ' ') + "..." if len(r['content']) > 120 else r['content']
                output_lines.append(
                    f"ID: #{r['id']} | Type: {r['type'].upper()}{file_scope_str} | Date: {r['timestamp']}\n"
                    f"   Résumé: {short_content}"
                )
            
            if not output_lines:
                res_text = (
                    f"ℹ️ Aucune observation correspondante trouvée dans la mémoire pour '{query}'.\n\n"
                    "👉 ASTUCES DE AUTO-CORRECTION :\n"
                    "1. Utilisez un mot-clé plus court ou sans terme technique ultra-spécifique.\n"
                    "2. Pour chercher dans le code source, utilisez 'loop_mem_code_rag' ou la CLI 'graphify query'.\n"
                    "3. Pour chercher dans la doc métier de référence, utilisez l'outil Open Notebook 'on_search_notes'."
                )
            else:
                res_text = "Index des observations trouvées :\n\n" + "\n\n".join(output_lines)
            
            return {
                "jsonrpc": "2.0",
                "result": {
                    "content": [{"type": "text", "text": res_text}]
                },
                "id": req_id
            }
            
        elif name == "loop_mem_timeline":
            project = arguments.get("project")
            results = get_session_timeline(project_name=project)
            
            output_lines = []
            for r in results:
                file_scope_str = f" [{r['file_scope']}]" if r['file_scope'] else ""
                short_content = r['content'][:100].replace('\n', ' ') + "..." if len(r['content']) > 100 else r['content']
                output_lines.append(
                    f"ID: #{r['id']} | Type: {r['type'].upper()}{file_scope_str} | Date: {r['timestamp']}\n"
                    f"   Aperçu: {short_content}"
                )
                
            res_text = "\n\n".join(output_lines) if output_lines else "Aucun historique d'observations disponible pour ce projet."
            
            return {
                "jsonrpc": "2.0",
                "result": {
                    "content": [{"type": "text", "text": f"Timeline chronologique du projet '{project}' :\n\n{res_text}"}]
                },
                "id": req_id
            }
            
        elif name == "loop_mem_get_observations":
            ids = arguments.get("ids", [])
            output_blocks = []
            
            for obs_id in ids:
                obs = get_observation_by_id(obs_id)
                if obs:
                    file_scope_str = f"\nFichiers : {obs['file_scope']}" if obs['file_scope'] else ""
                    output_blocks.append(
                        f"==================================================\n"
                        f"OBSERVATION #{obs['id']} ({obs['type'].upper()})\n"
                        f"Projet : {obs['project_name']} | Date : {obs['timestamp']}{file_scope_str}\n"
                        f"==================================================\n"
                        f"{obs['content']}"
                    )
                else:
                    output_blocks.append(f"Observation #{obs_id} introuvable.")
                    
            res_text = "\n\n".join(output_blocks)
            
            return {
                "jsonrpc": "2.0",
                "result": {
                    "content": [{"type": "text", "text": res_text}]
                },
                "id": req_id
            }
            
        elif name == "loop_mem_code_rag":
            query = arguments.get("query")
            active_project = get_active_project()
            if not active_project:
                # Tentative d'auto-détection si le fichier active_project.json n'existe pas
                projects_dir = Path("Projects")
                if projects_dir.exists():
                    subdirs = [p.name for p in projects_dir.iterdir() if p.is_dir()]
                    if subdirs:
                        active_project = subdirs[0]
            
            if not active_project:
                return {
                    "jsonrpc": "2.0",
                    "result": {
                        "content": [{"type": "text", "text": "Erreur: Aucun projet actif détecté."}]
                    },
                    "id": req_id
                }

            # --- TRACKING EVENT BUS ---
            try:
                from src.state import LoopState
                st = LoopState(project_name=active_project)
                p_path = Path("Projects") / active_project
                st.load_from_audit(p_path)
                st.add_to_journal("MCP_RAG", f"Agent a cherché dans le code: '{query}'", ["Graphify", "Code"])
                st.save_to_audit(p_path)
            except Exception as e:
                log_error(f"Failed to track MCP_RAG: {e}")
            # ---------------------------

            project_path = Path("Projects") / active_project
            results = search_in_memory(project_path, query, limit=5)
            
            # Charger les relations (edges) pour l'expansion 1-hop
            edges = []
            kg_file = project_path / "memory" / "knowledge_graph.json"
            if kg_file.exists():
                try:
                    with open(kg_file, "r", encoding="utf-8") as f:
                        edges.extend(json.load(f).get("edges", []))
                except Exception:
                    pass
            graph_file = project_path / "graphify-out" / "graph.json"
            if graph_file.exists():
                try:
                    with open(graph_file, "r", encoding="utf-8") as f:
                        edges.extend(json.load(f).get("edges", []))
                except Exception:
                    pass

            output_blocks = []
            for r in results:
                node_id = r["id"]
                node_label = r["label"]
                node_cat = r["category"]
                snippet = r["snippet"]
                
                # Recherche des voisins direct (1-hop)
                neighbors = []
                for edge in edges:
                    src = edge.get("source") or edge.get("from")
                    tgt = edge.get("target") or edge.get("to")
                    rel = edge.get("relation") or edge.get("type") or "related_to"
                    if src == node_id and tgt:
                        neighbors.append(f"-> ({rel}) -> {tgt}")
                    elif tgt == node_id and src:
                        neighbors.append(f"<- ({rel}) <- {src}")
                
                # Conserver uniquement les 5 relations les plus pertinentes/premières
                neighbors_str = "\n   Relations 1-hop:\n   " + "\n   ".join(neighbors[:5]) if neighbors else ""
                
                output_blocks.append(
                    f"--- RAG RESULT: {node_label} (ID: {node_id}, Catégorie: {node_cat}, Score: {r['score']:.2f}) ---\n"
                    f"Aperçu: {snippet}"
                    f"{neighbors_str}"
                )
            
            res_text = "\n\n".join(output_blocks) if output_blocks else "Aucun noeud de graphe correspondant trouvé."
            return {
                "jsonrpc": "2.0",
                "result": {
                    "content": [{"type": "text", "text": f"RAG Code & Graph Expansion (Projet: {active_project}):\n\n{res_text}"}]
                },
                "id": req_id
            }
            
        elif name == "loop_mem_rho_search":
            error_trace = arguments.get("error_trace")
            from src.loop_mem.db import search_rho_solution
            results = search_rho_solution(error_trace)
            
            output_blocks = []
            for r in results:
                output_blocks.append(
                    f"[Score: {r['score']:.2f}] Projet: {r['project_name']} | Keyword: {r['keyword']}\n"
                    f"Solution: {r['solution']}"
                )
                
            res_text = "\n\n".join(output_blocks) if output_blocks else "Aucune solution RHO trouvée pour cette erreur."
            return {
                "jsonrpc": "2.0",
                "result": {
                    "content": [{"type": "text", "text": f"Résultats RHO (Semantic Search):\n\n{res_text}"}]
                },
                "id": req_id
            }

        elif name == "loop_hypergraph_query":
            story_id = arguments.get("story_id")
            concept = arguments.get("concept")
            proj = arguments.get("project") or _SESSION_PROJECT or get_active_project() or "mLoop"
            
            from src.core.hypergraph_engine import HypergraphKnowledgeAbstract
            hg_file = Path("Projects") / proj / "memory" / "hypergraph.json"
            if not hg_file.exists():
                from src.pipelines.sync import sync_hypergraph
                sync_hypergraph(proj, Path("Projects") / proj, verbose=False)
                
            if not hg_file.exists():
                return {
                    "jsonrpc": "2.0",
                    "result": {
                        "content": [{"type": "text", "text": f"⚠️ Aucun hypergraphe disponible pour le projet '{proj}'."}]
                    },
                    "id": req_id
                }
                
            ka = HypergraphKnowledgeAbstract.load_from_file(hg_file)
            if story_id:
                unit = ka.get_hyper_story_unit(story_id)
                if unit:
                    return {
                        "jsonrpc": "2.0",
                        "result": {
                            "content": [{"type": "text", "text": json.dumps(unit, indent=2, ensure_ascii=False)}]
                        },
                        "id": req_id
                    }
                else:
                    return {
                        "jsonrpc": "2.0",
                        "result": {
                            "content": [{"type": "text", "text": f"⚠️ User Story '{story_id}' introuvable dans l'hypergraphe."}]
                        },
                        "id": req_id
                    }
            elif concept:
                node = ka.get_node(concept)
                related = ka.find_related_nodes(concept)
                res = {
                    "concept": node.to_dict() if node else {"node_id": concept},
                    "related_nodes": [r.to_dict() for r in related]
                }
                return {
                    "jsonrpc": "2.0",
                    "result": {
                        "content": [{"type": "text", "text": json.dumps(res, indent=2, ensure_ascii=False)}]
                    },
                    "id": req_id
                }
            else:
                return {
                    "jsonrpc": "2.0",
                    "result": {
                        "content": [{"type": "text", "text": json.dumps(ka.to_dict()["stats"], indent=2)}]
                    },
                    "id": req_id
                }
            
        else:
            return {
                "jsonrpc": "2.0",
                "result": {
                    "isError": True,
                    "content": [{"type": "text", "text": f"Outil '{name}' inconnu."}]
                },
                "id": req_id
            }
            
    except Exception as e:
        err_stack = traceback.format_exc()
        log_error(f"Erreur lors du traitement de {name} : {e}\n{err_stack}")
        return {
            "jsonrpc": "2.0",
            "result": {
                "isError": True,
                "content": [{"type": "text", "text": f"Erreur interne : {e}\n{err_stack}"}]
            },
            "id": req_id
        }

PROMPTS = [
    {
        "name": "mloop_grill_me",
        "description": "Session d'interrogatoire interactive pour clarifier les intentions et exigences métier.",
        "arguments": [{"name": "topic", "description": "Sujet ou fonctionnalité à clarifier", "required": True}]
    },
    {
        "name": "mloop_triage",
        "description": "Triage du backlog et découpage en récits verticaux actionnables (Agent-Ready).",
        "arguments": [{"name": "input_file", "description": "Chemin du fichier ou de la spécification à trier", "required": True}]
    },
    {
        "name": "mloop_vibe_check",
        "description": "Audit de santé pré-vol mLoop (vibe-check).",
        "arguments": [{"name": "project", "description": "Nom du projet mLoop", "required": False}]
    },
    {
        "name": "mloop_handoff",
        "description": "Génération de l'artefact de passage de relais entre sessions.",
        "arguments": [{"name": "summary", "description": "Résumé des travaux réalisés", "required": True}]
    }
]

def handle_prompts_list(req_id: Any) -> Dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "result": {"prompts": PROMPTS},
        "id": req_id
    }

def handle_prompts_get(req_id: Any, params: Dict[str, Any]) -> Dict[str, Any]:
    name = params.get("name")
    args = params.get("arguments", {})
    
    if name == "mloop_grill_me":
        topic = args.get("topic", "le sujet")
        prompt_text = f"Fais un interrogatoire interactif Grill-with-Docs sur le sujet : {topic}. Questionne sur les cas limites, la résilience et les contraintes techniques."
    elif name == "mloop_triage":
        input_file = args.get("input_file", "exigences")
        prompt_text = f"Exécute le skill triage (.agents/skills/triage/SKILL.md) sur le fichier {input_file} pour découper des récits verticaux au gabarit story_template.md."
    elif name == "mloop_vibe_check":
        proj = args.get("project", _SESSION_PROJECT or "mLoop")
        prompt_text = f"Exécute un audit de santé pré-vol vibe-check pour le projet {proj} via python src/swarm.py --project {proj} vibe-check."
    elif name == "mloop_handoff":
        summary = args.get("summary", "Fin de session")
        prompt_text = f"Rédige l'artefact Handoff sous memory/handoff.md avec le résumé : {summary}."
    else:
        return {
            "jsonrpc": "2.0",
            "error": {"code": -32602, "message": f"Prompt '{name}' non reconnu."},
            "id": req_id
        }

    return {
        "jsonrpc": "2.0",
        "result": {
            "description": f"Prompt mLoop {name}",
            "messages": [
                {
                    "role": "user",
                    "content": {"type": "text", "text": prompt_text}
                }
            ]
        },
        "id": req_id
    }

def main():
    global _SESSION_PROJECT
    log_error("Démarrage du serveur MCP stdio Memory Loop Session Memory (Protocole MCP 2026-07-28)...")
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            
            req = json.loads(line)
            method = req.get("method")
            req_id = req.get("id")
            params = req.get("params", {})
            
            # MCP 2026-07-28 : Extraction des métadonnées _meta (State Handle, Traceparent OpenTelemetry)
            _meta = params.get("_meta", {})
            if isinstance(_meta, dict):
                state_handle = _meta.get("stateHandle")
                if state_handle and isinstance(state_handle, str):
                    _SESSION_PROJECT = state_handle.replace("proj_", "").split("_")[0]
                traceparent = _meta.get("traceparent")
                if traceparent:
                    log_error(f"[OpenTelemetry] Traceparent: {traceparent}")
            
            if method == "initialize":
                res = handle_initialize(req_id, params)
            elif method == "server/discover":
                res = handle_server_discover(req_id, params)
            elif method == "tools/list":
                res = handle_tools_list(req_id, params)
            elif method == "tools/call":
                res = handle_tools_call(req_id, params)
            elif method == "prompts/list":
                res = handle_prompts_list(req_id)
            elif method == "prompts/get":
                res = handle_prompts_get(req_id, params)
            elif method == "resources/list":
                res = handle_resources_list(req_id)
            elif method == "resources/read":
                res = handle_resources_read(req_id, params)
            else:
                if req_id is not None:
                    res = {
                        "jsonrpc": "2.0",
                        "error": {
                            "code": -32601,
                            "message": f"Méthode '{method}' non supportée."
                        },
                        "id": req_id
                    }
                else:
                    continue
            
            sys.stdout.write(json.dumps(res) + "\n")
            sys.stdout.flush()
            
        except Exception as e:
            log_error(f"Erreur critique dans la boucle MCP : {e}")

if __name__ == "__main__":
    main()
