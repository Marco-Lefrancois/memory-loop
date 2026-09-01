from src.pipelines.dreamer import DreamerPipeline

def handle_dream(args, state, project_path):
    """Handler CLI pour la commande 'swarm.py dream'."""
    project_name = args.project
    results = DreamerPipeline.run_dream_consolidation(project_name=project_name)
    return 0 if results.get("status") != "ERROR" else 1
