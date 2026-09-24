"""
Wayfinder Pipeline - mLoop (MLOOP-222-BE / ADR-014).

Méta-orchestration d'initiatives complexes dans le brouillard.
Gère la carte des Decision Tickets (arbitrages HITL et investigations AFK).
Conforme ADR-0202 (<=300 lignes, <=15 Ko) et ADR-0369.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.utils.logger import get_logger

logger = get_logger("pipelines.wayfinder")

WAYFINDER_MAP_TEMPLATE = """# 🧭 Wayfinder Map : {initiative_name}

> [!NOTE]
> Cette carte recense l'ensemble des **tickets de décision** (arbitrages HITL, recherches AFK, choix d'architecture) nécessaires pour dissiper le brouillard de guerre.

## 🎯 Destination & Objectif Stratégique
- **Initiative** : {initiative_name}
- **Objectif** : {goal}
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
        self.canonical_dir = project_path / "memory" / "wayfinder"
        self.legacy_file = project_path / "backlog" / "wayfinder_map.md"

        # Emplacement canonique prioritaire
        self.map_file = (
            self.canonical_dir / "wayfinder_map.md"
            if not self.legacy_file.exists() or (self.canonical_dir / "wayfinder_map.md").exists()
            else self.legacy_file
        )

    def init_map(self, initiative_name: str, goal: Optional[str] = None) -> Path:
        """Initialise une nouvelle carte Wayfinder sous memory/wayfinder/."""
        self.canonical_dir.mkdir(parents=True, exist_ok=True)
        target_file = self.canonical_dir / "wayfinder_map.md"
        self.map_file = target_file

        if not target_file.exists():
            content = WAYFINDER_MAP_TEMPLATE.format(
                initiative_name=initiative_name,
                goal=goal or "Lever les ambiguïtés architecturales et dissiper le brouillard.",
                project_name=self.project_path.name,
                status="IN_PROGRESS",
                frontier_section="- *Aucune décision sur la frontière pour le moment.*",
                tickets_section="- *Aucun ticket de décision enregistré.*",
            )
            target_file.write_text(content, encoding="utf-8")
        return target_file

    def _parse_tickets(self) -> Dict[str, Dict[str, Any]]:
        """Parse l'ensemble des tickets consignés dans le registre."""
        if not self.map_file.exists():
            return {}

        content = self.map_file.read_text(encoding="utf-8")
        pattern = re.compile(
            r"### \[(?P<id>.*?)\] (?P<title>.*?)\n"
            r"(?:- \*\*Type\*\* : (?P<kind>HITL|AFK)\n)?"
            r"- \*\*Statut\*\* : (?P<status>.*?)\n"
            r"- \*\*Blocked By\*\* : (?P<blockers>.*?)\n"
            r"- \*\*Description\*\* : (?P<desc>.*?)\n"
            r"(?:- \*\*Décision\*\* : (?P<decision>.*?)\n)?",
            re.MULTILINE,
        )

        tickets: Dict[str, Dict[str, Any]] = {}
        for m in pattern.finditer(content):
            tid = m.group("id").strip()
            blockers_raw = m.group("blockers").strip()
            blockers = (
                [b.strip() for b in blockers_raw.split(",") if b.strip() and b.strip() != "Aucun"]
                if blockers_raw
                else []
            )
            tickets[tid] = {
                "id": tid,
                "title": m.group("title").strip(),
                "kind": (m.group("kind") or "HITL").strip(),
                "status": m.group("status").strip(),
                "blocked_by": blockers,
                "description": m.group("desc").strip(),
                "decision": (m.group("decision") or "").strip(),
            }
        return tickets

    def add_ticket(
        self,
        ticket_id: str,
        title: str,
        description: str,
        kind: str = "HITL",
        blocked_by: Optional[List[str]] = None,
    ) -> Path:
        """Ajoute ou met à jour un ticket de décision typé (HITL vs AFK)."""
        self.init_map(self.project_path.name)
        tickets = self._parse_tickets()

        tickets[ticket_id] = {
            "id": ticket_id,
            "title": title,
            "kind": kind.upper() if kind.upper() in ("HITL", "AFK") else "HITL",
            "status": "OPEN",
            "blocked_by": blocked_by or [],
            "description": description,
            "decision": "",
        }
        self._rewrite_map(tickets)
        return self.map_file

    def get_frontier(self) -> List[Dict[str, Any]]:
        """Calcule les tickets éligibles à la frontière (dont les dépendances sont résolues)."""
        tickets = self._parse_tickets()
        frontier: List[Dict[str, Any]] = []

        resolved_ids = {tid for tid, t in tickets.items() if t["status"] == "RESOLVED"}
        for tid, t in tickets.items():
            if t["status"] != "RESOLVED":
                all_blockers_done = all(b in resolved_ids for b in t["blocked_by"])
                if all_blockers_done:
                    frontier.append(t)
        return frontier

    def resolve_ticket(self, ticket_id: str, decision: str) -> bool:
        """Marque un ticket comme résolu et consigne l'arbitrage dans la carte."""
        tickets = self._parse_tickets()
        if ticket_id not in tickets:
            logger.warning("Ticket %s introuvable dans la carte Wayfinder", ticket_id)
            return False

        tickets[ticket_id]["status"] = "RESOLVED"
        tickets[ticket_id]["decision"] = decision
        self._rewrite_map(tickets)
        return True

    def _rewrite_map(self, tickets: Dict[str, Dict[str, Any]]) -> None:
        """Réécrit la carte Wayfinder avec la frontière mise à jour."""
        resolved_ids = {tid for tid, t in tickets.items() if t["status"] == "RESOLVED"}
        frontier_items = [
            t for t in tickets.values()
            if t["status"] != "RESOLVED" and all(b in resolved_ids for b in t["blocked_by"])
        ]

        if frontier_items:
            f_lines = [
                f"- **[{t['id']}]** `{t['kind']}` {t['title']} — *{t['description']}*"
                for t in frontier_items
            ]
            frontier_section = "\n".join(f_lines)
        else:
            frontier_section = "- *Aucune décision pendante sur la frontière.*"

        t_blocks = []
        for t in tickets.values():
            blockers_str = ", ".join(t["blocked_by"]) if t["blocked_by"] else "Aucun"
            dec_line = f"\n- **Décision** : {t['decision']}" if t["decision"] else ""
            block = (
                f"### [{t['id']}] {t['title']}\n"
                f"- **Type** : {t['kind']}\n"
                f"- **Statut** : {t['status']}\n"
                f"- **Blocked By** : {blockers_str}\n"
                f"- **Description** : {t['description']}"
                f"{dec_line}\n"
            )
            t_blocks.append(block)

        tickets_section = "\n".join(t_blocks) if t_blocks else "- *Aucun ticket enregistré.*"

        initiative = self.project_path.name
        goal = "Lever les ambiguïtés architecturales."
        if self.map_file.exists():
            old = self.map_file.read_text(encoding="utf-8")
            m_init = re.search(r"# 🧭 Wayfinder Map : (.*?)\n", old)
            if m_init:
                initiative = m_init.group(1).strip()
            m_goal = re.search(r"- \*\*Objectif\*\* : (.*?)\n", old)
            if m_goal:
                goal = m_goal.group(1).strip()

        content = WAYFINDER_MAP_TEMPLATE.format(
            initiative_name=initiative,
            goal=goal,
            project_name=self.project_path.name,
            status="IN_PROGRESS" if frontier_items else "COMPLETED",
            frontier_section=frontier_section,
            tickets_section=tickets_section,
        )
        self.map_file.write_text(content, encoding="utf-8")

    def to_dag(self, initiative_name: str = "Wayfinder_Initiative") -> "GraphRouter":
        """Convertit la carte en DAG exécutable GraphRouter."""
        from src.pipelines.graph_router import GraphRouter, TaskNode, NodeCategory, RiskLevel

        router = GraphRouter(initiative_name=initiative_name, project_dir=str(self.project_path))
        tickets = self._parse_tickets()

        for tid, t in tickets.items():
            is_high = "ADR" in t["title"] or "Règle" in t["title"] or "Regle" in t["title"]
            risk = RiskLevel.HIGH if is_high else (RiskLevel.LOW if t.get("kind") == "AFK" else RiskLevel.MEDIUM)
            node = TaskNode(
                id=tid,
                role="plan",
                description=f"{t['title']}: {t['description']}",
                blocked_by=t["blocked_by"],
                category=NodeCategory.LLM_AGENT,
                risk_level=risk,
            )
            router.add_node(node)
        return router
