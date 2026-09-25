"""
src/pipelines/bridge_certifier/_bc_degrade.py — Contrôle de dégradation
gracieuse des ponts MCP (MLOOP-215-FULL), niveau 1 in-process.

Le contrat de repli se déclenche sur une **capacité de protocole absente**, et
jamais sur l'identité de l'éditeur de l'hôte : un client hérité sans en-tête,
un hôte sans l'extension MCP Apps et un hôte avec l'extension produisent tous
trois une réponse lisible — jamais ``isError``, jamais un rejet silencieux.

Le volet « trois IDE supportés » est certifié ici au **niveau lexical**
(Échelle de preuve ADR-0385) : absence d'identifiant d'éditeur dans le code des
ponts. Ce n'est pas une preuve structurelle de non-dérive, et le rapport le
déclare explicitement dans ``details.evidence_level`` plutôt que d'afficher un
vert sur une simple recherche de chaîne.
"""

from __future__ import annotations

import re
from typing import Any

from src.bridges import mcp_ui
from src.bridges._mcp_protocol_core import HEADER_PROTOCOL_VERSION, HEADER_METHOD
from src.bridges._mcp_protocol_routing import route_from_headers
from src.pipelines.bridge_certifier._bc_checks import Checks, guard
from src.pipelines.bridge_certifier._bc_memory import bridge_session
from src.pipelines.bridge_certifier._bc_models import LEVEL_IN_PROCESS

# Identifiants d'éditeur susceptiibles de trahir une dégradation branchée sur
# l'IDE plutôt que sur la capacité de protocole (recherche lexicale bornée).
IDE_MARKERS = ("vscode", "jetbrains", "intellij", "windsurf", "trae", "codeoss")
LOCAL_URL_HINT = "http://localhost"

_UI_CAPS = {
    "extensions": {
        mcp_ui.UI_EXTENSION_ID: {"mimeTypes": [mcp_ui.UI_APP_MIME_TYPE]},
    }
}


def _call_tool(name: str, arguments: dict[str, Any] | None = None) -> Any:
    from src.bridges import mcp_loop_mem as lm  # import différé (anti-circularité)

    response, _project = lm.handle_tools_call(
        900, {"name": name, "arguments": arguments or {}}, None
    )
    return response


def _text(response: Any) -> str:
    content = ((response or {}).get("result") or {}).get("content") or []
    if not content:
        return ""
    return str((content[0] or {}).get("text") or "")


def control_degradation(checks: Checks) -> None:
    """``N1-DEGRADATION`` — repli sur capacité absente, contractuellement identique."""
    with bridge_session():
        # (a) Un client sans en-tête de version n'est jamais rejeté.
        without_headers = route_from_headers({})
        checks.expect(
            without_headers.accepted is True,
            "un client sans en-tête de version a été rejeté (absence ≠ rejet)",
        )
        checks.expect(
            without_headers.header_present is False,
            "l'absence d'en-tête n'est pas reconnue comme client hérité",
        )
        checks.capture("header_present_legacy", without_headers.header_present)

        # (b) Une version hors registre reste un refus dur, en-tête compris.
        unknown = route_from_headers(
            {
                HEADER_PROTOCOL_VERSION: "1999-01-01",
                HEADER_METHOD: "tools/list",
            }
        )
        checks.expect(
            unknown.accepted is False,
            "une version hors registre a été acceptée par la couche de routage",
        )

        # (c) Hôte sans l'extension MCP Apps : repli local lisible, jamais isError.
        mcp_ui.reset_ui_state()
        fallback = _call_tool("show_architecture")
        checks.expect(
            "isError" not in (fallback.get("result") or {}),
            "le repli UI a retourné isError au lieu d'un texte local",
        )
        checks.expect(
            LOCAL_URL_HINT in _text(fallback),
            f"le repli UI ne publie pas d'adresse locale (texte : {_text(fallback)[:120]!r})",
        )
        same = _call_tool("show_architecture")
        checks.expect(
            _text(same) == _text(fallback),
            "le repli UI n'est pas déterministe à capacité constante",
        )
        checks.capture("fallback_text", _text(fallback)[:200])

        # (d) Hôte avec l'extension : liaison outil → ressource, texte nominal.
        mcp_ui.note_client_capabilities(_UI_CAPS)
        checks.expect(
            mcp_ui.client_supports_ui() is True,
            "la capacité MCP Apps n'est pas reconnue malgré le mime type requis",
        )
        declared = _call_tool("show_database_schema")
        result = declared.get("result") or {}
        checks.expect(
            "isError" not in result,
            "la voie nominale UI a retourné isError",
        )
        checks.expect(
            "resourceUri" in str(result.get("_meta") or {}),
            f"_meta.ui.resourceUri absent de la voie nominale ({result.get('_meta')!r})",
        )
        checks.expect(
            LOCAL_URL_HINT not in _text(declared),
            "la voie nominale a basculé sur le repli local alors que la capacité est négociée",
        )


def control_ide_neutrality(checks: Checks) -> None:
    """``N1-IDE-NEUTRE`` — absence d'identifiant d'éditeur dans les ponts (niveau 1)."""
    from pathlib import Path

    hits: list[str] = []
    scanned = 0
    for path in sorted(Path("src/bridges").rglob("*.py")):
        scanned += 1
        try:
            source = path.read_text(encoding="utf-8", errors="replace").lower()
        except OSError as exc:
            checks.failures.append(f"{path} illisible : {exc}")
            continue
        for marker in IDE_MARKERS:
            if re.search(rf"\b{re.escape(marker)}\b", source):
                hits.append(f"{path.name}:{marker}")
    checks.capture("modules_scanned", scanned)
    checks.capture("evidence_level", "lexical (niveau 1) — non structurel")
    checks.expect(
        not hits,
        f"identifiant(s) d'éditeur trouvé(s) dans les ponts {hits!r} : "
        "dégradation potentiellement branchée sur l'IDE et non sur la capacité",
    )
    checks.expect(scanned > 0, "aucun module de pont analysé")


def run_degradation_controls() -> list[Any]:
    """Enchaîne les contrôles de dégradation gracieuse (niveau 1)."""
    return [
        guard(
            "N1-DEGRADATION",
            "Repli sur capacité absente : en-tête, texte local, liaison outil → ressource",
            control_degradation,
            level=LEVEL_IN_PROCESS,
        ),
        guard(
            "N1-IDE-NEUTRE",
            "Contrôles identiques pour les 3 IDE supportés (recherche lexicale bornée)",
            control_ide_neutrality,
            level=LEVEL_IN_PROCESS,
        ),
    ]
