"""Handlers Projet : init, resume, focus, vibe-check."""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from src.cli import ZeroFluffConsole
from src.state import ProjectLayout

if TYPE_CHECKING:
    import argparse
    from src.state import LoopState


def handle_init(args: argparse.Namespace, state: LoopState, project_path: Path) -> int:
    """Initialise l'arborescence d'un nouveau projet (Loi des 3 Piliers)."""
    p = Path("Projects") / state.project_name
    (p / ProjectLayout.REFERENCE).mkdir(parents=True, exist_ok=True)
    for subdir in ProjectLayout.DOCS_SUBDIRS:
        (p / ProjectLayout.DOCS / subdir).mkdir(parents=True, exist_ok=True)

    idx = p / ProjectLayout.DOCS / "index.md"
    if not idx.exists():
        idx.write_text(
            f"# 📚 Table des Matières Dynamique - SSOT Projet '{state.project_name}'\n\n"
            "## 🗂️ Sommaire de la Base de Connaissances\n",
            encoding="utf-8",
        )

    (p / ProjectLayout.BACKLOG / "stories").mkdir(parents=True, exist_ok=True)
    sb = p / ProjectLayout.BACKLOG / ProjectLayout.SPRINT_BACKLOG_FILE
    if not sb.exists():
        sb.write_text(
            f"# Sprint Backlog - Projet {state.project_name}\n\n"
            "| ID | Titre | Statut | Key Jira |\n| :--- | :--- | :--- | :--- |\n",
            encoding="utf-8",
        )

    oq_client = p / ProjectLayout.DOCS / "04-transverse" / "00-questions-ouvertes-client.md"
    if not oq_client.exists():
        oq_client.write_text(
            f"# Registre des Questions Ouvertes (Client / Légal) - {state.project_name}\n\n"
            "Ce document regroupe exclusivement les points d'arbitrage d'affaires et légaux.\n\n"
            "| ID | Sujet | Statut | Destinataire (Rôle) | Décision / Réponse |\n"
            "| :--- | :--- | :--- | :--- | :--- |\n",
            encoding="utf-8",
        )

    oq_dev = p / ProjectLayout.DOCS / "04-transverse" / "00-questions-ouvertes-devteam.md"
    if not oq_dev.exists():
        oq_dev.write_text(
            f"# Registre des Questions Ouvertes (Équipe Dev) - {state.project_name}\n\n"
            "Ce document regroupe exclusivement les défis et verrous techniques.\n\n"
            "| ID | Sujet | Statut | Destinataire (Rôle) | Décision / Réponse |\n"
            "| :--- | :--- | :--- | :--- | :--- |\n",
            encoding="utf-8",
        )

    (p / ProjectLayout.MEMORY).mkdir(parents=True, exist_ok=True)

    # 1. README.md racine
    readme_path = p / "README.md"
    if not readme_path.exists():
        readme_path.write_text(
            f"# 🚀 {state.project_name} — Documentation & Architecture SSOT\n\n"
            f"Bienvenue dans le dépôt officiel de documentation d'architecture, de règles d'affaires et de cadrage pour le projet **{state.project_name}**.\n\n"
            "---\n\n"
            "## 🎯 Objectifs du Projet\n"
            "1. Cadrage fonctionnel et découpage vertical des récits utilisateur (Gabarit Gold Standard).\n"
            "2. Source de Vérité Unique (SSOT) des règles métier et des contrats d'architecture.\n\n"
            "---\n\n"
            "## 📂 Architecture du Dépôt (Versionné dans Git)\n\n"
            "```\n"
            f"{state.project_name}/\n"
            "├── 📄 README.md                # Documentation produit et point d'entrée humain\n"
            "├── 📄 AGENTS.md                # Source de vérité agentique (Boot sequence & guardrails)\n"
            "├── 📄 opencode.json            # Configuration IDE OpenCode (MCP & commandes)\n"
            "├── 📄 .gitignore               # Protection Git (exclusion de reference/, .codegraph/)\n"
            "├── 📂 backlog/                 # User Stories (Gherkin 4 Piliers) & sprint_backlog.md\n"
            "├── 📂 docs/                    # Architecture SSOT, ADRs, règles métier\n"
            "└── 📂 memory/                  # EvidencePacks JSON & état de session\n"
            "```\n\n"
            "> [!NOTE]\n"
            "> **Espace Local Staging (`reference/`)** : Le dossier local `reference/` (matière première brute) est exclu de Git par le `.gitignore`. Toute la matière utile est normalisée en Markdown dans `docs/00-ingested/`.\n",
            encoding="utf-8",
        )

    # 2. AGENTS.md racine (100% Agnostique & Orienté Développeur / Assistant IA)
    agents_path = p / "AGENTS.md"
    if not agents_path.exists():
        agents_path.write_text(
            f"# 🛡️ Guide Agentique & Spécifications Développeur — {state.project_name}\n\n"
            f"Ce document constitue la **Source de Vérité Agentique et Fonctionnelle (SSOT)** pour le projet **{state.project_name}**.\n\n"
            "Il est conçu pour être consommé directement par l'équipe de développement et par tout assistant de codage IA (Cursor, GitHub Copilot, VS Code, OpenCode, Claude Code, OpenAI Codex).\n\n"
            "---\n\n"
            "## 1. Organisation du Dépôt & Source de Vérité\n\n"
            "Le dépôt est structuré de façon modulaire et étanche (La Loi des 3 Piliers) :\n\n"
            "```\n"
            "├── 📂 docs/                          # Source de Vérité Fonctionnelle & Architecturale (SSOT)\n"
            "│   ├── 📂 00-ingested/               # Analyse normalisée des documents sources & maquettes\n"
            "│   ├── 📂 01-architecture/           # Énoncé des Travaux (SOW), schémas et décisions d'architecture (ADRs)\n"
            "│   ├── 📂 02-business-rules/         # Règles d'affaires métier (RM-XXX)\n"
            "│   ├── 📂 04-transverse/             # Registres de questions ouvertes et arbitrages\n"
            "│   └── 📂 05-assets/                 # Actifs graphiques versionnés (maquettes, diagrammes)\n"
            "│\n"
            "├── 📂 backlog/                       # Terrain d'Exécution & Spécifications Prêtes pour Dev\n"
            "│   ├── 📄 sprint_backlog.md          # Matrice d'avancement & statut des récits\n"
            "│   └── 📂 stories/                   # User Stories au Gold Standard (4 Piliers Gherkin)\n"
            "│\n"
            "└── 📂 memory/                        # Traçabilité & Preuves de Spécifications\n"
            "    └── 📂 evidence/                  # EvidencePacks JSON associés à chaque récit\n"
            "```\n\n"
            "---\n\n"
            "## 2. Contrats de Spécification & Règle des 4 Piliers Gherkin\n\n"
            "Chaque User Story présente sous `backlog/stories/` constitue un **contrat fonctionnel déclaratif complet** structuré autour des **4 Piliers Gherkin** que le code applicatif doit obligatoirement satisfaire :\n\n"
            "1. **Chemin Nominal (*Happy Path*)** : Le parcours utilisateur standard complété avec succès.\n"
            "2. **Rejets Métier & Erreurs de Validation** : Données invalides, règles métier non respectées, formulaires incomplets.\n"
            "3. **Résilience Technique & Cas Limites (*Edge Cases*)** : Comportement hors-ligne, expiration de session (timeout réseau), saturation des requêtes (anti-rebond).\n"
            "4. **UX, Sécurité & Accessibilité** : Retours visuels clairs, accessibilité (WCAG AA), masquage des données sensibles et états de chargement.\n\n"
            "---\n\n"
            "## 3. Directives de Développement & Pureté Fonctionnelle\n\n"
            "- **Pureté Fonctionnelle & Zéro Code Physique** : Les spécifications décrivent le comportement métier et les flux d'écrans sans couplage rigide à une implémentation physique. Zéro snippet de code physique dans les récits.\n"
            "- **Doc-First Obligatoire** : Se référer en priorité aux documents d'analyse sous `docs/00-ingested/` pour le détail de chaque parcours.\n",
            encoding="utf-8",
        )

    # 3. opencode.json racine (100% Agnostique & Propre)
    opencode_path = p / "opencode.json"
    if not opencode_path.exists():
        import json
        opencode_config = {
            "$schema": "https://opencode.ai/schema.json",
            "project": state.project_name,
            "version": "1.0.0",
            "instructions": ["AGENTS.md"],
            "watcher": {
                "ignore": [
                    ".git/**",
                    "node_modules/**",
                    "bin/**",
                    "obj/**",
                    "memory/cache/**"
                ]
            }
        }
        opencode_path.write_text(json.dumps(opencode_config, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # 4. .gitignore racine
    gitignore_path = p / ".gitignore"
    if not gitignore_path.exists():
        gitignore_path.write_text(
            "# Python Bytecode & Cache\n"
            "__pycache__/\n"
            "*.py[cod]\n"
            "*$py.class\n"
            ".pytest_cache/\n\n"
            "# Graphify & CodeGraph Local AST Caches\n"
            "graphify-out/\n"
            ".codegraph/\n"
            "**/.codegraph/\n\n"
            "# Memory Machine Caches & Traces (Recalculable localement)\n"
            "memory/cache/\n"
            "memory/tmp/\n"
            "memory/execution_traces.json\n"
            "memory/ingest_cache.json\n\n"
            "# Matière Première Brute & Espace Local (Non synchronisé dans le dépôt)\n"
            "reference/\n\n"
            "# OS Metadata\n"
            ".DS_Store\n"
            "Thumbs.db\n"
            "desktop.ini\n\n"
            "# Temporary Office Lock files\n"
            "~$*.xlsx\n"
            "*.tmp\n",
            encoding="utf-8",
        )

    ZeroFluffConsole.success(
        f"Projet '{state.project_name}' initialisé avec succès (Structure agnostique prête)."
    )
    ZeroFluffConsole.info(
        f"📋 Prochaines étapes du cycle de vie projet (SOP - ADR-0330) :\n"
        f"  1. Déposez vos documents clients / maquettes dans 'Projects/{state.project_name}/reference/'\n"
        f"  2. Ingestion & normalisation Markdown : 'python src/swarm.py ingest --project {state.project_name}'\n"
        f"  3. Énoncé des Travaux & Cadrage (SOW) : 'python src/swarm.py to-sow --project {state.project_name} --size <T-SHIRT>'\n"
        f"  4. Découpage du backlog : 'Projects/{state.project_name}/backlog/sprint_backlog.md'\n"
        f"  5. Cadrage interactif des récits : 'python src/swarm.py grill --project {state.project_name} --story <ID>'"
    )
    return 0


def handle_resume(args: argparse.Namespace, state: LoopState, project_path: Path) -> int:
    """Restaure la session anti-amnésie."""
    from src.pipelines.session_resume import run_session_resume
    run_session_resume(state.project_name)
    return 0


def handle_focus(args: argparse.Namespace, state: LoopState, project_path: Path) -> int:
    """Verrouille l'attention sur un récit spécifique."""
    from src.pipelines.focus import set_focus
    from src.pipelines.sync import run_sync
    set_focus(args.project, args.story)
    run_sync(args.project, state, project_path, fast_mode=True, verbose=getattr(args, "verbose", False))
    return 0


def handle_vibe_check(args: argparse.Namespace, state: LoopState, project_path: Path) -> int:
    """Guardrail pré-vol de la session (gouvernance de phase ADR-0339)."""
    from src.pipelines.vibe_check import run_vibe_check
    stage = getattr(args, "stage", None) or getattr(args, "phase", None)
    res = run_vibe_check(state.project_name, stage=stage)
    return 0 if res.get("status") == "PASS" else 1


def handle_install_hooks(args: argparse.Namespace, state: LoopState, project_path: Path) -> int:
    """Installe le hook Git local pre-commit pour la protection automatique du projet."""
    git_dir = project_path / ".git"
    if not git_dir.exists():
        ZeroFluffConsole.warn(f"Le projet '{state.project_name}' n'est pas un dépôt Git (.git introuvable).")
        return 1

    hooks_dir = git_dir / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    pre_commit_file = hooks_dir / "pre-commit"
    root_dir = project_path.resolve().parent.parent
    swarm_py = root_dir / "src" / "swarm.py"

    hook_content = (
        "#!/bin/sh\n"
        "# mLoop Git Pre-Commit Hook (Auto-protection anti-amnésie & hygiène de projet)\n"
        "echo \"🛡️ [mLoop Pre-Commit] Exécution du Guardrail Vibe-Check...\"\n"
        f"cd \"{root_dir.as_posix()}\"\n"
        f"python \"{swarm_py.as_posix()}\" vibe-check --project {state.project_name}\n"
        "if [ $? -ne 0 ]; then\n"
        "    echo \"❌ [mLoop Pre-Commit] Commit bloqué : Échec du Guardrail Vibe-Check.\"\n"
        "    exit 1\n"
        "fi\n"
        "exit 0\n"
    )
    pre_commit_file.write_text(hook_content, encoding="utf-8")
    ZeroFluffConsole.success(f"Hook Git pre-commit installé avec succès dans {pre_commit_file}")
    return 0


def handle_guide(args: argparse.Namespace, state: LoopState | None, project_path: Path | None) -> int:
    """Affiche le guide d'utilisation du pipeline CLI mLoop par phase."""
    ZeroFluffConsole.section("GUIDE D'UTILISATION DU PIPELINE CLI — MEMORY LOOP (mLoop)")

    phases_data = {
        "sow": {
            "title": "🟡 Phase 0 : INCEPTION (Gathering, Cadrage & SOW)",
            "commands": [
                ("to-sow", "Générer l'Énoncé des Travaux (SOW) sous docs/01-architecture/"),
                ("ingest", "Ingérer les briefs et documents initiaux sous docs/00-ingested/"),
                ("research", "Recherche et analyse documentaire préliminaire"),
            ]
        },
        "spec": {
            "title": "🟠 Phase 1 : SPEC / INGEST (Ingestion & Analyse Documentaire)",
            "commands": [
                ("crawl", "Web Crawler automatique avec détection Markdown Twin"),
                ("markitdown_convert", "Conversion multi-formats (PDF, Office, etc.) vers Markdown"),
                ("extract", "Extraction déclarative YAML vers Knowledge Abstracts (ADR-0342)"),
                ("agentic-extract", "Extraction sémantique de règles métier (RM-XXX)"),
                ("code-init", "Initialisation de l'indexation AST CodeGraph"),
            ]
        },
        "plan": {
            "title": "🔵 Phase 2 : PLAN / ARCHI (Planification, Grill & Découpage)",
            "commands": [
                ("focus", "Verrouiller l'attention sur une User Story (--story <ID>)"),
                ("grill", "Entrevue interactive ciblée Grill-with-Docs & enregistrement d'ADRs"),
                ("to-spec", "Distiller une discussion en spécification d'architecture"),
                ("to-tickets", "Découper une spec en récits verticaux tracer-bullet"),
                ("wayfinder", "Meta-Orchestration (carte de décisions dans le brouillard)"),
                ("chunk", "Découpage sémantique d'un document massif (ADR-0323)"),
                ("hyper-query", "Interroger l'hypergraphe pour une User Story ou un concept (ADR-0343)"),
                ("archify", "Génération et validation de diagrammes d'architecture interactifs vectoriels"),
            ]
        },
        "build": {
            "title": "🟢 Phase 3 : BUILD / DEV (Développement & Workers Multi-Agents)",
            "commands": [
                ("self-dev", "Auto-évolution du framework mLoop (TDD Red-Green-Refactor)"),
                ("confidence", "Évaluation du score de confiance pré-édition (Confidence Gate)"),
                ("worker-spawn", "Instanciation d'un sous-agent Herdr isolé (Clean Slate)"),
                ("worker-status", "Affichage du statut des workers Herdr actifs"),
                ("worker-close", "Fermeture propre et libération des ressources d'un worker"),
                ("code-impact", "Calcul du rayon d'impact (Blast Radius) d'un symbole"),
                ("code-affected", "Identification des tests unitaires affectés par un changement"),
            ]
        },
        "validate": {
            "title": "🟣 Phase 4 : VALIDATE / QA (Validation Sémantique & Guardrails)",
            "commands": [
                ("wikifix", "Audit de cohérence SSOT, règles métier et intégrité INVEST"),
                ("struct-check", "Gatekeeper structurel Read-Only pré-Sentinel (hiérarchie H2/H3/H4, format listes, Gold Standard diff)"),
                ("rubber-duck", "Audit contradictoire Sentinel en lecture seule (4 Piliers Gherkin)"),
                ("audit-loop", "Validation déterministe des 3 couches de guardrails"),
                ("aoep", "Évaluation de la gouvernance d'état persistant AOEP-v0"),
                ("eval", "Exécution de la suite d'évaluations agentiques"),
                ("worker-harvest", "Moisson synchrone des livrables écrits par un worker"),
            ]
        },
        "ship": {
            "title": "🔴 Phase 5 : SHIP & SYNC (Synchronisation & Distribution)",
            "commands": [
                ("sync", "Synchronisation globale (WikiFix + Graphify + Hypergraphe + SQLite FTS5)"),
                ("export-obsidian", "Exporter l'hypergraphe en coffre Obsidian avec wikilinks (ADR-0343)"),
                ("jira_sync", "Synchronisation bidirectionnelle avec Jira Cloud"),
                ("cycle-status", "Bilan de santé et statut d'avancement des 5 phases"),
                ("calibrate", "Auto-étalonnage continu de l'écosystème mLoop (8 axes)"),
                ("plugin-validate", "Validation de conformité Agent Plugins 1.0"),
                ("plugin-export", "Empaquetage portable du plugin mLoop pour distribution"),
            ]
        }
    }

    target_phase = getattr(args, "phase", None)
    selected_phases = [target_phase] if target_phase and target_phase in phases_data else list(phases_data.keys())

    print("\nCommandes universelles de démarrage (Boot Sequence) :")
    print("  1. python src/swarm.py resume --project <nom_projet>")
    print("  2. python src/swarm.py vibe-check --project <nom_projet>")
    print("  3. python src/swarm.py focus --project <nom_projet> --story <story_id>\n")

    for pkey in selected_phases:
        pinfo = phases_data[pkey]
        print(f"\n{pinfo['title']}")
        print("─" * 70)
        for cmd, desc in pinfo["commands"]:
            print(f"  • python src/swarm.py {cmd:<18} : {desc}")

    print("\n" + "═" * 70)
    print("📖 Guide normatif complet : standards/protocols/CLI_PIPELINE_GUIDE.md")
    print("⌨️  OpenCode Dispatcher   : /loop <action> [arguments] (ex: /loop sync)")
    print("═" * 70 + "\n")
    return 0

