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
# Fournisseur natif Cline 3.x (ground truth @cline/llms/dist/models.js) :
# - Gratuit  : `cline-free/deepseek-v4.1-flash`  (confirmé dans le binaire installé)
# - Payant  : `cline-pass/deepseek-v4.1-flash`
# Ce modèle N'EST PAS routé via le proxy LiteLLM nmedia_cloud ; il utilise
# l'infrastructure Cline Bot Inc. directement (auto-approbation native,
# pas de clé utilisateur requise).
DEFAULT_CLINE_MODEL = "cline-free/deepseek-v4.1-flash"


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

    def needs_pane_run_fallback(self) -> bool:
        """Indique si le fallback `pane run` doit court-circuiter le lancement Herdr.

        Herdr lance l'agent via ``Start-Process`` sous Windows : un shim npm
        (``.cmd``/``.ps1``) échoue (« %1 n'est pas une application Win32 valide »)
        et **l'échec est asynchrone** — Herdr retourne ``launch_pending`` puis le
        volet meurt, produisant un worker fantôme. Dès que le binaire résolu
        n'est pas un ``.exe`` natif, le fallback déterministe est requis d'emblée.
        """
        binary = self.resolve_binary()
        return bool(binary) and not binary.lower().endswith(".exe")


def _resolve_npm_windows_binary(bin_name: str) -> Optional[str]:
    """Résout le binaire d'un CLI npm sous Windows pour le fallback pane-run.

    Deux topologies npm coexistent (ground truth locale) :

    - paquets embarquant un ``.exe`` (ex: ``opencode-ai``) — résolu en priorité ;
    - paquets ne générant que des shims (ex: ``cline``) → ``<bin>.cmd`` /
      ``<bin>.ps1``. Ces shims ne sont **pas** exécutables via ``Start-Process``
      ("%1 n'est pas une application Win32 valide") mais le sont via l'opérateur
      d'appel PowerShell ``& "<chemin>"`` employé par le fallback pane-run.

    Priorité de résolution : ``$APPDATA/npm/<bin>.exe`` → ``<bin>.cmd`` →
    ``shutil.which(<bin>.exe)`` → ``shutil.which(<bin>.cmd)``.
    """
    appdata = os.environ.get("APPDATA", "")
    npm_dir = Path(appdata) / "npm"
    for suffix in (".exe", ".cmd"):
        candidate = npm_dir / f"{bin_name}{suffix}"
        if candidate.exists():
            return str(candidate)
    for suffix in (".exe", ".cmd"):
        found = shutil.which(f"{bin_name}{suffix}")
        if found:
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
