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
        if (Path.cwd() / "backlog").exists() or project_name.lower() in [
            "mloop",
            "memory loop",
            "root",
        ]:
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
    extra_args: Optional[List[str]] = None,
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
        extra_args=extra_args,
    )

    if res.get("success"):
        ZeroFluffConsole.success(
            f"Worker Herdr instancié : {res.get('worker_name')} (Pane: {res.get('pane_id')})"
        )
        ZeroFluffConsole.info(
            f"Agent lancé avec kind='{res.get('kind', kind)}' | Modèle: {res.get('model', 'Défaut')}"
        )
        if res.get("task_type"):
            ZeroFluffConsole.info(f"Type de mission : {res.get('task_type').upper()}")
        ZeroFluffConsole.info(
            f"Récit cible : Projects/{project_name}/backlog/stories/{story_id}.md"
        )
    else:
        ZeroFluffConsole.error(
            f"Échec de l'instanciation du worker Herdr : {res.get('error', 'Inconnu')}"
        )

    return res


def run_worker_status(
    project_name: Optional[str] = None, story_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Queries and displays the status of registered Herdr workers, or probes a specific story.
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
        ZeroFluffConsole.warning(
            f"Impossible de contacter le daemon Herdr : {res.get('error', 'Daemon non démarré')}"
        )

    # Inspection ciblée d'une story spécifique via PTY read non-bloquant (Contournement L-01)
    if story_id:
        import re
        clean_id = re.sub(r"[^a-zA-Z0-9_]", "_", story_id).lower()
        worker_name = f"worker_{clean_id}"[:32]
        ZeroFluffConsole.info(f"\n[Sondage PTY non-bloquant pour '{story_id}'] (Worker: {worker_name})")
        read_res = herdr.read_agent_output(worker_name, lines=15, source="recent-unwrapped")
        raw_out = read_res.get("raw_output") or ""
        if isinstance(read_res.get("result"), dict):
            raw_out = read_res["result"].get("content") or raw_out
        if raw_out.strip():
            filtered = herdr.filter_terminal_bloat(raw_out)
            ZeroFluffConsole.info(f"Dernières lignes d'activité PTY :\n{filtered[-800:]}")
        else:
            ZeroFluffConsole.info("Aucune sortie PTY récente disponible pour ce worker.")

        if project_name:
            proj_path = resolve_project_path(project_name)
            from src.core.worker_signal import read_worker_signal
            signal = read_worker_signal(proj_path, story_id)
            if signal:
                ZeroFluffConsole.success(
                    f"Signal sidecar actif : [{signal.signal_type.value}] - {signal.reason or 'Nominal'}"
                )

    return res


def run_worker_harvest(project_name: str, story_id: str, lines: int = 150) -> Dict[str, Any]:
    """
    Harvests execution output from the worker pane, filters bloat, and updates EvidencePack.
    """
    ZeroFluffConsole.section(f"HERDR WORKER HARVEST - {story_id}")
    proj_path = resolve_project_path(project_name)

    # ADR-0355: Lecture du signal sidecar si présent (.mloop/status ou memory/worker_*.status)
    from src.core.worker_signal import read_worker_signal

    signal = read_worker_signal(proj_path, story_id)
    if signal:
        ZeroFluffConsole.info(
            f"Signal sidecar détecté : [{signal.signal_type.value}] - {signal.reason or 'Sans détails'}"
        )

    res = herdr.harvest_story_evidence(
        project_name=project_name,
        story_id=story_id,
        project_path=str(proj_path.resolve()),
        lines=lines,
    )

    if res.get("success"):
        if res.get("partial_harvest"):
            ZeroFluffConsole.warning(
                f"Moisson PARTIELLE pour {story_id} : le worker était encore actif (capture de repli 'visible'). "
                f"Relancez 'worker-harvest' après la fin d'exécution pour une moisson complète."
            )
        else:
            ZeroFluffConsole.success(
                f"Moisson PTY réussie pour {story_id} ({res.get('cleaned_lines')} lignes traitées)"
            )
        ZeroFluffConsole.info(f"Artefact EvidencePack mis à jour : {res.get('evidence_file')}")
        if res.get("summary_preview"):
            ZeroFluffConsole.info(f"Aperçu du log élagué : {res.get('summary_preview')[:120]}...")

        # ADR-0355: Validation de la preuve physique (Handoff Evidence Gate)
        from src.pipelines.completion_gate import CompletionGate, HandoffEvidencePolicy, GateStatus

        evidence_res = CompletionGate.validate_workspace_evidence(
            project_path=proj_path,
            story_id=story_id,
            signal=signal,
            policy=HandoffEvidencePolicy.OBSERVED,
        )
        res["evidence_gate"] = {
            "status": evidence_res.status.value,
            "requires_hitl": evidence_res.requires_hitl,
            "reasons": evidence_res.reasons,
            "warnings": evidence_res.warnings,
        }

        if evidence_res.status == GateStatus.FAIL:
            ZeroFluffConsole.error(f"Échec Gate d'évidence : {'; '.join(evidence_res.reasons)}")
        elif evidence_res.status == GateStatus.DEGENERATE_CANDIDATE:
            ZeroFluffConsole.warning(
                f"Alerte Gate d'évidence (HITL requis) : {'; '.join(evidence_res.reasons)}"
            )
        else:
            ZeroFluffConsole.success("Gate d'évidence validée (Preuve d'effort confirmée).")

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


def run_worker_close(project_name: str, story_id: str) -> Dict[str, Any]:
    """
    Closes a worker pane and cleans up resources.
    """
    ZeroFluffConsole.section(f"HERDR WORKER TEARDOWN - {story_id}")
    worker_name = f"worker_{story_id.replace('-', '_')}"

    res = herdr.cleanup_worker(worker_name)
    if res.get("success"):
        ZeroFluffConsole.success(f"Worker et volet {worker_name} fermés avec succès.")
    else:
        ZeroFluffConsole.warning(
            f"Fermeture volet {worker_name} : {res.get('error', 'Volet déjà clos ou non existant')}"
        )

    return res


def run_worker_reap(
    project_name: Optional[str] = None, timeout_sec: int = 300, force: bool = False
) -> Dict[str, Any]:
    """
    Purges stalled, idle, or zombie workers (ADR-0355 Stall Detection & Reaping).
    """
    ZeroFluffConsole.section("HERDR WORKER REAP - AUDIT ANTI-ZOMBIE (STALL DETECTION)")
    res = herdr.reap_zombie_workers(timeout_sec=timeout_sec, force=force)
    if res.get("success"):
        reaped_count = res.get("reaped_count", 0)
        if reaped_count > 0:
            ZeroFluffConsole.success(f"Purge réussie : {reaped_count} worker(s) arrêté(s).")
            for w in res.get("reaped", []):
                ZeroFluffConsole.info(
                    f" - Volet {w.get('pane_id')} ({w.get('name')}) fermé : {w.get('reason')}"
                )
        else:
            ZeroFluffConsole.info("Aucun worker zombie ou inactif détecté. Runtime sain.")
    else:
        errors = res.get("errors", [])
        ZeroFluffConsole.warning(f"Purge avec avertissements : {len(errors)} erreur(s).")
        for err in errors:
            ZeroFluffConsole.error(f" - Volet {err.get('pane_id')}: {err.get('error')}")

    return res


def run_worker_reap_zombies(project_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Purges all orphan/idle worker panes to guarantee zero-leak execution hygiene (Backward compatibility alias).
    """
    return run_worker_reap(project_name=project_name)


def run_frontier_autospawn(
    project_name: str, max_concurrent: int = 3, dry_run: bool = False
) -> Dict[str, Any]:
    """
    Calcule la Frontier du Task Graph (ADR-0367 / implement-spec) et déclenche
    les workers Herdr pour toutes les stories débloquées en parallèle.
    """
    from src.pipelines.task_graph import TaskGraph

    ZeroFluffConsole.section(f"HERDR TASK GRAPH FRONTIER - [{project_name}]")
    proj_path = resolve_project_path(project_name)

    graph = TaskGraph(proj_path)
    graph.load_stories()
    frontier = graph.get_frontier()

    if not frontier:
        ZeroFluffConsole.info("Aucune story dans la Frontier (toutes terminées ou bloquées).")
        return {"success": True, "frontier": [], "spawned": []}

    ZeroFluffConsole.success(
        f"Frontier active calculée : {len(frontier)} story(ies) prête(s) -> {', '.join(frontier)}"
    )

    target_stories = frontier[:max_concurrent]
    spawned = []

    if dry_run:
        ZeroFluffConsole.info(
            f"[DRY-RUN] Prêt à instancier {len(target_stories)} worker(s) : {', '.join(target_stories)}"
        )
        return {"success": True, "frontier": frontier, "spawned": target_stories, "dry_run": True}

    for story_id in target_stories:
        res = run_worker_spawn(project_name=project_name, story_id=story_id)
        if res.get("success"):
            spawned.append(story_id)

    ZeroFluffConsole.success(
        f"{len(spawned)}/{len(target_stories)} worker(s) instancié(s) sur la Frontier."
    )
    return {"success": True, "frontier": frontier, "spawned": spawned}
