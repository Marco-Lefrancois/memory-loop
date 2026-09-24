"""
Sous-registre déclaratif CLI — Domaine Infra & Opérations (MLOOP-175-BE).

Daemon & Extensions : app-server, mcp-serve, guardian-status, role-list.
Cache (ADR-0336) : cache-stats, cache-clear.
Fact-Check (ADR-0326/0352) : fact-check, fact-search, dossier-init,
                               check-leakage, nli-audit.
Visual Review & Annotation (ADR-0305/0307) : review, annotate, guide-export.
Résilience Agentique (ADR-0371) : agent-resilience, topology, rollback.
Dream RSI (ADR-0372) : dream-rsi.

Contraintes : ADR-0202 (≤300L/15Ko), ADR-0369 (zéro import circulaire).
"""

RUNTIME_OPS_COMMANDS: dict[str, dict] = {
    # ── Daemon & Architecture Codex Extensions ─────────────
    "app-server": {
        "handler": "daemon:handle_app_server",
        "help": "Démarrer le démon d'interfaçage JSON-RPC 2.0 mLoop App-Server",
        "args": [],
        "no_project": True,
    },
    "mcp-serve": {
        "handler": "mcp_serve:handle_mcp_serve",
        "help": "Démarrer le serveur MCP transport réseau SSE (MLOOP-103-BE)",
        "args": [
            {
                "name": "--host",
                "type": str,
                "default": "127.0.0.1",
                "help": "Adresse de bind (défaut: 127.0.0.1)",
            },
            {
                "name": "--port",
                "type": int,
                "default": 8380,
                "help": "Port HTTP SSE (défaut: 8380)",
            },
        ],
        "no_project": True,
    },
    "guardian-status": {
        "handler": "daemon:handle_guardian_status",
        "help": "Afficher l'état du Guardian Auto-Reviewer et du Circuit Breaker",
        "args": [],
    },
    "role-list": {
        "handler": "daemon:handle_role_list",
        "help": "Lister les manifestes de rôles agentiques déclaratifs disponibles",
        "args": [],
    },
    # ── Semantic Cache & LLM Optimizations (ADR-0336) ─────
    "cache-stats": {
        "handler": "cache:handle_cache_stats",
        "help": "Afficher les statistiques du cache sémantique déterministe LLM",
        "args": [],
        "no_project": True,
    },
    "cache-clear": {
        "handler": "cache:handle_cache_clear",
        "help": "Effacer le cache sémantique déterministe LLM",
        "args": [
            {"name": "--model", "type": str, "default": None, "help": "Modèle spécifique à purger"},
        ],
        "no_project": True,
    },
    # ── Fact-Check & NLI Ground Truth (ADR-0326 / ADR-0352) ──
    "fact-check": {
        "handler": "fact_check:handle_fact_check",
        "help": "Exécuter l'audit Fact-Check NLI sur une User Story et émettre son certificat",
        "args": [
            {
                "name": "--story",
                "type": str,
                "help": "Identifiant ou requête vers le récit à auditer",
            },
            {
                "name": "--strict",
                "action": "store_true",
                "help": "Mode strict : échoue si des exigences sont sans preuve",
            },
        ],
    },
    "fact-search": {
        "handler": "fact_search:handle_fact_search",
        "help": "Recherche factuelle haute précision dans l'index FTS5 SSOT documentaire",
        "args": [
            {
                "name": "--query",
                "type": str,
                "required": True,
                "help": "Requête de recherche factuelle",
            },
            {
                "name": "--limit",
                "type": int,
                "default": 5,
                "help": "Nombre maximal de faits à retourner (défaut: 5)",
            },
            {
                "name": "--layer",
                "type": str,
                "default": None,
                "help": "Filtrer par couche SSOT (ex: 01-architecture, 02-business-rules)",
            },
            {
                "name": "--no-synonyms",
                "action": "store_true",
                "help": "Désactiver l'expansion synonymique automatique",
            },
            {
                "name": "--include-superseded",
                "action": "store_true",
                "help": "Inclure les documents obsolètes/remplacés avec pénalité",
            },
        ],
        "no_project": True,
    },
    "dossier-init": {
        "handler": "analysis:handle_dossier_init",
        "help": "Initialise le Dossier de Preuves Documentaires (_fact_dossier.md) pour un récit",
        "args": [
            {
                "name": "--story",
                "type": str,
                "required": True,
                "help": "Identifiant ou chemin du récit cible (ex: INC-003-BE)",
            },
            {
                "name": "--force",
                "action": "store_true",
                "help": "Écraser si le fichier existe déjà",
            },
        ],
    },
    # ── Verification Leakage Gate (ADR-0354) ────────────────
    "check-leakage": {
        "handler": "gates:handle_check_leakage",
        "help": "Vérifier l'absence de fuites de spécification et assertions tautologiques (ADR-0354)",
        "args": [
            {"name": "--file", "type": str, "help": "Fichier de test spécifique à auditer"},
        ],
        "no_project": True,
    },
    # ── Contradiction Engine NLI (ADR-0326 / MLOOP-091-BE) ──
    "nli-audit": {
        "handler": "validation:handle_nli_audit",
        "help": "Audit de non-contradiction sémantique NLI et fuites de tests (ADR-0326 / ADR-0354)",
        "args": [],
        "phase": "validate",
    },
    # ── Visual Review & Annotation (Plannotator ADR-0305 / ADR-0307) ──
    "review": {
        "handler": "plannotator:handle_review",
        "help": "Revue de code visuelle interactive via Plannotator (diff Git local ou PR)",
        "args": [
            {"name": "--pr", "type": str, "help": "URL de Pull Request GitHub/GitLab à réviser"},
            {
                "name": "--tailscale",
                "action": "store_true",
                "help": "Partager la session sur le réseau Tailnet HTTPS",
            },
            {
                "name": "--no-local",
                "action": "store_true",
                "help": "Pour revue PR, diff seul sans checkout local",
            },
        ],
        "no_project": True,
    },
    "annotate": {
        "handler": "plannotator:handle_annotate",
        "help": "Annotation visuelle de récits, ADRs, documents ou URLs avec porte de décision",
        "args": [
            {
                "name": "--story",
                "type": str,
                "help": "Identifiant du récit à annoter (ex: US-042)",
            },
            {
                "name": "--adr",
                "type": str,
                "help": "Numéro ou mot-clé de l'ADR à annoter (ex: 0305)",
            },
            {
                "name": "--file",
                "type": str,
                "help": "Chemin vers un fichier local Markdown, HTML ou texte",
            },
            {
                "name": "--url",
                "type": str,
                "help": "URL d'une application web locale ou distante à annoter",
            },
            {
                "name": "--no-gate",
                "action": "store_true",
                "help": "Désactiver le bouton d'approbation (lecture et annotation libre)",
            },
            {
                "name": "--require-approval",
                "action": "store_true",
                "help": "Bloquer l'exécution tant que le réviseur n'approuve pas dans l'UI",
            },
            {
                "name": "--json",
                "action": "store_true",
                "help": "Émettre le résultat de validation structuré en JSON",
            },
            {
                "name": "--result-file",
                "type": str,
                "help": "Chemin où écrire le JSON de décision de manière atomique",
            },
            {
                "name": "--tailscale",
                "action": "store_true",
                "help": "Partager la session d'annotation sur le réseau Tailnet HTTPS",
            },
        ],
        "no_project": True,
    },
    "guide-export": {
        "handler": "plannotator:handle_guide_export",
        "help": "Exporter un guide de revue autonome HTML portable via Plannotator",
        "args": [
            {"name": "--snapshot", "type": str, "help": "Fichier snapshot JSON d'un guide"},
            {"name": "--id", "type": str, "help": "Identifiant d'un guide Plannotator existant"},
            {"name": "--out", "type": str, "help": "Chemin du fichier HTML de sortie"},
        ],
        "no_project": True,
    },
    # ── Résilience Agentique & Point-in-Time Recovery (ADR-0371) ──────────
    "agent-resilience": {
        "handler": "resilience:handle_agent_resilience",
        "help": "Audit de la posture de cyber-résilience agentique (ADR-0371)",
        "args": [{"name": "--json", "action": "store_true", "help": "Sortie au format JSON brut"}],
    },
    "topology": {
        "handler": "resilience:handle_topology",
        "help": "Cartographie topologique des agents et calcul du Blast Radius (ADR-0371)",
        "args": [
            {
                "name": "--agent",
                "type": str,
                "help": "Rôle spécifique d'agent (orchestrator, worker, qa, crawler...)",
            },
            {"name": "--json", "action": "store_true", "help": "Sortie au format JSON brut"},
        ],
    },
    "rollback": {
        "handler": "resilience:handle_rollback",
        "help": "Restauration déterministe point-in-time de l'état et de la mémoire (ADR-0371)",
        "args": [
            {
                "name": "--step",
                "type": int,
                "help": "Numéro d'étape du checkpoint à restaurer (1 = plus récent)",
            },
            {
                "name": "--target",
                "type": str,
                "help": "Partition de mémoire spécifique à restaurer sélectivement",
            },
        ],
    },
    # ── Dream RSI (ADR-0372) ───────────────────────────────
    "dream-rsi": {
        "handler": "dream_rsi:handle_dream_rsi",
        "help": "Exécuter le cycle Dream RSI (simulateur replay hors-ligne & optimisation de politique)",
        "args": [
            {
                "name": "--simulate",
                "action": "store_true",
                "help": "Simuler le cycle sans persistance",
            },
            {
                "name": "--apply",
                "action": "store_true",
                "help": "Sauvegarder la méta-politique (.mloop/dream_policy.json)",
            },
            {"name": "--json", "action": "store_true", "help": "Sortie au format JSON brut"},
        ],
    },
}
