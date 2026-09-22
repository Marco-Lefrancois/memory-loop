"""
ingest_indexers.py - Index generation logic for Ingest Agent (ADR-0202 <=300L).

Extracted from ingest_agent.py to comply with modular ceiling.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

from src.cli import ZeroFluffConsole
from src.state import ProjectLayout


def generate_ingested_index(state, initiative: Optional[str] = None) -> None:
    """Generate complete semantic index of documents under docs/00-ingested/index.md (ADR-0102)."""
    if initiative:
        ingested_dir = Path("Projects") / "mLoop" / "docs" / initiative / "00-ingested"
    else:
        ingested_dir = Path("Projects") / "mLoop" / "docs" / "00-ingested"
    if not ingested_dir.exists():
        return

    index_file = ingested_dir / "index.md"
    lines = [
        f"# 📚 Index des Documents Ingérés — mLoop",
        "",
        "> **Statut :** SSOT Documentaire Ingestion Phase 1 | **Généré le :** "
        + datetime.now().strftime("%Y-%m-%d %H:%M"),
        "",
        "Ce document répertorie l'ensemble des sources brutes ingérées depuis `reference/` et converties en Markdown normalisé selon l'ADR-0102 et l'ADR-0335.",
        "",
        "## 🗂️ Sommaire par Catégorie Thématique",
        "",
    ]

    categories = {
        "01-sow-et-contrats": "📄 01. Énoncés des Travaux & Contrats (SOW)",
        "02-guides-et-specs": "📘 02. Guides d'Implémentation & Spécifications",
        "03-scans-et-inventaires": "📊 03. Scans, Inventaires & Audits",
        "04-api-et-techniques": "🔌 04. Références API & Architecture Technique",
        "05-maquettes-notes": "🎨 05. Maquettes & Transcriptions d'Écrans",
        "maquettes": "🎨 05. Maquettes & Transcriptions d'Écrans",
    }

    # Dynamic discovery of any other subfolder
    base_ingested = Path("Projects") / "mLoop" / "docs" / "00-ingested"
    for sub in sorted(base_ingested.iterdir(), key=lambda d: d.name):
        if sub.is_dir() and sub.name not in categories and not sub.name.startswith("."):
            categories[sub.name] = f"📦 {sub.name.replace('-', ' ').title()}"

    found_any = False
    for cat_dir_name, cat_title in categories.items():
        cat_path = Path("Projects") / "mLoop" / "docs" / "00-ingested" / cat_dir_name
        md_files = list(cat_path.glob("*.md")) if cat_path.exists() else []
        if md_files:
            found_any = True
            lines.append(f"### {cat_title}")
            lines.append("")
            lines.append("| Document Markdown | Fichier Source Original | Termes Clés Identifiés |")
            lines.append("| :--- | :--- | :--- |")
            for mf in sorted(md_files, key=lambda f: f.name):
                matching = [
                    s for s in state.ingested_sources if Path(s.get("filepath", "")).stem == mf.stem
                ]
                orig_file = matching[0].get("filename", "N/A") if matching else "reference/"
                terms_str = (
                    ", ".join(f"`{t}`" for t in (matching[0].get("terms", [])[:5]))
                    if matching
                    else "—"
                )
                rel_link = f"[{mf.name}]({cat_dir_name}/{mf.name})"
                lines.append(f"| {rel_link} | `{orig_file}` | {terms_str} |")
            lines.append("")

    root_mds = [
        f
        for f in (Path("Projects") / "mLoop" / "docs" / "00-ingested").glob("*.md")
        if f.name not in ["index.md", "README.md"]
    ]
    if root_mds:
        found_any = True
        lines.append("### 📁 Autres Documents Ingérés")
        lines.append("")
        for mf in sorted(root_mds, key=lambda f: f.name):
            lines.append(f"- [{mf.name}]({mf.name})")
        lines.append("")

    if not found_any:
        lines.append("*(Aucun document ingéré pour le moment)*\n")

    try:
        index_file = Path("Projects") / "mLoop" / "docs" / "00-ingested" / "index.md"
        index_file.write_text("\n".join(lines), encoding="utf-8")
        ZeroFluffConsole.info(f"Index SSOT 00-ingested généré : {index_file}")
    except Exception as e:
        ZeroFluffConsole.warning(f"Impossible d'écrire 00-ingested/index.md : {e}")


def generate_docs_root_index(state) -> None:
    """Generate or update the SSOT root orientation map under docs/index.md (ADR-0102)."""
    docs_dir = Path("Projects") / "mLoop" / "docs"
    if not docs_dir.exists():
        return

    index_file = docs_dir / "index.md"
    if not index_file.exists() or "<!-- MLOOP_AUTO_GENERATED -->" in index_file.read_text(
        encoding="utf-8", errors="ignore"
    ):
        content = f"""<!-- MLOOP_AUTO_GENERATED -->
# 🧭 Carte d'Orientation SSOT & Architecture — mLoop

> **Source Unique de Vérité (SSOT)** conforme à l'[ADR-0102](standards/adr-system/0102-structure-ssot-dossier-docs.md).
> **Dernière synchronisation :** {datetime.now().strftime("%Y-%m-%d %H:%M")}

---

## 🗺️ Arborescence Canonique du Projet

| Dossier | Description & Rôle SSOT | Accès |
| :--- | :--- | :---: |
| **`00-ingested/`** | Matière première ingérée depuis `reference/` (SOW, specs, audits, APIs, maquettes). | [Explorer](00-ingested/index.md) |
| **`01-architecture/`** | Décisions d'architecture (ADRs), Énoncé des travaux (SOW), schémas techniques. | [Explorer](01-architecture/) |
| **`02-business-rules/`** | Catalogue vivant des règles d'affaires du domaine (`RM-XXX`). | [Explorer](02-business-rules/) |
| **`03-models/`** | Modèles de données, dictionnaires d'entités, schémas DrawDB / SQL. | [Explorer](03-models/) |
| **`04-transverse/`** | Questions ouvertes client/dev (`Q-XXX`), journal de bord et lexique métier. | [Explorer](04-transverse/) |
| **`05-assets/`** | Actifs visuels versionnés (Maquettes SVG, diagrammes, images). | [Explorer](05-assets/) |

---

## 📌 Raccourcis Clés du Projet
- 📋 **Sprint Backlog Maître** : [`backlog/sprint_backlog.md`](../backlog/sprint_backlog.md)
- 📖 **Lexique du Domaine** : [`docs/04-transverse/lexique_domaine.md`](04-transverse/lexique_domaine.md)
- ❓ **Questions Ouvertes Client** : [`docs/04-transverse/00-questions-ouvertes-client.md`](04-transverse/00-questions-ouvertes-client.md)
"""
        try:
            index_file = Path("Projects") / "mLoop" / "docs" / "index.md"
            index_file.write_text(content, encoding="utf-8")
            ZeroFluffConsole.info(f"Carte d'orientation SSOT racine synchronisée : {index_file}")
        except Exception as e:
            ZeroFluffConsole.warning(f"Impossible d'écrire docs/index.md : {e}")


def generate_maquettes_index(state) -> None:
    """Generate global maquettes index and mapping under docs/00-ingested/05-maquettes-notes/00-index-maquettes.md."""
    maquettes_dir = Path("Projects") / "mLoop" / "docs" / "00-ingested" / "05-maquettes-notes"
    if not maquettes_dir.exists():
        maquettes_dir = Path("Projects") / "mLoop" / "docs" / "00-ingested" / "maquettes"
    if maquettes_dir.exists() and any(maquettes_dir.glob("*.md")):
        try:
            from src.converters.svg_to_md import generate_maquettes_index

            index_path = generate_maquettes_index(maquettes_dir)
            ZeroFluffConsole.info(f"Index et Cartographie des Maquettes synchronisé : {index_path}")
        except Exception as e:
            ZeroFluffConsole.warning(f"Impossible de générer 00-index-maquettes.md : {e}")


def generate_lod_sidecars(state) -> None:
    """Generate LOD .abstract.md and .overview.md sidecars for docs/00-ingested/ and subdirs (ADR-0335)."""
    ingested_dir = Path("Projects") / "mLoop" / "docs" / "00-ingested"
    if not ingested_dir.exists():
        return

    # 1. Generate for each subdir of 00-ingested
    for sub_dir in ingested_dir.iterdir():
        if sub_dir.is_dir() and not sub_dir.name.startswith("."):
            if any(
                f.is_file() and f.suffix.lower() == ".md" and not f.name.startswith(".")
                for f in sub_dir.iterdir()
            ):
                try:
                    from src.core.lod_generator import LODGenerator

                    LODGenerator.generate_lod_sidecars(
                        directory_path=sub_dir,
                        source_info={"kind": "ingested_category", "category": sub_dir.name},
                        project_name="mLoop",
                    )
                except Exception as e:
                    ZeroFluffConsole.warning(f"Erreur sidecar LOD pour {sub_dir.name} : {e}")

    # 2. Generate for 00-ingested root if files present
    try:
        from src.core.lod_generator import LODGenerator

        LODGenerator.generate_lod_sidecars(
            directory_path=Path("Projects") / "mLoop" / "docs" / "00-ingested",
            source_info={
                "kind": "ingested_root",
                "uri": "mloop://docs/00-ingested",
            },
            project_name="mLoop",
        )
        ZeroFluffConsole.info("Sidecars LOD (L0/L1) synchronisés sous docs/00-ingested/")
    except Exception as e:
        ZeroFluffConsole.warning(f"Erreur sidecar LOD racine 00-ingested : {e}")
