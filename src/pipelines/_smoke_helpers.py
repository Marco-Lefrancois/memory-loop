"""
_smoke_helpers.py — Helpers du check de fumée imports (MLOOP-172-BE).

Fonctions utilitaires pour import_smoke_check.py :
  - path_to_module_name    : chemin fichier → nom module Python
  - can_import_module      : tente l'import d'un module
  - find_callers           : grep AST des fichiers importants un module
  - extract_imported_symbols : AST extract des symboles importés
  - check_symbols_resolved : vérifie la disponibilité des symboles

Conforme ADR-0369 : timeout= explicite, with sur ressources, zéro except pass nu.
Conforme ADR-0202 : <300 L / 15 Ko.
"""

from __future__ import annotations

import ast
import importlib
import importlib.util
import subprocess
import sys
from pathlib import Path

from src.utils.logger import get_logger

logger = get_logger("pipelines._smoke_helpers")

# ── Constantes ────────────────────────────────────────────────────────────────

_GREP_TIMEOUT = 15  # secondes


# ── Résolution de module Python depuis un chemin fichier ──────────────────────


def path_to_module_name(path: Path, src_root: Path = Path(".")) -> str:
    """Convertit un chemin fichier en nom de module Python pointé (ex: src.pipelines.vibe_check)."""
    try:
        rel = path.resolve().relative_to(src_root.resolve())
    except ValueError:
        rel = path
    parts = list(rel.with_suffix("").parts)
    return ".".join(parts)


# ── Import direct d'un module ─────────────────────────────────────────────────


def can_import_module(module_name: str) -> tuple[bool, str]:
    """
    Tente d'importer le module Python donné.

    Returns:
        (success, error_message) — success=True si l'import réussit sans exception.
    """
    try:
        spec = importlib.util.find_spec(module_name)
        if spec is None:
            return False, f"Module introuvable : {module_name!r}"
        mod = importlib.import_module(module_name)
        _ = mod
        return True, ""
    except Exception as exc:  # noqa: BLE001
        logger.debug(
            "Import échoué pour %r.",
            module_name,
            exc_info=True,
            extra={"module_name": module_name, "error": str(exc)},
        )
        return False, str(exc)


# ── Découverte des callers via grep AST ──────────────────────────────────────


def find_callers(module_name: str, src_dir: Path = Path("src")) -> list[str]:
    """
    Recherche les fichiers Python qui importent le module donné.

    Utilise rg (ripgrep) si disponible, sinon grep natif.
    Retourne une liste de chemins relatifs de fichiers callers.
    """
    patterns = [
        f"import {module_name}",
        f"from {module_name} import",
        f"from {module_name}.",
    ]
    callers: set[str] = set()

    for pattern in patterns:
        try:
            result = subprocess.run(
                ["rg", "--files-with-matches", "--glob", "*.py", "-e", pattern, str(src_dir)],
                capture_output=True,
                text=True,
                timeout=_GREP_TIMEOUT,
            )
            if result.returncode == 0:
                for line in result.stdout.splitlines():
                    callers.add(line.strip())
        except FileNotFoundError:
            try:
                result = subprocess.run(
                    ["grep", "-rl", "--include=*.py", pattern, str(src_dir)],
                    capture_output=True,
                    text=True,
                    timeout=_GREP_TIMEOUT,
                )
                if result.returncode == 0:
                    for line in result.stdout.splitlines():
                        callers.add(line.strip())
            except Exception as exc:
                logger.debug(
                    "grep indisponible pour pattern %r.",
                    pattern,
                    exc_info=True,
                    extra={"pattern": pattern, "error": str(exc)},
                )
        except subprocess.TimeoutExpired:
            logger.warning(
                "Timeout grep pour pattern %r — ignoré.",
                pattern,
                extra={"grep_pattern": pattern, "timeout_s": _GREP_TIMEOUT},
            )

    return sorted(callers)


# ── Extraction des symboles importés depuis un caller ────────────────────────


def extract_imported_symbols(caller_path: Path, module_name: str) -> list[str]:
    """
    Parse le fichier caller et extrait les symboles importés depuis module_name.

    Retourne une liste de noms de symboles.
    """
    try:
        with open(caller_path, encoding="utf-8", errors="replace") as f:
            source = f.read()
    except Exception as exc:
        logger.debug(
            "Lecture impossible de %s.",
            caller_path,
            exc_info=True,
            extra={"caller": str(caller_path), "error": str(exc)},
        )
        return []

    symbols: list[str] = []
    try:
        tree = ast.parse(source, filename=str(caller_path))
    except SyntaxError as exc:
        logger.debug(
            "SyntaxError lors du parsing de %s.",
            caller_path,
            exc_info=True,
            extra={"caller": str(caller_path), "error": str(exc)},
        )
        return []

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module and (
                node.module == module_name or node.module.startswith(module_name + ".")
            ):
                for alias in node.names:
                    if alias.name != "*":
                        symbols.append(alias.name)

    return symbols


# ── Vérification des symboles dans le module importé ─────────────────────────


def check_symbols_resolved(module_name: str, symbols: list[str]) -> list[tuple[str, str]]:
    """
    Vérifie que chaque symbole est accessible dans le module.

    Returns:
        Liste de (symbole, raison_échec) pour les symboles non résolus.
    """
    unresolved: list[tuple[str, str]] = []
    ok, err = can_import_module(module_name)
    if not ok:
        for sym in symbols:
            unresolved.append((sym, f"Module {module_name!r} non importable : {err}"))
        return unresolved

    mod = sys.modules.get(module_name)
    if mod is None:
        try:
            mod = importlib.import_module(module_name)
        except Exception as exc:
            for sym in symbols:
                unresolved.append((sym, str(exc)))
            return unresolved

    for sym in symbols:
        if not hasattr(mod, sym):
            unresolved.append((sym, f"Attribut {sym!r} absent de {module_name!r}"))

    return unresolved
