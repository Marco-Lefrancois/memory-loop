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

                frontmatter: dict = {}
                h1_title = ""

                fm_match = re.search(r"^---(.*?)---", content, re.DOTALL | re.MULTILINE)
                if fm_match:
                    try:
                        frontmatter = yaml.safe_load(fm_match.group(1)) or {}
                    except Exception as e:
                        logger.debug(
                            "Frontmatter YAML invalide ignoré",
                            extra={"file": str(f), "error": str(e)},
                        )

                h1_match = re.search(r"^#\s*(.*)$", content, re.MULTILINE)
                if h1_match:
                    h1_title = h1_match.group(1).strip()

                story_id = str(frontmatter.get("id", ""))
                jira_key = str(frontmatter.get("jira_key", ""))
                title_text = str(frontmatter.get("title", "")) or h1_title
                tags = [str(t) for t in frontmatter.get("tags", [])]

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
