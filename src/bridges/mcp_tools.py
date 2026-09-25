import json
import logging
import re
from pathlib import Path
from typing import Any
from src.loop_mem.db import (
    search_observations, get_session_timeline, get_observation_by_id,
    get_active_project, search_in_memory, search_rho_solution
)
from src.bridges.mcp_ui import attach_ui_meta, notify_ui_project_changed, ui_result

logger = logging.getLogger(__name__)


def _load_kg_edges(project_path: Path) -> list[dict]:
    edges = []
    for rel_path in ["memory/knowledge_graph.json", "graphify-out/graph.json"]:
        fpath = project_path / rel_path
        if fpath.exists():
            try:
                edges.extend(json.loads(fpath.read_text(encoding="utf-8")).get("edges", []))
            except Exception as exc:
                logger.debug(f"Erreur lecture edges {fpath}: {exc}", exc_info=True)
    return edges


def execute_loop_mem_search(arguments: dict, project: str | None) -> str:
    query = arguments.get("query", "")
    proj = arguments.get("project") or project
    obs_type = arguments.get("type")
    results = search_observations(query=query, project_name=proj, obs_type=obs_type)
    output_lines = []
    for r in results:
        scope = f" [{r['file_scope']}]" if r.get("file_scope") else ""
        short_c = r["content"][:120].replace("\n", " ") + "..." if len(r["content"]) > 120 else r["content"]
        output_lines.append(f"ID: #{r['id']} | Type: {r['type'].upper()}{scope} | Date: {r['timestamp']}\n   Résumé: {short_c}")
    if not output_lines:
        return f"ℹ️ Aucune observation trouvée pour '{query}'. Astuce: affinez les termes de recherche."
    return "Index des observations trouvées :\n\n" + "\n\n".join(output_lines)


def execute_loop_mem_code_rag(arguments: dict, active_project: str | None) -> str:
    query = arguments.get("query", "")
    proj = active_project or get_active_project() or "mLoop"
    project_path = Path("Projects") / proj
    results = search_in_memory(project_path, query, limit=5)
    edges = _load_kg_edges(project_path)

    output_blocks = []
    for r in results:
        node_id, label, cat, snippet = r["id"], r["label"], r["category"], r["snippet"]
        neighbors = []
        for edge in edges:
            src = edge.get("source") or edge.get("from")
            tgt = edge.get("target") or edge.get("to")
            rel = edge.get("relation") or edge.get("type") or "related_to"
            if src == node_id and tgt:
                neighbors.append(f"-> ({rel}) -> {tgt}")
            elif tgt == node_id and src:
                neighbors.append(f"<- ({rel}) <- {src}")
        neighbors_str = "\n   Relations 1-hop:\n   " + "\n   ".join(neighbors[:5]) if neighbors else ""
        output_blocks.append(f"--- RAG RESULT: {label} (ID: {node_id}, Catégorie: {cat}, Score: {r['score']:.2f}) ---\nAperçu: {snippet}{neighbors_str}")

    return "\n\n".join(output_blocks) if output_blocks else "Aucun nœud de graphe correspondant trouvé."


def execute_read_skill(arguments: dict) -> str:
    name = arguments.get("skill_name", "").strip()
    candidates = [Path(".agents/skills") / name / "SKILL.md", Path("standards/skills") / name / "SKILL.md"]
    for cand in candidates:
        if cand.exists():
            return cand.read_text(encoding="utf-8")
    return f"Compétence '{name}' introuvable sous .agents/skills ou standards/skills."


def execute_story_compliance(arguments: dict) -> str:
    content = arguments.get("content", "")
    issues, warnings = [], []
    scenarios = re.findall(r"(?:Scénario|Scenario)\s*:", content, re.IGNORECASE)
    if len(scenarios) < 4:
        issues.append(f"❌ [ADR-0301] Gherkin 4-Piliers incomplet : {len(scenarios)}/4 scénarios.")
    else:
        warnings.append(f"✅ [ADR-0301] Gherkin 4-Piliers : {len(scenarios)} scénarios détectés.")
    if not re.search(r"## Scénarios de test", content, re.IGNORECASE):
        issues.append("❌ Section '## Scénarios de test' manquante.")
    if not re.search(r"## Règles d", content, re.IGNORECASE):
        issues.append("❌ Section '## Règles d'affaires' manquante.")
    for kw in ["npm install", "yarn add", "expo install", "import {", "zustand", "redux"]:
        if kw in content.lower():
            issues.append(f"⚠️ Fuite technique détectée : `{kw}`.")
    sym = "🟢 CONFORME" if not issues else "🔴 NON CONFORME"
    res = f"### Rapport de Conformité Story ({sym})\n\n"
    if issues:
        res += "#### Problèmes :\n" + "\n".join([f"- {i}" for i in issues]) + "\n\n"
    if warnings:
        res += "#### Points validés :\n" + "\n".join([f"- {w}" for w in warnings])
    return res


def _load_tools_yaml_manifest() -> dict[str, list[str]]:
    manifest_path = Path("tools.yaml")
    if not manifest_path.exists():
        return {}
    try:
        import yaml
        content = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
        toolsets = {}
        for ts in content.get("toolsets", []):
            if isinstance(ts, dict) and "name" in ts:
                toolsets[ts["name"].upper()] = ts.get("tools", [])
        return toolsets
    except Exception as exc:
        logger.debug(f"Erreur chargement tools.yaml : {exc}", exc_info=True)
    return {}


def get_tools_definitions() -> list[dict]:
    return [
        {
            "name": "loop_mem_search",
            "phase": "PLAN",
            "description": "Recherche dans la mémoire persistante SQLite FTS5 (index condensé).",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Terme ou phrase textuelle FTS5."},
                    "project": {"type": "string", "description": "Nom du projet."},
                    "type": {"type": "string", "enum": ["decision", "bugfix", "feature", "discovery"]},
                },
                "required": ["query"],
            },
        },
        {
            "name": "loop_mem_code_rag",
            "phase": "BUILD",
            "description": "Recherche sémantique de code source avec expansion 1-hop dans le graphe de connaissances.",
            "inputSchema": {
                "type": "object",
                "properties": {"query": {"type": "string", "description": "Description du composant recherché."}},
                "required": ["query"],
            },
        },
        {
            "name": "read_skill",
            "phase": "SPEC",
            "description": "Lit la documentation complète d'une compétence agent (Standard SEP-2640).",
            "inputSchema": {
                "type": "object",
                "properties": {"skill_name": {"type": "string", "description": "Nom de la compétence (ex: 'triage')."}},
                "required": ["skill_name"],
            },
        },
        {
            "name": "check_story_compliance",
            "phase": "VALIDATE",
            "description": "Vérifie la conformité INVEST et 4 Piliers Gherkin d'un récit markdown.",
            "inputSchema": {
                "type": "object",
                "properties": {"content": {"type": "string", "description": "Contenu Markdown du récit."}},
                "required": ["content"],
            },
        },
        {
            "name": "loop_mem_timeline",
            "phase": "PLAN",
            "description": "Récupère la timeline chronologique condensée des observations.",
            "inputSchema": {
                "type": "object",
                "properties": {"project": {"type": "string", "description": "Nom du projet."}},
                "required": ["project"],
            },
        },
        {
            "name": "loop_mem_set_project",
            "phase": "SPEC",
            "description": "Définit le projet actif de session courante.",
            "inputSchema": {
                "type": "object",
                "properties": {"project": {"type": "string", "description": "Nom du projet."}},
                "required": ["project"],
            },
        },
        {
            "name": "show_architecture",
            "phase": "PLAN",
            "description": "Affiche le cockpit d'architecture Archify du projet dans un cadre MCP Apps lecture-seule (ressource ui://archify/cockpit).",
            "inputSchema": {"type": "object", "properties": {"project": {"type": "string", "description": "Nom du projet (defaut : projet actif)."}}, "required": []},
        },
        {
            "name": "show_database_schema",
            "phase": "PLAN",
            "description": "Affiche le schema relationnel DrawDB du projet dans un cadre MCP Apps lecture-seule (ressource ui://drawdb/schema).",
            "inputSchema": {"type": "object", "properties": {"project": {"type": "string", "description": "Nom du projet (defaut : projet actif)."}}, "required": []},
        },
    ]


def handle_tools_list(req_id: Any, params: dict | None = None) -> dict:
    params = params or {}
    _meta = params.get("_meta", {})
    phase_filter = (params.get("phase") or _meta.get("phase") or "").upper()
    manifest_toolsets = _load_tools_yaml_manifest()

    tools = [dict(t) for t in get_tools_definitions()]
    if phase_filter:
        allowed_names = manifest_toolsets.get(phase_filter, [])
        if allowed_names:
            tools = [t for t in tools if t.get("name") in allowed_names or t.get("phase") == phase_filter]
        else:
            tools = [t for t in tools if t.get("phase") == phase_filter]

    for t in tools:
        t.pop("phase", None)

    # Liaison outil -> ressource MCP Apps (SEP-1865, MLOOP-212-FE) : `_meta.ui.resourceUri`.
    attach_ui_meta(tools)

    tools.sort(key=lambda t: t["name"])
    return {"jsonrpc": "2.0", "result": {"tools": tools, "ttlMs": 300000}, "id": req_id}


def handle_tools_call(req_id: Any, params: dict, session_project: str | None) -> tuple[dict, str | None]:
    name = params.get("name")
    args = params.get("arguments", {})
    updated_proj = session_project

    try:
        if name == "loop_mem_set_project":
            updated_proj = args.get("project")
            text = f"✅ Projet actif de session: **{updated_proj}**"
            notify_ui_project_changed(updated_proj)
        elif name in ("show_architecture", "show_database_schema"):
            # Cadre MCP Apps : texte toujours significatif ; `_meta.ui` si capacite negociee (jamais isError).
            target = args.get("project") or session_project or "mLoop"
            text, ui_meta = ui_result(name, target)
            result: dict = {"content": [{"type": "text", "text": text}]}
            if ui_meta:
                result["_meta"] = ui_meta
            return {"jsonrpc": "2.0", "result": result, "id": req_id}, session_project
        elif name == "loop_mem_search":
            text = execute_loop_mem_search(args, session_project)
        elif name == "loop_mem_code_rag":
            text = execute_loop_mem_code_rag(args, session_project)
        elif name == "read_skill":
            text = execute_read_skill(args)
        elif name == "check_story_compliance":
            text = execute_story_compliance(args)
        elif name == "loop_mem_timeline":
            proj = args.get("project") or session_project or "mLoop"
            tl = get_session_timeline(project_name=proj)
            text = "\n\n".join([f"#{r['id']} [{r['type']}] {r['timestamp']}: {r['content'][:100]}" for r in tl]) if tl else "Aucun historique."
        else:
            return {"jsonrpc": "2.0", "result": {"isError": True, "content": [{"type": "text", "text": f"Outil '{name}' inconnu."}]}, "id": req_id}, updated_proj

        return {"jsonrpc": "2.0", "result": {"content": [{"type": "text", "text": text}]}, "id": req_id}, updated_proj
    except Exception as exc:
        logger.debug(f"Erreur tools/call {name}: {exc}", exc_info=True)
        return {"jsonrpc": "2.0", "result": {"isError": True, "content": [{"type": "text", "text": f"Erreur interne: {exc}"}]}, "id": req_id}, updated_proj
