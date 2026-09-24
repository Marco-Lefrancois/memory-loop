"""
herdr_worker_core.py - Worker lifecycle implementation (ADR-0202 <=300L).

Extracted from herdr_worker.py to comply with modular ceiling.
"""

import json
import os
import re
import time
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("mloop.herdr_worker_core")


TASK_MODEL_MAP = {
    "deepening": "nmedia_cloud/claude-opus-4.8",
    "validation": "nmedia_cloud/gpt-5.6-terra-thinking",
    "deepsearch": "nmedia_cloud/claude-sonnet-5",
    # Free tier natif OpenCode (ADR-0388) : facilite dev/build sans coût LiteLLM.
    # Portes qualité (deepening/validation/deepsearch/compaction) inchangées.
    "build": "opencode/mimo-v2.6-flash-free",
    "compaction": "nmedia_cloud/gemini-3.8-flash",
}


def filter_terminal_bloat(raw_text: str) -> str:
    """Filters ANSI escape sequences, spinners, and noisy progress bars."""
    if not raw_text:
        return ""
    ansi_regex = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    cleaned = ansi_regex.sub("", raw_text).replace("\r\n", "\n").replace("\r", "\n")
    spinners = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏", "◐", "◓", "◑", "◒"]
    skip_tokens = {"Loading...", "Working...", "Compiling..."}
    lines = []
    for line in cleaned.splitlines():
        s = line.strip()
        if not s or any(s.startswith(sp) for sp in spinners) or s in skip_tokens:
            continue
        lines.append(line)
    return "\n".join(lines)


def spawn_story_worker_impl(
    self,
    project_name: str,
    story_id: str,
    kind: str = "opencode",
    model: Optional[str] = None,
    task_type: Optional[str] = None,
    root_dir: Optional[str] = None,
    extra_args: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Spawns a clean-slate worker pane dedicated to a User Story."""
    cwd = root_dir or os.getcwd()
    clean_id = re.sub(r"[^a-zA-Z0-9_]", "_", story_id).lower()
    worker_name = f"worker_{clean_id}"[:32]
    logger.info(f"Spawning story worker '{worker_name}' for '{project_name}'...")
    self.ensure_server_running()
    target_model = model or (TASK_MODEL_MAP.get(task_type.lower()) if task_type else None)
    if kind == "claude":
        logger.warning("Standalone Claude Code not authenticated. Redirecting to OpenCode.")
        kind = "opencode"
        if not target_model:
            target_model = "nmedia_cloud/claude-opus-4.8"
    try:
        from src.core.worker_runtimes import get_worker_runtime

        runtime_spec = get_worker_runtime(kind)
    except (ImportError, KeyError) as exc:
        logger.debug(
            "Runtime worker non enregistré.",
            exc_info=True,
            extra={"kind": kind, "error": str(exc)},
        )
        runtime_spec = None
    if runtime_spec is not None and runtime_spec.default_model and not model:
        target_model = runtime_spec.default_model
    split_res = self._exec(["pane", "split", "--direction", "right", "--no-focus"])
    pane_id = None
    if split_res.get("success"):
        data = split_res.get("result", {})
        pane_id = data.get("result", {}).get("pane", {}).get("pane_id") or data.get("pane", {}).get(
            "pane_id"
        )
    if not pane_id:
        ws_res = self.create_workspace(cwd=cwd, label=f"mloop-{story_id}", no_focus=True)
        pane_id = ws_res.get("root_pane_id")
    if not pane_id:
        pane_id = "p_fallback_1"
        logger.warning(f"Could not retrieve pane_id, using fallback '{pane_id}'")
    if runtime_spec is not None:
        flags = runtime_spec.build_flags(model=target_model, extra_args=extra_args)
    else:
        flags = list(extra_args) if extra_args else ["--dangerously-skip-permissions"]

    # MLOOP-262-BE : Verrouillage strict du mode Plan pour Cline en Phase 2
    if kind == "cline" and task_type in ("plan", "grill", "analyse"):
        if "--plan" not in flags and "-p" not in flags:
            flags.append("--plan")

    # MLOOP-263-BE : Circuit-Breaker déterministe Cline -> OpenCode
    start_res = None
    try:
        start_res = self.start_agent(
            agent_name=worker_name, kind=kind, pane_id=str(pane_id), extra_args=flags
        )
    except Exception as exc:
        if kind == "cline":
            logger.warning(
                "Exception spawn Cline (%s). Déclenchement Circuit-Breaker : fallback vers OpenCode.",
                exc,
            )
            kind = "opencode"
            from src.core.worker_runtimes import get_worker_runtime
            flags = get_worker_runtime("opencode").build_flags(model=target_model, extra_args=extra_args)
            start_res = self.start_agent(
                agent_name=worker_name, kind=kind, pane_id=str(pane_id), extra_args=flags
            )
        else:
            raise

    if kind == "cline" and isinstance(start_res, dict) and not start_res.get("success"):
        logger.warning(
            "Échec start_agent Cline (%s). Déclenchement Circuit-Breaker : fallback vers OpenCode.",
            start_res.get("error"),
        )
        kind = "opencode"
        from src.core.worker_runtimes import get_worker_runtime
        flags = get_worker_runtime("opencode").build_flags(model=target_model, extra_args=extra_args)
        start_res = self.start_agent(
            agent_name=worker_name, kind=kind, pane_id=str(pane_id), extra_args=flags
        )

    time.sleep(3)
    try:
        self.wait_agent(worker_name, until_states=["idle", "done", "blocked"], timeout_ms=5000)
    except Exception as exc:
        logger.warning(
            "wait_agent timeout au spawn worker — prompt envoyé quand même (résilience).",
            exc_info=True,
            extra={
                "worker_id": worker_name,
                "pane_id": pane_id,
                "agent_kind": kind,
                "task_type": task_type,
                "timeout_ms": 5000,
                "error": str(exc),
            },
        )
    clean_target = (
        str(story_id).replace("\\", "/").replace("Projects/", "").replace(f"{project_name}/", "")
    )
    if clean_target.startswith("backlog/stories/"):
        clean_target = clean_target[len("backlog/stories/") :]
    elif clean_target.startswith("backlog/"):
        clean_target = clean_target[len("backlog/") :]
    if clean_target.endswith(".md"):
        clean_target = clean_target[:-3]
    story_file_rel = (
        f"Projects/{project_name}/backlog/sprint_backlog.md"
        if clean_target in ("sprint_backlog", "backlog")
        else f"Projects/{project_name}/backlog/stories/{clean_target}.md"
    )
    task_label = (task_type or "build").upper()
    prompt_text = (
        f"## Mission Worker mLoop — {clean_target} [{task_label}]\n\n"
        f"**Projet** : {project_name}\n**Récit** : `{story_file_rel}`\n**CWD** : `{cwd}`\n\n"
        f"### Démarrage (OBLIGATOIRE)\n"
        f"1. `python src/swarm.py resume --project {project_name}`\n"
        f"2. Lire `{story_file_rel}`\n3. Exécuter la mission '{task_label}'\n\n"
        f"### Règles\n"
        f"- Gabarit Gold Standard + 4 Piliers Gherkin\n"
        f"- Arrêt STRICT après '## Scénarios de test' (ZÉRO note IA)\n"
        f"- Traçabilité dans `memory/evidence/<STORY_ID>_evidence.json`\n"
        f"- Citations : `[Nom.md (Lignes X-Y)](file:///chemin)` — ancre #L INTERDITE\n"
        f"- Écris sous `Projects/{project_name}/` — Interdiction `init` ou altération `lifecycle_state.json`\n"
        f"- Termine par `python src/swarm.py sync --project {project_name}`\n"
        f"- Statut sidecar (ADR-0355) dans `memory/worker_{story_id}.status`\n"
    )
    prompt_res = self.prompt_agent(worker_name, prompt_text, wait=False)
    logger.info(
        "Worker lifecycle: spawn -> working",
        extra={
            "worker_id": worker_name,
            "pane_id": pane_id,
            "agent_kind": kind,
            "task_type": task_type,
            "model": target_model,
        },
    )
    return {
        "success": True,
        "worker_name": worker_name,
        "pane_id": pane_id,
        "story_id": story_id,
        "project": project_name,
        "kind": kind,
        "model": target_model,
        "task_type": task_type,
        "start_result": start_res,
        "prompt_result": prompt_res,
    }


def harvest_story_evidence_impl(
    self,
    project_name: str,
    story_id: str,
    project_path: Optional[str] = None,
    lines: int = 150,
) -> Dict[str, Any]:
    """Extracts execution logs, filters bloat, saves to evidence JSON."""
    clean_id = re.sub(r"[^a-zA-Z0-9_]", "_", story_id).lower()
    worker_name = f"worker_{clean_id}"[:32]
    read_res = self.read_agent_output(worker_name, lines=lines, source="recent-unwrapped")
    raw_output = read_res.get("raw_output") or ""
    if isinstance(read_res.get("result"), dict):
        raw_output = read_res["result"].get("content") or raw_output
    worker_active = bool(read_res.get("worker_was_active"))
    cleaned_output = filter_terminal_bloat(raw_output)
    proj_dir = Path(project_path) if project_path else Path.cwd() / "Projects" / project_name
    if not proj_dir.exists() and (Path.cwd() / "backlog").exists():
        proj_dir = Path.cwd()
    evidence_dir = proj_dir / "memory" / "evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    evidence_file = evidence_dir / f"{story_id}_evidence.json"
    existing_data = {}
    if evidence_file.exists():
        try:
            existing_data = json.loads(evidence_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning(
                "EvidencePack existant illisible — réinitialisation.",
                exc_info=True,
                extra={
                    "worker_id": worker_name,
                    "evidence_file": str(evidence_file),
                    "error": str(exc),
                },
            )
            existing_data = {}
    summary = cleaned_output[-2000:] if len(cleaned_output) > 2000 else cleaned_output
    existing_data = {
        **existing_data,
        "story_id": story_id,
        "herdr_worker": worker_name,
        "execution_summary": summary,
        "harvest_status": "PARTIAL" if worker_active else "COMPLETED",
    }
    evidence_file.write_text(
        json.dumps(existing_data, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    logger.info(
        "Worker lifecycle: harvest",
        extra={
            "worker_id": worker_name,
            "harvest_status": existing_data["harvest_status"],
            "cleaned_lines": len(cleaned_output.splitlines()),
            "worker_active": worker_active,
        },
    )
    return {
        "success": True,
        "story_id": story_id,
        "worker_name": worker_name,
        "evidence_file": str(evidence_file),
        "partial_harvest": worker_active,
        "worker_active_during_harvest": worker_active,
        "cleaned_lines": len(cleaned_output.splitlines()),
        "summary_preview": existing_data["execution_summary"][:300],
    }


def cleanup_worker_impl(self, story_id_or_pane: str) -> Dict[str, Any]:
    """Closes a worker pane and cleans up its resources."""
    pane_id = story_id_or_pane
    if ":" not in pane_id:
        agents_res = self.list_agents()
        if agents_res.get("success"):
            clean_target = re.sub(r"[^a-zA-Z0-9_]", "_", story_id_or_pane).lower()
            for ag in extract_agents_list_impl(agents_res.get("result", {})):
                ag_name = (ag.get("name") or "").lower()
                if (
                    ag_name == clean_target
                    or clean_target in ag_name
                    or f"worker_{clean_target}" in ag_name
                ):
                    if ag.get("pane_id"):
                        pane_id = ag["pane_id"]
                        break
    logger.info(
        "Worker lifecycle: close",
        extra={"worker_id": story_id_or_pane, "pane_id": pane_id},
    )
    return self.close_pane(pane_id)


def extract_agents_list_impl(agents_data: Any) -> List[Dict[str, Any]]:
    """Extracts agents list from Herdr response (v0.8.x nesting)."""
    inner = agents_data.get("result", {}) if isinstance(agents_data, dict) else {}
    agents_list = inner.get("agents", []) if isinstance(inner, dict) else []
    if not agents_list and isinstance(agents_data, dict):
        agents_list = agents_data.get("agents", [])
    return agents_list


def audit_and_reap_zombies_impl(self, project_name: Optional[str] = None) -> Dict[str, Any]:
    """Teardown Gate (Zero Zombie Policy - ADR-0306 / ADR-0345)."""
    logger.info("Auditing Herdr workers for zombie/idle processes...")
    list_res = self.list_agents()
    if not list_res.get("success"):
        return {"success": False, "reaped_count": 0, "error": list_res.get("error")}
    reaped = []
    for ag in extract_agents_list_impl(list_res.get("result", {})):
        name, pane_id = ag.get("name") or "", ag.get("pane_id")
        status = ag.get("agent_status") or ag.get("status")
        if (
            name.startswith("worker_")
            and pane_id
            and (status in ["idle", "done", "unknown"] or not status)
        ):
            logger.warning(
                "Zombie reap",
                extra={
                    "worker_id": name,
                    "pane_id": pane_id,
                    "status": status,
                    "age_seconds": ag.get("age_seconds"),
                },
            )
            cr = self.close_pane(pane_id)
            if not cr.get("success", False):
                logger.error(
                    "Échec reap zombie (fermeture volet impossible).",
                    extra={
                        "worker_id": name,
                        "pane_id": pane_id,
                        "status": status,
                        "close_error": cr.get("error"),
                    },
                )
            reaped.append(
                {
                    "name": name,
                    "pane_id": pane_id,
                    "status": status,
                    "close_success": cr.get("success", False),
                }
            )
    return {"success": True, "reaped_count": len(reaped), "reaped_workers": reaped}


def detect_stalled_agents_impl(self, timeout_sec: int = 300) -> List[Dict[str, Any]]:
    """Detects inactive agents (idle, stopped, blocked or no state)."""
    stalled: List[Dict[str, Any]] = []
    agents_res = self.list_agents()
    if not agents_res.get("success"):
        return stalled
    for ag in extract_agents_list_impl(agents_res.get("result", {})):
        state = (ag.get("agent_status") or ag.get("state") or "").lower()
        name = ag.get("name") or ag.get("agent", "unknown")
        pane_id = ag.get("pane_id")
        if state in (
            "idle",
            "stopped",
            "completed",
            "done",
            "failed",
            "blocked",
            "unknown",
            "",
        ):
            reason = (
                f"État terminal ou inactif ({state})"
                if state not in ("unknown", "")
                else "Agent sans état actif"
            )
            stalled.append({"name": name, "pane_id": pane_id, "state": state, "reason": reason})
    return stalled


def reap_zombie_workers_impl(self, timeout_sec: int = 300, force: bool = False) -> Dict[str, Any]:
    """Ferme automatiquement les volets/agents orphelins (Zéro Zombie)."""
    stalled = detect_stalled_agents_impl(self, timeout_sec=timeout_sec)
    reaped, errors = [], []
    for ag in stalled:
        pid = ag.get("pane_id")
        if not pid:
            continue
        cr = self.close_pane(pid)
        entry = {"name": ag.get("name"), "pane_id": pid, "reason": ag.get("reason")}
        if cr.get("success"):
            logger.warning(
                "Worker orphelin reapé.",
                extra={"worker_id": ag.get("name"), "pane_id": pid, "reason": ag.get("reason")},
            )
            reaped.append(entry)
        else:
            logger.error(
                "Échec fermeture worker orphelin.",
                extra={
                    "worker_id": ag.get("name"),
                    "pane_id": pid,
                    "reason": ag.get("reason"),
                    "close_error": cr.get("error"),
                },
            )
            errors.append({**entry, "error": cr.get("error")})
    return {
        "success": len(errors) == 0,
        "total_detected": len(stalled),
        "reaped_count": len(reaped),
        "reaped": reaped,
        "errors": errors,
    }
