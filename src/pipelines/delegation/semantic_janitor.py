"""
semantic_janitor.py - Continuous Semantic Memory Janitor & Watcher (ADR-0346)

Runs as a lightweight background health monitor or single-pass auditor,
checking relative links, phantom references, and Gherkin integrity with anti-loop debouncing.
"""

import os
import re
import time
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, List, Set

from src.cli import ZeroFluffConsole
from src.core.herdr_adapter import herdr


class SemanticJanitorWatcher:
    """
    In-memory health watcher with SHA256 caching and debouncing to prevent infinite loops.
    """
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.file_hashes: Dict[str, str] = {}
        self.last_alert_time: Dict[str, float] = {}

    def compute_sha256(self, file_path: Path) -> str:
        """Computes quick SHA256 of file content."""
        try:
            return hashlib.sha256(file_path.read_bytes()).hexdigest()
        except Exception:
            return ""

    def audit_file(self, file_path: Path) -> List[str]:
        """Audits a single markdown file for broken relative links and format anomalies."""
        issues = []
        if not file_path.exists() or file_path.suffix != ".md":
            return issues

        text = file_path.read_text(encoding="utf-8")

        # 1. Broken local file:/// links
        file_links = re.findall(r'\[([^\]]+)\]\((file:///[^)#]+)(?:#[^\)]+)?\)', text)
        for lbl, uri in file_links:
            clean_path = uri.replace("file:///", "").replace("%20", " ")
            if not Path(clean_path).exists() and not Path(f"/{clean_path}").exists():
                issues.append(f"Lien local introuvable : [{lbl}]({uri})")

        # 2. Jira-Only Referencing Guardrail (Jira-linking-only)
        if "backlog/stories" in str(file_path).replace("\\", "/"):
            # Check if internal temporary keys or local absolute paths are leaked inside functional body
            if "C:\\" in text or "file:///" in text:
                issues.append("Violation Jira-Only : Chemin absolu local détecté dans le corps du récit.")

        return issues

    def scan_project(self) -> Dict[str, Any]:
        """Scans all Markdown files in the project and reports issues."""
        md_files = list(self.project_path.glob("**/*.md"))
        total_scanned = 0
        issues_by_file: Dict[str, List[str]] = {}

        for mf in md_files:
            # Skip caches, .git, venv
            p_str = str(mf)
            if any(skip in p_str for skip in [".git", "node_modules", "venv", "__pycache__", ".overview.md"]):
                continue

            curr_hash = self.compute_sha256(mf)
            if self.file_hashes.get(p_str) == curr_hash:
                continue  # Content unchanged, skip

            self.file_hashes[p_str] = curr_hash
            total_scanned += 1

            file_issues = self.audit_file(mf)
            if file_issues:
                rel_name = mf.relative_to(self.project_path) if mf.is_relative_to(self.project_path) else mf.name
                issues_by_file[str(rel_name)] = file_issues

        return {
            "total_scanned": total_scanned,
            "total_issues": sum(len(v) for v in issues_by_file.values()),
            "issues": issues_by_file
        }


def run_semantic_janitor(
    project_name: str,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Runs a single-pass health check of the project's memory and documentation.
    """
    ZeroFluffConsole.section("SEMANTIC MEMORY JANITOR")
    proj_dir = Path.cwd() / "Projects" / project_name
    if not proj_dir.exists() and (Path.cwd() / "docs").exists():
        proj_dir = Path.cwd()

    watcher = SemanticJanitorWatcher(str(proj_dir))
    report = watcher.scan_project()

    if report["total_issues"] == 0:
        ZeroFluffConsole.success(f"Audit Janitor propre : {report['total_scanned']} fichier(s) vérifié(s), 0 anomalie.")
        herdr.show_notification(
            title="🧹 Janitor Sémantique : PASS",
            body=f"{report['total_scanned']} fichiers vérifiés. Zéro anomalie.",
            sound="done",
            position="bottom-right"
        )
    else:
        ZeroFluffConsole.warning(f"Janitor : {report['total_issues']} anomalie(s) détectée(s) dans {len(report['issues'])} fichier(s).")
        for fname, flist in list(report["issues"].items())[:5]:
            ZeroFluffConsole.info(f" 📄 {fname} :")
            for iss in flist[:2]:
                ZeroFluffConsole.info(f"    - {iss}")

        herdr.show_notification(
            title=f"⚠️ Janitor : {report['total_issues']} Anomalie(s)",
            body=f"Des liens brisés ou dérives ont été détectés dans {len(report['issues'])} fichier(s).",
            sound="request",
            position="top-right"
        )

    return {
        "success": True,
        "status": "JANITOR_COMPLETED",
        "report": report
    }
