"""
Tests unitaires pour MLOOP-140-BE : Instrumentation Logging Point d'Entrée CLI.

Valide que les exceptions non gérées et le cycle d'exécution du point d'entrée
(`swarm.py`, `router.py`, `cli.py`) sont capturés dans `errors.log` (ERROR,
exc_info) et `mloop.log` (INFO : commande, projet, durée, exit_code) avec
contexte structuré, conformément à ADR-0369.
"""

import logging
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest


@pytest.fixture
def log_dir():
    """Répertoire temporaire isolé pour les journaux rotatifs de test."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def fresh_cli_logger(log_dir):
    """
    Fournit un logger 'mloop.cli' neuf branché sur des handlers rotatifs
    pointant vers un répertoire de test, puis nettoie les handlers.
    """
    from src.utils.logger import (
        _setup_rotating_error_handler,
        _setup_rotating_info_handler,
    )

    logger = logging.getLogger("mloop.cli.test_entrypoint")
    original_handlers = logger.handlers[:]
    logger.handlers.clear()
    logger.setLevel(logging.INFO)
    logger.propagate = False

    _setup_rotating_error_handler(logger, log_dir)
    _setup_rotating_info_handler(logger, log_dir)

    yield logger, log_dir

    for h in logger.handlers:
        try:
            h.flush()
            h.close()
        except Exception:
            pass
    logger.handlers.clear()
    logger.handlers.extend(original_handlers)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


class TestErrorCaptureContract:
    """Le contrat Zero-Silent-Pass : une exception injectée finit dans errors.log."""

    def test_injected_exception_written_to_errors_log(self, fresh_cli_logger):
        logger, ldir = fresh_cli_logger
        try:
            raise RuntimeError("Panne CLI simulée MLOOP-140")
        except RuntimeError:
            logger.error(
                "Exception non gérée durant l'exécution CLI.",
                extra={
                    "command": "vibe-check",
                    "project": "mLoop",
                    "phase": "run",
                    "exit_code": 1,
                },
                exc_info=True,
            )
        for h in logger.handlers:
            h.flush()

        content = _read(ldir / "errors.log")
        assert "Exception non gérée durant l'exécution CLI." in content
        # exc_info=True doit sérialiser la trace de l'exception injectée.
        assert "RuntimeError" in content
        assert "Panne CLI simulée MLOOP-140" in content
        assert "Traceback" in content

    def test_structured_context_serialized_in_errors_log(self, fresh_cli_logger):
        logger, ldir = fresh_cli_logger
        logger.error(
            "Résolution du handler CLI échouée.",
            extra={
                "command": "sync",
                "project": "mLoop",
                "phase": "dispatch",
                "handler_ref": "bad:handler",
            },
        )
        for h in logger.handlers:
            h.flush()

        content = _read(ldir / "errors.log")
        assert "command=sync" in content
        assert "project=mLoop" in content
        assert "phase=dispatch" in content
        assert "handler_ref=bad:handler" in content


class TestExecutionTraceContract:
    """Le contrat de traçabilité INFO complète dans mloop.log."""

    def test_full_execution_traced_in_mloop_log(self, fresh_cli_logger):
        logger, ldir = fresh_cli_logger
        logger.info(
            "Démarrage de l'exécution CLI.",
            extra={"command": "resume", "project": "mLoop", "phase": "run"},
        )
        logger.info(
            "Fin de l'exécution CLI.",
            extra={
                "command": "resume",
                "project": "mLoop",
                "phase": "run",
                "duration_ms": 12.34,
                "exit_code": 0,
            },
        )
        for h in logger.handlers:
            h.flush()

        content = _read(ldir / "mloop.log")
        assert "Démarrage de l'exécution CLI." in content
        assert "Fin de l'exécution CLI." in content
        assert "command=resume" in content
        assert "exit_code=0" in content
        assert "duration_ms=12.34" in content

    def test_info_not_leaked_into_errors_log(self, fresh_cli_logger):
        logger, ldir = fresh_cli_logger
        logger.info(
            "Démarrage de l'exécution CLI.",
            extra={"command": "focus", "project": "mLoop", "phase": "run"},
        )
        for h in logger.handlers:
            h.flush()

        errors_content = _read(ldir / "errors.log")
        assert "Démarrage de l'exécution CLI." not in errors_content


class TestSwarmEntrypointInstrumentation:
    """swarm.py : resolve_project_name / get_project_context / main."""

    def test_resolve_project_name_logs_on_unknown_project(self, log_dir):
        import src.swarm as swarm

        with patch.object(swarm, "logger") as mock_logger:
            with pytest.raises(ValueError):
                swarm.resolve_project_name("projet_totalement_inexistant_xyz_140")
            assert mock_logger.error.called
            _, kwargs = mock_logger.error.call_args
            assert kwargs["extra"]["command"] == "resolve_project_name"
            assert kwargs["extra"]["phase"] == "resolve"

    def test_main_logs_unhandled_exception(self):
        import src.swarm as swarm

        with patch("src.commands.router.execute_cli", side_effect=RuntimeError("boom")):
            with patch.object(swarm, "logger") as mock_logger:
                with pytest.raises(RuntimeError):
                    swarm.main()
                assert mock_logger.error.called
                _, kwargs = mock_logger.error.call_args
                assert kwargs.get("exc_info") is True
                assert kwargs["extra"]["command"] == "main"

    def test_main_logs_keyboard_interrupt_as_warning(self):
        import src.swarm as swarm

        with patch("src.commands.router.execute_cli", side_effect=KeyboardInterrupt()):
            with patch.object(swarm, "logger") as mock_logger:
                with pytest.raises(SystemExit) as exc:
                    swarm.main()
                assert exc.value.code == 130
                assert mock_logger.warning.called
                _, kwargs = mock_logger.warning.call_args
                assert kwargs["extra"]["exit_code"] == 130


class TestRouterInstrumentation:
    """router.py : _resolve_handler / _build_parser / execute_cli."""

    def test_resolve_handler_logs_on_bad_reference(self):
        from src.commands import router

        with patch.object(router, "logger") as mock_logger:
            with pytest.raises(Exception):
                router._resolve_handler("module_inexistant_140:fonction")
            assert mock_logger.error.called
            _, kwargs = mock_logger.error.call_args
            assert kwargs.get("exc_info") is True
            assert kwargs["extra"]["command"] == "_resolve_handler"

    def test_execute_cli_traces_and_exits(self):
        from src.commands import router

        # Simuler un run nominal : _run_cli retourne un code de sortie 0.
        with patch.object(router, "_run_cli", return_value=0):
            with patch.object(router, "logger") as mock_logger:
                with pytest.raises(SystemExit) as exc:
                    router.execute_cli()
                assert exc.value.code == 0
                # Un log de démarrage (info) et un log de fin (info) sont émis.
                assert mock_logger.info.call_count >= 2

    def test_execute_cli_logs_error_on_unhandled_exception(self):
        from src.commands import router

        with patch.object(router, "_run_cli", side_effect=RuntimeError("panne dispatch")):
            with patch.object(router, "logger") as mock_logger:
                with pytest.raises(RuntimeError):
                    router.execute_cli()
                assert mock_logger.error.called
                error_calls = [c for c in mock_logger.error.call_args_list]
                # Au moins un appel error avec exc_info=True (capture ERROR).
                assert any(c.kwargs.get("exc_info") is True for c in error_calls)

    def test_execute_cli_final_exit_code_nonzero_logged_as_error(self):
        from src.commands import router

        with patch.object(router, "_run_cli", return_value=1):
            with patch.object(router, "logger") as mock_logger:
                with pytest.raises(SystemExit) as exc:
                    router.execute_cli()
                assert exc.value.code == 1
                # La clôture (finally) route un exit_code != 0 vers logger.error.
                assert mock_logger.error.called
                _, kwargs = mock_logger.error.call_args
                assert kwargs["extra"]["exit_code"] == 1


class TestLoggingConsoleWrapper:
    """cli.py : LoggingConsole double l'affichage d'une trace persistante."""

    def test_logging_console_error_double_writes(self):
        from src import cli

        with patch.object(cli.ZeroFluffConsole, "error") as mock_console:
            with patch.object(cli, "logger") as mock_logger:
                cli.LoggingConsole.error(
                    "Erreur critique test",
                    command="vibe-check",
                    project="mLoop",
                    phase="run",
                    exc_info=True,
                )
                # 1. Affichage console préservé.
                mock_console.assert_called_once_with("Erreur critique test")
                # 2. Persistance journalisée avec contexte + exc_info.
                assert mock_logger.error.called
                _, kwargs = mock_logger.error.call_args
                assert kwargs["extra"]["command"] == "vibe-check"
                assert kwargs["extra"]["project"] == "mLoop"
                assert kwargs.get("exc_info") is True

    def test_logging_console_info_uses_info_level(self):
        from src import cli

        with patch.object(cli.ZeroFluffConsole, "info") as mock_console:
            with patch.object(cli, "logger") as mock_logger:
                cli.LoggingConsole.info("Message informatif", command="sync", project="mLoop")
                mock_console.assert_called_once_with("Message informatif")
                assert mock_logger.info.called
                assert not mock_logger.error.called

    def test_logging_console_warning_uses_warning_level(self):
        from src import cli

        with patch.object(cli.ZeroFluffConsole, "warning") as mock_console:
            with patch.object(cli, "logger") as mock_logger:
                cli.LoggingConsole.warning("Avertissement", command="focus", project="mLoop")
                mock_console.assert_called_once_with("Avertissement")
                assert mock_logger.warning.called
