"""
src/pipelines/bridge_certifier/_bc_browser.py — Certification des ressources
``ui://`` dans un vrai navigateur (MLOOP-215-FULL), niveau 1 runtime.

Micro-grill 215-Q1 : le harnais ouvre chaque ressource dans une **enveloppe de
cadre fidèle à l'IDE** — un ``<iframe sandbox="allow-scripts">`` servi à un
document hôte — et observe cinq choses, une par ressource :

1. le document se rend sans erreur ;
2. **aucune requête réseau sortante** n'est émise (CSP ``connect-src 'none'``) ;
3. une interaction de base aboutit (repli dimensionnel puis activation du lien
   de repli, qui émet ``ui/open-link`` vers l'hôte) ;
4. un aller-retour ``project_changed`` de l'hôte met le badge à jour **en
   place**, sans rechargement ;
5. le pont répond au handshake ``ui/initialize``.

La dépendance Playwright est interrogée **avant** tout lancement : si elle est
absente, le contrôle échoue de façon nommée (état non exécuté, jamais un vert
obtenu par saut de test) — c'est l'objet de l'OQ-215-02.
"""

from __future__ import annotations

import html as html_lib
import importlib
import importlib.util
from typing import Any

from src.pipelines.bridge_certifier._bc_checks import Checks, guard
from src.pipelines.bridge_certifier._bc_models import LEVEL_IN_PROCESS
from src.bridges import mcp_ui

MIN_WIDTH_PX = 300
PROJECT_MARKER = "CERT-215"
NETWORK_SCHEMES = ("http://", "https://", "ws://", "wss://")

HOST_DOCUMENT = """<!doctype html>
<html lang="fr"><head><meta charset="utf-8"><title>Harnais de certification ui://</title>
<style>html,body{margin:0;padding:0;overflow:hidden}
iframe{border:0;width:100vw;height:100vh;display:block}</style></head>
<body><iframe id="frame" sandbox="allow-scripts" srcdoc="{resource}"></iframe>
<script>
window.__msgs = [];
window.addEventListener("message", function (event) {{ window.__msgs.push(event.data); }});
</script></body></html>"""


def playwright_status() -> tuple[bool, str]:
    """Dépendance de certification : présente ou nommée explicitement comme absente."""
    spec = importlib.util.find_spec("playwright")
    if spec is None:
        return False, "playwright absent de l'interpréteur en cours (OQ-215-02)"
    try:
        importlib.import_module("playwright.sync_api")
    except Exception as exc:  # noqa: BLE001 — l'absence est un constat, pas un crash
        return False, f"playwright inutilisable : {type(exc).__name__}: {exc}"
    return True, "playwright importable dans l'interpréteur en cours"


def _read_resource(uri: str) -> str:
    payload = mcp_ui.read_ui_resource(uri)
    if not isinstance(payload, dict) or not payload.get("ok"):
        raise RuntimeError(f"resources/read a refusé {uri} : {payload!r}")
    return str((payload.get("content") or {}).get("text") or "")


def _frame(page: Any) -> Any:
    for candidate in page.frames:
        if candidate is not page.main_frame:
            return candidate
    raise RuntimeError("le cadre sandboxé n'a pas été ouvert par le navigateur")


def _certify(uri: str, *, timeout_s: float) -> dict[str, Any]:
    """Exécute les 5 observations du cadre pour une ressource donnée."""
    sync_playwright = importlib.import_module("playwright.sync_api").sync_playwright

    resource_html = _read_resource(uri)
    host = HOST_DOCUMENT.format(resource=html_lib.escape(resource_html, quote=True))
    observations: dict[str, Any] = {"uri": uri, "resource_bytes": len(resource_html)}
    external: list[str] = []
    captured: list[Any] = []

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        try:
            context = browser.new_context(viewport={"width": 900, "height": 700})
            page = context.new_page()
            page.on(
                "request",
                lambda req: (
                    external.append(req.url) if req.url.startswith(NETWORK_SCHEMES) else None
                ),
            )
            page.set_content(host, wait_until="load", timeout=timeout_s * 1000)
            frame = _frame(page)
            captured_messages(page, captured)

            # 1. rendu + badge projet du cadre
            frame.wait_for_selector("#mloop-project-badge", timeout=timeout_s * 1000)
            observations["badge_initial"] = frame.eval_on_selector(
                "#mloop-project-badge", "el => el.textContent"
            )
            frame.evaluate("window.__cert_marker = 42")

            # 2. interaction de base : repli dimensionnel puis activation du lien
            page.set_viewport_size({"width": MIN_WIDTH_PX, "height": 700})
            frame.wait_for_selector(
                "#mloop-fallback-banner:not([hidden])", timeout=timeout_s * 1000
            )
            frame.click("#mloop-open-local")
            page.wait_for_function(
                "() => window.__msgs.some(m => m && m.method === 'ui/open-link')",
                timeout=timeout_s * 1000,
            )
            observations["interaction"] = "ui/open-link émis vers l'hôte"
            handshake = [m.get("method") for m in captured if isinstance(m, dict)]
            observations["handshake"] = [m for m in handshake if str(m).startswith("ui/")]

            # 3. aller-retour project_changed : mise à jour en place, zéro rechargement
            page.evaluate(
                "() => document.getElementById('frame').contentWindow.postMessage("
                "{type: 'project_changed', project: '%s'}, '*')" % PROJECT_MARKER
            )
            page.wait_for_function(
                "() => document.querySelector('#frame') && true", timeout=timeout_s * 1000
            )
            for _ in range(60):
                if (
                    frame.eval_on_selector("#mloop-project-badge", "el => el.textContent")
                    == PROJECT_MARKER
                ):
                    break
                page.wait_for_timeout(50)
            observations["badge_after"] = frame.eval_on_selector(
                "#mloop-project-badge", "el => el.textContent"
            )
            observations["marker_after"] = frame.evaluate("window.__cert_marker")
            observations["external_requests"] = external
        finally:
            browser.close()
    return observations


def captured_messages(page: Any, sink: list[Any]) -> None:
    """Rejoue le carnet de messages hôte dans ``sink`` (lecture différée)."""
    sink.extend(page.evaluate("() => window.__msgs.slice()"))


def _check_resource(checks: Checks, uri: str, *, timeout_s: float) -> None:
    if not checks.expect(
        uri in mcp_ui.UI_KNOWN_URIS, f"{uri} ne fait pas partie du registre officiel"
    ):
        return
    ok, status = playwright_status()
    checks.capture("playwright", status)
    if not checks.expect(ok, f"état non exécuté — {status} (OQ-215-02)"):
        return
    try:
        obs = _certify(uri, timeout_s=timeout_s)
    except Exception as exc:  # noqa: BLE001 — rupture runtime = constat du rapport
        checks.failures.append(f"échec du rendu navigateur : {type(exc).__name__}: {exc}")
        return
    checks.details.update(obs)
    checks.expect(bool(obs.get("badge_initial")), "le cadre ne rend pas de badge projet")
    checks.expect(obs.get("interaction") is not None, "l'interaction de base n'a pas abouti")
    checks.expect(
        PROJECT_MARKER in str(obs.get("badge_after")),
        f"project_changed n'a pas mis le badge à jour (reçu {obs.get('badge_after')!r})",
    )
    checks.expect(
        obs.get("marker_after") == 42,
        f"rechargement détecté pendant la mise à jour en place (marqueur {obs.get('marker_after')!r})",
    )
    checks.expect(
        not obs.get("external_requests"),
        f"requête(s) sortante(s) émise(s) : {obs.get('external_requests')!r}",
    )
    checks.expect(bool(obs.get("handshake")), "aucun handshake ui/initialize émis vers l'hôte")


def run_browser_controls(*, timeout_s: float = 30.0) -> list[Any]:
    """Un contrôle par ressource officielle (niveau 1, rendu réel)."""
    return [
        guard(
            "N1-NAV-ARCHIFY",
            "Cadre sandboxé ui://archify/cockpit : rendu, isolement, interaction",
            _check_resource,
            level=LEVEL_IN_PROCESS,
            uri=mcp_ui.UI_URI_ARCHIFY,
            timeout_s=timeout_s,
        ),
        guard(
            "N1-NAV-DRAWDB",
            "Cadre sandboxé ui://drawdb/schema : rendu, isolement, interaction",
            _check_resource,
            level=LEVEL_IN_PROCESS,
            uri=mcp_ui.UI_URI_DRAWDB,
            timeout_s=timeout_s,
        ),
    ]


# Réexporté pour que le runner puisse déclarer la dépendance manquante.
def missing_dependency() -> list[str]:
    ok, _ = playwright_status()
    return [] if ok else ["playwright"]
