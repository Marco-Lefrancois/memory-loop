#!/usr/bin/env python3
"""
tui_panes.py - Rich Human-Centric TUI Entrypoints for mLoop Herdr Plugin

Renders beautifully formatted Sprint Backlogs, EvidencePacks, Fact-Search dossiers,
DAG events, and Runtime Status using Rich panels, markdown syntax, and tables.
"""

import sys
import os
import json
import time
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.markdown import Markdown
    from rich.table import Table
    from rich.text import Text
    from rich import box

    RICH_AVAILABLE = True
    console = Console()
except ImportError:
    RICH_AVAILABLE = False
    console = None


def render_banner(title: str, subtitle: str = ""):
    """Renders a stylish human-friendly banner."""
    if RICH_AVAILABLE:
        grid = Table.grid(expand=True)
        grid.add_column(justify="left", ratio=1)
        grid.add_column(justify="right", ratio=1)
        grid.add_row(
            Text(f"🐑 mLoop — {title}", style="bold cyan"),
            Text(subtitle or "Herdr Runtime v0.8.2+", style="dim"),
        )
        console.print(Panel(grid, border_style="bright_blue", box=box.ROUNDED))
    else:
        print("=" * 65)
        print(f" 🐑 mLoop — {title} | {subtitle or 'Herdr Runtime v0.8.2+'}")
        print("=" * 65)


def wait_prompt():
    """Allows human inspection without instant process termination."""
    try:
        if RICH_AVAILABLE:
            console.print(
                "\n[dim]💡 [q] Quitter  •  [Entrée] Rafraîchir[/dim]", end=" "
            )
        else:
            print("\n💡 [q] Quitter • [Entrée] Rafraîchir: ", end="")
        inp = input().strip().lower()
        return inp != "q"
    except (KeyboardInterrupt, EOFError):
        return False


def cmd_backlog():
    """Renders the Sprint Backlog with clean markdown and INVEST badges."""
    render_banner("Sprint Backlog & INVEST Metrics", "Vue Split Déclarative")

    backlog_file = PROJECT_ROOT / "backlog" / "sprint_backlog.md"
    if not backlog_file.exists():
        proj_dir = PROJECT_ROOT / "Projects"
        candidates = (
            list(proj_dir.glob("*/backlog/sprint_backlog.md"))
            if proj_dir.exists()
            else []
        )
        if candidates:
            backlog_file = candidates[0]

    if not backlog_file.exists():
        if RICH_AVAILABLE:
            console.print(
                Panel(
                    "❌ Aucun fichier [bold yellow]sprint_backlog.md[/bold yellow] trouvé.",
                    border_style="red",
                )
            )
        else:
            print("❌ Aucun fichier sprint_backlog.md trouvé.")
        return

    content = backlog_file.read_text(encoding="utf-8")
    if RICH_AVAILABLE:
        console.print(
            Panel(
                Markdown(content),
                title=f"📄 {backlog_file.name}",
                border_style="cyan",
                box=box.ROUNDED,
            )
        )
    else:
        print(f"📄 Source: {backlog_file}\n")
        print(content)


def cmd_evidence():
    """Renders Fact-Search dossiers and EvidencePacks in structured cards."""
    render_banner("Fact-Search & EvidencePack Inspector", "SSOT Passages & Proofs")

    evidence_dirs = [
        PROJECT_ROOT / "memory" / "evidence",
        PROJECT_ROOT / "Projects" / "mLoop" / "memory" / "evidence",
    ]
    proj_dir = PROJECT_ROOT / "Projects"
    if proj_dir.exists():
        for pd in proj_dir.glob("*/memory/evidence"):
            if pd.is_dir() and pd not in evidence_dirs:
                evidence_dirs.append(pd)

    fact_search_files = []
    evidence_files = []
    for ed in evidence_dirs:
        if ed.exists():
            # Nom canonique (DOSSIER_DE_PREUVES_PROTOCOL.md §4) : <STORY_ID>_fact_dossier.md
            fact_search_files.extend(list(ed.glob("*_fact_dossier.md")))
            # Rétro-compatibilité lecture seule : ancien nommage divergent Mode Herdr (Phase 0 fix)
            fact_search_files.extend(list(ed.glob("*_fact_search.md")))
            evidence_files.extend(list(ed.glob("*_evidence.json")))

    # 1. Display latest Fact-Search Markdown dossier if present
    if fact_search_files:
        latest_fs = sorted(
            fact_search_files, key=lambda f: f.stat().st_mtime, reverse=True
        )[0]
        fs_content = latest_fs.read_text(encoding="utf-8")
        if RICH_AVAILABLE:
            console.print(
                Panel(
                    Markdown(fs_content),
                    title=f"📚 Dossier Fact-Search Actif : {latest_fs.name}",
                    border_style="green",
                    box=box.ROUNDED,
                )
            )
        else:
            print(f"\n📚 DOSSIER FACT-SEARCH : {latest_fs.name}\n")
            print(fs_content)
            print("-" * 60)

    # 2. Display EvidencePack cards
    if evidence_files:
        if RICH_AVAILABLE:
            table = Table(
                title="📦 EvidencePacks Sidecars Récents", box=box.ROUNDED, expand=True
            )
            table.add_column("Story ID", style="bold cyan", width=16)
            table.add_column("Statut", style="bold", width=14)
            table.add_column("Worker Herdr", style="dim", width=20)
            table.add_column("Résumé de Preuve", style="white")

            for ef in evidence_files[:8]:
                try:
                    data = json.loads(ef.read_text(encoding="utf-8"))
                    sid = data.get("story_id", ef.stem)
                    w = data.get("herdr_worker", "N/A")
                    st = data.get("harvest_status", "UNKNOWN")
                    summary = (
                        (data.get("execution_summary") or "").strip().replace("\n", " ")
                    )
                    preview = summary[:100] + ("..." if len(summary) > 100 else "")

                    st_style = (
                        "[bold green]COMPLETED[/]"
                        if st == "COMPLETED"
                        else f"[bold yellow]{st}[/]"
                    )
                    table.add_row(sid, st_style, w, preview)
                except Exception:
                    table.add_row(ef.stem, "[red]ERROR[/]", "-", "Fichier corrompu")

            console.print(table)
        else:
            print(f"\n📦 EvidencePacks ({len(evidence_files)} trouvés) :\n")
            for ef in evidence_files[:5]:
                try:
                    data = json.loads(ef.read_text(encoding="utf-8"))
                    print(f" • [{data.get('harvest_status')}] {data.get('story_id')}")
                    print(f"   Preuve: {data.get('execution_summary', '')[:100]}...\n")
                except Exception:
                    pass
    elif not fact_search_files:
        if RICH_AVAILABLE:
            console.print(
                Panel(
                    "ℹ️ Aucun EvidencePack ni dossier Fact-Search généré pour le moment.",
                    border_style="yellow",
                )
            )
        else:
            print("ℹ️ Aucun EvidencePack généré pour le moment.")


def cmd_dag():
    """Renders DAG Event Stream in a clean real-time table."""
    render_banner("DAG Monitor & Event Stream", "Flux Multi-Agents")
    events_file = PROJECT_ROOT / "memory" / "herdr_events.jsonl"

    if not events_file.exists():
        if RICH_AVAILABLE:
            console.print(
                Panel(
                    "ℹ️ Aucun événement live dans [dim]memory/herdr_events.jsonl[/dim].",
                    border_style="dim",
                )
            )
        else:
            print("ℹ️ Aucun flux d'événements live dans memory/herdr_events.jsonl.")
        return

    lines = events_file.read_text(encoding="utf-8").splitlines()
    if RICH_AVAILABLE:
        table = Table(
            title=f"📡 20 Derniers Événements ({events_file.name})",
            box=box.ROUNDED,
            expand=True,
        )
        table.add_column("Heure", style="dim", width=10)
        table.add_column("Type", style="bold magenta", width=18)
        table.add_column("Nœud DAG", style="cyan", width=16)
        table.add_column("Détail / Initiative", style="white")

        for l in lines[-20:]:
            if not l.strip():
                continue
            try:
                ev = json.loads(l)
                ts = time.strftime(
                    "%H:%M:%S", time.localtime(ev.get("timestamp", time.time()))
                )
                table.add_row(
                    ts,
                    ev.get("event_type", "event").upper(),
                    ev.get("node_id", "-"),
                    ev.get("initiative", ""),
                )
            except Exception:
                table.add_row("-", "RAW", "-", l[:80])
        console.print(table)
    else:
        for l in lines[-15:]:
            print(l)


def cmd_status():
    """Renders the comprehensive project runtime health status."""
    render_banner("mLoop Project & Worker Runtime Health", "Status Hub")
    try:
        from src.core.herdr_adapter import herdr

        res = herdr.list_agents()
        if res.get("success"):
            data = res.get("result", {})
            agents = data.get("result", {}).get("agents", []) or data.get("agents", [])
            if RICH_AVAILABLE:
                table = Table(
                    title=f"🤖 Workers Herdr Actifs ({len(agents)})",
                    box=box.ROUNDED,
                    expand=True,
                )
                table.add_column("Nom Worker", style="bold cyan")
                table.add_column("Statut", style="bold")
                table.add_column("Volet PTY", style="yellow")
                for a in agents:
                    st = a.get("agent_status", "unknown")
                    color = (
                        "green"
                        if st == "idle"
                        else ("yellow" if st == "working" else "red")
                    )
                    table.add_row(
                        a.get("name", "anon"),
                        f"[{color}]{st.upper()}[/{color}]",
                        str(a.get("pane_id", "-")),
                    )
                console.print(table)
            else:
                print(f"🤖 Workers actifs : {len(agents)}")
                for a in agents:
                    print(
                        f" - {a.get('name')}: {a.get('agent_status')} (Volet: {a.get('pane_id')})"
                    )
        else:
            print("ℹ️ Daemon Herdr en attente de connexion.")
    except Exception as e:
        print(f"Erreur de statut: {e}")


def cmd_reap_zombies():
    """Purges orphaned workers with visual feedback."""
    render_banner("Purge des Workers Zombies", "Teardown Gate")
    try:
        from src.core.herdr_adapter import herdr

        res = herdr.audit_and_reap_zombies()
        count = res.get("reaped_count", 0)
        if RICH_AVAILABLE:
            if count > 0:
                console.print(
                    Panel(
                        f"✅ [bold green]{count} worker(s) zombie(s)[/bold green] purgé(s) avec succès.",
                        border_style="green",
                    )
                )
            else:
                console.print(
                    Panel(
                        "✨ [bold cyan]Aucun worker orphelin détecté.[/bold cyan] Espace de travail propre.",
                        border_style="cyan",
                    )
                )
        else:
            print(f"✅ {count} worker(s) purgé(s).")
    except Exception as e:
        print(f"Erreur purge: {e}")


def main():
    if len(sys.argv) < 2:
        render_banner("mLoop Orchestrator TUI")
        print(
            "Usage: python tui_panes.py [backlog | evidence | dag | status | reap_zombies]"
        )
        return

    cmd = sys.argv[1].lower()
    keep_running = True

    while keep_running:
        if RICH_AVAILABLE:
            console.clear()

        if cmd == "backlog":
            cmd_backlog()
        elif cmd in ("evidence", "fact_search"):
            cmd_evidence()
        elif cmd == "dag":
            cmd_dag()
        elif cmd == "status":
            cmd_status()
        elif cmd == "reap_zombies":
            cmd_reap_zombies()
            break
        else:
            print(f"Commande TUI inconnue : {cmd}")
            break

        keep_running = wait_prompt()


if __name__ == "__main__":
    main()
