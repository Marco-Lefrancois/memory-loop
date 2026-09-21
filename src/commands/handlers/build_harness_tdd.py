"""
Handler TDD Enforcer — protocole Red-Green (ADR-0381 / EPIC-8).

Extrait de `build_harness.py` (découpage ADR-0202) pour maintenir chaque module
sous le plafond de 300 lignes. Consommé via la façade `build_harness.py`.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

from src.cli import ZeroFluffConsole, LoggingConsole

if TYPE_CHECKING:
    from src.state import LoopState


def _log_err(command: str, msg: str, args: Any = None, **ctx: Any) -> None:
    """Route une erreur handler vers LoggingConsole.error avec contexte standardise (MLOOP-142-BE)."""
    LoggingConsole.error(msg, command=command, project=getattr(args, "project", None), **ctx)


def handle_tdd_enforce(
    args: argparse.Namespace,
    state: Optional[LoopState] = None,
    project_path: Optional[Path] = None,
) -> int:
    """Commande d'enforcement et de traçabilité du cycle TDD Red-Green (ADR-0381)."""
    from src.core.tdd_enforcer import (
        TddEnforcer,
        MissingRedSnapshotError,
        UnexpectedPassingTestError,
        TestFailureError,
        AstViolationError,
    )

    phase = getattr(args, "phase", None)
    story_id = getattr(args, "story", None)
    test_arg = getattr(args, "test_file", None)
    source_arg = getattr(args, "source_file", None)

    if not phase or not story_id:
        _log_err(
            "tdd-enforce",
            "Arguments obligatoires : --phase [red|green|verify] et --story <ID>.",
            args,
            story_id=story_id,
            phase=phase,
        )
        return 1

    target_proj = getattr(args, "project", None) or os.getenv("MLOOP_ACTIVE_PROJECT", "mLoop")
    if project_path:
        base_dir = project_path
    elif (Path("Projects") / target_proj).exists():
        base_dir = Path("Projects") / target_proj
    else:
        base_dir = Path(".")

    evidence_file = base_dir / "memory" / "evidence" / f"{story_id}_evidence.json"
    fallback = Path("Projects") / "mLoop" / "memory" / "evidence" / f"{story_id}_evidence.json"
    if not evidence_file.exists() and fallback.exists():
        evidence_file = fallback

    enforcer = TddEnforcer()

    try:
        if phase == "red":
            if not test_arg:
                story_slug = story_id.lower().replace("-", "_")
                candidates = list(Path("tests").glob(f"*{story_slug}*.py"))
                if not candidates:
                    _log_err(
                        "tdd-enforce",
                        f"Spécifier --test-file pour la phase RED de {story_id}.",
                        args,
                        story_id=story_id,
                        phase="red",
                    )
                    return 1
                test_file = candidates[0]
            else:
                test_file = Path(test_arg)

            ZeroFluffConsole.step_s1(
                "TDD Enforcer [RED]", f"Vérification de l'échec initial pour {story_id}..."
            )
            red = enforcer.record_red(story_id, test_file, evidence_file)
            ZeroFluffConsole.info(
                f"Sceau RED validé : exit_code={red.exit_code} | SHA-256={red.test_sha256[:12]}..."
            )
            return 0

        elif phase == "green":
            if not test_arg or not source_arg:
                _log_err(
                    "tdd-enforce",
                    "La phase GREEN exige --test-file et --source-file.",
                    args,
                    story_id=story_id,
                    phase="green",
                )
                return 1

            ZeroFluffConsole.step_s1(
                "TDD Enforcer [GREEN]", f"Vérification du succès complet pour {story_id}..."
            )
            green = enforcer.record_green(story_id, Path(test_arg), Path(source_arg), evidence_file)
            ZeroFluffConsole.info(
                f"Sceau GREEN validé : exit_code={green.exit_code} | AST=OK | "
                f"SHA-256={green.source_sha256[:12]}..."
            )
            return 0

        elif phase == "verify":
            ZeroFluffConsole.step_s1(
                "TDD Enforcer [VERIFY]", f"Vérification conformité Gate 3 pour {story_id}..."
            )
            if enforcer.verify_gate_3_compliance(story_id, evidence_file):
                ZeroFluffConsole.info(
                    f"Récit {story_id} certifié TDD Red-Green. Approbation Gate 3 déverrouillée."
                )
                return 0
            _log_err(
                "tdd-enforce",
                f"Récit {story_id} non conforme TDD (couple Red/Green incomplet).",
                args,
                story_id=story_id,
                phase="verify",
            )
            return 1
        else:
            _log_err(
                "tdd-enforce",
                f"Phase inconnue : {phase} (valeurs admises : red, green, verify).",
                args,
                story_id=story_id,
                phase=phase,
            )
            return 1

    except (
        MissingRedSnapshotError,
        UnexpectedPassingTestError,
        TestFailureError,
        AstViolationError,
    ) as e:
        _log_err(
            "tdd-enforce",
            f"Violation TDD Enforcer : {e}",
            args,
            story_id=story_id,
            phase=phase,
            exc_info=True,
        )
        return 1
    except Exception as e:
        _log_err(
            "tdd-enforce",
            f"Erreur TDD Enforcer : {e}",
            args,
            story_id=story_id,
            phase=phase,
            exc_info=True,
        )
        return 1
