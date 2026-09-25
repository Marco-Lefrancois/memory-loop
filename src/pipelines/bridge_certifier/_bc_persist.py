"""
src/pipelines/bridge_certifier/_bc_persist.py — Lecture, persistance et rendu
du rapport de certification des ponts MCP (MLOOP-215-FULL).

Le JSON est l'artefact canonique ; le Markdown n'en est qu'un résumé lisible.
Toute écriture est atomique (fichier temporaire puis remplacement) pour qu'un
lecteur ne voie jamais un rapport tronqué pendant l'état ``CHARGEMENT``.

L'absence de rapport n'est **jamais** un verdict : c'est l'état
``INITIAL_VIDE``, que le contrôleur aval traduit en avertissement explicite
(« aucune certification exécutée ») et jamais en silence.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional

from src.pipelines.bridge_certifier._bc_models import (
    CertificationReport,
    SURFACE_ERREUR,
    SURFACE_INITIAL_VIDE,
    SURFACE_STATES,
    VERDICT_NON_CONFORME,
    ControlResult,
)

REPORT_FILENAME = "bridge_certification.json"
REPORT_MARKDOWN_FILENAME = "bridge_certification.md"

# Résumé pytest : « 1618 tests collected in 0.52s » / « 1437 passed, 5 skipped in 240.1s ».
_COUNTER_PATTERN = re.compile(
    r"(\d+)\s+(?:tests?\s+)?(collected|passed|failed|errors?|skipped|xfailed)\b"
)
_DURATION_PATTERN = re.compile(r"\bin\s+(\d+(?:\.\d+)?)s\b")


def dynamic_counters(payload: str) -> dict[str, Any]:
    """
    Extrait les compteurs **dynamiques** de la ligne récapitulative pytest
    (``123 passed, 4 failed in 12.34s``) d'une sortie ``-q``.

    Aucune valeur n'est devinée : une sortie illisible laisse ``collected`` à
    ``None`` et le contrôleur en conclut explicitement, sans jamais comparer à
    un nombre de tests figé (le compteur de la suite évolue à chaque récit).
    """
    counters: dict[str, Any] = {
        "collected": None,
        "passed": 0,
        "failed": 0,
        "errors": 0,
        "skipped": 0,
        "duration_s": None,
    }
    duration = _DURATION_PATTERN.search(payload or "")
    if duration:
        counters["duration_s"] = float(duration.group(1))
    for keyword, value in _COUNTER_PATTERN.findall(payload or ""):
        counters[keyword] = int(value)
    if counters["collected"] is None and (counters["passed"] + counters["failed"]) > 0:
        counters["collected"] = counters["passed"] + counters["failed"] + counters["skipped"]
    return counters


def report_paths(report_dir: Path) -> tuple[Path, Path]:
    """Chemins JSON (canonique) et Markdown (résumé) du rapport."""
    directory = Path(report_dir)
    return directory / REPORT_FILENAME, directory / REPORT_MARKDOWN_FILENAME


def read_certification_report(report_dir: Path) -> Optional[CertificationReport]:
    """
    Lit le rapport persisté ; retourne ``None`` en état ``INITIAL_VIDE``.

    Un fichier illisible n'est jamais dévoré : il est reconstruit comme un
    rapport d'état ``ERREUR`` pour que le contrôleur aval refuse d'en tirer un
    verdict ``CONFORME``.
    """
    path, _ = report_paths(report_dir)
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        broken = CertificationReport(surface_state=SURFACE_ERREUR, verdict=VERDICT_NON_CONFORME)
        broken.note("read_error", f"Rapport illisible : {exc}", level="error", path=str(path))
        return broken
    if not isinstance(payload, Mapping):
        broken = CertificationReport(surface_state=SURFACE_ERREUR, verdict=VERDICT_NON_CONFORME)
        broken.note("read_error", "Rapport non conforme au schéma attendu.", level="error")
        return broken
    return CertificationReport.from_dict(payload)


def surface_state_of(report: Optional[CertificationReport]) -> str:
    """État de surface observé par un lecteur (``INITIAL_VIDE`` si absent)."""
    if report is None:
        return SURFACE_INITIAL_VIDE
    return report.surface_state if report.surface_state in SURFACE_STATES else SURFACE_ERREUR


def write_certification_report(report: CertificationReport, report_dir: Path) -> tuple[Path, Path]:
    """Persiste le rapport JSON (atomique) et son résumé Markdown."""
    json_path, md_path = report_paths(report_dir)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    temp = json_path.with_suffix(".json.tmp")
    temp.write_text(report.to_json(), encoding="utf-8")
    temp.replace(json_path)
    md_path.write_text(render_markdown(report), encoding="utf-8")
    return json_path, md_path


def render_markdown(report: CertificationReport) -> str:
    """Résumé Markdown du rapport (le JSON reste l'artefact de preuve)."""
    lines = [
        f"# Certification des ponts MCP — {report.story_id}",
        "",
        f"- **Schéma** : `{report.schema}`",
        f"- **Exécuté le** : {report.executed_at}",
        f"- **Verdict** : `{report.verdict}`",
        f"- **État de surface** : `{report.surface_state}`",
        f"- **Exécutable** : `{'oui' if report.executable else 'non'}`",
        "- **Dépendances manquantes** : "
        + (", ".join(report.dependency_missing) if report.dependency_missing else "aucune"),
        "",
        "## Compteurs (dynamiques)",
        "",
        "| Clé | Valeur |",
        "| --- | --- |",
    ]
    for key, value in sorted(report.counters.items()):
        lines.append(f"| `{key}` | {value} |")
    lines += [
        "",
        "## Contrôles",
        "",
        "| Code | Niveau | Statut | Libellé | Diagnostic |",
        "| --- | --- | --- | --- | --- |",
    ]
    for control in report.controls:
        lines.append(
            f"| `{control.code}` | {control.level} | {control.status} | "
            f"{control.label} | {control.diagnostic} |"
        )
    if report.limits_admitted:
        lines += ["", "## Limites activement admises", ""]
        lines += [f"- {limit}" for limit in report.limits_admitted]
    if report.journal:
        lines += ["", "## Journal", ""]
        lines += [
            f"- `{entry.at}` **{entry.level}** `{entry.event}` — {entry.message}"
            for entry in report.journal
        ]
    lines.append("")
    return "\n".join(lines)


def summarize_controls(results: Iterable[ControlResult]) -> dict[str, int]:
    """Compteurs de contrôles pour la ligne de chargement à chaud."""
    controls = list(results)
    return {
        "controls_total": len(controls),
        "controls_passed": len([c for c in controls if c.passed]),
        "controls_failed": len([c for c in controls if not c.passed]),
    }
