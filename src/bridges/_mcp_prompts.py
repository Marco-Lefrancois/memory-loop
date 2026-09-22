"""Gestionnaires MCP prompts (MLOOP-145-BE — extraction ADR-0202 depuis mcp_loop_mem)."""

from __future__ import annotations

from typing import Any

PROMPTS = [
    {"name": "mloop_grill_me", "description": "Session d'interrogatoire Grill-with-Docs."},
    {"name": "mloop_triage", "description": "Triage du backlog et découpage en récits."},
    {"name": "mloop_vibe_check", "description": "Audit de santé pré-vol mLoop."},
    {"name": "mloop_handoff", "description": "Génération de l'artefact de passage de relais."},
]


def handle_prompts_list(req_id: Any) -> dict:
    return {"jsonrpc": "2.0", "result": {"prompts": PROMPTS}, "id": req_id}


def handle_prompts_get(req_id: Any, params: dict, session_project: str | None = None) -> dict:
    name = params.get("name")
    args = params.get("arguments", {})
    if name == "mloop_grill_me":
        text = f"Clarification interactive Grill-with-Docs sur: {args.get('topic', 'le sujet')}."
    elif name == "mloop_triage":
        text = f"Triage du fichier {args.get('input_file', 'exigences')} vers story_template.md."
    elif name == "mloop_vibe_check":
        proj = args.get("project", session_project or "mLoop")
        text = f"Audit pré-vol vibe-check pour {proj}."
    elif name == "mloop_handoff":
        text = f"Rédige memory/handoff.md avec le résumé: {args.get('summary', 'Fin de session')}."
    else:
        return {
            "jsonrpc": "2.0",
            "error": {"code": -32602, "message": f"Prompt '{name}' inconnu."},
            "id": req_id,
        }
    return {
        "jsonrpc": "2.0",
        "result": {
            "description": f"Prompt {name}",
            "messages": [{"role": "user", "content": {"type": "text", "text": text}}],
        },
        "id": req_id,
    }
