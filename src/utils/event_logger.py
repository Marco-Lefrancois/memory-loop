import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List

class EventLogger:
    """
    Enregistreur d'Événements Streaming JSONL mLoop.
    Écrit des événements dans memory/events.jsonl et Projects/<projet>/memory/events.jsonl.
    """

    def __init__(self, project_name: str = "mLoop"):
        self.project_name = project_name
        self.global_log_file = Path("memory") / "events.jsonl"
        self.project_log_file = Path("Projects") / project_name / "memory" / "events.jsonl"
        
        self.global_log_file.parent.mkdir(parents=True, exist_ok=True)
        self.project_log_file.parent.mkdir(parents=True, exist_ok=True)

    def log_event(self, event_type: str, agent_id: str, details: Dict[str, Any], file_attention: Optional[List[str]] = None) -> Dict[str, Any]:
        """Émet un événement au format JSONL."""
        now_iso = datetime.now(timezone.utc).isoformat()
        cwd_str = str(Path.cwd())

        payload = {
            "type": "tool_call",
            "cwd": cwd_str,
            "timestamp": now_iso,
            "event_type": event_type,
            "agent": agent_id,
            "project": self.project_name,
            "details": details,
            "file_attention": file_attention or []
        }

        # Écriture Fichier JSONL
        json_line = json.dumps(payload, ensure_ascii=False) + "\n"
        try:
            with open(self.global_log_file, "a", encoding="utf-8") as f:
                f.write(json_line)
        except Exception:
            pass

        try:
            with open(self.project_log_file, "a", encoding="utf-8") as f:
                f.write(json_line)
        except Exception:
            pass

        return payload

# Singleton global pour un enregistrement facile
_default_logger = None

def get_event_logger(project_name: Optional[str] = None) -> EventLogger:
    global _default_logger
    target_project = project_name or os.getenv("MLOOP_ACTIVE_PROJECT", "mLoop")
    if _default_logger is None or _default_logger.project_name != target_project:
        _default_logger = EventLogger(project_name=target_project)
    return _default_logger
