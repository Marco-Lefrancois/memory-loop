import sys
import os
import argparse
from pathlib import Path
import yaml

# Add src to path to import state
sys.path.append(str(Path(__file__).parent.parent.parent))
from src.state import LoopState

def validate_story_state(project_name: str, check_file: str = None):
    project_path = Path("Projects") / project_name
    audit_path = project_path / "graphify-out" / "graph.json"
    
    if not audit_path.exists():
        print(f"ERROR: Graph state not found for {project_name}")
        sys.exit(1)
        
    state = LoopState(project_name=project_name)
    state.load_from_audit(project_path)
    
    from src.pipelines.state_machine import StateMachineEngine
    engine = StateMachineEngine(str(project_path))
    in_analyze_list = engine.validate_single_in_analyze()
    story_id_override = os.environ.get("MLOOP_ACTIVE_STORY_ID")
    active_story = story_id_override or (in_analyze_list[0] if in_analyze_list else None)
    
    if not active_story:
        print("WARNING: No active story identified in IN_ANALYZE status or env. Proceeding with caution.")
        return
        
    print(f"STORY-GUARD: Validating state for story {active_story}...")
    
    if check_file:
        story = next((s for s in state.sprint_backlog if s.id == active_story), None)
        if not story:
            print(f"ERROR: Active story {active_story} not found in backlog.")
            sys.exit(1)
            
        components = story.components
        if not components:
            print("WARNING: Active story has no declared components in its SCC. Bypassing check.")
        else:
            check_file_lower = check_file.lower().replace("\\", "/")
            is_allowed = any(comp.lower().replace("\\", "/") in check_file_lower for comp in components)
            
            if not is_allowed:
                print(f"STORY-GUARD REJECTED: Accès refusé.")
                print(f"Le fichier '{check_file}' n'est pas déclaré dans le SCC de la Story {active_story}.")
                print(f"Composants autorisés: {components}")
                sys.exit(1)
            else:
                print(f"STORY-GUARD: Fichier '{check_file}' autorisé.")

    print(f"STORY-GUARD: Story {active_story} is healthy. Zero-Drift confirmed.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True)
    parser.add_argument("--check_file", required=False, help="Le chemin du fichier à valider contre le SCC")
    args = parser.parse_args()
    
    validate_story_state(args.project, args.check_file)
