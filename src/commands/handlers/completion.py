"""
Handler CLI ``completion-setup`` (MLOOP-192-BE / EPIC-19 — ADR-0369/0370).

Adaptateur mince du contrat historique ``(args, state, project_path)`` vers le
moteur Click : la logique réside dans ``src.cli.click_engine.completion``.
Module **créé** pour cette story — aucun handler existant de ``handlers/*`` modifié
(contrainte de mission), et import paresseux du moteur Click (parité des handlers
voisins : démarrage argparse sans charger le package ``click_engine``).
"""

from __future__ import annotations

from typing import Any


def handle_completion_setup(args: Any, state: Any | None, project_path: Any | None) -> int:
    """Affiche l'instruction d'activation de l'autocomplétion shell (CA-5).

    ``state`` / ``project_path`` sont ``None`` : la commande est déclarée
    ``no_project: True`` dans le registre (exempte de Lifecycle Gate).
    """
    del args, state, project_path  # signature historique non consommée
    from src.cli.click_engine.completion import run_completion_setup

    return run_completion_setup()
