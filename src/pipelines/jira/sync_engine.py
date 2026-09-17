"""
Sous-module Jira : sync_engine.py
Responsabilité : Logique complète de synchronisation du backlog local vers Jira Cloud.
Gère la création et la mise à jour des stories et sous-tâches via l'API Jira v2/v3.

Sécurité (ADR JIRA_SYNC_SAFE) :
- La fonction publique principale est désormais sync_targeted_to_jira() (périmètre explicite).
- build_sync_preview() génère le manifeste SHA-256 et le rapport dry-run.
- sync_backlog_to_jira() est maintenue pour la compatibilité ascendante uniquement ;
  elle délègue à sync_targeted_to_jira() avec la liste complète des éligibles.
"""
import hashlib
import os
import uuid
import httpx
import re
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from src.state import LoopState, ProjectLayout, SprintBacklogItem
from src.cli import ZeroFluffConsole
from src.pipelines.jira.md_cleaner import load_rich_description, clean_markdown_description
from src.pipelines.jira.adf_converter import markdown_to_adf
import json

class JiraMappingRequiredError(Exception):
    def __init__(self, missing_subtasks: list, allowed_subtasks: dict):
        self.missing_subtasks = missing_subtasks
        self.allowed_subtasks = allowed_subtasks
        
        types_info = []
        for v in sorted(allowed_subtasks.values(), key=lambda x: x['name']):
            types_info.append(f"  - {v['name']} (ID: {v['id']})")
        options_str = "\n".join(types_info)
        
        msg = (f"ACTION REQUIRED: The following subtask types are not mapped: {missing_subtasks}\n"
               f"Please configure them in LoopState (jira_subtask_mapping).\n"
               f"Available Jira issue types:\n{options_str}")
        super().__init__(msg)

# MAPPING DYNAMIQUE DES TYPES DE SOUS-TÂCHES PAR NOM DE COMPOSANT (Spécifique JEANCOUTU)
SUBTASK_TYPE_VARIATIONS = {
    "analyse": ["analyse", "analysis", "architecture"],
    "développement": ["développement", "developpement", "development", "programmation"],
    "test": ["assurance qualité", "assurance qualite", "qa", "test"],
    "assurance": ["assurance qualité", "assurance qualite", "qa", "test"],
    "déploiement": ["déploiement", "deploiement", "deployment"]
}

def _clean_title(title: str) -> str:
    """Nettoie le titre du markdown (retire les '# ' et les tags/préfixes)."""
    t = title.replace("# ", "").strip()
    return re.sub(r'^(?:\[.*?\]\s*)?(?:STORY|ST|REC)[A-Z0-9\-]*\s*[:\-]\s*', '', t, flags=re.IGNORECASE).strip()

def _clean_adf_description(md_content: str) -> str:
    """Retire le titre H1 (s'il existe) même après le frontmatter."""
    # 0. Temporairement ignorer le frontmatter pour trouver le H1
    content_to_check = md_content
    if content_to_check.startswith("---"):
        parts = content_to_check.split("---", 2)
        if len(parts) >= 3:
            content_to_check = parts[2]
            
    lines = content_to_check.splitlines()
    h1_found = None
    if lines:
        for i, line in enumerate(lines):
            if line.strip().startswith('# '):
                h1_found = line
                break
            elif line.strip(): # Du contenu autre qu'un H1 trouvé en premier
                break
    
    if h1_found:
        return md_content.replace(h1_found, "", 1).strip()
    return md_content.strip()

def _fetch_allowed_subtask_types(client: httpx.Client, project_key: str) -> dict:
    allowed_subtasks = {}
    try:
        r_meta = client.get("/rest/api/3/issuetype")
        if r_meta.status_code == 200:
            issue_types = r_meta.json()
            for it in issue_types:
                if it.get("subtask"):
                    it_name = it.get("name", "")
                    it_id = it.get("id")
                    clean_name = it_name.lstrip("- ").lower()
                    allowed_subtasks[clean_name] = {"id": it_id, "name": it_name}
    except Exception:
        pass
    return allowed_subtasks

def is_jira_status_closed(status_name: str, status_category_key: str = "") -> bool:
    """
    Détermine si un statut Jira correspond à un état FERMÉ / TERMINÉ / ARCHIVÉ.
    Règle constitutionnelle mLoop : 'si un récit est au statut FERMÉ dans jira ne jamais sync'.
    """
    if not status_name and not status_category_key:
        return False

    # 1. statusCategory Jira Cloud ("done" regroupe Fermé, Terminé, Closed, Done, Resolved, etc.)
    if status_category_key and status_category_key.strip().lower() == "done":
        return True

    # 2. Correspondance textuelle explicite multilingue (FR / EN)
    normalized = status_name.strip().lower()
    closed_keywords = {
        "fermé", "fermee", "fermée", "ferme", "closed", "close", "clos",
        "terminé", "terminee", "terminée", "termine", "done", "resolved",
        "résolu", "resolu", "archived", "archivé", "archive",
        "abandonné", "abandonne", "cancelled", "canceled", "annulé", "annule"
    }
    return normalized in closed_keywords

def _fetch_existing_stories(client: httpx.Client, state: LoopState) -> dict:
    existing_stories_map = {}
    try:
        jql = f"project = {state.jira_project_key} AND issuetype in (Story) ORDER BY created DESC"
        start_at = 0
        max_results = 100
        while start_at < 500:
            r_search = client.get(f"/rest/api/3/search/jql?jql={jql}&startAt={start_at}&maxResults={max_results}&fields=summary,status")
            if r_search.status_code == 200:
                search_data = r_search.json()
                issues = search_data.get("issues", [])
                if not issues:
                    break
                for issue in issues:
                    summary = issue.get("fields", {}).get("summary", "")
                    status_obj = issue.get("fields", {}).get("status", {})
                    for story_item in state.sprint_backlog:
                        if story_item.id in summary or _clean_title(story_item.title).lower() == _clean_title(summary).lower():
                            existing_stories_map[story_item.id] = {
                                "key": issue.get("key"),
                                "id": issue.get("id"),
                                "status": status_obj.get("name", ""),
                                "status_category": status_obj.get("statusCategory", {}).get("key", ""),
                            }
                if len(issues) < max_results:
                    break
                start_at += max_results
            else:
                break
    except Exception:
        pass
    return existing_stories_map

def _fetch_existing_subtask_data(client: httpx.Client, story_key: str) -> dict:
    existing_sub_data = {}
    try:
        r_issue = client.get(f"/rest/api/2/issue/{story_key}?fields=subtasks")
        if r_issue.status_code == 200:
            issue_details = r_issue.json()
            subtasks = issue_details.get("fields", {}).get("subtasks", [])
            for sub in subtasks:
                sub_summary = sub.get("fields", {}).get("summary", "")
                sub_key = sub.get("key")
                existing_sub_data[sub_summary.strip().lower()] = sub_key
    except Exception:
        pass
    return existing_sub_data

def _validate_subtasks_mapping(state: LoopState, allowed_subtasks: dict, project_path: Path) -> None:
    all_needed = set(state.jira_default_subtasks)
    for item in state.sprint_backlog:
        if getattr(item, 'grilled', False) and getattr(item, 'subtasks', None):
            all_needed.update(item.subtasks)
            
    missing_mappings = []
    for st_name in all_needed:
        st_lower = st_name.lower().strip()
        if st_lower not in state.jira_subtask_mapping:
            missing_mappings.append(st_name)
            
    if missing_mappings:
        raise JiraMappingRequiredError(missing_mappings, allowed_subtasks)


def _get_subtask_type_id(sub_name: str, allowed_subtasks: dict, state: LoopState) -> dict:
    comp_lower = sub_name.lower().strip()
    
    # 1. Utilisation du mappage sauvegardé dans le LoopState
    if comp_lower in state.jira_subtask_mapping:
        return {"id": state.jira_subtask_mapping[comp_lower]}
    
    # 2. Exact match (fallback)
    for clean_key, info in allowed_subtasks.items():
        if comp_lower == clean_key:
            return {"id": info["id"]}

    # 3. Partial match (fallback)
    for clean_key, info in allowed_subtasks.items():
        if comp_lower in clean_key or clean_key in comp_lower:
            return {"id": info["id"]}
            
    # 3. Utilisation des variations
    for target_key, variations in SUBTASK_TYPE_VARIATIONS.items():
        if any(v in comp_lower for v in variations) or target_key in comp_lower:
            for v in variations:
                for name, info in allowed_subtasks.items():
                    if v in name:
                        return {"id": info["id"]}
    standard_names = ["sub-task", "sous-tâche", "subtask", "sous-tache"]
    for sn in standard_names:
        for name, info in allowed_subtasks.items():
            if sn == name:
                return {"id": info["id"]}
    if allowed_subtasks:
        first_key = list(allowed_subtasks.keys())[0]
        return {"id": allowed_subtasks[first_key]["id"]}
    return None

def _create_subtask(
    client: httpx.Client,
    sub_name: str,
    parent_key: str,
    parent_title: str,
    project_key: str,
    allowed_subtasks: dict,
    actions_log: list,
    billing_id: str,
    components_payload: list,
    state: LoopState
):
    """Crée une sous-tâche Jira avec payload résilient et fallback automatique.
    Tente d'abord le payload complet (avec composants + facturation).
    En cas de rejet (400), bascule vers le payload minimal strict.
    Utilise l'API v3 de manière uniforme.
    """
    clean_st_title = _clean_title(parent_title)
    full_summary = f"{sub_name} - {clean_st_title}"
    matched_issuetype = _get_subtask_type_id(sub_name, allowed_subtasks, state)

    # Payload complet (tentative 1)
    sub_payload = {
        "fields": {
            "project": {"key": project_key},
            "parent": {"key": parent_key},
            "summary": full_summary,
            "issuetype": matched_issuetype
        }
    }
    if components_payload:
        sub_payload["fields"]["components"] = components_payload
    if billing_id:
        sub_payload["fields"]["customfield_10151"] = {"id": billing_id}

    try:
        r_sub = client.post("/rest/api/3/issue", json=sub_payload)
        if r_sub.status_code == 201:
            created_sub = r_sub.json()
            actions_log.append({
                "type": "  Sub-task",
                "id": created_sub.get("key", "-"),
                "title": sub_name,
                "action": "CREEE",
                "details": f"Sous-tache de {parent_key}"
            })
            return
        
        # Fallback automatique : payload minimal strict (sans champs optionnels)
        if r_sub.status_code in [400, 422]:
            minimal_payload = {
                "fields": {
                    "project": {"key": project_key},
                    "parent": {"key": parent_key},
                    "summary": full_summary,
                    "issuetype": matched_issuetype
                }
            }
            r_fallback = client.post("/rest/api/3/issue", json=minimal_payload)
            if r_fallback.status_code == 201:
                created_sub = r_fallback.json()
                actions_log.append({
                    "type": "  Sub-task",
                    "id": created_sub.get("key", "-"),
                    "title": sub_name,
                    "action": "CREEE",
                    "details": f"Sous-tache de {parent_key} (payload minimal)"
                })
                return
            else:
                actions_log.append({
                    "type": "  Sub-task", "id": "-", "title": sub_name, "action": "ECHEC",
                    "details": f"Erreur fallback: {r_fallback.text[:80]}"
                })
        else:
            actions_log.append({
                "type": "  Sub-task", "id": "-", "title": sub_name, "action": "ECHEC",
                "details": f"Erreur: {r_sub.text[:80]}"
            })
    except Exception as e:
        actions_log.append({
            "type": "  Sub-task", "id": "-", "title": sub_name, "action": "ECHEC",
            "details": f"Exception: {str(e)[:60]}"
        })

def _print_audit_report(actions_log: list) -> None:
    ZeroFluffConsole.section("RAPPORT D'AUDIT DE SYNCHRONISATION JIRA")
    print("=" * 115)
    print(f"{'TYPE':<12} | {'ID / CLE':<12} | {'TITRE / ELEMENT':<45} | {'ACTION':<10} | {'DETAILS'}")
    print("-" * 115)
    for act in actions_log:
        print(f"{act['type']:<12} | {act['id']:<12} | {act['title']:<45} | {act['action']:<10} | {act['details']}")
    print("=" * 115)

def _write_markdown_report(project_path: Path, project_name: str, actions_log: list) -> None:
    """Écrit le rapport de sync courant (jira_sync_report.md, horodaté, écrasé à chaque run)
    ET append une entrée dans le journal cumulatif (jira_sync_history.md) qui sert de
    transaction log persistant de toutes les opérations Jira effectuées.
    """
    from datetime import datetime
    run_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    report_path = project_path / "memory" / "jira_sync_report.md"
    history_path = project_path / "memory" / "jira_sync_history.md"

    # --- Statistiques synthétiques ---
    counts = {}
    for act in actions_log:
        k = act['action'].strip()
        counts[k] = counts.get(k, 0) + 1
    stats_parts = [f"{v} {k}" for k, v in sorted(counts.items())]
    stats_line = " · ".join(stats_parts) if stats_parts else "Aucune opération"

    # --- Lignes du tableau ---
    jira_base_url = (os.getenv("JIRA_URL") or "").rstrip("/")
    table_rows = []
    for act in actions_log:
        item_type  = act['type'].strip()
        item_id    = act['id'].strip()
        item_title = act['title'].replace("|", "\\|").strip()
        item_action= act['action'].strip()
        item_details = act['details'].replace("|", "\\|").strip()
        
        # Formater un lien cliquable si c'est une clé Jira valide
        if jira_base_url and re.match(r'^[A-Z0-9]+-\d+$', item_id):
            item_id_formatted = f"[{item_id}]({jira_base_url}/browse/{item_id})"
        else:
            item_id_formatted = item_id
            
        table_rows.append(f"| {item_type} | {item_id_formatted} | {item_title} | {item_action} | {item_details} |")

    # ── 1. Rapport courant (écrasé à chaque run, horodaté) ──────────────────
    report_lines = [
        f"# 📋 Rapport de Synchronisation Jira — Projet `{project_name}`\n",
        f"> **Exécuté le** : {run_ts}  |  **Résumé** : {stats_line}\n",
        "## 📊 Transactions",
        "| Type | ID / Clé | Élément / Titre | Action | Détails |",
        "| :--- | :--- | :--- | :--- | :--- |",
    ] + table_rows

    try:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text("\n".join(report_lines), encoding="utf-8")
        ZeroFluffConsole.success(f"Rapport de synchronisation rédigé sous memory/jira_sync_report.md")
    except Exception as e:
        ZeroFluffConsole.error(f"Échec de l'écriture du rapport Jira : {e}")

    # ── 2. Journal cumulatif (append, jamais écrasé) ─────────────────────────
    history_lines = [
        f"\n---\n",
        f"## 🕐 Session {run_ts} — {stats_line}",
        "| Type | ID / Clé | Élément / Titre | Action | Détails |",
        "| :--- | :--- | :--- | :--- | :--- |",
    ] + table_rows

    try:
        # Initialiser le fichier avec un en-tête si c'est la première fois
        if not history_path.exists():
            history_path.write_text(
                f"# 📒 Journal Cumulatif de Synchronisation Jira — Projet `{project_name}`\n\n"
                f"> Ce fichier est un **transaction log persistant**. Il est alimenté en mode append "
                f"à chaque exécution de `jira_sync` et n'est jamais écrasé.\n",
                encoding="utf-8"
            )
        with history_path.open("a", encoding="utf-8") as f:
            f.write("\n".join(history_lines) + "\n")
        ZeroFluffConsole.success(f"Journal cumulatif mis à jour sous memory/jira_sync_history.md")
    except Exception as e:
        ZeroFluffConsole.error(f"Échec de l'écriture du journal cumulatif : {e}")


def build_sync_preview(
    project_path: Path,
    state: LoopState,
    eligible_items: List[SprintBacklogItem],
    rejected_items: list,
    target_keys: List[str],
) -> dict:
    """
    Construit le manifeste de prévisualisation (dry-run) et calcule les SHA-256
    de chaque fichier story éligible. Écrit le manifeste sous memory/sync/jira_sync_preview.json.

    Retourne le dict du manifeste (avec 'manifest_id', 'file_hashes', 'eligible', 'rejected').
    """
    run_ts = datetime.now().isoformat()
    manifest_id = str(uuid.uuid4())[:8]
    file_hashes: dict = {}

    stories_dir = project_path / "backlog" / "stories"

    for item in eligible_items:
        # Cherche le fichier story correspondant
        candidates = list(stories_dir.rglob(f"*{item.id}*.md"))
        if not candidates:
            # Tenter avec jira_key
            jk = getattr(item, "jira_key", None) or ""
            if jk:
                candidates = list(stories_dir.rglob(f"*{jk}*.md"))
        if candidates:
            fp = candidates[0]
            try:
                file_hashes[str(fp)] = hashlib.sha256(fp.read_bytes()).hexdigest()
            except Exception:
                pass

    preview = {
        "manifest_id": manifest_id,
        "generated_at": run_ts,
        "project": state.project_name,
        "target_keys": target_keys,
        "eligible": [
            {
                "id": i.id,
                "jira_key": getattr(i, "jira_key", None) or "",
                "title": i.title,
                "status": getattr(i.status, "value", str(i.status)),
            }
            for i in eligible_items
        ],
        "rejected": [
            {
                "id": i.id,
                "jira_key": getattr(i, "jira_key", None) or "",
                "reason": reason,
            }
            for i, reason in rejected_items
        ],
        "file_hashes": file_hashes,
    }

    # Écriture du manifeste
    manifest_path = project_path / "memory" / "sync" / "jira_sync_preview.json"
    try:
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(
            json.dumps(preview, indent=2, ensure_ascii=False), encoding="utf-8"
        )
    except Exception as e:
        ZeroFluffConsole.warning(f"Impossible d'écrire le manifeste SHA-256 : {e}")

    return preview


def sync_targeted_to_jira(
    state: LoopState,
    project_path: Path,
    eligible_items: List[SprintBacklogItem],
    manifest_id: str = "",
) -> Optional[LoopState]:
    """
    Synchronise uniquement les items de la liste `eligible_items` vers Jira.
    Cette fonction est le point d'entrée sécurisé ; toutes les gardes ont déjà
    été vérifiées par handle_jira_sync().

    Le rapport généré est ciblé : seules les transactions des items fournis
    sont incluses (plus de bruit de "IGNORE sous-tâche" pour des stories hors-périmètre).
    """
    ZeroFluffConsole.step_s2(
        "Scrum Master",
        f"Synchronisation ciblée vers Jira ({len(eligible_items)} story(s), manifeste={manifest_id})..."
    )

    jira_url = os.getenv("JIRA_URL")
    jira_email = os.getenv("JIRA_EMAIL")
    jira_token = os.getenv("JIRA_API_TOKEN")

    if not all([jira_url, jira_email, jira_token]):
        ZeroFluffConsole.error("Identifiants Jira manquants dans le fichier .env.")
        return None

    auth = (jira_email, jira_token)
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Accept-Encoding": "gzip, deflate",
    }

    with httpx.Client(base_url=jira_url, auth=auth, headers=headers, timeout=30.0) as client:
        if state.jira_default_component_id:
            if str(state.jira_default_component_id).isdigit():
                components_payload = [{"id": str(state.jira_default_component_id)}]
            else:
                components_payload = [{"name": str(state.jira_default_component_id)}]
        else:
            components_payload = []

        billing_id = state.jira_default_billing_id
        global_epic_key = state.jira_epic_key

        allowed_subtasks = _fetch_allowed_subtask_types(client, state.jira_project_key)
        _validate_subtasks_mapping(state, allowed_subtasks, project_path)
        existing_stories_map = _fetch_existing_stories(client, state)

        cache_dir = project_path / "memory" / "cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = cache_dir / "jira_sync_cache.json"
        jira_cache: dict = {}
        if cache_file.exists():
            try:
                jira_cache = json.loads(cache_file.read_text(encoding="utf-8"))
            except Exception:
                pass

        actions_log: list = []
        if global_epic_key:
            actions_log.append({
                "type": "Epic",
                "id": global_epic_key,
                "title": "Epic de rattachement",
                "action": "RATTACHEE",
                "details": f"Liaison active sous {global_epic_key}",
            })

        # ── Traitement des items ciblés uniquement ────────────────────────────
        for item in eligible_items:
            story_files = list((project_path / "backlog" / "stories").rglob(f"*{item.id}*.md"))
            story_file_path = story_files[0] if story_files else None
            mtime = os.path.getmtime(story_file_path) if story_file_path and story_file_path.exists() else 0

            cached_item = jira_cache.get(item.id, {})
            if (
                mtime > 0
                and cached_item.get("mtime") == mtime
                and cached_item.get("status") == getattr(item, "status", None)
                and cached_item.get("jira_key")
            ):
                actions_log.append({
                    "type": "Story",
                    "id": cached_item["jira_key"],
                    "title": item.title,
                    "action": "INCHANGEE",
                    "details": "Synchronisation sautée (Cache Hit mtime)",
                })
                continue

            rich_description = load_rich_description(project_path, item.description, item.description)
            key_match = re.search(r'jira_key:\s*([A-Z0-9-]+)', rich_description)
            forced_key = key_match.group(1) if key_match else None

            if forced_key and (forced_key.endswith("-XXX") or "TBD" in forced_key.upper() or forced_key.upper().startswith("TEMP-")):
                forced_key = None
            elif forced_key:
                try:
                    r_chk = client.get(f"/rest/api/3/issue/{forced_key}?fields=issuetype")
                    if r_chk.status_code == 200:
                        itype = r_chk.json().get("fields", {}).get("issuetype", {})
                        if itype.get("subtask", False):
                            forced_key = None
                except Exception:
                    pass

            epic_match = re.search(r'epic_key:\s*([A-Z0-9-]+)', rich_description)
            story_epic_key = epic_match.group(1) if epic_match else global_epic_key

            already_exists = (forced_key is not None) or (item.id in existing_stories_map)
            story_key = (
                forced_key
                if forced_key
                else (existing_stories_map.get(item.id, {}).get("key") if already_exists else None)
            )

            current_billing_id = billing_id
            current_components = components_payload[:]

            if already_exists and item.id in existing_stories_map:
                map_entry = existing_stories_map[item.id]
                if is_jira_status_closed(map_entry.get("status", ""), map_entry.get("status_category", "")):
                    s_name = map_entry.get("status", "Fermé")
                    ZeroFluffConsole.warning(
                        f"🔒 Story {story_key} ({item.id}) est au statut FERMÉ ('{s_name}') dans Jira — synchronisation strictement ignorée (règle constitutionnelle)."
                    )
                    actions_log.append({
                        "type": "Story",
                        "id": story_key or map_entry.get("key"),
                        "title": _clean_title(item.title),
                        "action": "IGNORE_FERME",
                        "details": f"Statut Jira '{s_name}' (FERMÉ) — synchronisation interdite (règle constitutionnelle)",
                    })
                    continue

            if story_key:
                try:
                    r_existing = client.get(f"/rest/api/3/issue/{story_key}")
                    if r_existing.status_code == 200:
                        existing_data = r_existing.json()
                        e_fields = existing_data.get("fields", {})

                        # ── Garde constitutionnelle : Statut FERMÉ dans Jira ────
                        e_status = e_fields.get("status", {})
                        s_name = e_status.get("name", "")
                        s_cat = e_status.get("statusCategory", {}).get("key", "")
                        if is_jira_status_closed(s_name, s_cat):
                            ZeroFluffConsole.warning(
                                f"🔒 Story {story_key} ({item.id}) est au statut FERMÉ ('{s_name}') dans Jira — synchronisation strictement ignorée (règle constitutionnelle)."
                            )
                            actions_log.append({
                                "type": "Story",
                                "id": story_key,
                                "title": _clean_title(item.title),
                                "action": "IGNORE_FERME",
                                "details": f"Statut Jira '{s_name}' (FERMÉ) — synchronisation interdite (règle constitutionnelle)",
                            })
                            continue

                        if not current_components:
                            epic_comps = e_fields.get("components", [])
                            if epic_comps:
                                current_components = []
                                for c in epic_comps:
                                    if "id" in c:
                                        current_components.append({"id": c["id"]})
                                    elif "name" in c:
                                        current_components.append({"name": c["name"]})
                        if not current_billing_id:
                            b_f = e_fields.get("customfield_10151")
                            if isinstance(b_f, dict):
                                current_billing_id = b_f.get("id")
                            elif b_f:
                                current_billing_id = str(b_f)
                except Exception:
                    pass

            if story_epic_key and (not current_billing_id or not current_components):
                try:
                    r_epic = client.get(f"/rest/api/3/issue/{story_epic_key}")
                    if r_epic.status_code == 200:
                        epic_data = r_epic.json()
                        e_f = epic_data.get("fields", {})
                        if not current_billing_id:
                            b_f = e_f.get("customfield_10151")
                            if isinstance(b_f, dict):
                                current_billing_id = b_f.get("id")
                            elif b_f:
                                current_billing_id = str(b_f)
                        if not current_components:
                            epic_comps = e_f.get("components", [])
                            if epic_comps:
                                current_components = []
                                for c in epic_comps:
                                    if "id" in c:
                                        current_components.append({"id": c["id"]})
                                    elif "name" in c:
                                        current_components.append({"name": c["name"]})
                except Exception:
                    pass

            description_no_title = _clean_adf_description(rich_description)
            cleaned_description = clean_markdown_description(description_no_title)
            adf_description = markdown_to_adf(cleaned_description)

            subtasks_to_sync = state.jira_default_subtasks if state.jira_default_subtasks else [
                "- Analyse", "- Architecture de solutions",
                "- Programmation applicative mobile", "- Assurance qualité"
            ]
            clean_story_title = _clean_title(item.title)

            if already_exists and story_key:
                try:
                    update_payload = {"fields": {"summary": clean_story_title, "description": adf_description}}
                    r_update = client.put(f"/rest/api/3/issue/{story_key}", json=update_payload)

                    try:
                        struct_payload = {"fields": {"issuetype": {"name": "Story"}}}
                        if story_epic_key:
                            struct_payload["fields"]["parent"] = {"key": story_epic_key}
                        client.put(f"/rest/api/3/issue/{story_key}", json=struct_payload)
                    except Exception:
                        pass

                    if r_update.status_code in [200, 204]:
                        actions_log.append({
                            "type": "Story", "id": story_key, "title": clean_story_title,
                            "action": "MAJ", "details": f"Synchronisation réussie (manifeste {manifest_id})",
                        })

                        existing_sub_data = _fetch_existing_subtask_data(client, story_key)

                        for comp in subtasks_to_sync:
                            expected_summary = f"{comp} - {clean_story_title}"
                            found_key = None
                            found_summary = ""
                            comp_lower = comp.lower()

                            intent_variations = []
                            for target, vars in SUBTASK_TYPE_VARIATIONS.items():
                                if target in comp_lower:
                                    intent_variations = vars
                                    break
                            if not intent_variations:
                                intent_variations = [comp_lower]

                            for s_summary, s_key in existing_sub_data.items():
                                for var in intent_variations:
                                    if var in s_summary:
                                        found_key = s_key
                                        found_summary = s_summary
                                        break
                                if found_key:
                                    break

                            if found_key:
                                if found_summary != expected_summary.lower():
                                    try:
                                        r_sub_up = client.put(
                                            f"/rest/api/3/issue/{found_key}",
                                            json={"fields": {"summary": expected_summary}},
                                        )
                                        if r_sub_up.status_code in [200, 204]:
                                            actions_log.append({
                                                "type": "  Sub-task", "id": found_key,
                                                "title": comp, "action": "MAJ", "details": "Titre synchronisé",
                                            })
                                        else:
                                            actions_log.append({
                                                "type": "  Sub-task", "id": found_key,
                                                "title": comp, "action": "ECHEC",
                                                "details": f"MAJ {r_sub_up.status_code}",
                                            })
                                    except Exception:
                                        actions_log.append({
                                            "type": "  Sub-task", "id": found_key,
                                            "title": comp, "action": "IGNORE", "details": "Déjà présente",
                                        })
                                else:
                                    actions_log.append({
                                        "type": "  Sub-task", "id": found_key,
                                        "title": comp, "action": "IGNORE", "details": "Déjà présente",
                                    })
                            else:
                                _create_subtask(
                                    client, comp, story_key, item.title,
                                    state.jira_project_key, allowed_subtasks,
                                    actions_log, current_billing_id, current_components, state,
                                )
                    else:
                        actions_log.append({
                            "type": "Story", "id": story_key, "title": clean_story_title,
                            "action": "ECHEC", "details": f"Erreur {r_update.status_code}: {r_update.text[:80]}",
                        })
                except Exception as e:
                    actions_log.append({
                        "type": "Story", "id": story_key, "title": clean_story_title,
                        "action": "ECHEC", "details": str(e),
                    })
            else:
                try:
                    escaped_title = clean_story_title.replace('"', '\\"')
                    check_jql = f'project = {state.jira_project_key} AND summary ~ "\\"{escaped_title}\\""'
                    r_check = client.get(
                        f"/rest/api/3/search/jql?jql={check_jql}&maxResults=1&fields=summary"
                    )
                    if r_check.status_code == 200 and r_check.json().get("total", 0) > 0:
                        existing_issue = r_check.json().get("issues")[0]
                        actions_log.append({
                            "type": "Story", "id": item.id, "title": clean_story_title,
                            "action": "DOUBLON",
                            "details": f"Existe déjà ({existing_issue.get('key')})",
                        })
                        continue
                except Exception:
                    pass

                payload = {
                    "fields": {
                        "project": {"key": state.jira_project_key},
                        "summary": clean_story_title,
                        "description": adf_description,
                        "issuetype": {"name": "Story"},
                    }
                }
                if current_billing_id:
                    payload["fields"]["customfield_10151"] = {"id": current_billing_id}
                if current_components:
                    payload["fields"]["components"] = current_components
                if story_epic_key:
                    payload["fields"]["parent"] = {"key": story_epic_key}

                try:
                    r = client.post("/rest/api/3/issue", json=payload)
                    if r.status_code == 201:
                        created_story = r.json()
                        new_key = created_story.get("key")

                        try:
                            md_file_path = project_path / "backlog" / item.description
                            if md_file_path.exists():
                                content = md_file_path.read_text(encoding="utf-8")
                                if content.startswith("---"):
                                    parts = content.split("---", 2)
                                    if len(parts) >= 3:
                                        frontmatter = parts[1]
                                        if "jira_key:" not in frontmatter:
                                            new_frontmatter = frontmatter.rstrip() + f"\njira_key: {new_key}\n"
                                        else:
                                            new_frontmatter = re.sub(
                                                r'jira_key:\s*[A-Z0-9-]+',
                                                f'jira_key: {new_key}',
                                                frontmatter,
                                            )
                                        new_content = f"---{new_frontmatter}---{parts[2]}"
                                        md_file_path.write_text(new_content, encoding="utf-8")
                        except Exception as e_md:
                            actions_log.append({
                                "type": "Story", "id": new_key, "title": clean_story_title,
                                "action": "WARN", "details": f"MAJ MD local échouée: {e_md}",
                            })

                        try:
                            sb_path = project_path / ProjectLayout.BACKLOG / ProjectLayout.SPRINT_BACKLOG_FILE
                            if sb_path.exists():
                                sb_content = sb_path.read_text(encoding="utf-8")
                                updated = re.sub(
                                    rf'(\|\s*\*\*{re.escape(item.id)}[^|]*\|)\s*-\s*(\|)',
                                    rf'\1 {new_key} \2',
                                    sb_content,
                                )
                                if updated != sb_content:
                                    sb_path.write_text(updated, encoding="utf-8")
                        except Exception as e_sb:
                            actions_log.append({
                                "type": "Story", "id": new_key, "title": clean_story_title,
                                "action": "WARN", "details": f"MAJ sprint_backlog.md échouée: {e_sb}",
                            })

                        actions_log.append({
                            "type": "Story", "id": new_key, "title": clean_story_title,
                            "action": "CREEE",
                            "details": f"Nouvelle story créée (manifeste {manifest_id})",
                        })
                        for comp in subtasks_to_sync:
                            _create_subtask(
                                client, comp, new_key, item.title,
                                state.jira_project_key, allowed_subtasks,
                                actions_log, current_billing_id, current_components, state,
                            )
                    else:
                        actions_log.append({
                            "type": "Story", "id": item.id, "title": clean_story_title,
                            "action": "ECHEC", "details": r.text[:80],
                        })
                except Exception as e:
                    actions_log.append({
                        "type": "Story", "id": item.id, "title": clean_story_title,
                        "action": "ECHEC", "details": str(e),
                    })

        # ── Cache mtime ───────────────────────────────────────────────────────
        try:
            for act in actions_log:
                if act.get("action") in ("CREEE", "MISE_A_JOUR", "MAJ", "EXISTE", "INCHANGEE") \
                        and act.get("id") and act["id"] != "-":
                    for item in eligible_items:
                        if item.id in act["title"] or act["id"] in getattr(item, "jira_key", ""):
                            story_files = list(
                                (project_path / "backlog" / "stories").rglob(f"*{item.id}*.md")
                            )
                            if story_files and story_files[0].exists():
                                jira_cache[item.id] = {
                                    "mtime": os.path.getmtime(story_files[0]),
                                    "jira_key": act["id"],
                                    "status": getattr(item, "status", None),
                                }
            cache_file.write_text(
                json.dumps(jira_cache, indent=2, ensure_ascii=False), encoding="utf-8"
            )
        except Exception:
            pass

        _print_audit_report(actions_log)
        _write_markdown_report(project_path, state.project_name, actions_log)

    return state


def sync_backlog_to_jira(state: LoopState) -> LoopState:
    """
    Point d'entrée de compatibilité ascendante (conservé pour les appels internes).
    Délègue à sync_targeted_to_jira() avec la liste complète des éligibles.

    ⚠️  Les nouveaux appels doivent passer par handle_jira_sync() (via CLI)
        qui applique toutes les gardes de sécurité ADR JIRA_SYNC_SAFE.
    """
    ZeroFluffConsole.warning(
        "[COMPAT] sync_backlog_to_jira() est appelée en mode rétro-compatibilité.\n"
        "  Pour une synchronisation sécurisée, utilisez la CLI :\n"
        "  python src/swarm.py jira_sync --project <P> --story <CLE>"
    )
    project_path = Path(r"C:\Memory Loop\Projects") / state.project_name
    state.discover_backlog(project_path)

    eligible_items = [
        item for item in state.sprint_backlog
        if getattr(item, "jira_sync_eligible", item.grilled)
    ]
    result = sync_targeted_to_jira(
        state=state,
        project_path=project_path,
        eligible_items=eligible_items,
        manifest_id="compat",
    )
    return result if result is not None else state
