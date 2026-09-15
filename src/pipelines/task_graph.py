"""
Herdr Task Graph & Frontier Calculator (Inspiré du standard implement-spec / ADR-0367).
Modélise les dépendances bloquantes entre récits (DAG) et calcule la frontière de tâches prêtes.
"""
import re
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple


class TaskGraph:
    """Représente le graphe orienté acyclique (DAG) des récits d'un projet."""

    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.nodes: Dict[str, Dict[str, Any]] = {}
        self.dependencies: Dict[str, Set[str]] = {}  # story_id -> set of prerequisite story_ids
        self.reverse_dependencies: Dict[str, Set[str]] = {}  # story_id -> set of stories blocked by it

    def load_stories(self) -> None:
        """Scan et parse les métadonnées et blocages de tous les récits du projet."""
        candidates = []
        for folder in ["stories", "backlog", "docs/02-stories"]:
            d = self.project_path / folder
            if d.exists():
                candidates.extend(list(d.glob("US-*.md")) + list(d.glob("*.story.md")))

        for file_path in candidates:
            self._parse_story_file(file_path)

    def _parse_story_file(self, file_path: Path) -> None:
        """Extrait l'ID, le statut et les dépendances bloquantes d'un fichier story."""
        try:
            text = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return

        # Identification de l'ID de la story
        m_id = re.search(r"^(US-[A-Z0-9_-]+)", file_path.stem, re.IGNORECASE)
        story_id = m_id.group(1).upper() if m_id else file_path.stem.upper()

        # Identification du statut
        m_status = re.search(r"(?:Statut|Status)\s*:\s*([A-Z0-9_-]+)", text, re.IGNORECASE)
        status = m_status.group(1).upper() if m_status else "TODO"

        # Extraction des dépendances bloquantes (Blocked-By / Dépendances / Depends-On)
        blocked_by: Set[str] = set()
        block_matches = re.findall(r"(?:Blocked-By|Depends-On|Dépendances)\s*:\s*([^\r\n]+)", text, re.IGNORECASE)
        for line in block_matches:
            found_ids = re.findall(r"(US-[A-Z0-9_-]+)", line, re.IGNORECASE)
            for fid in found_ids:
                if fid.upper() != story_id:
                    blocked_by.add(fid.upper())

        self.nodes[story_id] = {
            "id": story_id,
            "path": file_path,
            "status": status,
            "is_done": status in ["DONE", "COMPLETED", "SHIPPED", "ACCEPTED"],
            "blocked_by": blocked_by,
        }
        self.dependencies[story_id] = blocked_by

        for dep in blocked_by:
            if dep not in self.reverse_dependencies:
                self.reverse_dependencies[dep] = set()
            self.reverse_dependencies[dep].add(story_id)

    def get_frontier(self) -> List[str]:
        """
        Calcule la 'Frontier' : liste ordonnée des récits non complétés
        dont TOUS les prérequis amont sont satisfaits (statut DONE).
        """
        frontier = []
        for story_id, data in self.nodes.items():
            if data["is_done"]:
                continue

            prereqs = self.dependencies.get(story_id, set())
            # Vérifier si tous les prérequis connus sont DONE
            all_prereqs_done = True
            for prereq_id in prereqs:
                if prereq_id in self.nodes:
                    if not self.nodes[prereq_id]["is_done"]:
                        all_prereqs_done = False
                        break
                else:
                    # Prérequis inconnu : considéré comme bloquant par sécurité (fail-closed)
                    all_prereqs_done = False
                    break

            if all_prereqs_done:
                frontier.append(story_id)

        return sorted(frontier)

    def to_dict(self) -> Dict[str, Any]:
        """Exporte l'état du graphe sous forme structurée."""
        return {
            "total_nodes": len(self.nodes),
            "frontier": self.get_frontier(),
            "nodes": {
                sid: {
                    "status": data["status"],
                    "is_done": data["is_done"],
                    "blocked_by": list(data["blocked_by"]),
                }
                for sid, data in self.nodes.items()
            },
        }


def get_ready_frontier(project_path: Path) -> List[str]:
    """Fonction utilitaire autonome pour calculer la frontière de tâches prêtes."""
    graph = TaskGraph(project_path)
    graph.load_stories()
    return graph.get_frontier()
