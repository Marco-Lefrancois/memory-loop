"""
Handlers Plannotator : review, annotate, guide-export, plannotator (ADR-014, ADR-0305, ADR-0307).

Sanctuarisation de la topologie de plan sous Projects/<project>/memory/plan/
et support du mode headless --approve pour l'intégration continue.
Conforme ADR-0202 (<=300 lignes, <=15 Ko) et ADR-0369.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from src.cli import ZeroFluffConsole

if TYPE_CHECKING:
    from src.state import LoopState


def _get_plannotator_binary() -> Optional[str]:
    """Résout le binaire plannotator sur PATH ou dans AppData Local."""
    cmd = shutil.which("plannotator")
    if cmd:
        return cmd

    local_appdata = os.environ.get("LOCALAPPDATA")
    if local_appdata:
        candidate = Path(local_appdata) / "plannotator" / "plannotator.exe"
        if candidate.exists():
            return str(candidate)

    home_candidate = Path.home() / "AppData" / "Local" / "plannotator" / "plannotator.exe"
    if home_candidate.exists():
        return str(home_candidate)

    return None


def handle_review(args: argparse.Namespace, state: LoopState, project_path: Path) -> int:
    """Lance une revue de code visuelle via Plannotator (diff local Git ou PR GitHub/GitLab)."""
    binary = _get_plannotator_binary()
    if not binary:
        ZeroFluffConsole.error(
            "Binaire 'plannotator' introuvable. Installez-le avec : irm https://plannotator.ai/install.ps1 | iex"
        )
        return 1

    cmd = [binary, "review"]
    pr_url = getattr(args, "pr", None)
    if pr_url:
        cmd.append(pr_url)
        if getattr(args, "no_local", False):
            cmd.append("--no-local")
    else:
        cmd.append("--git")

    if getattr(args, "tailscale", False):
        cmd.append("--tailscale")

    cwd = project_path if (project_path / ".git").exists() else Path.cwd()
    ZeroFluffConsole.info(f"Lancement de la revue Plannotator dans {cwd}...")
    try:
        res = subprocess.run(cmd, cwd=cwd, timeout=3600)
        return res.returncode
    except Exception as e:
        ZeroFluffConsole.error(f"Erreur lors du lancement de Plannotator review : {e}")
        return 1


def _resolve_annotation_target(
    args: argparse.Namespace, state: LoopState, project_path: Path
) -> Optional[str]:
    """Résout le fichier ou l'URL cible pour l'annotation (confinement projet strict)."""
    url = getattr(args, "url", None)
    if url:
        return url

    story_key = getattr(args, "story", None) or getattr(state, "focused_story", None)
    if story_key:
        stories_dir = project_path / "backlog" / "stories"
        if stories_dir.exists():
            direct_file = stories_dir / f"{story_key}.md"
            if direct_file.exists():
                return str(direct_file)
            matches = list(stories_dir.glob(f"*{story_key}*.md"))
            if matches:
                return str(matches[0])

    adr_id = getattr(args, "adr", None)
    if adr_id:
        adr_dir = Path("standards") / "adr-system"
        if adr_dir.exists():
            matches = list(adr_dir.glob(f"*{adr_id}*.md"))
            if matches:
                return str(matches[0])

    file_path = getattr(args, "file", None) or getattr(args, "target", None)
    if file_path:
        p = Path(file_path)
        if p.exists():
            return str(p)
        proj_p = project_path / file_path
        if proj_p.exists():
            return str(proj_p)
        return file_path

    if story_key:
        plan_dir = project_path / "memory" / "plan"
        if plan_dir.exists():
            for name in [
                f"{story_key}_phase_plan.md",
                f"implementation_plan_{story_key}.md",
                f"{story_key}.md",
            ]:
                candidate = plan_dir / name
                if candidate.exists():
                    return str(candidate)
            matches = [f for f in plan_dir.glob("*.md") if story_key.lower() in f.name.lower()]
            if matches:
                return str(matches[0])

    return None


def handle_annotate(args: argparse.Namespace, state: LoopState, project_path: Path) -> int:
    """Ouvre un document, une User Story ou un plan dans l'UI d'annotation Plannotator."""
    binary = _get_plannotator_binary()
    if not binary:
        ZeroFluffConsole.error(
            "Binaire 'plannotator' introuvable. Installez-le avec : irm https://plannotator.ai/install.ps1 | iex"
        )
        return 1

    target = _resolve_annotation_target(args, state, project_path)
    if not target:
        ZeroFluffConsole.error(
            "Cible introuvable. Spécifiez --story <KEY>, --file <PATH> ou --url <URL>."
        )
        return 1

    cmd = [binary, "annotate", target]
    if not getattr(args, "no_gate", False):
        cmd.append("--gate")
    if getattr(args, "require_approval", False):
        cmd.append("--require-approval")
    if getattr(args, "json", False) or getattr(args, "result_file", None):
        cmd.append("--json")
    result_file = getattr(args, "result_file", None)
    if result_file:
        cmd.extend(["--result-file", str(result_file)])
    if getattr(args, "tailscale", False):
        cmd.append("--tailscale")

    ZeroFluffConsole.info(f"Ouverture de Plannotator annotate sur : {target}")
    try:
        res = subprocess.run(cmd, timeout=3600)
        if res.returncode == 0:
            ZeroFluffConsole.success(f"Annotation / Validation terminée avec succès sur {target}")
            target_p = Path(target)
            if project_path and (project_path / "memory").exists():
                dest_dir = project_path / "memory" / "plan"
                dest_dir.mkdir(parents=True, exist_ok=True)
                dest_file = dest_dir / target_p.name
                if target_p != dest_file and target_p.exists():
                    shutil.copy2(target_p, dest_file)
                    ZeroFluffConsole.info(f"Plan archivé canoniquement dans le projet : {dest_file}")
        else:
            ZeroFluffConsole.warning(f"Plannotator s'est terminé avec le code {res.returncode}")
        return res.returncode
    except Exception as e:
        ZeroFluffConsole.error(f"Erreur lors de l'exécution de Plannotator annotate : {e}")
        return 1


def handle_approve(args: argparse.Namespace, state: LoopState, project_path: Path) -> int:
    """Approuve un plan de phase en mode interactif ou headless (--approve) (ADR-014)."""
    story_id = getattr(args, "story", None)
    plan_dir = project_path / "memory" / "plan"
    plan_dir.mkdir(parents=True, exist_ok=True)

    target = _resolve_annotation_target(args, state, project_path)
    if getattr(args, "approve", False):
        # Validation headless déterministe pour environnement CI/CD
        base_name = f"{story_id}_phase_plan" if story_id else (Path(target).stem if target else "plan")
        annotated_file = plan_dir / f"{base_name}.annotated.md"
        src_content = Path(target).read_text(encoding="utf-8") if target and Path(target).exists() else f"# Plan pour {story_id or 'initiative'}\n"
        approval_stamp = "\n\n<!-- Plannotator Approved (Headless CI/CD Mode) -->\n"
        annotated_file.write_text(src_content + approval_stamp, encoding="utf-8")
        ZeroFluffConsole.success(f"Plan validé et archivé canoniquement : {annotated_file}")
        return 0

    return handle_annotate(args, state, project_path)


def handle_guide_export(args: argparse.Namespace, state: LoopState, project_path: Path) -> int:
    """Exporte un Guided Review autonome au format HTML portable."""
    binary = _get_plannotator_binary()
    if not binary:
        ZeroFluffConsole.error(
            "Binaire 'plannotator' introuvable. Installez-le avec : irm https://plannotator.ai/install.ps1 | iex"
        )
        return 1

    out_file = getattr(args, "out", None) or str(
        project_path / "memory" / f"guided-review-{getattr(state, 'focused_story', 'review')}.html"
    )
    cmd = [binary, "guide", "export", "--out", out_file]
    try:
        res = subprocess.run(cmd, timeout=60.0)
        if res.returncode == 0:
            ZeroFluffConsole.success(f"Guide exporté avec succès : {out_file}")
        return res.returncode
    except Exception as e:
        ZeroFluffConsole.error(f"Erreur lors de l'export guide Plannotator : {e}")
        return 1


def handle_plannotator(args: argparse.Namespace, state: LoopState, project_path: Path) -> int:
    """Point d'entrée principal pour la commande `mloop plannotator`."""
    action = getattr(args, "action", "open") or "open"
    action = action.lower()

    if action == "open":
        return handle_annotate(args, state, project_path)
    if action == "approve":
        return handle_approve(args, state, project_path)
    if action == "status":
        bin_path = _get_plannotator_binary()
        plan_dir = project_path / "memory" / "plan"
        plans = list(plan_dir.glob("*.md")) if plan_dir.exists() else []

        ZeroFluffConsole.info("=== Statut du Harnais Plannotator ===")
        if bin_path:
            ZeroFluffConsole.success(f"  • Binaire Plannotator : DISPONIBLE ({bin_path})")
        else:
            ZeroFluffConsole.warning("  • Binaire Plannotator : NON INSTALLÉ")
        ZeroFluffConsole.info(f"  • Plans archivés ({project_path.name}) : {len(plans)} plan(s)")
        return 0

    ZeroFluffConsole.error(f"Action Plannotator inconnue : '{action}'. Actions valides : open, approve, status.")
    return 1
