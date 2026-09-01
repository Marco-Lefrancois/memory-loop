from pathlib import Path
from src.state import LoopState
from src.cli import ZeroFluffConsole

def run_drill(project_name: str, state: LoopState, project_path: Path, target: str = "global") -> LoopState:
    ZeroFluffConsole.section(f"Entrevue interactive Drill Me - {project_name} (Cible: {target})")
    
    # Dans le framework IDE-Driven v2.0.0, l'interview est menée directement par l'agent de l'IDE.
    # Ce script sert de validateur d'état déterministe pour le cycle.
    
    pending_questions = [c for c in state.clarifications if c.answer is None]
    
    if target == "global":
        if not state.clarifications:
            ZeroFluffConsole.info("Aucune clarification n'a encore été générée. L'agent IDE doit démarrer le bootstrap grill.")
        elif pending_questions:
            ZeroFluffConsole.warning(f"Des questions d'affaires restent en suspens ({len(pending_questions)} en attente) :")
            for q in pending_questions:
                print(f"  - [{q.id}] {q.question}")
        else:
            ZeroFluffConsole.success("Tous les points d'alignement globaux de haut niveau ont été clarifiés (Statut: DRILL_GLOBAL_COMPLETE).")
    else:
        # Cible une story spécifique
        story = next((s for s in state.sprint_backlog if s.id == target), None)
        if not story:
            ZeroFluffConsole.error(f"Story {target} introuvable dans le backlog.")
        elif story.grilled:
            ZeroFluffConsole.success(f"Clarifications de la story {target} finalisées (Statut: DRILL_STORY_COMPLETE).")
        else:
            ZeroFluffConsole.warning(f"La story {target} n'a pas encore été grillée.")
            
    state.save_to_audit(project_path)
    return state
