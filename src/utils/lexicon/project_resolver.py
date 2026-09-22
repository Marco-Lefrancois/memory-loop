# -*- coding: utf-8 -*-
"""
Résolution contextuelle de projets et tie-break managérial.
Sous-module du package lexicon (ADR-0202 / MLOOP-101-BE).
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Tuple

from src.utils.logger import get_logger
from src.utils.lexicon.entity_matcher import EntityMatcher

logger = get_logger("lexicon.project_resolver")


class ProjectResolver:
    """
    Moteur de découverte et de résolution dynamique des projets sous Projects/.
    Zéro dictionnaire codé en dur : extrait dynamiquement le vocabulaire, les titres,
    les tags et les métadonnées depuis le système de fichiers, le graphe et les fichiers Markdown.
    """

    @classmethod
    def _load_fts5_hits(cls, raw_name: str) -> Dict[str, int]:
        """Interroge la base SQLite FTS5 (project_lexicon) et retourne les hits par projet."""
        fts_hits_by_project: Dict[str, int] = {}
        try:
            from src.loop_mem.db import search_lexicon_terms

            db_hits = search_lexicon_terms(raw_name, limit=10)
            for hit in db_hits:
                p_name = hit.get("project_name")
                if p_name:
                    fts_hits_by_project[p_name] = fts_hits_by_project.get(p_name, 0) + 1
        except Exception as e:
            logger.debug(
                "Recherche FTS5 lexique non disponible ou échouée",
                extra={"raw_name": raw_name, "error": str(e)},
            )
        return fts_hits_by_project

    @classmethod
    def _score_project_folder(
        cls,
        p: Path,
        clean_query: str,
        query_tokens: set,
        fts_hits_by_project: Dict[str, int],
    ) -> int:
        """
        Calcule le score de correspondance pour un dossier projet donné.
        Retourne le score final (0 si hors périmètre).
        """
        folder_name = p.name
        score = EntityMatcher.compute_folder_score(clean_query, query_tokens, folder_name)

        # Bonus Dictionnaire de Lexique FTS5 (ADR-0327)
        if folder_name in fts_hits_by_project:
            score += min(fts_hits_by_project[folder_name] * 20, 40)

        # Inspection dynamique de CONTEXT.md (Lexique de domaine)
        context_file = p / "CONTEXT.md"
        if context_file.exists():
            try:
                ctx_head = context_file.read_text(encoding="utf-8")[:1000]
                ctx_tokens = set(EntityMatcher.tokenize(ctx_head))
                ctx_overlap = query_tokens.intersection(ctx_tokens)
                score += len(ctx_overlap) * 15
            except Exception as e:
                logger.debug(
                    "Lecture context ignorée",
                    extra={"context_file": str(context_file), "error": str(e)},
                )

        # Inspection des métadonnées (README.md, jira_config.json)
        jira_cfg = p / "jira_config.json"
        if jira_cfg.exists():
            try:
                cfg_text = jira_cfg.read_text(encoding="utf-8")
                if clean_query in EntityMatcher.normalize_string(cfg_text):
                    score += 20
            except Exception as e:
                logger.debug(
                    "Lecture jira_config ignorée",
                    extra={"jira_cfg": str(jira_cfg), "error": str(e)},
                )

        readme_file = p / "README.md"
        if readme_file.exists():
            try:
                head = readme_file.read_text(encoding="utf-8")[:500]
                head_tokens = set(EntityMatcher.tokenize(head))
                if query_tokens.intersection(head_tokens):
                    score += 15
            except Exception as e:
                logger.debug(
                    "Lecture readme ignorée",
                    extra={"readme_file": str(readme_file), "error": str(e)},
                )

        # Inspection des documents ingérés (docs/00-ingested/) — désambiguïsation sous-projets modulaires
        ingested_dir = p / "docs" / "00-ingested"
        if ingested_dir.exists() and query_tokens:
            try:
                ingested_overlap: set = set()
                for md_file in ingested_dir.glob("*.md"):
                    try:
                        head = md_file.read_text(encoding="utf-8", errors="ignore")[:2000]
                    except Exception as e:
                        logger.debug(
                            "Lecture document ingéré ignorée pendant le scoring projet",
                            exc_info=True,
                            extra={
                                "component": "lexicon.project_resolver",
                                "operation": "_score_project_folder",
                                "md_file": str(md_file),
                                "error": str(e),
                            },
                        )
                        continue
                    ingested_overlap |= query_tokens.intersection(EntityMatcher.tokenize(head))
                    if ingested_overlap == query_tokens:
                        break
                if len(ingested_overlap) >= 2 or (
                    query_tokens and len(ingested_overlap) / len(query_tokens) >= 0.5
                ):
                    score += len(ingested_overlap) * 18
            except Exception as e:
                logger.debug(
                    "Inspection ingested ignorée",
                    extra={"ingested_dir": str(ingested_dir), "error": str(e)},
                )

        # Règle d'or : le bonus de viabilité SSOT ne s'applique que si score > 0
        if score == 0:
            return 0

        has_backlog = (p / "backlog" / "sprint_backlog.md").exists() or (
            p / "backlog" / "stories"
        ).is_dir()
        has_docs = (p / "docs").is_dir()
        has_agents = (p / "AGENTS.md").exists()
        context_exists = context_file.exists()

        if has_backlog:
            score += 40
        if has_agents or context_exists:
            score += 15

        # Pénalité sévère si dossier fantôme (aucun pilier SSOT)
        if not has_backlog and not has_docs and not has_agents and not context_exists:
            score -= 50

        return score

    @classmethod
    def resolve_project(cls, raw_name: str, base_dir: str = "Projects") -> Optional[str]:
        """
        Découvre dynamiquement les projets sous Projects/ et les fait correspondre au prompt
        avec pondération SSOT et pénalité de dossier fantôme.
        """
        projects_dir = Path(base_dir)
        if not projects_dir.exists():
            return None

        clean_query = EntityMatcher.normalize_string(raw_name)
        query_tokens = set(EntityMatcher.tokenize(raw_name))

        # 0-bis. Correspondance exacte case-insensitive directe (priorité absolue)
        for p in projects_dir.iterdir():
            if not p.is_dir() or p.name.startswith(".") or p.name.startswith("_"):
                continue
            if p.name.endswith("_DEPRECATED"):
                continue
            if raw_name.lower() == p.name.lower():
                return p.name

        fts_hits_by_project = cls._load_fts5_hits(raw_name)
        candidates: List[Tuple[int, str]] = []

        for p in projects_dir.iterdir():
            if not p.is_dir() or p.name.startswith(".") or p.name.startswith("_"):
                continue
            if p.name.endswith("_DEPRECATED"):
                continue

            # 1. Correspondance exacte normalisée (Priorité absolue)
            norm_folder = EntityMatcher.normalize_string(p.name)
            if clean_query == norm_folder:
                return p.name

            score = cls._score_project_folder(p, clean_query, query_tokens, fts_hits_by_project)

            if score > 0:
                candidates.append((score, p.name))

        if candidates:
            # Tri déterministe : score décroissant, puis nom de dossier croissant (alphabétique)
            candidates.sort(key=lambda x: (-x[0], x[1]))
            best_score, best_project = candidates[0]
            if best_score >= 30:
                return best_project

        return None
