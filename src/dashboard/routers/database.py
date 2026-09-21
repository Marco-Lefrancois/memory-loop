"""
src/dashboard/routers/database.py — Visualiseur de Graphe et Explorateur SQLite (MLOOP-104-FE, MLOOP-075-FULL).
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

from src.dashboard.project_utils import resolve_project_canonical_name, resolve_project_path

logger = logging.getLogger("mloop.dashboard.database")
router = APIRouter(tags=["Graph & Database"])
REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
TABLE_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9_]+$")


def _get_allowed_db_roots(project_name: Optional[str] = None) -> List[Path]:
    """Répertoires autorisés pour les bases SQLite."""
    roots = [REPO_ROOT / "memory"]
    if project_name:
        roots.append(resolve_project_path(project_name) / "memory")
    return roots


def _resolve_secure_db_path(db_name: str, project_name: Optional[str] = None) -> Path:
    """Résout et valide le chemin de la base de données."""
    if not db_name or ".." in db_name or "/" in db_name or "\\" in db_name:
        raise HTTPException(status_code=403, detail="Accès interdit : nom de base non autorisé.")
    for root in _get_allowed_db_roots(project_name):
        candidate = (root / db_name).resolve()
        if any(root.resolve() in candidate.parents for root in _get_allowed_db_roots(project_name)):
            if candidate.exists() and candidate.is_file():
                return candidate
    raise HTTPException(
        status_code=404, detail=f"Base '{db_name}' introuvable dans les espaces mémoire."
    )


@contextmanager
def _open_readonly_connection(db_path: Path):
    """Connexion SQLite en lecture seule."""
    with sqlite3.connect(f"file:{db_path.as_posix()}?mode=ro", uri=True, timeout=5.0) as conn:
        conn.row_factory = sqlite3.Row
        yield conn


# ── ENDPOINTS GRAPHIFY ───────────────────────────────────────────────────────


@router.get("/api/graph/html", response_class=HTMLResponse)
def get_graph_html(project: Optional[str] = Query(None)) -> HTMLResponse:
    """Restitue le visualiseur graph.html généré par Graphify."""
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
                return HTMLResponse(
                    content=candidate.read_text(encoding="utf-8", errors="ignore"),
                    media_type="text/html; charset=utf-8",
                )
            except Exception as exc:
                logger.error("Erreur lecture graph.html : %s", exc)
                raise HTTPException(status_code=500, detail="Erreur lecture graphe.") from exc
    raise HTTPException(
        status_code=404,
        detail=f"Graphe non trouvé pour '{proj}'. Exécutez 'python src/swarm.py graph-run'.",
    )


@router.get("/api/graph/metadata")
def get_graph_metadata(project: Optional[str] = Query(None)) -> Dict[str, Any]:
    """Métadonnées structurelles du graphe (nœuds, liens, god-nodes)."""
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
                nodes, links = data.get("nodes", []), data.get("links", []) or data.get("edges", [])
                degree_map: Dict[str, int] = {}
                for link in links:
                    if link.get("source"):
                        degree_map[link["source"]] = degree_map.get(link["source"], 0) + 1
                    if link.get("target"):
                        degree_map[link["target"]] = degree_map.get(link["target"], 0) + 1
                god_nodes = [
                    {"id": n[0], "degree": n[1]}
                    for n in sorted(degree_map.items(), key=lambda x: x[1], reverse=True)[:5]
                ]
                return {
                    "project": proj,
                    "has_graph": True,
                    "nodes_count": len(nodes),
                    "edges_count": len(links),
                    "god_nodes": god_nodes,
                    "file_path": str(candidate.relative_to(REPO_ROOT)),
                }
            except Exception as exc:
                logger.warning("Échec métadonnées graph.json : %s", exc)
    return {
        "project": proj,
        "has_graph": False,
        "nodes_count": 0,
        "edges_count": 0,
        "god_nodes": [],
        "file_path": None,
    }


@router.get("/api/graph/force")
def get_force_graph_data(project: Optional[str] = Query(None)) -> Dict[str, Any]:
    """Données nœuds/liens pour le visualiseur force-directed D3.js."""
    proj = resolve_project_canonical_name(project)
    p_root = resolve_project_path(proj)
    candidates = [
        p_root / "graphify-out" / "graph.json",
        REPO_ROOT / "Projects" / proj / "graphify-out" / "graph.json",
        REPO_ROOT / "graphify-out" / "graph.json",
        p_root / "memory" / "knowledge_graph.json",
        REPO_ROOT / "memory" / "knowledge_graph.json",
    ]
    for gc in candidates:
        if not (gc.exists() and gc.is_file()):
            continue
        try:
            data = json.loads(gc.read_text(encoding="utf-8"))
            raw_nodes, raw_links = (
                data.get("nodes", []),
                data.get("links", []) or data.get("edges", []),
            )
            seen: set = set()
            nodes = []
            for n in raw_nodes:
                nid = n.get("id") or n.get("name")
                if not nid or nid in seen:
                    continue
                seen.add(nid)
                nodes.append(
                    {
                        "id": nid,
                        "label": n.get("label") or n.get("title") or nid,
                        "type": n.get("type") or n.get("layer") or n.get("category") or "Concept",
                        "group": n.get("group") or n.get("cluster") or 0,
                        "size": n.get("size") or n.get("weight") or 1,
                    }
                )
            node_ids = {n["id"] for n in nodes}
            links = [
                {
                    "source": l.get("source") or l.get("from"),
                    "target": l.get("target") or l.get("to"),
                    "label": l.get("label") or l.get("type") or "",
                    "weight": l.get("weight") or 1,
                }
                for l in raw_links
                if (l.get("source") or l.get("from")) in node_ids
                and (l.get("target") or l.get("to")) in node_ids
            ]
            return {"project": proj, "nodes": nodes, "links": links, "source": str(gc.name)}
        except Exception as exc:
            logger.warning("Échec lecture graph.json pour force: %s", exc)
    return {"project": proj, "nodes": [], "links": [], "source": "none"}


# ── ENDPOINTS SQLITE SOUVERAINS ─────────────────────────────────────────────


@router.get("/api/database/list")
def list_databases(project: Optional[str] = Query(None)) -> Dict[str, Any]:
    """Liste les bases SQLite autorisées."""
    proj = resolve_project_canonical_name(project)
    discovered, seen = [], set()
    for root in _get_allowed_db_roots(proj):
        if root.exists() and root.is_dir():
            for f in root.glob("*.db"):
                if f.is_file() and f.name not in seen:
                    seen.add(f.name)
                    discovered.append(
                        {
                            "name": f.name,
                            "size_bytes": f.stat().st_size,
                            "relative_path": str(f.relative_to(REPO_ROOT)),
                        }
                    )
    return {"project": proj, "total_databases": len(discovered), "databases": discovered}


@router.get("/api/database/tables")
def get_database_tables(
    db: str = Query(..., description="Nom de la base SQLite"), project: Optional[str] = Query(None)
) -> Dict[str, Any]:
    """Inspecte les tables et le nombre d'enregistrements d'une base SQLite."""
    proj = resolve_project_canonical_name(project)
    db_path = _resolve_secure_db_path(db, proj)
    with _open_readonly_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
        )
        tables_info = []
        for row in cursor.fetchall():
            t_name = row["name"]
            if not TABLE_NAME_PATTERN.match(t_name):
                continue
            cursor.execute(f'SELECT COUNT(*) as count FROM "{t_name}";')  # nosec B608
            cnt = cursor.fetchone()["count"]
            cursor.execute(f'PRAGMA table_info("{t_name}");')  # nosec B608
            cols = [c["name"] for c in cursor.fetchall()]
            tables_info.append(
                {"name": t_name, "records_count": cnt, "columns_count": len(cols), "columns": cols}
            )
        return {
            "database": db,
            "project": proj,
            "tables_count": len(tables_info),
            "tables": tables_info,
        }


@router.get("/api/database/records")
def get_database_records(
    db: str = Query(..., description="Nom de la base SQLite"),
    table: str = Query(..., description="Nom de la table"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=5, le=200),
    project: Optional[str] = Query(None),
) -> Dict[str, Any]:
    """Enregistrements paginés d'une table SQLite en lecture seule."""
    if not TABLE_NAME_PATTERN.match(table):
        raise HTTPException(status_code=400, detail=f"Nom de table '{table}' invalide.")
    proj = resolve_project_canonical_name(project)
    db_path = _resolve_secure_db_path(db, proj)
    with _open_readonly_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(f'SELECT COUNT(*) as count FROM "{table}";')  # nosec B608
        total_records = cursor.fetchone()["count"]
        cursor.execute(f'PRAGMA table_info("{table}");')  # nosec B608
        columns = [c["name"] for c in cursor.fetchall()]
        offset = (page - 1) * page_size
        cursor.execute(f'SELECT * FROM "{table}" LIMIT ? OFFSET ?;', (page_size, offset))  # nosec B608
        records = [dict(r) for r in cursor.fetchall()]
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
