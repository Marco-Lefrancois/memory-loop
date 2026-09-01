"""
worker_pipeline.py - Herdr Worker & Subagent Lifecycle Pipeline for mLoop Engine

Orchestrates clean-slate worker sessions per User Story, manages execution tracking,
harvests execution evidence from PTY output, and automates resource teardown.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional, List

from src.cli import ZeroFluffConsole
from src.core.herdr_adapter import herdr


def resolve_project_path(project_name: str, base_projects_dir: str = "Projects") -> Path:
    """Resolves project path with support for root-level projects or multi-tenant folders."""
    proj_path = Path(base_projects_dir) / project_name
    if not proj_path.exists():
        if (Path.cwd() / "backlog").exists() or project_name.lower() in ["mloop", "memory loop", "root"]:
            return Path.cwd()
        # Case-insensitive resolution
        if Path(base_projects_dir).exists():
            for p in Path(base_projects_dir).iterdir():
                if p.is_dir() and p.name.lower() == project_name.lower():
                    return p
        return proj_path
    return proj_path


def run_worker_spawn(
    project_name: str,
    story_id: str,
    kind: str = "opencode",
    model: Optional[str] = None,
    task_type: Optional[str] = None,
    extra_args: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Spawns an isolated Herdr worker pane for the given story and launches the agent.
    """
    ZeroFluffConsole.section(f"HERDR WORKER SPAWN - {story_id}")
    proj_path = resolve_project_path(project_name)

    res = herdr.spawn_story_worker(
        project_name=project_name,
        story_id=story_id,
        kind=kind,
        model=model,
        task_type=task_type,
        root_dir=str(proj_path.resolve()),
        extra_args=extra_args
    )

    if res.get("success"):
        ZeroFluffConsole.success(f"Worker Herdr instancié : {res.get('worker_name')} (Pane: {res.get('pane_id')})")
        ZeroFluffConsole.info(f"Agent lancé avec kind='{res.get('kind', kind)}' | Modèle: {res.get('model', 'Défaut')}")
        if res.get("task_type"):
            ZeroFluffConsole.info(f"Type de mission : {res.get('task_type').upper()}")
        ZeroFluffConsole.info(f"Récit cible : Projects/{project_name}/backlog/stories/{story_id}.md")
    else:
        ZeroFluffConsole.error(f"Échec de l'instanciation du worker Herdr : {res.get('error', 'Inconnu')}")

    return res


def run_worker_status(project_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Queries and displays the status of all registered Herdr workers.
    """
    ZeroFluffConsole.section("HERDR WORKERS - STATUT DU RUNTIME")
    res = herdr.list_agents()

    if res.get("success"):
        agents_data = res.get("result", {})
        inner = agents_data.get("result", {}) if isinstance(agents_data, dict) else {}
        agents_list = inner.get("agents", []) if isinstance(inner, dict) else []
        if not agents_list and isinstance(agents_data, dict):
            agents_list = agents_data.get("agents", [])
        
        if not agents_list and isinstance(res.get("raw_output"), str) and res.get("raw_output"):
            ZeroFluffConsole.info(f"Sortie brute Herdr : {res.get('raw_output')}")
        elif agents_list:
            ZeroFluffConsole.info(f"Total workers détectés : {len(agents_list)}")
            for ag in agents_list:
                name = ag.get("name") or ag.get("agent", "inconnu")
                state = ag.get("agent_status") or ag.get("state", "unknown")
                pane = ag.get("pane_id", "-")
                ZeroFluffConsole.info(f" - [{state.upper()}] Worker: {name} (Pane: {pane})")
        else:
            ZeroFluffConsole.info("Aucun worker Herdr actif actuellement.")
    else:
        ZeroFluffConsole.warning(f"Impossible de contacter le daemon Herdr : {res.get('error', 'Daemon non démarré')}")

    return res


def run_worker_harvest(
    project_name: str,
    story_id: str,
    lines: int = 150
) -> Dict[str, Any]:
    """
    Harvests execution output from the worker pane, filters bloat, and updates EvidencePack.
    """
    ZeroFluffConsole.section(f"HERDR WORKER HARVEST - {story_id}")
    proj_path = resolve_project_path(project_name)

    res = herdr.harvest_story_evidence(
        project_name=project_name,
        story_id=story_id,
        project_path=str(proj_path.resolve()),
        lines=lines
    )

    if res.get("success"):
        ZeroFluffConsole.success(f"Moisson PTY réussie pour {story_id} ({res.get('cleaned_lines')} lignes traitées)")
        ZeroFluffConsole.info(f"Artefact EvidencePack mis à jour : {res.get('evidence_file')}")
        if res.get("summary_preview"):
            ZeroFluffConsole.info(f"Aperçu du log élagué : {res.get('summary_preview')[:120]}...")

        # ADR-0341 : Re-vérification parente automatique des portails d'acceptation (GATES)
        try:
            from src.pipelines.gatekeeper import GatekeeperPipeline
            gk = GatekeeperPipeline(project_path=proj_path)
            gate_candidate = proj_path / "backlog" / "gates" / f"{story_id}.gates.md"
            if not gate_candidate.exists():
                gate_candidate = proj_path / "backlog" / "gates" / f"{story_id}.md"
            if gate_candidate.exists():
                ZeroFluffConsole.section(f"RE-VÉRIFICATION PARENTE DES PORTAILS — {story_id}")
                gk.execute(file_path=str(gate_candidate), mode="reverify", reverify=True)
        except Exception as exc:
            ZeroFluffConsole.warning(f"Re-vérification des gates ignorée ou échouée : {exc}")
    else:
        ZeroFluffConsole.error(f"Échec de la moisson d'évidences : {res.get('error', 'Inconnu')}")

    return res


def run_worker_close(
    project_name: str,
    story_id: str
) -> Dict[str, Any]:
    """
    Closes a worker pane and cleans up resources.
    """
    ZeroFluffConsole.section(f"HERDR WORKER TEARDOWN - {story_id}")
    worker_name = f"worker_{story_id.replace('-', '_')}"
    
    res = herdr.cleanup_worker(worker_name)
    if res.get("success"):
        ZeroFluffConsole.success(f"Worker et volet {worker_name} fermés avec succès.")
    else:
        ZeroFluffConsole.warning(f"Fermeture volet {worker_name} : {res.get('error', 'Volet déjà clos ou non existant')}")

    return res

