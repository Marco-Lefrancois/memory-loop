"""
src/dashboard/routers/traces.py — Routeur FastAPI pour les Traces et Délibérations Cognitives.

Expose l'arborescence des spans d'exécution, délibérations <thinking>, invocations d'outils
et critiques contradictoires Sentinel (Rubber Duck Engine).
Conforme ADR-0202 (<300 lignes, <15 Ko) et ADR-0369 (robustesse Python senior).
"""
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Query

from src.dashboard.cache import get_cached_or_compute
from src.dashboard.project_utils import resolve_project_canonical_name

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/traces", tags=["Traces & Cognition"])
REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent


def _resolve_traces_file(project: Optional[str]) -> Path:
    """Résout le chemin du fichier execution_traces.json pour le projet."""
    canon = resolve_project_canonical_name(project)
    if canon and canon not in ("Memory Loop", "mLoop", "global", "ALL", "All"):
        candidate = REPO_ROOT / "Projects" / canon / "memory" / "execution_traces.json"
        if candidate.exists():
            return candidate
    # Fallback mLoop principal
    main_proj = REPO_ROOT / "Projects" / "mLoop" / "memory" / "execution_traces.json"
    if main_proj.exists():
        return main_proj
    return REPO_ROOT / "memory" / "execution_traces.json"


@router.get("/tree")
def get_traces_tree(
    project: Optional[str] = Query(None),
    role: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
) -> Dict[str, Any]:
    """
    Retourne les traces cognitives avec pensée interne (<thinking>), outils et critiques Sentinel.
    """
    target_file = _resolve_traces_file(project)

    def _compute() -> Dict[str, Any]:
        raw_traces: List[Dict[str, Any]] = []
        if target_file.exists():
            try:
                with open(target_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        raw_traces = data
            except Exception as e:
                logger.debug("Erreur de lecture traces", exc_info=True, extra={"error": str(e)})

        # Filtrage par rôle éventuel
        if role:
            raw_traces = [t for t in raw_traces if str(t.get("agent_role")).lower() == role.lower()]

        # Tri antéchronologique (plus récent en premier)
        sorted_traces = list(reversed(raw_traces))[:limit]

        formatted: List[Dict[str, Any]] = []
        stats = {"total_traces": len(raw_traces), "rejected_count": 0, "accepted_count": 0}

        for tr in sorted_traces:
            critique = tr.get("rubber_duck_critique") or {}
            val_res = tr.get("validation_result") or {}
            status = critique.get("status") or ("PASSED" if val_res.get("wikifix_passed") else "NORMAL")

            if status == "REJECTED":
                stats["rejected_count"] += 1
            elif status in ("ACCEPTED", "PASSED"):
                stats["accepted_count"] += 1

            # Extraction du thinking pur sans balises
            thinking = tr.get("thinking_process", "")
            if "<thinking>" in thinking:
                thinking = thinking.replace("<thinking>", "").replace("</thinking>", "").strip()

            formatted.append(
                {
                    "trace_id": tr.get("trace_id", "trc_unknown"),
                    "timestamp": tr.get("timestamp", ""),
                    "agent_role": tr.get("agent_role", "worker"),
                    "event_type": tr.get("event_type", "STEP"),
                    "model_used": tr.get("model_used", "local-harness"),
                    "thinking": thinking,
                    "target_file": (tr.get("prompt_context") or {}).get("file", ""),
                    "rules": (tr.get("prompt_context") or {}).get("rules", []),
                    "tool_calls": tr.get("tool_calls", []),
                    "critique": {
                        "status": status,
                        "blocking_issues": critique.get("blocking_issues") or [],
                        "non_blocking_issues": critique.get("non_blocking_issues") or [],
                        "suggestions": critique.get("suggestions") or [],
                    },
                }
            )

        return {
            "project": project or "mLoop",
            "file_source": target_file.name if target_file.exists() else "none",
            "stats": stats,
            "traces": formatted,
        }

    cache_key = f"traces_{target_file.as_posix()}_{role}_{limit}"
    return get_cached_or_compute(cache_key, target_file, _compute, ttl_seconds=3.0)
