# -*- coding: utf-8 -*-
"""
Tests unitaires pour les Hooks de Pré-Compaction & Checkpoint Boundaries (ADR-0364).
"""
import json
import pytest
from pathlib import Path

from src.engine.hooks.path_resolver import PathAliasResolver
from src.engine.hooks.compaction import (
    PreCompactionHandler,
    CompactionRecoveryManager,
    CompactionCheckpoint,
    FileReservation,
    ToolOutcome,
)
from src.engine.hooks.registry import LifecycleHookRegistry, global_hook_registry
from src.utils.context_guard import ContextGuard
from src.commands.handlers.hook import handle_hook
import argparse


@pytest.fixture
def temp_project(tmp_path):
    """Crée une arborescence de projet mLoop éphémère isolée."""
    proj_dir = tmp_path / "Projects" / "TestCompaction"
    (proj_dir / "docs" / "00-ingested").mkdir(parents=True)
    (proj_dir / "docs" / "05-assets" / "maquettes").mkdir(parents=True)
    (proj_dir / "backlog" / "stories").mkdir(parents=True)
    (proj_dir / "memory" / "evidence").mkdir(parents=True)
    (proj_dir / "memory" / "compaction").mkdir(parents=True)

    # Documents de base
    (proj_dir / "docs" / "00-ingested" / "cadrage_technique.md").write_text("# Cadrage", encoding="utf-8")
    (proj_dir / "docs" / "05-assets" / "maquettes" / "screen_v1.svg").write_text("<svg></svg>", encoding="utf-8")
    (proj_dir / "backlog" / "stories" / "REC-100.md").write_text(
        "---\nid: REC-100\nstatus: IN_ANALYZE\n---\n# Titre Story\n## Critères d'acceptation\n- [ ] Critère 1\n## Scénarios de test\n### Pilier 1 : Scénario Nominal\n- Given A When B Then C\n",
        encoding="utf-8"
    )
    (proj_dir / "memory" / "evidence" / "REC-100_fact_dossier.md").write_text("# Preuves REC-100", encoding="utf-8")

    return proj_dir


class TestPathAliasResolver:
    """Tests de résolution et compression des Micro-URIs canoniques."""

    def test_resolve_micro_uris(self, temp_project):
        base_dir = temp_project.parent.parent
        proj_name = "TestCompaction"

        # assets://
        p_asset = PathAliasResolver.resolve("assets://screen_v1.svg", proj_name, base_dir)
        assert p_asset.name == "screen_v1.svg"
        assert "05-assets" in str(p_asset)

        # story:// avec extension implicite
        p_story = PathAliasResolver.resolve("story://REC-100", proj_name, base_dir)
        assert p_story.name == "REC-100.md"
        assert "backlog" in str(p_story)

        # evidence:// avec extension implicite
        p_evidence = PathAliasResolver.resolve("evidence://REC-100", proj_name, base_dir)
        assert p_evidence.name == "REC-100_fact_dossier.md"

        # source://
        p_source = PathAliasResolver.resolve("source://cadrage_technique.md", proj_name, base_dir)
        assert p_source.name == "cadrage_technique.md"

    def test_to_micro_uri(self, temp_project):
        base_dir = temp_project.parent.parent
        proj_name = "TestCompaction"

        phys_path = temp_project / "docs" / "05-assets" / "maquettes" / "screen_v1.svg"
        uri = PathAliasResolver.to_micro_uri(phys_path, proj_name, base_dir)
        assert uri == "assets://screen_v1.svg"

        story_path = temp_project / "backlog" / "stories" / "REC-100.md"
        uri_story = PathAliasResolver.to_micro_uri(story_path, proj_name, base_dir)
        assert uri_story == "story://REC-100"

    def test_get_project_root_stability(self, temp_project):
        base_dir = temp_project.parent.parent
        # Via nom
        root = PathAliasResolver.get_project_root("TestCompaction", base_dir)
        assert root.resolve() == temp_project.resolve()

        # Directement depuis le dossier projet
        root_direct = PathAliasResolver.get_project_root("TestCompaction", temp_project)
        assert root_direct.resolve() == temp_project.resolve()


class TestPreCompactionEngine:
    """Tests du cycle de génération de checkpoints et calcul de boussole LOD-0."""

    def test_checkpoint_creation_and_token_ceiling(self, temp_project):
        base_dir = temp_project.parent.parent
        checkpoint = PreCompactionHandler.create_checkpoint(
            project_name="TestCompaction",
            focused_story_id="REC-100",
            stage="BUILD",
            base_dir=base_dir,
        )

        assert checkpoint.project_name == "TestCompaction"
        assert checkpoint.focused_story_id == "REC-100"
        assert checkpoint.stage == "BUILD"
        assert checkpoint.checkpoint_hash is not None
        assert len(checkpoint.checkpoint_hash) == 64  # SHA-256

        # Vérification du budget de jetons (<= 1600 caractères ~ 400 tokens)
        assert len(checkpoint.resume_instructions) <= 1600
        assert "## 🛡️ mLoop Checkpoint Invariant" in checkpoint.resume_instructions

        # Vérification persistance sur disque
        latest_file = temp_project / "memory" / "compaction" / "latest_checkpoint.json"
        assert latest_file.exists()

        loaded_data = json.loads(latest_file.read_text(encoding="utf-8"))
        assert loaded_data["checkpoint_hash"] == checkpoint.checkpoint_hash

    def test_primary_artifact_resolution_zero_blindspot(self, temp_project):
        base_dir = temp_project.parent.parent

        # Phase BUILD avec story REC-100 -> Artefact #1 = fact_dossier
        cp_build = PreCompactionHandler.create_checkpoint(
            project_name="TestCompaction",
            focused_story_id="REC-100",
            stage="BUILD",
            base_dir=base_dir,
        )
        assert cp_build.primary_artifact_uri == "evidence://REC-100_fact_dossier.md"

        # Phase SPEC sans story -> Artefact #1 = premier document ingéré
        cp_spec = PreCompactionHandler.create_checkpoint(
            project_name="TestCompaction",
            focused_story_id=None,
            stage="SPEC",
            base_dir=base_dir,
        )
        assert "source://" in (cp_spec.primary_artifact_uri or "")


class TestCompactionRecoveryManager:
    """Tests du Triple Filet de Récupération (Fail-Safe Recovery)."""

    def test_recover_level_1_latest(self, temp_project):
        base_dir = temp_project.parent.parent
        created = PreCompactionHandler.create_checkpoint(
            project_name="TestCompaction",
            focused_story_id="REC-100",
            stage="BUILD",
            base_dir=base_dir,
        )

        recovered = CompactionRecoveryManager.recover_checkpoint(
            project_name="TestCompaction", base_dir=base_dir
        )
        assert recovered is not None
        assert recovered.checkpoint_hash == created.checkpoint_hash
        assert recovered.focused_story_id == "REC-100"

    def test_recover_level_2_history_fallback(self, temp_project):
        base_dir = temp_project.parent.parent
        created = PreCompactionHandler.create_checkpoint(
            project_name="TestCompaction",
            focused_story_id="REC-100",
            stage="BUILD",
            base_dir=base_dir,
        )

        # Suppression intentionnelle de latest_checkpoint.json pour forcer le niveau 2
        latest_file = temp_project / "memory" / "compaction" / "latest_checkpoint.json"
        latest_file.unlink()

        recovered = CompactionRecoveryManager.recover_checkpoint(
            project_name="TestCompaction", base_dir=base_dir
        )
        assert recovered is not None
        assert recovered.checkpoint_hash == created.checkpoint_hash

    def test_recover_level_3_session_health_fallback(self, temp_project):
        base_dir = temp_project.parent.parent
        # Création d'un SESSION_MEMORY_HEALTH.md sans checkpoints json
        comp_dir = temp_project / "memory" / "compaction"
        for f in comp_dir.glob("**/*"):
            if f.is_file():
                f.unlink()

        health_file = temp_project / "memory" / "SESSION_MEMORY_HEALTH.md"
        health_file.write_text(
            "# Diagnostic de Santé\n- **Projet Actif** : `TestCompaction`\n- **Story Cible** : `REC-100`\n",
            encoding="utf-8"
        )

        recovered = CompactionRecoveryManager.recover_checkpoint(
            project_name="TestCompaction", base_dir=base_dir
        )
        assert recovered is not None
        assert recovered.focused_story_id == "REC-100"


class TestContextGuardSidecarOffloading:
    """Tests de déportement sidecar pour les payloads volumineux."""

    def test_offload_heavy_tool_output(self, temp_project):
        base_dir = temp_project.parent.parent
        proj_name = "TestCompaction"

        short_output = "Petite sortie normale sous 2000 caractères."
        res_short = ContextGuard.offload_heavy_tool_output(
            short_output, max_chars=2000, project_name=proj_name, base_dir=base_dir
        )
        assert res_short == short_output

        heavy_output = "LIGNE_DE_TEST\n" * 200
        res_heavy = ContextGuard.offload_heavy_tool_output(
            heavy_output, max_chars=500, project_name=proj_name, base_dir=base_dir
        )
        assert len(res_heavy) < len(heavy_output)
        assert "evidence://../artifacts/sidecars/" in res_heavy
        assert "[⚠️ Sortie volumineuse" in res_heavy

        # Vérification du fichier physique écrit sur disque
        sidecars_dir = temp_project / "memory" / "artifacts" / "sidecars"
        assert sidecars_dir.exists()
        files = list(sidecars_dir.glob("*.txt"))
        assert len(files) == 1
        assert files[0].read_text(encoding="utf-8") == heavy_output


class TestHookCLIHandler:
    """Tests d'intégration du handler CLI 'hook'."""

    def test_handle_hook_pre_compact_and_resume(self, temp_project):
        args_pre = argparse.Namespace(
            event="pre_compact",
            project="TestCompaction",
            format="json",
            story="REC-100",
        )
        exit_code = handle_hook(args_pre, None, temp_project)
        assert exit_code == 0

        args_resume = argparse.Namespace(
            event="resume",
            project="TestCompaction",
            format="json",
            story=None,
        )
        exit_code_resume = handle_hook(args_resume, None, temp_project)
        assert exit_code_resume == 0
