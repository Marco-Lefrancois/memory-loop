"""
Générateur Déterministe & Synchroniseur du Guide CLI SSOT (ADR-0370).
Garantit la parité absolue entre le code Python (src/commands/_registry.py)
et le guide de référence normatif (standards/protocols/CLI_PIPELINE_GUIDE.md).
"""

from pathlib import Path
from typing import Any, Dict, List, Tuple
from src.commands._registry import COMMANDS

GUIDE_PATH = Path("standards/protocols/CLI_PIPELINE_GUIDE.md")

PHASE_MAPPING: Dict[str, str] = {
    # Phase 0 : INCEPTION (Gathering, Cadrage & SOW)
    "init": "sow",
    "to-sow": "sow",
    "ingest": "sow",
    "research": "sow",

    # Phase 1 : SPEC / INGEST (Ingestion & Analyse Documentaire)
    "crawl": "spec",
    "extract": "spec",
    "agentic-extract": "spec",
    "chunk": "spec",
    "parent-resolve": "spec",
    "deep-search": "spec",
    "csv-normalize": "spec",
    "csv-validate": "spec",
    "code-init": "spec",
    "code-status": "spec",
    "jira-read": "spec",

    # Phase 2 : PLAN / ARCHI (Planification, Architecture, Grill & Découpage)
    "focus": "plan",
    "grill": "plan",
    "grill-project": "plan",
    "to-tshirt": "plan",
    "to-spec": "plan",
    "to-tickets": "plan",
    "wayfinder": "plan",
    "drill": "plan",
    "deepen": "plan",
    "goal-cascade": "plan",
    "distill-invest": "plan",
    "graph-query": "plan",
    "graph-explain": "plan",
    "graph-impact": "plan",
    "graph-status": "plan",
    "hyper-query": "plan",
    "archify": "plan",
    "drawdb": "plan",
    "canvas": "plan",
    "export-obsidian": "plan",
    "story-clean": "plan",
    "update-story": "plan",
    "dossier-init": "plan",
    "multi-draft": "plan",

    # Phase 3 : BUILD / DEV (Développement & Workers Multi-Agents)
    "self-dev": "build",
    "confidence": "build",
    "worker-spawn": "build",
    "worker-status": "build",
    "worker-close": "build",
    "worker-harvest": "build",
    "worker-reap": "build",
    "worker-handoff-test": "build",
    "worker-legacy-mine": "build",
    "worker-shadow-estimate": "build",
    "worker-visual-dissect": "build",
    "worker-janitor-watch": "build",
    "code-explore": "build",
    "code-impact": "build",
    "code-affected": "build",
    "csv-diff": "build",
    "csv-anonymize": "build",
    "review": "build",
    "annotate": "build",

    # Phase 4 : VALIDATE / QA (Validation Sémantique, Fact-Check & Guardrails)
    "wikifix": "validate",
    "struct-check": "validate",
    "rubber-duck": "validate",
    "audit-loop": "validate",
    "aoep": "validate",
    "fact-check": "validate",
    "fact-search": "validate",
    "check-leakage": "validate",
    "gates": "validate",
    "gate-approve": "validate",
    "lifecycle-status": "validate",
    "lifecycle-clean": "validate",
    "tree": "validate",
    "guardian-status": "validate",
    "eval": "validate",
    "eval-harvest": "validate",
    "diagnose": "validate",
    "hill-climb": "validate",

    # Phase 5 : SHIP & SYNC (Synchronisation, Jira Cloud & Distribution)
    "sync": "ship",
    "sync-antigravity": "ship",
    "jira_sync": "ship",
    "notebooklm": "ship",
    "cycle-status": "ship",
    "calibrate": "ship",
    "plugin-validate": "ship",
    "plugin-export": "ship",
    "guide-export": "ship",
    "install-hooks": "ship",

    # Transverse / Observabilité, Mémoire, Tokens & Runtime
    "guide": "transverse",
    "resume": "transverse",
    "vibe-check": "transverse",
    "dashboard": "transverse",
    "app-server": "transverse",
    "token-tracker": "transverse",
    "context-watch": "transverse",
    "cache-stats": "transverse",
    "cache-clear": "transverse",
    "memory-hygiene": "transverse",
    "supersession-sync": "transverse",
    "memo-search": "transverse",
    "blast": "transverse",
    "dream": "transverse",
    "unlearn": "transverse",
    "svg-optimize": "transverse",
    "teach": "transverse",
    "hook": "transverse",
    "doctor": "transverse",
    "agent-probe": "transverse",
    "skill-doctor": "transverse",
    "skill-list": "transverse",
    "skill-invoke": "transverse",
    "role-list": "transverse",
    "graph-run": "transverse",
    "optimize": "transverse",
    "agent-resilience": "transverse",
    "topology": "plan",
    "rollback": "transverse",
    "dream-rsi": "transverse",
}

PHASE_HEADERS: Dict[str, Dict[str, str]] = {
    "sow": {
        "title": "🟡 Phase 0 : INCEPTION (Gathering, Cadrage & SOW)",
        "desc": "Cadrage amont, ingestion initiale des briefs clients et génération de l'Énoncé des Travaux (SOW).",
    },
    "spec": {
        "title": "🟠 Phase 1 : SPEC / INGEST (Ingestion, Exploration & Données)",
        "desc": "Ingestion multimodale, Web Crawling, parsing de code source AST, conversion MarkItDown et normalisation tabulaire CSV.",
    },
    "plan": {
        "title": "🔵 Phase 2 : PLAN / ARCHI (Planification, Architecture, Grill & Découpage)",
        "desc": "Entrevues interactives Grill-with-Docs, découpage vertical INVEST, modélisation de données (DrawDB/Mermaid), hypergraphe et toiles Obsidian Canvas.",
    },
    "build": {
        "title": "🟢 Phase 3 : BUILD / DEV (Développement & Workers Multi-Agents)",
        "desc": "Orchestration multi-agents isolée (Herdr Fork & Harvest), revue de code visuelle Plannotator, exploration d'impact AST et auto-évolution.",
    },
    "validate": {
        "title": "🟣 Phase 4 : VALIDATE / QA (Validation Sémantique, Fact-Check & Guardrails)",
        "desc": "Audit de non-régression INVEST (WikiFix), Gatekeeper structurel (struct-check), audit contradictoire Sentinel (rubber-duck), Fact-Check NLI et Runnable Gates.",
    },
    "ship": {
        "title": "🔴 Phase 5 : SHIP & SYNC (Synchronisation, Jira Cloud & Distribution)",
        "desc": "Synchronisation bidirectionnelle Jira Cloud, synchronisation sémantique locale, export Oracle Google NotebookLM, et packaging Agent Plugins 1.0.",
    },
    "transverse": {
        "title": "⚙️ Commandes Transverses (Observabilité, Mémoire, Tokens, Skills & Runtime)",
        "desc": "Surveillance de la fenêtre de contexte, audit des coûts TokenLedger, diagnostic des compétences (Skill Doctor), cache sémantique et serveurs d'API.",
    },
}

ARTEFACTS_MAP: Dict[str, str] = {
    "to-tshirt": "`docs/01-architecture/TSHIRT_SIZE_<PROJET>.md`",
    "to-sow": "`docs/01-architecture/SOW_<PROJET>.md`",
    "ingest": "`docs/00-ingested/` normalisé",
    "crawl": "`memory/crawler/cache/` (Markdown Twin)",
    "extract": "`docs/02-business-rules/`, `docs/03-models/`",
    "agentic-extract": "`docs/02-business-rules/RM-*.md`",
    "code-init": "Base SQLite `.codegraph/`",
    "focus": "Chargement de `backlog/stories/<ID>.md`",
    "grill": "ADRs dans `standards/adr-system/` & preuves",
    "grill-project": "`standards/adr-system/` & cadrage macro",
    "to-spec": "`docs/01-architecture/`",
    "to-tickets": "`backlog/stories/` + `sprint_backlog.md`",
    "archify": "Artefact HTML vectoriel interactif",
    "drawdb": "Interface DrawDB locale",
    "canvas": "`docs/05-assets/*.canvas`",
    "export-obsidian": "Coffre Obsidian structuré",
    "self-dev": "Code source sous `src/`",
    "worker-spawn": "Terminal PTY Herdr multiplexé",
    "worker-harvest": "Livrables intégrés sur disque",
    "wikifix": "`memory/wikifix_report.md`",
    "struct-check": "Rapport violations C1–C7",
    "rubber-duck": "Rapport sémantique 4 Piliers",
    "fact-check": "Certificat de véracité NLI",
    "sync": "Index FTS5 + Graphe sémantique",
    "jira_sync": "Tickets et champs Jira Cloud à jour",
    "notebooklm": "Export SSOT vers carnet officiel",
    "plugin-export": "Package AP 1.0 redistribuable",
    "guide-export": "Guide HTML autonome Plannotator",
    "dossier-init": "`memory/evidence/<STORY_ID>_fact_dossier.md`",
    "gate-approve": "`memory/lifecycle_state.json` (Porte validée)",
    "lifecycle-status": "Console / Historique du cycle de vie",
    "lifecycle-clean": "Nettoyage stories orphelines",
    "agent-resilience": "Score & Audit de Cyber-Résilience (ADR-0371)",
    "topology": "Cartographie Blast Radius & Surface d'Exposition",
    "rollback": "Restauration PITR de l'état et mémoire saine",
    "dream-rsi": "Méta-Politique Optimale (.mloop/dream_policy.json)",
    "multi-draft": "Rapport Challenge Multi-Drafts (ADR-0373)",
}


def _format_args(args_list: List[Dict[str, Any]]) -> str:
    """Formate les arguments CLI de façon lisible et compacte."""
    parts = []
    for a in args_list:
        name = a.get("name", "")
        req = a.get("required", False)
        typ = a.get("type", str)
        typ_name = typ.__name__ if hasattr(typ, "__name__") else "val"
        arg_str = f"{name} <{typ_name.upper()}>" if name.startswith("--") else f"<{name.upper()}>"
        if not req:
            arg_str = f"[{arg_str}]"
        parts.append(arg_str)
    return " ".join(parts) if parts else "*(Aucun)*"


def generate_guide_markdown() -> str:
    """Génère le texte Markdown complet et exhaustif pour CLI_PIPELINE_GUIDE.md."""
    total_commands = len(COMMANDS)

    lines = [
        "# 🧭 Guide Exhaustif du Pipeline Python CLI — Memory Loop (mLoop)",
        "",
        "**Statut** : SSOT Normatif & Guide de Référence Déterministe (ADR-0370)  ",
        "**Standard** : mLoop Core CLI Pipeline, Agent Plugins 1.0 & Python Senior Standards (ADR-0369)  ",
        f"**Commandes Actives** : {total_commands} Commandes Enregistrées dans `src/commands/_registry.py`  ",
        "**Date de Synchronisation** : 15 septembre 2026  ",
        "",
        "---",
        "",
        "## 1. 🌟 Vue d'Ensemble & Philosophie",
        "",
        "Le backend d'état **Memory Loop (mLoop)** est piloté par un moteur CLI unifié (`python src/swarm.py`). Il orchestre l'ensemble du cycle de vie des projets, depuis l'ingestion documentaire brute jusqu'à la synchronisation Jira/Git, la modélisation de données, et la livraison d'architectures prêtes pour les développeurs et agents IA (*Universal Dev Handoff*).",
        "",
        "### La Séquence d'Amorçage Obligatoire (Boot Sequence - ADR-0322)",
        "Au tout premier tour d'une session, l'orchestrateur exécute mécaniquement et sans exploration préalable :",
        "1. `python src/swarm.py resume --project <nom_projet>` : Restauration d'état et historique anti-amnésie.",
        "2. `python src/swarm.py vibe-check --project <nom_projet>` : Guardrail pré-vol de sécurité (17 contrôles stricts).",
        "3. `python src/swarm.py focus --project <nom_projet> --story <story_id>` : Verrou d'attention sur le récit cible.",
        "",
        "---",
        "",
        f"## 2. 🗺️ Matrice Complète des {total_commands} Commandes par Phase",
        "",
        "```mermaid",
        "flowchart LR",
        "    P0[\"0. INCEPTION<br>(Gathering & SOW)\"] --> P1[\"1. SPEC / INGEST<br>(Ingestion & Données)\"]",
        "    P1 --> P2[\"2. PLAN / ARCHI<br>(Analyse & Grill)\"]",
        "    P2 --> P3[\"3. BUILD / DEV<br>(Code & Workers)\"]",
        "    P3 --> P4[\"4. VALIDATE / QA<br>(Audit & Fact-Check)\"]",
        "    P4 --> P5[\"5. SHIP & SYNC<br>(Jira, Git & NotebookLM)\"]",
        "```",
        "",
    ]

    phase_order = ["sow", "spec", "plan", "build", "validate", "ship", "transverse"]

    for pkey in phase_order:
        pheader = PHASE_HEADERS[pkey]
        lines.append("---")
        lines.append("")
        lines.append(f"### {pheader['title']}")
        lines.append("")
        lines.append(f"> {pheader['desc']}")
        lines.append("")
        lines.append("| Commande CLI | Rôle / Description | Paramètres | Sorties / Artefacts Clés |")
        lines.append("| :--- | :--- | :--- | :--- |")

        # Filtrer et trier les commandes de cette phase
        cmds_in_phase = [
            (cname, COMMANDS[cname])
            for cname in sorted(COMMANDS.keys())
            if PHASE_MAPPING.get(cname) == pkey
        ]

        for cname, cmeta in cmds_in_phase:
            help_txt = cmeta.get("help", "").replace("|", "/")
            args_txt = _format_args(cmeta.get("args", [])).replace("|", "/")
            artefact_txt = ARTEFACTS_MAP.get(cname, "Console / Mémoire d'état")
            lines.append(f"| `python src/swarm.py {cname}` | {help_txt} | {args_txt} | {artefact_txt} |")

        lines.append("")

    lines.extend([
        "---",
        "",
        "## 3. ⌨️ Utilisation dans l'IDE OpenCode",
        "",
        "Dans l'environnement interactif OpenCode, l'ensemble des commandes sont invoquables via :",
        "",
        "1. **Le Dispatcher Universel** :",
        "   ```bash",
        "   /loop <action> [arguments]",
        "   # Exemples :",
        "   /loop resume --project BoireFrere_Segment2",
        "   /loop vibe-check --project BoireFrere_Segment2",
        "   /loop grill --project BoireFrere_Segment2",
        "   /loop guide --phase plan",
        "   /loop guide --sync   # Régénération automatique du guide CLI SSOT",
        "   ```",
        "",
        "2. **Gouvernance Anti-Drift Déterministe (ADR-0370)** :",
        "   Ce guide est le produit compilé de `src/commands/_registry.py`. Tout ajout de commande dans le code source Python est automatiquement répercuté lors de l'exécution de `python src/swarm.py guide --sync` ou par auto-healing lors du contrôle pré-vol `vibe-check`.",
        "",
    ])

    return "\n".join(lines)


def check_guide_parity() -> Tuple[bool, int, int, List[str]]:
    """
    Vérifie si le fichier CLI_PIPELINE_GUIDE.md est en parfaite parité avec _registry.py.
    Retourne (is_in_sync, total_registered, total_in_guide, missing_commands).
    """
    total_registered = len(COMMANDS)
    if not GUIDE_PATH.exists():
        return False, total_registered, 0, list(COMMANDS.keys())

    guide_content = GUIDE_PATH.read_text(encoding="utf-8")
    missing = []
    for cname in COMMANDS.keys():
        if f"`python src/swarm.py {cname}`" not in guide_content:
            missing.append(cname)

    is_in_sync = len(missing) == 0 and f"**Commandes Actives** : {total_registered}" in guide_content
    total_in_guide = total_registered - len(missing)
    return is_in_sync, total_registered, total_in_guide, missing


def sync_cli_guide() -> Tuple[bool, str]:
    """Régénère et écrit le fichier CLI_PIPELINE_GUIDE.md."""
    GUIDE_PATH.parent.mkdir(parents=True, exist_ok=True)
    new_content = generate_guide_markdown()
    GUIDE_PATH.write_text(new_content, encoding="utf-8")
    return True, f"CLI_PIPELINE_GUIDE.md synchronisé avec succès ({len(COMMANDS)} commandes actives)."
