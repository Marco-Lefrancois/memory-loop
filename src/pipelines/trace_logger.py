import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional

class ExecutionTraceLogger:
    """
    Enregistreur de traces d'exécution agentique exhaustif pour mLoop.
    Double niveau de persistance (Local Projet SSOT sous memory/execution_traces.json et Global Systémique).
    Consigne l'intégralité du raisonnement (<thinking>), des prompts et du contexte sans angle mort.
    """

    def __init__(self, project_path: Optional[Path] = None, project_name: Optional[str] = None):
        self.project_path = project_path
        self.project_name = project_name or (project_path.name if project_path else "default")
        
        # Persistance Niveau Projet (SSOT)
        if self.project_path:
            self.project_trace_file = self.project_path / "memory" / "execution_traces.json"
        else:
            self.project_trace_file = Path("Projects") / self.project_name / "memory" / "execution_traces.json"
            
        # Persistance Globale mLoop (Loop 4)
        self.global_trace_file = Path("memory/global_execution_traces.json")
        
        self.project_trace_file.parent.mkdir(parents=True, exist_ok=True)
        self.global_trace_file.parent.mkdir(parents=True, exist_ok=True)

    def log_trace(
        self,
        loop_level: int,
        agent_role: str,
        event_type: str,
        thinking_process: str,
        prompt_context: Dict[str, Any],
        tool_calls: List[Dict[str, Any]],
        validation_result: Dict[str, Any],
        rubber_duck_critique: Optional[Dict[str, Any]] = None,
        model_used: Optional[str] = None
    ) -> None:
        """
        Consigne une trace d'exécution exhaustive et complète.
        """
        entry = {
            "trace_id": f"trc_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S_%f')[:19]}",
            "project_name": self.project_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "loop_level": f"Loop {loop_level}",
            "agent_role": agent_role,
            "model_used": model_used or "Gemini 3.6 Flash (Thinking)",
            "thinking_process": thinking_process,
            "prompt_context": prompt_context,
            "event_type": event_type,
            "tool_calls": tool_calls,
            "validation_result": validation_result,
            "rubber_duck_critique": rubber_duck_critique or {}
        }

        # Écriture dans la trace Projet
        self._append_to_file(self.project_trace_file, entry)
        
        # Écriture dans la trace Globale mLoop
        self._append_to_file(self.global_trace_file, entry)

    def _append_to_file(self, filepath: Path, entry: Dict[str, Any]) -> None:
        traces = []
        if filepath.exists():
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    traces = json.load(f)
            except Exception:
                traces = []
                
        traces.append(entry)
        
        # Limite à 1000 entrées historiques
        if len(traces) > 1000:
            traces = traces[-1000:]
            
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(traces, f, indent=2, ensure_ascii=False)

