"""
Moteur de Calcul de Rayon d'Impact (Blast Radius Analysis) — 100% Python Native.

Analyse le graphe de dépendances AST et de connaissances (Graphify) :
- Identifie les dépendances ascendantes (fichiers/modules qui dépendent du composant).
- Identifie les dépendances descendantes (contrats, modèles, services appelés).
- Calcule le score de rayon d'impact et les tests à rejouer.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Set, Any, Optional


class BlastRadiusEngine:
    """Moteur d'analyse d'impact de code et de règles d'affaires."""

    def __init__(self, project_root: Path | str) -> None:
        self.project_root = Path(project_root)
        self.knowledge_graph = self._load_graph()

    def _load_graph(self) -> Dict[str, Any]:
        """Charge le graphe de connaissances sémantique et AST."""
        candidates = [
            self.project_root / "graphify-out" / "graph.json",
            self.project_root / "memory" / "knowledge_graph.json",
            Path("graphify-out") / "graph.json",
        ]
        for p in candidates:
            if p.exists():
                try:
                    return json.loads(p.read_text(encoding="utf-8"))
                except Exception:
                    pass
        return {"nodes": [], "edges": [], "links": []}

    def compute_blast_radius(self, target: str, max_depth: int = 2) -> Dict[str, Any]:
        """
        Calcule le rayon d'impact ascendant et descendant pour une cible (chemin de fichier, symbole ou RM-XXX).
        """
        nodes = self.knowledge_graph.get("nodes", [])
        edges = self.knowledge_graph.get("links", self.knowledge_graph.get("edges", []))

        target_clean = target.replace("\\", "/").lower()
        target_name = Path(target).stem.lower()

        # 1. Trouver le ou les nœuds correspondants
        matched_node_ids = set()
        for n in nodes:
            nid = str(n.get("id", "")).lower()
            label = str(n.get("label", n.get("name", ""))).lower()
            if target_clean in nid or target_name == label or target_name == nid:
                matched_node_ids.add(str(n.get("id", "")))

        # 2. Explorer les dépendances ascendantes (inbound) et descendantes (outbound)
        upstream_impact: Set[str] = set()    # Qui m'appelle
        downstream_impact: Set[str] = set()  # Qui j'appelle

        for e in edges:
            src = str(e.get("source", ""))
            tgt = str(e.get("target", ""))
            
            if any(m.lower() == src.lower() for m in matched_node_ids):
                downstream_impact.add(tgt)
            if any(m.lower() == tgt.lower() for m in matched_node_ids):
                upstream_impact.add(src)

        # 3. Détecter les tests et routes impactés
        affectedTests = [n for n in upstream_impact if "test" in n.lower() or "spec" in n.lower()]
        affectedRoutes = [n for n in upstream_impact | downstream_impact if "route" in n.lower() or "controller" in n.lower() or "api" in n.lower()]
        affectedModels = [n for n in upstream_impact | downstream_impact if "model" in n.lower() or "dto" in n.lower() or "schema" in n.lower()]

        # Calcul d'un score de risque de 1 à 10
        total_affected = len(upstream_impact) + len(downstream_impact)
        risk_score = min(10, max(1, total_affected * 2))

        return {
            "target": target,
            "matched_nodes": list(matched_node_ids),
            "upstream_dependencies": sorted(list(upstream_impact)),
            "downstream_dependencies": sorted(list(downstream_impact)),
            "affected_tests": sorted(affectedTests),
            "affected_routes": sorted(affectedRoutes),
            "affected_models": sorted(affectedModels),
            "total_nodes_affected": total_affected,
            "risk_score": risk_score,
            "risk_level": "ÉLEVÉ" if risk_score >= 7 else ("MOYEN" if risk_score >= 4 else "FAIBLE"),
        }

    def format_markdown_report(self, blast_result: Dict[str, Any]) -> str:
        """Formate le résultat d'impact en Markdown pour injection dans une User Story ou audit."""
        target = blast_result["target"]
        risk_level = blast_result["risk_level"]
        score = blast_result["risk_score"]

        lines = [
            f"### 💥 Analyse du Rayon d'Impact (Blast Radius : `{target}`)",
            f"- **Niveau de Risque** : `{risk_level}` (Score: `{score}/10`)",
            f"- **Composants Dépendants (Upstream)** : `{len(blast_result['upstream_dependencies'])}`",
            f"- **Contrats/Services Invoqués (Downstream)** : `{len(blast_result['downstream_dependencies'])}`",
        ]

        if blast_result["affected_routes"]:
            lines.append(f"- **Routes & Endpoints Touchés** : {', '.join(f'`{r}`' for r in blast_result['affected_routes'])}")

        if blast_result["affected_tests"]:
            lines.append(f"- **Tests Recommandés à Rejouer** : {', '.join(f'`{t}`' for t in blast_result['affected_tests'])}")

        return "\n".join(lines)


def calculate_blast_radius(project_root: Path | str, target: str) -> Dict[str, Any]:
    """Point d'entrée principal pour calculer le Blast Radius d'un composant."""
    engine = BlastRadiusEngine(project_root)
    return engine.compute_blast_radius(target)
