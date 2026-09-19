"""
Banc d'épreuves déterministes pytest pour la Normalisation OpenInference / OTel GenAI (MLOOP-072-BE / ADR-0380).
Couvre l'intégralité des 4 Piliers Gherkin de MLOOP-072-BE :
- Pilier 1 : Nominal (Émission de span TOOL normalisé avec trace_id, span_id, gen_ai.agent.name)
- Pilier 2 : Exceptions (Repli automatique des types inconnus vers CHAIN)
- Pilier 3 : Résilience (Concurrence multi-threads, gestion des lignes corrompues)
- Pilier 4 : UX / Observabilité (Requêtage et filtrage local query_events antéchronologique)
"""
from __future__ import annotations

import json
import tempfile
import threading
from pathlib import Path
import pytest

from src.utils.event_logger import EventLogger, get_event_logger


# ─── PILIER 1 : CHEMIN NOMINAL (Happy Path & Attributs Conformes) ─────────────

def test_event_logger_nominal_tool_span():
    """Émission d'un span TOOL conforme à la taxonomie OpenInference et OTel GenAI."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        logger = EventLogger(project_name="TestProject", base_dir=tmp_path)

        payload = logger.log_event(
            span_kind="TOOL",
            agent_id="Sentinel",
            details={"tool_name": "boundary_wrapper", "status": "success"},
            model="gemini-2.5-pro",
            tokens={"input": 120, "output": 45, "total": 165},
        )

        assert payload["openinference.span.kind"] == "TOOL"
        assert payload["gen_ai.agent.name"] == "Sentinel"
        assert payload["gen_ai.system"] == "mloop"
        assert payload["gen_ai.request.model"] == "gemini-2.5-pro"
        assert payload["gen_ai.usage.input_tokens"] == 120
        assert payload["gen_ai.usage.output_tokens"] == 45
        assert payload["gen_ai.usage.total_tokens"] == 165
        assert len(payload["trace_id"]) == 32
        assert len(payload["span_id"]) == 16
        assert "timestamp" in payload

        # Vérifier le fichier JSONL persisté
        log_file = tmp_path / "Projects" / "TestProject" / "memory" / "events.jsonl"
        assert log_file.exists()
        lines = [json.loads(line) for line in log_file.read_text(encoding="utf-8").splitlines() if line.strip()]
        assert len(lines) == 1
        assert lines[0]["openinference.span.kind"] == "TOOL"


def test_event_logger_trace_context_propagation():
    """Vérification de la propagation du parent_span_id lors de spans imbriqués."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        logger = EventLogger(project_name="TestProject", base_dir=tmp_path)

        parent = logger.log_event(span_kind="AGENT", agent_id="Orchestrator", details={"intent": "plan"})
        child = logger.log_event(
            span_kind="TOOL",
            agent_id="Worker",
            details={"tool": "write"},
            parent_span_id=parent["span_id"],
            trace_id=parent["trace_id"],
        )

        assert child["trace_id"] == parent["trace_id"]
        assert child["parent_span_id"] == parent["span_id"]


# ─── PILIER 2 : EXCEPTIONS & REJETS MÉTIER (Repli Résilient) ─────────────────

def test_event_logger_fallback_unknown_type_to_chain():
    """Un type non répertorié est replié sur CHAIN et le type original archivé."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        logger = EventLogger(project_name="TestProject", base_dir=tmp_path)

        payload = logger.log_event(
            span_kind="circuit_breaker_tripped",
            agent_id="PingPongGuard",
            details={"cycle": 3},
        )

        assert payload["openinference.span.kind"] == "CHAIN"
        assert payload["details"]["original_event_type"] == "circuit_breaker_tripped"


def test_event_logger_mapping_legacy_tool_call():
    """Un appel avec type legacy 'tool_call' est mappé proprement sur TOOL."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        logger = EventLogger(project_name="TestProject", base_dir=tmp_path)

        payload = logger.log_event(
            span_kind="tool_call",
            agent_id="Sentinel",
            details={"tool": "ast_checker"},
        )

        assert payload["openinference.span.kind"] == "TOOL"


# ─── PILIER 3 : RÉSILIENCE TECHNIQUE & CONCURRENCE ───────────────────────────

def test_event_logger_concurrent_writes_thread_safety():
    """Écritures concurrentes massives sans corruption de structure JSON."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        logger = EventLogger(project_name="TestProject", base_dir=tmp_path)

        errors = []

        def worker(thread_idx: int):
            try:
                for i in range(25):
                    logger.log_event(
                        span_kind="TOOL",
                        agent_id=f"Worker_{thread_idx}",
                        details={"iteration": i},
                    )
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker, args=(t,)) for t in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0

        # Vérifier que toutes les 100 lignes sont des JSON valides
        log_file = tmp_path / "Projects" / "TestProject" / "memory" / "events.jsonl"
        raw_lines = [line.strip() for line in log_file.read_text(encoding="utf-8").splitlines() if line.strip()]
        assert len(raw_lines) == 100
        for line in raw_lines:
            data = json.loads(line)
            assert "openinference.span.kind" in data


def test_event_logger_resilience_corrupted_jsonl_lines():
    """query_events ignore gracieusement les lignes JSON corrompues sans planter."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        logger = EventLogger(project_name="TestProject", base_dir=tmp_path)

        log_file = tmp_path / "Projects" / "TestProject" / "memory" / "events.jsonl"
        log_file.parent.mkdir(parents=True, exist_ok=True)

        valid_line = json.dumps({
            "trace_id": "11112222333344445555666677778888",
            "span_id": "12345678abcdef00",
            "openinference.span.kind": "AGENT",
            "gen_ai.agent.name": "Orchestrator",
            "timestamp": "2026-09-19T10:00:00Z",
            "details": {},
        })
        corrupted_line = "{CORRUPTED_JSON_LINE"

        log_file.write_text(f"{valid_line}\n{corrupted_line}\n{valid_line}\n", encoding="utf-8")

        events = logger.query_events(limit=50)
        assert len(events) == 2
        assert all(e["openinference.span.kind"] == "AGENT" for e in events)


# ─── PILIER 4 : UX / OBSERVABILITÉ & FILTRAGE ─────────────────────────────────

def test_event_logger_query_filtering_and_reverse_order():
    """query_events filtre par span_kind et renvoie les événements antéchronologiques."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        logger = EventLogger(project_name="TestProject", base_dir=tmp_path)

        logger.log_event(span_kind="AGENT", agent_id="Orchestrator", details={"step": 1})
        logger.log_event(span_kind="TOOL", agent_id="Worker", details={"step": 2})
        logger.log_event(span_kind="AGENT", agent_id="Sentinel", details={"step": 3})

        agent_spans = logger.query_events(filter_kind="AGENT")
        assert len(agent_spans) == 2
        # Antéchronologique : Sentinel (step 3) puis Orchestrator (step 1)
        assert agent_spans[0]["gen_ai.agent.name"] == "Sentinel"
        assert agent_spans[1]["gen_ai.agent.name"] == "Orchestrator"

        tool_spans = logger.query_events(filter_kind="TOOL")
        assert len(tool_spans) == 1
        assert tool_spans[0]["gen_ai.agent.name"] == "Worker"
