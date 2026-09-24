"""
Candidat A : Implémentation Standard Library Pure du Normaliseur OpenInference / OTel GenAI (MLOOP-072-BE).
Zéro dépendance externe, thread-safe (threading.Lock), conforme ADR-0202, ADR-0369 et ADR-0380.
"""
from __future__ import annotations

import json
import logging
import os
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

CANONICAL_SPANS = {"AGENT", "TOOL", "LLM", "CHAIN"}


class EventLogger:
    """Enregistreur d'événements streaming JSONL normalisé OpenInference / OTel GenAI."""

    def __init__(self, project_name: str = "mLoop", base_dir: Optional[Path] = None) -> None:
        self.project_name = project_name
        self.base_dir = Path(base_dir) if base_dir else Path(".")
        self.global_log_file = self.base_dir / "memory" / "events.jsonl"
        self.project_log_file = self.base_dir / "Projects" / project_name / "memory" / "events.jsonl"
        self._lock = threading.Lock()

        self.global_log_file.parent.mkdir(parents=True, exist_ok=True)
        self.project_log_file.parent.mkdir(parents=True, exist_ok=True)

    def _normalize_span_kind(self, raw_kind: str) -> tuple[str, Optional[str]]:
        """Mappe le type d'événement vers les 4 types canoniques OpenInference avec repli résilient."""
        cleaned = str(raw_kind).strip().upper()
        if cleaned in CANONICAL_SPANS:
            return cleaned, None

        lower = str(raw_kind).lower()
        if "tool" in lower:
            return "TOOL", None
        elif "llm" in lower or "chat" in lower or "model" in lower:
            return "LLM", None
        elif "agent" in lower:
            return "AGENT", None
        return "CHAIN", raw_kind

    def log_event(
        self,
        span_kind: str,
        agent_id: str,
        details: Optional[Dict[str, Any]] = None,
        file_attention: Optional[List[str]] = None,
        model: Optional[str] = None,
        tokens: Optional[Dict[str, int]] = None,
        trace_id: Optional[str] = None,
        parent_span_id: Optional[str] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Émet un span normalisé au format OpenInference / OTel GenAI."""
        normalized_kind, original_type = self._normalize_span_kind(span_kind)
        resolved_details = dict(details) if details else {}
        if original_type:
            resolved_details["original_event_type"] = original_type

        now_iso = datetime.now(timezone.utc).isoformat()
        resolved_trace_id = trace_id if (trace_id and len(trace_id) == 32) else uuid.uuid4().hex
        current_span_id = uuid.uuid4().hex[:16]

        payload: Dict[str, Any] = {
            "trace_id": resolved_trace_id,
            "span_id": current_span_id,
            "parent_span_id": parent_span_id,
            "timestamp": now_iso,
            "openinference.span.kind": normalized_kind,
            "gen_ai.system": "mloop",
            "gen_ai.agent.name": agent_id,
            "project": self.project_name,
            "details": resolved_details,
            "file_attention": file_attention or [],
        }

        if model:
            payload["gen_ai.request.model"] = model
        if tokens:
            payload["gen_ai.usage.input_tokens"] = tokens.get("input", 0)
            payload["gen_ai.usage.output_tokens"] = tokens.get("output", 0)
            payload["gen_ai.usage.total_tokens"] = tokens.get("total", 0)

        # Sérialisation atomique avec verrou thread-safe
        json_line = json.dumps(payload, ensure_ascii=False) + "\n"
        with self._lock:
            for target_file in (self.global_log_file, self.project_log_file):
                try:
                    if target_file.exists() and target_file.stat().st_size >= 5 * 1024 * 1024:
                        from src.commands.handlers.log_rotation import rotate_single_log
                        rotate_single_log(target_file, max_bytes=5 * 1024 * 1024)
                    with open(target_file, "a", encoding="utf-8") as f:
                        f.write(json_line)
                except OSError as e:
                    logger.debug("Échec écriture log JSONL sur %s : %s", target_file, e, exc_info=True)

        return payload

    def query_events(
        self,
        filter_kind: Optional[str] = None,
        agent_id: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Interroge les événements locaux par ordre antéchronologique."""
        source_file = self.project_log_file if self.project_log_file.exists() else self.global_log_file
        if not source_file.exists():
            return []

        events: List[Dict[str, Any]] = []
        with self._lock:
            try:
                with open(source_file, "r", encoding="utf-8") as f:
                    lines = f.readlines()
            except OSError as e:
                logger.debug("Échec lecture fichier log %s : %s", source_file, e, exc_info=True)
                return []

        # Parcourir à l'envers (les plus récents en premier)
        for raw in reversed(lines):
            line = raw.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError as e:
                logger.debug("Ligne JSONL corrompue ignorée : %s", e, exc_info=True)
                continue

            # Filtrage
            if filter_kind and data.get("openinference.span.kind") != filter_kind:
                continue
            if agent_id and data.get("gen_ai.agent.name") != agent_id:
                continue

            events.append(data)
            if len(events) >= limit:
                break

        return events


_default_logger: Optional[EventLogger] = None


def get_event_logger(project_name: Optional[str] = None) -> EventLogger:
    """Singleton global résilient pour l'enregistrement d'événements."""
    global _default_logger
    target_project = project_name or os.getenv("MLOOP_ACTIVE_PROJECT", "mLoop")
    if _default_logger is None or _default_logger.project_name != target_project:
        _default_logger = EventLogger(project_name=target_project)
    return _default_logger
