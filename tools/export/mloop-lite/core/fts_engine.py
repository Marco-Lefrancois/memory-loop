#!/usr/bin/env python3
"""
Moteur Autonome Fact-Search (SQLite FTS5 + Passage-Level Grounding)
Fait partie du sous-système Grill-with-Docs.
Conçu pour exécution CLI ou invocation programmatique par Agent IA.
"""
import sys
import os
import re
import json
import sqlite3
import hashlib
import argparse
from pathlib import Path
from typing import List, Dict, Any

DEFAULT_DB_PATH = Path(".fact_search_index.db")

def init_database(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS document_passages USING fts5(
            file_path UNINDEXED,
            passage_title,
            content,
            start_line UNINDEXED,
            end_line UNINDEXED,
            sha256 UNINDEXED,
            tokenize = 'unicode61'
        );
    """)
    conn.commit()
    return conn

def chunk_file(file_path: Path) -> List[Dict[str, Any]]:
    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return []
    
    file_sha256 = hashlib.sha256(content.encode("utf-8")).hexdigest()
    lines = content.splitlines()
    passages = []
    
    current_title = file_path.stem
    current_chunk = []
    chunk_start_line = 1
    
    for i, line in enumerate(lines, 1):
        if line.startswith(("# ", "## ", "### ", "#### ")):
            if current_chunk:
                passages.append({
                    "file_path": str(file_path).replace("\\", "/"),
                    "passage_title": current_title,
                    "content": "\n".join(current_chunk),
                    "start_line": chunk_start_line,
                    "end_line": i - 1,
                    "sha256": file_sha256
                })
                current_chunk = []
            current_title = line.strip("# ").strip()
            chunk_start_line = i
        current_chunk.append(line)
        
        if len(current_chunk) >= 60:
            passages.append({
                "file_path": str(file_path).replace("\\", "/"),
                "passage_title": current_title,
                "content": "\n".join(current_chunk),
                "start_line": chunk_start_line,
                "end_line": i,
                "sha256": file_sha256
            })
            current_chunk = []
            chunk_start_line = i + 1
            
    if current_chunk:
        passages.append({
            "file_path": str(file_path).replace("\\", "/"),
            "passage_title": current_title,
            "content": "\n".join(current_chunk),
            "start_line": chunk_start_line,
            "end_line": len(lines),
            "sha256": file_sha256
        })
    return passages

def index_directory(docs_dir: str, db_path: Path = DEFAULT_DB_PATH) -> Dict[str, int]:
    p = Path(docs_dir)
    if not p.exists():
        raise FileNotFoundError(f"Dossier introuvable : {docs_dir}")
        
    conn = init_database(db_path)
    cur = conn.cursor()
    cur.execute("DELETE FROM document_passages;")
    
    indexed_files = 0
    total_passages = 0
    extensions = ("*.md", "*.markdown", "*.txt", "*.json", "*.dbml")
    
    files = set()
    for ext in extensions:
        files.update(p.rglob(ext))
        
    for f in files:
        if any(part.startswith(".") for part in f.parts):
            continue
        passages = chunk_file(f)
        for pas in passages:
            cur.execute("""
                INSERT INTO document_passages (file_path, passage_title, content, start_line, end_line, sha256)
                VALUES (?, ?, ?, ?, ?, ?);
            """, (pas["file_path"], pas["passage_title"], pas["content"], pas["start_line"], pas["end_line"], pas["sha256"]))
            total_passages += 1
        indexed_files += 1
        
    conn.commit()
    conn.close()
    return {"indexed_files": indexed_files, "total_passages": total_passages}

def search_passages(query: str, limit: int = 5, db_path: Path = DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    if not db_path.exists():
        raise FileNotFoundError(f"Index inexistant : {db_path}. Exécutez 'index' au préalable.")
        
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    words = re.findall(r'\w+', query, re.UNICODE)
    if not words:
        return []
    fts_query = " OR ".join(f'"{w}"' for w in words)
    
    try:
        cur.execute("""
            SELECT file_path, passage_title, snippet(document_passages, 2, '>>>', '<<<', '...', 30), start_line, end_line, rank, sha256, content
            FROM document_passages
            WHERE document_passages MATCH ?
            ORDER BY rank
            LIMIT ?;
        """, (fts_query, limit))
        rows = cur.fetchall()
    except Exception as e:
        conn.close()
        raise RuntimeError(f"Erreur SQL FTS5: {e}")
        
    conn.close()
    
    results = []
    for fpath, title, snip, s_line, e_line, rank, sha, raw_content in rows:
        results.append({
            "file_path": fpath,
            "section": title,
            "snippet": snip,
            "start_line": s_line,
            "end_line": e_line,
            "score": round(abs(rank), 2),
            "sha256": sha,
            "raw_content": raw_content
        })
    return results

def main():
    parser = argparse.ArgumentParser(description="Moteur Fact-Search SQLite FTS5")
    subparsers = parser.add_subparsers(dest="command")
    
    p_index = subparsers.add_parser("index", help="Indexe un dossier de documentation")
    p_index.add_argument("--docs-dir", required=True, help="Chemin du dossier docs")
    p_index.add_argument("--db", default=str(DEFAULT_DB_PATH), help="Chemin de la base de données FTS5")
    
    p_search = subparsers.add_parser("search", help="Recherche plein-texte")
    p_search.add_argument("query", help="Termes de recherche")
    p_search.add_argument("--limit", type=int, default=5, help="Nombre maximal de résultats")
    p_search.add_argument("--json", action="store_true", help="Sortie au format JSON")
    p_search.add_argument("--db", default=str(DEFAULT_DB_PATH), help="Chemin de la base de données FTS5")
    
    args = parser.parse_args()
    if args.command == "index":
        stats = index_directory(args.docs_dir, Path(args.db))
        print(f"✅ Indexation réussie : {stats['indexed_files']} fichiers, {stats['total_passages']} passages indexés.")
    elif args.command == "search":
        results = search_passages(args.query, args.limit, Path(args.db))
        if args.json:
            print(json.dumps(results, indent=2, ensure_ascii=False))
        else:
            print(f"\n🔍 Résultats ({len(results)}) pour : \"{args.query}\"\n" + "="*80)
            for i, r in enumerate(results, 1):
                print(f"[{i}] 📄 {r['file_path']} (Lignes {r['start_line']}–{r['end_line']}) — Section: {r['section']}")
                print(f"    Extrait : {r['snippet']}")
                print("-" * 80)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
