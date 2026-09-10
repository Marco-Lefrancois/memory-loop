"""Handlers Plannotator : review, annotate, guide-export (ADR-0305, ADR-0307, ADR-0363)."""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
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
    ref_src = project_path / "reference"
    if not (cwd / ".git").exists() and ref_src.exists():
        for sub in ref_src.iterdir():
            if sub.is_dir() and (sub / ".git").exists():
                cwd = sub
                break

    ZeroFluffConsole.info(f"Lancement de la revue Plannotator dans {cwd}...")
    try:
        res = subprocess.run(cmd, cwd=cwd)
        return res.returncode
    except Exception as e:
        ZeroFluffConsole.error(f"Erreur lors du lancement de Plannotator review : {e}")
        return 1


def _resolve_annotation_target(
    args: argparse.Namespace, state: LoopState, project_path: Path
) -> Optional[str]:
    """Résout le fichier ou l'URL cible pour l'annotation."""
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

    candidate_plan = project_path / "memory" / "plan" / f"implementation_plan_{story_key}.md" if story_key else None
    if candidate_plan and candidate_plan.exists():
        return str(candidate_plan)

    return None


def handle_annotate(args: argparse.Namespace, state: LoopState, project_path: Path) -> int:
    """Ouvre un document, une User Story, une ADR ou une URL dans l'UI d'annotation Plannotator."""
    binary = _get_plannotator_binary()
    if not binary:
        ZeroFluffConsole.error(
            "Binaire 'plannotator' introuvable. Installez-le avec : irm https://plannotator.ai/install.ps1 | iex"
        )
        return 1

    target = _resolve_annotation_target(args, state, project_path)
    if not target:
        ZeroFluffConsole.error(
            "Cible introuvable. Spécifiez --story <KEY>, --adr <NUM>, --file <PATH> ou --url <URL>."
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
        res = subprocess.run(cmd)
        if res.returncode == 0:
            ZeroFluffConsole.success(f"Annotation / Validation terminée avec succès sur {target}")
        else:
            ZeroFluffConsole.warning(f"Plannotator s'est terminé avec le code {res.returncode}")
        return res.returncode
    except Exception as e:
        ZeroFluffConsole.error(f"Erreur lors de l'exécution de Plannotator annotate : {e}")
        return 1


def handle_guide_export(args: argparse.Namespace, state: LoopState, project_path: Path) -> int:
    """Exporte un Guided Review autonome au format HTML portable."""
    binary = _get_plannotator_binary()
    if not binary:
        ZeroFluffConsole.error(
            "Binaire 'plannotator' introuvable. Installez-le avec : irm https://plannotator.ai/install.ps1 | iex"
        )
        return 1

    out_file = getattr(args, "out", None)
    if not out_file:
        story_slug = getattr(state, "focused_story", "review")
        out_file = str(project_path / "memory" / f"guided-review-{story_slug}.html")

    cmd = [binary, "guide", "export"]

    snapshot = getattr(args, "snapshot", None)
    guide_id = getattr(args, "id", None)

    if snapshot:
        cmd.extend(["--snapshot", snapshot])
    elif guide_id:
        cmd.extend(["--id", guide_id])
    else:
        patch_file = project_path / "memory" / "temp_review.patch"
        try:
            diff_res = subprocess.run(["git", "diff", "HEAD~1...HEAD"], capture_output=True, text=True, cwd=project_path)
            if diff_res.returncode == 0 and diff_res.stdout.strip():
                patch_file.write_text(diff_res.stdout, encoding="utf-8")
                guide_json = project_path / "memory" / "temp_guide.json"
                import json
                guide_json.write_text(
                    json.dumps({
                        "title": f"Review Livraison {getattr(state, 'focused_story', state.project_name)}",
                        "intent": "Validation de story mLoop",
                        "sections": [{"title": "Modifications", "overview": "Diff complet", "diffs": []}]
                    }),
                    encoding="utf-8"
                )
                cmd.extend(["--guide", str(guide_json), "--patch", str(patch_file)])
            else:
                ZeroFluffConsole.warning("Aucun commit récent ou diff disponible pour l'export guide.")
                return 1
        except Exception as e:
            ZeroFluffConsole.error(f"Erreur lors de la génération du patch : {e}")
            return 1

    cmd.extend(["--out", out_file])
    ZeroFluffConsole.info(f"Génération du guide de revue portable : {out_file}...")
    try:
        res = subprocess.run(cmd)
        if res.returncode == 0:
            ZeroFluffConsole.success(f"Guide exporté avec succès : {out_file}")
        return res.returncode
    except Exception as e:
        ZeroFluffConsole.error(f"Erreur lors de l'export guide Plannotator : {e}")
        return 1
