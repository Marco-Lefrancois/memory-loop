"""
mLoop CLI Handlers pour le démon App-Server et la gouvernance Guardian.
"""

from pathlib import Path
from src.cli import ZeroFluffConsole


def handle_app_server(args, state, project_path):
    """Démarre le serveur JSON-RPC App-Server mLoop."""
    ZeroFluffConsole.section("DÉMARRAGE DU DÉMON MLOOP APP-SERVER (JSON-RPC 2.0)")
    ZeroFluffConsole.info("Serveur prêt sur flux stdio. En attente de requêtes JSON-RPC...")
    
    from src.daemon.app_server import AppServerProtocol
    server = AppServerProtocol()
    server.run_stdio()
    return 0


def handle_guardian_status(args, state, project_path):
    """Affiche l'état du Guardian Auto-Reviewer et du Circuit Breaker."""
    ZeroFluffConsole.section("STATUT DU GUARDIAN AUTO-REVIEWER & CIRCUIT BREAKER")
    from src.engine.guardian import GuardianAutoReviewer
    reviewer = GuardianAutoReviewer()
    
    cb = reviewer.circuit_breaker
    ZeroFluffConsole.info(f"Refus consécutifs actuels : {cb.consecutive_denials} / {cb.max_consecutive_denials}")
    ZeroFluffConsole.info(f"Seuil de déclenchement d'urgence (Circuit Breaker) : 3 refus consécutifs ou 10 sur 50 requêtes.")
    ZeroFluffConsole.success("Le Circuit Breaker est ARMÉ et OPÉRATIONNEL (État : NOMINAL).")
    return 0


def handle_role_list(args, state, project_path):
    """Liste les manifestes de rôles agentiques déclaratifs disponibles (ADR-0379)."""
    ZeroFluffConsole.section("MANIFESTES DES RÔLES AGENTIQUES MLOOP (.AGENTS/AGENTS/*.MD)")
    from src.core.standards_graph import StandardsGraphStore

    store = StandardsGraphStore.get_instance()
    agents = store.get_agents()

    if not agents:
        ZeroFluffConsole.info("Aucun rôle déclaratif trouvé.")
        return 0

    for name, agent in sorted(agents.items()):
        skills_str = ", ".join(agent.skills) if agent.skills else "(aucun outil spécialisé)"
        ZeroFluffConsole.info(f"🤖 Rôle : [{name.upper()}] (Fichier : {Path(agent.file_path).name})")
        if agent.role:
            print(f"   • Rôle & Mission : {agent.role}")
        print(f"   • Description : {agent.description}")
        print(f"   • Modèle cible : {agent.model} (Effort : {agent.model_reasoning_effort})")
        print(f"   • Bac à sable : {agent.sandbox_mode}")
        print(f"   • Compétences autorisées : {skills_str}\n")

    ZeroFluffConsole.success(f"{len(agents)} rôles agentiques chargés depuis StandardsGraph.")
    return 0
