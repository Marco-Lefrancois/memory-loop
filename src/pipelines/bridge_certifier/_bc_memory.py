"""
src/pipelines/bridge_certifier/_bc_memory.py — Contrôles de certification
**en mémoire** (niveau 1, échange in-process) des ponts MCP (MLOOP-215-FULL).

Deux boucles d'échanges distinctes sont certifiées, conformément au micro-grill
215-Q2 :

- ``N1-STDIO-ROUTAGE`` : la boucle stdio du pont injectée avec ``io.StringIO``
  sur ses flux standard (aucun processus, aucun fichier, aucun verrou) — c'est
  le transport réel, exécuté en mémoire ;
- ``N1-RESSOURCES-UI`` : les échanges ``resources/list`` / ``resources/read``
  de la boucle du pont, pour les 2 ressources ``ui://`` officielles.

Aucun test unitaire n'est « rejoué » ici : le harnais appelle le pont réel et
observe ses réponses, exactement comme un client le ferait.
"""

from __future__ import annotations

import io
import json
import logging
import re
import sys
from contextlib import contextmanager
from typing import Any, Iterator, Mapping

import src.bridges.mcp_loop_mem as lm
import src.bridges.mcp_resilience_guard as stdio_guard
from src.bridges import mcp_skills, mcp_ui
from src.bridges._mcp_elicitation import reset_elicitation_state
from src.bridges._mcp_protocol_core import (
    PROTOCOL_VERSION_LEGACY,
    PROTOCOL_VERSION_TARGET,
)
from src.pipelines.bridge_certifier._bc_checks import Checks, guard
from src.pipelines.bridge_certifier._bc_models import LEVEL_IN_PROCESS

HTTP_HEADER_KEY = "MCP-Protocol-Version"
_HOST_PATTERN = re.compile(r"https?://([^/\"'\s<>)]+)")
# Références qui déclenchent réellement un chargement réseau externe. Les URL
# de namespace XML (`xmlns="http://www.w3.org/2000/svg"`) ne sont pas des
# ressources : elles ne sont donc pas confondues avec une connexion sortante.
_RESOURCE_REF_PATTERN = re.compile(
    r"<(?:script|img|iframe|link|source|video|audio|embed|object)\b[^>]*?="
    r"[\"']\s*https?://([^/\"'\s<>]+)",
    re.IGNORECASE,
)
_LOCAL_HOSTS = {"localhost", "127.0.0.1", "[::1]", "0.0.0.0"}


def _normalized_host(raw: str) -> str:
    """Retire le port d'un hôte pour comparaison (``localhost:8080`` → ``localhost``)."""
    host = raw.lower().strip()
    if host.startswith("["):
        end = host.find("]")
        return host[: end + 1] if end != -1 else host
    return host.split(":")[0]


# Trames de la certification stdio : négociation ciblée, client hérité,
# version inconnue (refus dur) et une méthode standard du socle.
STDIO_FRAMES: tuple[dict[str, Any], ...] = (
    {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {"protocolVersion": PROTOCOL_VERSION_TARGET, "capabilities": {}},
    },
    {"jsonrpc": "2.0", "id": 2, "method": "initialize", "params": {"capabilities": {}}},
    {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "initialize",
        "params": {"protocolVersion": "1999-01-01", "capabilities": {}},
    },
    {"jsonrpc": "2.0", "id": 4, "method": "tools/list", "params": {}},
)

_SESSION_MODULES = (lm, stdio_guard)
_SESSION_ATTRS = ("_SESSION_PROTOCOL_VERSION", "_SESSION_PROJECT")


@contextmanager
def bridge_session() -> Iterator[None]:
    """Isole la session du pont : état négocié restauré à la sortie."""
    snapshot = [
        (mod, {name: getattr(mod, name) for name in _SESSION_ATTRS if hasattr(mod, name)})
        for mod in _SESSION_MODULES
    ]
    mcp_ui.reset_ui_state()
    reset_elicitation_state()
    mcp_skills.note_client_capabilities({})
    try:
        yield
    finally:
        for mod, values in snapshot:
            for name, value in values.items():
                setattr(mod, name, value)
        mcp_ui.reset_ui_state()
        reset_elicitation_state()
        mcp_skills.note_client_capabilities({})


def exchange(frame: Mapping[str, Any]) -> Any:
    """Passe une trame JSON-RPC dans la boucle réelle du pont, en mémoire."""
    raw = lm.process_message(json.dumps(dict(frame), ensure_ascii=False))
    if raw is None:
        return None
    return json.loads(raw)


def _run_stdio_loop(frames: tuple[dict[str, Any], ...]) -> list[dict[str, Any]]:
    """Injecte les trames dans la boucle stdio du pont via ``StringIO``."""
    payload = "".join(json.dumps(frame, ensure_ascii=False) + "\n" for frame in frames)
    stdin_backup, stdout_backup = sys.stdin, sys.stdout
    previous_level = logging.getLogger().manager.disable
    sys.stdin, sys.stdout = io.StringIO(payload), io.StringIO()
    # Le pont journalise sur le stdout réel : neutralisé le temps de la boucle
    # pour que la seule chose écrite soit la réponse JSON-RPC.
    logging.disable(logging.CRITICAL)
    try:
        stdio_guard.main()
        output = sys.stdout.getvalue()
    finally:
        logging.disable(previous_level)
        sys.stdin, sys.stdout = stdin_backup, stdout_backup
    responses: list[dict[str, Any]] = []
    for line in output.splitlines():
        if not line.strip():
            continue
        parsed = json.loads(line)
        if isinstance(parsed, dict):
            responses.append(parsed)
    return responses


def _routing(result: Any) -> dict[str, Any]:
    meta = result.get("_meta") if isinstance(result, dict) else None
    routing = meta.get("routing") if isinstance(meta, dict) else None
    return routing if isinstance(routing, dict) else {}


def control_stdio(checks: Checks) -> None:
    """``N1-STDIO-ROUTAGE`` — boucle stdio en mémoire, routage et refus dur."""
    with bridge_session():
        responses = _run_stdio_loop(STDIO_FRAMES)
    checks.capture("responses", len(responses))
    if not checks.expect(
        len(responses) == len(STDIO_FRAMES),
        f"la boucle stdio a rendu {len(responses)} réponse(s) pour {len(STDIO_FRAMES)} trame(s)",
    ):
        return

    initialize = responses[0].get("result") or {}
    checks.capture("negotiated", initialize.get("protocolVersion"))
    checks.expect(
        initialize.get("protocolVersion") == PROTOCOL_VERSION_TARGET,
        f"initialize n'a pas retenu {PROTOCOL_VERSION_TARGET} (reçu "
        f"{initialize.get('protocolVersion')!r})",
    )
    supported = initialize.get("supportedVersions") or []
    checks.expect(
        PROTOCOL_VERSION_LEGACY in supported,
        f"le registre unique ne publie plus {PROTOCOL_VERSION_LEGACY} (reçu {supported!r})",
    )
    routing = _routing(initialize)
    checks.expect(
        routing.get("protocolVersion") == PROTOCOL_VERSION_TARGET,
        f"_meta.routing.protocolVersion non lié à la cible (reçu {routing!r})",
    )
    checks.expect(
        routing.get("method") == "initialize", f"_meta.routing.method absent (reçu {routing!r})"
    )
    checks.expect(
        HTTP_HEADER_KEY not in json.dumps(responses[0], ensure_ascii=False),
        "un en-tête HTTP de version a été fabriqué sur un transport stdio",
    )

    legacy = responses[1]
    checks.expect(
        "result" in legacy,
        f"un client hérité sans version a été refusé (reçu {legacy.get('error')!r})",
    )

    unknown = responses[2].get("error") or {}
    checks.expect(
        unknown.get("code") == -32600,
        f"une version hors registre n'a pas été refusée en -32600 (reçu {unknown.get('code')!r})",
    )

    tools = (responses[3].get("result") or {}).get("tools") or []
    checks.capture("tools_count", len(tools))
    checks.expect(bool(tools), "tools/list a rendu un inventaire vide")
    checks.expect(
        _routing(responses[3].get("result") or {}).get("method") == "tools/list",
        "_meta.routing n'a pas été lié sur tools/list",
    )
    internal = [r.get("id") for r in responses if (r.get("error") or {}).get("code") == -32603]
    checks.expect(not internal, f"erreur interne -32603 sur les trames {internal!r}")


def control_resources(checks: Checks) -> None:
    """``N1-RESSOURCES-UI`` — inventaire et lecture des 2 ressources ``ui://``."""
    with bridge_session():
        listed = exchange({"jsonrpc": "2.0", "id": 11, "method": "resources/list", "params": {}})
        resources = ((listed or {}).get("result") or {}).get("resources") or []
        uris = {str(r.get("uri", "")) for r in resources}
        checks.capture("resources_listed", len(resources))
        checks.expect(
            mcp_ui.UI_URI_ARCHIFY in uris and mcp_ui.UI_URI_DRAWDB in uris,
            f"les 2 ressources ui:// ne sont pas exposées (reçu {sorted(uris)!r})",
        )
        for declared in resources:
            uri = str(declared.get("uri", ""))
            if not uri.startswith("ui://"):
                continue
            checks.expect(
                declared.get("mimeType") == mcp_ui.UI_APP_MIME_TYPE,
                f"{uri} : mimeType {declared.get('mimeType')!r} != {mcp_ui.UI_APP_MIME_TYPE!r}",
            )
            csp = ((declared.get("_meta") or {}).get("ui") or {}).get("csp") or {}
            checks.expect(
                csp.get("connectDomains") == [] and csp.get("resourceDomains") == [],
                f"{uri} : CSP déclarée avec des domaines de connexion ({csp!r})",
            )

        for uri in (mcp_ui.UI_URI_ARCHIFY, mcp_ui.UI_URI_DRAWDB):
            read = exchange(
                {"jsonrpc": "2.0", "id": 12, "method": "resources/read", "params": {"uri": uri}}
            )
            contents = ((read or {}).get("result") or {}).get("contents") or []
            if not checks.expect(len(contents) == 1, f"{uri} : resources/read n'a rien rendu"):
                continue
            html = str((contents[0] or {}).get("text") or "")
            checks.capture(f"{uri}.bytes", len(html))
            checks.expect(
                len(html) > 500, f"{uri} : document non autonome ({len(html)} caractères)"
            )
            checks.expect(
                "Content-Security-Policy" in html
                and "default-src 'none'" in html
                and "connect-src 'none'" in html,
                f"{uri} : CSP SEP-1865 absente ou default-src / connect-src non vides",
            )
            observed = sorted(
                {_normalized_host(h) for h in _HOST_PATTERN.findall(html)} - _LOCAL_HOSTS
            )
            checks.capture(f"{uri}.observed_hosts", observed)
            loading = sorted(
                {_normalized_host(h) for h in _RESOURCE_REF_PATTERN.findall(html)} - _LOCAL_HOSTS
            )
            checks.expect(
                not loading,
                f"{uri} : ressource(s) externe(s) chargée(s) {loading!r} — "
                "contrat de domaines de connexion et de ressources vides enfreint",
            )


def run_memory_controls() -> list[Any]:
    """Enchaîne les contrôles du périmètre mémoire (niveau 1)."""
    return [
        guard(
            "N1-STDIO-ROUTAGE",
            "Boucle stdio en mémoire : négociation, routage _meta, refus dur",
            control_stdio,
            level=LEVEL_IN_PROCESS,
        ),
        guard(
            "N1-RESSOURCES-UI",
            "Inventaire et lecture des 2 ressources ui:// (HTML autonome, CSP vide)",
            control_resources,
            level=LEVEL_IN_PROCESS,
        ),
    ]
