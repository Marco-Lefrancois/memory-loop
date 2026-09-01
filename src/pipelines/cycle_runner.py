"""
Cycle Runner Pipeline - mLoop v2.0.0
Diagnostic et suivi de l'avancement d'un projet à travers le cycle Spec-Driven Development :
1. Spec (Spécification)
2. Plan (Planification)
3. Build (Construction / Tranches verticaux)
4. Validate (Validation & Guardrails)
5. Ship (Livraison & Synchronisation)
"""

from pathlib import Path
from typing import Dict, Any
from src.state import ProjectLayout

class SpecCycleEngine:
    def __init__(self, project_name: str):
        self.project_name = project_name
        self.project_path = Path("Projects") / project_name

    def evaluate_cycle(self) -> Dict[str, Any]:
        results = {
            "project": self.project_name,
            "pipeline": "Spec -> Plan -> Build -> Validate -> Ship",
            "phases": {
                "1_spec": {"status": "NOT_STARTED", "details": ""},
                "2_plan": {"status": "NOT_STARTED", "details": ""},
                "3_build": {"status": "NOT_STARTED", "details": ""},
                "4_validate": {"status": "NOT_STARTED", "details": ""},
                "5_ship": {"status": "NOT_STARTED", "details": ""}
            }
        }

        if not self.project_path.exists():
            return results

        # 1. Spec
        specs_dir = self.project_path / ProjectLayout.DOCS / ProjectLayout.DOCS_ARCHITECTURE
        spec_files = list(specs_dir.glob("spec_*.md")) if specs_dir.exists() else []
        if spec_files:
            results["phases"]["1_spec"] = {
                "status": "COMPLETED",
                "details": f"{len(spec_files)} fichier(s) de spécification détecté(s)."
            }
        else:
            results["phases"]["1_spec"] = {
                "status": "IN_PROGRESS",
                "details": "Spécification en cours ou non distillée."
            }

        # 2. Plan
        stories_dir = self.project_path / ProjectLayout.BACKLOG / "stories"
        stories = list(stories_dir.glob("*.md")) if stories_dir.exists() else []
        sprint_backlog = self.project_path / ProjectLayout.BACKLOG / ProjectLayout.SPRINT_BACKLOG_FILE
        
        if stories and sprint_backlog.exists():
            results["phases"]["2_plan"] = {
                "status": "COMPLETED",
                "details": f"{len(stories)} récit(s) planifié(s) dans le backlog."
            }
        elif stories:
            results["phases"]["2_plan"] = {
                "status": "IN_PROGRESS",
                "details": "Récits créés, sprint_backlog en attente."
            }

        # 3. Build
        if stories:
            results["phases"]["3_build"] = {
                "status": "IN_PROGRESS",
                "details": "Phase de construction sous le contrôle du Story Constraint Contract (SCC)."
            }

        # 4. Validate
        wikifix_report = self.project_path / "memory" / "wikifix_report.md"
        if wikifix_report.exists():
            content = wikifix_report.read_text(encoding="utf-8")
            if "0 alerte(s)" in content:
                results["phases"]["4_validate"] = {
                    "status": "COMPLETED",
                    "details": "Validation sémantique Wikifix PASS (Sint-Score 100%)."
                }
            else:
                results["phases"]["4_validate"] = {
                    "status": "IN_PROGRESS",
                    "details": "Validation en cours avec alertes."
                }

        # 5. Ship
        db_file = self.project_path / "memory" / "state.db"
        graph_file = self.project_path / "graphify-out" / "graph.json"
        if db_file.exists() and graph_file.exists():
            results["phases"]["5_ship"] = {
                "status": "READY_FOR_SHIP",
                "details": "Base SQLite et Graphe sémantique Graphify synchronisés."
            }

        return results

def run_cycle_status(project_name: str) -> Dict[str, Any]:
    engine = SpecCycleEngine(project_name)
    return engine.evaluate_cycle()
