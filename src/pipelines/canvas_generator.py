# -*- coding: utf-8 -*-
"""
Générateur de toiles 2D interactives Obsidian Canvas (.canvas) pour mLoop (ADR-0337).
Exporte automatiquement le Story Mapping et le graphe DAG de sprint au format officiel JSON Canvas.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, Any, List, Optional

from src.cli import ZeroFluffConsole


class CanvasGenerator:
    """Moteur de génération et de synchronisation des toiles Obsidian Canvas."""

    STATUS_COLORS = {
        "READY_FOR_DEV": "4",       # 🟢 Vert
        "CLOSED": "4",              # 🟢 Vert
        "IN_ANALYZE": "3",          # 🟡 Jaune
        "READY_FOR_GROOMING": "2",  # 🟠 Orange
        "OPEN": "2",                # 🟠 Orange
        "BACKLOG": "5",             # 🔵 Bleu
        "ON-HOLD": "1",             # 🔴 Rouge
        "BLOCKED": "1"              # 🔴 Rouge
    }

    def __init__(self, project_path: Path | str):
        self.project_path = Path(project_path)
        self.backlog_dir = self.project_path / "backlog"
        self.stories_dir = self.backlog_dir / "stories"

    def scan_stories(self) -> List[Dict[str, Any]]:
        """Scanne les fichiers de récits verticaux et extrait les métadonnées pour le Canvas."""
        stories = []
        if not self.stories_dir.exists():
            return stories

        for story_file in sorted(self.stories_dir.rglob("*.md")):
            try:
                content = story_file.read_text(encoding="utf-8")
                story_id = story_file.stem
                title = story_id
                status = "OPEN"
                layer = "fullstack"
                epic = story_file.parent.name if story_file.parent != self.stories_dir else "Général"

                # Parse Frontmatter YAML
                fm_match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
                if fm_match:
                    fm_text = fm_match.group(1)
                    for line in fm_text.splitlines():
                        if ":" in line:
                            k, v = line.split(":", 1)
                            k, v = k.strip().lower(), v.strip()
                            if k == "id":
                                story_id = v
                            elif k == "title":
                                title = v
                            elif k == "status":
                                status = v.upper()
                            elif k == "layer":
                                layer = v.lower()
                            elif k in ("epic", "epic_key"):
                                epic = v

                # H1 Title fallback
                h1_m = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
                if h1_m and title == story_file.stem:
                    title = h1_m.group(1).strip()

                stories.append({
                    "id": story_id,
                    "file_stem": story_file.stem,
                    "title": title,
                    "status": status,
                    "layer": layer,
                    "epic": epic,
                    "file_path": str(story_file.relative_to(self.project_path)).replace("\\", "/")
                })
            except Exception:
                continue

        return stories

    def generate_story_mapping_canvas(self) -> Path:
        """Génère la toile 2D backlog/story_mapping.canvas regroupant les récits par épopée/couche."""
        stories = self.scan_stories()
        self.backlog_dir.mkdir(parents=True, exist_ok=True)
        target_file = self.backlog_dir / "story_mapping.canvas"

        # Grouper les stories par épopée
        epics: Dict[str, List[Dict[str, Any]]] = {}
        for s in stories:
            epics.setdefault(s.get("epic", "Général"), []).append(s)

        if not epics:
            epics["Backlog Général"] = [
                {"id": "DEMO-01", "file_stem": "DEMO-01", "title": "Exemple de Story", "status": "OPEN", "layer": "frontend"}
            ]

        nodes = []
        card_w, card_h = 320, 160
        margin_x, margin_y = 40, 30
        group_padding = 40

        curr_group_x = 0
        for epic_idx, (epic_name, epic_stories) in enumerate(epics.items()):
            group_id = f"group-epic-{epic_idx}"
            cols = 2 if len(epic_stories) > 3 else 1
            rows = (len(epic_stories) + cols - 1) // cols

            group_w = cols * card_w + (cols + 1) * margin_x
            group_h = rows * card_h + (rows + 1) * margin_y + 40

            nodes.append({
                "id": group_id,
                "type": "group",
                "label": f"📦 Épopée : {epic_name}",
                "x": curr_group_x,
                "y": 0,
                "width": group_w,
                "height": group_h,
                "color": "6"
            })

            for s_idx, s in enumerate(epic_stories):
                col = s_idx % cols
                row = s_idx // cols
                node_x = curr_group_x + margin_x + col * (card_w + margin_x)
                node_y = 60 + row * (card_h + margin_y)
                color = self.STATUS_COLORS.get(s.get("status", "OPEN"), "5")

                status_emoji = "🟢" if s.get("status") in ("READY_FOR_DEV", "CLOSED") else ("🟡" if s.get("status") == "IN_ANALYZE" else "⚪")
                file_stem = s.get("file_stem", s.get("id", "Story"))
                s_id = s.get("id", file_stem)
                s_title = s.get("title", s_id)
                s_layer = s.get("layer", "fullstack")
                s_status = s.get("status", "OPEN")

                card_text = (
                    f"### [[{file_stem}|{s_id}]] {status_emoji}\n"
                    f"**Titre** : {s_title[:45]}\n"
                    f"**Statut** : `{s_status}` · **Layer** : `{s_layer}`"
                )

                nodes.append({
                    "id": f"node-story-{s['id']}",
                    "type": "text",
                    "text": card_text,
                    "x": node_x,
                    "y": node_y,
                    "width": card_w,
                    "height": card_h,
                    "color": color
                })

            curr_group_x += group_w + group_padding

        canvas_data = {
            "nodes": nodes,
            "edges": []
        }

        target_file.write_text(json.dumps(canvas_data, indent=2, ensure_ascii=False), encoding="utf-8")
        ZeroFluffConsole.success(f"Toile Story Mapping générée sous : {target_file}")
        return target_file

    def generate_sprint_dag_canvas(self) -> Path:
        """Génère la toile d'ordonnancement séquentiel DAG backlog/sprint_dag.canvas."""
        stories = self.scan_stories()
        self.backlog_dir.mkdir(parents=True, exist_ok=True)
        target_file = self.backlog_dir / "sprint_dag.canvas"

        nodes = []
        edges = []
        card_w, card_h = 320, 160
        delta_x = 420
        delta_y = 220

        # Disposer les stories en chaîne ou grille ordonnée
        prev_node_id = None
        for idx, s in enumerate(stories):
            file_stem = s.get("file_stem", s.get("id", f"story-{idx}"))
            s_id = s.get("id", file_stem)
            node_id = f"node-dag-{s_id}"
            col = idx % 3
            row = idx // 3
            node_x = col * delta_x
            node_y = row * delta_y
            color = self.STATUS_COLORS.get(s.get("status", "OPEN"), "5")

            status_emoji = "🟢" if s.get("status") in ("READY_FOR_DEV", "CLOSED") else ("🟡" if s.get("status") == "IN_ANALYZE" else "⚪")
            s_title = s.get("title", s_id)
            s_status = s.get("status", "OPEN")
            s_layer = s.get("layer", "fullstack")

            card_text = (
                f"### [[{file_stem}|{s_id}]] {status_emoji}\n"
                f"**{s_title[:45]}**\n\n"
                f"Statut : `{s_status}`\n"
                f"Couche : `{s_layer}`"
            )

            nodes.append({
                "id": node_id,
                "type": "text",
                "text": card_text,
                "x": node_x,
                "y": node_y,
                "width": card_w,
                "height": card_h,
                "color": color
            })

            if prev_node_id:
                edges.append({
                    "id": f"edge-{idx}",
                    "fromNode": prev_node_id,
                    "fromSide": "right",
                    "toNode": node_id,
                    "toSide": "left",
                    "label": "Ordre"
                })
            prev_node_id = node_id

        canvas_data = {
            "nodes": nodes,
            "edges": edges
        }

        target_file.write_text(json.dumps(canvas_data, indent=2, ensure_ascii=False), encoding="utf-8")
        ZeroFluffConsole.success(f"Toile Sprint DAG générée sous : {target_file}")
        return target_file

    def generate_architecture_canvas(self) -> Path:
        """
        Génère une toile d'architecture 2D stratifiée par couches selon la spécification JSON Canvas (ADR-0349).
        Organise l'architecture en 5 strates colorées avec flux de données descendants.
        """
        arch_dir = self.project_path / "docs" / "01-architecture"
        if not arch_dir.exists():
            arch_dir = self.project_path / "docs"
        arch_dir.mkdir(parents=True, exist_ok=True)

        target_file = arch_dir / "architecture.canvas"

        layers_meta = [
            {
                "id": "layer_entry",
                "title": "🔴 Couche 1 : Points d'Entrée & Noyau",
                "desc": "CLI Dispatcher, Swarm Pipelines, Scripts d'amorçage\n(src/swarm.py, main.py)",
                "color": "1",  # Red
                "y": 0,
            },
            {
                "id": "layer_state",
                "title": "🟠 Couche 2 : Gestion d'État & Configuration",
                "desc": "LoopState, StateMachineEngine, Schémas Pydantic, Envsitter\n(src/state.py, src/pipelines/state_machine.py)",
                "color": "2",  # Orange
                "y": 240,
            },
            {
                "id": "layer_api",
                "title": "🔵 Couche 3 : Pipelines & Intégrations Externes",
                "desc": "Web Crawler, Research Pipeline, Ponts MCP, Jira Sync\n(src/pipelines/crawler.py, src/bridges/)",
                "color": "5",  # Cyan / Blue
                "y": 480,
            },
            {
                "id": "layer_data",
                "title": "🟡 Couche 4 : Données, Persistance & Mémoire",
                "desc": "SQLite FTS5 BM25, Graphify Hypergraph, EvidencePacks\n(src/memory/, graphify-out/, memory/)",
                "color": "3",  # Yellow
                "y": 720,
            },
            {
                "id": "layer_ui",
                "title": "🟢 Couche 5 : Interfaces & Restitution Visuelle",
                "desc": "Console ZeroFluff, Toiles Obsidian Canvas, Visualiseur HTML\n(src/cli.py, src/pipelines/canvas_generator.py)",
                "color": "4",  # Green
                "y": 960,
            },
        ]

        nodes = []
        edges = []
        node_width = 460
        node_height = 160
        start_x = 100

        for i, lm in enumerate(layers_meta):
            node_id = lm["id"]
            nodes.append({
                "id": node_id,
                "type": "text",
                "text": f"### {lm['title']}\n\n{lm['desc']}",
                "x": start_x,
                "y": lm["y"],
                "width": node_width,
                "height": node_height,
                "color": lm["color"]
            })

            if i > 0:
                prev_id = layers_meta[i - 1]["id"]
                edges.append({
                    "id": f"edge-arch-{i}",
                    "fromNode": prev_id,
                    "fromSide": "bottom",
                    "toNode": node_id,
                    "toSide": "top",
                    "label": "Flux descendant"
                })

        canvas_data = {
            "nodes": nodes,
            "edges": edges
        }

        target_file.write_text(json.dumps(canvas_data, indent=2, ensure_ascii=False), encoding="utf-8")
        ZeroFluffConsole.success(f"Toile d'Architecture Codebase 2D générée sous : {target_file}")
        return target_file

    def sync_all_canvases(self) -> Dict[str, Path]:
        """Génère et synchronise l'ensemble des toiles Canvas du projet."""
        f_mapping = self.generate_story_mapping_canvas()
        f_dag = self.generate_sprint_dag_canvas()
        f_arch = self.generate_architecture_canvas()
        return {
            "story_mapping": f_mapping,
            "sprint_dag": f_dag,
            "architecture": f_arch
        }
