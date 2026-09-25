"""
Candidat B : Implémentation Étendue du Normaliseur OpenInference / OTel GenAI (MLOOP-072-BE).
Comporte une couche de validation défensive des schémas de tokens et compteurs de débit.
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

CANONICAL_SPANS = frozenset({"AGENT", "TOOL", "LLM", "CHAIN"})


class EventLogger:
    """Enregistreur d'événements étendu avec compteurs et validation défensive."""

    def __init__(self, project_name: str = "mLoop", base_dir: Optional[Path] = None) -> None:
        self.project_name = project_name
        self.base_dir = Path(base_dir) if base_dir else Path(".")
        self.global_log_file = self.base_dir / "memory" / "events.jsonl"
        self.project_log_file = self.base_dir / "Projects" / project_name / "memory" / "events.jsonl"
        self._lock = threading.RLock()
        self._emitted_count: int = 0

        self.global_log_file.parent.mkdir(parents=True, exist_ok=True)
        self.project_log_file.parent.mkdir(parents=True, exist_ok=True)

    def _normalize_span_kind(self, raw_kind: str) -> tuple[str, Optional[str]]:
        candidate = str(raw_kind).strip().upper()
        if candidate in CANONICAL_SPANS:
            return candidate, None

        low = str(raw_kind).lower()
        if "tool" in low:
            return "TOOL", None
        if "llm" in low or "chat" in low or "gpt" in low or "gemini" in low:
            return "LLM", None
        if "agent" in low or "swarm" in low:
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
        """Émet un span structuré avec validation défensive."""
        norm_kind, orig_type = self._normalize_span_kind(span_kind)
        det = dict(details) if details is not None else {}
        if orig_type is not None:
            det["original_event_type"] = orig_type

        timestamp_str = datetime.now(timezone.utc).isoformat()
        t_id = trace_id if (trace_id and len(trace_id) == 32) else uuid.uuid4().hex
        s_id = uuid.uuid4().hex[:16]

        payload: Dict[str, Any] = {
            "trace_id": t_id,
            "span_id": s_id,
            "parent_span_id": parent_span_id,
            "timestamp": timestamp_str,
            "openinference.span.kind": norm_kind,
            "gen_ai.system": "mloop",
            "gen_ai.agent.name": str(agent_id),
            "project": self.project_name,
            "details": det,
            "file_attention": list(file_attention) if file_attention else [],
        }

        if model is not None:
            payload["gen_ai.request.model"] = str(model)

        if isinstance(tokens, dict):
            inp = int(tokens.get("input", 0))
            out = int(tokens.get("output", 0))
            tot = int(tokens.get("total", inp + out))
            payload["gen_ai.usage.input_tokens"] = inp
            payload["gen_ai.usage.output_tokens"] = out
            payload["gen_ai.usage.total_tokens"] = tot

        line_to_write = json.dumps(payload, ensure_ascii=False) + "\n"

        with self._lock:
            self._emitted_count += 1
            for path_target in [self.global_log_file, self.project_log_file]:
                try:
                    with open(path_target, "a", encoding="utf-8") as out_fp:
                        out_fp.write(line_to_write)
                except OSError as err:
                    logger.debug("Écriture événement échouée sur %s : %s", path_target, err, exc_info=True)

        return payload

    def query_events(
        self,
        filter_kind: Optional[str] = None,
        agent_id: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Lit et filtre les événements dans l'ordre antéchronologique."""
        target_src = self.project_log_file if self.project_log_file.exists() else self.global_log_file
        if not target_src.exists():
            return []

        with self._lock:
            try:
                with open(target_src, "r", encoding="utf-8") as in_fp:
                    file_lines = in_fp.readlines()
            except OSError as err:
                logger.debug("Lecture événements impossible sur %s : %s", target_src, err, exc_info=True)
                return []

        results: List[Dict[str, Any]] = []
        for raw_entry in reversed(file_lines):
            stripped = raw_entry.strip()
            if not stripped:
                continue
            try:
                item = json.loads(stripped)
            except json.JSONDecodeError as dec_err:
                logger.debug("Ligne JSON non parsable : %s", dec_err, exc_info=True)
                continue

            if filter_kind and item.get("openinference.span.kind") != filter_kind:
                continue
            if agent_id and item.get("gen_ai.agent.name") != agent_id:
                continue

            results.append(item)
            if len(results) >= limit:
                break

        return results


_default_logger: Optional[EventLogger] = None


def get_event_logger(project_name: Optional[str] = None) -> EventLogger:
    """Accesseur Singleton résilient."""
    global _default_logger
    active_name = project_name or os.getenv("MLOOP_ACTIVE_PROJECT", "mLoop")
    if _default_logger is None or _default_logger.project_name != active_name:
        _default_logger = EventLogger(project_name=active_name)
    return _default_logger
