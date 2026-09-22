"""
LLM-Wiki Structuring Engine (Pattern Karpathy & Obsidian PKM).

Analyse les documents ingérés sous docs/00-ingested/ et génère :
- Des notes de concepts atomiques croisées.
- Des liens bidirectionnels [[concepts]] reconnus nativement par Obsidian.
- Un index sémantique du domaine (docs/00-ingested/WIKI_INDEX.md).
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Set, Tuple
from src.utils.logger import get_logger

logger = get_logger("pipelines.llm_wiki")


class LLMWikiEngine:
    """Moteur de structuration et de maillage de base de connaissances au format LLM-Wiki."""

    def __init__(self, project_root: Path | str) -> None:
        self.project_root = Path(project_root)
        self.ingested_dir = self.project_root / "docs" / "00-ingested"

    def scan_and_link(self) -> Dict[str, Any]:
        """
        Scanne tous les fichiers Markdown sous docs/00-ingested/ et docs/,
        identifie les concepts clés et injecte les liens bidirectionnels [[WikiLinks]].
        """
        if not self.ingested_dir.exists():
            self.ingested_dir.mkdir(parents=True, exist_ok=True)

        # 1. Identifier les concepts existants
        concepts = self._extract_domain_concepts()
        
        # 2. Enrichir les documents avec des liens bidirectionnels
        files_updated = 0
        links_created = 0

        for md_file in self.ingested_dir.glob("**/*.md"):
            if md_file.name in {"WIKI_INDEX.md", "README.md"}:
                continue
            
            content = md_file.read_text(encoding="utf-8", errors="ignore")
            new_content, count = self._inject_wikilinks(content, concepts, current_file=md_file.stem)
            
            if count > 0 and new_content != content:
                md_file.write_text(new_content, encoding="utf-8")
                files_updated += 1
                links_created += count

        # 3. Générer/mettre à jour WIKI_INDEX.md
        self._generate_wiki_index(concepts)

        return {
            "concepts_indexed": len(concepts),
            "files_updated": files_updated,
            "links_created": links_created,
            "wiki_index_path": str(self.ingested_dir / "WIKI_INDEX.md"),
        }

    def _extract_domain_concepts(self) -> Dict[str, str]:
        """Extrait les termes et entités métier majeures (ex: OneTrustSDK, ConsentBanner, ConsentGroup)."""
        concepts: Dict[str, str] = {}
        
        # Scanner docs/
        docs_dir = self.project_root / "docs"
        if not docs_dir.exists():
            return concepts

        for md_file in docs_dir.glob("**/*.md"):
            stem = md_file.stem
            if stem.startswith("RM-") or stem.startswith("ADR-") or stem.isupper() or "_" in stem:
                concepts[stem] = str(md_file.relative_to(self.project_root))
            
            # Recherche de titres de niveau 1 ou 2
            try:
                content = md_file.read_text(encoding="utf-8", errors="ignore")
                for line in content.splitlines():
                    if line.startswith("# ") or line.startswith("## "):
                        title = line.lstrip("#").strip()
                        # Si le titre est un nom de concept propre (3 à 30 chars, sans ponctuation bizarre)
                        if 3 <= len(title) <= 30 and not title.startswith("Scénario") and not title.startswith("Pilier"):
                            clean_title = re.sub(r"[^\w\s-]", "", title).strip()
                            if clean_title and clean_title not in concepts:
                                concepts[clean_title] = str(md_file.relative_to(self.project_root))
            except Exception as e:
                logger.debug(
                    "Page wiki illisible lors de l'indexation des concepts, ignorée",
                    exc_info=True,
                    extra={
                        "component": "pipelines.llm_wiki",
                        "operation": "build_concept_index",
                        "error": str(e),
                    },
                )

        return concepts

    def _inject_wikilinks(self, content: str, concepts: Dict[str, str], current_file: str) -> Tuple[str, int]:
        """Injecte les liens [[Concept]] dans le texte Markdown de manière idempotente."""
        count = 0
        new_content = content

        for concept in sorted(concepts.keys(), key=len, reverse=True):
            if concept.lower() == current_file.lower():
                continue
            
            # Éviter de linker ce qui est déjà linké [[...]] ou dans un bloc de code
            pattern = rf"(?<!\[\[)(?<!`)\b({re.escape(concept)})\b(?!\]\])(?!`)"
            
            def repl(match: re.Match) -> str:
                nonlocal count
                count += 1
                return f"[[{match.group(1)}]]"

            # Remplacement limité à 3 occurrences par concept par fichier pour ne pas surcharger
            new_content, n = re.subn(pattern, repl, new_content, count=3)

        return new_content, count

    def _generate_wiki_index(self, concepts: Dict[str, str]) -> None:
        """Génère le document WIKI_INDEX.md regroupant tous les concepts atomiques reliés."""
        index_file = self.ingested_dir / "WIKI_INDEX.md"
        lines = [
            "# 🌐 Index Sémantique LLM-Wiki (Second Brain Obsidian)",
            "",
            "Ce document cartographie l'ensemble des concepts, règles métier et entités du projet sous forme de graphe wikifié.",
            "",
            "## 📑 Concepts & Entités Indexés",
            "",
        ]

        for concept in sorted(concepts.keys()):
            rel_path = concepts[concept]
            lines.append(f"- **[[{concept}]]** — *(Source : `{rel_path}`)*")

        lines.extend([
            "",
            "---",
            "*Généré automatiquement par `LLMWikiEngine` (Memory Loop 2.0).* ",
        ])

        index_file.write_text("\n".join(lines), encoding="utf-8")


def sync_llm_wiki(project_root: Path | str) -> Dict[str, Any]:
    """Exécute la synchronisation de la base LLM-Wiki."""
    engine = LLMWikiEngine(project_root)
    return engine.scan_and_link()
