#!/usr/bin/env python3
"""
mLoop Lite Exporter — Générateur de Livrables Corporatifs Autonome
Convertit un document Markdown en HTML exécutif prêt à imprimer en PDF (Ctrl+P).
Zéro dépendance externe.
"""
import re
import html
from pathlib import Path

CSS_STYLES = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
    --primary: #1e3a8a;
    --primary-light: #3b82f6;
    --accent: #f97316;
    --text: #1f2937;
    --text-light: #4b5563;
    --bg: #f9fafb;
    --card-bg: #ffffff;
    --border: #e5e7eb;
}

body {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    line-height: 1.6;
    color: var(--text);
    background-color: var(--bg);
    margin: 0;
    padding: 2rem;
}

.container {
    max-width: 900px;
    margin: 0 auto;
    background: var(--card-bg);
    padding: 3.5rem;
    border-radius: 12px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
    border: 1px solid var(--border);
}

.header {
    border-bottom: 2px solid var(--primary-light);
    padding-bottom: 1.5rem;
    margin-bottom: 2.5rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.brand {
    font-weight: 700;
    font-size: 1.25rem;
    color: var(--primary);
    letter-spacing: -0.5px;
}

.badge {
    background: #dbeafe;
    color: #1e40af;
    padding: 0.25rem 0.75rem;
    border-radius: 9999px;
    font-size: 0.85rem;
    font-weight: 600;
}

h1 {
    font-size: 2.2rem;
    color: #111827;
    margin-top: 0;
    letter-spacing: -1px;
    line-height: 1.2;
}

h2 {
    font-size: 1.45rem;
    color: var(--primary);
    border-bottom: 1px solid var(--border);
    padding-bottom: 0.5rem;
    margin-top: 2.5rem;
}

h3 {
    font-size: 1.15rem;
    color: #374151;
    margin-top: 1.8rem;
}

p, li {
    font-size: 1rem;
    color: #374151;
}

blockquote {
    border-left: 4px solid var(--accent);
    background: #fff7ed;
    margin: 1.5rem 0;
    padding: 1rem 1.25rem;
    border-radius: 0 8px 8px 0;
    font-style: normal;
}

blockquote p {
    margin: 0;
    color: #9a3412;
}

table {
    width: 100%;
    border-collapse: collapse;
    margin: 1.5rem 0;
    font-size: 0.95rem;
}

th, td {
    padding: 0.75rem 1rem;
    text-align: left;
    border-bottom: 1px solid var(--border);
}

th {
    background: #f8fafc;
    color: #1e293b;
    font-weight: 600;
    border-top: 1px solid var(--border);
}

tr:hover {
    background-color: #f8fafc;
}

code {
    font-family: 'JetBrains Mono', monospace;
    background: #f1f5f9;
    color: #0f172a;
    padding: 0.2rem 0.4rem;
    border-radius: 4px;
    font-size: 0.88em;
}

pre {
    background: #0f172a;
    color: #f8fafc;
    padding: 1.25rem;
    border-radius: 8px;
    overflow-x: auto;
}

pre code {
    background: transparent;
    color: inherit;
    padding: 0;
}

.footer {
    margin-top: 4rem;
    padding-top: 1.5rem;
    border-top: 1px solid var(--border);
    font-size: 0.85rem;
    color: var(--text-light);
    display: flex;
    justify-content: space-between;
}

@media print {
    body { background: #fff; padding: 0; }
    .container { box-shadow: none; border: none; padding: 0; max-width: 100%; }
    .header { margin-top: 0; }
    h2 { page-break-after: avoid; }
    table, blockquote, pre { page-break-inside: avoid; }
}
"""

def markdown_to_html(md_text: str) -> str:
    # Traitement des titres
    lines = md_text.splitlines()
    html_lines = []
    in_table = False
    in_code = False
    
    for line in lines:
        # Code block
        if line.startswith("```"):
            if in_code:
                html_lines.append("</code></pre>")
                in_code = False
            else:
                html_lines.append("<pre><code>")
                in_code = True
            continue
            
        if in_code:
            html_lines.append(html.escape(line))
            continue
            
        # Tables
        if "|" in line:
            if not in_table:
                html_lines.append("<table>")
                in_table = True
            parts = [p.strip() for p in line.split("|")[1:-1]]
            if all(set(p).issubset({'-', ':', ' '}) for p in parts if p):
                continue # séparateur
            is_header = not any("<td" in l for l in html_lines[-3:]) if html_lines else True
            tag = "th" if is_header else "td"
            row = "".join(f"<{tag}>{p}</{tag}>" for p in parts)
            html_lines.append(f"<tr>{row}</tr>")
            continue
        else:
            if in_table:
                html_lines.append("</table>")
                in_table = False
                
        # Headings
        if line.startswith("# "):
            html_lines.append(f"<h1>{line[2:].strip()}</h1>")
        elif line.startswith("## "):
            html_lines.append(f"<h2>{line[3:].strip()}</h2>")
        elif line.startswith("### "):
            html_lines.append(f"<h3>{line[4:].strip()}</h3>")
        elif line.startswith("> "):
            html_lines.append(f"<blockquote><p>{line[2:].strip()}</p></blockquote>")
        elif line.startswith("* ") or line.startswith("- "):
            html_lines.append(f"<li>{line[2:].strip()}</li>")
        elif line.strip() == "---":
            html_lines.append("<hr style='border: 0; border-top: 1px solid #e5e7eb; margin: 2rem 0;'>")
        elif line.strip():
            # Formatage inline
            p_line = line
            p_line = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', p_line)
            p_line = re.sub(r'\*(.*?)\*', r'<em>\1</em>', p_line)
            p_line = re.sub(r'`(.*?)`', r'<code>\1</code>', p_line)
            html_lines.append(f"<p>{p_line}</p>")
            
    if in_table:
        html_lines.append("</table>")
    if in_code:
        html_lines.append("</code></pre>")
        
    return "\n".join(html_lines)

def export_to_html(md_file: Path, out_html_file: Path, project_name: str = "Projet Nmédia") -> Path:
    raw_md = md_file.read_text(encoding="utf-8", errors="ignore")
    body_html = markdown_to_html(raw_md)
    
    full_html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{md_file.stem} — {project_name}</title>
    <style>
        {CSS_STYLES}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="brand">Nmédia • Solutions Numériques</div>
            <div class="badge">{project_name.upper()}</div>
        </div>
        
        {body_html}
        
        <div class="footer">
            <div>Document officiel de cadrage généré via <strong>mLoop Lite</strong></div>
            <div>Imprimer ou Exporter en PDF : <code>Ctrl + P</code></div>
        </div>
    </div>
</body>
</html>
"""
    out_html_file.write_text(full_html, encoding="utf-8")
    return out_html_file
