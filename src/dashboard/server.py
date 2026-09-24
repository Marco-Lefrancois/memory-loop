# -*- coding: utf-8 -*-
"""
Serveur FastAPI pour le Dashboard d'Observabilité et Supervision Souverain mLoop.
Point d'entrée ASGI central montant l'ensemble des routeurs modulaires (Dashboard 2.0).
Conforme ADR-0202 (<=300 lignes, <=15 Ko) et ADR-0369 (robustesse Python senior).
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from src.dashboard.routers.archify import router as archify_router
from src.dashboard.routers.backlog import (
    get_project_backlog,
    get_project_story_detail,
    get_stories,
    router as backlog_router,
)
from src.dashboard.routers.database import router as database_router
from src.dashboard.routers.drawdb import router as drawdb_router
from src.dashboard.routers.dream_rsi import router as dream_rsi_router
from src.dashboard.routers.events import (
    get_events,
    router as events_router,
    stream_events,
)
from src.dashboard.routers.governance import router as governance_router
from src.dashboard.routers.graph import (
    get_graph_stats,
    router as graph_router,
)
from src.dashboard.routers.ledger import (
    get_ledger,
    router as ledger_router,
)
from src.dashboard.routers.metrics import (
    get_metrics,
    router as metrics_router,
)
from src.dashboard.routers.overview import router as overview_router
from src.dashboard.routers.resilience import router as resilience_router
from src.dashboard.routers.rules import (
    get_rho_rules,
    router as rules_router,
)
from src.dashboard.routers.swarm import router as swarm_router
from src.dashboard.routers.system import (
    _get_active_project,
    _set_active_project,
    get_active_project,
    get_cycle_state,
    get_health,
    get_modules,
    get_projects,
    router as system_router,
    select_project,
    set_active_project,
)
from src.dashboard.routers.tooling import router as tooling_router
from src.dashboard.routers.traces import router as traces_router
from src.utils.logger import get_logger

logger = get_logger("dashboard.server")

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
STATIC_DIR = Path(__file__).resolve().parent / "static"

app = FastAPI(
    title="mLoop Sovereign Observability Hub",
    description="Tableau de bord de supervision et métriques en temps réel pour Memory Loop",
    version="1.0.0",
)

# Configuration CORS pour requêtes locales
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Montage des Routeurs Modulaires Agentiques (Dashboard 2.0) ─────────────────
# Routeurs pré-existants
app.include_router(overview_router)
app.include_router(swarm_router)
app.include_router(traces_router)
app.include_router(resilience_router)
app.include_router(dream_rsi_router)
app.include_router(governance_router)
app.include_router(database_router)
app.include_router(archify_router)
app.include_router(drawdb_router)

# Routeurs extraits (MLOOP-177-BE / ADR-0202)
app.include_router(system_router)
app.include_router(metrics_router)
app.include_router(ledger_router)
app.include_router(events_router)
app.include_router(backlog_router)
app.include_router(rules_router)
app.include_router(graph_router)
app.include_router(tooling_router)


# ── MONTER LE FRONTEND WEB ─────────────────────────────────────────────────────


@app.get("/", response_class=HTMLResponse)
def get_index():
    """Sert l'interface Web d'observabilité principale."""
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return HTMLResponse("<h1>mLoop Dashboard : index.html introuvable</h1>", status_code=404)


if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

__all__ = [
    "app",
    "stream_events",
    "get_events",
    "get_metrics",
    "get_ledger",
    "get_stories",
    "get_project_backlog",
    "get_project_story_detail",
    "get_rho_rules",
    "get_graph_stats",
    "get_health",
    "get_projects",
    "get_modules",
    "select_project",
    "get_cycle_state",
    "get_active_project",
    "set_active_project",
    "_get_active_project",
    "_set_active_project",
]
