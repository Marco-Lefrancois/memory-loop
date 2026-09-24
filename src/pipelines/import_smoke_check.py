"""
import_smoke_check.py — Check de fumée imports post-extraction modulaire (MLOOP-172-BE).

Usage:
    python -m src.pipelines.import_smoke_check --module src/pipelines/vibe_check.py
    python -m src.pipelines.import_smoke_check --module src/engine/rubber_duck/critic/__init__.py

Comportement :
    Pour un module extrait <X>, résoudre les imports des callers connus (grep AST)
    et signaler tout symbole non résolu avec le fichier caller exact.
    Léger : pas de comparaison exhaustive de surface AST.

Helpers : src/pipelines/_smoke_helpers.py
Conforme ADR-0369 : timeout= explicite, with sur ressources, zéro except pass nu.
Conforme ADR-0202 : <300 L / 15 Ko.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from src.pipelines._smoke_helpers import (
    can_import_module,
    check_symbols_resolved,
    extract_imported_symbols,
    find_callers,
    path_to_module_name,
)
from src.utils.logger import get_logger

logger = get_logger("pipelines.import_smoke_check")

# ── Constantes ────────────────────────────────────────────────────────────────

_EXIT_OK = 0
_EXIT_FAIL = 1


# ── Point d'entrée principal ──────────────────────────────────────────────────


def run_smoke_check(module_path: str, src_dir: str = "src") -> int:
    """
    Exécute le check de fumée complet pour un module extrait.

    Args:
        module_path: chemin vers le fichier .py du module (ex: src/pipelines/vibe_check.py)
        src_dir: répertoire racine des sources Python

    Returns:
        0 (OK) ou 1 (FAIL)
    """
    t0 = time.perf_counter()
    path = Path(module_path)

    if not path.exists():
        print(f"❌ Fichier introuvable : {module_path}", file=sys.stderr)
        return _EXIT_FAIL

    module_name = path_to_module_name(path, src_root=Path("."))
    print(f"\n🔍 Check de fumée imports — module : {module_name}")
    print(f"   Fichier : {path}")

    # 1. Import direct du module
    print("\n[1/3] Import direct du module…")
    ok, err = can_import_module(module_name)
    if not ok:
        print(f"   ❌ FAIL — Module non importable : {err}")
        logger.error(
            "Import direct échoué pour %r.",
            module_name,
            extra={"module_name": module_name, "error": err},
        )
        return _EXIT_FAIL
    print(f"   ✅ Module importable : {module_name}")

    # 2. Découverte des callers
    print("\n[2/3] Découverte des callers (grep AST)…")
    callers = find_callers(module_name, src_dir=Path(src_dir))
    print(f"   {len(callers)} caller(s) détecté(s).")

    # 3. Vérification des symboles importés par les callers
    print("\n[3/3] Vérification des symboles par caller…")
    all_unresolved: list[tuple[str, str, str]] = []  # (caller, symbole, raison)

    for caller_str in callers:
        caller_path = Path(caller_str)
        symbols = extract_imported_symbols(caller_path, module_name)
        if not symbols:
            continue
        unresolved = check_symbols_resolved(module_name, symbols)
        for sym, reason in unresolved:
            all_unresolved.append((caller_str, sym, reason))

    duration_ms = round((time.perf_counter() - t0) * 1000, 1)

    if all_unresolved:
        print(f"\n❌ {len(all_unresolved)} symbole(s) non résolu(s) :")
        for caller_str, sym, reason in all_unresolved:
            print(f"   • {caller_str} → {sym!r} : {reason}")
        logger.error(
            "Check fumée FAIL : %d symbole(s) non résolu(s) pour %r.",
            len(all_unresolved),
            module_name,
            extra={"module_name": module_name, "unresolved_count": len(all_unresolved)},
        )
        print(f"\n⏱️  Durée : {duration_ms} ms")
        return _EXIT_FAIL

    print(f"\n✅ Aucun symbole non résolu détecté. ({len(callers)} caller(s) vérifiés)")
    logger.info(
        "Check fumée PASS pour %r : %d caller(s) vérifiés.",
        module_name,
        len(callers),
        extra={"module_name": module_name, "callers_count": len(callers)},
    )
    print(f"⏱️  Durée : {duration_ms} ms")
    return _EXIT_OK


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Check de fumée imports post-extraction modulaire (MLOOP-172-BE)."
    )
    parser.add_argument(
        "--module",
        required=True,
        help="Chemin vers le fichier .py du module extrait (ex: src/pipelines/vibe_check.py)",
    )
    parser.add_argument(
        "--src-dir",
        default="src",
        help="Répertoire racine des sources Python (défaut: src)",
    )
    args = parser.parse_args()
    sys.exit(run_smoke_check(args.module, args.src_dir))


if __name__ == "__main__":
    main()
