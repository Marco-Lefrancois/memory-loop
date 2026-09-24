# -*- coding: utf-8 -*-
"""
Façade publique SemanticLexiconResolver (ADR-0327 / MLOOP-101-BE).

Module réduit à < 80 lignes ; délègue toute la logique au package lexicon/.
Les 16 sites d'import existants sont intangibles :
  `from src.utils.lexicon_resolver import SemanticLexiconResolver`
"""

from __future__ import annotations

import re
import yaml
from pathlib import Path
from typing import Optional, List

from src.utils.lexicon.entity_matcher import EntityMatcher
from src.utils.lexicon.project_resolver import ProjectResolver
from src.utils.logger import get_logger

logger = get_logger("lexicon_resolver")


class SemanticLexiconResolver:
    """
    Façade de résolution sémantique DYNAMIQUE et AGNOSTIQUE (mLoop Core - ADR-0327).
    Délègue à entity_matcher.py et project_resolver.py.
    """

    # ── API Publique intangible (16 sites d'import) ──────────────────────────

    @classmethod
    def normalize_string(cls, text: str) -> str:
        """Supprime accents, ponctuation et espaces pour comparaison floue uniforme."""
        return EntityMatcher.normalize_string(text)

    @classmethod
    def tokenize(cls, text: str) -> List[str]:
        """Découpe un texte en jetons de mots signifiants normalisés."""
        return EntityMatcher.tokenize(text)

    @classmethod
    def resolve_project_alias(cls, raw_name: str, base_dir: str = "Projects") -> Optional[str]:
        """
        Découvre dynamiquement les projets sous Projects/ et résout le nom de projet.
        API intangible (16 sites d'import).
        """
        return ProjectResolver.resolve_project(raw_name, base_dir)

    @classmethod
    def resolve_story_query(cls, query: str, stories_dir: Path) -> Optional[Path]:
        """
        Interroge d'abord la base SQLite FTS5, puis effectue un fallback dynamique
        sur les fichiers Markdown sous backlog/stories/.
        API intangible (16 sites d'import).
        """
        if not stories_dir.exists():
            return None

        # 0. Recherche ultra-rapide dans la base de données SQLite FTS5
        try:
            from src.loop_mem.db import search_lexicon_terms

            project_name = stories_dir.parent.parent.name
            db_hits = search_lexicon_terms(query, project_name=project_name, limit=3)
            if db_hits:
                src_rel = db_hits[0].get("source_file")
                if src_rel:
                    candidate_file = stories_dir.parent.parent / src_rel
                    if candidate_file.exists():
                        return candidate_file
        except Exception as e:
            logger.debug(
                "FTS5 story search non disponible",
                extra={"query": query, "error": str(e)},
            )

        clean_query = EntityMatcher.normalize_string(query)
        query_tokens = set(EntityMatcher.tokenize(query))
        num_matches = re.findall(r"\d+", query)
        target_num = int(num_matches[0]) if num_matches else None
        query_prefix = EntityMatcher.extract_query_prefix(query)

        from typing import Tuple, List as TList

        candidates: TList[Tuple[int, Path]] = []

        for f in stories_dir.rglob("*.md"):
            try:
                filename_norm = EntityMatcher.normalize_string(f.name)
                content = f.read_text(encoding="utf-8", errors="ignore")

                story_id = ""
                jira_key = ""
                title_text = ""
                tags: List[str] = []

                fm_match = re.search(r"^---(.*?)---", content, re.DOTALL | re.MULTILINE)
                if fm_match:
                    fm_block = fm_match.group(1)
                    id_m = re.search(r"^id:\s*['\"]?([^'\"\n\r]+)['\"]?", fm_block, re.MULTILINE)
                    if id_m:
                        story_id = id_m.group(1).strip()
                    jira_m = re.search(r"^jira_key:\s*['\"]?([^'\"\n\r]+)['\"]?", fm_block, re.MULTILINE)
                    if jira_m:
                        jira_key = jira_m.group(1).strip()
                    title_m = re.search(r"^title:\s*['\"]?([^'\"\n\r]+)['\"]?", fm_block, re.MULTILINE)
                    if title_m:
                        title_text = title_m.group(1).strip()
                    if "tags:" in fm_block:
                        tags_block = re.search(r"tags:\s*(?:\[([^\]]*)\]|\n((?:\s*-[^\n\r]+\r?\n?)+))", fm_block)
                        if tags_block:
                            if tags_block.group(1):
                                tags = [t.strip().strip("'\"") for t in tags_block.group(1).split(",") if t.strip()]
                            elif tags_block.group(2):
                                tags = [re.sub(r"^\s*-\s*", "", line).strip().strip("'\"") for line in tags_block.group(2).splitlines() if line.strip()]

                h1_match = re.search(r"^#\s*(.*)$", content, re.MULTILINE)
                if h1_match and not title_text:
                    title_text = h1_match.group(1).strip()

                score = EntityMatcher.score_story_candidate(
                    query=query,
                    clean_query=clean_query,
                    query_tokens=query_tokens,
                    target_num=target_num,
                    query_prefix=query_prefix,
                    story_id=story_id,
                    jira_key=jira_key,
                    title_text=title_text,
                    tags=tags,
                    filename_norm=filename_norm,
                    content=content,
                )

                if score > 0:
                    candidates.append((score, f))

            except Exception as e:
                logger.debug(
                    "Fichier lexique inexploitable lors du scoring, ignoré",
                    exc_info=True,
                    extra={
                        "component": "utils.lexicon_resolver",
                        "operation": "resolve_lexicon",
                        "error": str(e),
                    },
                )

        if candidates:
            candidates.sort(key=lambda x: x[0], reverse=True)
            best_score, best_file = candidates[0]
            if best_score >= 20:
                return best_file

        return None
