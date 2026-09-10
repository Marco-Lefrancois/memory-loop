"""
handoff_simulator.py - Universal Dev "Zero-Ask" Handoff Simulator (ADR-0319 / ADR-0346)

Spawns a blind, clean-slate worker agent with ONLY the User Story Markdown file
to test whether a developer can implement the feature with ZERO clarification questions.
"""

import os
import re
import json
import shutil
from pathlib import Path
from typing import Dict, Any, Optional

from src.cli import ZeroFluffConsole
from src.core.herdr_adapter import herdr


def resolve_story_file(project_name: str, story_id: str) -> Optional[Path]:
    """Finds the physical story Markdown file."""
    clean_id = re.sub(r'[^a-zA-Z0-9_\-]', '', story_id)
    candidates = [
        Path.cwd() / "Projects" / project_name / "backlog" / "stories" / f"{clean_id}.md",
        Path.cwd() / "backlog" / "stories" / f"{clean_id}.md",
        Path.cwd() / "Projects" / project_name / "backlog" / "stories" / f"{clean_id.upper()}.md",
    ]
    for c in candidates:
        if c.exists():
            return c
    return None


def run_handoff_simulator(
    project_name: str,
    story_id: str,
    timeout_sec: int = 120,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Executes a Black-Box Handoff simulation on the target User Story.
    """
    ZeroFluffConsole.section(f"ZERO-ASK HANDOFF SIMULATOR — {story_id}")
    story_path = resolve_story_file(project_name, story_id)

    if not story_path:
        err = f"Fichier de story introuvable pour '{story_id}' dans le projet '{project_name}'"
        ZeroFluffConsole.error(err)
        return {"success": False, "status": "FILE_NOT_FOUND", "error": err}

    story_content = story_path.read_text(encoding="utf-8")
    ZeroFluffConsole.info(f"Story chargée : {story_path.name} ({len(story_content.splitlines())} lignes)")

    # 1. Prepare isolated sandbox directory (Black-Box Enclave)
    sandbox_dir = Path.cwd() / "Projects" / project_name / "memory" / "tmp" / f"handoff_{story_id.lower()}"
    sandbox_dir.mkdir(parents=True, exist_ok=True)
    sandbox_story = sandbox_dir / story_path.name
    sandbox_story.write_text(story_content, encoding="utf-8")

    if dry_run:
        ZeroFluffConsole.info("[Dry Run] Simulation Black-Box initialisée avec succès.")
        return {
            "success": True,
            "status": "HANDOFF_APPROVED",
            "story_id": story_id,
            "sandbox_dir": str(sandbox_dir),
            "dry_run": True
        }

    # 2. Spawn isolated worker
    worker_name = f"worker_handoff_{story_id.lower().replace('-', '_')}"[:32]
    ZeroFluffConsole.info(f"Instanciation du worker testeur 'Zero-Ask' : {worker_name}...")

    split_res = herdr.split_pane(target_pane_id="p1", direction="right", no_focus=True)
    pane_id = split_res.get("new_pane_id") or "p_handoff_test"

    start_res = herdr.start_agent(
        agent_name=worker_name,
        kind="opencode",
        pane_id=str(pane_id),
        extra_args=["--yolo", "--model", "nmedia_cloud/claude-sonnet-4.6"]
    )

    # 3. Formulate Black-Box Prompt
    prompt_text = (
        f"## MISSION TEST : SIMULATION UNIVERSAL DEV HANDOFF [ZERO-ASK]\n\n"
        f"Tu es un développeur logiciel externe recevant ce récit : `{sandbox_story.resolve()}`.\n"
        f"Tu n'as AUCUN contexte préalable sur l'historique du projet.\n\n"
        f"### Consigne d'évaluation :\n"
        f"1. Lis attentivement `{sandbox_story.resolve()}`.\n"
        f"2. Analyse si les critères d'acceptation, les 4 Piliers Gherkin et les contrats d'interface sont 100% complets.\n"
        f"3. Si une seule information manque (API non documentée, règle ambiguë, header inventé), écris exactement :\n"
        f"   `[HANDOFF_FAILED] Raison : <explication précise>`\n"
        f"4. Si la spécification est limpide et complète, écris exactement :\n"
        f"   `[HANDOFF_PASSED] Spécification 100% autonome et prête au développement.`\n"
    )

    herdr.prompt_agent(worker_name, prompt_text, wait=True, timeout_ms=timeout_sec * 1000)

    # 4. Harvest logs & evaluate verdict
    read_res = herdr.read_agent_output(worker_name, lines=100, source="recent-unwrapped")
    raw_logs = read_res.get("raw_output") or ""
    cleaned_logs = herdr.filter_terminal_bloat(raw_logs)

    verdict = "HANDOFF_APPROVED"
    reasons = []

    if "[HANDOFF_FAILED]" in cleaned_logs or "manquante" in cleaned_logs.lower() or "ambigu" in cleaned_logs.lower():
        verdict = "HANDOFF_REJECTED"
        for line in cleaned_logs.splitlines():
            if "[HANDOFF_FAILED]" in line or "manque" in line.lower():
                reasons.append(line.strip())

    # 5. Teardown
    herdr.cleanup_worker(worker_name)
    shutil.rmtree(sandbox_dir, ignore_errors=True)

    # 6. Report
    if verdict == "HANDOFF_APPROVED":
        ZeroFluffConsole.success(f"✅ Handoff Validé : La story '{story_id}' est 100% autonome (Zero-Ask).")
        herdr.show_notification(
            title=f"✅ Handoff PASS : {story_id}",
            body="Story 100% autonome et claire pour les développeurs.",
            sound="done"
        )
    else:
        ZeroFluffConsole.warning(f"⚠️ Handoff Rejeté : Ambiguïtés détectées dans '{story_id}'.")
        for r in reasons[:3]:
            ZeroFluffConsole.info(f" - {r}")
        herdr.show_notification(
            title=f"⚠️ Handoff FAIL : {story_id}",
            body="Des clarifications sont requises avant transmission aux devs.",
            sound="request"
        )

    return {
        "success": True,
        "story_id": story_id,
        "status": verdict,
        "reasons": reasons,
        "summary": cleaned_logs[-500:] if len(cleaned_logs) > 500 else cleaned_logs
    }
