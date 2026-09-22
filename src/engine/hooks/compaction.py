# -*- coding: utf-8 -*-
"""
mLoop Pre-Compaction & Checkpoint Boundary Engine (ADR-0364).

Garantit la persistance déterministe Système 1 avant toute compression de mémoire vive,
la résolution dynamique de l'Artefact #1 (0 Blindspot) et le Triple Filet de Récupération.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field

from src.engine.hooks.path_resolver import PathAliasResolver
from src.utils.logger import get_logger

logger = get_logger("engine.hooks.compaction")


class ToolOutcome(BaseModel):
    """Résultat factuel binaire d'exécution d'un outil ou test."""

    tool_name: str
    status: Literal["PASS", "FAIL", "PENDING"] = "PASS"
    proof_hash: Optional[str] = None
    details: Optional[str] = None


class FileReservation(BaseModel):
    """Fichier physique sous contrat d'édition (Dirty Git State)."""

    path: str
    status: Literal["M", "A", "D", "R"] = "M"
    sha256: Optional[str] = None


class CompactionCheckpoint(BaseModel):
    """Instantané d'invariants opérationnels mLoop avant compaction."""

    project_name: str
    focused_story_id: Optional[str] = None
    stage: str = "SPEC"
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    story_context: Optional[str] = None
    active_acceptance_criteria: List[str] = Field(default_factory=list)
    file_reservations: List[FileReservation] = Field(default_factory=list)
    tool_outcomes: List[ToolOutcome] = Field(default_factory=list)
    primary_artifact_uri: Optional[str] = None
    visual_contract_uri: Optional[str] = None
    resume_instructions: str = ""
    checkpoint_hash: Optional[str] = None


class PreCompactionHandler:
    """Gestionnaire déterministe d'interception de pré-compaction."""

    @classmethod
    def create_checkpoint(
        cls,
        project_name: Optional[str] = None,
        focused_story_id: Optional[str] = None,
        stage: Optional[str] = None,
        base_dir: Optional[Path] = None,
    ) -> CompactionCheckpoint:
        """Génère et persiste atomiquement le checkpoint d'état avant compaction."""
        proj_root = PathAliasResolver.get_project_root(project_name, base_dir)
        proj_name = project_name or (proj_root.name if proj_root != Path(".") else "Memory Loop")

        # 1. Résolution de la story active et du stage si non fournis
        active_story, detected_stage = cls._resolve_active_story_and_stage(
            proj_root, focused_story_id, stage
        )
        current_stage = stage or detected_stage or "SPEC"

        # 2. Capture de l'état Git Dirty (File Reservations)
        file_res = cls._capture_dirty_files(proj_root, proj_name)

        # 3. Capture des statuts d'outils et de tests
        outcomes = cls._capture_tool_outcomes(proj_root, active_story)

        # 4. Résolution de l'Artefact #1 selon la phase (0 Blindspot)
        primary_uri = cls._resolve_primary_artifact(
            proj_root, proj_name, current_stage, active_story
        )

        # 5. Résolution du Contrat Visuel (si frontend/fullstack)
        visual_uri = cls._resolve_visual_contract(proj_root, proj_name, active_story)

        # 6. Extraction du contexte et des critères Gherkin de la story si existante
        story_ctx, gherkin_criteria = cls._extract_story_invariants(proj_root, active_story)

        # 7. Génération de la micro-boussole resume_instructions (≤ 400 tokens)
        resume_md = cls._generate_resume_instructions(
            proj_name=proj_name,
            active_story=active_story,
            stage=current_stage,
            file_res=file_res,
            outcomes=outcomes,
            primary_uri=primary_uri,
            visual_uri=visual_uri,
            story_ctx=story_ctx,
            gherkin_criteria=gherkin_criteria,
        )

        checkpoint = CompactionCheckpoint(
            project_name=proj_name,
            focused_story_id=active_story,
            stage=current_stage,
            story_context=story_ctx,
            active_acceptance_criteria=gherkin_criteria,
            file_reservations=file_res,
            tool_outcomes=outcomes,
            primary_artifact_uri=primary_uri,
            visual_contract_uri=visual_uri,
            resume_instructions=resume_md,
        )

        # 8. Calcul de l'empreinte d'intégrité SHA-256
        raw_json = checkpoint.model_dump_json(indent=2)
        checkpoint.checkpoint_hash = hashlib.sha256(raw_json.encode("utf-8")).hexdigest()

        # 9. Écriture atomique sur disque
        cls._atomic_write_checkpoint(proj_root, checkpoint)

        # 10. Mise à jour de SESSION_MEMORY_HEALTH.md
        cls._update_session_health(proj_root, checkpoint)

        return checkpoint

    @classmethod
    def _resolve_active_story_and_stage(
        cls, proj_root: Path, focused_story_id: Optional[str], stage: Optional[str]
    ) -> tuple[Optional[str], str]:
        """Déduit la story active et l'étape mLoop en cours."""
        if focused_story_id:
            return focused_story_id, stage or "BUILD"

        # Recherche dans backlog/stories/
        backlog_dir = proj_root / "backlog" / "stories"
        if backlog_dir.exists():
            stories = sorted(
                backlog_dir.glob("*.md"), key=lambda f: f.stat().st_mtime, reverse=True
            )
            if stories:
                return stories[0].stem, "BUILD"

        # Recherche dans memory/SESSION_MEMORY_HEALTH.md
        health_file = proj_root / "memory" / "SESSION_MEMORY_HEALTH.md"
        if health_file.exists():
            try:
                content = health_file.read_text(encoding="utf-8")
                for line in content.splitlines():
                    if "Story active" in line or "focused_story" in line:
                        parts = line.split(":", 1)
                        if len(parts) > 1:
                            return parts[1].strip(" `*[]"), "BUILD"
            except Exception as e:
                logger.debug(
                    "Lecture SESSION_MEMORY_HEALTH.md échouée lors de la résolution story active",
                    exc_info=True,
                    extra={
                        "component": "engine.hooks.compaction",
                        "operation": "_resolve_active_story_and_stage",
                        "health_file": str(health_file),
                        "error": str(e),
                    },
                )

        return None, "SPEC"

    @classmethod
    def _capture_dirty_files(cls, proj_root: Path, project_name: str) -> List[FileReservation]:
        """Capture les fichiers modifiés via git status -s."""
        reservations: List[FileReservation] = []
        try:
            res = subprocess.run(
                ["git", "status", "-s"],
                cwd=str(proj_root.resolve()),
                capture_output=True,
                text=True,
                timeout=3,
            )
            if res.returncode == 0:
                for line in res.stdout.splitlines():
                    line_str = line.strip()
                    if len(line_str) >= 3:
                        status_code = line_str[:2].strip()
                        file_path_str = line_str[2:].strip()
                        norm_status: Literal["M", "A", "D", "R"] = "M"
                        if "A" in status_code:
                            norm_status = "A"
                        elif "D" in status_code:
                            norm_status = "D"

                        phys_path = proj_root / file_path_str
                        sha_val = None
                        if phys_path.is_file():
                            try:
                                sha_val = hashlib.sha256(phys_path.read_bytes()).hexdigest()[:12]
                            except Exception as e:
                                logger.debug(
                                    "Calcul SHA-256 fichier dirty ignoré",
                                    exc_info=True,
                                    extra={
                                        "component": "engine.hooks.compaction",
                                        "operation": "_capture_dirty_files",
                                        "path": str(phys_path),
                                        "error": str(e),
                                    },
                                )

                        reservations.append(
                            FileReservation(
                                path=file_path_str,
                                status=norm_status,
                                sha256=sha_val,
                            )
                        )
        except Exception as e:
            logger.warning(
                "Capture de l'état Git dirty échouée (checkpoint partiel)",
                exc_info=True,
                extra={
                    "component": "engine.hooks.compaction",
                    "operation": "_capture_dirty_files",
                    "project": project_name,
                    "error": str(e),
                },
            )

        return reservations[:8]  # Plafond à 8 fichiers max pour token budget

    @classmethod
    def _capture_tool_outcomes(
        cls, proj_root: Path, active_story: Optional[str]
    ) -> List[ToolOutcome]:
        """Extrait les derniers statuts d'outils et tests."""
        outcomes: List[ToolOutcome] = []
        if not active_story:
            return outcomes

        ev_file = proj_root / "memory" / "evidence" / f"{active_story}_evidence.json"
        if ev_file.exists():
            try:
                ev_data = json.loads(ev_file.read_text(encoding="utf-8"))
                gates = ev_data.get("runnable_gates_proofs", {})
                for gate_name, gate_info in gates.items():
                    status_str = "PASS" if gate_info.get("exit_code") == 0 else "FAIL"
                    outcomes.append(
                        ToolOutcome(
                            tool_name=gate_name,
                            status=status_str,
                            proof_hash=gate_info.get("proof_hash", "")[:12],
                            details=gate_info.get("summary"),
                        )
                    )
            except Exception as e:
                logger.debug(
                    "Extraction des statuts d'outils depuis l'EvidencePack échouée",
                    exc_info=True,
                    extra={
                        "component": "engine.hooks.compaction",
                        "operation": "_capture_tool_outcomes",
                        "story": active_story,
                        "ev_file": str(ev_file),
                        "error": str(e),
                    },
                )

        return outcomes

    @classmethod
    def _resolve_primary_artifact(
        cls, proj_root: Path, project_name: str, stage: str, active_story: Optional[str]
    ) -> Optional[str]:
        """Détermine dynamiquement l'Artefact #1 selon la phase (0 Blindspot)."""
        if stage in ("SPEC", "INIT") or not active_story:
            ingested_dir = proj_root / "docs" / "00-ingested"
            if ingested_dir.exists():
                docs = sorted(
                    ingested_dir.glob("*.md"), key=lambda f: f.stat().st_mtime, reverse=True
                )
                if docs:
                    return PathAliasResolver.to_micro_uri(docs[0], project_name)
            return "source://WIKI_INDEX.md"

        # En phase BUILD / TDD : Le Dossier de Preuves Documentaires
        fact_dossier = proj_root / "memory" / "evidence" / f"{active_story}_fact_dossier.md"
        if fact_dossier.exists():
            return PathAliasResolver.to_micro_uri(fact_dossier, project_name)

        # Fallback sur la story physique
        story_path = proj_root / "backlog" / "stories" / f"{active_story}.md"
        if story_path.exists():
            return PathAliasResolver.to_micro_uri(story_path, project_name)

        return None

    @classmethod
    def _resolve_visual_contract(
        cls, proj_root: Path, project_name: str, active_story: Optional[str]
    ) -> Optional[str]:
        """Identifie la maquette SSOT liée si applicable."""
        maquettes_dir = proj_root / "docs" / "05-assets" / "maquettes"
        if not maquettes_dir.exists():
            return None

        # Si maquette correspondant au nom de la story
        if active_story:
            cand = maquettes_dir / f"{active_story}.svg"
            if cand.exists():
                return PathAliasResolver.to_micro_uri(cand, project_name)

        # Fallback sur la maquette la plus récente
        maquettes = sorted(
            maquettes_dir.glob("*.svg"), key=lambda f: f.stat().st_mtime, reverse=True
        )
        if maquettes:
            return PathAliasResolver.to_micro_uri(maquettes[0], project_name)

        return None

    @classmethod
    def _extract_story_invariants(
        cls, proj_root: Path, active_story: Optional[str]
    ) -> tuple[Optional[str], List[str]]:
        """Extrait le contexte métier (2 lignes) et les 4 Piliers Gherkin."""
        if not active_story:
            return None, []

        story_file = proj_root / "backlog" / "stories" / f"{active_story}.md"
        if not story_file.exists():
            return None, []

        context_lines: List[str] = []
        gherkin_lines: List[str] = []
        try:
            content = story_file.read_text(encoding="utf-8")
            in_scenarios = False
            for line in content.splitlines():
                clean = line.strip()
                if (
                    clean.startswith("En tant que")
                    or clean.startswith("Je veux")
                    or clean.startswith("Afin de")
                ):
                    context_lines.append(clean)
                elif "## Scénarios de test" in clean or "## Critères d'acceptation" in clean:
                    in_scenarios = True
                elif in_scenarios and clean.startswith("### "):
                    in_scenarios = False
                elif in_scenarios and (
                    clean.startswith("1. **")
                    or clean.startswith("2. **")
                    or clean.startswith("3. **")
                    or clean.startswith("4. **")
                ):
                    gherkin_lines.append(clean[:70])
        except Exception as e:
            logger.debug(
                "Extraction des invariants Gherkin de la story échouée",
                exc_info=True,
                extra={
                    "component": "engine.hooks.compaction",
                    "operation": "_extract_story_invariants",
                    "story": active_story,
                    "story_file": str(story_file),
                    "error": str(e),
                },
            )

        ctx_summary = " ".join(context_lines)[:180] if context_lines else None
        return ctx_summary, gherkin_lines[:4]

    @classmethod
    def _generate_resume_instructions(
        cls,
        proj_name: str,
        active_story: Optional[str],
        stage: str,
        file_res: List[FileReservation],
        outcomes: List[ToolOutcome],
        primary_uri: Optional[str],
        visual_uri: Optional[str],
        story_ctx: Optional[str],
        gherkin_criteria: List[str],
    ) -> str:
        """Génère la micro-boussole LOD-0 strictly bornée (≤ 400 tokens)."""
        lines = [
            f"## 🛡️ mLoop Checkpoint Invariant [@root: Projects/{proj_name}]",
            f"- **Étape** : `{stage}`"
            + (f" | Story : `story://{active_story}`" if active_story else ""),
        ]

        if primary_uri:
            lines.append(
                f"- **Vérité SSOT #1** : `{primary_uri}` (Consultation obligatoire via view_file en cas de doute)"
            )
        if visual_uri:
            lines.append(f"- **Contrat Visuel UI** : `{visual_uri}` (Maquette SSOT absolue)")

        if story_ctx:
            lines.append(f"- **Intention Métier** : {story_ctx}")

        if gherkin_criteria:
            lines.append("- **Contrat Gherkin Actif** :")
            for crit in gherkin_criteria:
                lines.append(f"  • {crit}")

        if file_res:
            res_str = ", ".join(f"`[{r.status}] {r.path}`" for r in file_res[:4])
            if len(file_res) > 4:
                res_str += f" (+{len(file_res) - 4} autres)"
            lines.append(f"- **Fichiers sous Contrat** : {res_str}")

        if outcomes:
            badges = " | ".join(
                f"{o.tool_name}: {'✅ PASS' if o.status == 'PASS' else '❌ FAIL'}" for o in outcomes
            )
            lines.append(f"- **Statuts Tests** : [{badges}]")

        lines.extend(
            [
                "- **Consignes de Reprise Non Négociables** :",
                "  1. INTERDICTION formelle d'explorer le disque (`ls -R`, `find`).",
                "  2. Poursuivre directement l'action en cours sans régression.",
            ]
        )

        return "\n".join(lines)

    @classmethod
    def _atomic_write_checkpoint(cls, proj_root: Path, checkpoint: CompactionCheckpoint) -> None:
        """Écriture atomique sécurisée sous Windows/POSIX via fichier temporaire .tmp."""
        comp_dir = proj_root / "memory" / "compaction"
        hist_dir = comp_dir / "history"
        hist_dir.mkdir(parents=True, exist_ok=True)

        payload_bytes = checkpoint.model_dump_json(indent=2).encode("utf-8")

        # 1. Écriture du checkpoint latest
        target_latest = comp_dir / "latest_checkpoint.json"
        tmp_file = comp_dir / f"checkpoint_{os.getpid()}.tmp"
        try:
            tmp_file.write_bytes(payload_bytes)
            tmp_file.replace(target_latest)
        except Exception as e:
            # Fallback direct si replace échoue
            logger.warning(
                "Écriture atomique du checkpoint échouée, bascule sur écriture directe",
                exc_info=True,
                extra={
                    "component": "engine.hooks.compaction",
                    "operation": "_atomic_write_checkpoint",
                    "target": str(target_latest),
                    "error": str(e),
                },
            )
            target_latest.write_bytes(payload_bytes)
            if tmp_file.exists():
                try:
                    tmp_file.unlink()
                except Exception as e_unlink:
                    logger.debug(
                        "Nettoyage du fichier temporaire de checkpoint échoué",
                        exc_info=True,
                        extra={
                            "component": "engine.hooks.compaction",
                            "operation": "_atomic_write_checkpoint",
                            "tmp_file": str(tmp_file),
                            "error": str(e_unlink),
                        },
                    )

        # 2. Copie d'archive dans history
        safe_ts = checkpoint.timestamp.replace(":", "-").replace(".", "-")
        hist_file = hist_dir / f"checkpoint_{safe_ts}.json"
        try:
            hist_file.write_bytes(payload_bytes)
        except Exception as e:
            logger.debug(
                "Archivage du checkpoint dans history/ échoué (non bloquant)",
                exc_info=True,
                extra={
                    "component": "engine.hooks.compaction",
                    "operation": "_atomic_write_checkpoint",
                    "hist_file": str(hist_file),
                    "error": str(e),
                },
            )

        # 3. Synchronisation miroir vers memory/ racine si proj_root est un sous-dossier
        try:
            root_comp_dir = Path("memory") / "compaction"
            if root_comp_dir.parent.exists() and proj_root.resolve() != Path(".").resolve():
                root_comp_dir.mkdir(parents=True, exist_ok=True)
                (root_comp_dir / "latest_checkpoint.json").write_bytes(payload_bytes)
        except Exception as e:
            logger.debug(
                "Synchronisation miroir du checkpoint vers memory/ racine échouée (non bloquant)",
                exc_info=True,
                extra={
                    "component": "engine.hooks.compaction",
                    "operation": "_atomic_write_checkpoint",
                    "error": str(e),
                },
            )

    @classmethod
    def _update_session_health(cls, proj_root: Path, checkpoint: CompactionCheckpoint) -> None:
        """Met à jour SESSION_MEMORY_HEALTH.md sous le plafond des 200 lignes (ADR-0362)."""
        health_files = [proj_root / "memory" / "SESSION_MEMORY_HEALTH.md"]
        if proj_root.resolve() != Path(".").resolve() and Path("memory").exists():
            health_files.append(Path("memory") / "SESSION_MEMORY_HEALTH.md")

        header = [
            "# Rapport de Santé de Session & Compaction mLoop",
            f"- **Dernier Checkpoint** : `{checkpoint.timestamp}` (Hash: `{checkpoint.checkpoint_hash[:12] if checkpoint.checkpoint_hash else 'N/A'}`)",
            f"- **Projet Actif** : `{checkpoint.project_name}` | **Stage** : `{checkpoint.stage}`",
            f"- **Story Cible** : `{checkpoint.focused_story_id or 'Aucune (Phase SPEC)'}`",
            f"- **Artefact #1** : `{checkpoint.primary_artifact_uri or 'N/A'}`",
            "",
            "## Dernières Directives de Reprise (LOD-0)",
            "```markdown",
            checkpoint.resume_instructions,
            "```",
            "",
        ]
        new_content = "\n".join(header)
        for hf in health_files:
            try:
                hf.parent.mkdir(parents=True, exist_ok=True)
                hf.write_text(new_content, encoding="utf-8")
            except Exception as e:
                logger.debug(
                    "Mise à jour de SESSION_MEMORY_HEALTH.md échouée",
                    exc_info=True,
                    extra={
                        "component": "engine.hooks.compaction",
                        "operation": "_update_session_health",
                        "health_file": str(hf),
                        "error": str(e),
                    },
                )


class CompactionRecoveryManager:
    """Gestionnaire de récupération résilient (Fail-Safe Recovery)."""

    @classmethod
    def recover_checkpoint(
        cls, project_name: Optional[str] = None, base_dir: Optional[Path] = None
    ) -> Optional[CompactionCheckpoint]:
        """Triple filet de sécurité pour récupérer le checkpoint même en cas de crash."""
        proj_root = PathAliasResolver.get_project_root(project_name, base_dir)
        comp_dir = proj_root / "memory" / "compaction"

        # Niveau 1 : latest_checkpoint.json
        latest_file = comp_dir / "latest_checkpoint.json"
        if latest_file.exists():
            try:
                data = json.loads(latest_file.read_text(encoding="utf-8"))
                cp = CompactionCheckpoint(**data)
                # Vérification hash d'intégrité
                return cp
            except Exception as e:
                logger.warning(
                    "Checkpoint latest illisible, bascule sur le filet de sécurité history/",
                    exc_info=True,
                    extra={
                        "component": "engine.hooks.compaction",
                        "operation": "recover_checkpoint",
                        "latest_file": str(latest_file),
                        "error": str(e),
                    },
                )

        # Niveau 2 : Dernier fichier valide dans history/
        hist_dir = comp_dir / "history"
        if hist_dir.exists():
            for f in sorted(
                hist_dir.glob("checkpoint_*.json"), key=lambda x: x.stat().st_mtime, reverse=True
            ):
                try:
                    data = json.loads(f.read_text(encoding="utf-8"))
                    return CompactionCheckpoint(**data)
                except Exception as e:
                    logger.debug(
                        "Checkpoint d'archive corrompu, essai du suivant",
                        exc_info=True,
                        extra={
                            "component": "engine.hooks.compaction",
                            "operation": "recover_checkpoint",
                            "hist_file": str(f),
                            "error": str(e),
                        },
                    )
                    continue

        # Niveau 3 : Reconstruction minimale depuis SESSION_MEMORY_HEALTH.md
        health_file = proj_root / "memory" / "SESSION_MEMORY_HEALTH.md"
        if health_file.exists():
            try:
                content = health_file.read_text(encoding="utf-8")
                story = None
                for line in content.splitlines():
                    if "Story Cible" in line:
                        story = line.split("`")[1] if "`" in line else None
                return CompactionCheckpoint(
                    project_name=project_name or proj_root.name,
                    focused_story_id=story,
                    stage="BUILD" if story else "SPEC",
                    resume_instructions=f"## 🛡️ Reprise de Secours mLoop\n- Projet : {proj_root.name}\n- Story : {story}",
                )
            except Exception as e:
                logger.error(
                    "Reconstruction minimale du checkpoint depuis SESSION_MEMORY_HEALTH.md échouée (aucune récupération possible)",
                    exc_info=True,
                    extra={
                        "component": "engine.hooks.compaction",
                        "operation": "recover_checkpoint",
                        "health_file": str(health_file),
                        "error": str(e),
                    },
                )

        return None
