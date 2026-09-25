"""
Module d'analyse statique AST et de traçabilité du code (Code Evidence Tracer).
Conforme aux standards ADR-0394, ADR-0369 (Senior Python, zéro dépendance externe) et ADR-0376.

Permet d'extraire les symboles qualifiés de code physique (chemin/fichier.py::NomClasse.methode)
et de les confronter de manière déterministe à la matrice de traçabilité EvidencePack 2.0.
"""

from __future__ import annotations

import ast
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Optional, Union

from src.pipelines.evidence_pack import CodeTraceabilityEntry


@dataclass
class ExtractedSymbol:
    """Représente un symbole de code physique extrait par analyse statique AST."""
    symbol_path: str
    name: str
    symbol_type: str  # class, method, async_method, function, async_function
    line_start: int
    line_end: int
    is_private: bool
    parent_symbol: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """Convertit le symbole en dictionnaire sérialisable."""
        return asdict(self)


@dataclass
class ReconciliationReport:
    """Rapport d'audit de réconciliation entre le code physique et la matrice de traçabilité."""
    is_valid: bool
    unanchored_symbols: list[ExtractedSymbol] = field(default_factory=list)
    dangling_entries: list[CodeTraceabilityEntry] = field(default_factory=list)
    matched_pairs: list[dict[str, Any]] = field(default_factory=list)
    summary: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convertit le rapport en dictionnaire sérialisable."""
        return {
            "is_valid": self.is_valid,
            "unanchored_symbols": [s.to_dict() for s in self.unanchored_symbols],
            "dangling_entries": list(self.dangling_entries),
            "matched_pairs": list(self.matched_pairs),
            "summary": dict(self.summary),
        }


class BaseAstExtractor(ABC):
    """Classe de base abstraite pour l'extraction de symboles AST selon le langage."""

    @abstractmethod
    def extract_symbols(self, source_code: str, relative_path: str) -> list[ExtractedSymbol]:
        """Extrait la liste des symboles qualifiés depuis une chaîne de code source."""
        pass


class PythonAstExtractor(BaseAstExtractor):
    """
    Extracteur AST déterministe pour le langage Python.
    Utilise exclusivement le module standard ast (zéro dépendance externe).
    """

    @staticmethod
    def _is_private_name(name: str) -> bool:
        """Détecte si un nom est privé conventionnel (commence par _ sans être un dunder)."""
        return name.startswith("_") and not (name.startswith("__") and name.endswith("__"))

    def extract_symbols(self, source_code: str, relative_path: str) -> list[ExtractedSymbol]:
        """
        Analyse récursivement l'arbre syntaxique abstrait d'un fichier source Python.
        Lève SyntaxError si le code est invalide.
        """
        # Normalisation du chemin avec slashs obliques
        norm_path = relative_path.replace("\\", "/").strip("/")

        try:
            tree = ast.parse(source_code, filename=norm_path)
        except SyntaxError as exc:
            raise SyntaxError(
                f"[CodeEvidenceTracer] Erreur de syntaxe lors du parsing AST de '{norm_path}': {exc}"
            ) from exc

        symbols: list[ExtractedSymbol] = []

        def _scan_nested_functions(node: ast.AST, parent_qual_name: str) -> None:
            """Scanne récursivement les sous-fonctions internes imbriquées."""
            for child in ast.iter_child_nodes(node):
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    nested_type = "async_function" if isinstance(child, ast.AsyncFunctionDef) else "function"
                    nested_path = f"{parent_qual_name}.{child.name}"
                    symbols.append(
                        ExtractedSymbol(
                            symbol_path=nested_path,
                            name=child.name,
                            symbol_type=nested_type,
                            line_start=child.lineno,
                            line_end=getattr(child, "end_lineno", child.lineno),
                            is_private=self._is_private_name(child.name),
                            parent_symbol=parent_qual_name,
                        )
                    )
                    # Récursion pour des fonctions encore plus imbriquées
                    _scan_nested_functions(child, nested_path)

        for top_node in tree.body:
            if isinstance(top_node, ast.ClassDef):
                class_qual = f"{norm_path}::{top_node.name}"
                symbols.append(
                    ExtractedSymbol(
                        symbol_path=class_qual,
                        name=top_node.name,
                        symbol_type="class",
                        line_start=top_node.lineno,
                        line_end=getattr(top_node, "end_lineno", top_node.lineno),
                        is_private=self._is_private_name(top_node.name),
                        parent_symbol=None,
                    )
                )

                for member in top_node.body:
                    if isinstance(member, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        method_type = "async_method" if isinstance(member, ast.AsyncFunctionDef) else "method"
                        method_qual = f"{norm_path}::{top_node.name}.{member.name}"
                        symbols.append(
                            ExtractedSymbol(
                                symbol_path=method_qual,
                                name=member.name,
                                symbol_type=method_type,
                                line_start=member.lineno,
                                line_end=getattr(member, "end_lineno", member.lineno),
                                is_private=self._is_private_name(member.name),
                                parent_symbol=class_qual,
                            )
                        )
                        # Sous-fonctions internes dans la méthode
                        _scan_nested_functions(member, method_qual)

            elif isinstance(top_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_type = "async_function" if isinstance(top_node, ast.AsyncFunctionDef) else "function"
                func_qual = f"{norm_path}::{top_node.name}"
                symbols.append(
                    ExtractedSymbol(
                        symbol_path=func_qual,
                        name=top_node.name,
                        symbol_type=func_type,
                        line_start=top_node.lineno,
                        line_end=getattr(top_node, "end_lineno", top_node.lineno),
                        is_private=self._is_private_name(top_node.name),
                        parent_symbol=None,
                    )
                )
                # Sous-fonctions internes dans la fonction de module
                _scan_nested_functions(top_node, func_qual)

        return symbols


class CodeEvidenceTracer:
    """
    Moteur de traçabilité déterministe Code ↔ Exigences (EvidencePack 2.0).
    Orchestre l'extraction des symboles AST et la détection du code fantôme (Ghost Code).
    """

    def __init__(self, extractor: Optional[BaseAstExtractor] = None):
        self._extractor = extractor or PythonAstExtractor()

    def extract_symbols_from_source(
        self, source_code: str, relative_path: str
    ) -> list[ExtractedSymbol]:
        """Extrait les symboles AST depuis une chaîne de code source."""
        return self._extractor.extract_symbols(source_code, relative_path)

    def extract_symbols_from_file(
        self, file_path: Union[str, Path], base_dir: Optional[Union[str, Path]] = None
    ) -> list[ExtractedSymbol]:
        """Extrait les symboles AST depuis un fichier physique sur disque."""
        path_obj = Path(file_path).resolve()
        base_obj = Path(base_dir).resolve() if base_dir else Path.cwd().resolve()

        try:
            rel_path = path_obj.relative_to(base_obj).as_posix()
        except ValueError:
            rel_path = path_obj.name

        source_code = path_obj.read_text(encoding="utf-8")
        return self.extract_symbols_from_source(source_code, rel_path)

    def reconcile(
        self,
        extracted: list[ExtractedSymbol],
        matrix: list[CodeTraceabilityEntry],
        allow_private_implicit: bool = True,
        allow_dunder_implicit: bool = True,
    ) -> ReconciliationReport:
        """
        Rapproche les symboles extraits du code source avec la matrice de traçabilité.
        Détecte le code fantôme non ancré et les entrées déclarées sans symbole physique.
        """
        matrix_by_symbol = {entry["ast_symbol"]: entry for entry in matrix}
        matched_pairs: list[dict[str, Any]] = []
        unanchored_symbols: list[ExtractedSymbol] = []

        # Identifier l'ensemble des fichiers examinés
        examined_files = {s.symbol_path.split("::")[0] for s in extracted}
        matched_symbol_paths = set()

        for sym in extracted:
            if sym.symbol_path in matrix_by_symbol:
                entry = matrix_by_symbol[sym.symbol_path]
                matched_pairs.append({
                    "symbol": sym.to_dict(),
                    "traceability_entry": entry,
                })
                matched_symbol_paths.add(sym.symbol_path)
            else:
                # Vérifier si c'est un helper privé implicitement toléré
                is_tolerated_private = (
                    allow_private_implicit
                    and sym.is_private
                    and sym.parent_symbol is not None
                    and sym.parent_symbol in matrix_by_symbol
                )

                # Vérifier si c'est une méthode dunder (ex: __init__) d'une classe déjà couverte
                is_dunder = sym.name.startswith("__") and sym.name.endswith("__")
                is_tolerated_dunder = (
                    allow_dunder_implicit
                    and is_dunder
                    and sym.parent_symbol is not None
                    and sym.parent_symbol in matrix_by_symbol
                )

                if not (is_tolerated_private or is_tolerated_dunder):
                    unanchored_symbols.append(sym)

        # Détection des entrées pendantes (dangling entries) pour les fichiers examinés
        dangling_entries: list[CodeTraceabilityEntry] = []
        extracted_paths = {s.symbol_path for s in extracted}

        for entry in matrix:
            entry_file = entry["ast_symbol"].split("::")[0]
            if entry_file in examined_files and entry["ast_symbol"] not in extracted_paths:
                dangling_entries.append(entry)

        is_valid = len(unanchored_symbols) == 0 and len(dangling_entries) == 0

        summary = {
            "total_extracted": len(extracted),
            "total_matrix": len(matrix),
            "matched": len(matched_pairs),
            "unanchored": len(unanchored_symbols),
            "dangling": len(dangling_entries),
        }

        return ReconciliationReport(
            is_valid=is_valid,
            unanchored_symbols=unanchored_symbols,
            dangling_entries=dangling_entries,
            matched_pairs=matched_pairs,
            summary=summary,
        )
