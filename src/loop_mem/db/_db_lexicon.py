"""
_db_lexicon.py — Persistance du lexique métier (upsert SQLite + sync disque).

Extraction MLOOP-178-BE (BR=20) depuis src/loop_mem/db.py monolithique (956 L).
Famille Q1-A : lexique métier ADR-0327 — upsert double table (project_lexicon
+ project_lexicon_fts) et indexation disque (stories, CONTEXT.md, glossaires).

Couplage fort : sync_project_lexicon_from_disk appelle upsert_lexicon_term
(même module — aucune frontière artificielle). Tous les accès passent par
`with get_observation_db_session()` (ADR-0369).
"""

import json
import logging
from pathlib import Path
from typing import List

from src.loop_mem.db._db_connection import get_observation_db_session

logger = logging.getLogger(__name__)


def upsert_lexicon_term(
    project_name: str,
    term: str,
    aliases: List[str] = None,
    category: str = "domain_term",
    definition: str = "",
    target_type: str = "story",
    target_id: str = "",
    source_file: str = "",
) -> int:
    """Insère ou met à jour un terme du lexique projet dans SQLite et FTS5."""
    from datetime import datetime

    now_iso = datetime.now().isoformat()
    aliases_list = aliases or []
    aliases_json_str = json.dumps(aliases_list, ensure_ascii=False)
    aliases_text = " ".join(aliases_list)

    with get_observation_db_session() as conn:
        cursor = conn.cursor()
        # 1. Upsert dans la table project_lexicon
        cursor.execute(
            """
            INSERT INTO project_lexicon (
                project_name, term, aliases_json, category, definition,
                target_type, target_id, source_file, last_updated
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(project_name, term) DO UPDATE SET
                aliases_json=excluded.aliases_json,
                category=excluded.category,
                definition=excluded.definition,
                target_type=excluded.target_type,
                target_id=excluded.target_id,
                source_file=excluded.source_file,
                last_updated=excluded.last_updated
        """,
            (
                project_name,
                term,
                aliases_json_str,
                category,
                definition,
                target_type,
                target_id,
                source_file,
                now_iso,
            ),
        )
        cursor.execute(
            "SELECT id FROM project_lexicon WHERE project_name=? AND term=?", (project_name, term)
        )
        row = cursor.fetchone()
        lex_id = row[0] if row else cursor.lastrowid

        # 2. Rafraîchir l'index FTS5 (perf : rowid explicite = lex_id pour éviter un scan complet
        # de la table virtuelle sur la colonne UNINDEXED "lexicon_id" — DELETE WHERE col=? sur une
        # colonne UNINDEXED force un full scan O(n) par appel, soit O(n^2) sur toute la boucle
        # d'ingestion. Le rowid FTS5 est lui nativement indexé -> O(log n) par appel.)
        cursor.execute(
            "INSERT OR REPLACE INTO project_lexicon_fts (rowid, lexicon_id, project_name, term, aliases, category, definition, target_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                lex_id,
                str(lex_id),
                project_name,
                term,
                aliases_text,
                category,
                definition,
                target_id,
            ),
        )

        return lex_id


def sync_project_lexicon_from_disk(project_name: str) -> int:
    """
    Extrait dynamiquement tous les termes métiers, règles, tags, récits,
    définitions de CONTEXT.md et glossaires Markdown depuis le disque du projet
    et met à jour la base de données SQLite FTS5.
    """
    import yaml
    import re

    project_dir = Path("Projects") / project_name
    if not project_dir.exists():
        return 0

    count = 0

    # 1. Scanner les stories du backlog
    stories_dir = project_dir / "backlog" / "stories"
    if stories_dir.exists():
        for md_file in stories_dir.rglob("*.md"):
            try:
                content = md_file.read_text(encoding="utf-8", errors="ignore")
                fm_match = re.search(r"^---(.*?)---", content, re.DOTALL | re.MULTILINE)
                frontmatter = {}
                if fm_match:
                    frontmatter = yaml.safe_load(fm_match.group(1)) or {}

                h1_match = re.search(r"^#\s*(.*)$", content, re.MULTILINE)
                h1_title = h1_match.group(1).strip() if h1_match else md_file.stem

                story_id = str(frontmatter.get("id", md_file.stem))
                jira_key = str(frontmatter.get("jira_key", ""))
                tags = [str(t) for t in frontmatter.get("tags", [])]

                aliases = [story_id, jira_key] + tags
                aliases = [a for a in aliases if a]

                upsert_lexicon_term(
                    project_name=project_name,
                    term=h1_title,
                    aliases=aliases,
                    category="story",
                    definition=f"User Story {story_id} ({jira_key})",
                    target_type="story",
                    target_id=story_id,
                    source_file=str(md_file.relative_to(project_dir).as_posix()),
                )
                count += 1
            except Exception as e:
                logger.debug(
                    "Indexation lexique d'une story échouée, passage à la suivante",
                    exc_info=True,
                    extra={
                        "component": "loop_mem.db",
                        "operation": "index_project_lexicon",
                        "md_file": str(md_file),
                        "error": str(e),
                    },
                )
                continue

    # 2. Scanner CONTEXT.md (Lexique et concepts directeurs du domaine)
    context_file = project_dir / "CONTEXT.md"
    if context_file.exists():
        try:
            ctx_text = context_file.read_text(encoding="utf-8", errors="ignore")
            # Extraire H1 (ex: "# Contexte Lexique et Architecture - Boire & Frères (Segment 2)")
            h1_m = re.search(r"^#\s*(.*)$", ctx_text, re.MULTILINE)
            if h1_m:
                h1_val = h1_m.group(1).strip()
                # Extraire le nom de domaine principal (ex: "Boire & Frères")
                domain_parts = re.split(r"[-–—:]", h1_val)
                main_domain = domain_parts[-1].strip() if len(domain_parts) > 1 else h1_val
                upsert_lexicon_term(
                    project_name=project_name,
                    term=h1_val,
                    aliases=[main_domain, project_name],
                    category="context",
                    definition=f"Document de contexte et architecture {project_name}",
                    target_type="context",
                    target_id="CONTEXT",
                    source_file="CONTEXT.md",
                )
                count += 1

            # Extraire les concepts sous forme **[NomDuConcept]** : Description
            concept_matches = re.findall(
                r"\*\*\[(.*?)\]\*\*\s*:\s*(.*?)(?=\n\n|\n\*\*|\Z)", ctx_text, re.DOTALL
            )
            for c_term, c_def in concept_matches:
                clean_term = c_term.strip()
                clean_def = c_def.strip()
                # Extraire d'éventuels sous-termes (ex: "Segment 1 (CRM)" -> "Segment 1", "CRM")
                aliases = [clean_term]
                sub_parts = re.findall(r"\((.*?)\)", clean_term)
                if sub_parts:
                    aliases.extend(sub_parts)
                upsert_lexicon_term(
                    project_name=project_name,
                    term=clean_term,
                    aliases=aliases,
                    category="context_concept",
                    definition=clean_def[:300],
                    target_type="context_concept",
                    target_id=clean_term,
                    source_file="CONTEXT.md",
                )
                count += 1
        except Exception as e:
            logger.debug(
                "Indexation des concepts CONTEXT.md échouée",
                exc_info=True,
                extra={
                    "component": "loop_mem.db",
                    "operation": "index_project_lexicon",
                    "context_file": str(context_file),
                    "error": str(e),
                },
            )

    # 3. Scanner les glossaires et lexiques sous docs/
    docs_dir = project_dir / "docs"
    if docs_dir.exists():
        glossary_files = list(docs_dir.rglob("*glossair*.md")) + list(docs_dir.rglob("*lexiq*.md"))
        for g_file in glossary_files:
            try:
                g_text = g_file.read_text(encoding="utf-8", errors="ignore")
                # Extraire le titre du glossaire
                gh1_m = re.search(r"^#\s*(.*)$", g_text, re.MULTILINE)
                if gh1_m:
                    gh1_title = gh1_m.group(1).strip()
                    upsert_lexicon_term(
                        project_name=project_name,
                        term=gh1_title,
                        aliases=[g_file.stem, "glossaire", "lexique"],
                        category="glossary_doc",
                        definition=f"Glossaire métier {project_name}",
                        target_type="doc",
                        target_id=g_file.stem,
                        source_file=str(g_file.relative_to(project_dir).as_posix()),
                    )
                    count += 1

                # Parser les tableaux Markdown | Terme | Définition |
                table_rows = re.findall(r"\|\s*\*\*(.*?)\*\*\s*\|\s*(.*?)\s*\|", g_text)
                for raw_term, raw_def in table_rows:
                    if raw_term.lower() in [
                        "terme",
                        "termes",
                        "concept",
                        "identifiant",
                    ]:
                        continue
                    term_clean = raw_term.strip()
                    def_clean = raw_def.strip()
                    # Séparer les alias par slash ou parenthèses (ex: "Buggy / Chariot" -> "Buggy", "Chariot")
                    term_aliases = [
                        t.strip() for t in re.split(r"[/,\(\)]", term_clean) if t.strip()
                    ]
                    upsert_lexicon_term(
                        project_name=project_name,
                        term=term_aliases[0] if term_aliases else term_clean,
                        aliases=term_aliases,
                        category="business_term",
                        definition=def_clean[:300],
                        target_type="glossary_term",
                        target_id=term_clean,
                        source_file=str(g_file.relative_to(project_dir).as_posix()),
                    )
                    count += 1
            except Exception as e:
                logger.debug(
                    "Indexation d'un glossaire échouée, passage au fichier suivant",
                    exc_info=True,
                    extra={
                        "component": "loop_mem.db",
                        "operation": "index_project_lexicon",
                        "g_file": str(g_file),
                        "error": str(e),
                    },
                )
                continue

    return count
