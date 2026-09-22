"""
Architecture Analyzer Pipeline - mLoop
Scan des modules superficiels (Shallow Modules) et détection des opportunités de refactorisation (Deepening).
Génère un rapport HTML interactif.
"""

import ast
import os
from pathlib import Path
from typing import Dict, List

from src.utils.logger import get_logger

logger = get_logger("pipelines.arch_analyzer")

HTML_REPORT_TEMPLATE = """<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>mLoop Architecture Deepening Report</title>
    <style>
        body {{ font-family: system-ui, -apple-system, sans-serif; background: #0f172a; color: #f8fafc; padding: 2rem; }}
        h1 {{ color: #38bdf8; }}
        .card {{ background: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 1.5rem; margin-bottom: 1rem; }}
        .badge {{ display: inline-block; padding: 0.25rem 0.5rem; border-radius: 4px; font-weight: bold; font-size: 0.8rem; }}
        .badge-shallow {{ background: #ef4444; color: #fff; }}
        .badge-deep {{ background: #22c55e; color: #fff; }}
        code {{ background: #0f172a; padding: 0.2rem 0.4rem; border-radius: 4px; font-family: monospace; }}
    </style>
</head>
<body>
    <h1>🏗️ mLoop Architecture Deepening Report</h1>
    <p>Rapport d'analyse de la profondeur des modules (Ousterhout Metrics & Deletion Test).</p>
    
    <div id="candidates">
        {cards_html}
    </div>
</body>
</html>
"""

CARD_TEMPLATE = """
<div class="card">
    <h2><code>{file_path}</code> <span class="badge {badge_class}">{ratio_label}</span></h2>
    <p><strong>Méthodes / Fonctions publiques :</strong> {public_methods_count}</p>
    <p><strong>Lignes de code (Loc) :</strong> {loc}</p>
    <p><strong>Ratio de Profondeur (LOC / Interface) :</strong> {ratio:.1f}</p>
    <p><strong>Verdict du Test de Suppression :</strong> {deletion_test_verdict}</p>
</div>
"""


class ArchAnalyzerEngine:
    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.storage_dir = project_path / "storage" / "reports"

    def analyze_repository(self) -> List[Dict]:
        results = []
        src_dir = self.project_path / "src"
        if not src_dir.exists():
            return results

        import json

        cache_dir = self.project_path / "memory" / "cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = cache_dir / "arch_analyzer_cache.json"

        cache_data = {}
        if cache_file.exists():
            try:
                cache_data = json.loads(cache_file.read_text(encoding="utf-8"))
            except Exception as e:
                logger.debug(
                    "Lecture du cache arch_analyzer échouée, démarrage avec cache vide",
                    exc_info=True,
                    extra={
                        "component": "pipelines.arch_analyzer",
                        "operation": "cache_read",
                        "cache_file": str(cache_file),
                        "error": str(e),
                    },
                )
                cache_data = {}

        new_cache_data = {}
        for py_file in src_dir.rglob("*.py"):
            if py_file.name.startswith("__"):
                continue
            rel_p = str(py_file.relative_to(self.project_path))
            mtime = os.path.getmtime(py_file)

            cached_entry = cache_data.get(rel_p, {})
            if cached_entry.get("mtime") == mtime and "metrics" in cached_entry:
                results.append(cached_entry["metrics"])
                new_cache_data[rel_p] = cached_entry
                continue

            try:
                content = py_file.read_text(encoding="utf-8")
                tree = ast.parse(content)
                loc = len(content.splitlines())

                # Compter les définitions de fonctions et classes
                funcs = [
                    node
                    for node in ast.walk(tree)
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                ]
                public_funcs = [f for f in funcs if not f.name.startswith("_")]

                interface_size = max(1, len(public_funcs))
                ratio = loc / interface_size

                is_shallow = ratio < 15 and loc > 30
                verdict = (
                    "Module superficiel : Fusionner ou concentrer la complexité derrière une interface plus simple."
                    if is_shallow
                    else "Module profond et bien encapsulé."
                )

                metrics = {
                    "file_path": rel_p,
                    "loc": loc,
                    "public_methods_count": len(public_funcs),
                    "ratio": ratio,
                    "is_shallow": is_shallow,
                    "verdict": verdict,
                }
                results.append(metrics)
                new_cache_data[rel_p] = {"mtime": mtime, "metrics": metrics}
            except Exception as e:
                logger.debug(
                    "Analyse AST d'un module échouée, fichier ignoré",
                    exc_info=True,
                    extra={
                        "component": "pipelines.arch_analyzer",
                        "operation": "ast_parse",
                        "file": rel_p,
                        "error": str(e),
                    },
                )
                continue

        try:
            cache_file.write_text(
                json.dumps(new_cache_data, indent=2, ensure_ascii=False), encoding="utf-8"
            )
        except Exception as e:
            logger.warning(
                "Écriture du cache arch_analyzer échouée",
                exc_info=True,
                extra={
                    "component": "pipelines.arch_analyzer",
                    "operation": "cache_write",
                    "cache_file": str(cache_file),
                    "entries": len(new_cache_data),
                    "error": str(e),
                },
            )

        return results

    def generate_html_report(self) -> Path:
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        candidates = self.analyze_repository()

        cards_html = ""
        for c in candidates:
            badge_class = "badge-shallow" if c["is_shallow"] else "badge-deep"
            ratio_label = "SHALLOW MODULE" if c["is_shallow"] else "DEEP MODULE"
            cards_html += CARD_TEMPLATE.format(
                file_path=c["file_path"],
                badge_class=badge_class,
                ratio_label=ratio_label,
                public_methods_count=c["public_methods_count"],
                loc=c["loc"],
                ratio=c["ratio"],
                deletion_test_verdict=c["verdict"],
            )

        report_path = self.storage_dir / "architecture_depth.html"
        full_html = HTML_REPORT_TEMPLATE.format(cards_html=cards_html)
        report_path.write_text(full_html, encoding="utf-8")
        return report_path
