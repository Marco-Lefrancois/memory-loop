"""
src/bridges/_mcp_ui_shell.py — Coquille HTML du cadre MCP Apps (MLOOP-212-FE).

Sous-module de ``mcp_ui.py`` (ADR-0202 : ≤300 lignes). Charge les artefacts
(showcase Archify / rendu DrawDB), strip les actifs CDN (zéro CDN) et injecte :
CSP meta, bannière de repli, badge projet, récepteur ``project_changed`` (mise
à jour en place, zéro rechargement) et zoom opt-in sur le schéma relationnel.
"""

from __future__ import annotations

import html as html_lib
import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger("bridges.mcp_ui.shell")


def _dbg(event: str, exc: Optional[BaseException] = None, **extra: Any) -> None:
    """Log DEBUG contextuel ADR-0369 (zéro silence d'exception nu, extra structuré)."""
    if exc is not None:
        extra["error"] = str(exc)
    logger.debug(event, exc_info=exc is not None, extra={"component": "bridges.mcp_ui", **extra})


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SHOWCASE_DIR = REPO_ROOT / "tools" / "archify" / "showcase"

# Seuil de repli dimensionnel (registre partagé 212-Q2) — SSOT réexportée par mcp_ui.py.
UI_MIN_WIDTH_PX = 320

# CSP SEP-1865 (aucun domaine déclaré) + garde-fous objet/base ; `connect-src
# 'none'` : zéro connexion réseau sortante depuis le cadre (212-Q1).
CSP_META = (
    '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; '
    "script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data:; media-src 'self' data:; connect-src 'none'; "
    "frame-src 'none'; object-src 'none'; base-uri 'self'\">"
)

_UI_CSS = """
#mloop-fallback-banner{position:fixed;left:0;right:0;bottom:0;z-index:2147483646;display:flex;gap:.75rem;align-items:center;justify-content:center;flex-wrap:wrap;padding:.5rem .9rem;background:#1e293b;color:#e2e8f0;border-top:2px solid #f59e0b;font:600 12px/1.4 system-ui,sans-serif}
#mloop-fallback-banner[hidden]{display:none!important}
#mloop-fallback-banner a{color:#fbbf24;text-decoration:underline;text-underline-offset:2px;padding:.15rem .4rem;border-radius:4px;border:1px solid transparent}
#mloop-fallback-banner a:hover{color:#0f172a;background:#fbbf24;text-decoration:none}
#mloop-fallback-banner a:focus-visible{outline:2px solid #38bdf8;outline-offset:2px;background:#0ea5e9;color:#0f172a}
#mloop-fallback-banner a:active{color:#0f172a;background:#f59e0b;transform:translateY(1px)}
#mloop-ui-chip{position:fixed;top:8px;right:8px;z-index:2147483647;padding:.15rem .55rem;background:rgba(15,23,42,.85);border:1px solid #334155;border-radius:999px;color:#94a3b8;font:600 11px/1.3 system-ui,sans-serif;pointer-events:none;max-width:45vw;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
#mloop-ui-chip b{color:#38bdf8}"""

# Balisage : badge projet (paramètre d'adresse visible) + bannière de repli non bloquante.
_UI_MARKUP = (
    '<div id="mloop-ui-chip" data-mloop-ui="keep" aria-hidden="true">projet&nbsp;'
    '<b id="mloop-project-badge">{project}</b></div>\n'
    '<div id="mloop-fallback-banner" data-mloop-ui="keep" hidden role="status">'
    "<span>Cadre trop étroit pour être exploitable.</span>"
    '<a id="mloop-open-local" href="{local_url}" target="_blank" rel="noopener">'
    "ouvrir dans le navigateur</a></div>"
)

# Coquille JS : handshake MCP Apps, seuil de repli, ouverture locale, projet en place, zoom opt-in.
_UI_JS = r"""
(function () {
  "use strict";
  var CFG = window.__MLOOP_UI__ || {};
  var MIN_W = CFG.minWidthPx || 320;
  var localUrl = CFG.localUrl || "";
  var project = CFG.project || "";
  var nextId = 1;
  function log(msg) { console.info("[mloop-ui] " + msg); }
  function toHost(method, params) {
    try { window.parent.postMessage({ jsonrpc: "2.0", id: nextId++, method: method, params: params || {} }, "*"); return true; }
    catch (err) { log("postMessage impossible vers le chat: " + err); return false; }
  }
  toHost("ui/initialize", { protocolVersion: "2026-01-26", appCapabilities: { availableDisplayModes: ["inline", "fullscreen"] } });
  toHost("ui/notifications/initialized", {});
  var banner = document.getElementById("mloop-fallback-banner"), bannerShown = false;
  function evalWidth(width) {
    if (!(width > 0) || !banner) { return; }
    if (width < MIN_W && !bannerShown) { banner.hidden = false; bannerShown = true; log("bannière de repli activée — largeur " + width + "px < " + MIN_W + "px"); }
    else if (width >= MIN_W && bannerShown) { banner.hidden = true; bannerShown = false; log("bannière de repli masquée — largeur " + width + "px"); }
  }
  function notifySize() { toHost("ui/notifications/size-changed", { width: document.documentElement.clientWidth, height: document.documentElement.clientHeight }); }
  if (typeof ResizeObserver === "function") {
    new ResizeObserver(function (entries) { var box = entries[0] && entries[0].contentRect;
      if (box) { evalWidth(Math.round(box.width)); notifySize(); } }).observe(document.documentElement);
  }
  window.addEventListener("resize", function () { evalWidth(document.documentElement.clientWidth); });
  evalWidth(document.documentElement.clientWidth);
  var openLocal = document.getElementById("mloop-open-local");
  if (openLocal) {
    openLocal.addEventListener("click", function (event) {
      event.preventDefault(); log("ouverture de l'adresse locale: " + localUrl); toHost("ui/open-link", { url: localUrl });
      try { window.open(localUrl, "_blank", "noopener"); } catch (err) { log("ouverture native refusée par le sandbox"); }
    });
  }
  (CFG.hideSelectors || []).forEach(function (sel) {
    Array.prototype.forEach.call(document.querySelectorAll(sel), function (node) { node.hidden = true; });
  });
  var badge = document.getElementById("mloop-project-badge");
  function applyProject(next, payload) {
    if (next && next !== project) {
      project = next;
      if (badge) { badge.textContent = project; }
      document.title = String(document.title).replace(/\s·\sprojet\s.*$/, "") + " · projet " + project;
      log("projet actif mis à jour en place: " + project);
    }
    if (payload && Array.isArray(payload.tables) && typeof window.renderSchema === "function") {
      window.renderSchema(payload.tables);
      log("schéma réactualisé en place — zoom/déplacement conservés (aucun rechargement)");
    } else if (payload && typeof payload.html === "string" && CFG.swapSelector) {
      var swap = document.querySelector(CFG.swapSelector);
      if (swap) { swap.innerHTML = payload.html; log("contenu réactualisé en place (aucun rechargement)"); }
    }
  }
  window.addEventListener("message", function (event) {
    if (event.source !== window.parent || !event.data || typeof event.data !== "object") { return; }
    var data = event.data;
    if (data.type === "project_changed") { applyProject(data.project, data.payload); return; }
    if (data.method === "ui/notifications/host-context-changed" && data.params && data.params.project) {
      applyProject(data.params.project, data.params.payload);
    }
  });
  var zoomEl = CFG.zoomTarget ? document.querySelector(CFG.zoomTarget) : null;
  if (zoomEl) {
    var view = { s: 1, x: 0, y: 0 };
    var drag = null;
    function applyView() {
      zoomEl.style.transformOrigin = "0 0";
      zoomEl.style.transform = "translate(" + view.x + "px," + view.y + "px) scale(" + view.s + ")";
    }
    document.addEventListener("wheel", function (event) {
      event.preventDefault();
      view.s = Math.min(4, Math.max(0.25, view.s * (event.deltaY < 0 ? 1.1 : 0.9090909091)));
      applyView();
    }, { passive: false });
    zoomEl.addEventListener("pointerdown", function (event) {
      drag = { x: event.clientX, y: event.clientY };
      try { zoomEl.setPointerCapture(event.pointerId); } catch (err) { log("pointer capture indisponible"); }
    });
    zoomEl.addEventListener("pointermove", function (event) {
      if (!drag) { return; }
      view.x += event.clientX - drag.x;
      view.y += event.clientY - drag.y;
      drag = { x: event.clientX, y: event.clientY };
      applyView();
    });
    zoomEl.addEventListener("pointerup", function () { drag = null; });
    zoomEl.addEventListener("pointercancel", function () { drag = null; });
    log("zoom/déplacement actifs sur " + CFG.zoomTarget);
  }
})();
"""

_SCRIPT_EXT = re.compile(
    r"<script\b[^>]*\bsrc\s*=\s*[\"']https?://[^\"']*[\"'][^>]*>.*?</script\s*>", re.I | re.S
)
_LINK_EXT = re.compile(r"<link\b[^>]*\bhref\s*=\s*[\"']https?://[^\"']*[\"'][^>]*>", re.I)
_IMPORT_EXT = re.compile(r"@import\s+(?:url\()?\s*[\"']?https?://[^)\"'\s]+[\"']?\s*\)?\s*;?", re.I)
_CSS_URL_EXT = re.compile(r"url\(\s*[\"']?https?://[^)\"'\s]+[\"']?\s*\)", re.I)


def strip_external_assets(source: str) -> tuple[str, int]:
    """Supprime les actifs externes (CDN/fontes) — In-Scope zéro CDN. Retourne (html, nb)."""
    stripped = 0
    for pattern in (_SCRIPT_EXT, _LINK_EXT, _IMPORT_EXT, _CSS_URL_EXT):
        source, count = pattern.subn("", source)
        stripped += count
    return source, stripped


def resolve_archify_artifact(project: str) -> Optional[Path]:
    """Résout l'artefact cockpit du projet (exact > préfixe le plus court > premier)."""
    if not SHOWCASE_DIR.is_dir():
        return None
    files = sorted(SHOWCASE_DIR.glob("*.architecture.html"))
    if not files:
        return None
    slug = re.sub(r"[^a-z0-9]+", "-", (project or "").lower()).strip("-")
    if slug:
        exact = SHOWCASE_DIR / f"{slug}.architecture.html"
        if exact in files:
            return exact
        candidates = [f for f in files if f.name.startswith(slug)]
        if candidates:
            return min(candidates, key=lambda f: (len(f.name), f.name))
    return files[0]


def _empty_state_page(kind: str, project: str, local_url: str, reason: str) -> str:
    """Surface Initial/Vide : page autonome honnête (jamais d'erreur bloquante). Injection faite par build_ui_page."""
    return (
        '<!DOCTYPE html><html lang="fr"><head><meta charset="utf-8">'
        f'<title>mLoop {html_lib.escape(kind)}</title></head><body><main style="display:flex;'
        "flex-direction:column;align-items:center;justify-content:center;min-height:60vh;gap:1rem;"
        'background:#0f172a;color:#e2e8f0;font:15px/1.5 system-ui,sans-serif;text-align:center">'
        f'<div style="font-size:2.5rem" aria-hidden="true">&#128736;</div><p>{html_lib.escape(reason)}</p>'
        f'<p style="font:600 12px/1.4 monospace;color:#94a3b8">projet : {html_lib.escape(project)}</p>'
        f'<p><a href="{html_lib.escape(local_url)}" style="color:#38bdf8">ouvrir dans le navigateur</a></p>'
        "</main></body></html>"
    )


def _head_snippet(
    project: str,
    local_url: str,
    uri: Optional[str],
    zoom_target: Optional[str],
    hide_selectors: list,
    min_width: int,
) -> str:
    config: Dict[str, Any] = {
        "uri": uri,
        "project": project,
        "localUrl": local_url,
        "minWidthPx": int(min_width),
        "zoomTarget": zoom_target,
        "swapSelector": "#schema-container" if zoom_target else None,
        "hideSelectors": hide_selectors,
    }
    return (
        CSP_META
        + "<style>"
        + _UI_CSS
        + "</style>\n<script>window.__MLOOP_UI__ = "
        + json.dumps(config, ensure_ascii=False)
        + ";</script>"
    )


def _body_snippet(project: str, local_url: str) -> str:
    markup = _UI_MARKUP.format(
        project=html_lib.escape(project or "—"),
        local_url=html_lib.escape(local_url or "#", quote=True),
    )
    return "\n" + markup + "\n<script>" + _UI_JS + "</script>\n"


def _inject(source: str, head_snippet: str, body_snippet: str) -> str:
    match = re.search(r"<head[^>]*>", source, re.I)
    source = (
        source[: match.end()] + head_snippet + source[match.end() :]
        if match
        else head_snippet + source
    )
    close = re.search(r"</body\s*>", source, re.I)
    if close:
        return source[: close.start()] + body_snippet + source[close.start() :]
    return source + body_snippet


def build_ui_page(kind: str, uri: str, project: str, local_url: str, min_width: int) -> str:
    """Assemble la page servie par resources/read : ``cockpit`` (artefact Archify stripé) ou ``schema`` (instantané DrawDB autonome, OQ-212-02)."""
    zoom_target: Optional[str] = None
    hide_selectors: list = []
    source = ""
    if kind == "schema":
        zoom_target = "#schema-container"
        hide_selectors = [".toolbar"]  # selecteur multi-schemas : rupture serveur hors cadre
        try:
            from tools.drawdb._discovery import find_dbml_files  # import différé (ADR-0202)
            from tools.drawdb._page import render_schema_page

            source = render_schema_page(find_dbml_files(project), 0)
        except Exception as exc:
            _dbg("ui_schema_render_failed", exc, project=project)
            source = _empty_state_page(
                "DrawDB ERD",
                project,
                local_url,
                "Impossible de générer l'instantané du schéma relationnel.",
            )
    else:
        path = resolve_archify_artifact(project)
        if path is None:
            source = _empty_state_page(
                "Archify Cockpit",
                project,
                local_url,
                "Aucun artefact Archify n'est disponible pour ce projet.",
            )
        else:
            try:
                source = path.read_text(encoding="utf-8", errors="ignore")
            except OSError as exc:
                _dbg("ui_cockpit_read_failed", exc, path=str(path))
                source = _empty_state_page(
                    "Archify Cockpit",
                    project,
                    local_url,
                    "Lecture de l'artefact cockpit impossible.",
                )
    source, stripped = strip_external_assets(source)
    if stripped:
        _dbg("ui_cdn_assets_stripped", stripped=stripped, kind=kind)
    head = _head_snippet(project, local_url, uri, zoom_target, hide_selectors, min_width)
    return _inject(source, head, _body_snippet(project, local_url))
