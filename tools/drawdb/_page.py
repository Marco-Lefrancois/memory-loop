"""
tools/drawdb/_page.py — Rendu HTML du visualiseur ERD souverain (MLOOP-152-BE)

Sous-module de runner.py pour respecter ADR-0202 (≤300 lignes / module).
Génère une page 100% locale : zéro CDN, zéro host externe.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List

from tools.drawdb._discovery import REPO_ROOT

logger = logging.getLogger("drawdb.runner.page")

DEFAULT_PORT: int = 8081


def render_schema_page(dbml_files: List[Path], selected_idx: int = 0) -> str:
    """
    Génère la page HTML 100% locale du visualiseur ERD.
    Embarque les données DBML parsées directement en JSON dans la balise <script>.
    Aucune ressource externe : zéro CDN, zéro host distant.
    """
    from src.bridges.drawdb_bridge import (
        parse_dbml,
    )  # Import différé pour compatibilité CLI autonome

    # Préparer le menu de sélection
    selector_options = ""
    for i, fp in enumerate(dbml_files):
        sel = "selected" if i == selected_idx else ""
        selector_options += f'<option value="{i}" {sel}>{fp.name} ({fp.parent.name})</option>\n'

    # Parser le DBML sélectionné
    tables: List[Dict[str, Any]] = []
    parse_error: str = ""
    selected_file_label = ""

    if dbml_files:
        idx = max(0, min(selected_idx, len(dbml_files) - 1))
        sel_path = dbml_files[idx]
        selected_file_label = (
            str(sel_path.relative_to(REPO_ROOT))
            if sel_path.is_relative_to(REPO_ROOT)
            else sel_path.name
        )
        try:
            content = sel_path.read_text(encoding="utf-8", errors="replace")
            tables = parse_dbml(content)
        except Exception as exc:
            parse_error = str(exc)
            logger.debug(
                "Erreur lors du parsing DBML",
                exc_info=True,
                extra={
                    "component": "drawdb",
                    "operation": "render_schema_page",
                    "file": str(sel_path),
                    "error": str(exc),
                },
            )

    tables_json = json.dumps(tables, ensure_ascii=False)

    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>mLoop DrawDB — Visualiseur ERD Souverain</title>
    <style>
        *,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
        body{{font-family:'Segoe UI',system-ui,sans-serif;background:#0f172a;color:#f8fafc;min-height:100vh;display:flex;flex-direction:column}}
        header{{background:#1e293b;padding:.75rem 1.5rem;border-bottom:1px solid #334155;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:.5rem}}
        header h1{{font-size:1rem;color:#38bdf8;display:flex;align-items:center;gap:.5rem;font-weight:700}}
        .badge{{background:#0284c7;color:#fff;padding:.15rem .55rem;border-radius:9999px;font-size:.7rem;font-weight:700;letter-spacing:.05em}}
        .badge.sovereign{{background:#065f46;color:#6ee7b7}}
        .toolbar{{background:#1e293b;border-bottom:1px solid #334155;padding:.5rem 1.5rem;display:flex;align-items:center;gap:.75rem;flex-wrap:wrap}}
        .toolbar label{{font-size:.75rem;color:#94a3b8;font-weight:600}}
        select.schema-select{{background:#0f172a;color:#f8fafc;border:1px solid #334155;border-radius:6px;padding:.3rem .6rem;font-size:.8rem;cursor:pointer}}
        select.schema-select:focus{{outline:2px solid #0284c7;border-color:#0284c7}}
        main{{flex:1;overflow:auto;padding:1.5rem}}
        .empty-state{{display:flex;flex-direction:column;align-items:center;justify-content:center;height:60vh;gap:1rem;text-align:center;color:#64748b}}
        .empty-state .icon{{font-size:3rem}}
        .empty-state .hint{{font-size:.8rem;background:#1e293b;padding:.5rem 1rem;border-radius:6px;border:1px solid #334155;color:#94a3b8;font-family:monospace}}
        .error-banner{{background:#450a0a;border:1px solid #b91c1c;color:#fca5a5;border-radius:8px;padding:.75rem 1rem;margin-bottom:1rem;font-size:.8rem;display:flex;align-items:center;gap:.5rem}}
        .schema-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:1.25rem}}
        .table-card{{background:#1e293b;border:1px solid #334155;border-radius:12px;overflow:hidden;box-shadow:0 4px 16px rgba(0,0,0,.4)}}
        .table-card-header{{background:#0f172a;padding:.6rem 1rem;border-bottom:1px solid #334155;display:flex;align-items:center;justify-content:space-between}}
        .table-name{{font-size:.85rem;font-weight:700;color:#38bdf8;font-family:monospace}}
        .field-count{{font-size:.65rem;color:#64748b;background:#0f172a;border:1px solid #334155;border-radius:9999px;padding:.1rem .4rem}}
        .table-card table{{width:100%;border-collapse:collapse;font-size:.75rem}}
        .table-card th{{padding:.35rem .75rem;background:#0f172a;color:#64748b;text-align:left;font-weight:600;font-size:.65rem;text-transform:uppercase;letter-spacing:.05em;border-bottom:1px solid #1e293b}}
        .table-card td{{padding:.35rem .75rem;border-bottom:1px solid #1e293b;color:#cbd5e1;font-family:monospace;vertical-align:middle}}
        .table-card tr:last-child td{{border-bottom:none}}
        .table-card tr:hover td{{background:#243046}}
        .badge-pk{{background:#1d4ed8;color:#bfdbfe;font-size:.6rem;padding:.1rem .35rem;border-radius:4px;font-weight:700}}
        .badge-fk{{background:#065f46;color:#6ee7b7;font-size:.6rem;padding:.1rem .35rem;border-radius:4px;font-weight:700}}
        .badge-unique{{background:#713f12;color:#fde68a;font-size:.6rem;padding:.1rem .35rem;border-radius:4px;font-weight:700}}
        .badge-nn{{background:#374151;color:#9ca3af;font-size:.6rem;padding:.1rem .35rem;border-radius:4px;font-weight:700}}
        .fk-ref{{font-size:.65rem;color:#34d399;margin-left:.25rem}}
        .footer{{background:#1e293b;border-top:1px solid #334155;padding:.5rem 1.5rem;font-size:.7rem;color:#475569;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:.25rem}}
        .sovereign-seal{{color:#34d399;font-weight:700}}
    </style>
</head>
<body>
    <header>
        <h1><span>🗄️</span> mLoop DrawDB — Visualiseur ERD Souverain</h1>
        <div style="display:flex;gap:.5rem;align-items:center;flex-wrap:wrap">
            <span class="badge sovereign">SOUVERAIN LOCAL</span>
            <span class="badge">PORT&nbsp;{DEFAULT_PORT}</span>
        </div>
    </header>

    {
        ""
        if not dbml_files
        else f'''
    <div class="toolbar">
        <label for="schema-selector">SCHÉMA :</label>
        <select id="schema-selector" class="schema-select" onchange="switchSchema(this.value)">
            {selector_options}
        </select>
        <span id="schema-path" style="font-size:.7rem;color:#475569;font-family:monospace">{selected_file_label}</span>
    </div>
    '''
    }

    <main>
        {
        ""
        if not parse_error
        else f'<div class="error-banner"><span>⚠️</span><span>Erreur de parsing DBML : {parse_error}</span></div>'
    }

        <div id="schema-container">
            {
        ""
        if dbml_files
        else '''
            <div class="empty-state">
                <div class="icon">🗄️</div>
                <div>Aucun fichier <strong>*.dbml</strong> détecté sous <code>Projects/&lt;projet&gt;/</code></div>
                <div class="hint">Créez un fichier .dbml dans votre projet mLoop pour visualiser votre ERD ici.</div>
            </div>
            '''
    }
        </div>
    </main>

    <div class="footer">
        <span>mLoop DrawDB Runner — Visualiseur ERD 100% Local (Zéro Exfiltration)</span>
        <span class="sovereign-seal">✅ ZÉRO DÉPENDANCE EXTERNE</span>
    </div>

    <script>
        // Données embarquées : ZÉRO appel réseau sortant
        const TABLES_DATA = {tables_json};
        const DBML_FILES_COUNT = {len(dbml_files)};

        function renderBadges(field) {{
            const badges = [];
            if (field.pk)     badges.push('<span class="badge-pk">PK</span>');
            if (field.fk)     badges.push('<span class="badge-fk">FK</span>');
            if (field.unique) badges.push('<span class="badge-unique">UQ</span>');
            if (field.not_null) badges.push('<span class="badge-nn">NN</span>');
            return badges.join(' ');
        }}

        function renderFkRef(field) {{
            if (field.fk_ref && Array.isArray(field.fk_ref)) {{
                return `<span class="fk-ref">→ ${{field.fk_ref[0]}}.${{field.fk_ref[1]}}</span>`;
            }}
            return '';
        }}

        function renderSchema(tables) {{
            const container = document.getElementById('schema-container');
            if (!tables || tables.length === 0) {{
                container.innerHTML = `
                <div class="empty-state">
                    <div class="icon">📋</div>
                    <div>Aucune table trouvée dans ce fichier DBML.</div>
                    <div class="hint">Vérifiez la syntaxe : Table NomTable {{ champ type [options] }}</div>
                </div>`;
                return;
            }}
            const grid = document.createElement('div');
            grid.className = 'schema-grid';
            tables.forEach(tbl => {{
                const fieldRows = (tbl.fields || []).map(f => `
                <tr>
                    <td><strong>${{f.name}}</strong></td>
                    <td style="color:#7dd3fc">${{f.type}}</td>
                    <td>${{renderBadges(f)}}${{renderFkRef(f)}}</td>
                    <td style="color:#94a3b8;font-size:.65rem">${{f.comment || ''}}</td>
                </tr>`).join('');
                grid.innerHTML += `
                <div class="table-card">
                    <div class="table-card-header">
                        <span class="table-name">${{tbl.name}}</span>
                        <span class="field-count">${{(tbl.fields||[]).length}} champs</span>
                    </div>
                    ${{tbl.comment ? `<div style="padding:.4rem .75rem;font-size:.7rem;color:#94a3b8;border-bottom:1px solid #334155;font-style:italic">${{tbl.comment}}</div>` : ''}}
                    <table>
                        <thead><tr>
                            <th>Champ</th><th>Type</th><th>Clés</th><th>Note</th>
                        </tr></thead>
                        <tbody>${{fieldRows}}</tbody>
                    </table>
                </div>`;
            }});
            container.innerHTML = '';
            container.appendChild(grid);
        }}

        function switchSchema(idx) {{
            window.location.href = '/?schema=' + idx;
        }}

        // Rendu initial avec les données pré-embarquées
        renderSchema(TABLES_DATA);
    </script>
</body>
</html>"""
