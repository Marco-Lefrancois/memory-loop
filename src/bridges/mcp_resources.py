import json
import logging
from pathlib import Path
from typing import Any
from src.loop_mem.db import search_observations, get_observation_by_id, get_active_project
from src.bridges._mcp_skills_rules import arbitrate_skill
from src.bridges.mcp_ui import list_ui_resources, read_ui_resource

logger = logging.getLogger(__name__)


def discover_skills() -> list[dict]:
    """Découvre les compétences sous .agents/skills et standards/skills (Standard SEP-2640)."""
    skills = []
    seen = set()
    search_dirs = [Path(".agents/skills"), Path("standards/skills")]
    for base_dir in search_dirs:
        if not base_dir.exists():
            continue
        for child in base_dir.iterdir():
            if child.is_dir():
                skill_md = child / "SKILL.md"
                if skill_md.exists() and child.name not in seen:
                    seen.add(child.name)
                    desc = f"Compétence agent '{child.name}'"
                    try:
                        first_lines = skill_md.read_text(encoding="utf-8").splitlines()[:5]
                        for line in first_lines:
                            if line.startswith("# "):
                                desc = line.replace("# ", "").strip()
                                break
                    except Exception as exc:
                        logger.debug(
                            f"Erreur lecture header skill {child.name}: {exc}", exc_info=True
                        )
                    skills.append({"name": child.name, "path": skill_md, "description": desc})
    return skills


def handle_resources_list(req_id: Any, session_project: str | None = None) -> dict:
    """Expose observations, Graphify nodes, ADRs et compétences SEP-2640 skill://."""
    project = session_project or get_active_project()
    resources = []
    if project:
        try:
            observations = search_observations(query="", project_name=project) or []
            for obs in observations[:20]:
                resources.append(
                    {
                        "uri": f"mloop://project/{project}/observation/{obs['id']}",
                        "name": f"[{obs['type'].upper()}] {obs['content'][:60]}...",
                        "mimeType": "text/plain",
                        "description": f"Observation #{obs['id']} du projet {project} ({obs['timestamp']})",
                    }
                )
        except Exception as exc:
            logger.debug(f"Erreur lecture observations list: {exc}", exc_info=True)

    graph_file = Path("graphify-out/graph.json")
    if graph_file.exists():
        resources.append(
            {
                "uri": "graphify://graph/summary",
                "name": "Graphify Knowledge Graph Summary",
                "mimeType": "application/json",
                "description": "Résumé du graphe de connaissances Graphify",
            }
        )

    # Standard SEP-2640 : Exposition des compétences via skill://
    for sk in discover_skills():
        resources.append(
            {
                "uri": f"skill://{sk['name']}",
                "name": f"Skill: {sk['name']}",
                "mimeType": "text/markdown",
                "description": sk["description"],
            }
        )

    # Extension MCP Apps (MLOOP-212-FE) : 2 ressources ui:// pre-declarees (SEP-1865).
    resources.extend(list_ui_resources())

    return {"jsonrpc": "2.0", "result": {"resources": resources}, "id": req_id}


def _read_skill_resource(uri: str, req_id: Any) -> dict:
    # SEP-2640 : le nom de compétence s'obtient en retirant le schéma et, le cas
    # échéant, le suffixe canonique `/SKILL.md` (les deux formes restent servies).
    skill_name = uri.replace("skill://", "").strip("/")
    if skill_name.endswith("/SKILL.md"):
        skill_name = skill_name[: -len("/SKILL.md")]
    candidates = [
        Path(".agents/skills") / skill_name / "SKILL.md",
        Path("standards/skills") / skill_name / "SKILL.md",
    ]
    for cand in candidates:
        if cand.exists():
            try:
                content = cand.read_text(encoding="utf-8")
            except Exception as exc:
                logger.debug(f"Erreur lecture skill {cand}: {exc}", exc_info=True)
                return {
                    "jsonrpc": "2.0",
                    "result": {
                        "isError": True,
                        "content": [
                            {"type": "text", "text": f"Erreur de lecture de la compétence : {exc}"}
                        ],
                    },
                    "id": req_id,
                }
            # Hiérarchie stricte (MLOOP-214-BE) : conflits tracés, contenu intact.
            arbitrate_skill(skill_name, content, bridge="resources")
            return {
                "jsonrpc": "2.0",
                "result": {
                    "contents": [{"uri": uri, "mimeType": "text/markdown", "text": content}]
                },
                "id": req_id,
            }
    return {
        "jsonrpc": "2.0",
        "result": {
            "isError": True,
            "content": [
                {
                    "type": "text",
                    "text": f"Compétence '{skill_name}' introuvable sous .agents/skills ou standards/skills.",
                }
            ],
        },
        "id": req_id,
    }


def _read_graphify_node(uri: str, req_id: Any) -> dict:
    node_name = uri.replace("graphify://node/", "")
    graph_file = Path("graphify-out/graph.json")
    if not graph_file.exists():
        return {
            "jsonrpc": "2.0",
            "result": {
                "isError": True,
                "content": [
                    {
                        "type": "text",
                        "text": "Le graphe 'graphify-out/graph.json' n'existe pas encore.",
                    }
                ],
            },
            "id": req_id,
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
                "result": {
                    "contents": [
                        {
                            "uri": uri,
                            "mimeType": "application/json",
                            "text": json.dumps(matched, indent=2, ensure_ascii=False),
                        }
                    ]
                },
                "id": req_id,
            }
        return {
            "jsonrpc": "2.0",
            "result": {
                "isError": True,
                "content": [
                    {"type": "text", "text": f"Nœud '{node_name}' introuvable dans le graphe."}
                ],
            },
            "id": req_id,
        }
    except Exception as exc:
        logger.debug(f"Erreur lecture node graphify: {exc}", exc_info=True)
        return {
            "jsonrpc": "2.0",
            "result": {
                "isError": True,
                "content": [{"type": "text", "text": f"Erreur Graphify: {exc}"}],
            },
            "id": req_id,
        }


def _read_adr_or_story(uri: str, req_id: Any, session_project: str | None) -> dict:
    if uri.startswith("loopmem://adr/"):
        adr_id = uri.replace("loopmem://adr/", "")
        adr_dir = Path("docs/01-architecture")
        matches = list(adr_dir.glob(f"*{adr_id}*.md")) if adr_dir.exists() else []
        if matches:
            return {
                "jsonrpc": "2.0",
                "result": {
                    "contents": [
                        {
                            "uri": uri,
                            "mimeType": "text/markdown",
                            "text": matches[0].read_text(encoding="utf-8"),
                        }
                    ]
                },
                "id": req_id,
            }
        return {
            "jsonrpc": "2.0",
            "result": {
                "isError": True,
                "content": [{"type": "text", "text": f"ADR #{adr_id} introuvable."}],
            },
            "id": req_id,
        }

    story_id = uri.replace("loopmem://story/", "")
    project = session_project or get_active_project() or "mLoop"
    story_dir = Path("Projects") / project / "backlog" / "stories"
    matches = list(story_dir.glob(f"*{story_id}*.md")) if story_dir.exists() else []
    if matches:
        return {
            "jsonrpc": "2.0",
            "result": {
                "contents": [
                    {
                        "uri": uri,
                        "mimeType": "text/markdown",
                        "text": matches[0].read_text(encoding="utf-8"),
                    }
                ]
            },
            "id": req_id,
        }
    return {
        "jsonrpc": "2.0",
        "result": {
            "isError": True,
            "content": [{"type": "text", "text": f"Récit #{story_id} introuvable."}],
        },
        "id": req_id,
    }


def handle_resources_read(req_id: Any, params: dict, session_project: str | None = None) -> dict:
    """Fetch full content of a resource (ui://, skill://, graphify://, loopmem://, mloop://)."""
    uri = params.get("uri", "")
    ui = read_ui_resource(uri, session_project)
    if ui is not None:
        if ui.get("ok"):
            return {"jsonrpc": "2.0", "result": {"contents": [ui["content"]]}, "id": req_id}
        return {
            "jsonrpc": "2.0",
            "result": {"isError": True, "content": [{"type": "text", "text": ui["message"]}]},
            "id": req_id,
        }
    if uri.startswith("skill://"):
        return _read_skill_resource(uri, req_id)
    if uri.startswith("graphify://node/"):
        return _read_graphify_node(uri, req_id)
    if uri.startswith("loopmem://adr/") or uri.startswith("loopmem://story/"):
        return _read_adr_or_story(uri, req_id, session_project)

    try:
        parts = uri.replace("mloop://project/", "").split("/observation/")
        obs_id = int(parts[-1])
        obs = get_observation_by_id(obs_id)
        if not obs:
            return {
                "jsonrpc": "2.0",
                "result": {
                    "isError": True,
                    "content": [{"type": "text", "text": f"Observation #{obs_id} introuvable."}],
                },
                "id": req_id,
            }
        file_scope_str = f"\nFichiers : {obs['file_scope']}" if obs.get("file_scope") else ""
        content = f"OBSERVATION #{obs['id']} ({obs['type'].upper()})\nProjet : {obs['project_name']} | Date : {obs['timestamp']}{file_scope_str}\n{'-' * 40}\n{obs['content']}"
        return {
            "jsonrpc": "2.0",
            "result": {"contents": [{"uri": uri, "mimeType": "text/plain", "text": content}]},
            "id": req_id,
        }
    except Exception as exc:
        logger.debug(f"Erreur lecture URI {uri}: {exc}", exc_info=True)
        return {
            "jsonrpc": "2.0",
            "result": {
                "isError": True,
                "content": [{"type": "text", "text": f"URI non reconnue ou invalide: {uri}"}],
            },
            "id": req_id,
        }
