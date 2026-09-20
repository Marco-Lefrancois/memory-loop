# -*- coding: utf-8 -*-
"""
Registre SSOT multi-runtimes des workers Herdr (ADR-0346 — Délégation Dual-Track).

Chaque runtime CLI de worker (opencode, cline, pi, omp, ...) est décrit par une
spécification déclarative `WorkerRuntimeSpec` :

- `one_shot_flags` : arguments activant l'exécution one-shot auto-approvée
  (opencode : `--yolo` ; cline 3.x : natif, aucun flag requis) ;
- `model_flag` : nom du flag de sélection modèle (valeur ajoutée à la suite) ;
- `default_model` : modèle par défaut (route LiteLLM nmedia_cloud) appliqué si
  aucun `--model` explicite n'est fourni (ex: Cline → glm-5.3-flash) ;
- `resolve_windows_binary` : résolution du binaire réel sous Windows — les shims
  npm (`.ps1`/`.cmd`) ne sont pas exécutables via Start-Process ("'%1' n'est pas
  une application Win32 valide"), donc on résout le `.exe` absolu du paquet npm
  (même piège avéré pour OpenCode et Cline).

Tout nouveau CLI (claude, aider, ...) = une entrée dans `WORKER_RUNTIMES` :
aucune branche conditionnelle supplémentaire dans `herdr_adapter`.
"""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional

# Modèle par défaut des missions de build déléguées au runtime Cline.
# Route LiteLLM nmedia_cloud (même proxy qu'OpenCode). Identifiant demandé
# explicitement par l'humain ; à confirmer à l'E2E (proxy injoignable 429
# lors de l'audit : `GET /v1/models` en échec temporaire).
DEFAULT_CLINE_MODEL = "nmedia_cloud/glm-5.3-flash"


@dataclass(frozen=True)
class WorkerRuntimeSpec:
    """Spécification déclarative d'un runtime CLI de worker (plug-in Herdr)."""

    kind: str
    one_shot_flags: List[str] = field(default_factory=list)
    model_flag: str = "--model"
    default_model: Optional[str] = None
    resolve_windows_binary: Optional[Callable[[], Optional[str]]] = None

    def build_flags(
        self, model: Optional[str] = None, extra_args: Optional[List[str]] = None
    ) -> List[str]:
        """Construit les arguments CLI du runtime pour un spawn Herdr.

        Sémantique historique préservée (herdr_adapter.spawn_story_worker) :
        les `extra_args` explicites court-circuitent les flags par défaut, puis
        le modèle est ajouté uniquement si son flag est absent de la ligne.
        """
        flags = list(extra_args) if extra_args else list(self.one_shot_flags)
        if model and "--model" not in flags and "-m" not in flags:
            flags.extend([self.model_flag, model])
        return flags

    def resolve_binary(self) -> Optional[str]:
        """Résout le binaire réel du runtime (Windows), sinon None (nom brut)."""
        if self.resolve_windows_binary is None:
            return None
        return self.resolve_windows_binary()


def _resolve_npm_windows_binary(bin_name: str) -> Optional[str]:
    """Résout le `.exe` npm réel sous Windows pour le binaire `bin_name`.

    Les shims npm (`<bin>.ps1`, `<bin>.cmd`) ne sont pas exécutables via
    Start-Process sous Windows : on résout donc le chemin absolu du `.exe`
    du paquet npm (`$APPDATA/npm/<bin>.exe`), sinon via shutil.which
    (résultat retenu uniquement s'il s'agit d'un `.exe`).
    """
    appdata = os.environ.get("APPDATA", "")
    exe_candidate = Path(appdata) / "npm" / f"{bin_name}.exe"
    if exe_candidate.exists():
        return str(exe_candidate)
    found = shutil.which(f"{bin_name}.exe") or shutil.which(bin_name)
    if found and found.endswith(".exe"):
        return found
    return None


WORKER_RUNTIMES: Dict[str, WorkerRuntimeSpec] = {
    # OpenCode — sémantique historique intangible (one-shot --yolo, pas de
    # modèle par défaut : la sélection reste pilotée par TASK_MODEL_MAP).
    "opencode": WorkerRuntimeSpec(
        kind="opencode",
        one_shot_flags=["--yolo"],
        resolve_windows_binary=lambda: _resolve_npm_windows_binary("opencode"),
    ),
    # Cline 3.x — one-shot auto-apprové par défaut (`--auto-approve: true`,
    # aucun équivalent de --yolo n'existe ; ground truth cline 3.0.62).
    "cline": WorkerRuntimeSpec(
        kind="cline",
        one_shot_flags=[],
        default_model=DEFAULT_CLINE_MODEL,
        resolve_windows_binary=lambda: _resolve_npm_windows_binary("cline"),
    ),
    # pi / omp — runtimes interactifs historiques (mode sans approbation +
    # sélection modèle, sans résolution binaire Windows dédiée).
    "pi": WorkerRuntimeSpec(
        kind="pi",
        one_shot_flags=["--dangerously-skip-permissions"],
    ),
    "omp": WorkerRuntimeSpec(
        kind="omp",
        one_shot_flags=["--dangerously-skip-permissions"],
    ),
}


def get_worker_runtime(kind: str) -> WorkerRuntimeSpec:
    """Retourne la spécification du runtime `kind`, sinon lève KeyError."""
    spec = WORKER_RUNTIMES.get(kind)
    if spec is None:
        raise KeyError(
            f"Runtime worker inconnu : '{kind}'. "
            f"Runtimes enregistrés : {sorted(WORKER_RUNTIMES)}"
        )
    return spec
