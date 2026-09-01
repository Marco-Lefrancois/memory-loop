"""Handlers Analyse : sync/wikifix, drill, confidence, rubber-duck, struct-check."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from src.cli import ZeroFluffConsole

if TYPE_CHECKING:
    import argparse
    from src.state import LoopState


def handle_sync(args: argparse.Namespace, state: LoopState, project_path: Path) -> int:
    """WikiFix + Synchronisation d'état du projet."""
    from src.pipelines.sync import run_sync
    run_sync(
        args.project,
        state,
        project_path,
        verbose=getattr(args, "verbose", False),
        incremental=getattr(args, "incremental", False)
    )
    return 0


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


def handle_struct_check(args: argparse.Namespace, state: LoopState, project_path: Path) -> int:
    """Gatekeeper structurel Read-Only — vérification typographique et stylistique (ADR-0338)."""
    from src.pipelines.struct_checker import StructCheckEngine, StructCheckReport

    strict = getattr(args, "strict", False)
    verbose = getattr(args, "verbose", False)
    target = getattr(args, "file", None)

    ZeroFluffConsole.info(f"Gatekeeper Structurel (struct-check) sur {args.project}...")
    engine = StructCheckEngine(project_path)

    # Résolution du/des fichier(s) cible(s) — même pattern que handle_rubber_duck
    files_to_check: list[Path] = []
    if target:
        raw_target = str(target).replace("\\", "/")
        p_str = str(project_path).replace("\\", "/")
        if raw_target.startswith(p_str):
            raw_target = raw_target[len(p_str):].lstrip("/")
        target_path = Path(raw_target) if Path(raw_target).is_absolute() else (project_path / raw_target)
        if target_path.exists():
            files_to_check.append(target_path)
        else:
            matches = list((project_path / "backlog" / "stories").rglob(f"*{raw_target}*"))
            if matches:
                files_to_check.append(matches[0])
            else:
                ZeroFluffConsole.error(f"Fichier cible introuvable : {target_path}")
                return 1
    else:
        stories_dir = project_path / "backlog" / "stories"
        if stories_dir.exists():
            files_to_check.extend(sorted(stories_dir.rglob("*.md")))

    if not files_to_check:
        ZeroFluffConsole.warning("Aucun récit trouvé à auditer.")
        return 0

    has_failures = False
    for f in files_to_check:
        report: StructCheckReport = engine.check_file(f, strict=strict)
        if not report.passed:
            has_failures = True

        # Affichage : toujours si échec ou si --verbose
        if verbose or not report.passed:
            status_icon = "❌" if not report.passed else "✅"
            ZeroFluffConsole.info(f"{status_icon} {f.name}")
            for v in report.violations:
                if v.severity == "BLOCKING":
                    ZeroFluffConsole.error(f"  [{v.check_id}] {v.message}")
                else:
                    ZeroFluffConsole.warning(f"  [{v.check_id}] {v.message}")
        elif report.passed:
            ZeroFluffConsole.success(f"✅ {f.name} — Conforme (struct-check)")

    if has_failures:
        ZeroFluffConsole.error("struct-check : violations BLOCKING détectées. Corriger avant rubber-duck.")
    else:
        ZeroFluffConsole.success("struct-check : tous les récits sont conformes structurellement.")

    return 1 if has_failures else 0


def handle_story_clean(args: argparse.Namespace, state: LoopState, project_path: Path) -> int:
    """Nettoie les blocs de traçabilité injectés dans les récits."""
    from src.pipelines.story_cleaner import run_story_clean
    run_story_clean(project_path)
    return 0


def handle_rubber_duck(args: argparse.Namespace, state: LoopState, project_path: Path) -> int:
    """Agent Sentinel (Rubber Duck) — revue contradictoire Read-Only."""
    from src.pipelines.rubber_duck import RubberDuckEngine
    from src.pipelines.state_machine import StateMachineEngine

    ZeroFluffConsole.info(f"Lancement de la Revue Sémantique de Contenu Sentinel (ADR-0326) sur {args.project}...")
    engine = RubberDuckEngine(project_path)
    fsm = StateMachineEngine(str(project_path))

    target = getattr(args, "file", None)
    files_to_check: list[Path] = []

    if target:
        raw_target = str(target).replace("\\", "/")
        p_str = str(project_path).replace("\\", "/")
        if raw_target.startswith(p_str):
            raw_target = raw_target[len(p_str):].lstrip("/")

        target_path = Path(raw_target) if Path(raw_target).is_absolute() else (project_path / raw_target)
        if target_path.exists():
            files_to_check.append(target_path)
        else:
            cand_story = project_path / "backlog" / "stories" / raw_target
            if cand_story.exists():
                files_to_check.append(cand_story)
            else:
                matches = list((project_path / "backlog" / "stories").rglob(f"*{raw_target}*"))
                if matches:
                    files_to_check.append(matches[0])
                else:
                    ZeroFluffConsole.error(f"Fichier cible introuvable : {target_path}")
                    return 1
    else:
        stories_dir = project_path / "backlog" / "stories"
        if stories_dir.exists():
            files_to_check.extend(list(stories_dir.rglob("*.md")))

    if not files_to_check:
        ZeroFluffConsole.warning("Aucun récit trouvé à auditer.")
        return 0

    has_blocking = False
    cached_count = 0
    for f in files_to_check:
        critique = engine.evaluate_file(f, force=bool(target))
        is_cached = critique.get("from_cache", False)

        if is_cached and not target and not getattr(args, "verbose", False):
            cached_count += 1
            if critique["blocking_issues"]:
                has_blocking = True
            continue

        ZeroFluffConsole.info(f"Audit de {f.name}{' (Cache Hit)' if is_cached else ''}...")
        report_file = engine.save_review_report(critique)

        if critique["blocking_issues"]:
            has_blocking = True
            if not is_cached:
                remaining_ttl = fsm.decrement_ttl(f)
                ZeroFluffConsole.error(
                    f"Rejet Rubber Duck ({len(critique['blocking_issues'])} problème(s) bloquant(s)) "
                    f"— TTL restant : {remaining_ttl}"
                )
                for issue in critique["blocking_issues"]:
                    print(f"  - [REJET] {issue}")
                try:
                    fsm.check_ttl(f)
                except Exception as ttl_err:
                    ZeroFluffConsole.error(str(ttl_err))
                engine.update_cache_mtime(f, critique)
            else:
                ZeroFluffConsole.error(
                    f"Rejet Rubber Duck ({len(critique['blocking_issues'])} problème(s) bloquant(s)) [Cached]"
                )
                for issue in critique["blocking_issues"]:
                    print(f"  - [REJET] {issue}")
        else:
            ZeroFluffConsole.success("Approbation Rubber Duck (Aucun problème bloquant).")

        if critique["non_blocking_issues"] and (not is_cached or target or getattr(args, "verbose", False)):
            ZeroFluffConsole.info(f"Points d'attention & résilience ({len(critique['non_blocking_issues'])} alerte(s)) :")
            for issue in critique["non_blocking_issues"]:
                print(f"  - [AVERTISSEMENT] {issue}")

        if "scores" in critique:
            scores = critique["scores"]
            print(f"\n📊 Évaluation Qualitative Avocat du Diable :")
            print(f"   • Discernement Métier : {scores.get('business_discernment')}/100")
            print(f"   • Cohérence Écosystème: {scores.get('ecosystem_coherence')}/100")
            print(f"   • Rigueur Technique   : {scores.get('technical_rigor')}/100")
            print(f"   • Trust Score Global  : {scores.get('overall_trust')}/100\n")

        suggest_patch = getattr(args, "suggest_patch", False)
        if (suggest_patch or target) and critique.get("remediation_patches"):
            ZeroFluffConsole.info(f"Propositions de Remédiation Gherkin ({len(critique['remediation_patches'])} patch(s)) :")
            for patch in critique["remediation_patches"]:
                print(f"\n  📝 [{patch.get('pillar_target')}] {patch.get('issue_addressed')}")
                for line in patch.get("suggested_gherkin", "").splitlines():
                    print(f"     {line}")
            print("")

        ZeroFluffConsole.success(f"Rapport enregistré sous : {report_file.relative_to(project_path)}")

    if cached_count > 0:
        ZeroFluffConsole.success(
            f"Audit Rubber Duck terminé : {cached_count}/{len(files_to_check)} récit(s) validés via cache mtime."
        )

    return 1 if has_blocking else 0


def handle_blast(args: argparse.Namespace, state: LoopState, project_path: Path) -> int:
    """Calcul du rayon d'impact (Blast Radius) d'un fichier ou composant."""
    from src.pipelines.blast_radius import BlastRadiusEngine

    target = getattr(args, "file", None) or getattr(args, "target", "")
    if not target:
        ZeroFluffConsole.error("Paramètre --file ou --target requis pour le calcul du Blast Radius.")
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
        path = project_path / target_file if (project_path / target_file).exists() else Path(target_file)

    if not path.exists():
        ZeroFluffConsole.error(f"Fichier introuvable : {path}")
        return 1

    chunker = MarkdownSemanticChunker()
    chunks = chunker.chunk_file(path)

    ZeroFluffConsole.success(f"Découpage sémantique réussi : {len(chunks)} chunks générés pour '{path.name}'.")
    for c in chunks:
        print(f"  [{c.chunk_id}] ({c.chunk_type.upper()}) {c.char_count} chars (~{c.token_estimate} tokens) | {c.header_path}")

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
        path = project_path / target_file if (project_path / target_file).exists() else Path(target_file)

    if not path.exists():
        ZeroFluffConsole.error(f"Fichier introuvable : {path}")
        return 1

    extractor = AgenticDocExtractor()
    report = extractor.process_file(path)

    ZeroFluffConsole.success(f"Extraction agentique terminée : {report.total_facts_extracted} faits/règles extraits ({report.total_chunks} chunks).")
    for f in report.facts:
        print(f"  [{f.fact_id}] ({f.category}) Confiance: {f.confidence_score:.2f} | {f.statement[:80]}...")

    return 0


def handle_eval_harvest(args: argparse.Namespace, state: LoopState, project_path: Path) -> int:
    """Moissonne les anomalies Sentinel / WikiFix pour créer des cas de test d'évaluation (ADR-0326)."""
    from src.pipelines.eval_harvester import AutoEvalHarvester

    harvester = AutoEvalHarvester(project_path)
    evals = harvester.harvest_from_wikifix()

    if not evals:
        ZeroFluffConsole.info("Aucune anomalie bloquante à moissonner dans le rapport d'audit.")
        return 0

    out_file = harvester.save_eval_pack(evals)
    ZeroFluffConsole.success(f"Moisson terminée : {len(evals)} cas d'évaluation consignés sous '{out_file.relative_to(project_path)}'.")
    for e in evals:
        print(f"  [{e.eval_id}] ({e.severity}) [{e.category}] {e.target_file} ➔ {e.issue_description[:70]}...")

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


def handle_supersession_sync(args: argparse.Namespace, state: LoopState, project_path: Path) -> int:
    """Synchronisation du registre de supersession des règles et décisions (ADR-0326)."""
    from src.loop_mem.supersession import MemorySupersessionEngine

    engine = MemorySupersessionEngine(project_path)
    ledger = engine.sync_ledger()

    ZeroFluffConsole.success(f"Registre de supersession synchronisé : {ledger['total_superseded']} élément(s) archivé(s).")
    for item_id, details in ledger.get("superseded_items", {}).items():
        print(f"  [SUPERSEDED] {item_id} ➔ {details['superseded_by']} ({details['reason']})")

    return 0


def handle_distill_invest(args: argparse.Namespace, state: LoopState, project_path: Path) -> int:
    """Génération du dataset d'instructions d'audit INVEST / Gherkin (ADR-0328)."""
    from src.pipelines.invest_dataset_distiller import InvestDatasetDistiller

    distiller = InvestDatasetDistiller(project_path)
    examples = distiller.generate_distilled_dataset()
    out_file = distiller.export_dataset_jsonl(examples)

    ZeroFluffConsole.success(f"Distillation terminée : {len(examples)} exemples générés sous '{out_file.relative_to(project_path)}'.")
    for ex in examples:
        print(f"  [{ex.example_id}] ({ex.category}) ➔ {ex.instruction[:60]}...")

    return 0


def handle_parent_resolve(args: argparse.Namespace, state: LoopState, project_path: Path) -> int:
    """Résolution du bloc parent pour un extrait sémantique (ADR-0328)."""
    from src.utils.parent_doc_resolver import ParentDocumentResolver
    # ... (omitted for brevity)
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
        ZeroFluffConsole.warning(f"Aucun hypergraphe trouvé sous {hypergraph_file}. Exécution préalable d'un sync...")
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
            
    # Requête générale sur les stats
    ZeroFluffConsole.section(f"Statistiques Hypergraphe — Projet : {args.project}")
    print(json.dumps(ka.to_dict()["stats"], indent=2))
    return 0





