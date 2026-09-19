"""
mLoop Engine - Boundary Tracing Wrapper (ADR-0380 / MLOOP-071-BE).
Interception déterministe des sorties d'outils volumineuses à la frontière d'exécution.
Déporte automatiquement vers l'OpaqueArtifactBus (>2k car. ou >30 lignes).
Conforme aux 7 Standards de Robustesse Python Senior (ADR-0369) et ADR-0202.
"""
from __future__ import annotations

import concurrent.futures
import functools
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Protocol, Tuple, Union

from src.engine.artifacts.bus import ArtifactHandle, OpaqueArtifactBus
from src.utils.logger import get_logger

logger = get_logger("boundary_wrapper")

DEFAULT_MAX_CHARS: int = 2000
DEFAULT_MAX_LINES: int = 30
DEFAULT_TIMEOUT_SECONDS: float = 30.0


class ArtifactBusProtocol(Protocol):
    """Protocole d'interface pour le bus d'artefacts déportés (ADR-0369 Standard 1)."""

    def store(
        self,
        content: str | bytes,
        summary: str = "",
        schema_type: str = "text/plain",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ArtifactHandle: ...

    def get_slice(self, handle_or_hash: str, start_line: int, end_line: int) -> str: ...

    def offload_if_exceeds(
        self,
        content: str,
        max_chars: int = 2000,
        max_lines: int = 30,
        summary: str = "",
        schema_type: str = "text/plain",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bool, str, Optional[ArtifactHandle]]: ...


class BoundaryToolTimeoutError(TimeoutError):
    """Exception levée lorsqu'un outil dépasse son délai d'exécution alloué (ADR-0369 Standard 3)."""
    pass


def offload_if_exceeds(
    output: Any,
    max_chars: int = DEFAULT_MAX_CHARS,
    max_lines: int = DEFAULT_MAX_LINES,
    bus: Optional[ArtifactBusProtocol] = None,
    tool_name: str = "tool",
    summary: str = "",
    metadata: Optional[Dict[str, Any]] = None,
) -> Tuple[str, bool]:
    """
    Évalue une sortie d'outil et la déporte vers l'OpaqueArtifactBus si elle excède les seuils.
    Retourne (texte_final, is_offloaded).
    """
    if output is None:
        return "", False

    text_output = str(output) if not isinstance(output, str) else output
    if not text_output.strip():
        return text_output, False

    lines = text_output.splitlines()
    raw_chars = len(text_output)
    line_count = len(lines)

    if raw_chars <= max_chars and line_count <= max_lines:
        logger.debug(
            "Sortie d'outil sous le seuil d'encombrement",
            extra={
                "tool": tool_name,
                "raw_chars": raw_chars,
                "line_count": line_count,
                "offloaded": False,
            },
        )
        return text_output, False

    active_bus = bus if bus is not None else OpaqueArtifactBus()
    artifact_summary = (
        summary or f"Sortie générée par {tool_name} ({raw_chars} car., {line_count} lignes)"
    )

    is_offloaded, descriptor, handle = active_bus.offload_if_exceeds(
        content=text_output,
        max_chars=max_chars,
        max_lines=max_lines,
        summary=artifact_summary,
        schema_type="text/plain",
        metadata=metadata or {"tool_name": tool_name},
    )

    if is_offloaded and handle is not None:
        tokens_saved = max(0, (raw_chars - len(descriptor)) // 4)
        logger.info(
            "Artefact déporté avec succès vers OpaqueArtifactBus",
            extra={
                "tool": tool_name,
                "sha256": handle.sha256,
                "raw_chars": raw_chars,
                "line_count": line_count,
                "tokens_saved": tokens_saved,
                "offloaded": True,
            },
        )
        # Émission d'un événement d'observabilité locale
        try:
            from src.utils.event_logger import EventLogger
            EventLogger.log_event(
                "artifact_persisted",
                {
                    "tool": tool_name,
                    "sha256": handle.sha256,
                    "handle_id": handle.handle_id,
                    "raw_chars": raw_chars,
                    "line_count": line_count,
                    "tokens_saved": tokens_saved,
                },
            )
        except Exception as e:
            logger.debug(
                "Échec non-bloquant de journalisation événementielle",
                exc_info=True,
                extra={"error": str(e)},
            )

        return descriptor, True

    return text_output, False


def get_artifact_slice(
    handle_id: str,
    start_line: int,
    end_line: int,
    bus: Optional[ArtifactBusProtocol] = None,
) -> str:
    """
    Extrait une projection fenêtrée d'un artefact sans charger tout le fichier en mémoire vive (ADR-0380).
    """
    if start_line < 1:
        raise ValueError(f"start_line doit être >= 1 (reçu : {start_line})")
    if end_line < start_line:
        raise ValueError(f"end_line ({end_line}) doit être >= start_line ({start_line})")

    active_bus = bus if bus is not None else OpaqueArtifactBus()
    return active_bus.get_slice(handle_id, start_line=start_line, end_line=end_line)


def boundary_trace(
    func: Optional[Callable[..., Any]] = None,
    *,
    max_chars: int = DEFAULT_MAX_CHARS,
    max_lines: int = DEFAULT_MAX_LINES,
    timeout_seconds: Optional[float] = DEFAULT_TIMEOUT_SECONDS,
    bus: Optional[ArtifactBusProtocol] = None,
    tool_name: Optional[str] = None,
) -> Callable[..., Any]:
    """
    Décorateur d'interception à la frontière d'exécution (Boundary Tracing - ADR-0380).
    Exécute la fonction avec timeout optionnel et déporte la sortie si volumineuse.
    """
    def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        resolved_tool_name = tool_name or getattr(fn, "__name__", "tool")

        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Exécution avec ou sans deadline (ADR-0369 Standard 3)
            if timeout_seconds is not None and timeout_seconds > 0:
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(fn, *args, **kwargs)
                    try:
                        raw_result = future.result(timeout=timeout_seconds)
                    except concurrent.futures.TimeoutError as e:
                        logger.error(
                            "Délai d'exécution d'outil dépassé à la frontière",
                            extra={"tool": resolved_tool_name, "timeout_seconds": timeout_seconds},
                        )
                        raise BoundaryToolTimeoutError(
                            f"L'outil '{resolved_tool_name}' a expiré après {timeout_seconds}s (Boundary Tracing)."
                        ) from e
            else:
                raw_result = fn(*args, **kwargs)

            processed, _ = offload_if_exceeds(
                output=raw_result,
                max_chars=max_chars,
                max_lines=max_lines,
                bus=bus,
                tool_name=resolved_tool_name,
            )
            return processed

        return wrapper

    if func is not None:
        return decorator(func)
    return decorator
