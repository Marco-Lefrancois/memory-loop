from pathlib import Path
import json
from src.state import LoopState, ProjectLayout
from src.cli import ZeroFluffConsole

class HandoffAgent:
    """
    Système 1 : Agent Handoff (Stub).
    Dans le framework IDE-Driven v2.0.0, la gestion de fin de session et du contexte
    est déléguée à la compétence (Skill) 'handoff' exécutée par l'agent de l'IDE.
    Ce pipeline sert de stub pour documenter le flux de travail.
    """

    def __init__(self, threshold: int = 10):
        self.name = "Handoff"
        self.threshold = threshold

    def execute(self, state: LoopState) -> LoopState:
        ZeroFluffConsole.step_s1(self.name, "Analyse du journal pour session recall et handoff...")
        
        project_path = Path("Projects") / state.project_name
        graph_file = project_path / "graphify-out" / "graph.json"
        
        if not graph_file.exists():
            return state

        try:
            with open(graph_file, "r", encoding="utf-8") as f:
                graph_data = json.load(f)
            
            nodes = graph_data.get("nodes", [])
            journal_nodes = [n for n in nodes if n.get("category") == "JournalEntry"]
            
            if len(journal_nodes) <= self.threshold:
                ZeroFluffConsole.info(f"Journal sous le seuil ({len(journal_nodes)}/{self.threshold}). Pas de handoff requis.")
                return state

            warning_msg = (
                f"[SATURATION_ALERT] Le journal contient {len(journal_nodes)} entrées (seuil de {self.threshold} dépassé). "
                "Risque de saturation de la fenêtre de contexte ! L'agent DOIT en informer l'utilisateur dans le chat et proposer de déclencher la compression sémantique / handoff."
            )
            ZeroFluffConsole.warning(warning_msg)
            if hasattr(state, 'audit_warnings') and isinstance(state.audit_warnings, list):
                state.audit_warnings.append(warning_msg)
            
        except Exception as e:
            ZeroFluffConsole.error(f"Erreur lors de la vérification Handoff : {e}")
            
        return state

