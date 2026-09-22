# -*- coding: utf-8 -*-
"""
Fact-Search Indexer Engine (mLoop Core - ADR-0326).

Indexe les documents Markdown de l'architecture SSOT dans SQLite et FTS5
avec préfixes contextuels Anthropic et métadonnées de lignage exactes.
"""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from pathlib import Path
from typing import Optional, List, Dict, Any

from src.engine.fact_search.chunker import TriFusionChunker, TriFusionChunk
from src.loop_mem.db import get_observation_db_session
from src.utils.logger import get_logger

logger = get_logger("fact_search.indexer")


class FactSearchIndexer:
    """Moteur d'indexation documentaire incrémentale pour Fact-Search 2.0."""

    @classmethod
    def _get_hash_cache_path(
        cls, project_name: str, docs_dir: Path, db_path: Optional[Path] = None
    ) -> Path:
        """Détermine le chemin du fichier cache MD5 au niveau projet."""
        if db_path:
            return Path(db_path).parent / f".fact_search_hashes_{project_name}.json"
        project_dir = Path("Projects") / project_name
        if project_dir.exists():
            return project_dir / "memory" / ".fact_search_hashes.json"
        if docs_dir and docs_dir.parent.exists() and docs_dir.parent.name != "Projects":
            return docs_dir.parent / "memory" / ".fact_search_hashes.json"
        return Path("memory") / f".fact_search_hashes_{project_name}.json"

    @classmethod
    def _load_hashes(cls, cache_path: Path) -> Dict[str, str]:
        """Charge le dictionnaire des hachages existants."""
        if cache_path.exists():
            try:
                return json.loads(cache_path.read_text(encoding="utf-8"))
            except Exception as e:
                logger.debug(
                    "Cache de hachage MD5 illisible ou corrompu, réindexation complète",
                    exc_info=True,
                    extra={
                        "component": "fact_search.indexer",
                        "operation": "_load_hashes",
                        "cache_path": str(cache_path),
                        "error": str(e),
                    },
                )
                return {}
        return {}

    @classmethod
    def _read_file_safe(cls, file_path: Path) -> str:
        """Lit un fichier texte UTF-8 avec contournement transparent de la limite Windows MAX_PATH (260 caractères)."""
        try:
            return file_path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            if os.name == "nt":
                resolved = file_path.resolve()
                p_str = str(resolved)
                if not p_str.startswith("\\\\?\\"):
                    p_str = "\\\\?\\" + p_str
                return Path(p_str).read_text(encoding="utf-8", errors="ignore")
            raise

    @classmethod
    def _save_hashes(cls, cache_path: Path, hashes: Dict[str, str]) -> None:
        """Sauvegarde atomiquement le cache de hachages."""
        try:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            tmp_path = cache_path.with_suffix(".tmp")
            tmp_path.write_text(json.dumps(hashes, indent=2, ensure_ascii=False), encoding="utf-8")
            tmp_path.replace(cache_path)
        except Exception as e:
            logger.warning(f"Impossible de sauvegarder le cache MD5 {cache_path}: {e}")

    @classmethod
    def _compute_content_hash(cls, content: str) -> str:
        """Calcule le hachage MD5 du contenu textuel normalisé."""
        return hashlib.md5(content.encode("utf-8")).hexdigest()

    @classmethod
    def index_project_docs(
        cls,
        project_name: str,
        docs_dir: Optional[Path] = None,
        db_path: Optional[Path] = None,
        force: bool = False,
    ) -> int:
        """
        Scanne tous les documents Markdown sous docs/ et standards/
        pour les découper via TriFusionChunker et les indexer dans SQLite et FTS5.
        Utilise un cache de hachage MD5 persistant pour ne re-traiter que les fichiers modifiés.
        """
        if docs_dir is None:
            docs_dir = Path("Projects") / project_name / "docs"

        if not docs_dir.exists():
            logger.debug(f"Dossier docs introuvable pour {project_name}: {docs_dir}")
            return 0

        cache_path = cls._get_hash_cache_path(project_name, docs_dir, db_path)
        cached_hashes = {} if force else cls._load_hashes(cache_path)
        current_hashes: Dict[str, str] = {}

        # 1. Collecter tous les fichiers éligibles avec leur contenu et couche SSOT
        layer_dirs = [
            ("01-architecture", "01-architecture"),
            ("02-business-rules", "02-business-rules"),
            ("03-models", "03-models"),
            ("00-ingested", "00-ingested"),
            ("04-transverse", "06-knowledge"),
            ("05-assets", "05-assets"),
            ("06-knowledge", "06-knowledge"),
        ]

        raw_files: List[tuple[Path, str, str, str]] = []  # (md_file, rel_path, layer_key, content)

        for folder_name, layer_key in layer_dirs:
            folder_path = docs_dir / folder_name
            if folder_path.exists():
                for md_file in folder_path.rglob("*.md"):
                    try:
                        content = cls._read_file_safe(md_file)
                        rel_path = md_file.relative_to(docs_dir.parent).as_posix()
                        raw_files.append((md_file, rel_path, layer_key, content))
                    except Exception as e:
                        logger.warning(f"Erreur lecture {md_file}: {e}")

        # Fichiers Markdown racine sous docs/
        for md_file in docs_dir.glob("*.md"):
            try:
                content = cls._read_file_safe(md_file)
                rel_path = md_file.relative_to(docs_dir.parent).as_posix()
                raw_files.append((md_file, rel_path, "01-architecture", content))
            except Exception as e:
                logger.warning(f"Erreur lecture racine {md_file}: {e}")

        # Dossier reference/ du projet si présent
        ref_dir = docs_dir.parent / "reference"
        if ref_dir.exists():
            for md_file in ref_dir.rglob("*.md"):
                try:
                    content = cls._read_file_safe(md_file)
                    rel_path = md_file.relative_to(docs_dir.parent).as_posix()
                    raw_files.append((md_file, rel_path, "06-knowledge", content))
                except Exception as e:
                    logger.warning(f"Erreur lecture reference {md_file}: {e}")

        # Standards globaux si mLoop ou global
        if project_name.lower() in ("mloop", "global"):
            standards_dir = Path("standards")
            if standards_dir.exists():
                for md_file in standards_dir.rglob("*.md"):
                    try:
                        content = cls._read_file_safe(md_file)
                        rel_path = md_file.as_posix()
                        layer_val = (
                            "01-architecture" if "adr" in rel_path.lower() else "02-business-rules"
                        )
                        raw_files.append((md_file, rel_path, layer_val, content))
                    except Exception as e:
                        logger.warning(f"Erreur lecture standard {md_file}: {e}")

        # 2. Filtrer les fichiers modifiés et identifier les fichiers supprimés
        files_to_index = []
        for md_file, rel_path, layer_key, content in raw_files:
            file_hash = cls._compute_content_hash(content)
            current_hashes[rel_path] = file_hash
            if force or cached_hashes.get(rel_path) != file_hash:
                files_to_index.append((md_file, rel_path, layer_key, content))

        deleted_paths = [p for p in cached_hashes if p not in current_hashes]

        if not files_to_index and not deleted_paths:
            logger.debug(
                f"[{project_name}] Indexation Fact-Search à jour (aucun fichier modifié sur {len(current_hashes)} documents)."
            )
            return 0

        # 3. Découper les fichiers modifiés via TriFusionChunker
        chunker = TriFusionChunker()
        chunks_to_insert: List[TriFusionChunk] = []
        for md_file, rel_path, layer_key, content in files_to_index:
            chunks = chunker.chunk_document(
                doc_path=rel_path,
                content=content,
                ssot_layer=layer_key,
            )
            chunks_to_insert.extend(chunks)

        # 4. Opérations transactionnelles dans SQLite et FTS5
        session_kwargs = {"db_path": db_path} if db_path else {}
        with get_observation_db_session(**session_kwargs) as conn:
            cursor = conn.cursor()
            from datetime import datetime

            now_iso = datetime.now().isoformat()

            # A. Purger les chunks des fichiers modifiés ou supprimés
            paths_to_purge = set(deleted_paths) | {rel_path for _, rel_path, _, _ in files_to_index}
            for purge_path in paths_to_purge:
                cursor.execute(
                    "SELECT id FROM docs_chunks WHERE project_name=? AND doc_path=?",
                    (project_name, purge_path),
                )
                old_ids = [r[0] for r in cursor.fetchall()]
                if old_ids:
                    # Purge FTS5 par rowid explicite
                    placeholders = ",".join("?" for _ in old_ids)
                    cursor.execute(
                        f"DELETE FROM docs_chunks_fts WHERE rowid IN ({placeholders})",
                        old_ids,
                    )
                    # Purge table relationnelle
                    cursor.execute(
                        "DELETE FROM docs_chunks WHERE project_name=? AND doc_path=?",
                        (project_name, purge_path),
                    )

            # B. Insérer les nouveaux chunks
            indexed_count = 0
            for chunk in chunks_to_insert:
                cursor.execute(
                    """
                    INSERT INTO docs_chunks (
                        project_name, doc_path, ssot_layer, section_h1, section_h2,
                        breadcrumb, line_start, line_end, content, last_updated
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                chunk_id = cursor.lastrowid

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

        # 5. Sauvegarder le nouveau cache de hachage
        cls._save_hashes(cache_path, current_hashes)

        logger.info(
            f"[{project_name}] Indexation Tri-Fusion terminée : {indexed_count} chunks insérés, "
            f"{len(files_to_index)} fichiers modifiés, {len(deleted_paths)} fichiers purgés."
        )
        return indexed_count
