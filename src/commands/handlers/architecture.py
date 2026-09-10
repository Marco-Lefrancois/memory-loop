"""Handlers Architecture : grill, wayfinder, to-spec, to-tickets, graph-run, deepen, diagnose."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

from src.cli import ZeroFluffConsole

if TYPE_CHECKING:
    import argparse
    from src.state import LoopState


def handle_grill(args: argparse.Namespace, state: LoopState, project_path: Path) -> int:
    """Session interactive Grill-with-Docs et génération d'ADR."""
    from src.pipelines.grill_engine import GrillEngine
    from src.pipelines.sync import run_sync

    ge = GrillEngine(project_path)
    search_term = (
        getattr(args, "query", None)
        or getattr(args, "title", None)
        or getattr(args, "story", None)
    )
    if search_term and search_term != "Décision d'Architecture":
        ge.perform_fact_search(str(search_term))

    # BUG-GRILL-02 : ne générer un ADR QUE si un contenu de décision réel est fourni
    # (--context ou --decision). Un simple marquage de story (--title + --story) ne doit
    # pas créer d'ADR parasite faisant doublon avec des décisions d'architecture existantes.
    ctx = getattr(args, "context", None)
    dec = getattr(args, "decision", None)
    if ctx or dec:
        adr_path = ge.record_adr(
            title=getattr(args, "title", None) or "Décision d'Architecture",
            context=ctx or "Contexte issu d'une session de grilling interactive.",
            decision=dec or "Décision arbitrée conjointement.",
            positives=getattr(args, "positives", None)
            or "Clarification du domaine et réduction de l'ambiguïté.",
            negatives=getattr(args, "negatives", None)
            or "Obligation d'alignement strict.",
        )
        ZeroFluffConsole.success(f"ADR généré avec succès : {adr_path}")
    else:
        ZeroFluffConsole.info(
            "Aucun contenu de décision (--context/--decision) fourni : marquage de story sans génération d'ADR."
        )

    if getattr(args, "story", None):
        if ge.mark_story_grilled(args.story):
            ZeroFluffConsole.success(
                f"Récit {args.story} marqué comme GRILLED (statut: READY_FOR_GROOMING)."
            )
        else:
            ZeroFluffConsole.warning(
                f"Récit {args.story} introuvable dans backlog/stories ou sprint_backlog.md."
            )
    run_sync(args.project, state, project_path)
    return 0


def handle_wayfinder(
    args: argparse.Namespace, state: LoopState, project_path: Path
) -> int:
    """Initialise ou met à jour la carte Wayfinder."""
    from src.pipelines.wayfinder import WayfinderEngine
    from src.pipelines.sync import run_sync

    wf = WayfinderEngine(project_path)
    map_path = wf.init_map(getattr(args, "title", "Initiative Principale"))
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


def handle_deepen(
    args: argparse.Namespace, state: LoopState, project_path: Path
) -> int:
    """Génère un rapport HTML de profondeur d'architecture."""
    from src.pipelines.arch_analyzer import ArchAnalyzerEngine

    aa = ArchAnalyzerEngine(project_path)
    report_path = aa.generate_html_report()
    ZeroFluffConsole.success(
        f"Rapport HTML de profondeur d'architecture généré : {report_path}"
    )
    return 0


def handle_diagnose(
    args: argparse.Namespace, state: LoopState, project_path: Path
) -> int:
    """Génère un harnais de reproduction déterministe."""
    from src.pipelines.diagnostics import DiagnosticEngine

    de = DiagnosticEngine(project_path)
    harness_path = de.create_harness(
        symptom_name=getattr(args, "symptom", "Symptome_Inconnu"),
        symptom_description="Régression ou anomalie d'état constatée.",
        command_invocation="python src/swarm.py confidence --file ...",
        initial_output="ECHEC / SIGNAL ROUGE",
    )
    ZeroFluffConsole.success(
        f"Harnais de reproduction déterministe généré : {harness_path}"
    )
    return 0


def handle_goal_cascade(
    args: argparse.Namespace, state: LoopState, project_path: Path
) -> int:
    """Alignement stratégique et Goal-Cascading (Wayfinder -> Epics -> Stories)."""
    from src.pipelines.goal_cascade import run_goal_cascade

    report = run_goal_cascade(project_path)
    ZeroFluffConsole.success(
        f"Goal-Cascading : {report['aligned_stories']}/{report['total_stories']} récit(s) alignés (Score: {report['alignment_score']}%)."
    )
    return 0


def handle_to_sow(
    args: argparse.Namespace, state: LoopState, project_path: Path
) -> int:
    """Génère un Énoncé des Travaux (SOW) et Évaluation Budgétaire depuis le gabarit officiel."""
    from src.pipelines.sow_engine import SOWEngine
    from src.pipelines.sync import run_sync

    title = getattr(args, "title", None)
    size = getattr(args, "size", None) or "M"

    engine = SOWEngine(project_path)
    sow_path = engine.generate_sow(title=title, target_size=size)
    ZeroFluffConsole.success(f"Énoncé des Travaux (SOW) généré : {sow_path}")

    # ADR-0331 §2.2 Règle #3 : Interdiction Formelle des Libellés Génériques
    granularity_violations = engine.validate_task_granularity(sow_path)
    if granularity_violations:
        ZeroFluffConsole.warning(
            f"[ADR-0331] {len(granularity_violations)} libellé(s) générique(s) "
            f"détecté(s) dans le tableau de chiffrage détaillé :"
        )
        for v in granularity_violations:
            ZeroFluffConsole.warning(f"  - {v}")

    return 0
