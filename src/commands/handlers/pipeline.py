"""Handlers Pipeline : ingest, research, crawl, teach, memory-hygiene."""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from src.cli import ZeroFluffConsole

if TYPE_CHECKING:
    import argparse
    from src.state import LoopState


def handle_ingest(args: argparse.Namespace, state: LoopState, project_path: Path) -> int:
    """Ingestion documentaire vers Markdown normalisé."""
    from src.pipelines.ingest import run_ingest
    run_ingest(args.project, state, project_path)
    return 0


def handle_research(args: argparse.Namespace, state: LoopState, project_path: Path) -> int:
    """Session de recherche automatisée."""
    from src.pipelines.research_pipeline import run_research
    run_research(
        args.project, state, project_path,
        query=getattr(args, "query", ""),
        explicit_url=getattr(args, "url", None),
    )
    return 0


def handle_crawl(args: argparse.Namespace, state: LoopState, project_path: Path) -> int:
    """Crawl d'une URL externe ou du backlog avec Smart Discovery & Caching."""
    from src.pipelines.crawler import WebCrawlerAgent
    try:
        include_paths = [args.include] if getattr(args, "include", None) else None
        exclude_paths = [args.exclude] if getattr(args, "exclude", None) else None

        crawler = WebCrawlerAgent(
            max_age=getattr(args, "max_age", None),
            max_depth=getattr(args, "max_depth", 0),
            include_paths=include_paths,
            exclude_paths=exclude_paths,
            allow_subdomains=getattr(args, "allow_subdomains", False),
            llms_txt=not getattr(args, "no_llms_txt", False),
            ignore_query_parameters=getattr(args, "ignore_query", False),
            json_schema_path=getattr(args, "json_schema", None),
            all_sources=getattr(args, "all_sources", False),
            render_js=getattr(args, "render_js", False),
            github_tree=not getattr(args, "no_github_tree", False),
        )
        crawler.execute(state, explicit_url=getattr(args, "url", None))
        ZeroFluffConsole.success("Crawl terminé.")
        return 0
    except Exception as e:
        ZeroFluffConsole.error(f"Erreur lors du crawl: {e}")
        return 1


def handle_teach(args: argparse.Namespace, state: LoopState, project_path: Path) -> int:
    """Pipeline d'apprentissage."""
    from src.pipelines.teach_pipeline import run_teach
    run_teach(args.project, state, project_path)
    return 0


def handle_memory_hygiene(args: argparse.Namespace, state: LoopState, project_path: Path) -> int:
    """Balayage de confiance de la mémoire vive."""
    from src.pipelines.memory_hygiene import MemoryHygieneAgent
    agent = MemoryHygieneAgent()
    agent.execute(state)
    return 0


def handle_update_story(args: argparse.Namespace, state: LoopState, project_path: Path) -> int:
    """Mise à jour d'une section H2 spécifique d'un récit (AST-Aware)."""
    from src.pipelines.story_editor import StoryEditorEngine
    editor = StoryEditorEngine(project_path)
    success = editor.update_section(args.story, args.section, args.content)
    return 0 if success else 1


def handle_dream(args: argparse.Namespace, state: LoopState, project_path: Path) -> int:
    """Consolidation nocturne et compression mémorielle (Sleep-Wake)."""
    from src.pipelines.dream_consolidator import run_dream_consolidation
    res = run_dream_consolidation(project_path)
    ZeroFluffConsole.success(f"Consolidation terminée [{res['status']}] : {res['evidence_packs_audited']} pack(s) audité(s) en {res['consolidation_duration_ms']} ms.")
    return 0

