# -*- coding: utf-8 -*-
"""
Contrôle C13 — Verrou d'état des récits (MLOOP-270-BE / ADR-011).

Corps de décision partagé par les deux portes du verrou anti-promotion :
  - **C13** (struct-check, par récit) : `assess_story_state_lock()` ;
  - **Check 25** (vibe-check, projet-wide) : `summarize_project_state_lock()`.

Règles tranchées (arbitrage OQ-270 — la FSM n'est PAS un ordre total : seule
l'appartenance à `GATED_STATUSES` est significative, jamais `>` / `>=`) :
  (a) `READY_FOR_DEV` sans `validated_by` / `validated_at` → BLOCKING toujours ;
  (b) entrée journal présente et `to_status != status`    → mismatch, BLOCKING si
      `strict` sinon WARNING ;
  (c) aucune entrée ET statut ∈ `GATED_STATUSES`          → mismatch, BLOCKING si
      `strict` sinon WARNING ;
  (d) aucune entrée ET statut ∉ `GATED_STATUSES`          → pas de violation.

Les statuts terminaux (`TERMINAL_STATUSES`) sont exemptés : jamais bloquants.

Contrat de non-écriture : le contrôle 25 appelle uniquement
`scan_transitions(apply_sanctions=False)` — aucun contrôle vibe-check ni
struct-check ne modifie jamais `backlog/` (Gate READ-ONLY ADR-0338).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from src.core.transition_journal import last_entry_for, read_entries
from src.pipelines import _story_lock_io as lock_io
from src.pipelines.story_status_lock import scan_transitions
from src.state import StoryStatus
from src.utils.logger import get_logger

logger = get_logger("pipelines._struct_c13")

# Identifiant du contrôle (registre vibe-check + revendication CA-4 du backfill).
CONTROL_NAME = "check_25_story_state_lock"

# Libellé canonique affiché dans le rapport vibe-check.
CONTROL_LABEL = "Verrou Anti-Promotion & Journal des Transitions (Check 25)"


def assess_story_state_lock(
    target_file: Path,
    frontmatter: Dict[str, Any],
    project_path: Path,
    strict: bool,
) -> List[Dict[str, Any]]:
    """Applique les règles (a)-(d) à un récit. Corps partagé C13 / Check 25.

    Args:
        target_file : fichier de récit audité (pour le stem en fallback d'`id`).
        frontmatter : frontmatter YAML déjà parsé par le struct-check.
        project_path : racine projet (racine du journal `story_transitions.jsonl`).
        strict : True ⇒ les mismatches journal/récit sont BLOCKING (sinon WARNING).

    Returns:
        Liste d'échecs normalisés `{"code", "severity", "message"}` (vide = conforme).
    """
    status = str(frontmatter.get("status") or "")
    if status in lock_io.TERMINAL_STATUSES:
        return []

    story_id = str(frontmatter.get("id") or Path(target_file).stem)
    mismatch_severity = "BLOCKING" if strict else "WARNING"
    issues: List[Dict[str, Any]] = []

    # (a) Promotion sans preuve d'approbation humaine — toujours BLOCKING.
    if status == StoryStatus.READY_FOR_DEV.value:
        missing = [
            key for key in lock_io.APPROVAL_KEYS if not str(frontmatter.get(key) or "").strip()
        ]
        if missing:
            issues.append(
                {
                    "code": "C13",
                    "severity": "BLOCKING",
                    "message": (
                        f"Le récit '{story_id}' est en READY_FOR_DEV sans "
                        f"approbation humaine tracée (champs manquants : "
                        f"{', '.join(missing)})."
                    ),
                }
            )

    # (b)/(c)/(d) Confrontation ligne d'état ↔ dernière entrée du journal.
    last = last_entry_for(project_path, story_id)
    if last is not None:
        journal_status = str(last.get("to_status") or "")
        if journal_status != status:
            issues.append(
                {
                    "code": "C13",
                    "severity": mismatch_severity,
                    "message": (
                        f"Le récit '{story_id}' diverge du journal des transitions "
                        f"(journal={journal_status} != récit={status}) — édition "
                        "brute de la ligne `status:` non journalisée."
                    ),
                }
            )
    elif status in lock_io.GATED_STATUSES:
        issues.append(
            {
                "code": "C13",
                "severity": mismatch_severity,
                "message": (
                    f"Le récit '{story_id}' est au statut engagé {status} sans "
                    "aucune entrée au journal story_transitions.jsonl (récit "
                    "engagé non journalisé)."
                ),
            }
        )
    return issues


def summarize_project_state_lock(project: Path, timeout_s: float = 10.0) -> Dict[str, Any]:
    """Verdict projet-wide du verrou (Check 25, forme `{"check", "status"}`).

    Décision, dans l'ordre :
      1. **CA-4** : revendication `control_claim` du Check 25 sans artefact réel
         sur disque ⇒ FAIL (revendication non corroborée) ;
      2. projet **non rétro-équipé** (`is_backfilled == False`) ⇒ PASS avec
         message WARNING (contrôle dégradé : les écarts legacy ne sont pas
         sanctionnables rétroactivement) ;
      3. sinon : tout écart **BLOCKING** du scan ⇒ FAIL, sinon PASS.

    Lecture seule : `apply_sanctions=False` — `backlog/` n'est jamais modifié.
    Une erreur logicielle inattendue est journalisée en ERROR puis dégradée en
    PASS (dégradation gracieuse, pattern C12) pour ne jamais faire échouer le
    guardrail pré-vol sur une anomalie du scanner.
    """
    project = Path(project)
    try:
        uncorroborated = _uncorroborated_claims(project)
        if uncorroborated:
            return {
                "check": (
                    f"{CONTROL_LABEL} : revendication(s) non corroborée(s) par un "
                    f"artefact sur disque ({', '.join(uncorroborated)}) — CA-4."
                ),
                "status": "FAIL",
            }

        scan = scan_transitions(project, apply_sanctions=False, timeout_s=timeout_s)
        issues = scan["issues"]

        if not scan["backfilled"]:
            return {
                "check": (
                    f"{CONTROL_LABEL} — WARNING : projet non rétro-équipé (aucune "
                    f"entrée origin=backfill), contrôle dégradé ({len(issues)} "
                    "écart(s) signalé(s) sans sanction)."
                ),
                "status": "PASS",
            }

        blocking = [issue for issue in issues if issue["severity"] == "BLOCKING"]
        if blocking:
            details = "; ".join(f"{issue['story_id']}: {issue['detail']}" for issue in blocking[:5])
            return {
                "check": (f"{CONTROL_LABEL} : {len(blocking)} écart(s) BLOCKING — {details}"),
                "status": "FAIL",
            }
        return {
            "check": f"{CONTROL_LABEL} — {len(issues)} écart(s) non bloquant(s).",
            "status": "PASS",
        }
    except Exception:
        logger.error(
            "Dégradation gracieuse Check 25 : scan du verrou impossible",
            exc_info=True,
            extra={"component": "pipelines._struct_c13", "operation": CONTROL_NAME},
        )
        return {
            "check": f"{CONTROL_LABEL} — WARNING : scan impossible (dégradation gracieuse).",
            "status": "PASS",
        }


def _uncorroborated_claims(project: Path) -> List[str]:
    """Revendications CA-4 du Check 25 dont l'artefact est absent du disque."""
    uncorroborated: List[str] = []
    for entry in read_entries(project):
        if entry.get("kind") != "control_claim":
            continue
        claim = entry.get("claim") or {}
        if claim.get("control") != CONTROL_NAME:
            continue
        artifact = Path(str(claim.get("artifact") or ""))
        resolved = artifact if artifact.is_absolute() else project / artifact
        if not resolved.exists():
            uncorroborated.append(str(artifact))
    return uncorroborated
