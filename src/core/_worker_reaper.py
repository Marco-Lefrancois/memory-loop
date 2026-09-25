# -*- coding: utf-8 -*-
"""
_worker_reaper.py - Teardown Gate & Zero-Zombie Policy pour workers Herdr (ADR-0202 <=300L).

Extrait de herdr_worker_core.py pour respecter le plafond modulaire (ADR-0202).
Regroupe l'audit et la purge déterministe des volets/agents orphelins
(ADR-0306 / ADR-0345). Conforme ADR-0369 : logging structuré, zéro except nu.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

# Nom de logger préservé (byte-compatible) : le teardown gate a été extrait de
# herdr_worker_core.py mais conserve le canal "mloop.herdr_worker_core" attendu
# par les contrats d'observabilité existants (tests/test_herdr_adapter.py).
logger = logging.getLogger("mloop.herdr_worker_core")


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
