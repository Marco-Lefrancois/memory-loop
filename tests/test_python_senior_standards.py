"""
Tests automatisés des 7 Standards de Robustesse Python Senior (ADR-0369 SSOT).
Valide mécaniquement l'application des règles d'ingénierie et de gouvernance des ressources.
"""

import ast
import inspect
import logging
import sqlite3
import subprocess
import warnings
from pathlib import Path
import pytest

from src.utils.logger import MLoopFormatter, MLoopLoggerAdapter, get_logger
from src.loop_mem.db import _get_observation_conn, get_observation_db_session, add_rho_rule, search_rho_solution
from src.commands.handlers.code_intelligence import _run_codegraph_command


class TestPythonSeniorStandards:
    """Suite de validation constitutionnelle ADR-0369."""

    # ═══════════════════════════════════════════════════════════
    # STANDARD 2 : CONTEXT MANAGERS D'ÉTAT & CYCLE DE VIE
    # ═══════════════════════════════════════════════════════════

    def test_get_observation_db_session_commits_and_closes(self, tmp_path):
        """Vérifie que get_observation_db_session garantit commit et close systématiques."""
        db_file = tmp_path / "test_session.db"
        with get_observation_db_session(db_file) as conn:
            conn.execute("CREATE TABLE test_table (id INT, val TEXT)")
            conn.execute("INSERT INTO test_table VALUES (1, 'val1')")
            # En sortie de bloc, commit et close doivent s'exécuter
        
        # Vérification externe : la table et la valeur sont bien persistées
        check_conn = sqlite3.connect(str(db_file))
        row = check_conn.execute("SELECT val FROM test_table WHERE id=1").fetchone()
        check_conn.close()
        assert row[0] == "val1"

    def test_get_observation_db_session_rollback_on_exception(self, tmp_path):
        """Vérifie le rollback automatique en cas d'exception dans le bloc contextuel."""
        db_file = tmp_path / "test_rollback.db"
        # Préparation de la table en amont
        with get_observation_db_session(db_file) as conn:
            conn.execute("CREATE TABLE test_table (id INT PRIMARY KEY, val TEXT)")

        # Tentative d'insertion qui crash
        with pytest.raises(RuntimeError, match="Transaction annulée"):
            with get_observation_db_session(db_file) as conn:
                conn.execute("INSERT INTO test_table VALUES (1, 'val1')")
                raise ValueError("Crash forcé pendant la transaction")

        # La transaction avortée a bien annulé l'insertion
        check_conn = sqlite3.connect(str(db_file))
        rows = check_conn.execute("SELECT * FROM test_table").fetchall()
        check_conn.close()
        assert len(rows) == 0

    # ═══════════════════════════════════════════════════════════
    # STANDARD 3 : DEADLINE / TIMEOUT SUR APPELS SUBPROCESS
    # ═══════════════════════════════════════════════════════════

    def test_run_codegraph_command_has_timeout_parameter(self):
        """Vérifie que _run_codegraph_command possède obligatoirement le paramètre timeout."""
        sig = inspect.signature(_run_codegraph_command)
        assert "timeout" in sig.parameters
        assert sig.parameters["timeout"].default == 30.0

    def test_ast_check_subprocess_has_timeout_in_code_intelligence(self):
        """Audit statique AST : vérifie que subprocess.run dans code_intelligence.py spécifie timeout."""
        source_file = Path("src/commands/handlers/code_intelligence.py")
        tree = ast.parse(source_file.read_text(encoding="utf-8"))

        subprocess_run_calls = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Attribute) and func.attr == "run":
                    if isinstance(func.value, ast.Name) and func.value.id == "subprocess":
                        subprocess_run_calls.append(node)

        assert len(subprocess_run_calls) > 0, "Aucun appel subprocess.run trouvé"
        for call_node in subprocess_run_calls:
            keyword_names = [kw.arg for kw in call_node.keywords]
            assert "timeout" in keyword_names, f"subprocess.run à la ligne {call_node.lineno} n'a pas de timeout !"

    # ═══════════════════════════════════════════════════════════
    # STANDARD 4 : LOGS CONTEXTUELS EXTRA={...} & LOGGER ADAPTER
    # ═══════════════════════════════════════════════════════════

    def test_mloop_formatter_serializes_extra_fields(self):
        """Vérifie que MLoopFormatter formate et injecte automatiquement les champs extra={...}."""
        formatter = MLoopFormatter(debug_mode=False)
        record = logging.LogRecord(
            name="mloop.test",
            level=logging.INFO,
            pathname=__file__,
            lineno=100,
            msg="Opération terminée",
            args=(),
            exc_info=None,
        )
        record.__dict__["project"] = "BoireFrere"
        record.__dict__["story_id"] = "REC-015"
        record.__dict__["duration_ms"] = 125

        formatted = formatter.format(record)
        assert "INFO [mloop.test] Opération terminée" in formatted
        assert "duration_ms=125" in formatted
        assert "project=BoireFrere" in formatted
        assert "story_id=REC-015" in formatted

    def test_mloop_logger_adapter_binds_context(self):
        """Vérifie que MLoopLoggerAdapter attache le contexte automatiquement."""
        logger = get_logger("test_comp", project="MyProject", story="STORY-1")
        assert isinstance(logger, MLoopLoggerAdapter)
        msg, kwargs = logger.process("Log message", {"extra": {"run_id": "r-9"}})
        assert kwargs["extra"]["project"] == "MyProject"
        assert kwargs["extra"]["story"] == "STORY-1"
        assert kwargs["extra"]["run_id"] == "r-9"

    # ═══════════════════════════════════════════════════════════
    # STANDARD 5 : TESTS DU CONTRAT D'ÉCHEC PARAMÉTRÉS
    # ═══════════════════════════════════════════════════════════

    @pytest.mark.parametrize("invalid_trace", ["", "   ", "   \n\t  "])
    def test_search_rho_solution_handles_empty_inputs(self, invalid_trace):
        """Vérifie que search_rho_solution gère proprement les entrées vides sans crash."""
        res = search_rho_solution(invalid_trace)
        assert res == []

    @pytest.mark.parametrize("bad_threshold", [-1.0, 0.0, 1.5])
    def test_search_rho_solution_handles_edge_thresholds(self, bad_threshold):
        """Vérifie la robustesse aux seuils limites."""
        res = search_rho_solution("Trace erreur quelconque", threshold=bad_threshold)
        assert isinstance(res, list)

    # ═══════════════════════════════════════════════════════════
    # STANDARD 1 & 2 : ASYNCLLMCLIENT CONTEXT MANAGER & INJECTION
    # ═══════════════════════════════════════════════════════════

    @pytest.mark.asyncio
    async def test_async_llm_client_context_manager_and_aclose(self):
        """Vérifie le protocole async with et la fermeture propre de AsyncLLMClient."""
        from src.core.llm_client import AsyncLLMClient

        async with AsyncLLMClient(enable_cache=False) as client:
            assert client is not None
            assert hasattr(client, "aclose")
        # En sortie de bloc, aclose a été exécuté

    def test_async_llm_client_allows_dependency_injection(self):
        """Vérifie que AsyncLLMClient accepte un client et un cache injectés."""
        from src.core.llm_client import AsyncLLMClient

        mock_openai = object()
        mock_cache = object()
        client = AsyncLLMClient(openai_client=mock_openai, cache=mock_cache)
        assert client._openai_client is mock_openai
        assert client.cache is mock_cache

    # ═══════════════════════════════════════════════════════════
    # STANDARD 7 : DÉPRÉCIATION EXPLICITE (STACKLEVEL=2)
    # ═══════════════════════════════════════════════════════════

    def test_get_observation_conn_emits_deprecation_warning(self):
        """Vérifie que _get_observation_conn émet un DeprecationWarning formel."""
        with pytest.deprecated_call():
            conn = _get_observation_conn()
            conn.close()

