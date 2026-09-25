"""
Sous-module vibe_check/_vc_cascade.py — Check 28 (MLOOP-323-BE / EPIC-32 / ADR-0393).

Sonde « Story Cascade Drift Check » intégrée au guardrail pré-vol Vibe-Check.

Déceler toute promotion groupée de récits (génération en cascade) sans instruction
d'un dossier de preuves unitaire par récit, symptôme d'un contournement de la séance
d'arbitrage 1:1 dédiée (Grill-Me).

Règles (ADR-0393) :
  - Analyse les récits sous `backlog/stories/` au statut `READY_FOR_GROOMING`
    ou `READY_FOR_DEV` (statuts « gated » exigeant une preuve unitaire scellée).
  - Contrôle l'existence du dossier de preuves `memory/evidence/<ID>_fact_dossier.md`.
  - Détecte une vélocité anormale : ≥ 3 récits gated modifiés dans une fenêtre
    inférieure à 60 secondes ET au moins un orphelin de dossier de preuves.
  - Sévérité graduée par le cycle de vie : `WARNING` informatif en Phase 2 (PLAN),
    `FAIL` bloquant impératif en Phase 4 (VALIDATE) et Phase 5 (SHIP).

Verdict tri-état PASS / WARNING / FAIL. Zero Crash Policy : une anomalie isolée
ne provoque jamais l'arrêt brutal du guardrail global (dégradation en WARNING).

Conforme ADR-0202 (≤ 300L), ADR-0369 (typage, logging structuré, zéro except pass nu).
"""

from __future__ import annotations

from pathlib import Path

import yaml

from src.utils.logger import get_logger

logger = get_logger("pipelines.vibe_check._vc_cascade")

CHECK_LABEL = "Détection de Cascade (Check 28)"

# Statuts « engagés » (Palier 2) exigeant un dossier de preuves unitaire scellé.
_GATED_STATUSES = frozenset({"READY_FOR_GROOMING", "READY_FOR_DEV"})

# Étapes où le Check 28 est bloquant (FAIL sur cascade) : Phase 4 et Phase 5.
_BLOCKING_STAGE_TOKENS = ("VALIDATE", "SHIP", "STAGE_4", "STAGE_5", "QA")

# Fenêtre temporelle (secondes) et seuil de récits pour qualifier une cascade.
_CASCADE_WINDOW_S = 60.0
_CASCADE_MIN_COUNT = 3

_NS_PER_S = 1_000_000_000


def _is_blocking_stage(stage_label: str) -> bool:
    """Détermine si l'étape courante rend le Check 28 bloquant (Phase 4 ou 5)."""
    upper = (stage_label or "").upper()
    return any(token in upper for token in _BLOCKING_STAGE_TOKENS)


def _parse_gated_story(story_file: Path) -> tuple[str, int] | None:
    """
    Extrait (story_id, mtime_ns) d'un récit au statut « gated », sinon None.

    Le statut est lu depuis le frontmatter YAML ; l'identifiant retenu est le
    champ `id`, avec repli sur le nom de fichier (stem).
    """
    try:
        content = story_file.read_text(encoding="utf-8", errors="replace")
    except OSError:
        logger.debug(
            "Lecture d'un récit impossible pour le Check 28 (ignoré).",
            exc_info=True,
            extra={"check_name": "check_28_cascade", "file_path": str(story_file)},
        )
        return None

    if not content.startswith("---"):
        return None
    parts = content.split("---", 2)
    if len(parts) < 3:
        return None

    try:
        data = yaml.safe_load(parts[1])
    except yaml.YAMLError:
        logger.debug(
            "Frontmatter YAML illisible pour le Check 28 (ignoré).",
            exc_info=True,
            extra={"check_name": "check_28_cascade", "file_path": str(story_file)},
        )
        return None

    if not isinstance(data, dict):
        return None

    status = str(data.get("status") or "").strip().upper()
    if status not in _GATED_STATUSES:
        return None

    story_id = str(data.get("id") or story_file.stem).strip()
    try:
        mtime_ns = story_file.stat().st_mtime_ns
    except OSError:
        logger.debug(
            "mtime d'un récit illisible pour le Check 28 (ignoré).",
            exc_info=True,
            extra={"check_name": "check_28_cascade", "file_path": str(story_file)},
        )
        return None
    return story_id, mtime_ns


def _collect_gated_stories(project_dir: Path) -> list[tuple[str, int]]:
    """Moissonne les récits « gated » sous backlog/stories/ (hors README/archive)."""
    stories_dir = project_dir / "backlog" / "stories"
    if not stories_dir.exists():
        return []
    collected: list[tuple[str, int]] = []
    for story_file in stories_dir.rglob("*.md"):
        if story_file.name.lower() == "readme.md":
            continue
        if any(part in ("archive", "_archive", "archive_deprecated") for part in story_file.parts):
            continue
        parsed = _parse_gated_story(story_file)
        if parsed is not None:
            collected.append(parsed)
    return collected


def _has_fact_dossier(project_dir: Path, story_id: str) -> bool:
    """Vérifie l'existence du dossier de preuves unitaire du récit."""
    dossier = project_dir / "memory" / "evidence" / f"{story_id}_fact_dossier.md"
    return dossier.exists()


def _detect_velocity_cascade(mtimes_ns: list[int]) -> bool:
    """
    Détecte une écriture en rafale : ≥ _CASCADE_MIN_COUNT récits dont les mtime
    tiennent dans une fenêtre glissante de _CASCADE_WINDOW_S secondes.
    """
    if len(mtimes_ns) < _CASCADE_MIN_COUNT:
        return False
    ordered = sorted(mtimes_ns)
    window_ns = int(_CASCADE_WINDOW_S * _NS_PER_S)
    left = 0
    for right in range(len(ordered)):
        while ordered[right] - ordered[left] > window_ns:
            left += 1
        if right - left + 1 >= _CASCADE_MIN_COUNT:
            return True
    return False


def check_28_story_cascade_drift(project_path: Path, stage: str) -> dict:
    """
    Check 28 : détection de dérive de cascade de récits (MLOOP-323-BE).

    Args:
        project_path: Répertoire racine du projet (Projects/<projet>).
        stage: Libellé d'étape du cycle de vie (bloquant en Phase 4 et Phase 5).

    Returns:
        dict {"check": <libellé>, "status": "PASS"|"WARNING"|"FAIL"}.
        Ne lève jamais d'exception non gérée (Zero Crash Policy).
    """
    project_dir = Path(project_path)
    if not project_dir.exists():
        return {"check": CHECK_LABEL, "status": "PASS"}

    blocking = _is_blocking_stage(stage)

    try:
        gated = _collect_gated_stories(project_dir)
        if not gated:
            return {"check": CHECK_LABEL, "status": "PASS"}

        orphans = [sid for (sid, _mtime) in gated if not _has_fact_dossier(project_dir, sid)]
        cascade = _detect_velocity_cascade([mtime for (_sid, mtime) in gated]) and bool(orphans)
    except Exception:
        logger.error(
            "Erreur inattendue lors de l'audit de cascade Check 28 (isolée).",
            exc_info=True,
            extra={
                "check_name": "check_28_cascade",
                "violation_type": "audit_error",
                "project": str(project_dir),
            },
        )
        # Zero Crash : dégradation en WARNING plutôt que crash du guardrail.
        return {
            "check": f"{CHECK_LABEL} (audit interrompu — voir logs)",
            "status": "WARNING",
        }

    if not orphans:
        logger.debug(
            "Check 28 : tous les récits engagés disposent de leur dossier de preuves.",
            extra={"check_name": "check_28_cascade", "gated_count": len(gated)},
        )
        return {"check": CHECK_LABEL, "status": "PASS"}

    detail = ", ".join(orphans[:5])
    if len(orphans) > 5:
        detail += f" (+{len(orphans) - 5} autre(s))"

    cascade_flag = " — vélocité de cascade détectée (< 60s)" if cascade else ""
    status = "FAIL" if blocking else "WARNING"
    logger.debug(
        "Check 28 : récits engagés orphelins de dossier de preuves détectés.",
        extra={
            "check_name": "check_28_cascade",
            "orphan_count": len(orphans),
            "cascade": cascade,
            "blocking": blocking,
        },
    )
    return {
        "check": (
            f"{CHECK_LABEL} ({len(orphans)} récit(s) sans dossier de preuves "
            f"unitaire : {detail}{cascade_flag})"
        ),
        "status": status,
    }


__all__ = ["check_28_story_cascade_drift"]
