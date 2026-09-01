import argparse
import yaml
import sys
import os
import re
from pathlib import Path
from typing import Dict, Any, List

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from src.state import LoopState
from src.cli import ZeroFluffConsole

def optimize_rho(project_name: str, keyword: str, msg: str, scope: str = "project"):
    ZeroFluffConsole.section("Retrospective Harness Optimization (RHO)")
    
    # Déterminer le fichier cible
    if scope == "global":
        target_file = Path("standards") / "rho_rules.yaml"
    else:
        target_file = Path("Projects") / project_name / "memory" / "rho_rules.yaml"
        
    if not target_file.parent.exists():
        target_file.parent.mkdir(parents=True, exist_ok=True)
        
    rules_data = {"rules": []}
    if target_file.exists():
        try:
            with open(target_file, "r", encoding="utf-8") as f:
                rules_data = yaml.safe_load(f) or {"rules": []}
                if "rules" not in rules_data:
                    rules_data["rules"] = []
        except Exception as e:
            ZeroFluffConsole.error(f"Erreur de lecture de {target_file}: {e}")
            
    # Vérifier si la règle existe déjà
    for rule in rules_data["rules"]:
        if rule.get("keyword") == keyword.lower():
            ZeroFluffConsole.info(f"La règle RHO pour le mot-clé '{keyword}' existe déjà.")
            return

    # Ajouter la nouvelle règle
    rules_data["rules"].append({
        "keyword": keyword.lower(),
        "msg": f"[RHO] {msg}",
        "status": "ACTIVE"
    })
    
    try:
        with open(target_file, "w", encoding="utf-8") as f:
            yaml.dump(rules_data, f, allow_unicode=True, sort_keys=False)
        ZeroFluffConsole.success(f"Nouvelle règle RHO ajoutée ({scope} scope) dans {target_file.as_posix()}")
        ZeroFluffConsole.info(f"Keyword: '{keyword}' -> Msg: '[RHO] {msg}'")
        
        # --- NOUVEAUTÉ : Enregistrement dans la base RAG Vectorielle (Ollama + SQLite) ---
        try:
            from src.loop_mem.db import add_rho_rule
            add_rho_rule(project_name, keyword, keyword, msg)
            ZeroFluffConsole.success("Règle RHO indexée sémantiquement dans loop_mem.db.")
        except Exception as e:
            ZeroFluffConsole.warning(f"RAG DB offline: {e}")
        
        # [Auto-Journal] Enregistrement d'un événement au dashboard
        from src.state import LoopState, JournalEntry
        p_path = Path("Projects") / project_name
        if p_path.exists():
            state = LoopState(project_name=project_name)
            try:
                state.load_from_audit(p_path)
            except Exception:
                state.load_from_graph(p_path)
            
            entry = JournalEntry(
                event="RHO Optimization [Chaos Testing]",
                details=f"Nouvelle règle ajoutée ({scope} scope) pour le mot-clé '{keyword}'.\nMessage: {msg}",
                impacted_nodes=["rho_rules.yaml"]
            )
            state.journal.append(entry)
            state.save_to_audit(p_path)
            ZeroFluffConsole.success("Événement RHO envoyé au Dashboard.")
            
    except Exception as e:
        ZeroFluffConsole.error(f"Erreur d'écriture de {target_file}: {e}")


def dream_collector(project_name: str) -> Dict[str, Any]:
    """
    RHO Dream & Tombstone Collector (Blindspot #1 & #4 : Upstream & Silent State Poisoning).
    Cross-checks active RHO rules against recent Architecture Decision Records (ADRs).
    Marks deprecated or contradicted rules as TOMBSTONE to prevent stale memory poisoning.
    """
    ZeroFluffConsole.section(f"RHO Dream & Tombstone Collector [{project_name}]")
    
    project_path = Path("Projects") / project_name
    adrs_dir = project_path / "docs" / "01-architecture"
    rho_file = project_path / "memory" / "rho_rules.yaml"
    global_rho_file = Path("standards") / "rho_rules.yaml"
    
    deprecated_count = 0
    checked_rules = 0
    tombstone_reports = []

    # 1. Collecter les textes d'ADRs
    adr_texts = []
    if adrs_dir.exists():
        for adr_path in adrs_dir.glob("ADR-*.md"):
            try:
                text = adr_path.read_text(encoding="utf-8")
                adr_texts.append({"path": adr_path.name, "content": text})
            except Exception:
                pass

    # 2. Auditer les règles du projet et globales
    target_files = [f for f in [rho_file, global_rho_file] if f.exists()]
    
    for fpath in target_files:
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            
            rules = data.get("rules", [])
            modified = False
            
            for rule in rules:
                checked_rules += 1
                kw = rule.get("keyword", "")
                current_status = rule.get("status", "ACTIVE")
                
                if current_status == "TOMBSTONE":
                    continue
                    
                # Vérifier si un ADR supersedes ou déprécie ce mot-clé / concept
                for adr in adr_texts:
                    content_lower = adr["content"].lower()
                    if kw.lower() in content_lower and any(term in content_lower for term in ["obsolète", "déprécié", "superseded", "remplacé par", "tombstone"]):
                        rule["status"] = "TOMBSTONE"
                        rule["tombstone_reason"] = f"Contradicted or superseded by {adr['path']}"
                        deprecated_count += 1
                        modified = True
                        tombstone_reports.append(f"Rule '{kw}' marked TOMBSTONE by {adr['path']}")
                        ZeroFluffConsole.warning(f"Règle RHO '{kw}' dépréciée (TOMBSTONE) suite à {adr['path']}")
                        break
            
            if modified:
                with open(fpath, "w", encoding="utf-8") as f:
                    yaml.dump(data, f, allow_unicode=True, sort_keys=False)
                ZeroFluffConsole.success(f"Fichier {fpath.name} mis à jour avec les nouveaux TOMBSTONES.")
        except Exception as e:
            ZeroFluffConsole.error(f"Erreur durant dream_collector sur {fpath}: {e}")

    summary = {
        "project": project_name,
        "checked_rules": checked_rules,
        "tombstones_applied": deprecated_count,
        "reports": tombstone_reports
    }
    ZeroFluffConsole.info(f"Dream hygiene terminée : {deprecated_count} règle(s) passée(s) en TOMBSTONE sur {checked_rules} vérifiée(s).")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True)
    parser.add_argument("--keyword", help="Le mot-clé ou motif qui déclenche la règle")
    parser.add_argument("--msg", help="Le message ou la directive à afficher")
    parser.add_argument("--scope", choices=["project", "global"], default="project", help="Portée de la règle")
    parser.add_argument("--dream", action="store_true", help="Lance le collecteur d'hygiène nocturne RHO (Tombstones)")
    args = parser.parse_args()
    
    if args.dream:
        dream_collector(args.project)
    elif args.keyword and args.msg:
        optimize_rho(args.project, args.keyword, args.msg, args.scope)
    else:
        parser.print_help()
