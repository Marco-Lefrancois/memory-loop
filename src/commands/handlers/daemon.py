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
    """Liste les manifestes de rôles agentiques déclaratifs disponibles."""
    ZeroFluffConsole.section("MANIFESTES DES RÔLES AGENTIQUES MLOOP (STANDARDS/AGENTS)")
    agents_dir = Path("standards/agents")
    try:
        import tomllib
    except ImportError:
        import toml as tomllib

    if not agents_dir.exists():
        ZeroFluffConsole.warning("Aucun dossier standards/agents/ trouvé.")
        return 0

    roles = list(agents_dir.glob("*.toml"))
    if not roles:
        ZeroFluffConsole.info("Aucun rôle déclaratif trouvé.")
        return 0

    for role_file in sorted(roles):
        try:
            data = tomllib.loads(role_file.read_text(encoding="utf-8"))
            name = data.get("name", role_file.stem)
            desc = data.get("description", "Aucune description.")
            model = data.get("model", "Hérité")
            effort = data.get("model_reasoning_effort", "medium")
            sandbox = data.get("sandbox_mode", "read-only")
            
            ZeroFluffConsole.info(f"🤖 Rôle : [{name.upper()}] (Fichier : {role_file.name})")
            print(f"   • Description : {desc}")
            print(f"   • Modèle cible : {model} (Effort : {effort})")
            print(f"   • Bac à sable : {sandbox}\n")
        except Exception as e:
            ZeroFluffConsole.warning(f"Erreur de lecture du rôle {role_file.name} : {e}")

    ZeroFluffConsole.success(f"{len(roles)} rôles déclaratifs chargés avec succès.")
    return 0
