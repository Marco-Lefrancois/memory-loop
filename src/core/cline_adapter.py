# -*- coding: utf-8 -*-
"""
Adaptateur runtime Cline CLI pour Herdr (ADR-0346 — Délégation Dual-Track).
Façade de compatibilité déléguant au registre SSOT multi-runtimes
`worker_runtimes` (source unique de vérité des flags et du routage modèle).

Ground truth locale (cline --help, version 3.0.62) :
- Le mode one-shot (prompt en argument) est auto-apprové par défaut
  (`--auto-approve`, default: true) — aucun équivalent de `--yolo` n'existe.
- Sélection modèle : `-m, --model <model-id>`.
- Binaire résolu via shim npm (`cline.ps1`/`cline.cmd`) : sous Windows,
  Start-Process exige le `.exe` réel (même pattern que OpenCode).
"""

from __future__ import annotations

import logging
from typing import List, Optional

from src.core.worker_runtimes import DEFAULT_CLINE_MODEL, get_worker_runtime

logger = logging.getLogger(__name__)

__all__ = ["DEFAULT_CLINE_MODEL", "build_cline_flags", "resolve_cline_binary"]


def build_cline_flags(
    model: Optional[str] = None, extra_args: Optional[List[str]] = None
) -> List[str]:
    """Construit les arguments CLI Cline pour un spawn Herdr one-shot.

    Args:
        model: Identifiant du modèle cible (route LiteLLM nmedia_cloud).
        extra_args: Si fourni, court-circuite la construction par défaut.

    Returns:
        Liste d'arguments prête pour `herdr agent start ... -- <flags>`.
    """
    return get_worker_runtime("cline").build_flags(model=model, extra_args=extra_args)


def resolve_cline_binary() -> Optional[str]:
    """Résout le binaire `cline.exe` réel pour le fallback Windows.

    Les shims npm (`cline.ps1`, `cline.cmd`) ne sont pas exécutables via
    Start-Process sous Windows ("%1 n'est pas une application Win32 valide") :
    on résout donc le chemin absolu du `.exe` npm, sinon via shutil.which.

    Returns:
        Chemin absolu du `.exe` si trouvé, sinon None (le fallback Herdr
        retombera alors sur le nom brut `cline`).
    """
    return get_worker_runtime("cline").resolve_binary()
