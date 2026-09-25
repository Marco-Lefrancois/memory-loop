"""
mLoop Grill Pipeline Package (ADR-0320 / ADR-0389 / ADR-012)
Modularisation propre du moteur d'interrogatoire Grill-with-Docs.
"""

from src.pipelines.grill._adr_writer import (
    EMERGENCY_FALLBACK_TEMPLATE,
    get_next_adr_id,
    render_adr_content,
    resolve_adr_template,
    write_adr_file,
)
from src.pipelines.grill._cli_handler import execute_grill_cli, inspect_session_health
from src.pipelines.grill._elicitation import (
    ElicitationError,
    build_standard_question,
    render_fallback_markdown,
    validate_content,
    validate_requested_schema,
)
from src.pipelines.grill._elicitation_flow import answer_elicitation, create_elicitation
from src.pipelines.grill._elicitation_registry import is_answered, read_decision_records
from src.pipelines.grill._elicitation_state import expire_due, set_task_lifecycle
from src.pipelines.grill._engine import GrillEngine
from src.pipelines.grill._frontier import (
    UNGRILLABLE_KEYWORDS,
    check_context_health,
    detect_ungrillable_signals,
    format_frontier_round,
)
from src.pipelines.grill._handoff import promote_prototype, stage_prototype

__all__ = [
    "GrillEngine",
    "resolve_adr_template",
    "get_next_adr_id",
    "render_adr_content",
    "write_adr_file",
    "detect_ungrillable_signals",
    "format_frontier_round",
    "check_context_health",
    "stage_prototype",
    "promote_prototype",
    "execute_grill_cli",
    "inspect_session_health",
    "UNGRILLABLE_KEYWORDS",
    "EMERGENCY_FALLBACK_TEMPLATE",
    # Élicitation Form Mode (MLOOP-213-BE)
    "ElicitationError",
    "answer_elicitation",
    "build_standard_question",
    "create_elicitation",
    "expire_due",
    "is_answered",
    "read_decision_records",
    "render_fallback_markdown",
    "set_task_lifecycle",
    "validate_content",
    "validate_requested_schema",
]
