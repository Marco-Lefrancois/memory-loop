"""
Tests unitaires pour MLOOP-142-BE : Instrumentation Logging des 5 Handlers CLI Principaux.

Valide que les 5 handlers à fort volume d'erreurs utilisateur
(`code_intelligence`, `build_harness`, `analysis_audit`, `tooling`, `export_story`)
routent leurs échecs vers `LoggingConsole.error` avec un contexte structuré
(`command`, `project`, `story_id`, `target_keys`, `dry_run`, `apply_mode`,
`subcommand`) et que les exceptions injectées atterrissent dans `errors.log`
(niveau ERROR, `exc_info=True`), conformément à ADR-0369 (Zero-Silent-Pass).

Le contrat testé (calqué sur `tests/test_cli_logging.py` — MLOOP-140-BE) :
1. Chemins de validation d'arguments → `LoggingConsole.error(command=..., project=...)`.
2. Chemins d'exception → `LoggingConsole.error(..., exc_info=True)`.
3. Ex-`except Exception:` nus silencieux → `logger.debug(..., exc_info=True)`
   sans altérer le flux de contrôle (fallback préservé).
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest


# ─── Fixtures ──────────────────────────────────────────────────────────────


def _ns(**kwargs) -> argparse.Namespace:
    """Construit un Namespace argparse minimal pour piloter un handler."""
    return argparse.Namespace(**kwargs)


@pytest.fixture
def captured_error():
    """Patch LoggingConsole.error dans src.cli et capture ses appels."""
    from src import cli

    with patch.object(cli.LoggingConsole, "error") as mock_err:
        yield mock_err


def _last_kwargs(mock_err) -> dict:
    """Retourne les kwargs du dernier appel à LoggingConsole.error."""
    assert mock_err.called, "LoggingConsole.error n'a pas été appelé."
    _, kwargs = mock_err.call_args
    return kwargs


# ─── 1. code_intelligence.py ────────────────────────────────────────────────


class TestCodeIntelligenceLogging:
    """code-explore / graph-query / code-impact / code-affected / code-status."""

    def test_code_explore_missing_query_logs_context(self):
        from src.commands.handlers import code_intelligence as ci
        from src.commands.handlers import _codegraph_common as cc

        # codegraph présent, mais --query vide → erreur de validation loggée.
        with patch.object(ci, "_get_codegraph_binary", return_value="codegraph"):
            with patch.object(cc.LoggingConsole, "error") as mock_err:
                rc = ci.handle_code_explore(_ns(query="", path=None, project="mLoop"))
                assert rc == 1
                _, kwargs = mock_err.call_args
                assert kwargs["command"] == "code-explore"
                assert kwargs["project"] == "mLoop"

    def test_code_explore_binary_missing_logs(self):
        from src.commands.handlers import code_intelligence as ci
        from src.commands.handlers import _codegraph_common as cc

        with patch.object(ci, "_get_codegraph_binary", return_value=None):
            with patch.object(cc.LoggingConsole, "error") as mock_err:
                rc = ci.handle_code_explore(_ns(query="Foo", path=None, project="mLoop"))
                assert rc == 1
                _, kwargs = mock_err.call_args
                assert kwargs["command"] == "code-explore"

    def test_code_explore_exception_logs_exc_info(self):
        from src.commands.handlers import code_intelligence as ci
        from src.commands.handlers import _codegraph_common as cc

        with patch.object(ci, "_get_codegraph_binary", return_value="codegraph"):
            with patch.object(
                ci, "_run_codegraph_command", side_effect=RuntimeError("boom explore")
            ):
                with patch.object(ci, "_find_target_source_path", return_value=Path(".")):
                    with patch.object(cc.LoggingConsole, "error") as mock_err:
                        rc = ci.handle_code_explore(
                            _ns(query="Foo", path=None, project="mLoop", compact=False)
                        )
                        assert rc == 1
                        _, kwargs = mock_err.call_args
                        assert kwargs["command"] == "code-explore"
                        assert kwargs.get("exc_info") is True

    def test_code_impact_missing_symbol_logs(self):
        from src.commands.handlers import code_intelligence as ci
        from src.commands.handlers import _codegraph_common as cc

        with patch.object(ci, "_get_codegraph_binary", return_value="codegraph"):
            with patch.object(cc.LoggingConsole, "error") as mock_err:
                rc = ci.handle_code_impact(_ns(symbol="", path=None, project="mLoop"))
                assert rc == 1
                _, kwargs = mock_err.call_args
                assert kwargs["command"] == "code-impact"

    def test_resolve_source_path_silent_pass_is_instrumented(self):
        """L'ex-`except Exception:` nu (résolution projet actif) logge en DEBUG."""
        from src.commands.handlers import _codegraph_common as cc

        with patch("src.loop_mem.db.get_active_project", side_effect=RuntimeError("db down")):
            with patch.object(cc.logger, "debug") as mock_debug:
                # Ne doit PAS lever : le fallback racine workspace est préservé.
                result = cc._find_target_source_path(project_path=None, explicit_path=None)
                assert result == Path(".")
                assert mock_debug.called
                _, kwargs = mock_debug.call_args
                assert kwargs.get("exc_info") is True


# ─── 2. build_harness.py ────────────────────────────────────────────────────


class TestBuildHarnessLogging:
    """code-check / code-tournament / tdd-enforce."""

    def test_code_check_no_target_logs(self):
        from src.commands.handlers import build_harness as bh

        with patch.object(bh.LoggingConsole, "error") as mock_err:
            rc = bh.handle_code_check(_ns(file=None, all=False, story=None, project="mLoop"))
            assert rc == 1
            _, kwargs = mock_err.call_args
            assert kwargs["command"] == "code-check"

    def test_code_tournament_missing_args_logs_story_id(self):
        from src.commands.handlers import build_harness as bh

        with patch.object(bh.LoggingConsole, "error") as mock_err:
            rc = bh.handle_code_tournament(
                _ns(story=None, target=None, test_file=None, project="mLoop")
            )
            assert rc == 1
            _, kwargs = mock_err.call_args
            assert kwargs["command"] == "code-tournament"
            assert "story_id" in kwargs

    def test_tdd_enforce_missing_args_logs_phase(self):
        from src.commands.handlers import build_harness as bh

        with patch.object(bh.LoggingConsole, "error") as mock_err:
            rc = bh.handle_tdd_enforce(
                _ns(
                    phase=None,
                    story=None,
                    test_file=None,
                    source_file=None,
                    project="mLoop",
                )
            )
            assert rc == 1
            _, kwargs = mock_err.call_args
            assert kwargs["command"] == "tdd-enforce"
            assert "phase" in kwargs


# ─── 3. analysis_audit.py ───────────────────────────────────────────────────


class TestAnalysisAuditLogging:
    """struct-check / rubber-duck / dossier-init."""

    def test_dossier_init_missing_story_logs(self, tmp_path):
        from src.commands.handlers import analysis_audit as aa

        with patch.object(aa.LoggingConsole, "error") as mock_err:
            rc = aa.handle_dossier_init(
                _ns(story=None, force=False, project="mLoop"), None, tmp_path
            )
            assert rc == 1
            _, kwargs = mock_err.call_args
            assert kwargs["command"] == "dossier-init"
            assert kwargs["project"] == "mLoop"

    def test_dossier_init_unresolvable_story_logs_story_id(self, tmp_path):
        from src.commands.handlers import analysis_audit as aa

        # stories_dir inexistant + query non résolvable → erreur "introuvable".
        with patch(
            "src.utils.lexicon_resolver.SemanticLexiconResolver.resolve_story_query",
            return_value=None,
        ):
            with patch.object(aa.LoggingConsole, "error") as mock_err:
                rc = aa.handle_dossier_init(
                    _ns(story="ZZZ-999-XX", force=False, project="mLoop"),
                    None,
                    tmp_path,
                )
                assert rc == 1
                _, kwargs = mock_err.call_args
                assert kwargs["command"] == "dossier-init"
                assert kwargs.get("story_id") == "ZZZ-999-XX"

    def test_struct_check_target_not_found_logs(self, tmp_path):
        from src.commands.handlers import analysis_audit as aa

        # Aucun fichier ne matche → chemin "Fichier cible introuvable".
        fake_engine = MagicMock()
        with patch("src.pipelines.struct_checker.StructCheckEngine", return_value=fake_engine):
            with patch.object(aa.LoggingConsole, "error") as mock_err:
                rc = aa.handle_struct_check(
                    _ns(
                        strict=False,
                        verbose=False,
                        file="inexistant_xyz_142",
                        project="mLoop",
                    ),
                    None,
                    tmp_path,
                )
                assert rc == 1
                _, kwargs = mock_err.call_args
                assert kwargs["command"] == "struct-check"


# ─── 4. tooling.py ──────────────────────────────────────────────────────────


class TestToolingLogging:
    """archify / csv-validate / csv-normalize / csv-anonymize / csv-diff."""

    def test_archify_missing_file_logs(self, tmp_path):
        from src.commands.handlers import tooling

        # doctor=False + file=None → erreur de validation.
        with patch.object(tooling.LoggingConsole, "error") as mock_err:
            rc = tooling.handle_archify(
                _ns(
                    doctor=False,
                    file=None,
                    type=None,
                    project="mLoop",
                    validate_only=False,
                    output=None,
                    quality=None,
                ),
                None,
                tmp_path,
            )
            assert rc == 1
            _, kwargs = mock_err.call_args
            assert kwargs["command"] == "archify"

    def test_csv_validate_missing_file_logs_target(self, tmp_path):
        from src.commands.handlers import tooling

        missing = tmp_path / "absent.csv"
        schema = tmp_path / "schema.json"
        schema.write_text("{}", encoding="utf-8")
        with patch.object(tooling.LoggingConsole, "error") as mock_err:
            rc = tooling.handle_csv_validate(
                _ns(file=str(missing), schema=str(schema), project="mLoop"),
                None,
                None,
            )
            assert rc == 1
            _, kwargs = mock_err.call_args
            assert kwargs["command"] == "csv-validate"
            assert "target_keys" in kwargs

    def test_csv_diff_missing_old_logs(self, tmp_path):
        from src.commands.handlers import tooling

        with patch.object(tooling.LoggingConsole, "error") as mock_err:
            rc = tooling.handle_csv_diff(
                _ns(
                    old=str(tmp_path / "absent_old.csv"),
                    new=str(tmp_path / "absent_new.csv"),
                    key="id",
                    project="mLoop",
                ),
                None,
                None,
            )
            assert rc == 1
            _, kwargs = mock_err.call_args
            assert kwargs["command"] == "csv-diff"


# ─── 5. export_story.py ─────────────────────────────────────────────────────


class TestExportStoryLogging:
    """jira_sync : validation d'arguments + Zero-Silent-Pass sur le manifeste."""

    def test_jira_sync_no_target_logs_full_context(self):
        from src.commands.handlers import export_story as es
        from src.commands.handlers import _jira_sync_common as jc

        state = SimpleNamespace(project_name="mLoop")
        args = _ns(
            apply=False,
            dry_run=False,
            all=False,
            confirm_all_project_stories=False,
            allow_in_analyze=False,
            confirm_scope=None,
            story=None,
            stories=None,
        )
        with patch.object(jc.LoggingConsole, "error") as mock_err:
            rc = es.handle_jira_sync(args, state, Path("."))
            assert rc == 2
            _, kwargs = mock_err.call_args
            assert kwargs["command"] == "jira_sync"
            assert kwargs["project"] == "mLoop"
            assert "apply_mode" in kwargs
            assert "dry_run" in kwargs

    def test_jira_sync_all_mode_locked_logs(self):
        from src.commands.handlers import export_story as es
        from src.commands.handlers import _jira_sync_common as jc

        state = SimpleNamespace(project_name="mLoop")
        args = _ns(
            apply=False,
            dry_run=False,
            all=True,
            confirm_all_project_stories=False,
            allow_in_analyze=False,
            confirm_scope=None,
            story=None,
            stories=None,
        )
        with patch.object(jc.LoggingConsole, "error") as mock_err:
            rc = es.handle_jira_sync(args, state, Path("."))
            assert rc == 2
            _, kwargs = mock_err.call_args
            assert kwargs["command"] == "jira_sync"
            assert kwargs.get("apply_mode") is False

    def test_jira_sync_temp_key_blocked_logs(self):
        from src.commands.handlers import export_story as es
        from src.commands.handlers import _jira_sync_common as jc

        state = SimpleNamespace(project_name="mLoop")
        args = _ns(
            apply=False,
            dry_run=False,
            all=False,
            confirm_all_project_stories=False,
            allow_in_analyze=False,
            confirm_scope=None,
            story="TEMP-001",
            stories=None,
        )
        with patch.object(jc.LoggingConsole, "error") as mock_err:
            rc = es.handle_jira_sync(args, state, Path("."))
            assert rc == 2
            _, kwargs = mock_err.call_args
            assert kwargs["command"] == "jira_sync"
            assert kwargs.get("target_keys") == ["TEMP-001"]

    def test_verify_manifest_corrupt_read_is_instrumented(self, tmp_path):
        """L'ex-`except Exception:` nu (manifeste corrompu) logge en DEBUG sans lever."""
        from src.commands.handlers import export_story as es
        from src.commands.handlers import _jira_sync_common as jc

        manifest_dir = tmp_path / "memory" / "sync"
        manifest_dir.mkdir(parents=True, exist_ok=True)
        # Manifeste JSON corrompu → déclenche l'exception de lecture.
        (manifest_dir / "jira_sync_preview.json").write_text(
            "{ this is not valid json", encoding="utf-8"
        )

        preview = {"file_hashes": {}}
        with patch.object(jc.logger, "debug") as mock_debug:
            result = es._verify_sha256_manifest(preview, tmp_path)
            # Le contrat : on ne lève pas, on écrit le nouveau manifeste (True).
            assert result is True
            assert mock_debug.called
            _, kwargs = mock_debug.call_args
            assert kwargs.get("exc_info") is True


# ─── 6. Contrat d'intégration errors.log (Zero-Silent-Pass ADR-0369) ─────────


class TestErrorsLogIntegrationContract:
    """
    Contrat de bout en bout : une erreur routée via LoggingConsole.error avec
    exc_info=True est physiquement persistée dans errors.log.
    """

    @pytest.fixture
    def isolated_error_logger(self, tmp_path):
        from src.utils.logger import _setup_rotating_error_handler

        logger = logging.getLogger("mloop.handler.test_142_integration")
        original = logger.handlers[:]
        logger.handlers.clear()
        logger.setLevel(logging.ERROR)
        logger.propagate = False
        _setup_rotating_error_handler(logger, tmp_path)
        yield logger, tmp_path
        for h in logger.handlers:
            try:
                h.flush()
                h.close()
            except Exception:
                pass
        logger.handlers.clear()
        logger.handlers.extend(original)

    def test_handler_exception_context_written_to_errors_log(self, isolated_error_logger):
        logger, ldir = isolated_error_logger
        try:
            raise RuntimeError("Panne handler simulée MLOOP-142")
        except RuntimeError:
            logger.error(
                "Erreur d'execution : Panne handler simulée MLOOP-142",
                extra={
                    "command": "code-explore",
                    "project": "mLoop",
                    "target_keys": "AuthService",
                },
                exc_info=True,
            )
        for h in logger.handlers:
            h.flush()

        content = (ldir / "errors.log").read_text(encoding="utf-8")
        assert "Panne handler simulée MLOOP-142" in content
        assert "command=code-explore" in content
        assert "project=mLoop" in content
        assert "target_keys=AuthService" in content
        assert "RuntimeError" in content
        assert "Traceback" in content
