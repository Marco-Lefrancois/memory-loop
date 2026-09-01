"""
Wayfinder Pipeline - mLoop
Meta-orchestration d'initiatives complexes dans le brouillard.
Génère et gère la carte des Decision Tickets (décisions d'architecture/métier à trancher).
Convertit dynamiquement les cartes d'initiative en graphes d'exécution DAG (Graph Engineering).
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Optional

WAYFINDER_MAP_TEMPLATE = """# 🧭 Wayfinder Map : {initiative_name}

> [!NOTE]
> Cette carte recense l'ensemble des **tickets de décision** (arbitrages, questions ouvertes OQ, choix d'architecture) nécessaires pour lever le brouillard avant le développement.

## Status de l'Initiative
- **Initiative** : {initiative_name}
- **Projet** : {project_name}
- **Statut** : {status}

## 🚦 Frontière des Décisions (Prêtes à trancher)
{frontier_section}

## 📋 Registre des Tickets de Décision
{tickets_section}

---
*Généré automatiquement par mLoop Wayfinder Engine.*
"""

class WayfinderEngine:
    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.backlog_dir = project_path / "backlog"
        self.map_file = self.backlog_dir / "wayfinder_map.md"

    def init_map(self, initiative_name: str) -> Path:
        """Initialise une nouvelle carte Wayfinder si elle n'existe pas encore."""
        self.backlog_dir.mkdir(parents=True, exist_ok=True)
        if not self.map_file.exists():
            content = WAYFINDER_MAP_TEMPLATE.format(
                initiative_name=initiative_name,
                project_name=self.project_path.name,
                status="IN_PROGRESS",
                frontier_section="- *Aucune décision sur la frontière pour le moment.*",
                tickets_section="- *Aucun ticket de décision enregistré.*"
            )
            self.map_file.write_text(content, encoding="utf-8")
        return self.map_file

    def to_dag(self, initiative_name: str = "Wayfinder_Initiative") -> "GraphRouter":
        """
        Converts the Wayfinder Decision Map into a runnable GraphRouter DAG instance.
        Creates TaskNodes for each ticket with dependency resolution.
        """
        from src.pipelines.graph_router import GraphRouter, TaskNode, NodeCategory, RiskLevel

        router = GraphRouter(initiative_name=initiative_name, project_dir=str(self.project_path))
        if not self.map_file.exists():
            return router

        content = self.map_file.read_text(encoding="utf-8")
        tickets = re.findall(r"### \[(.*?)\] (.*?)\n- \*\*Statut\*\* : (.*?)\n- \*\*Blocked By\*\* : (.*?)\n- \*\*Description\*\* : (.*?)\n\n", content, re.DOTALL)

        for tid, title, status, blockers_raw, desc in tickets:
            blockers = [b.strip() for b in blockers_raw.split(",") if b.strip() and b.strip() != "Aucun"]
            node = TaskNode(
                id=tid,
                role="plan",
                description=f"{title}: {desc.strip()}",
                blocked_by=blockers,
                category=NodeCategory.LLM_AGENT,
                risk_level=RiskLevel.HIGH if "ADR" in title or "Règle" in title else RiskLevel.MEDIUM
            )
            router.add_node(node)

        return router
