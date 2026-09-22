"""Génération de la toile d'architecture 2D stratifiée (MLOOP-145-BE — extraction ADR-0202)."""

from __future__ import annotations

import json
from pathlib import Path


class ArchitectureCanvasMixin:
    """Toile architecture JSON Canvas (ADR-0349) — dépend de self.project_path."""

    project_path: Path

    def generate_architecture_canvas(self) -> Path:
        """
        Génère une toile d'architecture 2D stratifiée par couches selon la spécification JSON Canvas (ADR-0349).
        Organise l'architecture en 5 strates colorées avec flux de données descendants.
        """
        from src.cli import ZeroFluffConsole

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
            nodes.append(
                {
                    "id": node_id,
                    "type": "text",
                    "text": f"### {lm['title']}\n\n{lm['desc']}",
                    "x": start_x,
                    "y": lm["y"],
                    "width": node_width,
                    "height": node_height,
                    "color": lm["color"],
                }
            )

            if i > 0:
                prev_id = layers_meta[i - 1]["id"]
                edges.append(
                    {
                        "id": f"edge-arch-{i}",
                        "fromNode": prev_id,
                        "fromSide": "bottom",
                        "toNode": node_id,
                        "toSide": "top",
                        "label": "Flux descendant",
                    }
                )

        canvas_data = {"nodes": nodes, "edges": edges}

        target_file.write_text(
            json.dumps(canvas_data, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        ZeroFluffConsole.success(f"Toile d'Architecture Codebase 2D générée sous : {target_file}")
        return target_file
