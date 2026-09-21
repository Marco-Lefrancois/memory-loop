"""Handlers Analyse — Core (drill, confidence, blast, chunk, agentic-extract, token-tracker, etc.)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

from src.cli import ZeroFluffConsole

if TYPE_CHECKING:
    import argparse
    from src.state import LoopState


def handle_drill(args: argparse.Namespace, state: LoopState, project_path: Path) -> int:
    """Drill d'analyse approfondie."""
    from src.pipelines.drill import run_drill

    run_drill(args.project, state, project_path)
    return 0


def handle_confidence(args: argparse.Namespace, state: LoopState, project_path: Path) -> int:
    """Évalue le score de confiance d'un fichier."""
    from src.bridges.confidence_gate import evaluate_confidence

    result = evaluate_confidence(args.file)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 1 if result["status"] == "REJECT" else 0


def handle_blast(args: argparse.Namespace, state: LoopState, project_path: Path) -> int:
    """Calcul du rayon d'impact (Blast Radius) d'un fichier ou composant."""
    from src.pipelines.blast_radius import BlastRadiusEngine

    target = getattr(args, "file", None) or getattr(args, "target", "")
    if not target:
        ZeroFluffConsole.error(
            "Paramètre --file ou --target requis pour le calcul du Blast Radius."
        )
        return 1

    engine = BlastRadiusEngine(project_path)
    res = engine.compute_blast_radius(target)
    report = engine.format_markdown_report(res)
    print("\n" + report + "\n")
    return 0


def handle_chunk(args: argparse.Namespace, state: LoopState, project_path: Path) -> int:
    """Découpage sémantique d'un fichier Markdown (ADR-0323)."""
    from src.utils.semantic_chunker import MarkdownSemanticChunker

    target_file = getattr(args, "file", None)
    if not target_file:
        ZeroFluffConsole.error("Paramètre --file requis pour le découpage sémantique.")
        return 1

    path = Path(target_file)
    if not path.is_absolute() and project_path:
        path = (
            project_path / target_file
            if (project_path / target_file).exists()
            else Path(target_file)
        )

    if not path.exists():
        ZeroFluffConsole.error(f"Fichier introuvable : {path}")
        return 1

    chunker = MarkdownSemanticChunker()
    chunks = chunker.chunk_file(path)

    ZeroFluffConsole.success(
        f"Découpage sémantique réussi : {len(chunks)} chunks générés pour '{path.name}'."
    )
    for c in chunks:
        print(
            f"  [{c.chunk_id}] ({c.chunk_type.upper()}) {c.char_count} chars (~{c.token_estimate} tokens) | {c.header_path}"
        )

    return 0


def handle_agentic_extract(args: argparse.Namespace, state: LoopState, project_path: Path) -> int:
    """Extraction documentaire agentique multi-passes (ADR-0323)."""
    from src.pipelines.agentic_doc_extractor import AgenticDocExtractor

    target_file = getattr(args, "file", None)
    if not target_file:
        ZeroFluffConsole.error("Paramètre --file requis pour l'extraction agentique.")
        return 1

    path = Path(target_file)
    if not path.is_absolute() and project_path:
        path = (
            project_path / target_file
            if (project_path / target_file).exists()
            else Path(target_file)
        )

    if not path.exists():
        ZeroFluffConsole.error(f"Fichier introuvable : {path}")
        return 1

    extractor = AgenticDocExtractor()
    report = extractor.process_file(path)

    ZeroFluffConsole.success(
        f"Extraction agentique terminée : {report.total_facts_extracted} faits/règles extraits ({report.total_chunks} chunks)."
    )
    for f in report.facts:
        print(
            f"  [{f.fact_id}] ({f.category}) Confiance: {f.confidence_score:.2f} | {f.statement[:80]}..."
        )

    return 0


def handle_context_watch(args: argparse.Namespace, state: LoopState, project_path: Path) -> int:
    """Surveillance de l'occupation contextuelle et alerte Dumb-Zone (ADR-0326)."""
    from src.utils.context_monitor import ContextMonitor

    monitor = ContextMonitor()
    report = monitor.evaluate_project_state(project_path)
    gauge_str = monitor.render_ascii_gauge(report)

    print("\n" + gauge_str + "\n")
    return 1 if report.zone == "DUMB_ZONE" else 0


def handle_token_tracker(args: argparse.Namespace, state: LoopState, project_path: Path) -> int:
    """Audit de la consommation de tokens et de coûts par interaction, projet et clé (ADR-0329)."""
    from datetime import datetime, timezone
    from src.utils.token_ledger import TokenLedger

    project_name = getattr(args, "project", None) or getattr(state, "project_name", None)
    if project_name in ("default", "Global", ""):
        project_name = None

    date_filter = None
    if getattr(args, "today", False):
        date_filter = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    elif getattr(args, "date", None):
        date_filter = args.date

    top_n = getattr(args, "top", 10) or 10

    report = TokenLedger.generate_report(
        project_name=project_name,
        date_filter=date_filter,
        top_n=top_n,
    )
    print("\n" + report + "\n")
    return 0


def handle_distill_invest(args: argparse.Namespace, state: LoopState, project_path: Path) -> int:
    """Génération du dataset d'instructions d'audit INVEST / Gherkin (ADR-0328)."""
    from src.pipelines.invest_dataset_distiller import InvestDatasetDistiller

    distiller = InvestDatasetDistiller(project_path)
    examples = distiller.generate_distilled_dataset()
    out_file = distiller.export_dataset_jsonl(examples)

    ZeroFluffConsole.success(
        f"Distillation terminée : {len(examples)} exemples générés sous '{out_file.relative_to(project_path)}'."
    )
    for ex in examples:
        print(f"  [{ex.example_id}] ({ex.category}) ➔ {ex.instruction[:60]}...")

    return 0


def handle_parent_resolve(args: argparse.Namespace, state: LoopState, project_path: Path) -> int:
    """Résolution du bloc parent pour un extrait sémantique (ADR-0328)."""
    from src.utils.parent_doc_resolver import ParentDocumentResolver

    return 0


def handle_story_clean(args: argparse.Namespace, state: LoopState, project_path: Path) -> int:
    """Nettoyer les sections de mémoire temporaires."""
    from src.pipelines.story_cleaner import run_story_clean

    run_story_clean(project_path, verbose=getattr(args, "verbose", False))
    return 0


def handle_export_obsidian(args: argparse.Namespace, state: LoopState, project_path: Path) -> int:
    """Exporte l'hypergraphe du projet sous forme de coffre Obsidian avec wikilinks (ADR-0337 / ADR-0343)."""
    from src.core.hypergraph_engine import HypergraphKnowledgeAbstract

    hypergraph_file = project_path / "memory" / "hypergraph.json"
    if not hypergraph_file.exists():
        ZeroFluffConsole.warning(
            f"Aucun hypergraphe trouvé sous {hypergraph_file}. Exécution préalable d'un sync..."
        )
        from src.pipelines.sync import sync_hypergraph

        sync_hypergraph(args.project, project_path, verbose=True)

    if not hypergraph_file.exists():
        ZeroFluffConsole.error("Impossible de charger ou générer l'hypergraphe.")
        return 1

    ka = HypergraphKnowledgeAbstract.load_from_file(hypergraph_file)
    out_dir_arg = getattr(args, "out", None) or "docs/07-obsidian-vault"
    out_dir = Path(out_dir_arg) if Path(out_dir_arg).is_absolute() else (project_path / out_dir_arg)

    ka.export_obsidian_vault(out_dir)
    ZeroFluffConsole.success(f"✓ Coffre Obsidian exporté avec succès dans : {out_dir}")
    ZeroFluffConsole.info(f" • {len(ka.nodes)} fiches d'entités créées sous Entities/")
    ZeroFluffConsole.info(f" • {len(ka.edges)} fiches d'hyper-arêtes créées sous Stories/")
    return 0


def handle_hyper_query(args: argparse.Namespace, state: LoopState, project_path: Path) -> int:
    """Interroge l'hypergraphe pour une User Story ou un concept spécifique (ADR-0343)."""
    from src.core.hypergraph_engine import HypergraphKnowledgeAbstract

    hypergraph_file = project_path / "memory" / "hypergraph.json"
    if not hypergraph_file.exists():
        from src.pipelines.sync import sync_hypergraph

        sync_hypergraph(args.project, project_path, verbose=False)

    if not hypergraph_file.exists():
        ZeroFluffConsole.error("Hypergraphe introuvable.")
        return 1

    ka = HypergraphKnowledgeAbstract.load_from_file(hypergraph_file)
    story_id = getattr(args, "story", None)
    if story_id:
        unit = ka.get_hyper_story_unit(story_id)
        if unit:
            ZeroFluffConsole.section(f"Hyper-Story Unit : {story_id}")
            print(json.dumps(unit, indent=2, ensure_ascii=False))
            return 0
        else:
            ZeroFluffConsole.warning(f"Récit '{story_id}' introuvable dans l'hypergraphe.")
            return 1

    ZeroFluffConsole.section(f"Statistiques Hypergraphe — Projet : {args.project}")
    print(json.dumps(ka.to_dict()["stats"], indent=2))
    return 0
