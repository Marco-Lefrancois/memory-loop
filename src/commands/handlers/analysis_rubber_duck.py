"""
Handler Rubber Duck — Agent Sentinel de revue contradictoire Read-Only (ADR-0326).

Extrait de `analysis_audit.py` (découpage ADR-0202) pour maintenir chaque module
sous le plafond de 300 lignes. Consommé via la façade `analysis.py`.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from src.cli import ZeroFluffConsole, LoggingConsole

if TYPE_CHECKING:
    import argparse
    from src.state import LoopState


def _log_err(msg: str, args: Any = None, **ctx: Any) -> None:
    """Route une erreur rubber-duck vers LoggingConsole.error avec contexte standardise (MLOOP-142-BE)."""
    LoggingConsole.error(msg, command="rubber-duck", project=getattr(args, "project", None), **ctx)


def _resolve_targets(args: "argparse.Namespace", project_path: Path) -> "list[Path] | None":
    """Résout la liste des récits à auditer ; retourne None si la cible explicite est introuvable."""
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
                    _log_err(
                        f"Fichier cible introuvable : {target_path}",
                        args,
                        target_keys=str(target),
                    )
                    return None
    else:
        stories_dir = project_path / "backlog" / "stories"
        if stories_dir.exists():
            files_to_check.extend(list(stories_dir.rglob("*.md")))

    return files_to_check


def _print_critique_details(critique: dict, args: "argparse.Namespace", is_cached: bool) -> None:
    """Affiche les points d'attention non-bloquants, scores et patchs de remédiation."""
    target = getattr(args, "file", None)
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
        print("\n📊 Évaluation Qualitative Avocat du Diable :")
        print(f"   • Discernement Métier : {scores.get('business_discernment')}/100")
        print(f"   • Cohérence Écosystème: {scores.get('ecosystem_coherence')}/100")
        print(f"   • Rigueur Technique   : {scores.get('technical_rigor')}/100")
        print(f"   • Trust Score Global  : {scores.get('overall_trust')}/100\n")

    if (getattr(args, "suggest_patch", False) or target) and critique.get("remediation_patches"):
        ZeroFluffConsole.info(
            f"Propositions de Remédiation Gherkin ({len(critique['remediation_patches'])} patch(s)) :"
        )
        for patch in critique["remediation_patches"]:
            print(f"\n  📝 [{patch.get('pillar_target')}] {patch.get('issue_addressed')}")
            for line in patch.get("suggested_gherkin", "").splitlines():
                print(f"     {line}")
        print("")


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

    files_to_check = _resolve_targets(args, project_path)
    if files_to_check is None:
        return 1
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
            n = len(critique["blocking_issues"])
            if not is_cached:
                remaining_ttl = fsm.decrement_ttl(f)
                _log_err(
                    f"Rejet Rubber Duck ({n} problème(s) bloquant(s)) — TTL restant : {remaining_ttl}",
                    args,
                    target_keys=f.name,
                )
                for issue in critique["blocking_issues"]:
                    print(f"  - [REJET] {issue}")
                try:
                    fsm.check_ttl(f)
                except Exception as ttl_err:
                    _log_err(
                        str(ttl_err),
                        args,
                        target_keys=f.name,
                        subcommand="check_ttl",
                        exc_info=True,
                    )
                engine.update_cache_mtime(f, critique)
            else:
                _log_err(
                    f"Rejet Rubber Duck ({n} problème(s) bloquant(s)) [Cached]",
                    args,
                    target_keys=f.name,
                )
                for issue in critique["blocking_issues"]:
                    print(f"  - [REJET] {issue}")
        else:
            ZeroFluffConsole.success("Approbation Rubber Duck (Aucun problème bloquant).")

        _print_critique_details(critique, args, is_cached)

        ZeroFluffConsole.success(
            f"Rapport enregistré sous : {report_file.relative_to(project_path)}"
        )

    if cached_count > 0:
        ZeroFluffConsole.success(
            f"Audit Rubber Duck terminé : {cached_count}/{len(files_to_check)} récit(s) validés via cache mtime."
        )

    return 1 if has_blocking else 0
