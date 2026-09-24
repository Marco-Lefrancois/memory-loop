"""
Grill Engine - mLoop (Shim de Rétrocompatibilité ADR-0202)
Ce module redirige vers le package modulaire src.pipelines.grill (ADR-012).
"""

from src.pipelines.grill import (
    EMERGENCY_FALLBACK_TEMPLATE,
    GrillEngine,
    UNGRILLABLE_KEYWORDS,
    check_context_health,
    detect_ungrillable_signals,
    execute_grill_cli,
    format_frontier_round,
    get_next_adr_id,
    promote_prototype,
    render_adr_content,
    resolve_adr_template,
    stage_prototype,
    write_adr_file,
)

# Alias de rétrocompatibilité pour ADR_TEMPLATE
ADR_TEMPLATE = EMERGENCY_FALLBACK_TEMPLATE

__all__ = [
    "GrillEngine",
    "resolve_adr_template",
    "get_next_adr_id",
    "render_adr_content",
    "write_adr_file",
    "detect_ungrillable_signals",
    "format_frontier_round",
    "check_context_health",
    "UNGRILLABLE_KEYWORDS",
    "EMERGENCY_FALLBACK_TEMPLATE",
    "ADR_TEMPLATE",
]
