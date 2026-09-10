"""
Handlers Graph Intelligence : Integration de Graphify et du Graphe de Connaissances dans le pipeline mLoop (ADR-0204 et ADR-0363).
Fournit une passerelle deterministe pour l'interrogation conceptuelle, la synthese de voisinage k-hop et l'analyse de dependances architecturales.
"""
from __future__ import annotations

import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from src.cli import ZeroFluffConsole
from src.bridges.mcp_graphify import load_knowledge_graph

if TYPE_CHECKING:
    import argparse
    from src.state import LoopState


def _resolve_target_project(args: argparse.Namespace, state: Optional[LoopState]) -> Optional[str]:
    """Resout le projet cible : explicite --global, argument CLI, state actif ou DB."""
    if getattr(args, "global_graph", False):
        return "global"
    if getattr(args, "project", None):
        return args.project
    if state and getattr(state, "project_name", None):
        return state.project_name
    try:
        from src.loop_mem.db import get_active_project
        return get_active_project()
    except Exception:
        return None


def handle_graph_status(args: argparse.Namespace, state: Optional[LoopState], project_path: Optional[Path]) -> int:
    """Affiche les statistiques de sante et la fraicheur du graphe de connaissances."""
    target_project = _resolve_target_project(args, state) or "mLoop"
    ZeroFluffConsole.step_s1("Graphify Status", f"Diagnostic du graphe pour le perimetre : {target_project}")

    data, gpath = load_knowledge_graph(target_project)
    if not gpath or not gpath.exists():
        ZeroFluffConsole.warning(f"Aucun graphe de connaissances trouve pour le projet '{target_project}'.")
        return 0

    nodes = data.get("nodes", [])
    edges = data.get("links", data.get("edges", []))
    size_kb = gpath.stat().st_size / 1024
    mtime_str = datetime.datetime.fromtimestamp(gpath.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")

    print(f"\n  Source Graph      : {gpath}")
    print(f"  Perimetre Projet  : {target_project}")
    print(f"  Taille Fichier    : {size_kb:.1f} Ko")
    print(f"  Derniere Revision : {mtime_str}")
    print(f"  Noeuds Indexes    : {len(nodes)}")
    print(f"  Relations (Aretes): {len(edges)}\n")
    return 0


def _get_node_desc(node: dict) -> str:
    """Extrait la description d'un nœud qu'elle soit directe ou imbriquée dans properties."""
    desc = node.get("description")
    if not desc and isinstance(node.get("properties"), dict):
        desc = node["properties"].get("description") or node["properties"].get("summary")
    return desc or "Pas de description disponible."


def handle_graph_query(args: argparse.Namespace, state: Optional[LoopState], project_path: Optional[Path]) -> int:
    """Recherche ciblee de concepts/ADRs dans le graphe de connaissances (Agentic Token-Budgeted)."""
    query = getattr(args, "query", "").strip()
    if not query:
        ZeroFluffConsole.error("L'argument --query est obligatoire pour interroger le graphe.")
        return 1

    limit = getattr(args, "limit", 5) or 5
    target_project = _resolve_target_project(args, state) or "mLoop"
    ZeroFluffConsole.step_s1("Graphify Query", f"Recherche de '{query}' dans {target_project} (max {limit} resultats)")

    data, gpath = load_knowledge_graph(target_project)
    nodes = data.get("nodes", [])
    q_lower = query.lower()

    matches = []
    for n in nodes:
        nid = str(n.get("id", "")).lower()
        label = str(n.get("label", n.get("name", ""))).lower()
        desc = _get_node_desc(n).lower()
        if q_lower in nid or q_lower in label or q_lower in desc:
            matches.append(n)

    if not matches:
        print(f"\nAucun noeud correspondant a '{query}' dans le graphe ({gpath or 'Introuvable'}).\n")
        return 0

    print(f"\n### Resultats Graphify ({min(len(matches), limit)}/{len(matches)} noeuds correspondants) :\n")
    for mn in matches[:limit]:
        nid = mn.get("id") or mn.get("name", "N/A")
        label = mn.get("label") or mn.get("name") or nid
        desc = _get_node_desc(mn)
        print(f"* **{label}** (`{nid}`)")
        print(f"  - Description : {desc}\n")

    return 0


def handle_graph_explain(args: argparse.Namespace, state: Optional[LoopState], project_path: Optional[Path]) -> int:
    """Restitue la fiche d'un concept et ses voisins k-hop sous format Markdown compact (< 400 tokens)."""
    concept = getattr(args, "concept", "").strip()
    if not concept:
        ZeroFluffConsole.error("L'argument --concept est obligatoire.")
        return 1

    target_project = _resolve_target_project(args, state) or "mLoop"
    ZeroFluffConsole.step_s1("Graphify Explain", f"Explication du concept '{concept}' dans {target_project}")

    data, gpath = load_knowledge_graph(target_project)
    nodes = data.get("nodes", [])
    edges = data.get("links", data.get("edges", []))

    c_lower = concept.lower()
    target_node = None
    for n in nodes:
        nid = str(n.get("id", "")).lower()
        label = str(n.get("label", n.get("name", ""))).lower()
        if c_lower in nid or c_lower in label:
            target_node = n
            break

    if not target_node:
        print(f"\nNoeud '{concept}' introuvable dans le graphe ({gpath or 'Introuvable'}).\n")
        return 0

    nid = target_node.get("id") or target_node.get("name", concept)
    label = target_node.get("label") or target_node.get("name") or nid
    desc = _get_node_desc(target_node)

    out_neighbors = []
    in_neighbors = []
    for e in edges:
        s = str(e.get("source", ""))
        t = str(e.get("target", ""))
        lbl = e.get("label", "rel")
        if s.lower() == str(nid).lower():
            out_neighbors.append(f"-> [{lbl}] -> `{t}`")
        elif t.lower() == str(nid).lower():
            in_neighbors.append(f"<- [{lbl}] <- `{s}`")

    print(f"\n### Fiche Concept : {label} (`{nid}`)")
    print(f"- **Source Graph** : `{gpath}`")
    print(f"- **Description**  : {desc}\n")

    if out_neighbors:
        print("**Dependances Sortantes (1-Hop) :**")
        for rel in out_neighbors[:10]:
            print(f"  {rel}")
        print()

    if in_neighbors:
        print("**Dependances Entrantes (1-Hop) :**")
        for rel in in_neighbors[:10]:
            print(f"  {rel}")
        print()

    if not out_neighbors and not in_neighbors:
        print("*Noeud isole sans relations directes.*\n")

    return 0


def handle_graph_impact(args: argparse.Namespace, state: Optional[LoopState], project_path: Optional[Path]) -> int:
    """Calcule le rayon d'impact conceptuel et architectural (Blast Radius)."""
    target = getattr(args, "target", "").strip()
    if not target:
        ZeroFluffConsole.error("L'argument --target est obligatoire pour le calcul d'impact.")
        return 1

    target_project = _resolve_target_project(args, state) or "mLoop"
    ZeroFluffConsole.step_s1("Graphify Impact", f"Calcul de l'impact pour '{target}' dans {target_project}")

    data, gpath = load_knowledge_graph(target_project)
    try:
        from src.pipelines.blast_radius import BlastRadiusEngine
        engine = BlastRadiusEngine(project_root=Path("Projects") / (target_project or "mLoop"))
        engine.knowledge_graph = data
        blast_res = engine.compute_blast_radius(target)
        report = engine.format_markdown_report(blast_res)
        print(f"\n{report}\n")
        return 0
    except Exception as e:
        ZeroFluffConsole.warning(f"Moteur BlastRadius standard indisponible ({e}). Utilisation du fallback 1-hop.")
        setattr(args, "concept", target)
        return handle_graph_explain(args, state, project_path)