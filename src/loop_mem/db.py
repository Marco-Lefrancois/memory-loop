import sqlite3
import json
import logging
import re
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


def get_active_project() -> Optional[str]:
    """Retourne le nom du projet actif stocké dans memory/active_project.json."""
    active_json = Path("memory/active_project.json")
    if active_json.exists():
        try:
            with open(active_json, "r", encoding="utf-8") as f:
                return json.load(f).get("active_project")
        except Exception:
            pass
    return None


def search_in_memory(project_path: Path, query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Recherche plein texte en mémoire dans le graphe consolidé du projet.
    Fusionne knowledge_graph.json et graph.json, et filtre sur les attributs textuels.
    """
    nodes = []

    # 1. Charger knowledge_graph.json
    kg_file = project_path / "memory" / "knowledge_graph.json"
    if kg_file.exists():
        try:
            with open(kg_file, "r", encoding="utf-8") as f:
                nodes.extend(json.load(f).get("nodes", []))
        except Exception:
            pass

    # 2. Charger graph.json
    graph_file = project_path / "graphify-out" / "graph.json"
    if graph_file.exists():
        try:
            with open(graph_file, "r", encoding="utf-8") as f:
                nodes.extend(json.load(f).get("nodes", []))
        except Exception:
            pass

    # Dédupliquer les nœuds par ID pour éviter les doublons de fusion
    seen_ids = set()
    unique_nodes = []
    for n in nodes:
        node_id = n.get("id")
        if node_id and node_id not in seen_ids:
            seen_ids.add(node_id)
            unique_nodes.append(n)

    query_lower = query.lower().strip()
    if not query_lower:
        return []

    results = []
    for n in unique_nodes:
        node_id = n.get("id", "")
        label = n.get("label", "")
        category = n.get("category", "")
        props = n.get("properties", {})

        desc = props.get("description", "")
        text_chunk = props.get("text_chunk", "")

        # Concaténation de recherche
        search_content = f"{node_id} {label} {category} {desc} {text_chunk}".lower()

        if query_lower in search_content:
            # Calcul du score de pertinence simple
            score = 1.0
            if query_lower == node_id.lower():
                score += 5.0
            elif query_lower in node_id.lower():
                score += 3.0

            if query_lower == label.lower():
                score += 4.0
            elif query_lower in label.lower():
                score += 2.0

            if query_lower in category.lower():
                score += 1.0

            # Snippet d'aperçu propre
            snippet_source = text_chunk or desc or "Pas de description."
            snippet = snippet_source[:150] + "..." if len(snippet_source) > 150 else snippet_source

            results.append(
                {
                    "id": node_id,
                    "label": label or node_id,
                    "category": category,
                    "snippet": snippet,
                    "score": score,
                }
            )

    # Trier par score décroissant
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:limit]


# ═══════════════════════════════════════════════════════════
# Observation Memory (Session Memory) — MCP loop_mem bridge
# ═══════════════════════════════════════════════════════════
# Stocke et indexe en FTS5 les observations de session
# (décisions, bugs, features, découvertes) par projet.
# Base dédiée : memory/loop_mem.db
# ═══════════════════════════════════════════════════════════

from contextlib import contextmanager

_OBSERVATION_DB_PATH = Path("memory/loop_mem.db")


@contextmanager
def get_observation_db_session(db_path: Path = _OBSERVATION_DB_PATH):
    """
    Context Manager pour la base de données des observations mLoop.
    Garantit l'auto-commit des transactions, le rollback en cas d'erreur
    et la fermeture systématique de la connexion (Zero DB Lock avec WAL mode).
    """
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), timeout=15.0)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA busy_timeout=20000;")
    except Exception:
        pass
    _init_observation_db(conn, db_path)
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise RuntimeError(f"[DB ERROR] Transaction annulée sur {db_path} : {e}") from e
    finally:
        conn.close()


def _get_observation_conn() -> sqlite3.Connection:
    """Retourne une connexion à la base des observations (Legacy helper déprécié — ADR-0369)."""
    import warnings

    warnings.warn(
        "_get_observation_conn() is deprecated (ADR-0369); use 'with get_observation_db_session() as conn:' instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    _OBSERVATION_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(_OBSERVATION_DB_PATH), timeout=20.0)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA busy_timeout=20000;")
    except Exception:
        pass
    _init_observation_db(conn, _OBSERVATION_DB_PATH)
    return conn


_INITIALIZED_DBS = set()


def _init_observation_db(conn: sqlite3.Connection, db_path: Path):
    """Crée les tables si elles n'existent pas (exécuté une seule fois par base)."""
    canon = str(db_path)
    if canon in _INITIALIZED_DBS:
        return
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS observations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_name TEXT NOT NULL,
            type TEXT NOT NULL CHECK(type IN ('decision', 'bugfix', 'feature', 'discovery')),
            file_scope TEXT,
            timestamp TEXT NOT NULL,
            content TEXT NOT NULL
        )
    """)
    # Table FTS5 : le contenu est stocké dans le FTS5 et on référence l'id
    # de la table observations via observation_id (UNINDEXED = stocké sans indexation full-text)
    cursor.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS observations_fts USING fts5(
            observation_id UNINDEXED,
            project_name UNINDEXED,
            type UNINDEXED,
            content
        )
    """)
    # Table pour le RHO (Chaos Testing / Auto-Healing sémantique)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rho_memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_name TEXT NOT NULL,
            keyword TEXT NOT NULL,
            error_trace TEXT NOT NULL,
            solution TEXT NOT NULL,
            embedding_json TEXT
        )
    """)
    # Table Lexique Métier Dynamique par Projet (ADR-0327)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS project_lexicon (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_name TEXT NOT NULL,
            term TEXT NOT NULL,
            aliases_json TEXT,
            category TEXT,
            definition TEXT,
            target_type TEXT,
            target_id TEXT,
            source_file TEXT,
            last_updated TEXT NOT NULL,
            UNIQUE(project_name, term)
        )
    """)
    cursor.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS project_lexicon_fts USING fts5(
            lexicon_id UNINDEXED,
            project_name UNINDEXED,
            term,
            aliases,
            category UNINDEXED,
            definition,
            target_id
        )
    """)
    # Table Chunks Documentaires SSOT & Fact-Search 2.0 (ADR-0326)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS docs_chunks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_name TEXT NOT NULL,
            doc_path TEXT NOT NULL,
            ssot_layer TEXT NOT NULL,
            section_h1 TEXT,
            section_h2 TEXT,
            breadcrumb TEXT,
            line_start INTEGER,
            line_end INTEGER,
            content TEXT NOT NULL,
            last_updated TEXT NOT NULL,
            UNIQUE(project_name, doc_path, line_start, line_end)
        )
    """)
    cursor.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS docs_chunks_fts USING fts5(
            chunk_id UNINDEXED,
            project_name UNINDEXED,
            ssot_layer UNINDEXED,
            doc_path UNINDEXED,
            breadcrumb,
            section_h1,
            section_h2,
            content
        )
    """)
    conn.commit()


def add_observation(
    project_name: str,
    obs_type: str,
    content: str,
    file_scope: Optional[str] = None,
) -> int:
    """Ajoute une observation et la synchronise dans l'index FTS5.
    Retourne l'ID de la nouvelle observation."""
    from datetime import datetime

    now_iso = datetime.now().isoformat()
    with get_observation_db_session() as conn:
        cursor = conn.cursor()

        # 1. Insert into observations table
        cursor.execute(
            """
            INSERT INTO observations (project_name, type, file_scope, timestamp, content)
            VALUES (?, ?, ?, ?, ?)
        """,
            (project_name, obs_type, file_scope, now_iso, content),
        )
        obs_id = cursor.lastrowid

        # 2. Insert into FTS5 table
        cursor.execute(
            """
            INSERT INTO observations_fts (observation_id, project_name, type, content)
            VALUES (?, ?, ?, ?)
        """,
            (str(obs_id), project_name, obs_type, content),
        )

        return obs_id


def search_observations(
    query: str,
    project_name: Optional[str] = None,
    obs_type: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Recherche plein texte dans les observations via FTS5."""
    with get_observation_db_session() as conn:
        cursor = conn.cursor()

        conditions: List[str] = []

        # Nettoyer la requête pour FTS5 (enlever les opérateurs spéciaux risquant des syntax errors)
        cleaned_query = "".join(c if c.isalnum() or c.isspace() else " " for c in query).strip()
        if not cleaned_query:
            cleaned_query = "*"

        params: List[Any] = [cleaned_query]

        if project_name:
            conditions.append("fts.project_name = ?")
            params.append(project_name)
        if obs_type:
            conditions.append("fts.type = ?")
            params.append(obs_type)

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        try:
            # On joint les 2 tables via observation_id pour récupérer file_scope et timestamp
            cursor.execute(
                f"""
                SELECT o.id, o.project_name, o.type, o.file_scope, o.timestamp, o.content
                FROM observations_fts fts
                JOIN observations o ON o.id = CAST(fts.observation_id AS INTEGER)
                WHERE observations_fts MATCH ? AND {where_clause}
                ORDER BY rank
                LIMIT 20
            """,
                params,
            )
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.OperationalError:
            # Fallback si MATCH échoue quand même : recherche simple par LIKE
            like_clause = f"%{query}%"
            params_fallback = [like_clause]
            conditions_fallback = []
            if project_name:
                conditions_fallback.append("o.project_name = ?")
                params_fallback.append(project_name)
            if obs_type:
                conditions_fallback.append("o.type = ?")
                params_fallback.append(obs_type)
            where_clause_fallback = (
                " AND ".join(conditions_fallback) if conditions_fallback else "1=1"
            )

            cursor.execute(
                f"""
                SELECT o.id, o.project_name, o.type, o.file_scope, o.timestamp, o.content
                FROM observations o
                WHERE o.content LIKE ? AND {where_clause_fallback}
                ORDER BY o.timestamp DESC
                LIMIT 20
            """,
                params_fallback,
            )
            return [dict(row) for row in cursor.fetchall()]


def get_session_timeline(project_name: str) -> List[Dict[str, Any]]:
    """Timeline chronologique (desc) de toutes les observations d'un projet."""
    with get_observation_db_session() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, project_name, type, file_scope, timestamp, content
            FROM observations
            WHERE project_name = ?
            ORDER BY timestamp DESC
            LIMIT 50
        """,
            (project_name,),
        )
        return [dict(row) for row in cursor.fetchall()]


def get_observation_by_id(obs_id: int) -> Optional[Dict[str, Any]]:
    """Récupère le détail complet d'une observation par son ID."""
    with get_observation_db_session() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, project_name, type, file_scope, timestamp, content
            FROM observations
            WHERE id = ?
        """,
            (obs_id,),
        )
        row = cursor.fetchone()
        return dict(row) if row else None


# ═══════════════════════════════════════════════════════════
# RHO Memory - Chaos Testing & Semantic RAG
# ═══════════════════════════════════════════════════════════


def add_rho_rule(project_name: str, keyword: str, error_trace: str, solution: str) -> int:
    """Ajoute une règle RHO avec son embedding Ollama pour recherche sémantique."""
    from src.loop_mem.ollama_embed import get_embedding

    # On embedde la trace d'erreur pour pouvoir la retrouver quand un bug similaire se produit
    embed_vector = get_embedding(error_trace)
    embed_json = json.dumps(embed_vector) if embed_vector else "[]"

    with get_observation_db_session() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO rho_memory (project_name, keyword, error_trace, solution, embedding_json)
            VALUES (?, ?, ?, ?, ?)
        """,
            (project_name, keyword, error_trace, solution, embed_json),
        )
        return cursor.lastrowid


def search_rho_solution(error_trace: str, threshold: float = 0.70) -> List[Dict[str, Any]]:
    """Cherche la solution la plus similaire dans la mémoire RHO via similarité cosinus locale."""
    from src.loop_mem.ollama_embed import get_embedding, cosine_similarity

    query_embed = get_embedding(error_trace)
    if not query_embed:
        return []

    results = []
    with get_observation_db_session() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, project_name, keyword, error_trace, solution, embedding_json FROM rho_memory"
        )
        for row in cursor.fetchall():
            try:
                db_embed = json.loads(row["embedding_json"])
                if db_embed:
                    score = cosine_similarity(query_embed, db_embed)
                    if score >= threshold:
                        results.append(
                            {
                                "id": row["id"],
                                "project_name": row["project_name"],
                                "keyword": row["keyword"],
                                "error_trace": row["error_trace"],
                                "solution": row["solution"],
                                "score": score,
                            }
                        )
            except Exception:
                logger.debug(
                    "Ligne RHO ignorée (embedding illisible ou incompatible)",
                    exc_info=True,
                    extra={"rho_id": row["id"], "project": row["project_name"]},
                )

    # Tri par score décroissant
    results.sort(key=lambda x: x["score"], reverse=True)
    return results


# ═══════════════════════════════════════════════════════════
# Lexique Métier & Base Sémantique Dynamique (ADR-0327)
# ═══════════════════════════════════════════════════════════


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


def search_lexicon_terms(
    query: str,
    project_name: Optional[str] = None,
    limit: int = 10,
) -> List[Dict[str, Any]]:
    """Recherche plein texte dans le lexique métier via FTS5."""
    with get_observation_db_session() as conn:
        cursor = conn.cursor()

        # Nettoyage de la requête pour syntaxe FTS5 (remplacer ponctuation par des espaces)
        clean_q = "".join(c if c.isalnum() else " " for c in query).strip()
        if not clean_q:
            return []

        words = clean_q.split()
        fts_query = " ".join(f"{w}*" for w in words)

        if project_name:
            cursor.execute(
                """
                SELECT l.id, l.project_name, l.term, l.aliases_json, l.category,
                       l.definition, l.target_type, l.target_id, l.source_file,
                       bm25(project_lexicon_fts) as rank
                FROM project_lexicon_fts f
                JOIN project_lexicon l ON l.id = CAST(f.lexicon_id AS INTEGER)
                WHERE project_lexicon_fts MATCH ? AND f.project_name = ?
                ORDER BY rank ASC LIMIT ?
            """,
                (fts_query, project_name, limit),
            )
        else:
            cursor.execute(
                """
                SELECT l.id, l.project_name, l.term, l.aliases_json, l.category,
                       l.definition, l.target_type, l.target_id, l.source_file,
                       bm25(project_lexicon_fts) as rank
                FROM project_lexicon_fts f
                JOIN project_lexicon l ON l.id = CAST(f.lexicon_id AS INTEGER)
                WHERE project_lexicon_fts MATCH ?
                ORDER BY rank ASC LIMIT ?
            """,
                (fts_query, limit),
            )

        results = []
        for row in cursor.fetchall():
            results.append(
                {
                    "id": row["id"],
                    "project_name": row["project_name"],
                    "term": row["term"],
                    "aliases": json.loads(row["aliases_json"] or "[]"),
                    "category": row["category"],
                    "definition": row["definition"],
                    "target_type": row["target_type"],
                    "target_id": row["target_id"],
                    "source_file": row["source_file"],
                }
            )
        return results


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
            except Exception:
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
        except Exception:
            pass

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
            except Exception:
                continue

    return count


# ═══════════════════════════════════════════════════════════
# Fact-Search 2.0 — Chunks SSOT, Breadcrumbs & Coverage (ADR-0326)
# ═══════════════════════════════════════════════════════════

LAYER_WEIGHTS = {
    "architecture": 1.2,
    "business_rules": 1.2,
    "context": 1.1,
    "models": 1.0,
    "knowledge": 0.9,
    "ingested": 0.8,
    "reference": 1.0,
    "docs": 0.7,
}


def _determine_ssot_layer(rel_path: str) -> str:
    p = rel_path.replace("\\", "/").lower()
    if "architecture-segment2" in p or "01-architecture" in p or "adr-" in p:
        return "architecture"
    if "analyse-fonctionnelle" in p or "02-business-rules" in p or "rm-" in p:
        return "business_rules"
    if "03-models" in p or "model" in p or "structure-de-données" in p:
        return "models"
    if "reference" in p or ".wiki" in p:
        return "reference"
    if "00-ingested" in p or "ingested" in p:
        return "ingested"
    if "06-knowledge" in p:
        return "knowledge"
    if "context.md" in p:
        return "context"
    return "docs"


# ──────────────────────────────────────────────────────────────────────────────
# 6. MOTEUR FACT-SEARCH 2.0 (Délégation Canonique vers src.engine.fact_search)
# ──────────────────────────────────────────────────────────────────────────────
def index_project_docs_to_fts5(project_name: str, db_path: Optional[Path] = None) -> int:
    """Scanne et indexe les documents d'un projet dans SQLite FTS5 via TriFusionChunker."""
    from src.engine.fact_search import FactSearchIndexer

    project_dir = (
        Path("Projects") / project_name
        if (Path("Projects") / project_name).exists()
        else Path.cwd()
    )
    docs_dir = project_dir / "docs"
    return FactSearchIndexer.index_project_docs(
        project_name=project_name, docs_dir=docs_dir, db_path=db_path
    )


def fact_search_query(
    query: str,
    project_name: Optional[str] = None,
    expand_synonyms: bool = True,
    limit: int = 10,
    log_audit: bool = True,
    db_path: Optional[Path] = None,
) -> List[Dict[str, Any]]:
    """Recherche plein texte déterministe avec expansion, BM25 et extraits KWIC."""
    from src.engine.fact_search import FactSearchRetriever

    return FactSearchRetriever.search(
        query=query,
        project_name=project_name,
        expand_synonyms=expand_synonyms,
        limit=limit,
        log_audit=log_audit,
        db_path=db_path,
    )


def calculate_story_fact_coverage(
    story_path: Path,
    project_name: str,
    db_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """Calcule le score de couverture Fact-Search d'une User Story (ADR-0326)."""
    from src.engine.fact_search import FactSearchCoverageEvaluator

    return FactSearchCoverageEvaluator.evaluate_story_coverage(
        story_path=story_path,
        project_name=project_name,
        db_path=db_path,
    )
