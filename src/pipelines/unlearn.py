import os
import json
import yaml
from pathlib import Path
from src.cli import ZeroFluffConsole
from src.bridges.mcp_loop_mem import clear_preloaded_context

def run_unlearn(project_name: str, concept_id: str) -> dict:
    ZeroFluffConsole.section(f"Agentic Unlearning: Désapprentissage de '{concept_id}'")
    
    project_path = Path("Projects") / project_name
    memory_dir = project_path / "memory"
    
    nodes_removed = 0
    edges_removed = 0
    rho_rules_disabled = 0
    
    # 1. Purge from Knowledge Graph
    graph_path = memory_dir / "knowledge_graph.json"
    if graph_path.exists():
        try:
            with open(graph_path, "r", encoding="utf-8") as f:
                graph_data = json.load(f)
                
            old_nodes = graph_data.get("nodes", [])
            old_edges = graph_data.get("edges", [])
            
            removed_node_ids = set()
            new_nodes = []
            for node in old_nodes:
                node_str = json.dumps(node).lower()
                if concept_id.lower() in node_str:
                    n_id = str(node.get("id") or node.get("name") or "")
                    if n_id:
                        removed_node_ids.add(n_id)
                    nodes_removed += 1
                else:
                    new_nodes.append(node)
                    
            new_edges = []
            for edge in old_edges:
                src = str(edge.get("source") or edge.get("from") or "")
                tgt = str(edge.get("target") or edge.get("to") or "")
                if src in removed_node_ids or tgt in removed_node_ids:
                    edges_removed += 1
                else:
                    new_edges.append(edge)
                    
            graph_data["nodes"] = new_nodes
            graph_data["edges"] = new_edges
            
            with open(graph_path, "w", encoding="utf-8") as f:
                json.dump(graph_data, f, indent=2, ensure_ascii=False)
                
            ZeroFluffConsole.success(f"[Graphify] Purge terminée : {nodes_removed} nœud(s) et {edges_removed} arête(s) supprimé(s).")
        except Exception as e:
            ZeroFluffConsole.error(f"Erreur lors de la purge du graphe : {e}")

    # 2. Invalidate RHO Rules
    rho_file = memory_dir / "rho_rules.yaml"
    if rho_file.exists():
        try:
            with open(rho_file, "r", encoding="utf-8") as f:
                rules_data = yaml.safe_load(f) or {"rules": []}
                
            rules = rules_data.get("rules", [])
            new_rules = []
            for rule in rules:
                kw = str(rule.get("keyword", "")).lower()
                if concept_id.lower() in kw:
                    rho_rules_disabled += 1
                else:
                    new_rules.append(rule)
                    
            rules_data["rules"] = new_rules
            with open(rho_file, "w", encoding="utf-8") as f:
                yaml.dump(rules_data, f, allow_unicode=True, sort_keys=False)
                
            ZeroFluffConsole.success(f"[RHO] Invalidation terminée : {rho_rules_disabled} règle(s) RHO désactivée(s).")
        except Exception as e:
            ZeroFluffConsole.error(f"Erreur lors de l'invalidation RHO : {e}")

    # 3. Purge RAM Cache
    clear_preloaded_context(concept_id)
    ZeroFluffConsole.success(f"[RAM Cache] Cache mémoire purgé pour '{concept_id}'.")

    # 4. Tombstone Event Logging
    try:
        from src.state import LoopState, JournalEntry
        if project_path.exists():
            state = LoopState(project_name=project_name)
            try:
                state.load_from_audit(project_path)
            except Exception:
                state.load_from_graph(project_path)
                
            entry = JournalEntry(
                event="Agentic Unlearning (Tombstone)",
                details=f"Désapprentissage du concept '{concept_id}'. Nodes supprimés: {nodes_removed}, RHO dépréciés: {rho_rules_disabled}.",
                impacted_nodes=[concept_id]
            )
            state.journal.append(entry)
            state.save_to_audit(project_path)
            ZeroFluffConsole.success("Tombstone enregistré dans le journal du projet.")
    except Exception as e:
        ZeroFluffConsole.info(f"Journalisation Tombstone ignorée : {e}")

    return {
        "status": "unlearned",
        "concept": concept_id,
        "nodes_removed": nodes_removed,
        "edges_removed": edges_removed,
        "rho_rules_disabled": rho_rules_disabled
    }
