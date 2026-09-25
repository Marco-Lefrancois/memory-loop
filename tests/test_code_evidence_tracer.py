"""
Tests unitaires pour le moteur d'extraction AST et de traçabilité du code (MLOOP-331-BE).
Couvre les 4 Piliers Gherkin définis dans la spécification du récit.
"""

import pytest
from pathlib import Path
from src.pipelines.evidence_pack import CodeTraceabilityEntry
from src.engine.code_evidence_tracer import (
    CodeEvidenceTracer,
    ExtractedSymbol,
    ReconciliationReport,
    PythonAstExtractor,
)


SAMPLE_PYTHON_CODE = """
class DataWorker:
    def __init__(self, name: str):
        self.name = name

    def process_records(self, records: list) -> int:
        def _clean_item(x):
            return x.strip()
        return len([_clean_item(r) for r in records])

    async def flush_async(self) -> bool:
        return True

    def _private_internal(self) -> None:
        pass

def standalone_helper(x: int) -> int:
    return x * 2

def _module_private_util(msg: str) -> str:
    return msg.upper()
"""


def test_pilier_1_nominal_ast_symbol_extraction():
    """
    Pilier 1 : Extraction nominale complète des symboles qualifiés AST depuis un source Python.
    Vérifie les chemins canoniques chemin/fichier.py::Classe.methode et chemin/fichier.py::fonction.
    """
    tracer = CodeEvidenceTracer()
    symbols = tracer.extract_symbols_from_source(
        SAMPLE_PYTHON_CODE,
        relative_path="src/workers/data_worker.py"
    )

    symbol_paths = [s.symbol_path for s in symbols]

    # Vérifications des symboles qualifiés
    assert "src/workers/data_worker.py::DataWorker" in symbol_paths
    assert "src/workers/data_worker.py::DataWorker.__init__" in symbol_paths
    assert "src/workers/data_worker.py::DataWorker.process_records" in symbol_paths
    assert "src/workers/data_worker.py::DataWorker.flush_async" in symbol_paths
    assert "src/workers/data_worker.py::DataWorker._private_internal" in symbol_paths
    assert "src/workers/data_worker.py::standalone_helper" in symbol_paths
    assert "src/workers/data_worker.py::_module_private_util" in symbol_paths

    # Vérification des types
    flush_symbol = next(s for s in symbols if s.symbol_path == "src/workers/data_worker.py::DataWorker.flush_async")
    assert flush_symbol.symbol_type == "async_method"

    func_symbol = next(s for s in symbols if s.symbol_path == "src/workers/data_worker.py::standalone_helper")
    assert func_symbol.symbol_type == "function"
    assert not func_symbol.is_private


def test_pilier_1_nominal_reconciliation_success():
    """
    Pilier 1 : Réconciliation nominale où 100% des symboles publics modifiés sont ancrés.
    """
    tracer = CodeEvidenceTracer()
    symbols = tracer.extract_symbols_from_source(
        SAMPLE_PYTHON_CODE,
        relative_path="src/workers/data_worker.py"
    )

    matrix: list[CodeTraceabilityEntry] = [
        {
            "ast_symbol": "src/workers/data_worker.py::DataWorker",
            "requirement_ref": "RM-101",
            "gherkin_scenario": "Pilier 1 (Nominal)",
            "rationale": "Classe de traitement principale des données reçues.",
            "test_symbol": "tests/test_worker.py::test_init",
        },
        {
            "ast_symbol": "src/workers/data_worker.py::DataWorker.__init__",
            "requirement_ref": "RM-101",
            "gherkin_scenario": "Pilier 1 (Nominal)",
            "rationale": "Initialisation du travailleur avec son identifiant.",
            "test_symbol": "tests/test_worker.py::test_init",
        },
        {
            "ast_symbol": "src/workers/data_worker.py::DataWorker.process_records",
            "requirement_ref": "RM-102",
            "gherkin_scenario": "Pilier 1 (Nominal)",
            "rationale": "Traitement par lot des enregistrements métier.",
            "test_symbol": "tests/test_worker.py::test_process",
        },
        {
            "ast_symbol": "src/workers/data_worker.py::DataWorker.flush_async",
            "requirement_ref": "RM-103",
            "gherkin_scenario": "Pilier 1 (Nominal)",
            "rationale": "Purge asynchrone sécurisée du tampon mémoire.",
            "test_symbol": "tests/test_worker.py::test_flush",
        },
        {
            "ast_symbol": "src/workers/data_worker.py::standalone_helper",
            "requirement_ref": "TECH-FOUNDATION",
            "gherkin_scenario": "Pilier 3 (Résilience)",
            "rationale": "Multiplicateur de quota pour la mise à l'échelle.",
            "test_symbol": "tests/test_worker.py::test_helper",
        },
        {
            "ast_symbol": "src/workers/data_worker.py::_module_private_util",
            "requirement_ref": "INFRA",
            "gherkin_scenario": "Pilier 3 (Résilience)",
            "rationale": "Formatage interne des libellés de messages.",
            "test_symbol": "tests/test_worker.py::test_util",
        },
    ]

    report = tracer.reconcile(symbols, matrix, allow_private_implicit=True)
    assert report.is_valid is True
    assert len(report.unanchored_symbols) == 0
    assert len(report.dangling_entries) == 0
    assert report.summary["matched"] >= 6


def test_pilier_2_exception_ghost_code_detection():
    """
    Pilier 2 : Détection de code physique non justifié (Ghost Code).
    """
    tracer = CodeEvidenceTracer()
    unanchored_code = """
class PaymentGateway:
    def charge(self, amount: float):
        pass

    def secret_backdoor(self):
        # Code non audité !
        return "unanchored"
"""
    symbols = tracer.extract_symbols_from_source(
        unanchored_code,
        relative_path="src/billing/payment.py"
    )

    incomplete_matrix: list[CodeTraceabilityEntry] = [
        {
            "ast_symbol": "src/billing/payment.py::PaymentGateway",
            "requirement_ref": "RM-PAY-01",
            "gherkin_scenario": "Pilier 1",
            "rationale": "Passerelle de paiement sécurisée.",
            "test_symbol": "tests/test_payment.py::test_charge",
        },
        {
            "ast_symbol": "src/billing/payment.py::PaymentGateway.charge",
            "requirement_ref": "RM-PAY-01",
            "gherkin_scenario": "Pilier 1",
            "rationale": "Débit transactionnel d'un montant donné.",
            "test_symbol": "tests/test_payment.py::test_charge",
        },
    ]

    report = tracer.reconcile(symbols, incomplete_matrix)
    assert report.is_valid is False
    assert len(report.unanchored_symbols) == 1
    assert report.unanchored_symbols[0].symbol_path == "src/billing/payment.py::PaymentGateway.secret_backdoor"


def test_pilier_2_syntax_error_handling():
    """
    Pilier 2 : Rejet immédiat avec SyntaxError contextualisée sur code invalide.
    """
    tracer = CodeEvidenceTracer()
    invalid_code = "def broken_syntax(x\n    return x"
    with pytest.raises(SyntaxError):
        tracer.extract_symbols_from_source(invalid_code, relative_path="src/broken.py")


def test_pilier_3_resilience_nested_private_helpers():
    """
    Pilier 3 : Tolérance des sous-fonctions privées imbriquées lorsque la fonction parente est couverte.
    """
    tracer = CodeEvidenceTracer()
    code = """
def main_routine(data):
    def _inner_cleaner(x):
        return x.strip()
    return [_inner_cleaner(d) for d in data]
"""
    symbols = tracer.extract_symbols_from_source(code, relative_path="src/etl/routine.py")
    matrix: list[CodeTraceabilityEntry] = [
        {
            "ast_symbol": "src/etl/routine.py::main_routine",
            "requirement_ref": "RM-ETL-05",
            "gherkin_scenario": "Pilier 1",
            "rationale": "Nettoyage séquentiel du flux de données amont.",
            "test_symbol": "tests/test_routine.py::test_main",
        }
    ]

    report = tracer.reconcile(symbols, matrix, allow_private_implicit=True)
    assert report.is_valid is True
    assert len(report.unanchored_symbols) == 0


def test_pilier_4_observability_and_summary_report():
    """
    Pilier 4 : Génération d'un dictionnaire récapitulatif complet pour les linters et le CLI.
    """
    tracer = CodeEvidenceTracer()
    symbols = tracer.extract_symbols_from_source(
        SAMPLE_PYTHON_CODE,
        relative_path="src/workers/data_worker.py"
    )
    empty_matrix: list[CodeTraceabilityEntry] = []

    report = tracer.reconcile(symbols, empty_matrix, allow_private_implicit=False)
    summary = report.to_dict()

    assert "is_valid" in summary
    assert "summary" in summary
    assert summary["summary"]["total_extracted"] == len(symbols)
    assert summary["summary"]["unanchored"] > 0
    assert summary["summary"]["matched"] == 0
