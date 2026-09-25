"""
Grill Guards — mLoop (ADR-0393 / MLOOP-322-BE).

Barrières d'écriture protégeant l'étanchéité du scope macro transverse.

L'exécution d'un grill sur un périmètre transverse (`EPIC` ou `PROJECT`) a
l'interdiction technique absolue de modifier les fichiers sous `backlog/stories/`.
Ce module fournit un gestionnaire de contexte qui capture un instantané des
horodatages de modification (mtime) des récits avant l'opération transverse et
lève `LifecycleAuthorityError` si une mutation est détectée à la sortie.
"""

from __future__ import annotations

import datetime
import json
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, Iterator, Optional

from src.pipelines._fsm_authority import LifecycleAuthorityError
from src.utils.logger import get_logger

logger = get_logger("pipelines.grill.guards")

# Scopes transverses interdisant toute mutation de récit (ADR-0393).
TRANSVERSE_SCOPES = frozenset({"EPIC", "PROJECT"})


def log_lifecycle_violation(
    project_path: Path, story_id: Optional[str], violation: str, scope: str = "STORY"
) -> None:
    """
    Consigne une infraction d'autorité de cycle de vie dans le journal d'audit
    `memory/audit_lifecycle_violations.jsonl` (ADR-0393 / MLOOP-322-BE).

    Helper partagé par GrillEngine et le gestionnaire CLI pour éviter la
    duplication et maintenir les modules sous le plafond de 300 lignes (ADR-0202).
    """
    entry = {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "project": project_path.name,
        "story_id": story_id or "",
        "violation": violation,
        "scope": scope,
    }
    audit_file = project_path / "memory" / "audit_lifecycle_violations.jsonl"
    try:
        audit_file.parent.mkdir(parents=True, exist_ok=True)
        with open(audit_file, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError as exc:
        logger.debug(
            "Écriture du journal d'audit lifecycle échouée",
            exc_info=True,
            extra={
                "component": "pipelines.grill.guards",
                "operation": "log_lifecycle_violation",
                "story_id": story_id or "",
                "error": str(exc),
            },
        )


def _snapshot_mtimes(stories_dir: Path) -> Dict[str, float]:
    """Capture les mtime de tous les récits Markdown sous stories_dir."""
    snapshot: Dict[str, float] = {}
    if not stories_dir.exists():
        return snapshot
    for story_file in stories_dir.rglob("*.md"):
        try:
            snapshot[str(story_file)] = story_file.stat().st_mtime_ns
        except OSError as exc:
            logger.debug(
                "Impossible de lire le mtime d'un récit, ignoré du snapshot",
                exc_info=True,
                extra={
                    "component": "pipelines.grill.guards",
                    "operation": "snapshot_mtimes",
                    "file": str(story_file),
                    "error": str(exc),
                },
            )
    return snapshot


def assert_grill_target_allowed(
    project_path: Path, story_id: str, target_status: Optional[str]
) -> None:
    """
    Bridage strict (ADR-0393 / MLOOP-322-BE) : le moteur de grill ne peut JAMAIS
    promouvoir un récit au-delà de READY_FOR_GROOMING.

    Toute demande machine visant READY_FOR_DEV (ou tout autre statut) est une
    tentative de contournement de la Gate 2 (autorité humaine exclusive) : elle
    est journalisée puis rejetée en Fail-Closed via LifecycleAuthorityError.
    Un `target_status` à None laisse passer (comportement par défaut = grooming).
    """
    if target_status is None:
        return

    from src.state import StoryStatus

    requested = StoryStatus.from_raw(target_status)
    if requested == StoryStatus.READY_FOR_GROOMING:
        return

    log_lifecycle_violation(
        project_path,
        story_id,
        f"mark_story_grilled a reçu target_status={requested.value} "
        f"(seul READY_FOR_GROOMING est autorisé)",
        scope="STORY",
    )
    raise LifecycleAuthorityError(
        f"[BRIDAGE GRILL BLOQUANT] mark_story_grilled ne peut promouvoir le récit "
        f"'{story_id}' qu'au statut READY_FOR_GROOMING (demandé : {requested.value}).\n"
        f"➡ La transition vers READY_FOR_DEV relève exclusivement de l'autorité "
        f"humaine nominative en Gate 2."
    )


@contextmanager
def assert_no_story_mutation(scope: str, stories_dir: Path) -> Iterator[None]:
    """
    Gestionnaire de contexte interdisant toute mutation de récit sous
    `stories_dir` lorsque le `scope` est transverse (`EPIC` ou `PROJECT`).

    Capture un instantané des mtime à l'entrée et vérifie à la sortie qu'aucun
    fichier n'a été créé, supprimé ou modifié. Lève `LifecycleAuthorityError`
    (Fail-Closed) si une mutation est détectée.

    Pour un scope non transverse (ex: `STORY`), le garde est inactif et laisse
    passer les mutations légitimes du micro-grill unitaire.
    """
    normalized = (scope or "").strip().upper()
    if normalized not in TRANSVERSE_SCOPES:
        yield
        return

    before = _snapshot_mtimes(stories_dir)
    try:
        yield
    finally:
        after = _snapshot_mtimes(stories_dir)

        created = sorted(set(after) - set(before))
        deleted = sorted(set(before) - set(after))
        modified = sorted(path for path in set(before) & set(after) if before[path] != after[path])

        if created or deleted or modified:
            violations = {
                "created": created,
                "deleted": deleted,
                "modified": modified,
            }
            logger.error(
                "Mutation de récit détectée en scope transverse (interdit)",
                extra={
                    "component": "pipelines.grill.guards",
                    "operation": "assert_no_story_mutation",
                    "scope": normalized,
                    "violations": violations,
                },
            )
            detail_lines = []
            for label, files in (
                ("Créés", created),
                ("Supprimés", deleted),
                ("Modifiés", modified),
            ):
                for path in files:
                    detail_lines.append(f"  - [{label}] {path}")
            details = "\n".join(detail_lines)
            raise LifecycleAuthorityError(
                f"[ÉTANCHÉITÉ SCOPE MACRO BLOQUANTE] Le grill transverse "
                f"(scope={normalized}) a tenté de muter des fichiers sous "
                f"backlog/stories/, ce qui est techniquement interdit.\n"
                f"{details}\n"
                f"➡ Un grill EPIC/PROJECT tranche les choix d'architecture "
                f"transverses uniquement ; la rédaction/mutation de récits exige "
                f"un mandat unitaire explicite (grill-me --story <ID>)."
            )
