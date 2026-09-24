# -*- coding: utf-8 -*-
"""
Failure Contracts ADR-0369 §5 — Découverte multi-niveaux de l'indexeur Fact-Search.

Couvre les 6 cas du PLAN-ADR-0390 §3 (Composant B) :
1. Arbre plat seul         -> régression stricte (foyer historique inchangé).
2. Arbre niché             -> découverte + doc_path préfixé docs/ (ADR-0390 §B).
3. Mixte plat + niché      -> sans doublon de chunks (anti-chevauchement).
4. Profondeur 3            -> NON découverte (limite assumée, ADR-0390 §A).
5. Contrat doc_path        -> tout chunk résout sous la racine projet (liens file:///).
6. Incrément/purge niché   -> fichier supprimé purgé au passage suivant.
"""

from pathlib import Path

import pytest

from src.engine.fact_search.indexer import FactSearchIndexer
from src.loop_mem.db import get_observation_db_session

PROJECT = "test_nested_proj"


def _index(docs_dir: Path, db_file: Path, project: str = PROJECT, force: bool = False) -> int:
    return FactSearchIndexer.index_project_docs(
        project_name=project,
        docs_dir=docs_dir,
        db_path=db_file,
        force=force,
    )


def _fetch_paths(db_file: Path, project: str = PROJECT) -> list[str]:
    with get_observation_db_session(db_path=db_file) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT DISTINCT doc_path FROM docs_chunks WHERE project_name=? ORDER BY doc_path",
            (project,),
        )
        return [r[0] for r in cursor.fetchall()]


def _fetch_chunk_rows(db_file: Path, project: str = PROJECT) -> list[tuple]:
    with get_observation_db_session(db_path=db_file) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT doc_path, line_start, line_end FROM docs_chunks WHERE project_name=?",
            (project,),
        )
        return cursor.fetchall()


# ─────────────────────────────────────────────────────────────────────────────
# 1. RÉGRESSION — arbre plat seul (foyer historique, comportement identique)
# ─────────────────────────────────────────────────────────────────────────────
def test_1_flat_tree_regression(tmp_path: Path):
    docs_dir = tmp_path / "docs"
    (docs_dir / "01-architecture").mkdir(parents=True)
    (docs_dir / "01-architecture" / "ADR-001.md").write_text(
        "# ADR-001 : Architecture Initiale\n\nContenu substantiel architecture.\n",
        encoding="utf-8",
    )
    (docs_dir / "00-ingested").mkdir(parents=True)
    (docs_dir / "00-ingested" / "CDC.md").write_text(
        "# Cahier des charges\n\nSpécification client.\n", encoding="utf-8"
    )

    db_file = tmp_path / "loop_mem.db"
    count = _index(docs_dir, db_file)

    assert count >= 2, "L'arbre plat doit être indexé (régession stricte)"
    paths = _fetch_paths(db_file)
    assert paths == [
        "docs/00-ingested/CDC.md",
        "docs/01-architecture/ADR-001.md",
    ], f"doc_path plat inchangés attendus, obtenu : {paths}"


# ─────────────────────────────────────────────────────────────────────────────
# 2. NOMINAL — arbre niché docs/<domaine>/<couche> découvert, préfixe docs/
# ─────────────────────────────────────────────────────────────────────────────
def test_2_nested_tree_discovered_with_docs_prefix(tmp_path: Path):
    docs_dir = tmp_path / "docs"
    nested = docs_dir / "OneTrust" / "00-ingested" / "03-scans"
    nested.mkdir(parents=True)
    (nested / "scan.md").write_text(
        "# Scan OneTrust\n\nRésultat d'analyse ApplicationInsights.\n", encoding="utf-8"
    )

    db_file = tmp_path / "loop_mem.db"
    count = _index(docs_dir, db_file)

    assert count >= 1, "Le fichier niché doit être découvert (ADR-0390 §A)"
    paths = _fetch_paths(db_file)
    assert paths == ["docs/OneTrust/00-ingested/03-scans/scan.md"], (
        f"doc_path niché attendu avec préfixe docs/, obtenu : {paths}"
    )

    # Contrat de résolution du handler CLI (fact_search.py L74-95) : le chemin
    # doit exister relativement à la racine projet (= parent de docs/).
    assert (tmp_path / paths[0]).exists(), "doc_path doit résoudre sous la racine projet"


# ─────────────────────────────────────────────────────────────────────────────
# 3. MIXTE — plat + niché sans doublon (y compris domaine portant un nom de couche)
# ─────────────────────────────────────────────────────────────────────────────
def test_3_mixed_flat_and_nested_no_duplicates(tmp_path: Path):
    docs_dir = tmp_path / "docs"
    # Foyer plat
    (docs_dir / "00-ingested").mkdir(parents=True)
    (docs_dir / "00-ingested" / "flat.md").write_text(
        "# Doc plat\n\nContenu du foyer plat.\n", encoding="utf-8"
    )
    # Foyer niché standard
    nested = docs_dir / "DomaineA" / "00-ingested"
    nested.mkdir(parents=True)
    (nested / "niche.md").write_text("# Doc niché\n\nContenu du foyer niché.\n", encoding="utf-8")
    # Bordure : un « domaine » qui porte un nom de couche (anti-chevauchement).
    # Ce fichier est couvert UNIQUEMENT par le foyer plat (rglob récursif).
    weird = docs_dir / "00-ingested" / "00-ingested"
    weird.mkdir(parents=True)
    (weird / "bordure.md").write_text(
        "# Bordure\n\nFichier sous couche homonyme.\n", encoding="utf-8"
    )

    db_file = tmp_path / "loop_mem.db"
    _index(docs_dir, db_file)

    paths = _fetch_paths(db_file)
    expected = [
        "docs/00-ingested/00-ingested/bordure.md",
        "docs/00-ingested/flat.md",
        "docs/DomaineA/00-ingested/niche.md",
    ]
    assert paths == expected, f"Arbre mixte attendu sans doublon, obtenu : {paths}"

    # Aucune clé de chunk (doc_path, line_start, line_end) ne doit apparaître deux fois
    # : un double comptage foyer plat + foyer niché produirait des doublons.
    rows = _fetch_chunk_rows(db_file)
    assert len(rows) == len(set(rows)), "Des chunks en doublon ont été insérés"


# ─────────────────────────────────────────────────────────────────────────────
# 4. LIMITE ASSUMÉE — profondeur 3 non découverte (ADR-0390 §A)
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize(
    "relative_dir",
    [
        "a/b/00-ingested",  # domaine > sous-domaine > couche
        "DomaineA/SousDomaine/01-architecture",
    ],
)
def test_4_depth_three_not_discovered(tmp_path: Path, relative_dir: str):
    docs_dir = tmp_path / "docs"
    deep_dir = docs_dir / Path(relative_dir)
    deep_dir.mkdir(parents=True)
    (deep_dir / "profond.md").write_text(
        "# Doc profond\n\nHors profondeur bornée.\n", encoding="utf-8"
    )
    # Un témoin plat pour prouver que l'indexation a bien tourné
    (docs_dir / "00-ingested").mkdir(parents=True)
    (docs_dir / "00-ingested" / "temoin.md").write_text(
        "# Témoin\n\nPreuve d'exécution.\n", encoding="utf-8"
    )

    db_file = tmp_path / "loop_mem.db"
    _index(docs_dir, db_file)

    paths = _fetch_paths(db_file)
    assert paths == ["docs/00-ingested/temoin.md"], (
        f"La profondeur 3 ne doit pas être découverte (limite assumée) ; "
        f"seul le témoin plat attendu, obtenu : {paths}"
    )


# ─────────────────────────────────────────────────────────────────────────────
# 5. CONTRAT doc_path — toute insertion résout sous la racine projet
# ─────────────────────────────────────────────────────────────────────────────
def test_5_doc_path_contract_resolves_under_project_root(tmp_path: Path):
    docs_dir = tmp_path / "docs"
    (docs_dir / "01-architecture").mkdir(parents=True)
    (docs_dir / "01-architecture" / "plat.md").write_text("# Plat\n\nContenu.\n", encoding="utf-8")
    nested = docs_dir / "DomaineB" / "04-transverse"
    nested.mkdir(parents=True)
    (nested / "niche.md").write_text("# Niché\n\nContenu.\n", encoding="utf-8")

    db_file = tmp_path / "loop_mem.db"
    _index(docs_dir, db_file)

    paths = _fetch_paths(db_file)
    assert len(paths) >= 2
    for doc_path in paths:
        assert doc_path.startswith(("docs/", "reference/")), (
            f"doc_path hors contrat (racine projet requise) : {doc_path}"
        )
        assert (tmp_path / doc_path).exists(), (
            f"doc_path non résoluble sous la racine projet (lien file:/// cassé) : {doc_path}"
        )


# ─────────────────────────────────────────────────────────────────────────────
# 6. INCRÉMENT/PURGE — suppression d'un fichier niché purgé au passage suivant
# ─────────────────────────────────────────────────────────────────────────────
def test_6_nested_incremental_purge(tmp_path: Path):
    docs_dir = tmp_path / "docs"
    nested = docs_dir / "DomaineC" / "00-ingested"
    nested.mkdir(parents=True)
    file_x = nested / "x.md"
    file_x.write_text("# Doc X\n\nContenu X.\n", encoding="utf-8")
    file_y = nested / "y.md"
    file_y.write_text("# Doc Y\n\nContenu Y.\n", encoding="utf-8")

    db_file = tmp_path / "loop_mem.db"
    count_1 = _index(docs_dir, db_file)
    assert count_1 >= 2
    assert len(_fetch_paths(db_file)) == 2

    # Aucune modification -> 0 insertion (incrément)
    assert _index(docs_dir, db_file) == 0

    # Suppression de x.md -> purgé au passage suivant, y.md intact
    file_x.unlink()
    _index(docs_dir, db_file)
    paths = _fetch_paths(db_file)
    assert paths == ["docs/DomaineC/00-ingested/y.md"], f"x.md doit être purgé, obtenu : {paths}"

    with get_observation_db_session(db_path=db_file) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM docs_chunks_fts WHERE project_name=? AND doc_path LIKE '%x.md'",
            (PROJECT,),
        )
        assert cursor.fetchone()[0] == 0, "Les lignes FTS de x.md doivent être purgées"
