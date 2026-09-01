import hashlib
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
import tree_sitter_python
import tree_sitter_typescript
import tree_sitter_c_sharp
from tree_sitter import Language, Parser
from src.cli import ZeroFluffConsole

class Extractor:
    """Gère l'extraction AST et la détection sémantique (Stories)."""
    
    def __init__(self):
        self.py_parser = self._init_parser(tree_sitter_python.language())
        self.ts_parser = self._init_parser(tree_sitter_typescript.language_typescript())
        self.tsx_parser = self._init_parser(tree_sitter_typescript.language_tsx())
        self.cs_parser = self._init_parser(tree_sitter_c_sharp.language())

    def _init_parser(self, lang):
        try:
            language = Language(lang)
            return Parser(language)
        except Exception as e:
            ZeroFluffConsole.warning(f"Erreur init parser Tree-Sitter : {e}")
            return None

    def calculate_sha256(self, file_path: Path) -> str:
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception:
            return ""

    def extract_stories(self, content: str, file_node_id: str, physical_edges: list):
        """Extrait les marqueurs de stories [US-XXX] ou [RPM9-XXX]."""
        story_matches = re.findall(r'\[(US-\d+|RPM9-\d+)\]', content)
        for story_id in story_matches:
            physical_edges.append({
                "source": story_id,
                "target": file_node_id,
                "type": "implements",
                "properties": {}
            })

    def parse_python_ast(self, content: str, file_node_id: str, nodes: list, edges: list, tech_lexicon: dict, source_paths: list, path: Path):
        if not self.py_parser: return
        try:
            tree = self.py_parser.parse(bytes(content, "utf8"))
            root = tree.root_node
            
            def walk(node):
                if node.type == "import_statement":
                    imp_text = content[node.start_byte:node.end_byte].strip().lower()
                    for tech_key in tech_lexicon:
                        if tech_key in imp_text:
                            edges.append({"source": file_node_id, "target": tech_lexicon[tech_key][2], "type": "uses", "properties": {"context": "import"}})
                    for other_path in source_paths:
                        if other_path != path:
                            other_name = other_path.stem.lower()
                            if f" {other_name}" in imp_text or f",{other_name}" in imp_text:
                                edges.append({"source": file_node_id, "target": other_path.name, "type": "imports", "properties": {}})

                elif node.type == "import_from_statement":
                    imp_text = content[node.start_byte:node.end_byte].strip().lower()
                    for tech_key in tech_lexicon:
                        if tech_key in imp_text:
                            edges.append({"source": file_node_id, "target": tech_lexicon[tech_key][2], "type": "uses", "properties": {"context": "import_from"}})
                    for other_path in source_paths:
                        if other_path != path:
                            other_name = other_path.stem.lower()
                            if f"from {other_name}" in imp_text or f"from .{other_name}" in imp_text or f"from ..{other_name}" in imp_text:
                                edges.append({"source": file_node_id, "target": other_path.name, "type": "imports", "properties": {}})

                elif node.type == "class_definition":
                    name_node = node.child_by_field_name("name")
                    if name_node:
                        class_name = content[name_node.start_byte:name_node.end_byte].strip()
                        class_id = f"{file_node_id}::{class_name}"
                        nodes.append({"id": class_id, "category": "Class", "properties": {"description": f"Classe {class_name} definie dans {file_node_id}", "name": class_name}})
                        edges.append({"source": file_node_id, "target": class_id, "type": "defines", "properties": {}})

                elif node.type == "function_definition":
                    name_node = node.child_by_field_name("name")
                    if name_node:
                        func_name = content[name_node.start_byte:name_node.end_byte].strip()
                        func_id = f"{file_node_id}::{func_name}"
                        nodes.append({"id": func_id, "category": "Function", "properties": {"description": f"Fonction {func_name} definie dans {file_node_id}", "name": func_name}})
                        edges.append({"source": file_node_id, "target": func_id, "type": "defines", "properties": {}})
                        
                for child in node.children:
                    walk(child)
            walk(root)
        except Exception:
            pass

    def parse_typescript_ast(self, content: str, file_node_id: str, nodes: list, edges: list, tech_lexicon: dict, source_paths: list, path: Path):
        parser = self.tsx_parser if path.suffix == ".tsx" else self.ts_parser
        if not parser: return
        try:
            tree = parser.parse(bytes(content, "utf8"))
            root = tree.root_node
            
            def walk(node):
                if node.type == "import_statement":
                    imp_text = content[node.start_byte:node.end_byte].strip().lower()
                    for tech_key in tech_lexicon:
                        if tech_key in imp_text:
                            edges.append({"source": file_node_id, "target": tech_lexicon[tech_key][2], "type": "uses", "properties": {"context": "import"}})
                    for other_path in source_paths:
                        if other_path != path:
                            other_name = other_path.stem.lower()
                            if f"'{other_name}'" in imp_text or f'"{other_name}"' in imp_text or f"/{other_name}" in imp_text:
                                edges.append({"source": file_node_id, "target": other_path.name, "type": "imports", "properties": {}})

                elif node.type in ("class_declaration", "class"):
                    name_node = node.child_by_field_name("name")
                    if name_node:
                        class_name = content[name_node.start_byte:name_node.end_byte].strip()
                        class_id = f"{file_node_id}::{class_name}"
                        nodes.append({"id": class_id, "category": "Class", "properties": {"description": f"Classe {class_name} definie dans {file_node_id}", "name": class_name}})
                        edges.append({"source": file_node_id, "target": class_id, "type": "defines", "properties": {}})

                elif node.type in ("function_declaration", "function"):
                    name_node = node.child_by_field_name("name")
                    if name_node:
                        func_name = content[name_node.start_byte:name_node.end_byte].strip()
                        func_id = f"{file_node_id}::{func_name}"
                        nodes.append({"id": func_id, "category": "Function", "properties": {"description": f"Fonction {func_name} definie dans {file_node_id}", "name": func_name}})
                        edges.append({"source": file_node_id, "target": func_id, "type": "defines", "properties": {}})
                        
                for child in node.children:
                    walk(child)
            walk(root)
        except Exception:
            pass

    def parse_csharp_ast(self, content: str, file_node_id: str, nodes: list, edges: list, tech_lexicon: dict, source_paths: list, path: Path):
        """Extraction AST C# via Tree-Sitter (remplace les Regex)."""
        if not self.cs_parser: return
        try:
            tree = self.cs_parser.parse(bytes(content, "utf8"))
            root = tree.root_node
            
            def walk(node):
                if node.type == "using_directive":
                    imp_text = content[node.start_byte:node.end_byte].strip().lower()
                    for tech_key in tech_lexicon:
                        if tech_key in imp_text:
                            edges.append({"source": file_node_id, "target": tech_lexicon[tech_key][2], "type": "uses", "properties": {"context": "using"}})
                
                elif node.type in ("class_declaration", "interface_declaration", "record_declaration"):
                    name_node = node.child_by_field_name("name")
                    if name_node:
                        class_name = content[name_node.start_byte:name_node.end_byte].strip()
                        class_id = f"{file_node_id}::{class_name}"
                        cat = "Interface" if node.type == "interface_declaration" else "Class"
                        nodes.append({"id": class_id, "category": cat, "properties": {"description": f"{cat} {class_name} definie dans {file_node_id}", "name": class_name}})
                        edges.append({"source": file_node_id, "target": class_id, "type": "defines", "properties": {}})
                
                elif node.type == "method_declaration":
                    name_node = node.child_by_field_name("name")
                    if name_node:
                        func_name = content[name_node.start_byte:name_node.end_byte].strip()
                        func_id = f"{file_node_id}::{func_name}"
                        nodes.append({"id": func_id, "category": "Method", "properties": {"description": f"Methode {func_name} definie dans {file_node_id}", "name": func_name}})
                        edges.append({"source": file_node_id, "target": func_id, "type": "defines", "properties": {}})

                for child in node.children:
                    walk(child)
            walk(root)
        except Exception:
            pass
