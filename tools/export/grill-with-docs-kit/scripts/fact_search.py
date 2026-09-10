#!/usr/bin/env python3
"""
Moteur Autonome Fact-Search & Evidence Logger (SQLite FTS5 + Passage Grounding)
Fait partie du Kit Grill-with-Docs mLoop.
Sans dépendance externe (Standard Library Python uniquement).
"""
import sys
import os
import re
import json
import sqlite3
import hashlib
import argparse
from pathlib import Path
from datetime import datetime

DB_FILE = Path(".fact_search_index.db")

def init_db(db_path: Path):
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

def chunk_markdown_file(file_path: Path):
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
        
        # Split chunks larger than 60 lines
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

def cmd_index(docs_dir: str):
    p = Path(docs_dir)
    if not p.exists():
        print(f"❌ Dossier introuvable : {docs_dir}")
        sys.exit(1)
        
    print(f"🔄 Indexation des documents sous '{docs_dir}'...")
    conn = init_db(DB_FILE)
    cur = conn.cursor()
    cur.execute("DELETE FROM document_passages;")
    
    indexed_files = 0
    total_passages = 0
    
    extensions = ("*.md", "*.markdown", "*.txt", "*.json", "*.dbml")
    files = []
    for ext in extensions:
        files.extend(p.rglob(ext))
        
    for f in set(files):
        passages = chunk_markdown_file(f)
        for pas in passages:
            cur.execute("""
                INSERT INTO document_passages (file_path, passage_title, content, start_line, end_line, sha256)
                VALUES (?, ?, ?, ?, ?, ?);
            """, (pas["file_path"], pas["passage_title"], pas["content"], pas["start_line"], pas["end_line"], pas["sha256"]))
            total_passages += 1
        indexed_files += 1
        
    conn.commit()
    conn.close()
    print(f"✅ Indexation terminée : {indexed_files} fichiers analysés, {total_passages} passages indexés sous {DB_FILE}")

def cmd_search(query: str, limit: int = 5):
    if not DB_FILE.exists():
        print("❌ L'index FTS5 n'existe pas. Exécutez d'abord 'fact_search.py index --docs-dir <chemin>'.")
        sys.exit(1)
        
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    
    # Nettoyer et formater la requête FTS5
    words = re.findall(r'\w+', query, re.UNICODE)
    if not words:
        print("Requête vide.")
        return
    fts_query = " OR ".join(f'"{w}"' for w in words)
    
    try:
        cur.execute(f"""
            SELECT file_path, passage_title, snippet(document_passages, 2, '>>>', '<<<', '...', 30), start_line, end_line, rank, content
            FROM document_passages
            WHERE document_passages MATCH ?
            ORDER BY rank
            LIMIT ?;
        """, (fts_query, limit))
        rows = cur.fetchall()
    except Exception as e:
        print(f"Erreur SQL FTS5: {e}")
        rows = []
        
    conn.close()
    
    print(f"\n🔍 Résultats Fact-Search pour : \"{query}\" ({len(rows)} trouvés)\n" + "="*80)
    for i, (fpath, title, snip, s_line, e_line, rank, raw_content) in enumerate(rows, 1):
        print(f"[{i}] 📄 {fpath} (Lignes {s_line}–{e_line}) — Section: {title}")
        print(f"    Extrait : {snip}")
        print("-" * 80)

def cmd_evidence(story_id: str, output_file: str, query: str, source_file: str, lines: str, verbatim: str, fact: str):
    out_path = Path(output_file)
    data = {}
    if out_path.exists():
        try:
            data = json.loads(out_path.read_text(encoding="utf-8"))
        except Exception:
            data = {}
            
    data["story_id"] = story_id
    data["jira_key"] = data.get("jira_key", story_id)
    data["last_updated"] = datetime.now().isoformat()
    data["fact_search_status"] = "VERIFIED"
    
    if "fact_search_proofs" not in data:
        data["fact_search_proofs"] = []
        
    data["fact_search_proofs"].append({
        "query": query,
        "source_file": source_file,
        "section": lines,
        "matched_fact": f"« {verbatim} » ➔ Fait établi : {fact}",
        "confidence": "HIGH",
        "timestamp": datetime.now().isoformat()
    })
    
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"✅ Preuve Fact-Search consignée dans {output_file}")

def main():
    parser = argparse.ArgumentParser(description="Moteur Fact-Search FTS5 & EvidencePack Logger")
    subparsers = parser.add_subparsers(dest="subcommand")
    
    p_index = subparsers.add_parser("index", help="Indexe un répertoire de documentation")
    p_index.add_argument("--docs-dir", required=True, help="Dossier contenant les fichiers markdown/textes")
    
    p_search = subparsers.add_parser("search", help="Recherche plein-texte dans l'index")
    p_search.add_argument("query", help="Requête factuelle à chercher")
    p_search.add_argument("--limit", type=int, default=5, help="Nombre max de résultats")
    
    p_ev = subparsers.add_parser("evidence", help="Ajoute une preuve dans un EvidencePack JSON")
    p_ev.add_argument("--story-id", required=True, help="ID du récit (ex: INC-001-BE)")
    p_ev.add_argument("--output", required=True, help="Chemin du fichier evidence.json")
    p_ev.add_argument("--query", required=True, help="Requête de recherche initiale")
    p_ev.add_argument("--source", required=True, help="Fichier physique source")
    p_ev.add_argument("--lines", required=True, help="Plage de lignes (ex: Lignes 313-337)")
    p_ev.add_argument("--verbatim", required=True, help="Citation exacte du document")
    p_ev.add_argument("--fact", required=True, help="Fait établi traduit")
    
    args = parser.parse_args()
    if args.subcommand == "index":
        cmd_index(args.docs_dir)
    elif args.subcommand == "search":
        cmd_search(args.query, args.limit)
    elif args.subcommand == "evidence":
        cmd_evidence(args.story_id, args.output, args.query, args.source, args.lines, args.verbatim, args.fact)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
