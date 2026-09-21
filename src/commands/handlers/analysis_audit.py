"""Handlers Analyse — Audit (rubber-duck, struct-check, eval-harvest, dossier-init)."""

from __future__ import annotations

import re
import datetime
import json
from pathlib import Path
from typing import TYPE_CHECKING

from src.cli import ZeroFluffConsole
from src.utils.blueprints import BlueprintLoader

if TYPE_CHECKING:
    import argparse
    from src.state import LoopState


def handle_struct_check(args: argparse.Namespace, state: LoopState, project_path: Path) -> int:
    """Gatekeeper structurel Read-Only — vérification typographique et stylistique (ADR-0338)."""
    from src.pipelines.struct_checker import StructCheckEngine, StructCheckReport

    strict = getattr(args, "strict", False)
    verbose = getattr(args, "verbose", False)
    target = getattr(args, "file", None)
    ZeroFluffConsole.info(f"Gatekeeper Structurel (struct-check) sur {args.project}...")
    engine = StructCheckEngine(project_path)
    files_to_check: list[Path] = []
    if target:
        raw_target = str(target).replace("\\", "/")
        p_str = str(project_path).replace("\\", "/")
        if raw_target.startswith(p_str):
            raw_target = raw_target[len(p_str) :].lstrip("/")
        target_path = (
            Path(raw_target) if Path(raw_target).is_absolute() else (project_path / raw_target)
        )
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
        ZeroFluffConsole.error(
            "struct-check : violations BLOCKING détectées. Corriger avant rubber-duck."
        )
    else:
        ZeroFluffConsole.success("struct-check : tous les récits sont conformes structurellement.")

    return 1 if has_failures else 0


def handle_rubber_duck(args: argparse.Namespace, state: LoopState, project_path: Path) -> int:
    """Agent Sentinel (Rubber Duck) — revue contradictoire Read-Only."""
    from src.pipelines.rubber_duck import RubberDuckEngine
    from src.pipelines.state_machine import StateMachineEngine

    ZeroFluffConsole.info(
        f"Lancement de la Revue Sémantique de Contenu Sentinel (ADR-0326) sur {args.project}..."
    )
    engine = RubberDuckEngine(project_path)
    fsm = StateMachineEngine(str(project_path))
    target = getattr(args, "file", None)
    files_to_check: list[Path] = []

    if target:
        raw_target = str(target).replace("\\", "/")
        p_str = str(project_path).replace("\\", "/")
        if raw_target.startswith(p_str):
            raw_target = raw_target[len(p_str) :].lstrip("/")

        target_path = (
            Path(raw_target) if Path(raw_target).is_absolute() else (project_path / raw_target)
        )
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

        if critique["non_blocking_issues"] and (
            not is_cached or target or getattr(args, "verbose", False)
        ):
            ZeroFluffConsole.info(
                f"Points d'attention & résilience ({len(critique['non_blocking_issues'])} alerte(s)) :"
            )
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
            ZeroFluffConsole.info(
                f"Propositions de Remédiation Gherkin ({len(critique['remediation_patches'])} patch(s)) :"
            )
            for patch in critique["remediation_patches"]:
                print(f"\n  📝 [{patch.get('pillar_target')}] {patch.get('issue_addressed')}")
                for line in patch.get("suggested_gherkin", "").splitlines():
                    print(f"     {line}")
            print("")

        ZeroFluffConsole.success(
            f"Rapport enregistré sous : {report_file.relative_to(project_path)}"
        )

    if cached_count > 0:
        ZeroFluffConsole.success(
            f"Audit Rubber Duck terminé : {cached_count}/{len(files_to_check)} récit(s) validés via cache mtime."
        )

    return 1 if has_blocking else 0


def handle_eval_harvest(args: argparse.Namespace, state: LoopState, project_path: Path) -> int:
    """Moissonne les anomalies Sentinel / WikiFix pour créer des cas de test d'évaluation (ADR-0326)."""
    from src.pipelines.eval_harvester import AutoEvalHarvester

    harvester = AutoEvalHarvester(project_path)
    evals = harvester.harvest_from_wikifix()

    if not evals:
        ZeroFluffConsole.info("Aucune anomalie bloquante à moissonner dans le rapport d'audit.")
        return 0

    out_file = harvester.save_eval_pack(evals)
    ZeroFluffConsole.success(
        f"Moisson terminée : {len(evals)} cas d'évaluation consignés sous '{out_file.relative_to(project_path)}'."
    )
    for e in evals:
        print(
            f"  [{e.eval_id}] ({e.severity}) [{e.category}] {e.target_file} ➔ {e.issue_description[:70]}..."
        )

    return 0


def handle_dossier_init(args: argparse.Namespace, state: LoopState, project_path: Path) -> int:
    """Initialise le Dossier de Preuves Documentaires (_fact_dossier.md) pour un récit."""
    from src.utils.lexicon_resolver import SemanticLexiconResolver

    story_query = getattr(args, "story", None)
    force = getattr(args, "force", False)

    if not story_query:
        ZeroFluffConsole.error("Le paramètre --story <STORY_ID> est obligatoire pour dossier-init.")
        return 1

    stories_dir = project_path / "backlog" / "stories"
    target_story = SemanticLexiconResolver.resolve_story_query(story_query, stories_dir)
    if not target_story or not target_story.exists():
        matches = list(stories_dir.rglob(f"*{story_query}*.md")) if stories_dir.exists() else []
        if matches:
            target_story = matches[0]
        else:
            cand = Path(story_query)
            if cand.exists():
                target_story = cand
            else:
                ZeroFluffConsole.error(
                    f"Récit introuvable pour '{story_query}' sous {stories_dir}."
                )
                return 1

    content = target_story.read_text(encoding="utf-8", errors="replace")
    fm_match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    story_id = target_story.stem
    jira_key = ""
    title = target_story.stem
    if fm_match:
        fm_text = fm_match.group(1)
        id_m = re.search(r"^id:\s*(.+)$", fm_text, re.MULTILINE)
        if id_m:
            story_id = id_m.group(1).strip()
        jk_m = re.search(r"^jira_key:\s*(.+)$", fm_text, re.MULTILINE)
        if jk_m:
            jira_key = jk_m.group(1).strip()
        t_m = re.search(r"^title:\s*(.+)$", fm_text, re.MULTILINE)
        if t_m:
            title = t_m.group(1).strip().strip("'\"")

    h1_m = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    if h1_m and not title:
        title = h1_m.group(1).strip()

    evidence_dir = project_path / "memory" / "evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    dossier_file = evidence_dir / f"{story_id}_fact_dossier.md"

    if dossier_file.exists() and not force:
        ZeroFluffConsole.warning(
            f"Le Dossier de Preuves '{dossier_file.name}' existe déjà.\n"
            f"Utilisez --force pour écraser."
        )
        return 0

    now_iso = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    template = BlueprintLoader.render(
        "project_fact_dossier_template.md",
        {
            "STORY_ID": story_id,
            "JIRA_KEY": jira_key,
            "NOW_ISO": now_iso,
            "TITLE": title,
            "DATE": now_iso[:10],
        },
    )

    with open(dossier_file, "w", encoding="utf-8") as f:
        f.write(template)
    ZeroFluffConsole.success(f"Dossier de Preuves Documentaires initialisé : {dossier_file}")
    return 0
