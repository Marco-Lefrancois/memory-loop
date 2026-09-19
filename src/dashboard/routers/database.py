"""
src/dashboard/routers/database.py — Explorateur souverain de Graphe et Bases SQLite (MLOOP-075-FULL).

Fournit les routes pour :
1. L'intégration du visualiseur de graphe Graphify (/api/graph/html & /api/graph/metadata).
2. L'exploration déterministe en lecture seule stricte des bases SQLite locales (/api/database/*).
Conforme ADR-0202 (<= 300 lignes) et ADR-0369 (sécurité read-only, sanitization, zéro-docking).
"""
from __future__ import annotations

import json
import logging
import math
import re
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse

from src.dashboard.project_utils import (
    resolve_project_canonical_name,
    resolve_project_path,
)

logger = logging.getLogger("mloop.dashboard.database")

router = APIRouter(tags=["Graph & Database"])
REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent

TABLE_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9_]+$")


def _get_allowed_db_roots(project_name: Optional[str] = None) -> List[Path]:
    """Retourne la liste stricte des répertoires autorisés pour les bases SQLite."""
    roots = [REPO_ROOT / "memory"]
    if project_name:
        p_root = resolve_project_path(project_name)
        roots.append(p_root / "memory")
    return roots


def _resolve_secure_db_path(db_name: str, project_name: Optional[str] = None) -> Path:
    """
    Résout et valide de façon étanche le chemin de la base de données (ADR-0380 & MLOOP-075-FULL).
    Interdit formellement le path-traversal et l'accès hors répertoires souverains memory/.
    """
    if not db_name or ".." in db_name or "/" in db_name or "\\" in db_name:
        raise HTTPException(
            status_code=403,
            detail="Accès interdit : nom de base de données non autorisé ou tentative de traversée.",
        )

    allowed_roots = _get_allowed_db_roots(project_name)
    for root in allowed_roots:
        candidate = (root / db_name).resolve()
        if any(root.resolve() in candidate.parents for root in allowed_roots) or candidate.parent in [r.resolve() for r in allowed_roots]:
            if candidate.exists() and candidate.is_file():
                return candidate

    raise HTTPException(
        status_code=404,
        detail=f"Base de données '{db_name}' introuvable dans les espaces mémoire autorisés.",
    )


@contextmanager
def _open_readonly_connection(db_path: Path):
    """Ouvre une connexion SQLite garantie en lecture seule stricte encapsulée dans un gestionnaire de contexte."""
    uri = f"file:{db_path.as_posix()}?mode=ro"
    with sqlite3.connect(uri, uri=True, timeout=5.0) as conn:
        conn.row_factory = sqlite3.Row
        yield conn


# ── ENDPOINTS GRAPHIFY ───────────────────────────────────────────────────────

@router.get("/api/graph/html", response_class=HTMLResponse)
def get_graph_html(project: Optional[str] = Query(None)) -> HTMLResponse:
    """Restitue le visualiseur interactif graph.html généré par Graphify."""
    proj = resolve_project_canonical_name(project)
    p_root = resolve_project_path(proj)

    candidates = [
        p_root / "graphify-out" / "graph.html",
        REPO_ROOT / "Projects" / proj / "graphify-out" / "graph.html",
    ]
    if proj in ("Memory Loop", "mLoop", "global", "ALL"):
        candidates.append(REPO_ROOT / "graphify-out" / "graph.html")

    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            try:
                content = candidate.read_text(encoding="utf-8", errors="ignore")
                return HTMLResponse(content=content, media_type="text/html; charset=utf-8")
            except Exception as exc:
                logger.error("Erreur lecture graph.html : %s", exc)
                raise HTTPException(status_code=500, detail="Erreur lors de la lecture du fichier de graphe.") from exc

    raise HTTPException(
        status_code=404,
        detail=f"Graphe Graphify non trouvé pour le projet '{proj}'. Exécutez 'python src/swarm.py graph-run'.",
    )


@router.get("/api/graph/metadata")
def get_graph_metadata(project: Optional[str] = Query(None)) -> Dict[str, Any]:
    """Retourne les métadonnées structurelles du graphe de connaissances (nœuds, liens, god-nodes)."""
    proj = resolve_project_canonical_name(project)
    p_root = resolve_project_path(proj)

    candidates = [
        p_root / "graphify-out" / "graph.json",
        REPO_ROOT / "Projects" / proj / "graphify-out" / "graph.json",
        REPO_ROOT / "graphify-out" / "graph.json",
    ]

    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            try:
                data = json.loads(candidate.read_text(encoding="utf-8", errors="ignore"))
                nodes = data.get("nodes", [])
                links = data.get("links", []) or data.get("edges", [])

                # Détection heuristique des God Nodes (degré de connexion le plus élevé)
                degree_map: Dict[str, int] = {}
                for link in links:
                    src = link.get("source")
                    tgt = link.get("target")
                    if src:
                        degree_map[src] = degree_map.get(src, 0) + 1
                    if tgt:
                        degree_map[tgt] = degree_map.get(tgt, 0) + 1

                top_nodes = sorted(degree_map.items(), key=lambda x: x[1], reverse=True)[:5]
                god_nodes = [{"id": n[0], "degree": n[1]} for n in top_nodes]

                return {
                    "project": proj,
                    "has_graph": True,
                    "nodes_count": len(nodes),
                    "edges_count": len(links),
                    "god_nodes": god_nodes,
                    "file_path": str(candidate.relative_to(REPO_ROOT)),
                }
            except Exception as exc:
                logger.warning("Échec analyse métadonnées graph.json : %s", exc)

    return {
        "project": proj,
        "has_graph": False,
        "nodes_count": 0,
        "edges_count": 0,
        "god_nodes": [],
        "file_path": None,
    }


# ── ENDPOINTS SQLITE SOUVERAINS ─────────────────────────────────────────────

@router.get("/api/database/list")
def list_databases(project: Optional[str] = Query(None)) -> Dict[str, Any]:
    """Liste toutes les bases SQLite autorisées pour le projet spécifié."""
    proj = resolve_project_canonical_name(project)
    roots = _get_allowed_db_roots(proj)
    discovered: List[Dict[str, Any]] = []
    seen = set()

    for root in roots:
        if root.exists() and root.is_dir():
            for f in root.glob("*.db"):
                if f.is_file() and f.name not in seen:
                    seen.add(f.name)
                    discovered.append({
                        "name": f.name,
                        "size_bytes": f.stat().st_size,
                        "relative_path": str(f.relative_to(REPO_ROOT)),
                    })

    return {
        "project": proj,
        "total_databases": len(discovered),
        "databases": discovered,
    }


@router.get("/api/database/tables")
def get_database_tables(
    db: str = Query(..., description="Nom du fichier de la base de données"),
    project: Optional[str] = Query(None),
) -> Dict[str, Any]:
    """Inspecte les tables et le nombre d'enregistrements d'une base SQLite autorisée."""
    proj = resolve_project_canonical_name(project)
    db_path = _resolve_secure_db_path(db, proj)

    with _open_readonly_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        tables_raw = cursor.fetchall()
        tables_info = []

        for row in tables_raw:
            t_name = row["name"]
            if not TABLE_NAME_PATTERN.match(t_name):
                continue
            cursor.execute(f'SELECT COUNT(*) as count FROM "{t_name}";')  # nosec B608
            cnt = cursor.fetchone()["count"]
            cursor.execute(f'PRAGMA table_info("{t_name}");')  # nosec B608
            cols = [c["name"] for c in cursor.fetchall()]
            tables_info.append({
                "name": t_name,
                "records_count": cnt,
                "columns_count": len(cols),
                "columns": cols,
            })

        return {
            "database": db,
            "project": proj,
            "tables_count": len(tables_info),
            "tables": tables_info,
        }


@router.get("/api/database/records")
def get_database_records(
    db: str = Query(..., description="Nom du fichier de la base de données"),
    table: str = Query(..., description="Nom de la table à consulter"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=5, le=200),
    project: Optional[str] = Query(None),
) -> Dict[str, Any]:
    """Restitue les enregistrements paginés d'une table SQLite en lecture seule stricte."""
    if not TABLE_NAME_PATTERN.match(table):
        raise HTTPException(
            status_code=400,
            detail=f"Nom de table '{table}' invalide. Caractères alphanumériques et soulignés uniquement.",
        )

    proj = resolve_project_canonical_name(project)
    db_path = _resolve_secure_db_path(db, proj)

    with _open_readonly_connection(db_path) as conn:
        cursor = conn.cursor()
        # Comptage total
        cursor.execute(f'SELECT COUNT(*) as count FROM "{table}";')  # nosec B608
        total_records = cursor.fetchone()["count"]

        # Colonnes
        cursor.execute(f'PRAGMA table_info("{table}");')  # nosec B608
        columns = [c["name"] for c in cursor.fetchall()]

        # Pagination sécurisée
        offset = (page - 1) * page_size
        cursor.execute(
            f'SELECT * FROM "{table}" LIMIT ? OFFSET ?;',  # nosec B608
            (page_size, offset),
        )
        rows = cursor.fetchall()
        records = [dict(r) for r in rows]

        total_pages = max(1, math.ceil(total_records / page_size))

        return {
            "database": db,
            "table": table,
            "project": proj,
            "columns": columns,
            "total_records": total_records,
            "total_pages": total_pages,
            "current_page": page,
            "page_size": page_size,
            "records": records,
        }
