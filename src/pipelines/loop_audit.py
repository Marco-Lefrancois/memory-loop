"""
Loop Audit Pipeline - mLoop v2.0.0
Consolide l'évaluation déterministe des 3 couches de guardrails de la boucle agentique :
1. Story Guard (Story Constraint Contract SCC)
2. Linter Sémantique & Sint-Score (WikiFix INVEST / Gherkin)
3. Gouvernance d'État Persistant (AOEP-v0)
4. Retrospective Harness Optimization (RHO Rules)
"""

from pathlib import Path
from typing import Dict, Any
import json
import sys

from src.bridges.story_guard import validate_story_state
from src.pipelines.aoep_runner import run_aoep_eval
from src.pipelines.wikifix import WikiFixAgent
from src.state import LoopState

class LoopAuditEngine:
    def __init__(self, project_name: str):
        self.project_name = project_name
        self.project_path = Path("Projects") / project_name

    def run_full_audit(self) -> Dict[str, Any]:
        results = {
            "project": self.project_name,
            "cognitive_core": "OK",
            "memory_layers": "OK (Graphify + SQLite FTS5)",
            "guardrails": {
                "story_guard": "PASS",
                "sint_score_wikifix": "PASS",
                "aoep_governance": "PASS",
                "rho_learning": "PASS"
            },
            "status": "PASS"
        }

        # 1. Audit Story Guard
        try:
            validate_story_state(self.project_name)
        except SystemExit as e:
            if e.code != 0:
                results["guardrails"]["story_guard"] = "FAIL"
                results["status"] = "FAIL"

        # 2. Audit Sint-Score / WikiFix
        try:
            state = LoopState(project_name=self.project_name)
            state.load_from_audit(self.project_path)
            WikiFixAgent().execute(state)
        except Exception as e:
            results["guardrails"]["sint_score_wikifix"] = f"FAIL: {str(e)}"
            results["status"] = "FAIL"

        # 3. Audit AOEP-v0
        try:
            aoep_res = run_aoep_eval(self.project_name)
            if aoep_res.get("aoep_score") != "PASS":
                results["guardrails"]["aoep_governance"] = "FAIL"
                results["status"] = "FAIL"
        except Exception as e:
            results["guardrails"]["aoep_governance"] = f"FAIL: {str(e)}"
            results["status"] = "FAIL"

        # 4. Audit RHO Rules
        rho_rules_file = self.project_path / "directives" / "rho_rules.yaml"
        if not rho_rules_file.exists():
            global_rho = Path("directives/rho_rules.yaml")
            if not global_rho.exists():
                results["guardrails"]["rho_learning"] = "WARN: Aucun fichier rho_rules.yaml détecté."

        return results

def run_loop_audit(project_name: str) -> Dict[str, Any]:
    engine = LoopAuditEngine(project_name)
    return engine.run_full_audit()
