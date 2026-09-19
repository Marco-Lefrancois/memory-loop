"""
Project Lifecycle Management Engine (mLoop)
SSOT Normatif : ADR-0339 / PROJECT_LIFECYCLE_STAGES.md

Gère la machine à états de projet (FSM), la traçabilité déterministe des 6 phases
et le passage bloquant des 6 Portes de Gouvernance (Quality Gates).
"""

from __future__ import annotations

import hashlib
import json
import logging
import shutil
import time
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field

logger = logging.getLogger("lifecycle")


class ProjectLifecycleStage(str, Enum):
    """Les 5 phases séquentielles officielles du cycle de vie mLoop (ADR-0375)."""
    STAGE_1_INGEST = "STAGE_1_INGEST"                 # Phase 1 : INGEST & EXPLORE (Amorçage, Ingestion & Cartographie)
    STAGE_2_PLAN_ANALYSE = "STAGE_2_PLAN_ANALYSE"     # Phase 2 : PLAN & ANALYSE (Macro-Planification T-Shirt/SOW & Micro-Analyse Stories)
    STAGE_3_BUILD = "STAGE_3_BUILD"                   # Phase 3 : BUILD & DEV (Développement physique & Tests unitaires)
    STAGE_4_VALIDATE = "STAGE_4_VALIDATE"             # Phase 4 : VALIDATE & QA (Audit QA, Evals & Non-régression)
    STAGE_5_SHIP = "STAGE_5_SHIP"                     # Phase 5 : SHIP & SYNC (Distribution Jira, Git & Clôture)

    # Rétro-compatibilité legacy ADR-0339 (préservés pour compatibilité sérialisation & tests)
    STAGE_0_TSHIRT = "STAGE_0_TSHIRT"
    STAGE_1_SOW = "STAGE_1_SOW"
    STAGE_2_PLAN_GRILL = "STAGE_2_PLAN_GRILL"


# Ordre strict des 5 phases canoniques (ADR-0375)
STAGE_ORDER: List[ProjectLifecycleStage] = [
    ProjectLifecycleStage.STAGE_1_INGEST,
    ProjectLifecycleStage.STAGE_2_PLAN_ANALYSE,
    ProjectLifecycleStage.STAGE_3_BUILD,
    ProjectLifecycleStage.STAGE_4_VALIDATE,
    ProjectLifecycleStage.STAGE_5_SHIP,
]

STAGE_NAMES: Dict[ProjectLifecycleStage, str] = {
    ProjectLifecycleStage.STAGE_1_INGEST: "Phase 1 : INGEST & EXPLORE (Amorçage & Ingestion)",
    ProjectLifecycleStage.STAGE_2_PLAN_ANALYSE: "Phase 2 : PLAN & ANALYSE (Planification & Spécifications)",
    ProjectLifecycleStage.STAGE_3_BUILD: "Phase 3 : BUILD (Développement Physique)",
    ProjectLifecycleStage.STAGE_4_VALIDATE: "Phase 4 : VALIDATE (Assurance Qualité & Evals)",
    ProjectLifecycleStage.STAGE_5_SHIP: "Phase 5 : SHIP & SYNC (Distribution & Clôture)",
    # Aliases legacy
    ProjectLifecycleStage.STAGE_0_TSHIRT: "Phase 1 : INGEST & EXPLORE (Amorçage & Ingestion)",
    ProjectLifecycleStage.STAGE_1_SOW: "Phase 2 : PLAN & ANALYSE (Planification & Spécifications)",
    ProjectLifecycleStage.STAGE_2_PLAN_GRILL: "Phase 2 : PLAN & ANALYSE (Planification & Spécifications)",
}

GATE_DEFINITIONS: Dict[int, Dict[str, Any]] = {
    0: {
        "name": "Gate 0 : Cadrage Initial (Alias Gate 1)",
        "from_stage": ProjectLifecycleStage.STAGE_1_INGEST,
        "to_stage": ProjectLifecycleStage.STAGE_2_PLAN_ANALYSE,
        "description": "Validation d'amorçage (alias rétro-compatible de Gate 1).",
        "requires_human": False,
    },
    1: {
        "name": "Gate 1 : Ingestion & Cadrage Initial Prêt",
        "from_stage": ProjectLifecycleStage.STAGE_1_INGEST,
        "to_stage": ProjectLifecycleStage.STAGE_2_PLAN_ANALYSE,
        "description": "Validation que les sources brutes sont ingérées et que le projet peut être planifié et analysé.",
        "requires_human": False,
    },
    2: {
        "name": "Gate 2 : Definition of Ready (DoR)",
        "from_stage": ProjectLifecycleStage.STAGE_2_PLAN_ANALYSE,
        "to_stage": ProjectLifecycleStage.STAGE_3_BUILD,
        "description": "Validation DoR sans ambiguïté par WikiFix & Sentinel (4 Piliers Gherkin + EvidencePacks).",
        "requires_human": False,
    },
    3: {
        "name": "Gate 3 : Definition of Done (DoD)",
        "from_stage": ProjectLifecycleStage.STAGE_3_BUILD,
        "to_stage": ProjectLifecycleStage.STAGE_4_VALIDATE,
        "description": "Tests unitaires et d'intégration 100% au vert.",
        "requires_human": False,
    },
    4: {
        "name": "Gate 4 : Conformité Métier & Recette QA",
        "from_stage": ProjectLifecycleStage.STAGE_4_VALIDATE,
        "to_stage": ProjectLifecycleStage.STAGE_5_SHIP,
        "description": "Audit contradictoire Sentinel / QA Lead approuvé.",
        "requires_human": True,
    },
    5: {
        "name": "Gate 5 : Clôture de Cycle & Synchronisation",
        "from_stage": ProjectLifecycleStage.STAGE_5_SHIP,
        "to_stage": None,
        "description": "Synchronisation Jira et Git réussie, archivage mémoire scellé.",
        "requires_human": True,
    },
}

# Matrice des restrictions de commandes par phase minimale requise (ADR-0375)
COMMAND_MIN_STAGE: Dict[str, ProjectLifecycleStage] = {
    # Phase 1 : INGEST & EXPLORE
    "ingest": ProjectLifecycleStage.STAGE_1_INGEST,
    "research": ProjectLifecycleStage.STAGE_1_INGEST,
    "markitdown_convert": ProjectLifecycleStage.STAGE_1_INGEST,
    "crawl": ProjectLifecycleStage.STAGE_1_INGEST,
    "extract": ProjectLifecycleStage.STAGE_1_INGEST,
    "agentic-extract": ProjectLifecycleStage.STAGE_1_INGEST,
    "notebooklm": ProjectLifecycleStage.STAGE_1_INGEST,
    "svg-optimize": ProjectLifecycleStage.STAGE_1_INGEST,
    "svg-ocr": ProjectLifecycleStage.STAGE_1_INGEST,
    "csv-normalize": ProjectLifecycleStage.STAGE_1_INGEST,
    "csv-validate": ProjectLifecycleStage.STAGE_1_INGEST,
    "lifecycle-status": ProjectLifecycleStage.STAGE_1_INGEST,
    "lifecycle-clean": ProjectLifecycleStage.STAGE_1_INGEST,
    "gate-approve": ProjectLifecycleStage.STAGE_1_INGEST,
    
    # Phase 2 : PLAN & ANALYSE (Macro-Planification & Micro-Analyse)
    "to-tshirt": ProjectLifecycleStage.STAGE_2_PLAN_ANALYSE,
    "to-sow": ProjectLifecycleStage.STAGE_2_PLAN_ANALYSE,
    "grill-project": ProjectLifecycleStage.STAGE_2_PLAN_ANALYSE,
    "focus": ProjectLifecycleStage.STAGE_2_PLAN_ANALYSE,
    "grill": ProjectLifecycleStage.STAGE_2_PLAN_ANALYSE,
    "to-spec": ProjectLifecycleStage.STAGE_2_PLAN_ANALYSE,
    "to-tickets": ProjectLifecycleStage.STAGE_2_PLAN_ANALYSE,
    "archify": ProjectLifecycleStage.STAGE_2_PLAN_ANALYSE,
    "chunk": ProjectLifecycleStage.STAGE_2_PLAN_ANALYSE,
    "hyper-query": ProjectLifecycleStage.STAGE_2_PLAN_ANALYSE,
    "wayfinder": ProjectLifecycleStage.STAGE_2_PLAN_ANALYSE,
    "struct-check": ProjectLifecycleStage.STAGE_2_PLAN_ANALYSE,
    "rubber-duck": ProjectLifecycleStage.STAGE_2_PLAN_ANALYSE,
    "multi-draft": ProjectLifecycleStage.STAGE_2_PLAN_ANALYSE,
    "worker-status": ProjectLifecycleStage.STAGE_2_PLAN_ANALYSE,
    "worker-close": ProjectLifecycleStage.STAGE_2_PLAN_ANALYSE,
    "worker-harvest": ProjectLifecycleStage.STAGE_2_PLAN_ANALYSE,
    
    # Phase 3 : BUILD & DEV
    "self-dev": ProjectLifecycleStage.STAGE_3_BUILD,
    "confidence": ProjectLifecycleStage.STAGE_3_BUILD,
    "worker-spawn": ProjectLifecycleStage.STAGE_3_BUILD,
    "code-impact": ProjectLifecycleStage.STAGE_3_BUILD,
    "code-affected": ProjectLifecycleStage.STAGE_3_BUILD,
    
    # Phase 4 : VALIDATE & QA
    "aoep": ProjectLifecycleStage.STAGE_4_VALIDATE,
    "eval": ProjectLifecycleStage.STAGE_4_VALIDATE,
    "audit-loop": ProjectLifecycleStage.STAGE_4_VALIDATE,
    "validate-sprint": ProjectLifecycleStage.STAGE_4_VALIDATE,
    
    # Phase 5 : SHIP & SYNC
    "jira-sync": ProjectLifecycleStage.STAGE_5_SHIP,
    "jira_sync": ProjectLifecycleStage.STAGE_5_SHIP,
    "cycle-status": ProjectLifecycleStage.STAGE_5_SHIP,
}

# Matrice des restrictions par type de tâche pour les workers Herdr (ADR-0375)
WORKER_TASK_TYPE_MIN_STAGE: Dict[str, ProjectLifecycleStage] = {
    "deepening": ProjectLifecycleStage.STAGE_2_PLAN_ANALYSE,
    "deepsearch": ProjectLifecycleStage.STAGE_2_PLAN_ANALYSE,
    "validation": ProjectLifecycleStage.STAGE_2_PLAN_ANALYSE,
    "build": ProjectLifecycleStage.STAGE_3_BUILD,
    "compaction": ProjectLifecycleStage.STAGE_3_BUILD,
}


class GateApprovalRecord(BaseModel):
    """Enregistrement infalsifiable d'approbation d'une Porte de Gouvernance."""
    gate_number: int
    gate_name: str
    approved_at_utc: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    approver: str
    notes: str = ""
    checksum: str = ""


class ProjectLifecycleState(BaseModel):
    """État persistant et canonique du cycle de vie d'un projet client (SSOT)."""
    project_name: str
    current_stage: ProjectLifecycleStage = ProjectLifecycleStage.STAGE_1_INGEST
    gates: Dict[str, GateApprovalRecord] = Field(default_factory=dict)
    created_at_utc: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at_utc: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @property
    def canonical_stage(self) -> ProjectLifecycleStage:
        if self.current_stage in (ProjectLifecycleStage.STAGE_0_TSHIRT, ProjectLifecycleStage.STAGE_1_INGEST):
            return ProjectLifecycleStage.STAGE_1_INGEST
        if self.current_stage in (
            ProjectLifecycleStage.STAGE_1_SOW,
            ProjectLifecycleStage.STAGE_2_PLAN_GRILL,
            ProjectLifecycleStage.STAGE_2_PLAN_ANALYSE,
        ):
            return ProjectLifecycleStage.STAGE_2_PLAN_ANALYSE
        return self.current_stage

    @property
    def stage_index(self) -> int:
        return STAGE_ORDER.index(self.canonical_stage)

    def is_gate_approved(self, gate_number: int) -> bool:
        return str(gate_number) in self.gates


class ProjectLifecycleManager:
    """Gestionnaire de persistance et de contrôle d'accès au cycle de vie projet."""

    STATE_FILE_NAME = "lifecycle_state.json"

    @classmethod
    def get_state_file(cls, project_path: Path) -> Path:
        return project_path / "memory" / cls.STATE_FILE_NAME

    @classmethod
    def get_state(cls, project_path: Path) -> ProjectLifecycleState:
        """Lit l'état persistant SSOT. S'il n'existe pas ou est corrompu, l'amorce de façon déterministe."""
        state_file = cls.get_state_file(project_path)
        if state_file.exists():
            try:
                with open(state_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                # Migration déterministe ADR-0375 des anciens états ADR-0339
                raw_stage = data.get("current_stage")
                if raw_stage == "STAGE_0_TSHIRT":
                    sprint_file = project_path / "backlog" / "sprint_backlog.md"
                    stories_dir = project_path / "backlog" / "stories"
                    arch_dir = project_path / "docs" / "01-architecture"
                    specs_dir = project_path / "docs" / "02-specs"
                    has_work = (
                        sprint_file.exists()
                        or (stories_dir.exists() and any(stories_dir.glob("*.md")))
                        or (arch_dir.exists() and any(arch_dir.glob("*.md")))
                        or (specs_dir.exists() and any(specs_dir.glob("*.md")))
                    )
                    data["current_stage"] = (
                        ProjectLifecycleStage.STAGE_2_PLAN_ANALYSE.value
                        if has_work
                        else ProjectLifecycleStage.STAGE_1_INGEST.value
                    )
                elif raw_stage in ("STAGE_1_SOW", "STAGE_2_PLAN_GRILL"):
                    data["current_stage"] = ProjectLifecycleStage.STAGE_2_PLAN_ANALYSE.value
                return ProjectLifecycleState(**data)
            except Exception as e:
                # Sauvegarde d'urgence du fichier corrompu (ADR-0369)
                timestamp = int(datetime.now(timezone.utc).timestamp())
                corrupt_backup = state_file.with_name(f"{state_file.name}.corrupt.{timestamp}")
                try:
                    shutil.copy2(str(state_file), str(corrupt_backup))
                    state_file.unlink(missing_ok=True)
                    logger.warning(
                        f"Fichier d'état corrompu archivé vers {corrupt_backup} : {e}",
                        exc_info=True,
                        extra={"project": project_path.name, "corrupt_backup": str(corrupt_backup)},
                    )
                except Exception as backup_err:
                    logger.debug(
                        f"Impossible d'archiver le fichier corrompu : {backup_err}",
                        exc_info=True,
                        extra={"project": project_path.name},
                    )
                logger.warning(
                    f"Erreur lecture {state_file}, ré-amorçage : {e}",
                    extra={"project": project_path.name},
                )

        # Amorçage initial déterministe
        return cls.init_lifecycle(project_path)

    @classmethod
    def save_state(
        cls, project_path: Path, state: ProjectLifecycleState, allow_regression: bool = False
    ) -> None:
        """Sauvegarde atomique de l'état persistant avec barrière anti-régression."""
        state_file = cls.get_state_file(project_path)

        # Barrière anti-régression : vérifier si un état plus avancé existe déjà
        if state_file.exists() and not allow_regression:
            try:
                with open(state_file, "r", encoding="utf-8") as f:
                    existing_data = json.load(f)
                raw_existing = ProjectLifecycleStage(existing_data.get("current_stage"))
                existing_canonical = (
                    ProjectLifecycleStage.STAGE_1_INGEST
                    if raw_existing in (ProjectLifecycleStage.STAGE_0_TSHIRT, ProjectLifecycleStage.STAGE_1_INGEST)
                    else ProjectLifecycleStage.STAGE_2_PLAN_ANALYSE
                    if raw_existing in (
                        ProjectLifecycleStage.STAGE_1_SOW,
                        ProjectLifecycleStage.STAGE_2_PLAN_GRILL,
                        ProjectLifecycleStage.STAGE_2_PLAN_ANALYSE,
                    )
                    else raw_existing
                )
                existing_gates = set(existing_data.get("gates", {}).keys())

                existing_idx = STAGE_ORDER.index(existing_canonical)
                new_idx = STAGE_ORDER.index(state.canonical_stage)

                new_gates = set(state.gates.keys())
                lost_gates = existing_gates - new_gates

                if new_idx < existing_idx or lost_gates:
                    msg = (
                        f"Régression de cycle de vie interdite pour '{project_path.name}' : "
                        f"passage de {raw_existing.value} (index {existing_idx}) à {state.current_stage.value} (index {new_idx}) "
                        f"ou perte de portes {sorted(list(lost_gates))}."
                    )
                    logger.warning(
                        msg,
                        extra={
                            "project": project_path.name,
                            "existing_stage": raw_existing.value,
                            "new_stage": state.current_stage.value,
                            "lost_gates": list(lost_gates),
                        },
                    )
                    raise ValueError(msg)
            except json.JSONDecodeError as json_err:
                logger.debug(
                    f"Vérification anti-régression ignorée suite à JSON corrompu : {json_err}",
                    exc_info=True,
                    extra={"project": project_path.name},
                )
            except ValueError:
                raise
            except Exception as read_err:
                logger.debug(
                    f"Vérification anti-régression ignorée suite à erreur de lecture : {read_err}",
                    exc_info=True,
                    extra={"project": project_path.name},
                )

        state.updated_at_utc = datetime.now(timezone.utc).isoformat()
        state_file.parent.mkdir(parents=True, exist_ok=True)
        tmp_file = state_file.with_suffix(".tmp")
        with open(tmp_file, "w", encoding="utf-8") as f:
            f.write(state.model_dump_json(indent=2))
        tmp_file.replace(state_file)

    @classmethod
    def init_lifecycle(
        cls,
        project_path: Path,
        initial_stage: Optional[ProjectLifecycleStage] = None,
        force: bool = False,
    ) -> ProjectLifecycleState:
        """Initialise un nouvel état projet conforme de façon idempotente."""
        state_file = cls.get_state_file(project_path)

        # Garde d'idempotence : si l'état existe et est sain, le préserver sauf force=True
        if state_file.exists() and not force:
            try:
                with open(state_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                existing_state = ProjectLifecycleState(**data)
                logger.info(
                    f"État de cycle de vie existant préservé pour '{project_path.name}' "
                    f"({existing_state.current_stage.value}, {len(existing_state.gates)} porte(s))."
                )
                return existing_state
            except Exception as load_err:
                logger.debug(
                    f"État existant non réutilisable lors de init_lifecycle : {load_err}",
                    exc_info=True,
                    extra={"project": project_path.name},
                )

        proj_name = project_path.name

        # Détermination de l'étape initiale selon la présence de livrables existants (Fast-Track)
        if initial_stage is None:
            sow_files = (
                list((project_path / "docs" / "01-architecture").glob("SOW_*.md"))
                if (project_path / "docs" / "01-architecture").exists()
                else []
            )
            specs_files = (
                list((project_path / "docs" / "02-specs").glob("*.md"))
                if (project_path / "docs" / "02-specs").exists()
                else []
            )
            sprint_file = project_path / "backlog" / "sprint_backlog.md"
            if sow_files or specs_files or sprint_file.exists():
                initial_stage = ProjectLifecycleStage.STAGE_2_PLAN_ANALYSE
            else:
                initial_stage = ProjectLifecycleStage.STAGE_1_INGEST

        state = ProjectLifecycleState(
            project_name=proj_name,
            current_stage=initial_stage,
            gates={},
        )
        cls.save_state(project_path, state, allow_regression=force)
        logger.info(f"Cycle de vie amorcé pour '{proj_name}' en étape {initial_stage.value}")
        return state

    @classmethod
    def can_execute_command(
        cls, project_path: Path, command_name: str, task_type: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Contrôle déterministe pré-vol : vérifie si la commande CLI est autorisée
        pour l'étape actuelle du projet.
        
        Args:
            project_path: Chemin vers la racine du projet
            command_name: Nom de la commande CLI
            task_type: Type de mission pour les workers (deepening, deepsearch, validation, build, compaction)
            
        Returns:
            Tuple (allowed: bool, reason: str)
        """
        # Commandes universellement autorisées quel que soit le projet ou la phase
        universal_commands = {
            "resume", "vibe-check", "guide", "doctor", "sync", "help",
            "fact-search", "graph-query", "code-explore", "lifecycle-status",
            "lifecycle-clean", "gate-approve", "init",
            "agent-resilience", "topology", "rollback",
            "dream-rsi",
        }
        cmd_norm = command_name.lower().replace("_", "-")
        if cmd_norm in universal_commands:
            return True, "Commande universelle autorisée."

        if not project_path or not project_path.exists():
            return True, "Aucun projet spécifique ciblé."

        state = cls.get_state(project_path)
        min_required = COMMAND_MIN_STAGE.get(cmd_norm)

        # Gouvernance fine pour worker-spawn par task-type (ADR-0339 / Option 1)
        if cmd_norm == "worker-spawn":
            if task_type:
                t_norm = task_type.lower().strip()
                min_required = WORKER_TASK_TYPE_MIN_STAGE.get(t_norm, ProjectLifecycleStage.STAGE_3_BUILD)
            else:
                min_required = ProjectLifecycleStage.STAGE_3_BUILD

        if min_required is None:
            # Commande non répertoriée dans la matrice stricte : autoriser par défaut
            return True, "Commande non restreinte."

        current_idx = STAGE_ORDER.index(state.canonical_stage)
        req_stage = (
            ProjectLifecycleStage.STAGE_1_INGEST
            if min_required in (ProjectLifecycleStage.STAGE_0_TSHIRT, ProjectLifecycleStage.STAGE_1_INGEST)
            else ProjectLifecycleStage.STAGE_2_PLAN_ANALYSE
            if min_required in (
                ProjectLifecycleStage.STAGE_1_SOW,
                ProjectLifecycleStage.STAGE_2_PLAN_GRILL,
                ProjectLifecycleStage.STAGE_2_PLAN_ANALYSE,
            )
            else min_required
        )
        required_idx = STAGE_ORDER.index(req_stage)

        if current_idx < required_idx:
            # Violation de porte
            gate_needed = current_idx + 1  # La porte à franchir pour avancer (Gate 1 pour sortir de Phase 1)
            gate_def = GATE_DEFINITIONS.get(gate_needed, {})
            gate_name = gate_def.get("name", f"Gate {gate_needed}")
            detail = ""
            if cmd_norm == "worker-spawn" and not task_type and current_idx == STAGE_ORDER.index(ProjectLifecycleStage.STAGE_2_PLAN_ANALYSE):
                detail = " En Phase 2 (STAGE_2_PLAN_ANALYSE), spécifiez un --task-type d'analyse ('deepening', 'deepsearch', 'validation') pour déléguer."

            return (
                False,
                f"La commande '{cmd_norm}' requiert au minimum l'étape '{min_required.value}' ({STAGE_NAMES.get(min_required, min_required.value)}). "
                f"Le projet est actuellement en '{state.current_stage.value}' ({STAGE_NAMES.get(state.current_stage, state.current_stage.value)}).{detail} "
                f"Vous devez d'abord franchir la '{gate_name}' via "
                f"'python src/swarm.py gate-approve --project {project_path.name} --gate {gate_needed} --approver <nom>'."
            )

        return True, "Étape valide."

    @classmethod
    def approve_gate(
        cls,
        project_path: Path,
        gate_number: int,
        approver: str,
        notes: str = "",
    ) -> ProjectLifecycleState:
        """
        Valide formellement une Porte de Gouvernance et fait progresser le projet vers la phase suivante.
        """
        if gate_number not in GATE_DEFINITIONS:
            raise ValueError(f"Porte inconnue : Gate {gate_number}. Portes valides : 1 à 5.")

        state = cls.get_state(project_path)
        gate_def = GATE_DEFINITIONS[gate_number]

        # Vérification d'alignement de phase (avec support canonique)
        expected_stage = gate_def["from_stage"]
        current_canonical = state.canonical_stage
        expected_canonical = (
            ProjectLifecycleStage.STAGE_1_INGEST
            if expected_stage in (ProjectLifecycleStage.STAGE_0_TSHIRT, ProjectLifecycleStage.STAGE_1_INGEST)
            else ProjectLifecycleStage.STAGE_2_PLAN_ANALYSE
            if expected_stage in (
                ProjectLifecycleStage.STAGE_1_SOW,
                ProjectLifecycleStage.STAGE_2_PLAN_GRILL,
                ProjectLifecycleStage.STAGE_2_PLAN_ANALYSE,
            )
            else expected_stage
        )
        if current_canonical != expected_canonical:
            raise ValueError(
                f"Impossible de valider la Gate {gate_number} : le projet est en étape '{state.current_stage.value}', "
                f"alors que cette porte requiert d'être en étape '{expected_stage.value}'."
            )

        # Validations bloquantes spécifiques Gate 1 (ADR-0378 / Check 13 / Anti-Ghost-Bias)
        if gate_number in (0, 1):
            stories_dir = project_path / "backlog" / "stories"
            if stories_dir.exists():
                premature = [sf.name for sf in stories_dir.glob("*.md") if sf.name.lower() != "readme.md"]
                if premature:
                    raise ValueError(
                        f"Approbation de Gate {gate_number} refusée (Check 13 / Anti-Ghost-Bias) : "
                        f"des récits physiques ({len(premature)}) existent déjà sous backlog/stories/ : {premature[:3]}. "
                        f"En Phase 1 (INGEST & EXPLORE), la création de stories est formellement interdite. "
                        f"Lancez 'python src/swarm.py lifecycle-clean --confirm' pour assainir le backlog avant de valider la Gate 1."
                    )
            ref_dir = project_path / "reference"
            raw_files = [f for f in ref_dir.rglob("*") if f.is_file()] if ref_dir.exists() else []
            ingested_dir = project_path / "docs" / "00-ingested"
            ingested_files = list(ingested_dir.glob("*.md")) if ingested_dir.exists() else []
            manifest_file = ingested_dir / "source_manifest.json" if ingested_dir.exists() else None
            has_ingested = bool(ingested_files or (manifest_file and manifest_file.exists()))
            if raw_files and not has_ingested:
                raise ValueError(
                    f"Approbation de Gate {gate_number} refusée : des fichiers bruts sont présents dans reference/ "
                    f"mais aucun document normalisé n'a été trouvé sous docs/00-ingested/ pour '{project_path.name}'. "
                    f"Lancez 'python src/swarm.py ingest --project {project_path.name}' avant d'approuver la Gate 1."
                )
        # Validations bloquantes spécifiques Gate 4 (ADR-0383 / MLOOP-092-BE : Recette QA Opposable)
        if gate_number == 4:
            from src.core.gate4_validator import validate_gate4_approval
            validate_gate4_approval(project_path, approver)

        # Calcul d'empreinte de sécurité sur les livrables de la phase
        checksum = cls._compute_stage_deliverables_hash(project_path, state.current_stage)

        record = GateApprovalRecord(
            gate_number=gate_number,
            gate_name=gate_def["name"],
            approver=approver,
            notes=notes,
            checksum=checksum,
        )

        state.gates[str(gate_number)] = record

        # Transition d'étape
        next_stage = gate_def["to_stage"]
        if next_stage:
            state.current_stage = next_stage

        cls.save_state(project_path, state)
        logger.info(
            f"[LIFECYCLE] Gate {gate_number} approuvée par '{approver}'. "
            f"Projet '{project_path.name}' transite vers '{state.current_stage.value}'."
        )
        return state

    @classmethod
    def clean_premature_stories(
        cls, project_path: Path, confirm: bool = False
    ) -> Dict[str, Any]:
        """
        Déplace et archive de manière réversible les stories créées prématurément
        et leurs EvidencePacks dans memory/archive/premature_stories/<timestamp>/
        pour éliminer le 'Ghost Bias' et restaurer la neutralité cognitive du LLM sans perte de données (ADR-0339 / L-08).
        """
        if not confirm:
            logger.warning(
                f"[LIFECYCLE-CLEAN] Nettoyage refusé pour '{project_path.name}' : confirmation explicite requise (confirm=False).",
                extra={"project": project_path.name},
            )
            return {
                "status": "refused",
                "deleted_stories": [],
                "deleted_evidence": [],
                "archived_stories": [],
                "archived_evidence": [],
                "archive_dir": None,
                "message": "Nettoyage refusé : confirmation explicite requise (passez --confirm).",
            }

        state = cls.get_state(project_path)
        if state.canonical_stage != ProjectLifecycleStage.STAGE_1_INGEST:
            return {
                "status": "noop",
                "deleted_stories": [],
                "deleted_evidence": [],
                "archived_stories": [],
                "archived_evidence": [],
                "archive_dir": None,
                "message": "Le projet est en Phase 2 ou supérieure. Aucune suppression de story requise.",
            }

        deleted_stories = []
        deleted_evidence = []

        # Dossier d'archivage horodaté sécurisé (ZÉRO unlink destructif - L-08)
        timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        archive_dir = project_path / "memory" / "archive" / "premature_stories" / timestamp_str

        # 1. Déplacement des stories sous backlog/stories/ vers l'archive
        stories_dir = project_path / "backlog" / "stories"
        if stories_dir.exists():
            for sf in list(stories_dir.glob("*.md")):
                if sf.name.lower() != "readme.md":
                    archive_dir.mkdir(parents=True, exist_ok=True)
                    sf_name = sf.name
                    target_dest = archive_dir / sf_name
                    shutil.move(str(sf), str(target_dest))
                    deleted_stories.append(sf_name)
                    logger.warning(
                        f"[LIFECYCLE-CLEAN] Story prématurée archivée : {sf_name} -> {target_dest}",
                        extra={"project": project_path.name, "file": sf_name, "archive": str(target_dest)},
                    )

        # 2. Déplacement des EvidencePacks et fact_dossiers sous memory/evidence/ vers l'archive
        evidence_dir = project_path / "memory" / "evidence"
        if evidence_dir.exists():
            for ef in list(evidence_dir.glob("*_evidence.json")) + list(evidence_dir.glob("*_fact_dossier.md")):
                archive_dir.mkdir(parents=True, exist_ok=True)
                ef_name = ef.name
                target_dest = archive_dir / ef_name
                shutil.move(str(ef), str(target_dest))
                deleted_evidence.append(ef_name)
                logger.warning(
                    f"[LIFECYCLE-CLEAN] Preuve prématurée archivée : {ef_name} -> {target_dest}",
                    extra={"project": project_path.name, "file": ef_name, "archive": str(target_dest)},
                )

        # 3. Réalignement macroscopique de sprint_backlog.md
        backlog_file = project_path / "backlog" / "sprint_backlog.md"
        if backlog_file.exists():
            try:
                with open(backlog_file, "r", encoding="utf-8") as f:
                    content = f.read()
                # Remplacement des statuts engagés par OPEN
                for kw in ["IN_ANALYZE", "READY_FOR_GROOMING", "READY_FOR_DEV", "IN_DEV"]:
                    content = content.replace(kw, "OPEN")
                with open(backlog_file, "w", encoding="utf-8") as f:
                    f.write(content)
            except Exception as e:
                logger.debug(f"Erreur mise à jour sprint_backlog.md : {e}", exc_info=True)

        res_dict = {
            "status": "completed",
            "deleted_stories": deleted_stories,
            "deleted_evidence": deleted_evidence,
            "archived_stories": deleted_stories,
            "archived_evidence": deleted_evidence,
            "archive_dir": str(archive_dir) if (deleted_stories or deleted_evidence) else None,
            "message": (
                f"Nettoyage sécurisé effectué : {len(deleted_stories)} story(ies) et {len(deleted_evidence)} "
                f"preuve(s) archivée(s) vers {archive_dir}."
                if (deleted_stories or deleted_evidence)
                else "Aucune story prématurée à nettoyer."
            ),
        }
        return res_dict

    @classmethod
    def _compute_stage_deliverables_hash(
        cls, project_path: Path, stage: ProjectLifecycleStage
    ) -> str:
        """Calcule un SHA-256 déterministe sur les livrables clés de la phase courante."""
        h = hashlib.sha256()
        files_to_hash = []

        canonical = (
            ProjectLifecycleStage.STAGE_1_INGEST
            if stage in (ProjectLifecycleStage.STAGE_0_TSHIRT, ProjectLifecycleStage.STAGE_1_INGEST)
            else ProjectLifecycleStage.STAGE_2_PLAN_ANALYSE
            if stage in (
                ProjectLifecycleStage.STAGE_1_SOW,
                ProjectLifecycleStage.STAGE_2_PLAN_GRILL,
                ProjectLifecycleStage.STAGE_2_PLAN_ANALYSE,
            )
            else stage
        )

        if canonical == ProjectLifecycleStage.STAGE_1_INGEST:
            ingested_dir = project_path / "docs" / "00-ingested"
            if ingested_dir.exists():
                manifest_file = ingested_dir / "source_manifest.json"
                if manifest_file.exists():
                    files_to_hash.append(manifest_file)
                files_to_hash.extend(sorted(ingested_dir.glob("*.md")))
            assets_dir = project_path / "docs" / "05-assets"
            if assets_dir.exists():
                files_to_hash.extend(sorted(f for f in assets_dir.rglob("*.svg") if f.is_file()))
            lexicon_file = project_path / "docs" / "04-transverse" / "lexique_domaine.md"
            if lexicon_file.exists():
                files_to_hash.append(lexicon_file)

        elif canonical == ProjectLifecycleStage.STAGE_2_PLAN_ANALYSE:
            arch_dir = project_path / "docs" / "01-architecture"
            if arch_dir.exists():
                files_to_hash.extend(sorted(arch_dir.glob("TSHIRT_SIZE_*.md")))
                files_to_hash.extend(sorted(arch_dir.glob("SOW_*.md")))
            backlog_file = project_path / "backlog" / "sprint_backlog.md"
            if backlog_file.exists():
                files_to_hash.append(backlog_file)
            stories_dir = project_path / "backlog" / "stories"
            if stories_dir.exists():
                files_to_hash.extend(sorted(stories_dir.glob("*.md")))

        for f in files_to_hash:
            h.update(f.read_bytes())

        return h.hexdigest()[:16] if files_to_hash else "empty_phase_deliverable"
