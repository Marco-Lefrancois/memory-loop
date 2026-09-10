#!/usr/bin/env python3
"""
Gestionnaire et Validateur d'EvidencePacks JSON (Universal Dev Handoff)
Fait partie du sous-système Grill-with-Docs.
"""
import sys
import os
import json
import hashlib
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

def calculate_sha256(file_path: Path) -> str:
    if not file_path.exists():
        return ""
    return hashlib.sha256(file_path.read_bytes()).hexdigest()

def log_evidence(
    story_id: str,
    output_path: Path,
    query: str,
    source_file: str,
    start_line: int,
    end_line: int,
    verbatim: str,
    fact: str,
    jira_key: str = None,
    log_file: Path = Path("memory/fact_search_log.jsonl")
) -> Dict[str, Any]:
    output_path = Path(output_path)
    data: Dict[str, Any] = {}
    if output_path.exists():
        try:
            data = json.loads(output_path.read_text(encoding="utf-8"))
        except Exception:
            data = {}
            
    data["story_id"] = story_id
    data["jira_key"] = jira_key or data.get("jira_key", story_id)
    data["timestamp"] = datetime.now().isoformat()
    data["fact_search_status"] = "VERIFIED"
    
    if "fact_search_proofs" not in data:
        data["fact_search_proofs"] = []
        
    proof_entry = {
        "query": query,
        "source_file": source_file,
        "section": f"Lignes {start_line}–{end_line}",
        "matched_fact": f"« {verbatim} » ➔ Fait établi : {fact}",
        "confidence": "HIGH",
        "timestamp": datetime.now().isoformat()
    }
    data["fact_search_proofs"].append(proof_entry)
    
    # Hash source file if exists
    if "source_hashes_sha256" not in data:
        data["source_hashes_sha256"] = {}
    src_p = Path(source_file)
    if src_p.exists():
        data["source_hashes_sha256"][source_file] = calculate_sha256(src_p)
        
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    
    # Append to cumulative audit log
    try:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        with open(log_file, "a", encoding="utf-8") as f:
            log_record = {
                "timestamp": datetime.now().isoformat(),
                "story_id": story_id,
                "query": query,
                "source_file": source_file,
                "section": f"Lignes {start_line}–{end_line}",
                "confidence": "HIGH"
            }
            f.write(json.dumps(log_record, ensure_ascii=False) + "\n")
    except Exception:
        pass
        
    return data

def validate_evidence_file(file_path: Path) -> bool:
    try:
        data = json.loads(file_path.read_text(encoding="utf-8"))
        required_keys = ["story_id", "jira_key", "timestamp", "fact_search_status", "fact_search_proofs"]
        for k in required_keys:
            if k not in data:
                print(f"❌ {file_path.name} : Clé obligatoire manquante '{k}'")
                return False
        return True
    except Exception as e:
        print(f"❌ {file_path.name} : JSON invalide ({e})")
        return False

def validate_all(evidence_dir: Path) -> bool:
    p = Path(evidence_dir)
    if not p.exists():
        print(f"Dossier introuvable : {evidence_dir}")
        return False
    files = list(p.glob("*.json"))
    print(f"Audit de conformité sur {len(files)} EvidencePacks...")
    all_valid = True
    for f in files:
        valid = validate_evidence_file(f)
        if valid:
            print(f"  ✅ {f.name} — Conforme")
        else:
            all_valid = False
    return all_valid

def main():
    parser = argparse.ArgumentParser(description="EvidencePack Logger & Validator")
    subparsers = parser.add_subparsers(dest="command")
    
    p_log = subparsers.add_parser("log", help="Consigne une preuve Fact-Search dans un EvidencePack")
    p_log.add_argument("--story-id", required=True, help="ID interne de la story (ex: INC-001-BE)")
    p_log.add_argument("--jira-key", help="Clé Jira officielle (ex: COUVBOIRE-1044)")
    p_log.add_argument("--output", required=True, help="Chemin du fichier JSON de sortie")
    p_log.add_argument("--query", default="", help="Requête de recherche initiale")
    p_log.add_argument("--source-file", required=True, help="Fichier physique source")
    p_log.add_argument("--start-line", type=int, default=1, help="Ligne de début")
    p_log.add_argument("--end-line", type=int, default=1, help="Ligne de fin")
    p_log.add_argument("--verbatim", required=True, help="Citation exacte du document")
    p_log.add_argument("--fact", required=True, help="Traduction fonctionnelle du fait établi")
    
    p_val = subparsers.add_parser("validate-all", help="Valide tous les EvidencePacks d'un dossier")
    p_val.add_argument("--evidence-dir", default="memory/evidence", help="Dossier contenant les fichiers JSON")
    
    args = parser.parse_args()
    if args.command == "log":
        log_evidence(
            story_id=args.story_id,
            output_path=Path(args.output),
            query=args.query,
            source_file=args.source_file,
            start_line=args.start_line,
            end_line=args.end_line,
            verbatim=args.verbatim,
            fact=args.fact,
            jira_key=args.jira_key
        )
        print(f"✅ Preuve enregistrée sous {args.output}")
    elif args.command == "validate-all":
        ok = validate_all(Path(args.evidence_dir))
        sys.exit(0 if ok else 1)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
