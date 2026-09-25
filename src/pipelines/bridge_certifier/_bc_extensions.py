"""
src/pipelines/bridge_certifier/_bc_extensions.py — Contrôles de certification
des extensions officielles du pont MCP (MLOOP-215-FULL), niveau 1 in-process.

Trois contrôles, un par extension de la spécification MCP 2026-07-28 :

- ``N1-ELICITATION-FORM`` : annonce de l'extension Form Mode et routage de
  ``elicitation/create`` (une absence de routage est un refus silencieux) ;
- ``N1-COMPETENCES-SKILLS`` : pont à double pile ``skills/list`` (voie moderne
  déclarée, repli historique sinon) ;
- ``N1-TACHES-ASYNC`` : cycle ``tasks/create | status | cancel | result``.

Le troisième contrôle n'est pas « décoratif » : les primitives `tasks/*` de
MLOOP-211-BE sont un prérequis contractuel de 215. Leur absence se traduit par
un ``FAIL`` explicite nommant le récit en cause, jamais par un test sauté.
"""

from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Mapping
from unittest.mock import patch

from src.bridges import mcp_skills
from src.bridges._mcp_elicitation import ELICITATION_EXTENSION_ID, ELICITATION_METHOD
from src.bridges._mcp_tasks_service import TaskService
from src.core.task_handles import TaskStore
from src.core.task_spawner import HerdrLaunchHandle
from src.pipelines.bridge_certifier._bc_checks import Checks, guard
from src.pipelines.bridge_certifier._bc_memory import bridge_session, exchange
from src.pipelines.bridge_certifier._bc_models import LEVEL_IN_PROCESS

TASKS_METHODS = ("tasks/create", "tasks/status", "tasks/cancel", "tasks/result")

_Elicitation_CAPS = {
    "extensions": {ELICITATION_EXTENSION_ID: {"modes": ["form"]}},
}
_SKILLS_CAPS = {"extensions": {mcp_skills.SKILLS_EXTENSION_ID: {}}}


def _error_code(response: Any) -> Any:
    error = (response or {}).get("error") if isinstance(response, dict) else None
    return error.get("code") if isinstance(error, dict) else None


def _initialize(caps: Mapping[str, Any]) -> Any:
    return exchange(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {"protocolVersion": "2026-07-28", "capabilities": dict(caps)},
        }
    )


def control_elicitation(checks: Checks) -> None:
    """``N1-ELICITATION-FORM`` — annonce serveur + routage de l'enveloppe."""
    with bridge_session():
        initialized = _initialize(_Elicitation_CAPS)
        result = (initialized or {}).get("result") or {}
        extensions = ((result.get("capabilities") or {}).get("extensions")) or {}
        checks.capture("extensions", sorted(extensions))
        checks.expect(
            ELICITATION_EXTENSION_ID in extensions,
            f"l'extension {ELICITATION_EXTENSION_ID} n'est pas annoncée par le serveur",
        )
        modes = (extensions.get(ELICITATION_EXTENSION_ID) or {}).get("modes")
        checks.expect(
            modes == ["form"],
            f"mode Form Mode non publié (reçu {modes!r}) ; le mode URL reste hors périmètre",
        )

        # Schéma fermé exigé par la règle métier (options ``enum`` obligatoires).
        request = exchange(
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": ELICITATION_METHOD,
                "params": {
                    "message": "Contrat de certification : arbitrage du PO ?",
                    "requestedSchema": {
                        "type": "object",
                        "properties": {
                            "reponse": {
                                "type": "string",
                                "description": "Arbitrage du PO",
                                "enum": ["accepte", "rejete"],
                            }
                        },
                        "required": ["reponse"],
                        "additionalProperties": False,
                    },
                },
            }
        )
        code = _error_code(request)
        checks.expect(
            code != -32601,
            f"{ELICITATION_METHOD} non routée par le pont (-32601) : extension 213 absente",
        )
        if request is not None and request.get("result"):
            envelope = request["result"]
            checks.expect(bool(envelope.get("message")), "l'enveloppe ne porte pas de message")
            checks.expect(
                isinstance(envelope.get("requestedSchema"), dict),
                "l'enveloppe ne porte pas de requestedSchema objet",
            )
            checks.expect(
                envelope.get("mode") in (None, "form"),
                f"mode hors périmètre servi : {envelope.get('mode')!r}",
            )
            checks.capture("elicitation_mode", envelope.get("mode"))
        elif code is not None:
            checks.capture("elicitation_error", code)
            reasons = (((request or {}).get("error") or {}).get("data") or {}).get("reasons")
            checks.expect(
                False,
                f"échange d'élicitation refusé en {code} pour un schéma fermé "
                f"(motifs : {reasons!r})",
            )


def control_skills(checks: Checks) -> None:
    """``N1-COMPETENCES-SKILLS`` — pont à double pile, deux voies certifiées."""
    with bridge_session():
        mcp_skills.note_client_capabilities({})
        legacy = exchange({"jsonrpc": "2.0", "id": 3, "method": "skills/list", "params": {}})
        legacy_entries = ((legacy or {}).get("result") or {}).get("skills")
        checks.expect(
            isinstance(legacy_entries, list),
            f"voie historique : réponse invalide ({json.dumps(legacy, ensure_ascii=False)[:160]!r})",
        )
        checks.expect(
            bool(legacy_entries),
            "voie historique : aucune compétence servie depuis .agents/skills",
        )
        checks.capture("legacy_skills", len(legacy_entries or []))

        mcp_skills.note_client_capabilities(_SKILLS_CAPS)
        checks.expect(
            mcp_skills.client_supports_skills() is True,
            "la déclaration de l'extension io.modelcontextprotocol/skills est ignorée",
        )
        modern = exchange({"jsonrpc": "2.0", "id": 4, "method": "skills/list", "params": {}})
        modern_entries = ((modern or {}).get("result") or {}).get("skills")
        checks.expect(
            isinstance(modern_entries, list),
            f"voie moderne : réponse invalide ({json.dumps(modern, ensure_ascii=False)[:160]!r})",
        )
        checks.capture("modern_skills", len(modern_entries or []))

        missing = exchange(
            {
                "jsonrpc": "2.0",
                "id": 5,
                "method": "skills/get",
                "params": {"uri": "skill://router/SKILL.md"},
            }
        )
        checks.expect(
            (missing or {}).get("result") is not None,
            f"skills/get n'a pas servi router (code {_error_code(missing)!r})",
        )


class _CertSpawner:
    """Lanceur de certification : poignée réelle mais sans thread — ``arm()`` et
    ``terminate()`` deviennent des no-op, aucun compagnon n'est jamais engagé."""

    def launch(self, record: Any, execution: Mapping[str, Any]) -> HerdrLaunchHandle:
        return HerdrLaunchHandle(
            task_id=record.task_id,
            subprocess_id=record.subprocess_id or record.task_id,
            on_failure=lambda task_id, cause: None,
            on_event=lambda task_id, message: None,
        )


def control_tasks(checks: Checks) -> None:
    """``N1-TACHES-ASYNC`` — cycle asynchrone des primitive ``tasks/*``."""
    # Certification isolée : store temporaire + lanceur factice. Un contrôle ne
    # doit ni engager de compagnon physique ni écrire dans le projet réel (le
    # spawn réel est couvert par la suite de MLOOP-211-BE).
    with TemporaryDirectory(prefix="mloop_cert_tasks_") as tmp:
        service = TaskService(
            store=TaskStore("mLoop", base_dir=Path(tmp) / "Projects"),
            spawner=_CertSpawner(),
        )
        with bridge_session(), patch("src.bridges._mcp_tasks.get_service", return_value=service):
            created = exchange(
                {
                    "jsonrpc": "2.0",
                    "id": 6,
                    "method": "tasks/create",
                    "params": {"story_id": "MLOOP-215-FULL", "command": "worker-spawn"},
                }
            )
            result = (created or {}).get("result")
            checks.expect(
                isinstance(result, dict) and result.get("task_id") is not None,
                "tasks/create ne renvoie pas de tâche identifiable "
                f"(code {_error_code(created)!r}) — primitives tasks/* de MLOOP-211-BE absentes",
            )
            task_id = (result or {}).get("task_id") if isinstance(result, dict) else None

            # Ordre contractuel : avancement sur tâche vivante, désistement
            # (transition terminal + échéance), puis verdict sur tâche terminée.
            for index, (method, params) in enumerate(
                (
                    ("tasks/status", {"task_id": task_id}),
                    ("tasks/cancel", {"task_id": task_id}),
                    ("tasks/result", {"task_id": task_id}),
                ),
                start=7,
            ):
                response = exchange(
                    {"jsonrpc": "2.0", "id": index, "method": method, "params": params}
                )
                checks.expect(
                    response is not None and response.get("result") is not None,
                    f"{method} non servi (code {_error_code(response)!r})",
                )
            checks.capture("tasks_create_result", result)


def run_extension_controls() -> list[Any]:
    """Enchaîne les contrôles des extensions officielles (niveau 1)."""
    return [
        guard(
            "N1-ELICITATION-FORM",
            "Élicitation Form Mode : annonce serveur et routage de l'enveloppe",
            control_elicitation,
            level=LEVEL_IN_PROCESS,
        ),
        guard(
            "N1-COMPETENCES-SKILLS",
            "Compétences SEP-2640 : voie moderne et repli historique",
            control_skills,
            level=LEVEL_IN_PROCESS,
        ),
        guard(
            "N1-TACHES-ASYNC",
            "Cycle tasks/create · status · result · cancel (prérequis MLOOP-211-BE)",
            control_tasks,
            level=LEVEL_IN_PROCESS,
        ),
    ]
