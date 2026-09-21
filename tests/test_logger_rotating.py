"""
Tests unitaires pour MLOOP-110-BE : Persistance Rotative des Journaux d'Erreurs.
Valide le RotatingFileHandler, la rotation par taille et le format structuré.
"""

import logging
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from src.utils.logger import (
    MLoopFormatter,
    MLoopLoggerAdapter,
    _setup_rotating_error_handler,
    _setup_rotating_info_handler,
    get_logger,
)


@pytest.fixture
def log_dir():
    """Crée un répertoire temporaire pour les logs de test."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def clean_logger():
    """Nettoie les handlers du logger mloop entre les tests."""
    logger = logging.getLogger("mloop.test_rotating")
    original_handlers = logger.handlers[:]
    yield logger
    for h in logger.handlers:
        try:
            h.close()
        except Exception:
            pass
    logger.handlers.clear()
    logger.handlers.extend(original_handlers)


class TestMLoopFormatter:
    """Tests pour le formateur MLoopFormatter."""

    def test_console_format(self):
        fmt = MLoopFormatter(debug_mode=False, file_mode=False)
        assert "%(levelname)s" in fmt._fmt
        assert "%(message)s" in fmt._fmt

    def test_debug_format(self):
        fmt = MLoopFormatter(debug_mode=True, file_mode=False)
        assert "%(asctime)s" in fmt._fmt
        assert "%(lineno)d" in fmt._fmt

    def test_file_format(self):
        fmt = MLoopFormatter(file_mode=True)
        assert "%(asctime)s" in fmt._fmt
        assert fmt.datefmt == "%Y-%m-%d %H:%M:%S"

    def test_extracts_extra_attrs(self):
        fmt = MLoopFormatter(debug_mode=False, file_mode=False)
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="hello",
            args=(),
            exc_info=None,
        )
        record.custom_key = "custom_value"
        result = fmt.format(record)
        assert "custom_key=custom_value" in result


class TestRotatingErrorHandler:
    """Tests pour le RotatingFileHandler d'erreurs."""

    def test_error_handler_created(self, log_dir, clean_logger):
        _setup_rotating_error_handler(clean_logger, log_dir)
        error_handlers = [
            h
            for h in clean_logger.handlers
            if isinstance(h, logging.handlers.RotatingFileHandler) and h.level == logging.ERROR
        ]
        assert len(error_handlers) == 1
        assert error_handlers[0].baseFilename.endswith("errors.log")

    def test_error_log_receives_error_messages(self, log_dir, clean_logger):
        _setup_rotating_error_handler(clean_logger, log_dir)
        error_log = log_dir / "errors.log"
        clean_logger.error("Test error message")
        for h in clean_logger.handlers:
            h.flush()
        assert error_log.exists()
        content = error_log.read_text(encoding="utf-8")
        assert "Test error message" in content

    def test_error_log_ignores_info_messages(self, log_dir, clean_logger):
        _setup_rotating_error_handler(clean_logger, log_dir)
        error_log = log_dir / "errors.log"
        clean_logger.info("Test info message")
        for h in clean_logger.handlers:
            h.flush()
        if error_log.exists():
            content = error_log.read_text(encoding="utf-8")
            assert "Test info message" not in content

    def test_rotation_on_max_bytes(self, log_dir, clean_logger):
        tiny_max = 100
        _setup_rotating_error_handler(clean_logger, log_dir, max_bytes=tiny_max, backup_count=3)
        for i in range(20):
            clean_logger.error(f"Error line {i} with enough content to trigger rotation {'x' * 50}")
        for h in clean_logger.handlers:
            h.flush()
        error_log = log_dir / "errors.log"
        assert error_log.exists()
        backup_files = list(log_dir.glob("errors.log.*"))
        assert len(backup_files) > 0


class TestRotatingInfoHandler:
    """Tests pour le RotatingFileHandler info."""

    def test_info_handler_created(self, log_dir, clean_logger):
        _setup_rotating_info_handler(clean_logger, log_dir)
        info_handlers = [
            h
            for h in clean_logger.handlers
            if isinstance(h, logging.handlers.RotatingFileHandler) and h.level == logging.INFO
        ]
        assert len(info_handlers) == 1
        assert info_handlers[0].baseFilename.endswith("mloop.log")

    def test_info_log_contains_all_levels(self, log_dir, clean_logger):
        clean_logger.setLevel(logging.INFO)
        _setup_rotating_info_handler(clean_logger, log_dir)
        clean_logger.info("Info message")
        clean_logger.warning("Warning message")
        clean_logger.error("Error message")
        for h in clean_logger.handlers:
            h.flush()
        info_log = log_dir / "mloop.log"
        content = info_log.read_text(encoding="utf-8")
        assert "Info message" in content
        assert "Warning message" in content
        assert "Error message" in content


class TestGetLoggerIntegration:
    """Tests d'intégration pour get_logger avec persistance rotative."""

    @patch.dict(
        os.environ,
        {
            "MLOOP_LOG_DIR": "",
            "MLOOP_LOG_ENABLE_FILE": "true",
            "MLOOP_LOG_LEVEL": "DEBUG",
        },
        clear=False,
    )
    def test_get_logger_creates_file_handlers(self, log_dir):
        with patch.dict(os.environ, {"MLOOP_LOG_DIR": str(log_dir)}, clear=False):
            logger = get_logger("test_integration")
            rotating_handlers = [
                h for h in logger.handlers if isinstance(h, logging.handlers.RotatingFileHandler)
            ]
            assert len(rotating_handlers) == 2
            for h in rotating_handlers:
                h.close()
                logger.removeHandler(h)

    @patch.dict(os.environ, {"MLOOP_LOG_ENABLE_FILE": "false"}, clear=False)
    def test_get_logger_disabled_file_logging(self):
        logger = get_logger("test_no_file")
        rotating_handlers = [
            h for h in logger.handlers if isinstance(h, logging.handlers.RotatingFileHandler)
        ]
        assert len(rotating_handlers) == 0

    def test_get_logger_returns_adapter_with_context(self):
        logger = get_logger("test_adapter", project="mLoop", story_id="US-01")
        assert isinstance(logger, MLoopLoggerAdapter)
        assert logger.extra["project"] == "mLoop"
        assert logger.extra["story_id"] == "US-01"

    def test_get_logger_singleton_behavior(self):
        logger1 = get_logger("test_singleton")
        logger2 = get_logger("test_singleton")
        assert logger1 is logger2


class TestMLoopLoggerAdapter:
    """Tests pour l'adaptateur contextuel."""

    def test_process_merges_extra(self):
        base_logger = logging.getLogger("mloop.test_adapter_merge")
        adapter = MLoopLoggerAdapter(base_logger, {"project": "mLoop"})
        msg, kwargs = adapter.process("test", {"extra": {"story_id": "US-01"}})
        assert kwargs["extra"]["project"] == "mLoop"
        assert kwargs["extra"]["story_id"] == "US-01"
