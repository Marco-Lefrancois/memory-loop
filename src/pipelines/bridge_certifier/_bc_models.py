"""
src/pipelines/bridge_certifier/_bc_models.py — Modèles du harnais de
certification des ponts MCP (MLOOP-215-FULL).

Contrat du rapport (ADR-0387 + micro-grill 215) : un rapport JSON unique,
artefact de preuve, décrit par un identifiant de schéma stable, un verdict
binaire, un **état de surface** parmi les 4 états autorisés, des compteurs de
tests calculés sur le compteur dynamique de pytest (jamais une valeur figée),
la liste des contrôles exécutés avec leur niveau de preuve, un journal structuré
et la liste des limites activement admises (*Admission of Limits*).

États de surface
----------------
- ``INITIAL_VIDE``   : aucun rapport persisté (état initial, lecture seule) ;
- ``CHARGEMENT``     : rapport en cours de production (journal à chaud) ;
- ``SUCCES``         : rapport persisté, verdict ``CONFORME`` ;
- ``ERREUR``         : rapport persisté, verdict ``NON_CONFORME``.

Le rapport est sérialisable sans dépendance externe (``dict`` + ``json``) :
un agent aval doit pouvoir le consommer sans aucune librairie additionnelle.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional

# ── Identifiants du contrat ───────────────────────────────────────────────────
SCHEMA_ID = "mloop.bridge_certification/1"
STORY_ID = "MLOOP-215-FULL"

# Limites d'isolement de structure de module (ADR-0387, pilier 4).
MODULE_MAX_LINES = 300
MODULE_MAX_BYTES = 15360

STATUS_PASS = "PASS"
STATUS_FAIL = "FAIL"
STATUSES = (STATUS_PASS, STATUS_FAIL)

VERDICT_CONFORME = "CONFORME"
VERDICT_NON_CONFORME = "NON_CONFORME"

SURFACE_INITIAL_VIDE = "INITIAL_VIDE"
SURFACE_CHARGEMENT = "CHARGEMENT"
SURFACE_SUCCES = "SUCCES"
SURFACE_ERREUR = "ERREUR"
SURFACE_STATES = (
    SURFACE_INITIAL_VIDE,
    SURFACE_CHARGEMENT,
    SURFACE_SUCCES,
    SURFACE_ERREUR,
)

# Échelle de preuve ADR-0385 : 1 lexico-fonctionnel, 2 structurel / intégration,
# 3 dynamique runtime (audit manuel des IDE réels — hors périmètre machine).
LEVEL_IN_PROCESS = 1
LEVEL_INTEGRATION = 2
LEVEL_MANUAL = 3
KNOWN_LEVELS = (LEVEL_IN_PROCESS, LEVEL_INTEGRATION, LEVEL_MANUAL)


class CertificationError(RuntimeError):
    """Rupture du harnais pendant l'exécution (état de surface ``ERREUR``)."""


@dataclass(frozen=True)
class ControlResult:
    """Résultat d'un contrôle de certification, horodaté et tracé."""

    code: str
    level: int
    label: str
    status: str
    diagnostic: str = ""
    details: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.status not in STATUSES:
            raise CertificationError(
                f"Statut inconnu {self.status!r} pour {self.code!r} (attendu {list(STATUSES)})."
            )
        if self.level not in KNOWN_LEVELS:
            raise CertificationError(
                f"Niveau de preuve inconnu {self.level!r} pour {self.code!r} "
                f"(attendu {list(KNOWN_LEVELS)})."
            )

    @property
    def passed(self) -> bool:
        return self.status == STATUS_PASS

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["details"] = dict(self.details)
        return data

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ControlResult":
        return cls(
            code=str(payload.get("code", "")),
            level=int(payload.get("level", LEVEL_IN_PROCESS)),
            label=str(payload.get("label", "")),
            status=str(payload.get("status", STATUS_FAIL)),
            diagnostic=str(payload.get("diagnostic", "")),
            details=dict(payload.get("details") or {}),
        )


@dataclass
class JournalEntry:
    """Ligne du journal structuré diffusé pendant l'état ``CHARGEMENT``."""

    at: str
    event: str
    level: str = "info"
    message: str = ""
    counters: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["counters"] = dict(self.counters)
        return data

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "JournalEntry":
        return cls(
            at=str(payload.get("at", "")),
            event=str(payload.get("event", "")),
            level=str(payload.get("level", "info")),
            message=str(payload.get("message", "")),
            counters=dict(payload.get("counters") or {}),
        )


def utc_now_iso() -> str:
    """Horodatage UTC ISO-8601 (toujours aware, jamais de fuseau local)."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class CertificationReport:
    """Rapport persisté de certification des ponts (artefact de preuve)."""

    executed_at: str = field(default_factory=utc_now_iso)
    verdict: str = VERDICT_NON_CONFORME
    surface_state: str = SURFACE_ERREUR
    executable: bool = True
    dependency_missing: list[str] = field(default_factory=list)
    counters: dict[str, Any] = field(default_factory=dict)
    controls: list[ControlResult] = field(default_factory=list)
    journal: list[JournalEntry] = field(default_factory=list)
    limits_admitted: list[str] = field(default_factory=list)
    scope: dict[str, Any] = field(default_factory=dict)
    schema: str = SCHEMA_ID
    story_id: str = STORY_ID

    @property
    def failed_controls(self) -> list[ControlResult]:
        return [c for c in self.controls if not c.passed]

    @property
    def passed_controls(self) -> list[ControlResult]:
        return [c for c in self.controls if c.passed]

    @property
    def is_conforme(self) -> bool:
        return self.verdict == VERDICT_CONFORME

    def control(self, code: str) -> Optional[ControlResult]:
        for item in self.controls:
            if item.code == code:
                return item
        return None

    def note(
        self, event: str, message: str, *, level: str = "info", **counters: Any
    ) -> JournalEntry:
        """Journalise une étape en état ``CHARGEMENT`` (compteurs à chaud)."""
        entry = JournalEntry(
            at=utc_now_iso(),
            event=event,
            level=level,
            message=message,
            counters=counters or dict(self.counters),
        )
        self.journal.append(entry)
        return entry

    def add(self, result: ControlResult) -> ControlResult:
        self.controls.append(result)
        self.note(
            "control",
            f"{result.code} → {result.status}",
            level="info" if result.passed else "error",
            code=result.code,
            status=result.status,
            passed=len(self.passed_controls),
            failed=len(self.failed_controls),
        )
        return result

    def finalize(self) -> "CertificationReport":
        """Calcule verdict et état de surface une fois les contrôles clos."""
        failing = self.failed_controls
        self.verdict = VERDICT_CONFORME if not failing else VERDICT_NON_CONFORME
        self.surface_state = SURFACE_SUCCES if not failing else SURFACE_ERREUR
        self.note(
            "finalize",
            f"Verdict {self.verdict} ({len(self.passed_controls)}/{len(self.controls)} contrôles).",
            level="info" if not failing else "error",
            verdict=self.verdict,
            failed=len(failing),
        )
        return self

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "story_id": self.story_id,
            "executed_at": self.executed_at,
            "verdict": self.verdict,
            "surface_state": self.surface_state,
            "executable": self.executable,
            "dependency_missing": list(self.dependency_missing),
            "scope": dict(self.scope),
            "counters": dict(self.counters),
            "controls": [c.to_dict() for c in self.controls],
            "journal": [j.to_dict() for j in self.journal],
            "limits_admitted": list(self.limits_admitted),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "CertificationReport":
        return cls(
            executed_at=str(payload.get("executed_at", "")),
            verdict=str(payload.get("verdict", VERDICT_NON_CONFORME)),
            surface_state=str(payload.get("surface_state", SURFACE_ERREUR)),
            executable=bool(payload.get("executable", True)),
            dependency_missing=list(payload.get("dependency_missing") or []),
            counters=dict(payload.get("counters") or {}),
            controls=[ControlResult.from_dict(c) for c in payload.get("controls") or []],
            journal=[JournalEntry.from_dict(j) for j in payload.get("journal") or []],
            limits_admitted=list(payload.get("limits_admitted") or []),
            scope=dict(payload.get("scope") or {}),
            schema=str(payload.get("schema", SCHEMA_ID)),
            story_id=str(payload.get("story_id", STORY_ID)),
        )

    def to_json(self, *, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)


def summarize_controls(results: Iterable[ControlResult]) -> dict[str, int]:
    """Compteurs de contrôles pour la ligne de chargement à chaud."""
    controls = list(results)
    return {
        "controls_total": len(controls),
        "controls_passed": len([c for c in controls if c.passed]),
        "controls_failed": len([c for c in controls if not c.passed]),
    }


def default_report_dir(project_root: Path) -> Path:
    """Emplacement canonique du rapport : ``<projet>/memory/evidence``."""
    return Path(project_root) / "memory" / "evidence"
