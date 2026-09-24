"""
Générateur Déterministe & Synchroniseur du Guide CLI SSOT (ADR-0370).
Garantit la parité absolue entre le code Python (src/commands/_registry.py)
et le guide de référence normatif (standards/protocols/CLI_PIPELINE_GUIDE.md).
"""

from pathlib import Path
from typing import Any, Dict, List, Tuple
from src.commands._registry import COMMANDS

GUIDE_PATH = Path("standards/protocols/CLI_PIPELINE_GUIDE.md")

from src.pipelines.guide_data import ARTEFACTS_MAP, PHASE_HEADERS, PHASE_MAPPING


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
        "    P4 --> P5[\"5. SHIP & SYNC<br>(Jira, Git & Distribution)\"]",
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
            if PHASE_MAPPING.get(cname, "transverse") == pkey
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
