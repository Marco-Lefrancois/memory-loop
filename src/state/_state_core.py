# src/state/_state_core.py — Noyau d'état mLoop (MLOOP-173-BE)
# Familles : exceptions, enums, modèles Pydantic, SavepointManager
# Rétrocompatibilité ADR-0202 — ne pas instancier LoopState ici (§3.2)

import json
import time
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from src.core.layout import ProjectLayout, load_adr_contracts as _load_adr_contracts  # noqa: F401
from src.utils.logger import get_logger

logger = get_logger("state")

# ─── Exceptions

class LoopStateError(Exception):
    """Exception de base pour le moteur d'état mLoop."""

    pass

class IntegrityError(LoopStateError):
    """Exception levée en cas de violation d'intégrité de l'état."""

    pass

class MaxRevisionsReached(LoopStateError):
    """Exception levée par le circuit breaker lors d'un cycle infini."""

    pass

# ─── Enums

class LoopPhase(str, Enum):
    SPEC = "spec"
    PLAN = "plan"
    BUILD = "build"
    VALIDATE = "validate"
    SHIP = "ship"
    ERROR = "error"

class ProjectMode(str, Enum):
    """
    Détermine le cycle de vie applicable au LoopState.
    CLIENT : SPEC → PLAN → VALIDATE. MLOOP : cycle complet 5 phases.
    """

    CLIENT = "client"
    MLOOP = "mloop"

class StoryType(str, Enum):
    """Types officiels de récits dans mLoop (Frontmatter YAML)."""

    FEATURE = "Feature"
    ARCHITECTURE = "Architecture"
    TECHNICAL_DEBT = "Technical_Debt"
    BUG = "Bug"
    SPIKE = "Spike"

    @classmethod
    def from_raw(cls, raw: str) -> "StoryType":
        """Parse case-insensitive et normalise le type de récit."""
        if not raw:
            return cls.FEATURE
        norm = raw.strip().lower().replace("-", "_").replace(" ", "_")
        mapping = {
            "feature": cls.FEATURE,
            "architecture": cls.ARCHITECTURE,
            "technical_debt": cls.TECHNICAL_DEBT,
            "tech_debt": cls.TECHNICAL_DEBT,
            "debt": cls.TECHNICAL_DEBT,
            "bug": cls.BUG,
            "hotfix": cls.BUG,
            "spike": cls.SPIKE,
        }
        return mapping.get(norm, cls.FEATURE)

class StoryStatus(str, Enum):
    """
    Statuts officiels du cycle de vie d'un récit mLoop.
    CLIENT : OPEN → IN_ANALYZE → IN_PLAN → IN_VALIDATE → READY_FOR_GROOMING → READY_FOR_DEV → IN_DEV → IN_QA → ACCEPTED
    MLOOP  : OPEN → IN_ANALYZE → IN_PLAN → IN_BUILD → IN_VALIDATE → SHIPPED
    """

    # ─── Commun aux deux modes ─────────────────────────────────────
    DRAFT = "DRAFT"
    BACKLOG = "BACKLOG"
    OPEN = "OPEN"
    IN_ANALYZE = "IN_ANALYZE"
    IN_PLAN = "IN_PLAN"
    IN_REVIEW = "IN_REVIEW"
    IN_VALIDATE = "IN_VALIDATE"
    ON_HOLD = "ON_HOLD"
    ERROR = "ERROR"
    # ─── Mode CLIENT ───────────────────────────────────────────────
    READY_FOR_GROOMING = "READY_FOR_GROOMING"
    READY_FOR_DEV = "READY_FOR_DEV"
    IN_DEV = "IN_DEV"
    IN_QA = "IN_QA"
    DONE = "DONE"
    ACCEPTED = "ACCEPTED"
    # ─── Mode MLOOP uniquement ─────────────────────────────────────
    IN_BUILD = "IN_BUILD"
    SHIPPED = "SHIPPED"

    @classmethod
    def from_raw(cls, raw: str) -> "StoryStatus":
        """Parse case-insensitive depuis le frontmatter YAML. Retourne OPEN pour valeur inconnue."""
        normalized = raw.strip().upper().replace(" ", "_").replace("-", "_")
        try:
            return cls(normalized)
        except ValueError:
            return cls.OPEN

# ─── Modèles Pydantic

class TokenBudget(BaseModel):
    """Circuit Breaker Financier — compteur de tokens LLM consommés."""

    tokens_used: int = 0
    max_tokens: int = Field(
        default_factory=lambda: int(__import__("os").getenv("MLOOP_MAX_TOKENS", "50000"))
    )

    @property
    def is_exhausted(self) -> bool:
        """Retourne True si le budget est épuisé."""
        return self.tokens_used >= self.max_tokens

    def consume(self, tokens: int) -> None:
        """Incrémente le compteur de tokens consommés."""
        self.tokens_used += tokens

class Directives(BaseModel):
    tech: str = ""
    business: str = ""

class KnowledgeGraph(BaseModel):
    nodes: List[Dict[str, Any]] = Field(default_factory=list)
    edges: List[Dict[str, Any]] = Field(default_factory=list)

class Clarification(BaseModel):
    question: str
    answer: Optional[str] = None

_GRILLED_STATUSES = frozenset(
    {
        "IN_REVIEW",
        "READY_FOR_GROOMING",
        "READY_FOR_DEV",
        "IN_DEV",
        "IN_QA",
        "DONE",
        "ACCEPTED",
    }
)

class SprintBacklogItem(BaseModel):
    id: str
    title: str
    description: str
    type: StoryType = StoryType.FEATURE
    components: List[str] = Field(default_factory=list)
    jira_key: Optional[str] = None
    status: StoryStatus = StoryStatus.OPEN
    invest_score: str = "N/A"
    clarifications: List[Clarification] = Field(default_factory=list)

    @property
    def grilled(self) -> bool:
        """Compatibilité ascendante : True si le récit est prêt pour la revue humaine."""
        return self.status.value in _GRILLED_STATUSES

    @property
    def jira_sync_eligible(self) -> bool:
        """Règle mLoop : statuts éligibles à la synchronisation Jira Cloud."""
        return self.status.value in _GRILLED_STATUSES

class AnalysisResult(BaseModel):
    intent: str = ""
    constraints: List[str] = Field(default_factory=list)
    missing_information: List[str] = Field(default_factory=list)

class PlanStep(BaseModel):
    step_id: int
    action: str
    expected_output: str

class PlanResult(BaseModel):
    steps: List[PlanStep] = Field(default_factory=list)

class QAReport(BaseModel):
    is_valid: bool = True
    score: float = 1.0
    revisions_count: int = 0

class JournalEntry(BaseModel):
    id: str = Field(default_factory=lambda: f"entry_{int(time.time())}")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    event: str
    details: str
    impacted_nodes: List[str] = Field(default_factory=list)

# ─── SavepointManager

class SavepointManager:
    """
    Gestionnaire FIFO de checkpoints in-flight (3 derniers).
    Sauvegarde atomique via fichier .tmp + replace (ADR-0352).
    """

    MAX_RETAINED = 3

    @staticmethod
    def get_checkpoints_dir(project_path: Optional[Path] = None) -> Path:
        target_dir = (
            project_path / "memory" / "checkpoints"
            if project_path
            else Path("memory") / "checkpoints"
        )
        target_dir.mkdir(parents=True, exist_ok=True)
        return target_dir

    @classmethod
    def save_checkpoint(
        cls,
        state_dict: Dict[str, Any],
        project_path: Optional[Path] = None,
        reason: str = "in_flight",
    ) -> Path:
        target_dir = cls.get_checkpoints_dir(project_path)
        timestamp = int(time.time())
        filename = f"checkpoint_{timestamp}_{reason}.json"
        target_file = target_dir / filename
        tmp_file = target_dir / f"{filename}.tmp"
        payload = {
            "checkpoint_version": "1.0",
            "timestamp": timestamp,
            "datetime_utc": datetime.now(timezone.utc).isoformat(),
            "reason": reason,
            "state": state_dict,
        }
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        tmp_file.replace(target_file)
        cls.prune_old_checkpoints(target_dir)
        return target_file

    @classmethod
    def prune_old_checkpoints(cls, target_dir: Path) -> None:
        try:
            checkpoints = sorted(
                target_dir.glob("checkpoint_*.json"), key=lambda p: p.stat().st_mtime
            )
            while len(checkpoints) > cls.MAX_RETAINED:
                oldest = checkpoints.pop(0)
                try:
                    oldest.unlink(missing_ok=True)
                except Exception as e:
                    logger.debug(
                        "Suppression d'un checkpoint obsolète échouée (ignorée)",
                        exc_info=True,
                        extra={
                            "component": "state",
                            "operation": "prune_old_checkpoints",
                            "checkpoint": str(oldest),
                            "error": str(e),
                        },
                    )
        except Exception as e:
            logger.debug(f"Erreur de nettoyage des checkpoints: {e}")

    @classmethod
    def list_checkpoints(cls, project_path: Optional[Path] = None) -> List[Path]:
        target_dir = cls.get_checkpoints_dir(project_path)
        return sorted(
            target_dir.glob("checkpoint_*.json"), key=lambda p: p.stat().st_mtime, reverse=True
        )

    @classmethod
    def load_latest_checkpoint(
        cls, project_path: Optional[Path] = None
    ) -> Optional[Dict[str, Any]]:
        checkpoints = cls.list_checkpoints(project_path)
        if not checkpoints:
            return None
        latest = checkpoints[0]
        try:
            with open(latest, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("state")
        except Exception as e:
            logger.warning(f"Impossible de lire le checkpoint {latest}: {e}")
            return None
