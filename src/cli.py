import sys
from typing import Any, Optional
from rich.console import Console
from rich.theme import Theme

from src.utils.logger import get_logger

from src.utils.logger import get_logger

logger = get_logger("cli")

# Premium, modern, low-noise dark palette
custom_theme = Theme(
    {
        "info": "dim white",
        "success": "bold #8ce8a2",
        "warning": "bold #ffcb6b",
        "error": "bold #ff5370",
        "highlight": "#80cbc4",
        "section": "bold #89ddff",
        "system1": "#c792ea",
        "system2": "#82b1ff",
        "subtle": "gray50",
    }
)

console = Console(theme=custom_theme, highlight=False)


class ZeroFluffConsole:
    """
    Console logger following the strict Zero-Fluff principle.
    Only prints high-signal text, avoiding ascii art and noisy animations.
    """

    @staticmethod
    def _clean(text: str) -> str:
        if not isinstance(text, str):
            return str(text)
        try:
            text.encode("cp1252")
            return text
        except UnicodeEncodeError:
            return text.encode("cp1252", errors="ignore").decode("cp1252")

    @staticmethod
    def info(msg: str) -> None:
        console.print(f"[subtle](i)[/subtle] [info]{ZeroFluffConsole._clean(msg)}[/info]")

    @staticmethod
    def success(msg: str) -> None:
        console.print(f"[success][v][/success] [info]{ZeroFluffConsole._clean(msg)}[/info]")

    @staticmethod
    def warning(msg: str) -> None:
        console.print(f"[warning][!][/warning] [info]{ZeroFluffConsole._clean(msg)}[/info]")

    @staticmethod
    def error(msg: str) -> None:
        console.print(f"[error][x][/error] [error]{ZeroFluffConsole._clean(msg)}[/error]")

    @staticmethod
    def section(title: str) -> None:
        console.print()
        console.print(f"[section]=== {ZeroFluffConsole._clean(title).upper()} ===[/section]")

    @staticmethod
    def step_s1(agent_name: str, action: str) -> None:
        console.print(
            f"  [system1]* [S1] {ZeroFluffConsole._clean(agent_name)}:[/system1] [info]{ZeroFluffConsole._clean(action)}[/info]"
        )
        try:
            from src.utils.event_logger import get_event_logger

            get_event_logger().log_event("STEP_S1", agent_name, {"action": action})
        except Exception:
            logger.debug(
                "Échec de l'émission de l'événement STEP_S1 (non-bloquant).",
                extra={"agent": agent_name, "phase": "event_log"},
                exc_info=True,
            )

    @staticmethod
    def step_s2(agent_name: str, action: str) -> None:
        console.print(
            f"  [system2]o [S2] {ZeroFluffConsole._clean(agent_name)}:[/system2] [info]{ZeroFluffConsole._clean(action)}[/info]"
        )
        try:
            from src.utils.event_logger import get_event_logger

            get_event_logger().log_event("STEP_S2", agent_name, {"action": action})
        except Exception:
            logger.debug(
                "Échec de l'émission de l'événement STEP_S2 (non-bloquant).",
                extra={"agent": agent_name, "phase": "event_log"},
                exc_info=True,
            )

    @staticmethod
    def value(label: str, val: Any) -> None:
        console.print(
            f"    [subtle]->[/subtle] [highlight]{ZeroFluffConsole._clean(label)}:[/highlight] [info]{ZeroFluffConsole._clean(str(val))}[/info]"
        )

    @staticmethod
    def prompt_input(question: str) -> str:
        console.print()
        console.print(
            f"[section]?[/section] [bold white]{ZeroFluffConsole._clean(question)}[/bold white]"
        )
        sys.stdout.write("  [highlight]> [/highlight]")
        sys.stdout.flush()
        val = sys.stdin.readline().strip()
        return val


class LoggingConsole:
    """
    Wrapper d'instrumentation autour de ZeroFluffConsole (MLOOP-140-BE / ADR-0369).

    Double chaque sortie de haute criticité affichée à l'utilisateur d'une trace
    persistante dans les journaux rotatifs (`errors.log` / `mloop.log`) avec
    contexte structuré, sans modifier ni monkeypatcher ZeroFluffConsole.

    L'affichage console reste strictement identique à ZeroFluffConsole ; seule
    la persistance journalisée est ajoutée en parallèle.
    """

    @staticmethod
    def _context(command: Any = None, project: Any = None, phase: Any = None, **extra: Any) -> dict:
        ctx = {"command": command, "project": project, "phase": phase}
        ctx.update(extra)
        return ctx

    @staticmethod
    def info(
        msg: str, command: Any = None, project: Any = None, phase: Any = None, **extra: Any
    ) -> None:
        ZeroFluffConsole.info(msg)
        logger.info(msg, extra=LoggingConsole._context(command, project, phase, **extra))

    @staticmethod
    def success(
        msg: str, command: Any = None, project: Any = None, phase: Any = None, **extra: Any
    ) -> None:
        ZeroFluffConsole.success(msg)
        logger.info(msg, extra=LoggingConsole._context(command, project, phase, **extra))

    @staticmethod
    def warning(
        msg: str, command: Any = None, project: Any = None, phase: Any = None, **extra: Any
    ) -> None:
        ZeroFluffConsole.warning(msg)
        logger.warning(msg, extra=LoggingConsole._context(command, project, phase, **extra))

    @staticmethod
    def error(
        msg: str,
        command: Any = None,
        project: Any = None,
        phase: Any = None,
        exc_info: bool = False,
        **extra: Any,
    ) -> None:
        ZeroFluffConsole.error(msg)
        logger.error(
            msg,
            extra=LoggingConsole._context(command, project, phase, **extra),
            exc_info=exc_info,
        )
