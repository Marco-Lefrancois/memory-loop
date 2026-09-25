"""
src/pipelines/bridge_certifier/_bc_subprocess.py — Contrôle du transport stdio
réel du pont (MLOOP-215-FULL), niveau 2 intégration.

Micro-grill 215-Q2, niveau 2 : le pont est **réellement lancé en processus
fils**, avec entrée/sortie par tuyaux (``PIPE``), un délai explicite sur chaque
attente (ADR-0369 *Zero-Unbounded-Wait*) et une transcription écrite dans un
fichier unique dérivé d'un répertoire de travail dédié — jamais un ``.log``
partagé entre exécutions, jamais d'interpréteur ``wsl``.

Le contrôle vérifie aussi son propre contrat de délai : une attente bornée doit
réellement lever ``TimeoutExpired`` et réclamer le fils, sinon le harnais
afficherait un vert pendant qu'un pont bloqué tiendrait le port.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Any

from src.pipelines.bridge_certifier._bc_checks import Checks, guard
from src.pipelines.bridge_certifier._bc_models import LEVEL_INTEGRATION

GUARD_LAUNCHER = "from src.bridges.mcp_resilience_guard import main; main()"
DEADLINE_PROBE_SECONDS = 1.0
DEADLINE_PROBE_SLEEP_SECONDS = 30.0
DEADLINE_UPPER_BOUND_SECONDS = 10.0
INITIALIZE_FRAME = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {"protocolVersion": "2026-07-28", "capabilities": {}},
}


def _child_command() -> list[str]:
    return [sys.executable, "-c", GUARD_LAUNCHER]


def control_transport(
    checks: Checks,
    *,
    repo_root: Path,
    work_dir: Path,
    timeout_s: float = 60.0,
) -> None:
    """``N2-TRANSPORT-STDIO`` — échange réel borné + probe du contrat de délai."""
    transcript = work_dir / f"bridge_stdio_{time.monotonic_ns()}_{uuid.uuid4().hex[:8]}.log"
    checks.capture("transcript", transcript.name)

    payload = json.dumps(INITIALIZE_FRAME, ensure_ascii=False) + "\n"
    started = time.monotonic()
    try:
        proc = subprocess.run(  # noqa: S603 — commande interne, pas d'entrée externe
            _child_command(),
            input=payload,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=str(repo_root),
            timeout=timeout_s,
        )
    except subprocess.TimeoutExpired:
        checks.failures.append(
            f"le pont n'a pas répondu en {timeout_s}s : délai explicite dépassé "
            "(le fils a été réclamé par subprocess, aucun orphelin laissé)"
        )
        return
    except OSError as exc:
        checks.failures.append(f"lancement du pont impossible : {exc}")
        return
    elapsed = round(time.monotonic() - started, 3)
    checks.capture("exchange_elapsed_s", elapsed)

    transcript.write_text(
        f"# entrée\n{payload}# sortie\n{proc.stdout or ''}\n# erreurs\n{proc.stderr or ''}\n",
        encoding="utf-8",
    )
    checks.expect(transcript.is_file(), "la transcription unique n'a pas été écrite")

    checks.expect(
        proc.returncode == 0,
        f"le pont a terminé en code {proc.returncode} (stderr : {(proc.stderr or '')[:200]!r})",
    )
    lines = [line for line in (proc.stdout or "").splitlines() if line.strip()]
    checks.capture("responses", len(lines))
    if not checks.expect(len(lines) == 1, f"{len(lines)} réponse(s) rendue(s) pour 1 trame"):
        return
    response = json.loads(lines[0])
    routing = ((response.get("result") or {}).get("_meta") or {}).get("routing") or {}
    checks.expect(
        routing.get("protocolVersion") == "2026-07-28",
        f"_meta.routing non lié sur le transport réel (reçu {routing!r})",
    )
    checks.expect(
        routing.get("method") == "initialize",
        f"_meta.routing.method erroné sur le transport réel (reçu {routing!r})",
    )
    checks.expect(
        "MCP-Protocol-Version" not in (proc.stdout or ""),
        "un en-tête HTTP de version a été émis sur un transport stdio réel",
    )

    # (b) Contrat de délai : l'attente bornée doit réellement se déclencher.
    probe_started = time.monotonic()
    try:
        subprocess.run(  # noqa: S603 — probe interne bornée
            [sys.executable, "-c", f"import time; time.sleep({DEADLINE_PROBE_SLEEP_SECONDS})"],
            capture_output=True,
            timeout=DEADLINE_PROBE_SECONDS,
            cwd=str(repo_root),
        )
    except subprocess.TimeoutExpired:
        probe_elapsed = round(time.monotonic() - probe_started, 3)
        checks.capture("deadline_probe_elapsed_s", probe_elapsed)
        checks.expect(
            probe_elapsed < DEADLINE_UPPER_BOUND_SECONDS,
            f"le délai n'a pas été honoré : {probe_elapsed}s écoulées pour "
            f"{DEADLINE_PROBE_SECONDS}s demandés",
        )
    else:
        checks.failures.append(
            "aucune TimeoutExpired levée : le fils endormi n'a pas été réclamé "
            "dans le délai — contrat ADR-0369 non démontré"
        )


def run_transport_controls(
    *, repo_root: Path, work_dir: Path, timeout_s: float = 60.0
) -> list[Any]:
    """Contrôle unique du périmètre transport (niveau 2)."""
    return [
        guard(
            "N2-TRANSPORT-STDIO",
            "Processus fils réel : tuyaux bornés, transcription unique, délai explicite",
            control_transport,
            level=LEVEL_INTEGRATION,
            repo_root=repo_root,
            work_dir=work_dir,
            timeout_s=timeout_s,
        ),
    ]
