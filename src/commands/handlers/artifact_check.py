"""
Handler CLI artifact-check — Harnais Multimodal d'Artefacts (MLOOP-304-FULL / EPIC-30).

Point d'entrée de la commande unifiée `python src/swarm.py artifact-check`.
Moissonne les artefacts visuels du projet (.svg, .html, .json, .canvas sous docs/
et backlog/) et les soumet aux trois harnais d'EPIC-30 :
  - DeterministicArtifactGate      (MLOOP-300-BE) — anti-raster-paste & openability.
  - ConnectorIntegrityValidator    (MLOOP-301-BE) — topologie fermée des connecteurs.
  - ArchitecturalAuditDecoupler    (MLOOP-303-BE) — score composite topo × visuel.

Émet un rapport consolidé sous memory/reports/artifact_audit_report.json et retourne
0 (tout vert) ou 1 (violation bloquante). Zero Crash Policy : une anomalie isolée est
journalisée sans arrêter l'audit global.

Options : --file (audit ciblé), --json (sortie CI/CD), --strict (S_topo = 1.0 requis).

Conforme ADR-0202 (≤ 300L), ADR-0369 (typage, context managers, logging structuré).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

from src.cli import ZeroFluffConsole
from src.utils.logger import get_logger

logger = get_logger("handler.artifact_check")

if TYPE_CHECKING:
    import argparse
    from src.state import LoopState

_ARTIFACT_SUFFIXES = {".svg", ".html", ".json", ".canvas"}
_SCAN_ROOTS = ("docs", "backlog")
_JSON_SKIP_NAMES = {
    "source_manifest.json",
    "lifecycle_state.json",
    "package.json",
    "package-lock.json",
    "tsconfig.json",
}


def _resolve_target_file(raw_target: str, project_path: Path) -> Path | None:
    """Résout un chemin de fichier ciblé (absolu, relatif projet ou tel quel)."""
    normalized = str(raw_target).replace("\\", "/")
    p_str = str(project_path).replace("\\", "/")
    if normalized.startswith(p_str):
        normalized = normalized[len(p_str) :].lstrip("/")
    candidate = Path(normalized) if Path(normalized).is_absolute() else (project_path / normalized)
    if candidate.exists() and candidate.is_file():
        return candidate
    direct = Path(raw_target)
    return direct if direct.exists() and direct.is_file() else None


def _collect_artifacts(project_path: Path) -> list[Path]:
    """Moissonne les artefacts visuels sous docs/ et backlog/ (hors archives/manifestes)."""
    artifacts: list[Path] = []
    for root_name in _SCAN_ROOTS:
        root = project_path / root_name
        if not root.exists():
            continue
        for candidate in root.rglob("*"):
            if not candidate.is_file() or candidate.suffix.lower() not in _ARTIFACT_SUFFIXES:
                continue
            if candidate.suffix.lower() == ".json" and candidate.name.lower() in _JSON_SKIP_NAMES:
                continue
            if any(
                p in ("archive", "_archive", "node_modules", "__pycache__") for p in candidate.parts
            ):
                continue
            artifacts.append(candidate)
    return artifacts


def _audit_artifact(artifact: Path, strict: bool) -> dict:
    """Audite un artefact unique via les trois harnais et retourne sa fiche de résultat."""
    from src.pipelines.artifact_gate import evaluate_artifact_gate
    from src.pipelines.connector_validator import validate_connector_integrity
    from src.pipelines.audit_decoupler import calculate_decoupled_architecture_score

    entry: dict = {"file": str(artifact), "verdict": "PASS", "errors": []}

    gate = evaluate_artifact_gate(artifact)
    entry["reason"] = gate.reason
    entry["raster_ratio"] = gate.raster_ratio
    entry["vector_elements_count"] = gate.vector_elements_count
    entry["checksum"] = gate.checksum
    if not gate.is_valid:
        entry["verdict"] = "FAIL"
        entry["errors"].append(gate.reason)

    topo_score = 1.0
    if artifact.suffix.lower() in {".json", ".canvas"}:
        try:
            payload = json.loads(artifact.read_text(encoding="utf-8", errors="strict"))
        except (json.JSONDecodeError, ValueError, OSError, UnicodeDecodeError):
            logger.debug(
                "Artefact JSON illisible ignoré pour la validation topologique.",
                exc_info=True,
                extra={"check_name": "artifact_check", "file_path": str(artifact)},
            )
            payload = None
        if isinstance(payload, dict) and ("nodes" in payload or "edges" in payload):
            topo = validate_connector_integrity(payload)
            entry["node_count"] = topo.node_count
            entry["edge_count"] = topo.edge_count
            if not topo.is_valid:
                topo_score = 0.4
                entry["verdict"] = "FAIL"
                entry["errors"].extend(topo.errors)

    audit = calculate_decoupled_architecture_score(topo_score, 1.0)
    entry["topology_score"] = topo_score
    entry["composite_score"] = audit.composite_score
    if strict and topo_score < 1.0:
        entry["verdict"] = "FAIL"
        entry["errors"].append("STRICT_TOPOLOGY_DEFICIT")
    return entry


def _write_report(project_path: Path, report: dict) -> Path:
    """Écrit le rapport consolidé sous memory/reports/artifact_audit_report.json."""
    reports_dir = project_path / "memory" / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    report_path = reports_dir / "artifact_audit_report.json"
    with report_path.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False)
    return report_path


def handle_artifact_check(
    args: "argparse.Namespace", state: "LoopState", project_path: Path
) -> int:
    """
    Exécute l'audit global (ou ciblé) des artefacts visuels du projet.

    Returns:
        int : 0 si tous les artefacts sont conformes, 1 en cas de violation bloquante.
    """
    project_path = Path(project_path)
    json_mode = bool(getattr(args, "json", False))
    strict = bool(getattr(args, "strict", False))
    target = getattr(args, "file", None)

    if target:
        resolved = _resolve_target_file(str(target), project_path)
        if resolved is None:
            if not json_mode:
                ZeroFluffConsole.error(f"Artefact introuvable : {target}")
            logger.error(
                "Cible artifact-check introuvable.",
                extra={
                    "check_name": "artifact_check",
                    "violation_type": "missing_target",
                    "file_path": str(target),
                },
            )
            return 1
        artifacts = [resolved]
    else:
        artifacts = _collect_artifacts(project_path)

    entries = [_audit_artifact(a, strict) for a in artifacts]
    fail_count = sum(1 for e in entries if e["verdict"] == "FAIL")
    pass_count = len(entries) - fail_count
    exit_code = 1 if fail_count > 0 else 0

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "project_path": str(project_path),
        "strict": strict,
        "total": len(entries),
        "pass": pass_count,
        "fail": fail_count,
        "verdict": "PASS" if exit_code == 0 else "FAIL",
        "artifacts": entries,
    }

    report_path = _write_report(project_path, report)

    if json_mode:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        ZeroFluffConsole.section("Audit d'Intégrité des Artefacts (EPIC-30 / Check 27)")
        for entry in entries:
            name = Path(entry["file"]).name
            if entry["verdict"] == "PASS":
                ZeroFluffConsole.success(
                    f"{name} : PASS (raster={entry['raster_ratio']}, score={entry['composite_score']})"
                )
            else:
                ZeroFluffConsole.error(f"{name} : FAIL — {', '.join(entry['errors'])}")
        ZeroFluffConsole.info(
            f"Bilan : {pass_count} PASS / {fail_count} FAIL sur {len(entries)} artefact(s)."
        )
        ZeroFluffConsole.value("Rapport scellé", str(report_path))

    logger.info(
        "artifact-check terminé.",
        extra={
            "check_name": "artifact_check",
            "total": len(entries),
            "pass": pass_count,
            "fail": fail_count,
            "exit_code": exit_code,
        },
    )
    return exit_code


__all__ = ["handle_artifact_check"]
