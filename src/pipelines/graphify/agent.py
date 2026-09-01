import json
import re
from pathlib import Path
import subprocess

from src.state import LoopState, KnowledgeGraph, ProjectLayout
from src.cli import ZeroFluffConsole

from src.pipelines.graphify.extractor import Extractor
from src.pipelines.graphify.builder import GraphBuilder


class GraphifyAgent:
    """
    SystÃ¨me 1 : Agent Graphify (FaÃ§ade modulaire - ADR-0010).
    Orchestre Extractor, Builder, et Indexer.
    IntÃ¨gre graphifyy pour les exports Obsidian et HTML.
    """

    def __init__(self):
        self.name = "Graphify"
        self.extractor = Extractor()
        self.builder = GraphBuilder()

    def execute(self, state: LoopState) -> LoopState:
        ZeroFluffConsole.step_s1(
            self.name, "Extraction et modelisation du graphe semantique..."
        )
        project_path = Path("Projects") / state.project_name

        # --- 1. Délégué au paquet officiel graphify ---
        ZeroFluffConsole.info(
            "[Graphify] Lancement du moteur officiel graphify pour la génération HTML/Obsidian..."
        )
        try:
            # Assure la création du dossier obsidian et html via le CLI officiel
            subprocess.run(
                ["graphify", "update", "."],
                cwd=str(project_path),
                capture_output=True,
                check=False,
                shell=True,
            )
            ZeroFluffConsole.success(
                "[Graphify] Exports interactifs (HTML/Obsidian) mis à jour avec succès."
            )
        except Exception as e:
            ZeroFluffConsole.warning(
                f"[Graphify] Erreur lors de l'exécution de graphify: {e}"
            )

        # --- 2. Enrichissement mLoop Custom ---
        global_docs_cache_dir = Path("memory") / "crawler" / "cache"
        self.builder.enrich_lexicon(global_docs_cache_dir)

        # Collecte des sources
        file_hashes = {}
        text_sources = []
        source_paths = []

        ref_dir = project_path / ProjectLayout.REFERENCE
        if ref_dir.exists():
            source_paths.extend(list(ref_dir.rglob("*.md")))
            # NOTE : les fichiers de code source (.cs, .py, .ts...) sous reference/ ne sont
            # PLUS injectes dans le moteur de lexique textuel Graphify (NLP sur ".split()").
            # Sur une codebase volumineuse (ex: milliers de .cs), la boucle O(n^2) de
            # detection d'associations dans GraphBuilder.add_text_nodes() devient quasi
            # non-terminante. Le code source reste indexe separement et de facon adaptee
            # (AST) par CodeGraph, en lecture seule. Frontiere Boundary Code vs Architecture.

        backlog_dir = project_path / ProjectLayout.BACKLOG
        if backlog_dir.exists():
            source_paths.extend(list(backlog_dir.rglob("*.md")))

        docs_cache_dir = project_path / ProjectLayout.MEMORY / "docs_cache"
        if docs_cache_dir.exists():
            source_paths.extend(list(docs_cache_dir.rglob("*.md")))

        if global_docs_cache_dir.exists():
            source_paths.extend(list(global_docs_cache_dir.rglob("*.md")))

        src_dir = project_path / ProjectLayout.SRC
        if src_dir.exists():
            for ext in ["*.py", "*.ts", "*.tsx", "*.js", "*.cs"]:
                source_paths.extend(list(src_dir.rglob(ext)))

        journal_path = project_path / ProjectLayout.JOURNAL / "JOURNAL.md"
        if journal_path.exists():
            source_paths.append(journal_path)

        import os

        cache_file = project_path / "memory" / "ingest_cache.json"
        graph_file = project_path / "memory" / "knowledge_graph.json"

        old_cache = {}
        if cache_file.exists():
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    old_cache = json.load(f)
            except Exception:
                pass

        file_hashes = {}
        for path in source_paths:
            try:
                try:
                    key_path = str(path.relative_to(project_path))
                except ValueError:
                    key_path = str(path)

                mtime = os.path.getmtime(path)
                cached_item = old_cache.get(key_path, {})
                if (
                    isinstance(cached_item, dict)
                    and cached_item.get("mtime") == mtime
                    and cached_item.get("hash")
                ):
                    h = cached_item["hash"]
                else:
                    h = self.extractor.calculate_sha256(path)

                if h:
                    file_hashes[key_path] = {"hash": h, "mtime": mtime}
            except (OSError, FileNotFoundError, PermissionError):
                continue

        cache_hit = False
        changed_details = []
        old_nodes_count = 0
        old_edges_count = 0

        if graph_file.exists():
            try:
                with open(graph_file, "r", encoding="utf-8") as f:
                    old_g = json.load(f)
                    old_nodes_count = len(old_g.get("nodes", []))
                    old_edges_count = len(old_g.get("edges", []))
            except Exception:
                pass

        if cache_file.exists() and graph_file.exists():
            try:
                if old_cache == file_hashes:
                    cache_hit = True
                else:
                    changed = [
                        Path(f).name
                        for f, data in file_hashes.items()
                        if old_cache.get(f, {}).get("hash") != data["hash"]
                        and f in old_cache
                    ]
                    added = [Path(f).name for f in file_hashes if f not in old_cache]
                    removed = [Path(f).name for f in old_cache if f not in file_hashes]
                    if changed:
                        changed_details.append(f"Modifiés: {', '.join(changed)}")
                    if added:
                        changed_details.append(f"Ajoutés: {', '.join(added)}")
                    if removed:
                        changed_details.append(f"Supprimés: {', '.join(removed)}")
            except Exception:
                pass
        else:
            changed_details.append("Initialisation complète du graphe.")

        if cache_hit:
            ZeroFluffConsole.success("Aucun changement detecte (Cache Hit SHA256).")
            try:
                with open(graph_file, "r", encoding="utf-8") as f:
                    g_data = json.load(f)
                    state.knowledge_graph = KnowledgeGraph(
                        nodes=g_data.get("nodes", []), edges=g_data.get("edges", [])
                    )
                return state
            except Exception:
                pass

        # --- 3. Construction des nÅ“uds mLoop ---
        physical_nodes = []
        physical_edges = []

        for path in source_paths:
            if "backlog" in path.parts:
                try:
                    content = path.read_text(encoding="utf-8")
                    k_m = re.search(r"jira_key:\s*([A-Z0-9-]+)", content)
                    id_m = re.search(r"id:\s*(US-\d+)", content)
                    lay_m = re.search(r"layer:\s*([\w-]+)", content)
                    epic_m = re.search(r"epic_key:\s*([A-Z0-9-]+)", content)

                    if k_m:
                        feat_id = k_m.group(1)
                        physical_nodes.append(
                            {
                                "id": feat_id,
                                "category": "Feature",
                                "properties": {
                                    "name": f"Feature {feat_id}",
                                    "local_id": id_m.group(1) if id_m else "",
                                    "layer": lay_m.group(1) if lay_m else "vertical",
                                    "file": path.name,
                                    "text_chunk": content,
                                },
                            }
                        )
                        if epic_m:
                            epic_id = epic_m.group(1)
                            # Ajouter le nœud Epic (sera dédupliqué par GraphBuilder au besoin)
                            physical_nodes.append(
                                {
                                    "id": epic_id,
                                    "category": "Epic",
                                    "properties": {
                                        "name": f"Epic {epic_id}",
                                        "layer": "business",
                                    },
                                }
                            )
                            # Lier la Feature à son Epic
                            physical_edges.append(
                                {
                                    "source": feat_id,
                                    "target": epic_id,
                                    "type": "BELONGS_TO_EPIC",
                                    "properties": {},
                                }
                            )
                except Exception:
                    pass

            if any(p in path.parts for p in ["reference", "docs_cache", "crawler"]):
                try:
                    text_sources.append(path.read_text(encoding="utf-8"))
                except Exception:
                    pass

            if "src" in path.parts:
                file_rel_path = str(path.relative_to(project_path))
                file_node_id = path.name
                physical_nodes.append(
                    {
                        "id": file_node_id,
                        "category": "Code File",
                        "properties": {
                            "description": f"Fichier source : {file_rel_path}",
                            "path": file_rel_path,
                        },
                    }
                )

                try:
                    content = path.read_text(encoding="utf-8")
                    self.extractor.extract_stories(
                        content, file_node_id, physical_edges
                    )

                    if path.suffix == ".py":
                        self.extractor.parse_python_ast(
                            content,
                            file_node_id,
                            physical_nodes,
                            physical_edges,
                            self.builder.tech_lexicon,
                            source_paths,
                            path,
                        )
                    elif path.suffix in (".ts", ".tsx", ".js"):
                        self.extractor.parse_typescript_ast(
                            content,
                            file_node_id,
                            physical_nodes,
                            physical_edges,
                            self.builder.tech_lexicon,
                            source_paths,
                            path,
                        )
                    elif path.suffix == ".cs":
                        self.extractor.parse_csharp_ast(
                            content,
                            file_node_id,
                            physical_nodes,
                            physical_edges,
                            self.builder.tech_lexicon,
                            source_paths,
                            path,
                        )
                except Exception:
                    pass

        self.builder.add_text_nodes(text_sources)

        # Ingestion des données de session (loop-mem)
        try:
            from src.loop_mem.db import get_session_timeline

            observations = get_session_timeline(state.project_name)
            for obs in observations:
                obs_node_id = f"LoopMem::Observation::{obs['id']}"
                physical_nodes.append(
                    {
                        "id": obs_node_id,
                        "category": "Observation",
                        "properties": {
                            "type": obs["type"],
                            "content": obs["content"],
                            "timestamp": obs["timestamp"],
                            "session_id": obs["session_id"],
                            "file_scope": obs["file_scope"] or "",
                        },
                    }
                )
                if obs["file_scope"]:
                    files = [
                        f.strip()
                        for f in obs["file_scope"].replace(",", " ").split()
                        if f.strip()
                    ]
                    for file_path_str in files:
                        physical_edges.append(
                            {
                                "source": Path(file_path_str).name,
                                "target": obs_node_id,
                                "type": "impacted_by",
                                "properties": {},
                            }
                        )
        except Exception:
            pass

        # ContextJournal
        if journal_path.exists():
            try:
                journal_text = journal_path.read_text(encoding="utf-8")
                self.builder.g.add_node(
                    "ContextJournal",
                    category="Governance",
                    description="Mémoire vive",
                    text_chunk=journal_text[:800],
                )
                self.builder.g.add_edge(
                    "ContextJournal", "State Machine", type="informs"
                )
                for node_id in list(self.builder.g.nodes):
                    if (
                        node_id != "ContextJournal"
                        and len(node_id) > 3
                        and node_id.lower() in journal_text.lower()
                    ):
                        self.builder.g.add_edge(
                            "ContextJournal", node_id, type="references"
                        )
            except Exception:
                pass

        # --- 4. Sérialisation ---
        nodes_list, edges_list = self.builder.merge_and_serialize(
            physical_nodes, physical_edges, graph_file
        )
        state.knowledge_graph = KnowledgeGraph(nodes=nodes_list, edges=edges_list)

        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(file_hashes, f, indent=2, ensure_ascii=False)

        # L'indexation SQLite FTS5 (graph_index.db) a été retirée au profit du moteur de recherche L3 In-Memory.
        pass

        ZeroFluffConsole.success(
            f"Graphe semantique construit : [highlight]{len(nodes_list)} noeuds[/highlight], [highlight]{len(edges_list)} relations[/highlight]."
        )

        from src.state import JournalEntry

        nodes_diff = len(nodes_list) - old_nodes_count
        edges_diff = len(edges_list) - old_edges_count

        diff_str = f"[{'+' if nodes_diff >= 0 else ''}{nodes_diff} nœuds, {'+' if edges_diff >= 0 else ''}{edges_diff} relations]"
        base_msg = (
            " | ".join(changed_details)
            if changed_details
            else "Recalcul complet du graphe."
        )
        details_msg = f"{base_msg}\nÉvolution du graphe : {len(nodes_list)} nœuds et {len(edges_list)} relations {diff_str}."

        entry = JournalEntry(
            event="Auto-Sync [Graphify]",
            details=details_msg,
            impacted_nodes=["Graphify Database"],
        )
        state.journal.append(entry)

        return state
