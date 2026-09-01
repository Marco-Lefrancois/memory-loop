# -*- coding: utf-8 -*-
"""
Fact-Search Indexer Engine (mLoop Core - ADR-0326).

Indexe les documents Markdown de l'architecture SSOT dans SQLite et FTS5
avec préfixes contextuels Anthropic et métadonnées de lignage exactes.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Optional, List, Dict, Any

from src.engine.fact_search.chunker import TriFusionChunker, TriFusionChunk
from src.loop_mem.db import get_observation_db_session
from src.utils.logger import get_logger

logger = get_logger("fact_search.indexer")


class FactSearchIndexer:
    """Moteur d'indexation documentaire pour Fact-Search 2.0."""

    @classmethod
    def index_project_docs(
        cls,
        project_name: str,
        docs_dir: Optional[Path] = None,
        db_path: Optional[Path] = None,
    ) -> int:
        """
        Scanne tous les documents Markdown sous docs/ et standards/
        pour les découper via TriFusionChunker et les indexer dans SQLite et FTS5.
        """
        if docs_dir is None:
            docs_dir = Path("Projects") / project_name / "docs"

        if not docs_dir.exists():
            logger.debug(f"Dossier docs introuvable pour {project_name}: {docs_dir}")
            return 0

        chunker = TriFusionChunker()
        all_chunks: List[TriFusionChunk] = []

        # Scanner les sous-dossiers SSOT
        layer_dirs = [
            ("01-architecture", "01-architecture"),
            ("02-business-rules", "02-business-rules"),
            ("03-models", "03-models"),
            ("00-ingested", "00-ingested"),
            ("05-assets", "05-assets"),
            ("06-knowledge", "06-knowledge"),
        ]

        for folder_name, layer_key in layer_dirs:
            folder_path = docs_dir / folder_name
            if folder_path.exists():
                for md_file in folder_path.rglob("*.md"):
                    try:
                        content = md_file.read_text(encoding="utf-8", errors="ignore")
                        rel_path = md_file.relative_to(docs_dir.parent).as_posix()
                        chunks = chunker.chunk_document(
                            doc_path=rel_path,
                            content=content,
                            ssot_layer=layer_key,
                        )
                        all_chunks.extend(chunks)
                    except Exception as e:
                        logger.warning(f"Erreur lecture {md_file}: {e}")

        # Scanner également les fichiers Markdown racine sous docs/
        for md_file in docs_dir.glob("*.md"):
            try:
                content = md_file.read_text(encoding="utf-8", errors="ignore")
                rel_path = md_file.relative_to(docs_dir.parent).as_posix()
                chunks = chunker.chunk_document(
                    doc_path=rel_path,
                    content=content,
                    ssot_layer="01-architecture",
                )
                all_chunks.extend(chunks)
            except Exception as e:
                logger.warning(f"Erreur lecture racine {md_file}: {e}")

        if not all_chunks:
            return 0

        # Insertion transactionnelle dans docs_chunks et docs_chunks_fts
        session_kwargs = {"db_path": db_path} if db_path else {}
        with get_observation_db_session(**session_kwargs) as conn:
            cursor = conn.cursor()
            from datetime import datetime

            now_iso = datetime.now().isoformat()

            indexed_count = 0
            for chunk in all_chunks:
                # 1. Table relationnelle
                cursor.execute(
                    """
                    INSERT INTO docs_chunks (
                        project_name, doc_path, ssot_layer, section_h1, section_h2,
                        breadcrumb, line_start, line_end, content, last_updated
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(project_name, doc_path, line_start, line_end) DO UPDATE SET
                        content=excluded.content,
                        breadcrumb=excluded.breadcrumb,
                        section_h1=excluded.section_h1,
                        section_h2=excluded.section_h2,
                        last_updated=excluded.last_updated
                """,
                    (
                        project_name,
                        chunk.doc_path,
                        chunk.ssot_layer,
                        chunk.section_h1,
                        chunk.section_h2,
                        chunk.breadcrumb,
                        chunk.line_start,
                        chunk.line_end,
                        chunk.content,
                        now_iso,
                    ),
                )

                cursor.execute(
                    "SELECT id FROM docs_chunks WHERE project_name=? AND doc_path=? AND line_start=? AND line_end=?",
                    (
                        project_name,
                        chunk.doc_path,
                        chunk.line_start,
                        chunk.line_end,
                    ),
                )
                row = cursor.fetchone()
                chunk_id = row[0] if row else cursor.lastrowid

                # 2. Table FTS5 avec préfixe contextuel Anthropic (perf : rowid explicite = chunk_id
                # pour éviter un scan complet de la table virtuelle sur la colonne UNINDEXED
                # "chunk_id" — DELETE WHERE col=? sur une colonne UNINDEXED force un full scan O(n)
                # par appel, soit O(n^2) sur toute la boucle d'ingestion des chunks documentaires.
                # Le rowid FTS5 est lui nativement indexé -> O(log n) par appel.
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO docs_chunks_fts (
                        rowid, chunk_id, project_name, ssot_layer, doc_path, breadcrumb, section_h1, section_h2, content
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        chunk_id,
                        str(chunk_id),
                        project_name,
                        chunk.ssot_layer,
                        chunk.doc_path,
                        chunk.breadcrumb,
                        chunk.section_h1,
                        chunk.section_h2,
                        chunk.contextual_content,
                    ),
                )
                indexed_count += 1

        logger.info(
            f"[{project_name}] Indexation Tri-Fusion terminée : {indexed_count} chunks indexés."
        )
        return indexed_count
