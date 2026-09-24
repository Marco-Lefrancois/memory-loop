"""Handlers Architecture — Core (grill, to-tshirt, wayfinder, to-spec, to-tickets, graph-run)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

from src.cli import ZeroFluffConsole

if TYPE_CHECKING:
    import argparse
    from src.state import LoopState

def handle_grill(args: argparse.Namespace, state: LoopState, project_path: Path) -> int:
    """Session interactive Grill-with-Docs v2 (ADR-0320 / ADR-0389 / ADR-013)."""
    from src.pipelines.grill import execute_grill_cli

    return execute_grill_cli(args, state, project_path)


def handle_to_tshirt(
    args: argparse.Namespace, state: LoopState, project_path: Path
) -> int:
    """Génère un Dimensionnement Budgétaire (T-Shirt Size) d'avant-projet dans docs/01-architecture/."""
    from src.utils.blueprints import BlueprintLoader
    import datetime

    title = getattr(args, "title", None) or project_path.name
    date_iso = datetime.date.today().isoformat()

    out_dir = project_path / "docs" / "01-architecture"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"TSHIRT_SIZE_{project_path.name}.md"

    content = BlueprintLoader.render(
        "tshirt_size_template.md",
        {
            "NOM_DU_PROJET": title,
            "DATE_ISO": date_iso,
        },
    )
    content = content.replace("[NOM_DU_PROJET]", title).replace("[DATE_ISO]", date_iso)

    out_file.write_text(content, encoding="utf-8")
    ZeroFluffConsole.success(f"Dimensionnement Budgétaire (T-Shirt Size) généré : {out_file}")
    return 0


def handle_wayfinder(
    args: argparse.Namespace, state: LoopState, project_path: Path
) -> int:
    """Initialise, affiche la frontière ou résout un ticket Wayfinder (ADR-014)."""
    from src.pipelines.wayfinder import WayfinderEngine
    from src.pipelines.sync import run_sync

    wf = WayfinderEngine(project_path)
    action = getattr(args, "action", None) or "init-map"
    action = action.lower()

    if action in ("resolve", "resolve-ticket"):
        ticket_id = getattr(args, "ticket", None)
        decision = getattr(args, "decision", None)
        if not ticket_id or not decision:
            ZeroFluffConsole.error("Paramètres obligatoires : --ticket <ID> et --decision <TEXT>.")
            return 1
        ok = wf.resolve_ticket(ticket_id, decision)
        if ok:
            ZeroFluffConsole.success(f"Ticket Wayfinder {ticket_id} résolu : {decision}")
            run_sync(args.project, state, project_path)
            return 0
        ZeroFluffConsole.error(f"Échec de résolution : ticket {ticket_id} introuvable.")
        return 1

    if action == "frontier":
        frontier = wf.get_frontier()
        ZeroFluffConsole.info(f"=== Frontière de Décision Wayfinder ({project_path.name}) ===")
        if not frontier:
            ZeroFluffConsole.success("Toutes les décisions de la frontière sont levées.")
        for t in frontier:
            ZeroFluffConsole.info(f"  • [{t['id']}] ({t['kind']}) {t['title']} — {t['description']}")
        return 0

    title = getattr(args, "title", None) or getattr(args, "initiative", "Initiative Principale")
    goal = getattr(args, "goal", None)
    map_path = wf.init_map(title, goal=goal)
    ZeroFluffConsole.success(f"Carte Wayfinder initialisée/mise à jour : {map_path}")
    run_sync(args.project, state, project_path)
    return 0


def handle_to_spec(
    args: argparse.Namespace, state: LoopState, project_path: Path
) -> int:
    """Génère une spécification technique depuis le contexte projet."""
    from src.pipelines.ticket_pipeline import TicketPipelineEngine

    tp = TicketPipelineEngine(project_path)
    spec_path = tp.create_spec(
        title=getattr(args, "title", "Spécification Générale"),
        overview="Spécification générée via mLoop to-spec pipeline.",
        scope="Composants principaux",
        architecture="Source de vérité architecturale",
        acceptance_criteria="Scénarios Gherkin de validation",
    )
    ZeroFluffConsole.success(f"Spécification générée : {spec_path}")
    return 0


def handle_to_tickets(
    args: argparse.Namespace, state: LoopState, project_path: Path
) -> int:
    """Découpe en tickets verticaux depuis l'architecture."""
    from src.pipelines.ticket_pipeline import TicketPipelineEngine
    from src.pipelines.sync import run_sync

    tp = TicketPipelineEngine(project_path)
    ZeroFluffConsole.info("Découpage des tickets verticaux...")
    res = tp.decompose_to_tickets(
        project_path / "docs" / "01-architecture",
        [
            {
                "title": "Initialisation du module principal",
                "type": "BE",
                "blocked_by": [],
            }
        ],
    )
    ZeroFluffConsole.success(
        f"Stories générées dans backlog/stories ({len(res)} récits)."
    )
    run_sync(args.project, state, project_path)
    return 0


def handle_graph_run(
    args: argparse.Namespace, state: LoopState, project_path: Path
) -> int:
    """Exécution Graph Engineering (DAG Multi-Agents)."""
    from src.pipelines.graph_router import (
        GraphRouter,
        TaskNode,
        NodeCategory,
        RiskLevel,
    )
    from src.pipelines.evidence import EvidencePack, EvidenceItem
    from src.pipelines.wayfinder import WayfinderEngine

    initiative_title = getattr(args, "title", "Initiative_Principale")
    ZeroFluffConsole.info(
        f"Lancement de l'exécution Graph Engineering (DAG Multi-Agents) pour : {args.project}"
    )

    wf = WayfinderEngine(project_path)
    if wf.map_file.exists():
        router = wf.to_dag(initiative_name=initiative_title)
        ZeroFluffConsole.info("Carte Wayfinder détectée. Chargement du DAG dynamique.")
    else:
        router = GraphRouter(
            initiative_name=initiative_title, project_dir=str(project_path)
        )
        n1 = TaskNode(
            id="node_spec",
            role="orchestrator",
            description="Spécification des besoins & Rôles",
            blocked_by=[],
            category=NodeCategory.LLM_AGENT,
            risk_level=RiskLevel.LOW,
        )
        n2 = TaskNode(
            id="node_plan_be",
            role="plan",
            description="Plan d'architecture Back-End & Modèle",
            blocked_by=["node_spec"],
            category=NodeCategory.LLM_AGENT,
            risk_level=RiskLevel.HIGH,
        )
        n3 = TaskNode(
            id="node_plan_fe",
            role="plan",
            description="Plan d'architecture Front-End & UI",
            blocked_by=["node_spec"],
            category=NodeCategory.LLM_AGENT,
            risk_level=RiskLevel.MEDIUM,
        )
        n4 = TaskNode(
            id="node_reducer",
            role="reducer",
            description="Nœud Déterministe : Fusion & Déduplication des EvidencePacks (Barrier/Reduce)",
            blocked_by=["node_plan_be", "node_plan_fe"],
            category=NodeCategory.DETERMINISTIC_CODE,
            risk_level=RiskLevel.LOW,
        )
        for n in [n1, n2, n3, n4]:
            router.add_node(n)

    from src.pipelines.evidence import EvidencePack, EvidenceItem, EvidenceReducer

    if getattr(args, "resume", False):
        if router.load_checkpoint():
            ZeroFluffConsole.success(
                "Checkpoint d'exécution chargé. Les nœuds déjà complétés seront sautés."
            )

    # Exécution orchestrée du DAG avec transport des EvidencePacks
    if (
        router.nodes.get("node_spec")
        and router.nodes["node_spec"].status != "completed"
    ):
        if router.mark_running("node_spec"):
            pack_spec = EvidencePack(
                source_node="node_spec", initiative_name=initiative_title
            )
            pack_spec.add_item(
                EvidenceItem(
                    evidence_id="SPEC-01",
                    target_file="docs/01-architecture/initiative.md",
                    line_range=(1, 20),
                    rule_ref="GENERAL",
                    confidence=1.0,
                    risk_level="LOW",
                    description=f"Spécification pour {initiative_title}",
                    evidence_payload={"scope": initiative_title},
                )
            )
            router.mark_completed("node_spec", evidence_pack=pack_spec)

    packs_for_reducer = []
    for nid, role, target_file, rule_ref in [
        ("node_plan_be", "plan", "src/api/routes.py", "API_ROUTE"),
        ("node_plan_fe", "plan", "src/ui/views.tsx", "API_ROUTE"),
    ]:
        if router.nodes.get(nid) and router.nodes[nid].status != "completed":
            if router.mark_running(nid):
                pack = EvidencePack(source_node=nid, initiative_name=initiative_title)
                pack.add_item(
                    EvidenceItem(
                        evidence_id=f"{nid}-EV",
                        target_file=target_file,
                        line_range=(1, 30),
                        rule_ref=rule_ref,
                        confidence=0.95,
                        risk_level="LOW",
                        description=f"Plan architectural généré par {nid}",
                        evidence_payload={
                            "route": "/api/v1/onetrust/consent",
                            "method": "POST",
                            "fields": ["consent_id", "status"],
                        },
                    )
                )
                router.mark_completed(nid, evidence_pack=pack)
                packs_for_reducer.append(pack)
        elif router.nodes.get(nid) and router.nodes[nid].evidence_pack:
            packs_for_reducer.append(router.nodes[nid].evidence_pack)

    if (
        router.nodes.get("node_reducer")
        and router.nodes["node_reducer"].status != "completed"
    ):
        if router.mark_running("node_reducer"):
            merged_pack = EvidenceReducer.merge_and_deduplicate(
                packs_for_reducer, target_node_name="node_reducer"
            )
            router.mark_completed("node_reducer", evidence_pack=merged_pack)

    summary = router.get_summary()
    ZeroFluffConsole.success(
        f"DAG Execution Summary: {summary['completed']}/{summary['total_nodes']} complété(s)."
    )
    ZeroFluffConsole.info("Événements Herdr diffusés vers memory/herdr_events.jsonl.")
    return 0 if router.is_completed() else 1
