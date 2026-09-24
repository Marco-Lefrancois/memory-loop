# src/state/_state_serializer.py — Mixin Sérialiseur LoopState (MLOOP-173-BE)
# Familles : checkpoint, save_to_graph, load_from_graph, save_to_audit,
#            load_from_audit, add_to_journal, discover_backlog
# INTERDIT : instancier LoopState ou ProjectState ici (§3.2 singleton)

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.state._state_core import (
    JournalEntry,
    KnowledgeGraph,
    SavepointManager,
    SprintBacklogItem,
    StoryStatus,
    logger,
)


class StateSerializerMixin:
    """
    Mixin portant les méthodes I/O de LoopState.
    Ne contient aucune instanciation de LoopState (règle §3.2).
    Doit être combiné avec StateAccessorsMixin et BaseModel.
    """

    # ─── Typing stubs (résolus par LoopState au runtime via BaseModel) ───
    project_name: str
    graph_path: str
    last_checkpoint_timestamp: float
    checkpoint_interval_seconds: int
    journal: List["JournalEntry"]
    jira_project_key: Optional[str]
    jira_epic_key: Optional[str]
    jira_default_billing_id: Optional[str]
    jira_default_component_id: Optional[str]
    jira_default_subtasks: List[str]
    jira_subtask_mapping: Dict[str, str]
    knowledge_graph: "KnowledgeGraph"
    sprint_backlog: List["SprintBacklogItem"]

    def checkpoint(
        self, project_path: Optional[Path] = None, reason: str = "in_flight", force: bool = False
    ) -> Optional[Path]:
        """Crée un point de contrôle atomique sur disque si le délai est atteint ou forcé."""
        import time

        if not force and not self.should_checkpoint():  # type: ignore[attr-defined]
            return None
        target_proj = project_path or (
            Path("Projects") / self.project_name if self.project_name else None
        )
        state_data = self.model_dump(exclude={"sprint_backlog", "knowledge_graph"})  # type: ignore[attr-defined]
        saved_file = SavepointManager.save_checkpoint(
            state_data, project_path=target_proj, reason=reason
        )
        self.last_checkpoint_timestamp = time.time()
        logger.info(
            f"[CHECKPOINT] État in-flight sauvegardé sous {saved_file.name} (Raison: {reason})"
        )
        return saved_file

    def load_from_graph(self, project_path: Path) -> None:
        """Charge l'état depuis le nœud 'ML_ACTIVE_STATE' du graphe Graphify."""
        graph_file = project_path / self.graph_path
        if not graph_file.exists():
            return
        try:
            with open(graph_file, "r", encoding="utf-8") as f:
                graph_data = json.load(f)
            nodes = graph_data.get("nodes", [])
            state_node = next((n for n in nodes if n.get("label") == "ML_ACTIVE_STATE"), None)
            if state_node and "properties" in state_node:
                from src.state import LoopState  # noqa: PLC0415

                loaded_state = LoopState.model_validate(state_node["properties"])
                for field in self.__class__.model_fields:  # type: ignore[attr-defined]
                    if field not in ("sprint_backlog", "journal", "knowledge_graph"):
                        setattr(self, field, getattr(loaded_state, field))
            journal_nodes = [n for n in nodes if n.get("category") == "JournalEntry"]
            journal_entries: List[JournalEntry] = []
            for n in journal_nodes:
                if "properties" in n:
                    try:
                        journal_entries.append(JournalEntry.model_validate(n["properties"]))
                    except Exception as e:
                        logger.debug(
                            "Entrée de journal invalide ignorée lors du chargement du graphe",
                            exc_info=True,
                            extra={
                                "component": "state",
                                "operation": "load_from_graph",
                                "node_id": n.get("id", ""),
                                "error": str(e),
                            },
                        )
            journal_entries.sort(key=lambda x: x.timestamp)
            self.journal = journal_entries
        except Exception as e:
            logger.warning(
                "Chargement de l'état depuis le graphe échoué",
                exc_info=True,
                extra={
                    "component": "state",
                    "operation": "load_from_graph",
                    "graph_file": str(graph_file),
                    "error": str(e),
                },
            )

    def add_to_journal(
        self, event: str, details: str, impacted_nodes: Optional[List[str]] = None
    ) -> None:
        """Ajoute une entrée au journal et la lie sémantiquement au graphe."""
        entry = JournalEntry(event=event, details=details, impacted_nodes=impacted_nodes or [])
        self.journal.append(entry)

    def save_to_graph(self, project_path: Path) -> None:
        """Sauvegarde l'état actuel et le journal dans le graphe Graphify."""
        graph_file = project_path / self.graph_path
        if not graph_file.parent.exists():
            graph_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            state_data = self.model_dump(  # type: ignore[attr-defined]
                exclude={"sprint_backlog", "knowledge_graph", "journal"}
            )
            graph_data: Dict[str, Any] = {"nodes": [], "edges": []}
            if graph_file.exists():
                try:
                    with open(graph_file, "r", encoding="utf-8") as f:
                        graph_data = json.load(f)
                except Exception as e:
                    logger.debug(
                        "Lecture du graphe existant échouée, reconstruction à partir d'un squelette vide",
                        exc_info=True,
                        extra={
                            "component": "state",
                            "operation": "save_to_graph",
                            "graph_file": str(graph_file),
                            "error": str(e),
                        },
                    )
            nodes_list = graph_data.get("nodes", [])
            edges_list = graph_data.get("edges", [])
            existing_node_ids = {n.get("id") for n in nodes_list}
            state_node = next((n for n in nodes_list if n.get("label") == "ML_ACTIVE_STATE"), None)
            if state_node:
                state_node["properties"] = state_data
            else:
                nodes_list.append(
                    {
                        "id": "ml_active_state",
                        "label": "ML_ACTIVE_STATE",
                        "category": "LoopState",
                        "properties": state_data,
                    }
                )
            for entry in self.journal:
                entry_id = f"journal_{entry.id}"
                if entry_id not in existing_node_ids:
                    nodes_list.append(
                        {
                            "id": entry_id,
                            "label": f"Journal: {entry.event}",
                            "category": "JournalEntry",
                            "properties": entry.model_dump(),
                        }
                    )
                    for node_label in entry.impacted_nodes:
                        edges_list.append(
                            {"source": entry_id, "target": node_label, "relation": "IMPACTS"}
                        )
            graph_data["nodes"] = nodes_list
            graph_data["edges"] = edges_list
            tmp_graph_file = graph_file.with_suffix(".tmp")
            with open(tmp_graph_file, "w", encoding="utf-8") as f:
                json.dump(graph_data, f, indent=2, ensure_ascii=False)
            tmp_graph_file.replace(graph_file)
        except Exception as e:
            logger.warning(f"Erreur lors de la sauvegarde dans le graphe ({graph_file}): {e}")

    def load_from_audit(self, project_path: Path) -> None:
        """Charge l'état depuis le graphe et la configuration du projet."""
        self.load_from_graph(project_path)
        self.discover_backlog(project_path)
        jira_cfg = project_path / "jira_config.json"
        if jira_cfg.exists():
            try:
                with open(jira_cfg, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                for key in (
                    "jira_project_key",
                    "jira_epic_key",
                    "jira_default_billing_id",
                    "jira_default_component_id",
                    "jira_default_subtasks",
                    "jira_subtask_mapping",
                ):
                    if key in cfg:
                        setattr(self, key, cfg[key])
            except Exception as e:
                logger.debug(f"Lecture jira_config {jira_cfg} ignorée: {e}")
        kg_file = project_path / "memory" / "knowledge_graph.json"
        if kg_file.exists():
            try:
                with open(kg_file, "r", encoding="utf-8") as f:
                    g_data = json.load(f)
                self.knowledge_graph = KnowledgeGraph(
                    nodes=g_data.get("nodes", []), edges=g_data.get("edges", [])
                )
            except Exception as e:
                logger.debug(f"Lecture knowledge_graph {kg_file} ignorée: {e}")

    def save_to_audit(self, project_path: Path) -> None:
        """Sauvegarde l'état dans le graphe."""
        self.save_to_graph(project_path)

    def discover_backlog(self, project_path: Path) -> None:
        """Scans backlog folder and populates sprint_backlog from Markdown Frontmatter (ADR-0011)."""
        import re
        import yaml

        backlog_dir = project_path / "backlog"
        if not backlog_dir.exists():
            return
        discovered_items = []
        for md_file in backlog_dir.rglob("*.md"):
            if any(p in ("archive", "_archive", "archive_deprecated", "reference") for p in md_file.parts):
                continue
            try:
                content = md_file.read_text(encoding="utf-8")
                match = re.search(r"^---(.*?)---", content, re.DOTALL | re.MULTILINE)
                if match:
                    frontmatter = yaml.safe_load(match.group(1))
                    title_match = re.search(r"^#\s*(.*)$", content, re.MULTILINE)
                    raw_title = title_match.group(1).strip() if title_match else md_file.stem
                    clean_title = re.sub(
                        r"^(?:\[.*?\]\s*)?(?:STORY|ST|REC)[A-Z0-9\-]*\s*[:\-]\s*",
                        "",
                        raw_title,
                        flags=re.IGNORECASE,
                    ).strip()
                    raw_status = str(frontmatter.get("status", "OPEN"))
                    item = SprintBacklogItem(
                        id=frontmatter.get("id", md_file.stem),
                        title=clean_title,
                        description=md_file.relative_to(backlog_dir).as_posix(),
                        components=frontmatter.get("components", []),
                        jira_key=frontmatter.get("jira_key"),
                        status=StoryStatus.from_raw(raw_status),
                        invest_score=str(frontmatter.get("invest_score", "N/A")),
                    )
                    discovered_items.append(item)
            except Exception as e:
                logger.debug(
                    "Parsing d'une story du sprint backlog échoué, fichier ignoré",
                    exc_info=True,
                    extra={
                        "component": "state",
                        "operation": "load_sprint_backlog",
                        "story_file": str(md_file),
                        "error": str(e),
                    },
                )
                continue
        self.sprint_backlog = discovered_items
