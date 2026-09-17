"""
Handlers Résilience Agentique & Point-in-Time Recovery (ADR-0371).
Commandes : agent-resilience, topology, rollback.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

from src.cli import ZeroFluffConsole
from src.pipelines.agent_resilience import (
    AgentTopologyMapper,
    AgentStateRollbackEngine,
    ResilienceAudit,
)

if TYPE_CHECKING:
    import argparse
    from src.state import LoopState


def handle_agent_resilience(args: argparse.Namespace, state: LoopState, project_path: Path) -> int:
    """Audit global de la résilience agentique mLoop."""
    project_name = args.project or (state.project_name if state else "mLoop")
    ZeroFluffConsole.section(f"Audit de Résilience Agentique - {project_name} (ADR-0371)")

    audit_res = ResilienceAudit.audit(project_name, project_path=project_path)

    if getattr(args, "json", False):
        print(json.dumps(audit_res, indent=2, ensure_ascii=False))
        return 0

    idx = audit_res["resilience_index"]
    status = audit_res["status"]
    cp_info = audit_res["checkpoints"]
    ev_info = audit_res["evidence"]
    mem_info = audit_res["memory_hygiene"]

    status_color = "success" if status == "EXCELLENT" else ("warning" if status == "STABLE" else "error")
    ZeroFluffConsole.info(f"Score Global de Résilience : [{status_color}]{idx}/100 ({status})[/{status_color}]")
    ZeroFluffConsole.info(f"Points de Contrôle (Checkpoints) : {cp_info['count']} enregistrés (Score: {cp_info['score']}%)")
    if cp_info.get("latest"):
        ZeroFluffConsole.info(f"Dernier Checkpoint Sain : {cp_info['latest']}")

    ZeroFluffConsole.info(
        f"Dossiers de Preuves (EvidencePacks) : {ev_info['valid']}/{ev_info['total']} valides (Score: {ev_info['score']}%)"
    )

    hygiene_label = "Conforme ADR-0362" if mem_info["ok"] else "ALERTE : Dépassement de plafond"
    ZeroFluffConsole.info(
        f"Hygiène Mémoire (SESSION_MEMORY_HEALTH.md) : {mem_info['lines']} lignes / {mem_info['bytes']} octets ({hygiene_label})"
    )
    ZeroFluffConsole.info(f"Topologies d'Agents Cartographiées : {audit_res['topologies_mapped']} rôles")

    ZeroFluffConsole.success("Audit de résilience terminé avec succès.")
    return 0


def handle_topology(args: argparse.Namespace, state: LoopState, project_path: Path) -> int:
    """Cartographie de la topologie d'agents et calcul du Blast Radius."""
    project_name = args.project or (state.project_name if state else "mLoop")
    role = getattr(args, "agent", None)

    ZeroFluffConsole.section(f"Topologie Agentique & Blast Radius - {project_name}")

    if role:
        calc = AgentTopologyMapper.compute_blast_radius(role)
        topology = AgentTopologyMapper.get_topology(role)

        if getattr(args, "json", False):
            print(json.dumps(calc, indent=2, ensure_ascii=False))
            return 0

        ZeroFluffConsole.info(f"Rôle Analysé : {topology.role.upper()} ({topology.description})")
        ZeroFluffConsole.info(f"Niveau d'Impact : {calc['level']} (Score: {calc['blast_score']}/100)")
        unattended_str = "AUTORISÉ (Sûr)" if calc["unattended_authorized"] else "INTERDIT (HITL Obligatoire)"
        ZeroFluffConsole.info(f"Mode Unattended : {unattended_str}")
        ZeroFluffConsole.info(f"Chemins Autorisés en Écriture : {topology.authorized_write_paths}")
        ZeroFluffConsole.info(f"Chemins Strictement Interdits : {topology.forbidden_paths}")
        ZeroFluffConsole.info(f"Partitions Mémoire Connectées : {topology.connected_memory_partitions}")
        ZeroFluffConsole.info(f"Outils Système Autorisés : {topology.allowed_tools}")
    else:
        topologies = AgentTopologyMapper.list_all_topologies()
        if getattr(args, "json", False):
            print(json.dumps([t.model_dump() for t in topologies], indent=2, ensure_ascii=False))
            return 0

        ZeroFluffConsole.info(f"Nombre de rôles répertoriés : {len(topologies)}")
        for t in topologies:
            calc = AgentTopologyMapper.compute_blast_radius(t.role)
            unattended_str = "OUI" if calc["unattended_authorized"] else "NON (HITL)"
            ZeroFluffConsole.info(
                f"  - {t.role.upper():<12} | Impact: {calc['level']:<10} | Score: {calc['blast_score']:<3} | Unattended: {unattended_str} | {t.description}"
            )

    ZeroFluffConsole.success("Cartographie topologique vérifiée.")
    return 0


def handle_rollback(args: argparse.Namespace, state: LoopState, project_path: Path) -> int:
    """Point-in-Time Recovery (PITR) déterministe."""
    project_name = args.project or (state.project_name if state else "mLoop")
    step = getattr(args, "step", None)
    selective = getattr(args, "target", None)

    ZeroFluffConsole.section(f"Restauration Déterministe Point-in-Time - {project_name}")

    if not step:
        # Afficher la liste des points de restauration disponibles
        points = AgentStateRollbackEngine.list_restore_points(project_path)
        if not points:
            ZeroFluffConsole.warning("Aucun checkpoint disponible pour ce projet.")
            return 0

        ZeroFluffConsole.info(f"{len(points)} point(s) de restauration horodaté(s) disponible(s) :")
        for p in points:
            ZeroFluffConsole.info(
                f"  [Étape {p['step']}] {p['filename']} | Phase: {p['phase']} | Date: {p['datetime_utc']} | SHA-256: {p['sha256'][:12]}... ({p['size_bytes']} o)"
            )
        ZeroFluffConsole.info("Pour restaurer une étape, exécutez : python src/swarm.py rollback --step <n>")
        return 0

    res = AgentStateRollbackEngine.rollback_to_step(
        project_name=project_name,
        step=step,
        project_path=project_path,
        selective_partition=selective,
    )

    if not res["success"]:
        ZeroFluffConsole.error(f"Échec de la restauration : {res.get('error')}")
        return 1

    ZeroFluffConsole.success(
        f"État restauré avec succès à l'étape {res['restored_step']} depuis {res['checkpoint_file']} (Phase: {res['phase']})."
    )
    ZeroFluffConsole.info(f"Empreinte d'intégrité SHA-256 validée : {res['sha256']}")
    if res.get("selective_partition"):
        ZeroFluffConsole.info(f"Partition sélective isolée : {res['selective_partition']}")
    return 0
