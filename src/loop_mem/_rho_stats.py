"""Statistiques mémoire RHO (MLOOP-145-BE — extraction ADR-0202 depuis rho_hybrid_search)."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Dict

from src.utils.logger import get_logger

logger = get_logger("loop_mem.rho_stats")


def get_rho_hybrid_stats(project_name: str) -> Dict[str, Any]:
    """Retourne les statistiques de la mémoire RHO pour un projet."""
    stats = {
        "project": project_name,
        "total_rules": 0,
        "active_rules": 0,
        "tombstone_rules": 0,
        "embedded_rules": 0,
    }

    try:
        db_path = Path("memory/loop_mem.db")
        if not db_path.exists():
            return stats

        with sqlite3.connect(str(db_path), timeout=10.0) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) as total, "
                "SUM(CASE WHEN embedding_json != '[]' THEN 1 ELSE 0 END) as embedded "
                "FROM rho_memory WHERE project_name = ?",
                (project_name,),
            )
            row = cursor.fetchone()
            if row:
                stats["total_rules"] = row["total"]
                stats["embedded_rules"] = row["embedded"]

        rho_file = Path("Projects") / project_name / "memory" / "rho_rules.yaml"
        if rho_file.exists():
            import yaml

            with open(rho_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
                rules = data.get("rules", [])
                stats["active_rules"] = sum(1 for r in rules if r.get("status") == "ACTIVE")
                stats["tombstone_rules"] = sum(1 for r in rules if r.get("status") == "TOMBSTONE")

    except Exception as exc:
        logger.debug("Erreur récupération stats RHO", exc_info=True)

    return stats
