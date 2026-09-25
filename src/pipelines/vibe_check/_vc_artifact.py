"""
Sous-module vibe_check/_vc_artifact.py — Check 27 (MLOOP-304-FULL / EPIC-30).

Contrôle d'intégrité « Fidélité Topologique & Intégrité des Artefacts » intégré
au guardrail pré-vol Vibe-Check. Bloquant en Phase 2 (PLAN & ANALYSE, Gate 2 DoR)
et en Phase 4 (VALIDATE, Gate 4 Recette QA) ; informatif (PASS) sinon.

Moissonne les artefacts visuels du projet (.svg, .html, .json, .canvas sous docs/
et backlog/) et les soumet à la porte déterministe DeterministicArtifactGate
(MLOOP-300-BE) et au validateur topologique ConnectorIntegrityValidator (MLOOP-301-BE).

Verdict tri-état PASS / WARNING / FAIL. Zero Crash Policy : une anomalie isolée sur
un artefact ne provoque jamais l'arrêt brutal du guardrail global.

Conforme ADR-0202 (≤ 300L), ADR-0369 (typage, logging structuré, zéro except pass nu).
"""

from __future__ import annotations

import json
from pathlib import Path

from src.utils.logger import get_logger

logger = get_logger("pipelines.vibe_check._vc_artifact")

CHECK_LABEL = "Fidélité Topologique & Intégrité des Artefacts (Check 27 / EPIC-30)"

# Étapes où le Check 27 est bloquant (FAIL sur violation).
_BLOCKING_STAGE_TOKENS = ("PLAN", "VALIDATE", "STAGE_2", "STAGE_4", "GRILL")

# Extensions d'artefacts moissonnés.
_ARTIFACT_SUFFIXES = {".svg", ".html", ".json", ".canvas"}

# Répertoires racines scannés (relatifs au projet).
_SCAN_ROOTS = ("docs", "backlog")

# Fichiers JSON à ignorer (non-artefacts : état, manifeste, configs).
_JSON_SKIP_NAMES = {
    "source_manifest.json",
    "lifecycle_state.json",
    "package.json",
    "package-lock.json",
    "tsconfig.json",
}


def _is_blocking_stage(stage_label: str) -> bool:
    """Détermine si l'étape courante rend le Check 27 bloquant (Phase 2 ou 4)."""
    upper = (stage_label or "").upper()
    return any(token in upper for token in _BLOCKING_STAGE_TOKENS)


def _collect_artifacts(project_dir: Path) -> list[Path]:
    """Moissonne les fichiers d'artefacts visuels sous docs/ et backlog/."""
    artifacts: list[Path] = []
    for root_name in _SCAN_ROOTS:
        root = project_dir / root_name
        if not root.exists():
            continue
        for candidate in root.rglob("*"):
            if not candidate.is_file():
                continue
            if candidate.suffix.lower() not in _ARTIFACT_SUFFIXES:
                continue
            if candidate.suffix.lower() == ".json" and candidate.name.lower() in _JSON_SKIP_NAMES:
                continue
            if any(
                part in ("archive", "_archive", "node_modules", "__pycache__")
                for part in candidate.parts
            ):
                continue
            artifacts.append(candidate)
    return artifacts


def _audit_single_artifact(artifact: Path) -> list[str]:
    """Soumet un artefact à la porte déterministe et au validateur topologique."""
    from src.pipelines.artifact_gate import evaluate_artifact_gate
    from src.pipelines.connector_validator import validate_connector_integrity

    failures: list[str] = []

    gate = evaluate_artifact_gate(artifact)
    if not gate.is_valid:
        failures.append(f"{artifact.name}:[{gate.reason}]")

    # Contrôle topologique additionnel pour les spécifications JSON IR de diagrammes.
    if artifact.suffix.lower() in {".json", ".canvas"}:
        try:
            payload = json.loads(artifact.read_text(encoding="utf-8", errors="strict"))
        except (json.JSONDecodeError, ValueError, OSError, UnicodeDecodeError):
            logger.debug(
                "Artefact JSON illisible ignoré pour la validation topologique.",
                exc_info=True,
                extra={"check_name": "check_27_artifact", "file_path": str(artifact)},
            )
            return failures
        if isinstance(payload, dict) and ("nodes" in payload or "edges" in payload):
            topo = validate_connector_integrity(payload)
            if not topo.is_valid:
                first_error = topo.errors[0] if topo.errors else "CONNECTOR_INTEGRITY_FAIL"
                failures.append(f"{artifact.name}:[{first_error}]")

    return failures


def check_27_artifact_topology(project_path: Path, stage: str) -> dict:
    """
    Check 27 : intégrité topologique et anti-raster-paste des artefacts du projet.

    Args:
        project_path: Répertoire racine du projet (Projects/<projet>).
        stage: Libellé d'étape du cycle de vie (bloquant en Phase 2 et Phase 4).

    Returns:
        dict {"check": <libellé>, "status": "PASS"|"WARNING"|"FAIL"}.
        Ne lève jamais d'exception non gérée (Zero Crash Policy).
    """
    project_dir = Path(project_path)
    blocking = _is_blocking_stage(stage)

    if not project_dir.exists():
        return {"check": CHECK_LABEL, "status": "PASS"}

    all_failures: list[str] = []
    scanned = 0
    try:
        artifacts = _collect_artifacts(project_dir)
        for artifact in artifacts:
            scanned += 1
            all_failures.extend(_audit_single_artifact(artifact))
    except Exception:
        logger.error(
            "Erreur inattendue lors de l'audit d'artefacts Check 27 (isolée).",
            exc_info=True,
            extra={
                "check_name": "check_27_artifact",
                "violation_type": "audit_error",
                "project": str(project_dir),
            },
        )
        # Zero Crash : dégradation en WARNING plutôt que crash du guardrail.
        return {
            "check": f"{CHECK_LABEL} (audit interrompu — voir logs)",
            "status": "WARNING",
        }

    if not all_failures:
        logger.debug(
            "Check 27 : tous les artefacts sont conformes.",
            extra={"check_name": "check_27_artifact", "scanned": scanned},
        )
        return {"check": CHECK_LABEL, "status": "PASS"}

    detail = ", ".join(all_failures[:5])
    if len(all_failures) > 5:
        detail += f" (+{len(all_failures) - 5} autre(s))"

    status = "FAIL" if blocking else "WARNING"
    logger.debug(
        "Check 27 : artefacts non conformes détectés.",
        extra={
            "check_name": "check_27_artifact",
            "scanned": scanned,
            "failure_count": len(all_failures),
            "blocking": blocking,
        },
    )
    return {
        "check": f"{CHECK_LABEL} ({len(all_failures)} violation(s) : {detail})",
        "status": status,
    }


__all__ = ["check_27_artifact_topology"]
