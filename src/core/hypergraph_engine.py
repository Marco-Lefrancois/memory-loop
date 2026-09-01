"""
Moteur d'Hypergraphes et Hyper-Story Units pour mLoop (Standard ADR-0343).
Inspiré par les concepts de Knowledge Abstracts (KA) et d'hyper-arêtes N-aires de Hyper-Extract.

Permet de modéliser les relations complexes entre User Stories, Personas, Routes API,
Règles Métier, Modèles DDD, Décisions d'Architecture (ADR) et Tests Gherkin 4 Piliers.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set


@dataclass
class HyperNode:
    """Représente une entité atomique typée dans l'hypergraphe."""
    node_id: str
    node_type: str  # 'Story', 'Persona', 'ApiContract', 'BusinessRule', 'DataModel', 'ADR', 'GherkinTest', 'UiComponent'
    label: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    valid_from: Optional[str] = None
    deprecated_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "node_type": self.node_type,
            "label": self.label,
            "metadata": self.metadata,
            "valid_from": self.valid_from,
            "deprecated_at": self.deprecated_at
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HyperNode":
        return cls(
            node_id=data["node_id"],
            node_type=data["node_type"],
            label=data["label"],
            metadata=data.get("metadata", {}),
            valid_from=data.get("valid_from"),
            deprecated_at=data.get("deprecated_at")
        )


@dataclass
class HyperEdge:
    """
    Représente une hyper-arête reliant simultanément N nœuds.
    Exemple : Hyper-Story Unit reliant {Story, Persona, API, BusinessRule, DataModel, ADR, GherkinTest}.
    """
    edge_id: str
    edge_type: str  # 'STORY_UNIT', 'FEATURE_SLICE', 'ARCH_DEPENDENCY', 'DATA_FLOW'
    node_ids: Set[str] = field(default_factory=set)
    label: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    status: str = "DRAFT"  # 'DRAFT', 'GRILL_IN_PROGRESS', 'READY_FOR_DEV', 'DONE'
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "edge_id": self.edge_id,
            "edge_type": self.edge_type,
            "node_ids": sorted(list(self.node_ids)),
            "label": self.label,
            "metadata": self.metadata,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HyperEdge":
        return cls(
            edge_id=data["edge_id"],
            edge_type=data["edge_type"],
            node_ids=set(data.get("node_ids", [])),
            label=data.get("label", ""),
            metadata=data.get("metadata", {}),
            status=data.get("status", "DRAFT"),
            created_at=data.get("created_at", datetime.now(timezone.utc).isoformat()),
            updated_at=data.get("updated_at", datetime.now(timezone.utc).isoformat())
        )


@dataclass
class HypergraphMergeReport:
    """Rapport de fusion incrémentale de deux hypergraphes."""
    added_nodes: List[str] = field(default_factory=list)
    updated_nodes: List[str] = field(default_factory=list)
    added_edges: List[str] = field(default_factory=list)
    updated_edges: List[str] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return bool(self.added_nodes or self.updated_nodes or self.added_edges or self.updated_edges)


class HypergraphKnowledgeAbstract:
    """
    Knowledge Abstract persistant basé sur un modèle Hypergraphe N-aire.
    Permet l'interrogation ultra-rapide et l'isolation de sous-contextes pour agents IA.
    """

    def __init__(self, project_name: str = "default", metadata: Optional[Dict[str, Any]] = None):
        self.project_name = project_name
        self.metadata = metadata or {}
        self.nodes: Dict[str, HyperNode] = {}
        self.edges: Dict[str, HyperEdge] = {}

    def add_node(self, node: HyperNode) -> None:
        """Ajoute ou met à jour un nœud dans l'hypergraphe."""
        self.nodes[node.node_id] = node

    def add_hyper_edge(self, edge: HyperEdge) -> None:
        """Ajoute ou met à jour une hyper-arête."""
        self.edges[edge.edge_id] = edge

    def get_node(self, node_id: str) -> Optional[HyperNode]:
        return self.nodes.get(node_id)

    def get_edge(self, edge_id: str) -> Optional[HyperEdge]:
        return self.edges.get(edge_id)

    def create_story_unit(
        self,
        story_id: str,
        title: str,
        persona: Optional[str] = None,
        api_contracts: Optional[List[str]] = None,
        business_rules: Optional[List[str]] = None,
        data_models: Optional[List[str]] = None,
        adrs: Optional[List[str]] = None,
        gherkin_scenarios: Optional[List[str]] = None,
        ui_components: Optional[List[str]] = None,
        status: str = "DRAFT"
    ) -> HyperEdge:
        """
        Crée une Hyper-Story Unit canonique reliant de manière atomique
        tous les éléments constitutifs du récit.
        """
        node_ids: Set[str] = set()

        # Nœud Story principal
        story_node_id = f"STORY:{story_id}"
        self.add_node(HyperNode(node_id=story_node_id, node_type="Story", label=title, metadata={"story_id": story_id}))
        node_ids.add(story_node_id)

        # Persona
        if persona:
            persona_id = f"PERSONA:{persona.lower().replace(' ', '_')}"
            self.add_node(HyperNode(node_id=persona_id, node_type="Persona", label=persona))
            node_ids.add(persona_id)

        # Routes API
        if api_contracts:
            for api in api_contracts:
                api_id = f"API:{api}"
                self.add_node(HyperNode(node_id=api_id, node_type="ApiContract", label=api))
                node_ids.add(api_id)

        # Règles Métier
        if business_rules:
            for br in business_rules:
                br_id = f"BR:{br}"
                self.add_node(HyperNode(node_id=br_id, node_type="BusinessRule", label=br))
                node_ids.add(br_id)

        # Modèles de données
        if data_models:
            for mdl in data_models:
                mdl_id = f"MODEL:{mdl}"
                self.add_node(HyperNode(node_id=mdl_id, node_type="DataModel", label=mdl))
                node_ids.add(mdl_id)

        # ADRs
        if adrs:
            for adr in adrs:
                adr_id = f"ADR:{adr}"
                self.add_node(HyperNode(node_id=adr_id, node_type="ADR", label=adr))
                node_ids.add(adr_id)

        # Scénarios Gherkin
        if gherkin_scenarios:
            for sc in gherkin_scenarios:
                sc_id = f"TEST:{sc}"
                self.add_node(HyperNode(node_id=sc_id, node_type="GherkinTest", label=sc))
                node_ids.add(sc_id)

        # Composants UI
        if ui_components:
            for ui in ui_components:
                ui_id = f"UI:{ui}"
                self.add_node(HyperNode(node_id=ui_id, node_type="UiComponent", label=ui))
                node_ids.add(ui_id)

        edge_id = f"EDGE_STORY_{story_id}"
        edge = HyperEdge(
            edge_id=edge_id,
            edge_type="STORY_UNIT",
            node_ids=node_ids,
            label=f"Story Unit: {title} ({story_id})",
            status=status,
            metadata={"story_id": story_id}
        )
        self.add_hyper_edge(edge)
        return edge

    def get_hyper_story_unit(self, story_id: str) -> Optional[Dict[str, Any]]:
        """
        Retourne le Knowledge Abstract complet d'une User Story :
        L'hyper-arête et la liste dégroupée de tous les nœuds connectés.
        """
        edge_id = f"EDGE_STORY_{story_id}"
        edge = self.edges.get(edge_id)
        if not edge:
            # Recherche par metadata
            for e in self.edges.values():
                if e.metadata.get("story_id") == story_id or f"STORY:{story_id}" in e.node_ids:
                    edge = e
                    break

        if not edge:
            return None

        connected_nodes = [self.nodes[nid].to_dict() for nid in edge.node_ids if nid in self.nodes]
        return {
            "story_id": story_id,
            "edge": edge.to_dict(),
            "nodes_by_type": self._group_nodes_by_type([self.nodes[nid] for nid in edge.node_ids if nid in self.nodes]),
            "connected_nodes": connected_nodes
        }

    def _group_nodes_by_type(self, nodes: List[HyperNode]) -> Dict[str, List[Dict[str, Any]]]:
        grouped: Dict[str, List[Dict[str, Any]]] = {}
        for n in nodes:
            grouped.setdefault(n.node_type, []).append(n.to_dict())
        return grouped

    def find_related_nodes(self, node_id: str) -> List[HyperNode]:
        """Trouve tous les nœuds co-présents dans au moins une hyper-arête commune."""
        related_ids: Set[str] = set()
        for edge in self.edges.values():
            if node_id in edge.node_ids:
                related_ids.update(edge.node_ids)
        related_ids.discard(node_id)
        return [self.nodes[nid] for nid in related_ids if nid in self.nodes]

    def query(self, filter_func: Callable[[HyperEdge], bool]) -> List[HyperEdge]:
        """Interroge les hyper-arêtes selon un prédicat de filtrage."""
        return [e for e in self.edges.values() if filter_func(e)]

    def merge_with(self, other: "HypergraphKnowledgeAbstract") -> HypergraphMergeReport:
        """
        Fusionne un autre hypergraphe de manière incrémentale (Incremental Knowledge Evolution).
        Détecte les ajouts et modifications de nœuds et d'hyper-arêtes.
        """
        report = HypergraphMergeReport()

        # Fusion des nœuds
        for nid, node in other.nodes.items():
            if nid not in self.nodes:
                self.nodes[nid] = node
                report.added_nodes.append(nid)
            else:
                existing = self.nodes[nid]
                if existing.label != node.label or existing.metadata != node.metadata:
                    self.nodes[nid] = node
                    report.updated_nodes.append(nid)

        # Fusion des hyper-arêtes
        for eid, edge in other.edges.items():
            if eid not in self.edges:
                self.edges[eid] = edge
                report.added_edges.append(eid)
            else:
                existing = self.edges[eid]
                if existing.node_ids != edge.node_ids or existing.status != edge.status or existing.metadata != edge.metadata:
                    existing.node_ids.update(edge.node_ids)
                    existing.status = edge.status
                    existing.metadata.update(edge.metadata)
                    existing.updated_at = datetime.now(timezone.utc).isoformat()
                    report.updated_edges.append(eid)

        return report

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_name": self.project_name,
            "version": "1.0",
            "metadata": self.metadata,
            "stats": {
                "total_nodes": len(self.nodes),
                "total_edges": len(self.edges)
            },
            "nodes": {nid: n.to_dict() for nid, n in self.nodes.items()},
            "edges": {eid: e.to_dict() for eid, e in self.edges.items()}
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HypergraphKnowledgeAbstract":
        ka = cls(project_name=data.get("project_name", "default"), metadata=data.get("metadata", {}))
        for nid, ndata in data.get("nodes", {}).items():
            ka.nodes[nid] = HyperNode.from_dict(ndata)
        for eid, edata in data.get("edges", {}).items():
            ka.edges[eid] = HyperEdge.from_dict(edata)
        return ka

    def save_to_file(self, file_path: Path) -> None:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(self.to_json(indent=2), encoding="utf-8")

    @classmethod
    def load_from_file(cls, file_path: Path) -> "HypergraphKnowledgeAbstract":
        if not file_path.exists():
            raise FileNotFoundError(f"Fichier d'hypergraphe introuvable : {file_path}")
        data = json.loads(file_path.read_text(encoding="utf-8"))
        return cls.from_dict(data)

    def export_obsidian_vault(self, output_dir: Path) -> None:
        """
        Exporte l'hypergraphe en coffre Obsidian avec liens bidirectionnels [[wikilinks]].
        Standard ADR-0337 & Inspiration Hyper-Extract.
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        stories_dir = output_dir / "Stories"
        entities_dir = output_dir / "Entities"
        stories_dir.mkdir(exist_ok=True)
        entities_dir.mkdir(exist_ok=True)

        # Fiches d'entités
        for node in self.nodes.values():
            clean_name = node.node_id.replace(":", "_").replace("/", "_")
            node_file = entities_dir / f"{clean_name}.md"
            lines = [
                f"# {node.label} (`{node.node_id}`)",
                "",
                f"**Type :** `{node.node_type}`",
                ""
            ]
            if node.metadata:
                lines.append("## 📋 Métadonnées")
                lines.append("```json")
                lines.append(json.dumps(node.metadata, indent=2, ensure_ascii=False))
                lines.append("```")
                lines.append("")

            # Liens vers les hyper-arêtes participantes
            participating_edges = [e for e in self.edges.values() if node.node_id in e.node_ids]
            if participating_edges:
                lines.append("## 🔗 Hyper-Story Units Participantes")
                for e in participating_edges:
                    clean_edge = e.edge_id.replace(":", "_")
                    lines.append(f"* [[{clean_edge}|{e.label}]] (Statut: `{e.status}`)")
                lines.append("")

            node_file.write_text("\n".join(lines), encoding="utf-8")

        # Fiches d'hyper-arêtes (Story Units)
        for edge in self.edges.values():
            clean_edge = edge.edge_id.replace(":", "_")
            edge_file = stories_dir / f"{clean_edge}.md"
            lines = [
                f"# {edge.label}",
                "",
                f"**ID Arête :** `{edge.edge_id}` | **Type :** `{edge.edge_type}` | **Statut :** `{edge.status}`",
                "",
                "## 🕸️ Composants Reliés (Hyper-Arête N-aire)",
                ""
            ]
            for nid in sorted(edge.node_ids):
                if nid in self.nodes:
                    node = self.nodes[nid]
                    clean_node = node.node_id.replace(":", "_").replace("/", "_")
                    lines.append(f"* `{node.node_type}` : [[{clean_node}|{node.label}]]")
                else:
                    lines.append(f"* `{nid}`")

            lines.append("")
            lines.append(f"*Créé le : {edge.created_at} | Mis à jour le : {edge.updated_at}*")
            edge_file.write_text("\n".join(lines), encoding="utf-8")
