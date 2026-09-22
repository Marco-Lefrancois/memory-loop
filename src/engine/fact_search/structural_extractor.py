# -*- coding: utf-8 -*-
"""
Structural Wikilink & Frontmatter Extractor (mLoop Core - Quick Win Kwipu).

Extrait de manière déterministe (zéro coût LLM) les triplets de relations
à partir des wikilinks Obsidian [[cible]] et du YAML frontmatter :
1. Inférence contextuelle des relations à partir de la phrase entourant le lien.
2. Extraction des métadonnées de dépendance et d'appartenance de récits (Epic, Status, Tags).
3. Injection directe dans le lexique métier project_lexicon pour navigation et expansion.
"""

from __future__ import annotations

import re
import yaml
from pathlib import Path
from typing import List, Dict, Tuple, Any, Optional

from src.loop_mem.db import upsert_lexicon_term
from src.utils.logger import get_logger

logger = get_logger("fact_search.structural_extractor")

# Motifs d'inférence de relation par expression régulière (FR & EN)
RELATION_PATTERNS_FR_EN: List[Tuple[re.Pattern, str]] = [
    # Dépendance & Blocage
    (re.compile(r'(?i)\b(?:dépend\s+de|depend[s]?\s+on|bloqué\s+par|blocked\s+by)\b'), "depends_on"),
    (re.compile(r'(?i)\b(?:bloque|blocks|prérequis\s+pour|prerequisite\s+for)\b'), "blocks"),
    # Implémentation & Référence
    (re.compile(r'(?i)\b(?:implémente|implements|réalise|conforme\s+à)\b'), "implements"),
    (re.compile(r'(?i)\b(?:remplace|supersedes|obsolète\s+par)\b'), "supersedes"),
    (re.compile(r'(?i)\b(?:lié\s+à|relates\s+to|associé\s+à|associated\s+with)\b'), "relates_to"),
    # Responsabilité & Propriété
    (re.compile(r'(?i)\b(?:responsable\s+(?:de|du|des)|responsible\s+for)\b'), "responsible_for"),
    (re.compile(r'(?i)\b(?:assigné\s+à|assigned\s+to|attribué\s+à)\b'), "assigned_to"),
    # Utilisation & Technologie
    (re.compile(r'(?i)\b(?:utilise|uses|consomme|s\'appuie\s+sur|based\s+on)\b'), "uses"),
    (re.compile(r'(?i)\b(?:fournit|provides|expose|produit)\b'), "provides"),
    # Test & Validation
    (re.compile(r'(?i)\b(?:teste|tests|valide|validates|vérifie)\b'), "tests"),
    # Appartenance
    (re.compile(r'(?i)\b(?:partie\s+de|part\s+of|sous-système\s+de|module\s+de)\b'), "part_of"),
]

FALLBACK_RELATION = "references"
WIKILINK_RE = re.compile(r'\[\[([^\]|]+)(?:\|([^\]]+))?\]\]')
FRONTMATTER_RE = re.compile(r'^---\s*\n(.*?)\n---\s*\n', re.DOTALL)


class StructuralWikilinkExtractor:
    """Extracteur déterministe de relations wikilinks et frontmatter."""

    @classmethod
    def infer_relation_from_context(cls, line: str, default: str = FALLBACK_RELATION) -> str:
        """Déduit le type de relation sémantique à partir du contexte textuel immédiat."""
        for pattern, rel_type in RELATION_PATTERNS_FR_EN:
            if pattern.search(line):
                return rel_type
        return default

    @classmethod
    def extract_wikilinks_from_text(
        cls, file_name: str, text: str
    ) -> List[Tuple[str, str, str]]:
        """
        Extrait tous les wikilinks d'un texte avec inférence contextuelle de la relation.
        Retourne une liste de triplets (source, relation, cible).
        """
        triples: List[Tuple[str, str, str]] = []
        seen = set()

        for match in WIKILINK_RE.finditer(text):
            target = match.group(1).strip()
            if not target:
                continue

            pair_key = (file_name.lower(), target.lower())
            if pair_key in seen:
                continue
            seen.add(pair_key)

            # Ligne de contexte immédiate entourant le wikilink
            line_start = text.rfind("\n", 0, match.start()) + 1
            line_end = text.find("\n", match.end())
            if line_end == -1:
                line_end = len(text)
            line = text[line_start:line_end].strip()

            # Isoler la clause locale précédant le wikilink (depuis le dernier délimiteur ou lien)
            prev_link_end = text.rfind("]]", 0, match.start())
            clause_start = max(line_start, prev_link_end + 2 if prev_link_end != -1 and prev_link_end > line_start else line_start)
            clause = text[clause_start:match.start()].strip()

            relation = cls.infer_relation_from_context(clause)
            if relation == FALLBACK_RELATION:
                relation = cls.infer_relation_from_context(line)

            triples.append((file_name, relation, target))

        return triples

    @classmethod
    def extract_frontmatter_relations(
        cls, file_name: str, frontmatter: Dict[str, Any]
    ) -> List[Tuple[str, str, str]]:
        """
        Génère des triplets relationnels à partir du frontmatter YAML d'une story ou note.
        """
        triples: List[Tuple[str, str, str]] = []
        if not isinstance(frontmatter, dict):
            return triples

        # Epic parent
        epic_key = frontmatter.get("epic_key")
        if epic_key:
            triples.append((file_name, "belongs_to_epic", str(epic_key).strip()))

        # Statut du récit / document
        status = frontmatter.get("status")
        if status:
            triples.append((file_name, "has_status", str(status).strip()))

        # Dépendances explicites
        deps = frontmatter.get("dependencies") or frontmatter.get("depends_on") or []
        if isinstance(deps, str):
            deps = [deps]
        if isinstance(deps, list):
            for dep in deps:
                if dep:
                    triples.append((file_name, "depends_on", str(dep).strip()))

        # Relations transverses
        relates = frontmatter.get("relates_to") or frontmatter.get("related") or []
        if isinstance(relates, str):
            relates = [relates]
        if isinstance(relates, list):
            for rel in relates:
                if rel:
                    triples.append((file_name, "relates_to", str(rel).strip()))

        # Tags
        tags = frontmatter.get("tags") or []
        if isinstance(tags, list):
            for tag in tags:
                if tag:
                    triples.append((file_name, "has_tag", str(tag).strip()))

        return triples

    @classmethod
    def extract_from_file(
        cls, file_path: Path
    ) -> Tuple[List[Tuple[str, str, str]], Dict[str, Any]]:
        """Extrait l'ensemble des relations d'un fichier Markdown (wikilinks + frontmatter)."""
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            logger.warning(f"Impossible de lire {file_path}: {e}")
            return [], {}

        file_stem = file_path.stem
        frontmatter = {}
        body = content

        fm_match = FRONTMATTER_RE.match(content.lstrip("\ufeff").lstrip())
        if fm_match:
            try:
                fm_data = yaml.safe_load(fm_match.group(1))
                if isinstance(fm_data, dict):
                    frontmatter = fm_data
                    body = content[fm_match.end():]
            except Exception as e:
                logger.debug(
                    "Frontmatter YAML illisible, extraction du corps seule effectuée",
                    exc_info=True,
                    extra={
                        "component": "engine.fact_search.structural_extractor",
                        "operation": "extract_structural",
                        "error": str(e),
                    },
                )

        wikilink_triples = cls.extract_wikilinks_from_text(file_stem, body)
        fm_triples = cls.extract_frontmatter_relations(file_stem, frontmatter)

        all_triples = list({(s, r, o) for s, r, o in (wikilink_triples + fm_triples)})
        return all_triples, frontmatter

    @classmethod
    def sync_project_structural_relations(
        cls,
        project_name: str,
        project_dir: Optional[Path] = None,
    ) -> int:
        """
        Scanne les dossiers backlog/stories et docs/ pour extraire
        toutes les relations et les synchroniser dans project_lexicon.
        """
        if project_dir is None:
            project_dir = Path("Projects") / project_name
            if not project_dir.exists():
                project_dir = Path.cwd()

        scanned_files: List[Path] = []

        stories_dir = project_dir / "backlog" / "stories"
        if stories_dir.exists():
            scanned_files.extend(stories_dir.rglob("*.md"))

        docs_dir = project_dir / "docs"
        if docs_dir.exists():
            scanned_files.extend(docs_dir.rglob("*.md"))

        total_relations_synced = 0

        for md_file in scanned_files:
            triples, fm = cls.extract_from_file(md_file)
            rel_file = str(md_file.relative_to(project_dir).as_posix()) if project_dir in md_file.parents else md_file.name

            for source, relation, target in triples:
                # Stocker dans project_lexicon
                term_entry = f"{source} --[{relation}]--> {target}"
                upsert_lexicon_term(
                    project_name=project_name,
                    term=term_entry,
                    aliases=[source, target, relation],
                    category="structural_relation",
                    definition=f"Relation {relation} entre {source} et {target}",
                    target_type="relation",
                    target_id=target,
                    source_file=rel_file,
                )
                total_relations_synced += 1

        logger.info(
            f"[{project_name}] {total_relations_synced} relations structurelles synchronisées dans le lexique."
        )
        return total_relations_synced
