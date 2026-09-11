# -*- coding: utf-8 -*-
"""
Serveur FastAPI pour le Dashboard d'Observabilité et Supervision Souverain mLoop.
Expose des endpoints REST pour les métriques de tokens, le flux d'événements,
la visualisation du backlog et l'intégrité de la mémoire (Zéro-Docker).
Supporte la résolution canonique des projets (ex: Boire & Frères) et la récursion des stories/preuves.
"""

from __future__ import annotations

import json
import os
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

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


def _canonical_key(name: str) -> str:
    """Normalise un nom pour recherche tolérante (minuscules sans accents ni ponctuation)."""
    if not name:
        return ""
    normalized = unicodedata.normalize("NFD", str(name))
    clean = "".join(c for c in normalized if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-zA-Z0-9]", "", clean).lower()


def _resolve_project_canonical_name(project_name: Optional[str]) -> str:
    """Résout le nom canonique du projet en gérant les alias (ex: 'boire' -> 'BoireFrere_Segment2')."""
    if not project_name:
        return _get_active_project()

    clean = project_name.strip()
    if clean in ("Memory Loop", "mLoop", "global", "All"):
        return clean

    # Utiliser le résolveur officiel mLoop si disponible
    try:
        from src.swarm import resolve_project_name
        resolved = resolve_project_name(clean)
        if resolved:
            return resolved
    except Exception:
        pass

    # Fallback recherche directe dans Projects/
    projects_dir = REPO_ROOT / "Projects"
    if projects_dir.exists():
        target_canon = _canonical_key(clean)
        for p in projects_dir.iterdir():
            if p.is_dir() and not p.name.startswith("."):
                p_canon = _canonical_key(p.name)
                if target_canon == p_canon or (target_canon and (target_canon in p_canon or p_canon in target_canon)):
                    return p.name

    return clean


def _get_active_project() -> str:
    """Résout le nom du projet actif."""
    env_proj = os.getenv("MLOOP_ACTIVE_PROJECT")
    if env_proj:
        return _resolve_project_canonical_name(env_proj)

    active_json = REPO_ROOT / "memory" / "active_project.json"
    if active_json.exists():
        try:
            data = json.loads(active_json.read_text(encoding="utf-8"))
            if data.get("active_project"):
                return _resolve_project_canonical_name(data["active_project"])
        except Exception:
            pass

    return "Memory Loop"


def _set_active_project(project_name: str) -> str:
    """Met à jour et persiste le projet actif dans memory/active_project.json et os.environ."""
    canon = _resolve_project_canonical_name(project_name)
    os.environ["MLOOP_ACTIVE_PROJECT"] = canon
    active_json = REPO_ROOT / "memory" / "active_project.json"
    try:
        active_json.parent.mkdir(parents=True, exist_ok=True)
        active_json.write_text(
            json.dumps({"active_project": canon}, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )
    except Exception:
        pass
    return canon


def _list_available_projects() -> List[str]:
    """Retourne la liste de tous les projets disponibles dans le dépôt."""
    projects = set()
    projects_dir = REPO_ROOT / "Projects"
    if projects_dir.exists():
        for p in projects_dir.iterdir():
            if p.is_dir() and not p.name.startswith(".") and not p.name.endswith("_DEPRECATED"):
                projects.add(p.name)

    # Toujours inclure le projet cadre mLoop
    projects.add("Memory Loop")

    # Trier avec le projet actif en tête
    active = _get_active_project()
    sorted_projects = sorted(list(projects), key=lambda x: (x != active, x.lower()))
    return sorted_projects


def _get_project_root(project_name: Optional[str]) -> Path:
    """Résout le chemin racine d'un projet cible."""
    canon = _resolve_project_canonical_name(project_name)
    if not canon or canon in ("Memory Loop", "mLoop", "global"):
        return REPO_ROOT
    p_path = REPO_ROOT / "Projects" / canon
    if p_path.exists():
        return p_path
    return REPO_ROOT


def _match_project_alias(candidate: str, target: str) -> bool:
    """Vérifie si deux noms de projets correspondent au même projet (alias tolérant)."""
    if not candidate or not target:
        return False
    if candidate.lower() == target.lower():
        return True
    c_canon = _canonical_key(candidate)
    t_canon = _canonical_key(target)
    if c_canon == t_canon:
        return True
    # Gérer BoireFrere_Reception vs BoireFrere_Segment2 vs Boire et Frère
    if "boire" in c_canon and "boire" in t_canon:
        return True
    if "metro" in c_canon and "metro" in t_canon:
        return c_canon in t_canon or t_canon in c_canon
    return False


# ── ENDPOINTS REST ─────────────────────────────────────────────────────────────


@app.get("/api/health")
def get_health() -> Dict[str, Any]:
    """Vérification de l'état de santé du serveur d'observabilité."""
    active_p = _get_active_project()
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "engine": "Memory Loop (mLoop)",
        "version": "1.0.0",
        "mode": "sovereign-local",
        "docker_free": True,
        "active_project": active_p,
    }


@app.get("/api/projects")
def get_projects() -> Dict[str, Any]:
    """Liste tous les projets connus et identifie le projet actif."""
    projs = _list_available_projects()
    friendly_names = {
        "BoireFrere_Segment2": "🐣 Boire & Frères (Segment 2)",
        "Metro_SANTE": "🏥 Metro - Santé",
        "Metro_FOOD": "🛒 Metro - Alimentation",
        "Metro_COMMERCE": "💳 Metro - E-Commerce",
        "Metro_SHARED": "📦 Metro - Shared",
        "Memory Loop": "🌀 Memory Loop",
        "mLoop-Dashboard": "📊 mLoop Dashboard",
        "HTC": "🧱 HTC Maçonnerie",
        "ReviewSenseCloud": "⭐ ReviewSense Cloud",
    }
    formatted = [
        {"id": p, "name": friendly_names.get(p, p)}
        for p in projs
    ]
    return {
        "active_project": _get_active_project(),
        "projects": projs,
        "projects_formatted": formatted,
    }


@app.post("/api/project/select")
def select_project(payload: Optional[Dict[str, Any]] = None, project: Optional[str] = Query(None)) -> Dict[str, Any]:
    """Persiste le projet actif sélectionné par l'utilisateur."""
    target = project or (payload.get("project") if payload else None)
    if not target:
        raise HTTPException(status_code=400, detail="Paramètre 'project' manquant.")
    canon = _set_active_project(target)
    return {
        "status": "ok",
        "active_project": canon,
        "message": f"Projet actif persisté : {canon}",
    }


@app.get("/api/metrics")
def get_metrics(project: Optional[str] = None) -> Dict[str, Any]:
    """
    Agrège les métriques de consommation de jetons et de coûts depuis token_ledger.jsonl.
    """
    target_project = _resolve_project_canonical_name(project)
    p_root = _get_project_root(target_project)

    ledger_files: List[tuple[Path, bool]] = []  # (chemin, est_fichier_dédié_au_projet)

    # 1. Fichier spécifique projet si existant
    if p_root != REPO_ROOT:
        proj_ledger = p_root / "memory" / "token_ledger.jsonl"
        if proj_ledger.exists():
            ledger_files.append((proj_ledger, True))

    # 2. Fichier global racine
    global_ledger = REPO_ROOT / "memory" / "token_ledger.jsonl"
    if global_ledger.exists():
        ledger_files.append((global_ledger, False))

    entries = []
    seen_fingerprints = set()

    for l_path, is_dedicated in ledger_files:
        try:
            with open(l_path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                        entry_proj = entry.get("project", "")

                        # Si le fichier provient directement du dossier du projet cible, tout appartient au projet !
                        if not is_dedicated and target_project not in ("Memory Loop", "mLoop", "global", "All"):
                            # Filtre tolérant pour le fichier global
                            if not _match_project_alias(entry_proj, target_project):
                                continue

                        # Déduplication par empreinte timestamp + action + tokens
                        fp = f"{entry.get('timestamp')}_{entry.get('action')}_{entry.get('total_tokens_est')}_{entry.get('model')}"
                        if fp in seen_fingerprints:
                            continue
                        seen_fingerprints.add(fp)
                        entries.append(entry)
                    except Exception:
                        continue
        except Exception:
            pass

    # Calculs agrégés
    total_prompt_tokens = sum(e.get("prompt_tokens_est", 0) for e in entries)
    total_completion_tokens = sum(e.get("completion_tokens_est", 0) for e in entries)
    total_tokens = total_prompt_tokens + total_completion_tokens
    total_cost_usd = sum(e.get("cost_usd_est", 0.0) for e in entries)

    # Ventilation par modèle
    models_stats: Dict[str, Dict[str, Any]] = {}
    for e in entries:
        m_name = e.get("model", "unknown")
        if m_name not in models_stats:
            models_stats[m_name] = {"calls": 0, "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0, "cost_usd": 0.0}
        models_stats[m_name]["calls"] += 1
        models_stats[m_name]["prompt_tokens"] += e.get("prompt_tokens_est", 0)
        models_stats[m_name]["completion_tokens"] += e.get("completion_tokens_est", 0)
        models_stats[m_name]["total_tokens"] += e.get("total_tokens_est", 0)
        models_stats[m_name]["cost_usd"] += e.get("cost_usd_est", 0.0)

    for m in models_stats.values():
        m["cost_usd"] = round(m["cost_usd"], 4)

    # Ventilation par action
    actions_stats: Dict[str, Dict[str, Any]] = {}
    for e in entries:
        act = e.get("action", "unknown")
        if act not in actions_stats:
            actions_stats[act] = {"calls": 0, "tokens": 0, "cost_usd": 0.0}
        actions_stats[act]["calls"] += 1
        actions_stats[act]["tokens"] += e.get("total_tokens_est", 0)
        actions_stats[act]["cost_usd"] += e.get("cost_usd_est", 0.0)

    for a in actions_stats.values():
        a["cost_usd"] = round(a["cost_usd"], 4)

    entries.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    recent_interactions = entries[:30]

    return {
        "project": target_project,
        "total_calls": len(entries),
        "total_tokens": total_tokens,
        "prompt_tokens": total_prompt_tokens,
        "completion_tokens": total_completion_tokens,
        "total_cost_usd": round(total_cost_usd, 4),
        "models_breakdown": models_stats,
        "top_actions": sorted(actions_stats.items(), key=lambda x: x[1]["tokens"], reverse=True)[:8],
        "recent_interactions": recent_interactions,
    }


@app.get("/api/events")
def get_events(
    project: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500),
    event_type: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Retourne le journal live des événements récents depuis events.jsonl.
    """
    target_project = _resolve_project_canonical_name(project)
    p_root = _get_project_root(target_project)

    events_files: List[tuple[Path, bool]] = []

    if p_root != REPO_ROOT:
        p_events = p_root / "memory" / "events.jsonl"
        if p_events.exists():
            events_files.append((p_events, True))

    global_events = REPO_ROOT / "memory" / "events.jsonl"
    if global_events.exists():
        events_files.append((global_events, False))

    raw_events = []
    seen = set()

    for ef, is_dedicated in events_files:
        try:
            with open(ef, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        ev = json.loads(line)
                        if not is_dedicated and target_project not in ("Memory Loop", "mLoop", "global", "All"):
                            if not _match_project_alias(ev.get("project", ""), target_project):
                                continue

                        if event_type and event_type != "ALL":
                            if ev.get("event_type", "").upper() != event_type.upper():
                                continue

                        fp = f"{ev.get('timestamp')}_{ev.get('event_type')}_{ev.get('agent')}_{str(ev.get('details'))[:40]}"
                        if fp in seen:
                            continue
                        seen.add(fp)
                        raw_events.append(ev)
                    except Exception:
                        continue
        except Exception:
            pass

    raw_events.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    selected = raw_events[:limit]

    return {
        "project": target_project,
        "count": len(selected),
        "total_captured": len(raw_events),
        "events": selected,
    }


@app.get("/api/stories")
def get_stories(project: Optional[str] = None) -> Dict[str, Any]:
    """
    Scanne les User Stories du projet récursivement, extrait leur statut et inspecte leurs EvidencePacks.
    """
    target_project = _resolve_project_canonical_name(project)
    p_root = _get_project_root(target_project)

    backlog_root = p_root / "backlog"
    # Si racine mLoop, inclure aussi Projects/mLoop-Dashboard/backlog
    backlog_roots = [backlog_root]
    if target_project == "Memory Loop":
        dash_b = REPO_ROOT / "Projects" / "mLoop-Dashboard" / "backlog"
        if dash_b.exists():
            backlog_roots.append(dash_b)

    # 1. Scanner le sprint_backlog.md pour extraire la table de métadonnées officielles
    sprint_table: Dict[str, Dict[str, str]] = {}
    for b_root in backlog_roots:
        sb_file = b_root / "sprint_backlog.md"
        if sb_file.exists():
            try:
                sb_text = sb_file.read_text(encoding="utf-8", errors="ignore")
                for row in re.finditer(r"\|\s*([A-Za-z0-9_\-]+)\s*\|\s*([^|]+)\|\s*([^|]+)\|\s*([^|]*)\|", sb_text):
                    s_id = row.group(1).strip()
                    s_title = row.group(2).strip()
                    s_status = row.group(3).strip().upper()
                    s_jira = row.group(4).strip()
                    if s_id.lower() not in ("id", "---"):
                        sprint_table[s_id] = {
                            "title": s_title,
                            "status": s_status,
                            "jira_key": s_jira,
                        }
            except Exception:
                pass

    # 2. Indexer tous les EvidencePacks existants (recherche récursive)
    evidence_index: Dict[str, Path] = {}
    evidence_dirs = [p_root / "memory" / "evidence", REPO_ROOT / "memory" / "evidence"]
    for ev_dir in evidence_dirs:
        if ev_dir.exists():
            for ev_file in ev_dir.rglob("*.json"):
                stem = ev_file.stem.replace("_evidence", "")
                evidence_index[stem.lower()] = ev_file

    stories = []
    seen_ids = set()

    for b_root in backlog_roots:
        if not b_root.exists():
            continue
        # Scan récursif pour découvrir toutes les sous-catégories (01-reception, etc.)
        for md_file in b_root.rglob("*.md"):
            rel_parts = [p.lower() for p in md_file.relative_to(b_root).parts]
            if any(x in rel_parts for x in ("reviews", "gates", "archive", "templates", "tmp")):
                continue
            if md_file.name.lower() in ("sprint_backlog.md", "readme.md", "wayfinder_map.md"):
                continue
            try:
                content = md_file.read_text(encoding="utf-8", errors="ignore")
                story_id = md_file.stem
                title = md_file.stem
                status = "OPEN"
                stype = "Feature"
                layer = "vertical-slice"
                jira_key = ""
                epic_key = ""

                # Parser frontmatter YAML
                fm_match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
                if fm_match:
                    fm_text = fm_match.group(1)
                    for line in fm_text.splitlines():
                        if ":" in line:
                            k, v = line.split(":", 1)
                            k = k.strip().lower()
                            v = v.strip().strip("'\"")
                            if k == "id":
                                story_id = v
                            elif k == "title":
                                title = v
                            elif k == "status":
                                status = v.upper()
                            elif k == "type":
                                stype = v
                            elif k == "layer":
                                layer = v
                            elif k == "jira_key":
                                jira_key = v
                            elif k == "epic_key":
                                epic_key = v

                # Enrichir avec la table sprint_backlog.md si présente
                if story_id in sprint_table:
                    sb_info = sprint_table[story_id]
                    if sb_info.get("status") and status == "OPEN":
                        status = sb_info["status"]
                    if sb_info.get("jira_key") and not jira_key:
                        jira_key = sb_info["jira_key"]
                    if sb_info.get("title") and title == md_file.stem:
                        title = sb_info["title"]

                # Chercher titre H1 si non trouvé
                if title == md_file.stem:
                    h1_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
                    if h1_match:
                        title = h1_match.group(1).strip()

                if story_id in seen_ids:
                    continue
                seen_ids.add(story_id)

                # Vérifier présence de l'EvidencePack via l'index récursif
                ev_candidate = evidence_index.get(story_id.lower()) or evidence_index.get(md_file.stem.lower())
                has_evidence = ev_candidate is not None
                evidence_info = {}

                if has_evidence and ev_candidate:
                    try:
                        ev_data = json.loads(ev_candidate.read_text(encoding="utf-8"))
                        evidence_info = {
                            "risk_level": ev_data.get("highest_risk", "LOW"),
                            "total_items": len(ev_data.get("items", [])) or len(ev_data.get("facts_verified", [])),
                            "confidence_score": ev_data.get("root_score", 1.0),
                            "file_name": ev_candidate.name,
                        }
                    except Exception:
                        pass

                scenario_count = len(re.findall(r"(?im)^\s*(?:Scénario|Scenario)\s*:", content))

                rel_path = md_file.relative_to(p_root).as_posix() if p_root != REPO_ROOT else md_file.relative_to(REPO_ROOT).as_posix()

                stories.append({
                    "id": story_id,
                    "title": title,
                    "status": status,
                    "type": stype,
                    "layer": layer,
                    "jira_key": jira_key,
                    "epic_key": epic_key,
                    "file_path": rel_path,
                    "has_evidence": has_evidence,
                    "evidence_info": evidence_info,
                    "scenario_count": scenario_count,
                })
            except Exception:
                continue

    status_order = {
        "READY_FOR_DEV": 1,
        "IN_BUILD": 2,
        "IN_QA": 3,
        "IN_PLAN": 4,
        "IN_ANALYZE": 5,
        "OPEN": 6,
        "DONE": 7,
        "ACCEPTED": 8,
    }
    stories.sort(key=lambda x: (status_order.get(x["status"], 99), x["id"]))

    return {
        "project": target_project,
        "total_stories": len(stories),
        "stories": stories,
        "status_counts": {
            s: sum(1 for item in stories if item["status"] == s)
            for s in set(item["status"] for item in stories)
        }
    }


@app.get("/api/graph")
def get_graph_stats(project: Optional[str] = None) -> Dict[str, Any]:
    """
    Statistiques du graphe de connaissances (Ground Truth) et de l'hypergraphe.
    """
    target_project = _resolve_project_canonical_name(project)
    p_root = _get_project_root(target_project)

    graph_candidates = [
        p_root / "memory" / "knowledge_graph.json",
        p_root / "memory" / "hypergraph.json",
        p_root / "graphify-out" / "graph.json",
        REPO_ROOT / "memory" / "knowledge_graph.json",
        REPO_ROOT / "graphify-out" / "graph.json",
    ]

    nodes: List[Dict[str, Any]] = []
    edges: List[Dict[str, Any]] = []

    for gc in graph_candidates:
        if gc.exists():
            try:
                data = json.loads(gc.read_text(encoding="utf-8"))
                if "nodes" in data and isinstance(data["nodes"], list):
                    nodes.extend(data["nodes"])
                if "edges" in data and isinstance(data["edges"], list):
                    edges.extend(data["edges"])
                if nodes:
                    break
            except Exception:
                pass

    unique_nodes = {}
    for n in nodes:
        nid = n.get("id") or n.get("name")
        if nid and nid not in unique_nodes:
            unique_nodes[nid] = n

    node_types: Dict[str, int] = {}
    for n in unique_nodes.values():
        ntype = n.get("type") or n.get("layer") or n.get("label") or "Concept"
        node_types[ntype] = node_types.get(ntype, 0) + 1

    sample_nodes = list(unique_nodes.values())[:15]

    return {
        "project": target_project,
        "total_nodes": len(unique_nodes),
        "total_edges": len(edges),
        "node_types": node_types,
        "sample_nodes": sample_nodes,
    }


@app.get("/api/state")
def get_cycle_state(project: Optional[str] = None) -> Dict[str, Any]:
    """
    Retourne l'état d'avancement des 6 phases du cycle de vie logiciel mLoop pour le projet ciblé.
    """
    target_project = _resolve_project_canonical_name(project)
    p_root = _get_project_root(target_project)

    # 1. SOW : Présence de documents ingérés ou cadrage
    has_ingested = (p_root / "docs" / "00-ingested").exists() and any((p_root / "docs" / "00-ingested").iterdir())
    has_sow = has_ingested or (p_root / "docs" / "00-sow.md").exists()

    # 2. SPEC : Stories dans le backlog
    backlog_dir = p_root / "backlog"
    stories_list = list(backlog_dir.rglob("*.md")) if backlog_dir.exists() else []
    stories_count = len([s for s in stories_list if s.name.lower() not in ("sprint_backlog.md", "readme.md")])

    # 3. PLAN : Récits prêts au dev ou architecture définie
    has_arch = (p_root / "docs" / "01-architecture").exists()
    has_ready_stories = (p_root / "backlog" / "sprint_backlog.md").exists() or (stories_count > 0)

    # 5. VALIDATE : Présence de preuves d'EvidencePacks
    evidence_dir = p_root / "memory" / "evidence"
    has_validate = evidence_dir.exists() and any(evidence_dir.rglob("*.json"))

    phases = [
        {
            "key": "sow",
            "name": "1. SOW & Cadrage",
            "status": "COMPLETED" if has_sow else "PENDING",
            "details": f"{len(list((p_root / 'docs' / '00-ingested').glob('*.md')))} document(s) SSOT ingéré(s)" if has_ingested else "",
        },
        {
            "key": "spec",
            "name": "2. Spécification (Gherkin)",
            "status": "COMPLETED" if stories_count > 0 else "IN_PROGRESS",
            "details": f"{stories_count} User Story(ies) formalisée(s)",
        },
        {
            "key": "plan",
            "name": "3. Architecture & Contrats",
            "status": "COMPLETED" if (has_arch and has_ready_stories) else ("IN_PROGRESS" if has_ready_stories else "NOT_STARTED"),
            "details": "Récits cadrés et validés en Sprint Backlog" if has_ready_stories else "",
        },
        {
            "key": "build",
            "name": "4. Implémentation Isolée",
            "status": "NOT_STARTED",
            "details": "Handoff dev en cours",
        },
        {
            "key": "validate",
            "name": "5. Validation & EvidencePack",
            "status": "COMPLETED" if has_validate else "PENDING",
            "details": f"{len(list(evidence_dir.rglob('*.json')))} EvidencePack(s) certifié(s)" if has_validate else "",
        },
        {
            "key": "ship",
            "name": "6. Universal Dev Handoff",
            "status": "COMPLETED" if (has_validate and stories_count > 0) else "PENDING",
            "details": "Ready for Dev",
        },
    ]

    return {
        "project": target_project,
        "phases": phases,
        "pipeline": "SOW -> SPEC -> PLAN -> BUILD -> VALIDATE -> SHIP",
    }


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
