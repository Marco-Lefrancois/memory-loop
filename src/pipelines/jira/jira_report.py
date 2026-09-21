"""
Sous-module Jira : jira_report.py
Responsabilité : Génération des rapports d'audit et journaux de synchronisation.
"""

import os
import re
from datetime import datetime
from pathlib import Path
from src.cli import ZeroFluffConsole


def _print_audit_report(actions_log: list) -> None:
    ZeroFluffConsole.section("RAPPORT D'AUDIT DE SYNCHRONISATION JIRA")
    print("=" * 115)
    print(
        f"{'TYPE':<12} | {'ID / CLE':<12} | {'TITRE / ELEMENT':<45} | {'ACTION':<10} | {'DETAILS'}"
    )
    print("-" * 115)
    for act in actions_log:
        print(
            f"{act['type']:<12} | {act['id']:<12} | "
            f"{act['title']:<45} | {act['action']:<10} | {act['details']}"
        )
    print("=" * 115)


def _write_markdown_report(project_path: Path, project_name: str, actions_log: list) -> None:
    """Écrit le rapport de sync courant (jira_sync_report.md, horodaté, écrasé à chaque run)
    ET append une entrée dans le journal cumulatif (jira_sync_history.md).
    """
    run_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    report_path = project_path / "memory" / "jira_sync_report.md"
    history_path = project_path / "memory" / "jira_sync_history.md"

    counts = {}
    for act in actions_log:
        k = act["action"].strip()
        counts[k] = counts.get(k, 0) + 1
    stats_parts = [f"{v} {k}" for k, v in sorted(counts.items())]
    stats_line = " · ".join(stats_parts) if stats_parts else "Aucune opération"

    jira_base_url = (os.getenv("JIRA_URL") or "").rstrip("/")
    table_rows = []
    for act in actions_log:
        item_type = act["type"].strip()
        item_id = act["id"].strip()
        item_title = act["title"].replace("|", "\\|").strip()
        item_action = act["action"].strip()
        item_details = act["details"].replace("|", "\\|").strip()

        if jira_base_url and re.match(r"^[A-Z0-9]+-\d+$", item_id):
            item_id_formatted = f"[{item_id}]({jira_base_url}/browse/{item_id})"
        else:
            item_id_formatted = item_id

        table_rows.append(
            f"| {item_type} | {item_id_formatted} | {item_title} | {item_action} | {item_details} |"
        )

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
        ZeroFluffConsole.success(
            "Rapport de synchronisation rédigé sous memory/jira_sync_report.md"
        )
    except Exception as e:
        ZeroFluffConsole.error(f"Échec de l'écriture du rapport Jira : {e}")

    history_lines = [
        f"\n---\n",
        f"## 🕐 Session {run_ts} — {stats_line}",
        "| Type | ID / Clé | Élément / Titre | Action | Détails |",
        "| :--- | :--- | :--- | :--- | :--- |",
    ] + table_rows

    try:
        if not history_path.exists():
            history_path.write_text(
                f"# 📒 Journal Cumulatif de Synchronisation Jira — "
                f"Projet `{project_name}`\n\n"
                f"> Ce fichier est un **transaction log persistant**. "
                f"Il est alimenté en mode append "
                f"à chaque exécution de `jira_sync` et n'est jamais écrasé.\n",
                encoding="utf-8",
            )
        with history_path.open("a", encoding="utf-8") as f:
            f.write("\n".join(history_lines) + "\n")
        ZeroFluffConsole.success("Journal cumulatif mis à jour sous memory/jira_sync_history.md")
    except Exception as e:
        ZeroFluffConsole.error(f"Échec de l'écriture du journal cumulatif : {e}")
