"""
worker_signal.py - Protocole de signalisation sidecar (.status) pour workers mLoop (ADR-0355)

Inspiré du protocole léger de Sortie (.sortie/status), ce module permet aux sous-agents
de déclarer leur statut d'exécution sans couplage lourd ni appels d'outils complexes :
- COMPLETED : Mission terminée avec succès et livrables produits.
- BLOCKED : Agent bloqué par un manque d'information ou une contradiction.
- NEEDS_REVIEW : Agent sollicitant un arbitrage ou une revue humaine.
- NO_CHANGE_NEEDED : Agent certifiant qu'aucune modification n'était requise.
"""

from __future__ import annotations

import json
import time
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

from src.utils.logger import get_logger

logger = get_logger("worker_signal")


class WorkerSignalType(str, Enum):
    """Types de signaux officiels émis par un worker mLoop."""
    COMPLETED = "COMPLETED"
    BLOCKED = "BLOCKED"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    NO_CHANGE_NEEDED = "NO_CHANGE_NEEDED"

    @classmethod
    def from_raw(cls, raw: str) -> Optional[WorkerSignalType]:
        """Normalise et convertit une chaîne en WorkerSignalType (insensible à la casse/séparateurs)."""
        if not raw:
            return None
        norm = raw.strip().upper().replace("-", "_").replace(" ", "_")
        aliases = {
            "DONE": cls.COMPLETED,
            "SUCCESS": cls.COMPLETED,
            "PASS": cls.COMPLETED,
            "COMPLETED": cls.COMPLETED,
            "BLOCKED": cls.BLOCKED,
            "BLOCK": cls.BLOCKED,
            "STUCK": cls.BLOCKED,
            "NEEDS_REVIEW": cls.NEEDS_REVIEW,
            "NEEDS_HUMAN_REVIEW": cls.NEEDS_REVIEW,
            "REVIEW": cls.NEEDS_REVIEW,
            "NO_CHANGE": cls.NO_CHANGE_NEEDED,
            "NO_CHANGE_NEEDED": cls.NO_CHANGE_NEEDED,
            "UNCHANGED": cls.NO_CHANGE_NEEDED,
        }
        return aliases.get(norm)


class WorkerSignal(BaseModel):
    """
    Représentation structurée d'un signal sidecar émis par un sous-agent.
    """
    signal_type: WorkerSignalType
    story_id: str = ""
    reason: str = ""
    details: Dict[str, Any] = Field(default_factory=dict)
    timestamp: float = Field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.signal_type.value,
            "story_id": self.story_id,
            "reason": self.reason,
            "details": self.details,
            "timestamp": self.timestamp,
        }


def get_signal_file_paths(project_path: Path, story_id: str) -> list[Path]:
    """
    Retourne les chemins candidats où un fichier de statut peut être déposé par l'agent.
    Priorité :
    1. Projects/<proj>/memory/worker_<story_id>.status (avec '-' et '_')
    2. Projects/<proj>/.mloop/status
    3. <cwd>/memory/worker_<story_id>.status
    4. <cwd>/.mloop/status
    """
    clean_id = story_id.replace("\\", "/").split("/")[-1].replace(".md", "")
    underscore_id = clean_id.replace("-", "_")
    candidates = [
        project_path / "memory" / f"worker_{clean_id}.status",
        project_path / "memory" / f"worker_{underscore_id}.status",
        project_path / ".mloop" / "status",
        project_path / f"worker_{clean_id}.status",
        project_path / f"worker_{underscore_id}.status",
    ]
    cwd = Path.cwd()
    if cwd != project_path:
        candidates.extend([
            cwd / "memory" / f"worker_{clean_id}.status",
            cwd / "memory" / f"worker_{underscore_id}.status",
            cwd / ".mloop" / "status",
        ])
    return candidates


def resolve_signal_path(project_path: Path, story_id: str = "") -> Path:
    """Retourne le chemin canonique de statut sidecar pour un projet et un récit."""
    if story_id:
        clean_id = story_id.replace("\\", "/").split("/")[-1].replace(".md", "")
        return project_path / "memory" / f"worker_{clean_id}.status"
    return project_path / ".mloop" / "status"


def parse_signal_content(content: str, story_id: str = "") -> Optional[WorkerSignal]:
    """
    Parse le contenu d'un fichier statut (JSON ou clé: valeur / clé = valeur texte simple).
    """
    content = content.strip()
    if not content:
        return None

    # 1. Tentative JSON
    if content.startswith("{") and content.endswith("}"):
        try:
            data = json.loads(content)
            raw_status = data.get("status") or data.get("signal") or data.get("state", "")
            sig_type = WorkerSignalType.from_raw(raw_status)
            if sig_type:
                return WorkerSignal(
                    signal_type=sig_type,
                    story_id=data.get("story_id", story_id) or story_id,
                    reason=data.get("reason", ""),
                    details=data.get("details", {}),
                    timestamp=float(data.get("timestamp", time.time())),
                )
        except Exception as err:
            logger.debug(f"Échec parsing JSON pour le signal: {err}")

    # 2. Format texte clé-valeur (compatible Sortie .sortie/status)
    # Ex:
    # STATUS: BLOCKED
    # REASON: Spécification ambiguë pour le profilage API
    # ou STATUS = NO_CHANGE_NEEDED
    lines = content.splitlines()
    status_str = ""
    reason_str = ""
    parsed_story_id = story_id
    details: Dict[str, Any] = {}

    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        
        delimiter = None
        if ":" in line:
            delimiter = ":"
        elif "=" in line:
            delimiter = "="

        if delimiter:
            key, val = line.split(delimiter, 1)
            key = key.strip().upper()
            val = val.strip()
            if key in ("STATUS", "SIGNAL", "STATE"):
                status_str = val
            elif key in ("REASON", "MESSAGE", "CAUSE"):
                reason_str = val
            elif key in ("STORY_ID", "STORY"):
                parsed_story_id = val
            else:
                details[key.lower()] = val
        elif not status_str:
            # Ligne unique de statut direct, ex: "blocked" ou "no-change-needed"
            status_str = line

    sig_type = WorkerSignalType.from_raw(status_str)
    if sig_type:
        return WorkerSignal(
            signal_type=sig_type,
            story_id=parsed_story_id,
            reason=reason_str,
            details=details,
            timestamp=time.time(),
        )

    return None


parse_worker_signal = parse_signal_content


def read_worker_signal(project_path: Path, story_id: str) -> Optional[WorkerSignal]:
    """
    Lit et parse le signal sidecar d'un worker s'il existe.
    """
    candidates = get_signal_file_paths(project_path, story_id)
    for path in candidates:
        if path.is_file():
            try:
                raw = path.read_text(encoding="utf-8")
                signal = parse_signal_content(raw, story_id)
                if signal:
                    logger.info(f"Signal worker détecté depuis '{path}': {signal.signal_type.value} ({signal.reason})")
                    return signal
            except Exception as err:
                logger.warning(f"Erreur de lecture du fichier signal '{path}': {err}")
    return None


def write_worker_signal(
    project_path: Path,
    signal_or_story: Any,
    signal_type: Optional[WorkerSignalType] = None,
    reason: str = "",
    details: Optional[Dict[str, Any]] = None,
    use_json: bool = True
) -> Path:
    """
    Écrit un signal sidecar pour le worker spécifié.
    Supporte soit (project_path, signal: WorkerSignal) soit (project_path, story_id, signal_type, ...).
    """
    if isinstance(signal_or_story, WorkerSignal):
        sig = signal_or_story
        story_id = sig.story_id
    else:
        story_id = str(signal_or_story)
        sig = WorkerSignal(
            signal_type=signal_type or WorkerSignalType.COMPLETED,
            story_id=story_id,
            reason=reason,
            details=details or {},
            timestamp=time.time(),
        )

    if story_id:
        clean_id = story_id.replace("\\", "/").split("/")[-1].replace(".md", "")
        target_file = project_path / "memory" / f"worker_{clean_id}.status"
    else:
        target_file = project_path / ".mloop" / "status"

    target_file.parent.mkdir(parents=True, exist_ok=True)

    if use_json:
        target_file.write_text(json.dumps(sig.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
    else:
        content = f"STATUS: {sig.signal_type.value}\nREASON: {sig.reason}\n"
        if sig.details:
            for k, v in sig.details.items():
                content += f"{k.upper()}: {v}\n"
        target_file.write_text(content, encoding="utf-8")

    # Écrire également une copie dans .mloop/status pour consultation directe
    try:
        dot_mloop_file = project_path / ".mloop" / "status"
        dot_mloop_file.parent.mkdir(parents=True, exist_ok=True)
        dot_mloop_file.write_text(target_file.read_text(encoding="utf-8"), encoding="utf-8")
    except Exception as e:
        logger.warning(
            "Copie du statut worker vers .mloop/status échouée",
            exc_info=True,
            extra={
                "component": "core.worker_signal",
                "operation": "write_worker_signal",
                "error": str(e),
            },
        )

    return target_file

