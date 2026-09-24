"""
_lc_transitions.py — TransitionsMixin : persistance d'état & contrôle CLI (ADR-0339/ADR-0375).
Méthodes : get_state_file, get_state, save_state, init_lifecycle, can_execute_command.
"""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Tuple

from ._lc_logger import logger
from ._lc_models import (
    COMMAND_MIN_STAGE,
    GATE_DEFINITIONS,
    STAGE_NAMES,
    STAGE_ORDER,
    WORKER_TASK_TYPE_MIN_STAGE,
    ProjectLifecycleStage,
    ProjectLifecycleState,
)


class TransitionsMixin:
    """Mixin : persistance d'état et contrôle d'accès aux commandes CLI."""

    STATE_FILE_NAME = "lifecycle_state.json"

    @classmethod
    def get_state_file(cls, project_path: Path) -> Path:
        return project_path / "memory" / cls.STATE_FILE_NAME

    @classmethod
    def get_state(cls, project_path: Path) -> ProjectLifecycleState:
        """Lit l'état SSOT. Si absent ou corrompu, amorce de façon déterministe."""
        state_file = cls.get_state_file(project_path)
        if state_file.exists():
            try:
                with open(state_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                # Migration ADR-0375 des anciens états ADR-0339
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
        """Sauvegarde atomique avec barrière anti-régression."""
        state_file = cls.get_state_file(project_path)
        if state_file.exists() and not allow_regression:
            try:
                with open(state_file, "r", encoding="utf-8") as f:
                    existing_data = json.load(f)
                raw_existing = ProjectLifecycleStage(existing_data.get("current_stage"))
                existing_canonical = (
                    ProjectLifecycleStage.STAGE_1_INGEST
                    if raw_existing
                    in (ProjectLifecycleStage.STAGE_0_TSHIRT, ProjectLifecycleStage.STAGE_1_INGEST)
                    else ProjectLifecycleStage.STAGE_2_PLAN_ANALYSE
                    if raw_existing
                    in (
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
        """Initialise l'état projet de façon idempotente."""
        state_file = cls.get_state_file(project_path)
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
        """Contrôle pré-vol : vérifie si la commande CLI est autorisée pour la phase actuelle."""
        universal_commands = {
            "resume",
            "vibe-check",
            "guide",
            "doctor",
            "sync",
            "help",
            "fact-search",
            "graph-query",
            "code-explore",
            "lifecycle-status",
            "lifecycle-clean",
            "gate-approve",
            "init",
            "agent-resilience",
            "topology",
            "rollback",
            "dream-rsi",
        }
        cmd_norm = command_name.lower().replace("_", "-")
        if cmd_norm in universal_commands:
            return True, "Commande universelle autorisée."
        if not project_path or not project_path.exists():
            return True, "Aucun projet spécifique ciblé."
        state = cls.get_state(project_path)
        min_required = COMMAND_MIN_STAGE.get(cmd_norm)
        # Gouvernance fine worker-spawn par task-type (ADR-0339 / Option 1)
        if cmd_norm == "worker-spawn":
            if task_type:
                t_norm = task_type.lower().strip()
                min_required = WORKER_TASK_TYPE_MIN_STAGE.get(
                    t_norm, ProjectLifecycleStage.STAGE_3_BUILD
                )
            else:
                min_required = ProjectLifecycleStage.STAGE_3_BUILD

        if min_required is None:
            return True, "Commande non restreinte."
        current_idx = STAGE_ORDER.index(state.canonical_stage)
        req_stage = (
            ProjectLifecycleStage.STAGE_1_INGEST
            if min_required
            in (ProjectLifecycleStage.STAGE_0_TSHIRT, ProjectLifecycleStage.STAGE_1_INGEST)
            else ProjectLifecycleStage.STAGE_2_PLAN_ANALYSE
            if min_required
            in (
                ProjectLifecycleStage.STAGE_1_SOW,
                ProjectLifecycleStage.STAGE_2_PLAN_GRILL,
                ProjectLifecycleStage.STAGE_2_PLAN_ANALYSE,
            )
            else min_required
        )
        required_idx = STAGE_ORDER.index(req_stage)

        if current_idx < required_idx:
            gate_needed = current_idx + 1
            gate_def = GATE_DEFINITIONS.get(gate_needed, {})
            gate_name = gate_def.get("name", f"Gate {gate_needed}")
            detail = ""
            if (
                cmd_norm == "worker-spawn"
                and not task_type
                and current_idx == STAGE_ORDER.index(ProjectLifecycleStage.STAGE_2_PLAN_ANALYSE)
            ):
                detail = " En Phase 2 (STAGE_2_PLAN_ANALYSE), spécifiez un --task-type d'analyse ('deepening', 'deepsearch', 'validation') pour déléguer."

            return (
                False,
                f"La commande '{cmd_norm}' requiert au minimum l'étape '{min_required.value}' ({STAGE_NAMES.get(min_required, min_required.value)}). "
                f"Le projet est actuellement en '{state.current_stage.value}' ({STAGE_NAMES.get(state.current_stage, state.current_stage.value)}).{detail} "
                f"Vous devez d'abord franchir la '{gate_name}' via "
                f"'python src/swarm.py gate-approve --project {project_path.name} --gate {gate_needed} --approver <nom>'.",
            )

        return True, "Étape valide."
