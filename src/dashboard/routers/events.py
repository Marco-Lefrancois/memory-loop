# -*- coding: utf-8 -*-
"""
src/dashboard/routers/events.py — Routeur FastAPI pour les événements et le streaming SSE en temps réel.
Conforme ADR-0202 (<=300 lignes, <=15 Ko) et ADR-0369 (robustesse Python senior).
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

from src.dashboard.module_utils import match_module_entry
from src.dashboard.project_utils import (
    match_project_alias as _match_project_alias,
    resolve_project_canonical_name as _resolve_project_canonical_name,
    resolve_project_path as _get_project_root,
)
from src.utils.logger import get_logger

logger = get_logger("dashboard.routers.events")
REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent

router = APIRouter(tags=["Événements & SSE"])


@router.get("/api/events")
def get_events(
    project: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500),
    event_type: Optional[str] = None,
    module: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Retourne le journal live des événements récents depuis events.jsonl.
    """
    target_project = _resolve_project_canonical_name(project)
    p_root = _get_project_root(target_project)

    events_files: List[tuple[Path, bool]] = []

    if p_root != REPO_ROOT:
        p_events = p_root / "memory" / "events.jsonl"
        if p_events.exists():
            events_files.append((p_events, True))

    global_events = REPO_ROOT / "memory" / "events.jsonl"
    if global_events.exists():
        events_files.append((global_events, False))

    raw_events = []
    seen = set()

    for ef, is_dedicated in events_files:
        try:
            with open(ef, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        ev = json.loads(line)
                        if not is_dedicated and target_project not in (
                            "Memory Loop",
                            "mLoop",
                            "global",
                            "All",
                            "ALL",
                            "*",
                        ):
                            if not _match_project_alias(ev.get("project", ""), target_project):
                                continue

                        if event_type and event_type != "ALL":
                            if ev.get("event_type", "").upper() != event_type.upper():
                                continue

                        if module and module.upper() not in ("ALL", "*", "TOUS"):
                            details_str = str(ev.get("details", ""))
                            target_str = str(ev.get("target", ""))
                            if not match_module_entry(
                                target_str, module, [details_str, str(ev.get("file_attention", ""))]
                            ):
                                continue

                        fp = f"{ev.get('timestamp')}_{ev.get('event_type')}_{ev.get('agent')}_{str(ev.get('details'))[:40]}"
                        if fp in seen:
                            continue
                        seen.add(fp)
                        raw_events.append(ev)
                    except Exception as e:
                        logger.debug(
                            "Événement JSONL illisible dans events.jsonl, ligne ignorée",
                            exc_info=True,
                            extra={
                                "component": "dashboard.routers.events",
                                "operation": "get_events",
                                "events_path": str(ef),
                                "error": str(e),
                            },
                        )
                        continue
        except Exception as e:
            logger.warning(
                "Lecture de events.jsonl échouée, journal d'événements incomplet",
                exc_info=True,
                extra={
                    "component": "dashboard.routers.events",
                    "operation": "get_events",
                    "events_path": str(ef),
                    "error": str(e),
                },
            )

    raw_events.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    selected = raw_events[:limit]

    return {
        "project": target_project,
        "count": len(selected),
        "total_captured": len(raw_events),
        "events": selected,
    }


@router.get("/api/stream/events")
async def stream_events(
    project: Optional[str] = None,
    event_type: Optional[str] = None,
    module: Optional[str] = None,
):
    """
    Stream SSE (Server-Sent Events) pour l'Event Bus mLoop en temps réel (ST-112).
    Diffuse les événements au fur et à mesure de leur écriture dans memory/events.jsonl.
    """
    target_project = _resolve_project_canonical_name(project)

    async def event_generator():
        # 1. Événement initial : 40 derniers événements
        initial_res = get_events(
            project=target_project, limit=40, event_type=event_type, module=module
        )
        initial_list = list(reversed(initial_res.get("events", [])))
        yield f"event: initial\ndata: {json.dumps(initial_list, ensure_ascii=False)}\n\n"

        events_file = REPO_ROOT / "memory" / "events.jsonl"
        last_pos = events_file.stat().st_size if events_file.exists() else 0
        seen_fp = set()
        for ev in initial_list:
            fp = f"{ev.get('timestamp')}_{ev.get('event_type')}_{ev.get('agent')}_{str(ev.get('details'))[:40]}"
            seen_fp.add(fp)

        heartbeat_counter = 0
        try:
            while True:
                await asyncio.sleep(0.5)
                heartbeat_counter += 1

                if heartbeat_counter >= 30:  # ~15s ping
                    yield ": keepalive\n\n"
                    heartbeat_counter = 0

                if not events_file.exists():
                    continue

                curr_size = events_file.stat().st_size
                if curr_size < last_pos:
                    last_pos = 0

                if curr_size > last_pos:
                    try:
                        with open(events_file, "r", encoding="utf-8", errors="ignore") as f:
                            f.seek(last_pos)
                            new_lines = f.readlines()
                            last_pos = f.tell()

                        for line in new_lines:
                            line = line.strip()
                            if not line:
                                continue
                            try:
                                ev = json.loads(line)
                                entry_proj = ev.get("project", "")
                                if target_project not in (
                                    "Memory Loop",
                                    "mLoop",
                                    "global",
                                    "All",
                                    "ALL",
                                    "*",
                                ):
                                    if not _match_project_alias(entry_proj, target_project):
                                        continue

                                if event_type and event_type != "ALL":
                                    if ev.get("event_type", "").upper() != event_type.upper():
                                        continue

                                if module and module.upper() not in ("ALL", "*", "TOUS"):
                                    details_str = str(ev.get("details", ""))
                                    target_str = str(ev.get("target", ""))
                                    if not match_module_entry(
                                        target_str,
                                        module,
                                        [details_str, str(ev.get("file_attention", ""))],
                                    ):
                                        continue

                                fp = f"{ev.get('timestamp')}_{ev.get('event_type')}_{ev.get('agent')}_{str(ev.get('details'))[:40]}"
                                if fp in seen_fp:
                                    continue
                                seen_fp.add(fp)

                                yield f"event: message\ndata: {json.dumps(ev, ensure_ascii=False)}\n\n"
                            except Exception as e:
                                logger.debug(
                                    "Événement SSE JSONL illisible, ligne ignorée",
                                    exc_info=True,
                                    extra={
                                        "component": "dashboard.routers.events",
                                        "operation": "stream_events",
                                        "events_path": str(events_file),
                                        "error": str(e),
                                    },
                                )
                                continue
                    except Exception as e:
                        logger.warning(
                            "Lecture incrémentale de events.jsonl échouée, flux SSE suspendu pour ce cycle",
                            exc_info=True,
                            extra={
                                "component": "dashboard.routers.events",
                                "operation": "stream_events",
                                "events_path": str(events_file),
                                "error": str(e),
                            },
                        )
        except asyncio.CancelledError:
            logger.debug(
                "Flux SSE d'événements annulé par le client",
                extra={"component": "dashboard.routers.events", "operation": "stream_events"},
            )

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
