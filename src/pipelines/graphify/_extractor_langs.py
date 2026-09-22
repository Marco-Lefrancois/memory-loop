"""Parsers AST TypeScript/TSX et C# (MLOOP-145-BE — extraction ADR-0202 depuis extractor).

Mixin consommé par Extractor — accède à self.ts_parser / self.tsx_parser / self.cs_parser.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


class LangParsersMixin:
    """Parsers Tree-Sitter multi-langages (TypeScript, TSX, C#)."""

    ts_parser: Any
    tsx_parser: Any
    cs_parser: Any

    def parse_typescript_ast(
        self,
        content: str,
        file_node_id: str,
        nodes: list,
        edges: list,
        tech_lexicon: dict,
        source_paths: list,
        path: Path,
    ):
        from src.utils.logger import get_logger

        logger = get_logger("pipelines.graphify.extractor")
        parser = self.tsx_parser if path.suffix == ".tsx" else self.ts_parser
        if not parser:
            return
        try:
            tree = parser.parse(bytes(content, "utf8"))
            root = tree.root_node

            def walk(node):
                if node.type == "import_statement":
                    imp_text = content[node.start_byte : node.end_byte].strip().lower()
                    for tech_key in tech_lexicon:
                        if tech_key in imp_text:
                            edges.append(
                                {
                                    "source": file_node_id,
                                    "target": tech_lexicon[tech_key][2],
                                    "type": "uses",
                                    "properties": {"context": "import"},
                                }
                            )
                    for other_path in source_paths:
                        if other_path != path:
                            other_name = other_path.stem.lower()
                            if (
                                f"'{other_name}'" in imp_text
                                or f'"{other_name}"' in imp_text
                                or f"/{other_name}" in imp_text
                            ):
                                edges.append(
                                    {
                                        "source": file_node_id,
                                        "target": other_path.name,
                                        "type": "imports",
                                        "properties": {},
                                    }
                                )

                elif node.type in ("class_declaration", "class"):
                    name_node = node.child_by_field_name("name")
                    if name_node:
                        class_name = content[name_node.start_byte : name_node.end_byte].strip()
                        class_id = f"{file_node_id}::{class_name}"
                        nodes.append(
                            {
                                "id": class_id,
                                "category": "Class",
                                "properties": {
                                    "description": f"Classe {class_name} definie dans {file_node_id}",
                                    "name": class_name,
                                },
                            }
                        )
                        edges.append(
                            {
                                "source": file_node_id,
                                "target": class_id,
                                "type": "defines",
                                "properties": {},
                            }
                        )

                elif node.type in ("function_declaration", "function"):
                    name_node = node.child_by_field_name("name")
                    if name_node:
                        func_name = content[name_node.start_byte : name_node.end_byte].strip()
                        func_id = f"{file_node_id}::{func_name}"
                        nodes.append(
                            {
                                "id": func_id,
                                "category": "Function",
                                "properties": {
                                    "description": f"Fonction {func_name} definie dans {file_node_id}",
                                    "name": func_name,
                                },
                            }
                        )
                        edges.append(
                            {
                                "source": file_node_id,
                                "target": func_id,
                                "type": "defines",
                                "properties": {},
                            }
                        )

                for child in node.children:
                    walk(child)

            walk(root)
        except Exception as e:
            logger.warning(
                "Parsing AST TypeScript/TSX échoué (fichier non indexé dans le graphe)",
                exc_info=True,
                extra={
                    "component": "pipelines.graphify.extractor",
                    "operation": "parse_typescript_ast",
                    "file_node_id": file_node_id,
                    "path": str(path),
                    "error": str(e),
                },
            )

    def parse_csharp_ast(
        self,
        content: str,
        file_node_id: str,
        nodes: list,
        edges: list,
        tech_lexicon: dict,
        source_paths: list,
        path: Path,
    ):
        """Extraction AST C# via Tree-Sitter (remplace les Regex)."""
        from src.utils.logger import get_logger

        logger = get_logger("pipelines.graphify.extractor")
        if not self.cs_parser:
            return
        try:
            tree = self.cs_parser.parse(bytes(content, "utf8"))
            root = tree.root_node

            def walk(node):
                if node.type == "using_directive":
                    imp_text = content[node.start_byte : node.end_byte].strip().lower()
                    for tech_key in tech_lexicon:
                        if tech_key in imp_text:
                            edges.append(
                                {
                                    "source": file_node_id,
                                    "target": tech_lexicon[tech_key][2],
                                    "type": "uses",
                                    "properties": {"context": "using"},
                                }
                            )

                elif node.type in (
                    "class_declaration",
                    "interface_declaration",
                    "record_declaration",
                ):
                    name_node = node.child_by_field_name("name")
                    if name_node:
                        class_name = content[name_node.start_byte : name_node.end_byte].strip()
                        class_id = f"{file_node_id}::{class_name}"
                        cat = "Interface" if node.type == "interface_declaration" else "Class"
                        nodes.append(
                            {
                                "id": class_id,
                                "category": cat,
                                "properties": {
                                    "description": f"{cat} {class_name} definie dans {file_node_id}",
                                    "name": class_name,
                                },
                            }
                        )
                        edges.append(
                            {
                                "source": file_node_id,
                                "target": class_id,
                                "type": "defines",
                                "properties": {},
                            }
                        )

                elif node.type == "method_declaration":
                    name_node = node.child_by_field_name("name")
                    if name_node:
                        func_name = content[name_node.start_byte : name_node.end_byte].strip()
                        func_id = f"{file_node_id}::{func_name}"
                        nodes.append(
                            {
                                "id": func_id,
                                "category": "Method",
                                "properties": {
                                    "description": f"Methode {func_name} definie dans {file_node_id}",
                                    "name": func_name,
                                },
                            }
                        )
                        edges.append(
                            {
                                "source": file_node_id,
                                "target": func_id,
                                "type": "defines",
                                "properties": {},
                            }
                        )

                for child in node.children:
                    walk(child)

            walk(root)
        except Exception as e:
            logger.warning(
                "Parsing AST C# échoué (fichier non indexé dans le graphe)",
                exc_info=True,
                extra={
                    "component": "pipelines.graphify.extractor",
                    "operation": "parse_csharp_ast",
                    "file_node_id": file_node_id,
                    "path": str(path),
                    "error": str(e),
                },
            )
