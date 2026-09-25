# -*- coding: utf-8 -*-
"""
_plan_act_guard.py - Garde-fou Plan/Act & Circuit-Breaker Cline (ADR-0202 <=300L).

Extrait de herdr_worker_core.py pour respecter le plafond modulaire (ADR-0202).
Regroupe :
  * PlanActGuard : évaluation déterministe fail-closed du mode Plan/Act (MLOOP-262-BE).
  * resolve_story_path : localisation du récit sous backlog/stories/.
  * start_with_circuit_breaker : bascule déterministe Cline -> OpenCode (MLOOP-263-BE).

Conforme ADR-0369 : typage strict, logging structuré, zéro `except Exception: pass` nu.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger("mloop.core.plan_act_guard")

# Statuts de maturité autorisant le Mode Act (écriture de code). Tout autre => Plan.
_ACT_STATUS = "READY_FOR_DEV"
_ACT_GRILL = "DONE"
_PLAN_FLAGS = ("--plan", "-p")

# Regex frontmatter : capture status et grill_me (valeurs entre quotes optionnelles).
_STATUS_RE = re.compile(r"^\s*status\s*:\s*['\"]?([A-Za-z0-9_\-]+)['\"]?", re.MULTILINE)
_GRILL_RE = re.compile(r"^\s*grill_me\s*:\s*['\"]?([A-Za-z0-9_\-]+)['\"]?", re.MULTILINE)


def resolve_story_path(
    project_name: str, story_id: str, root: Optional[Path] = None
) -> Optional[Path]:
    """Localise le fichier de récit sous Projects/<project>/backlog/stories/<id>.md.

    Retourne None si introuvable (déclenche le mode Plan fail-closed en amont).
    """
    base = root or Path.cwd()
    clean = str(story_id).replace("\\", "/")
    clean = clean.replace("Projects/", "").replace(f"{project_name}/", "")
    if clean.startswith("backlog/stories/"):
        clean = clean[len("backlog/stories/") :]
    elif clean.startswith("backlog/"):
        clean = clean[len("backlog/") :]
    if clean.endswith(".md"):
        clean = clean[:-3]
    candidates = [
        base / "Projects" / project_name / "backlog" / "stories" / f"{clean}.md",
        base / "backlog" / "stories" / f"{clean}.md",
    ]
    for cand in candidates:
        if cand.exists():
            return cand
    return None


class PlanActGuard:
    """Garde-fou déterministe d'application du mode Plan/Act pour Cline (MLOOP-262-BE)."""

    @staticmethod
    def evaluate_mode(story_path: Optional[str]) -> str:
        """Retourne 'plan' ou 'act' selon le statut de maturité du récit.

        Règle : 'act' si (status == READY_FOR_DEV ET grill_me == DONE), sinon 'plan'.
        Fail-closed : tout doute (fichier absent, illisible, YAML incomplet) => 'plan'.
        """
        if not story_path:
            logger.debug(
                "PlanActGuard.evaluate_mode : chemin de récit absent — mode 'plan' fail-closed.",
                extra={"story_path": story_path, "resolved_mode": "plan"},
            )
            return "plan"
        path = Path(story_path)
        if not path.exists():
            logger.debug(
                "PlanActGuard.evaluate_mode : récit introuvable — mode 'plan' fail-closed.",
                extra={"story_path": str(path), "resolved_mode": "plan"},
            )
            return "plan"
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            logger.debug(
                "PlanActGuard.evaluate_mode : lecture récit impossible — mode 'plan' fail-closed.",
                exc_info=True,
                extra={"story_path": str(path), "error": str(exc), "resolved_mode": "plan"},
            )
            return "plan"
        status_m = _STATUS_RE.search(text)
        grill_m = _GRILL_RE.search(text)
        status = status_m.group(1).strip().upper() if status_m else ""
        grill = grill_m.group(1).strip().upper() if grill_m else ""
        mode = "act" if (status == _ACT_STATUS and grill == _ACT_GRILL) else "plan"
        logger.debug(
            "PlanActGuard.evaluate_mode : mode évalué.",
            extra={
                "story_path": str(path),
                "status": status,
                "grill_me": grill,
                "resolved_mode": mode,
            },
        )
        return mode

    @staticmethod
    def enforce_flags(flags: List[str], mode: str) -> List[str]:
        """Injecte ou retire '--plan' selon le mode requis (idempotent).

        * mode 'plan' : garantit la présence de '--plan' (si ni '--plan' ni '-p').
        * mode 'act'  : purge tout résidu '--plan' / '-p'.
        """
        result = list(flags) if flags else []
        if mode == "act":
            return [f for f in result if f not in _PLAN_FLAGS]
        # mode 'plan' (défaut sécurisé)
        if not any(f in result for f in _PLAN_FLAGS):
            result.append("--plan")
        return result


def start_with_circuit_breaker(
    self: Any,
    worker_name: str,
    kind: str,
    pane_id: str,
    flags: List[str],
    target_model: Optional[str],
    extra_args: Optional[List[str]],
) -> Dict[str, Any]:
    """Démarre l'agent avec Circuit-Breaker déterministe Cline -> OpenCode (MLOOP-263-BE).

    Retourne un dict {'start_res': ..., 'kind': ..., 'flags': ...} reflétant le
    runtime effectivement démarré (Cline ou repli OpenCode).
    """

    def _fallback_flags() -> List[str]:
        from src.core.worker_runtimes import get_worker_runtime

        return get_worker_runtime("opencode").build_flags(model=target_model, extra_args=extra_args)

    start_res: Optional[Dict[str, Any]] = None
    effective_kind = kind
    effective_flags = flags
    try:
        start_res = self.start_agent(
            agent_name=worker_name, kind=effective_kind, pane_id=str(pane_id), extra_args=flags
        )
    except Exception as exc:  # noqa: BLE001 — repli résilient tracé (ADR-0369)
        if kind != "cline":
            logger.error(
                "Échec spawn agent non-Cline — propagation de l'exception.",
                exc_info=True,
                extra={"worker_id": worker_name, "agent_kind": kind, "error": str(exc)},
            )
            raise
        logger.warning(
            "Exception spawn Cline (%s). Déclenchement Circuit-Breaker : fallback OpenCode.",
            exc,
            extra={"worker_id": worker_name, "agent_kind": "cline"},
        )
        effective_kind = "opencode"
        effective_flags = _fallback_flags()
        start_res = self.start_agent(
            agent_name=worker_name,
            kind=effective_kind,
            pane_id=str(pane_id),
            extra_args=effective_flags,
        )

    if kind == "cline" and isinstance(start_res, dict) and not start_res.get("success"):
        logger.warning(
            "Échec start_agent Cline (%s). Déclenchement Circuit-Breaker : fallback OpenCode.",
            start_res.get("error"),
            extra={"worker_id": worker_name, "agent_kind": "cline"},
        )
        effective_kind = "opencode"
        effective_flags = _fallback_flags()
        start_res = self.start_agent(
            agent_name=worker_name,
            kind=effective_kind,
            pane_id=str(pane_id),
            extra_args=effective_flags,
        )

    return {"start_res": start_res, "kind": effective_kind, "flags": effective_flags}
