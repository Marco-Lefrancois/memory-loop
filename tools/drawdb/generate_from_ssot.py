import json
import re
from pathlib import Path
from src.bridges.drawdb_bridge import parse_dbml, mloop_tables_to_drawdb

SSOT_PATH = Path(r"C:\Memory Loop\Projects\BoireFrere_Segment2\reference\Structure-de-données.md")
OUT_HTML = Path(r"C:\Memory Loop\tools\drawdb\static\index.html")

def build_visualizer():
    raw_content = SSOT_PATH.read_text(encoding="utf-8")
    
    # 1. Extraire les tables
    tables = parse_dbml(raw_content)
    tables_by_name = {t["name"]: t for t in tables}
    
    # Définition des modules métiers de la SSOT officielle
    ssot_modules = [
        ("all", "🌐 Vue d'ensemble", list(tables_by_name.keys())),
        ("incubation", "🥚 Incubation & Setter", ["Setter", "IncubationAssignment", "InventoryLot"]),
        ("reception", "🚚 Réception & Désinfection", ["SanitizationChamber", "InstanceDesinfection", "Reception", "ReceptionLot", "InspectionType", "Inspection", "InspectionIssue"]),
        ("inventaire", "📊 Inventaire & Traçabilité", ["InventoryLot", "InventoryTransaction", "Logs"])
    ]

    # Convertir en JSON drawDB
    drawdb_json = mloop_tables_to_drawdb(tables, title="Boire Frères - SIGPA Segment 2 (SSOT 2026-07-15)")

    color_map = {
        'Setter': '#38bdf8',
        'IncubationAssignment': '#38bdf8',
        'InventoryLot': '#10b981',
        'InventoryTransaction': '#059669',
        'SanitizationChamber': '#8b5cf6',
        'InstanceDesinfection': '#a855f7',
        'Reception': '#f59e0b',
        'ReceptionLot': '#d97706',
        'Inspection': '#ec4899',
        'InspectionType': '#f43f5e',
        'InspectionIssue': '#e11d48',
        'Logs': '#64748b'
    }

    tables_data = []
    for t in tables:
        tname = t["name"]
        color = color_map.get(tname, "#38bdf8")
        fields = []
        for f in t.get("fields", []):
            fields.append({
                "name": f["name"],
                "type": f["type"],
                "pk": f.get("pk", False),
                "fk": f.get("fk", False),
                "notNull": f.get("not_null", False),
                "unique": f.get("unique", False),
                "comment": f.get("comment", "")
            })
        tables_data.append({
            "name": tname,
            "color": color,
            "fields": fields
        })

    # Relations globales de la SSOT
    all_relations = [
        ("Setter", "IncubationAssignment", "SetterId"),
        ("InventoryLot", "IncubationAssignment", "lotId"),
        ("InventoryLot", "InventoryTransaction", "lotId"),
        ("SanitizationChamber", "InstanceDesinfection", "cabane_id"),
        ("InstanceDesinfection", "Reception", "sanitizationInstanceId"),
        ("Reception", "ReceptionLot", "receptionId"),
        ("InventoryLot", "ReceptionLot", "InventoryLotId"),
        ("Reception", "Inspection", "receptionId"),
        ("Inspection", "InspectionIssue", "inspectionId"),
        ("InspectionType", "InspectionIssue", "inspectionTypeId")
    ]

    # Générer le Mermaid pour chaque module
    diagrams = {}
    for mod_key, mod_title, mod_tables in ssot_modules:
        lines = ["erDiagram"]
        # Filtrer les relations dont les 2 tables sont dans le module
        for src, dst, lbl in all_relations:
            if src in mod_tables and dst in mod_tables:
                lines.append(f'    {src} ||--o{ dst} : "{lbl}"')
        
        # Ajouter les tables
        for tname in mod_tables:
            if tname in tables_by_name:
                t = tables_by_name[tname]
                lines.append(f"    {tname} {{")
                for f in t.get("fields", []):
                    pk_str = " PK" if f.get("pk") else ""
                    fk_str = " FK" if f.get("fk") else ""
                    cleaned_type = f["type"].replace(" ", "_").replace("(", "_").replace(")", "_")
                    comment_str = f' "{f.get("comment")}"' if f.get("comment") else ""
                    lines.append(f"        {cleaned_type} {f['name']}{pk_str}{fk_str}{comment_str}")
                lines.append("    }")
        diagrams[mod_key] = {
            "title": mod_title,
            "code": "\n".join(lines)
        }

    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>mLoop Sovereign ERD & Database Hub — Boire Frères SSOT</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;600&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    
    <!-- Mermaid CDN -->
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
    <script>
        mermaid.initialize({{
            startOnLoad: false,
            theme: 'dark',
            themeVariables: {{
                darkMode: true,
                background: '#0b0f19',
                primaryColor: '#1e293b',
                primaryTextColor: '#f8fafc',
                primaryBorderColor: '#38bdf8',
                lineColor: '#94a3b8',
                secondaryColor: '#151d2f',
                tertiaryColor: '#0f172a'
            }},
            er: {{
                useMaxWidth: false,
                entityPadding: 15,
                stroke: '#38bdf8',
                fill: '#151d2f'
            }}
        }});
    </script>

    <style>
        :root {{
            --bg-main: #0b0f19;
            --bg-card: #151d2f;
            --bg-card-header: #1e293b;
            --border-color: #334155;
            --accent-primary: #38bdf8;
            --accent-emerald: #10b981;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --pk-badge: #e11d48;
            --fk-badge: #3b82f6;
        }}

        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: 'Inter', system-ui, -apple-system, sans-serif;
            background-color: var(--bg-main);
            color: var(--text-main);
            height: 100vh;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }}

        /* HEADER */
        header {{
            background: #0f172a;
            padding: 0.75rem 1.5rem;
            border-bottom: 1px solid var(--border-color);
            display: flex;
            justify-content: space-between;
            align-items: center;
            z-index: 100;
        }}
        .header-title {{
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }}
        .header-title h1 {{
            font-size: 1.15rem;
            font-weight: 700;
            color: var(--accent-primary);
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}
        .badge {{
            background: #0369a1;
            color: #e0f2fe;
            padding: 0.2rem 0.6rem;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 600;
        }}
        .badge-ssot {{
            background: #064e3b;
            color: #6ee7b7;
            border: 1px solid #059669;
        }}
        .header-actions {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}
        .btn {{
            background: #1e293b;
            color: var(--text-main);
            border: 1px solid var(--border-color);
            padding: 0.45rem 0.9rem;
            border-radius: 6px;
            font-size: 0.8rem;
            font-weight: 600;
            cursor: pointer;
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            transition: all 0.15s ease;
        }}
        .btn:hover {{
            background: #334155;
            border-color: #64748b;
        }}
        .btn-emerald {{
            background: #059669;
            border-color: #047857;
            color: white;
        }}
        .btn-emerald:hover {{
            background: #047857;
        }}

        /* MODE SWITCH BAR */
        .mode-switch-bar {{
            background: #131d31;
            padding: 0.5rem 1.5rem;
            border-bottom: 1px solid var(--border-color);
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 1rem;
        }}
        .mode-toggles {{
            display: flex;
            gap: 0.5rem;
            background: #0b0f19;
            padding: 0.25rem;
            border-radius: 8px;
            border: 1px solid var(--border-color);
        }}
        .mode-btn {{
            background: none;
            border: none;
            color: var(--text-muted);
            padding: 0.45rem 1rem;
            border-radius: 6px;
            font-size: 0.82rem;
            font-weight: 600;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            transition: all 0.15s ease;
        }}
        .mode-btn:hover {{
            color: white;
        }}
        .mode-btn.active {{
            background: #0284c7;
            color: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.3);
        }}

        /* DROPDOWN SELECT POUR MODULES ERD */
        .erd-module-selector-box {{
            display: flex;
            align-items: center;
            gap: 0.6rem;
            background: #0b0f19;
            padding: 0.25rem 0.75rem;
            border-radius: 8px;
            border: 1px solid var(--border-color);
        }}
        .erd-module-selector-label {{
            font-size: 0.78rem;
            font-weight: 600;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            display: flex;
            align-items: center;
            gap: 0.3rem;
        }}
        .erd-select {{
            background: #1e293b;
            color: #38bdf8;
            border: 1px solid var(--border-color);
            padding: 0.4rem 0.8rem;
            border-radius: 6px;
            font-size: 0.84rem;
            font-weight: 600;
            cursor: pointer;
            outline: none;
            transition: all 0.15s ease;
        }}
        .erd-select:hover, .erd-select:focus {{
            border-color: #38bdf8;
            box-shadow: 0 0 10px rgba(56, 189, 248, 0.25);
        }}
        .erd-select option {{
            background: #0f172a;
            color: #f8fafc;
            padding: 0.4rem;
        }}

        /* WORKSPACE */
        .main-workspace {{
            flex: 1;
            display: flex;
            overflow: hidden;
            position: relative;
        }}

        /* 1. VUE RELATIONNELLE MERMAID */
        .relation-view {{
            display: flex;
            flex: 1;
            flex-direction: column;
            overflow: auto;
            position: relative;
            background-color: #0b0f19;
            background-image: radial-gradient(circle, #1e293b 1px, transparent 1px);
            background-size: 24px 24px;
        }}
        .canvas-toolbar {{
            position: absolute;
            top: 1rem;
            right: 1.5rem;
            z-index: 50;
            display: flex;
            gap: 0.5rem;
            background: rgba(15, 23, 42, 0.85);
            backdrop-filter: blur(8px);
            padding: 0.4rem;
            border-radius: 8px;
            border: 1px solid var(--border-color);
        }}
        .tool-btn {{
            background: #1e293b;
            color: white;
            border: 1px solid var(--border-color);
            padding: 0.3rem 0.6rem;
            border-radius: 4px;
            font-size: 0.8rem;
            cursor: pointer;
        }}
        .tool-btn:hover {{
            background: #334155;
        }}
        .diagram-wrapper {{
            flex: 1;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 3rem 2rem;
            min-height: 100%;
            transform-origin: center center;
            transition: transform 0.1s ease;
        }}
        #mermaidContainer {{
            display: flex;
            justify-content: center;
            align-items: center;
            width: 100%;
        }}

        /* 2. VUE CARTES */
        .cards-view {{
            display: none;
            flex: 1;
            overflow: hidden;
        }}
        .sidebar {{
            width: 280px;
            background: #0f172a;
            border-right: 1px solid var(--border-color);
            display: flex;
            flex-direction: column;
            flex-shrink: 0;
        }}
        .sidebar-search {{
            padding: 0.75rem;
            border-bottom: 1px solid var(--border-color);
        }}
        .search-input {{
            width: 100%;
            background: #1e293b;
            border: 1px solid var(--border-color);
            padding: 0.5rem 0.75rem;
            border-radius: 6px;
            color: var(--text-main);
            font-size: 0.82rem;
            outline: none;
        }}
        .sidebar-list {{
            flex: 1;
            overflow-y: auto;
            padding: 0.5rem;
        }}
        .sidebar-item {{
            padding: 0.5rem 0.75rem;
            margin-bottom: 0.25rem;
            border-radius: 6px;
            font-size: 0.8rem;
            font-weight: 500;
            color: var(--text-muted);
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}
        .sidebar-item:hover {{
            background: #1e293b;
            color: var(--text-main);
        }}
        .cards-content {{
            flex: 1;
            overflow-y: auto;
            padding: 1.5rem;
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
            gap: 1.25rem;
            align-content: start;
        }}
        .db-card {{
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
            display: flex;
            flex-direction: column;
        }}
        .db-card-header {{
            background: var(--bg-card-header);
            padding: 0.6rem 0.9rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid var(--border-color);
        }}
        .db-card-title {{
            font-size: 0.85rem;
            font-weight: 700;
            color: var(--text-main);
            display: flex;
            align-items: center;
            gap: 0.4rem;
        }}
        .db-card-body {{
            padding: 0.25rem 0;
            display: flex;
            flex-direction: column;
        }}
        .db-row {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.35rem 0.9rem;
            font-size: 0.78rem;
            font-family: 'Fira Code', monospace;
            border-bottom: 1px solid rgba(51, 65, 85, 0.4);
        }}
        .db-row:last-child {{
            border-bottom: none;
        }}
        .field-meta {{
            display: flex;
            align-items: center;
            gap: 0.35rem;
        }}
        .field-name {{
            color: #f1f5f9;
        }}
        .field-type {{
            color: #38bdf8;
            font-size: 0.75rem;
        }}
        .badge-mini {{
            padding: 0.1rem 0.3rem;
            border-radius: 3px;
            font-size: 0.65rem;
            font-weight: 700;
        }}
        .badge-pk {{
            background: var(--pk-badge);
            color: white;
        }}
        .badge-fk {{
            background: var(--fk-badge);
            color: white;
        }}

        /* 3. VUE CODE */
        .code-view {{
            display: none;
            flex: 1;
            overflow: auto;
            padding: 1.5rem;
            background: #070a13;
        }}
        pre {{
            font-family: 'Fira Code', monospace;
            font-size: 0.85rem;
            line-height: 1.5;
            color: #e2e8f0;
        }}

        /* 4. VUE ONLINE DRAWDB */
        .online-view {{
            display: none;
            width: 100%;
            height: 100%;
            flex-direction: column;
        }}
        iframe {{
            width: 100%;
            height: 100%;
            border: none;
        }}

        /* TOAST */
        .toast {{
            position: fixed;
            bottom: 2rem;
            right: 2rem;
            background: #0284c7;
            color: white;
            padding: 0.75rem 1.25rem;
            border-radius: 8px;
            font-weight: 600;
            font-size: 0.85rem;
            box-shadow: 0 10px 15px -3px rgba(0,0,0,0.5);
            display: none;
            z-index: 1000;
        }}
    </style>
</head>
<body>
    <header>
        <div class="header-title">
            <h1><span>🎨</span> mLoop Database & ERD Hub</h1>
            <span class="badge">Boire Frères — SIGPA</span>
            <span class="badge badge-ssot">SSOT 2026-07-15 ({len(tables)} Tables Officielles)</span>
        </div>
        <div class="header-actions">
            <button class="btn btn-emerald" onclick="copyActiveCode()">📋 Copier le Schéma Actif</button>
            <button class="btn" onclick="copyDbml()">📑 Copier DBML SSOT</button>
            <a href="https://www.drawdb.app/editor" target="_blank" class="btn" style="background:#0284c7; color:white;">🚀 Ouvrir drawdb.app ↗</a>
        </div>
    </header>

    <div class="mode-switch-bar">
        <div class="mode-toggles">
            <button class="mode-btn active" id="btnModeGraph" onclick="switchMainMode('graph')">
                <span>🕸️</span> Diagramme Relationnel (ERD)
            </button>
            <button class="mode-btn" id="btnModeCards" onclick="switchMainMode('cards')">
                <span>🎴</span> Vue Dictionnaire & Colonnes
            </button>
            <button class="mode-btn" id="btnModeDbml" onclick="switchMainMode('dbml')">
                <span>📜</span> Source DBML SSOT
            </button>
            <button class="mode-btn" id="btnModeJson" onclick="switchMainMode('json')">
                <span>⚙️</span> JSON drawDB
            </button>
            <button class="mode-btn" id="btnModeOnline" onclick="switchMainMode('online')">
                <span>🌐</span> Éditeur Web drawDB
            </button>
        </div>

        <!-- DROPDOWN SÉLECTEUR DE MODULE SSOT -->
        <div id="graphDropdownContainer" class="erd-module-selector-box">
            <span class="erd-module-selector-label"><span>📌</span> Module SSOT :</span>
            <select id="erdModuleSelect" class="erd-select" onchange="onModuleDropdownChange(this.value)">
                <option value="all" selected>🌐 Vue d'ensemble (Toutes les tables SSOT)</option>
                <option value="incubation">🥚 Incubation & Setter</option>
                <option value="reception">🚚 Réception & Désinfection</option>
                <option value="inventaire">📊 Inventaire & Traçabilité</option>
            </select>
        </div>
    </div>

    <div class="main-workspace">
        <!-- VUE 1 : GRAPHE DE RELATIONS MERMAID -->
        <div class="relation-view" id="viewGraph">
            <div class="canvas-toolbar">
                <button class="tool-btn" onclick="zoomIn()">➕ Zoom +</button>
                <button class="tool-btn" onclick="zoomOut()">➖ Zoom -</button>
                <button class="tool-btn" onclick="resetZoom()">🔄 Réinitialiser</button>
            </div>
            <div class="diagram-wrapper" id="diagramWrapper">
                <div id="mermaidContainer"></div>
            </div>
        </div>

        <!-- VUE 2 : GRILLE DE CARTES -->
        <div class="cards-view" id="viewCards">
            <div class="sidebar">
                <div class="sidebar-search">
                    <input type="text" id="searchInput" class="search-input" placeholder="Filtrer les tables..." onkeyup="filterCards()">
                </div>
                <div class="sidebar-list" id="sidebarList"></div>
            </div>
            <div class="cards-content" id="cardsGrid"></div>
        </div>

        <!-- VUE 3 : DBML -->
        <div class="code-view" id="viewDbml">
            <pre><code id="dbmlCode"></code></pre>
        </div>

        <!-- VUE 4 : JSON DRAWDB -->
        <div class="code-view" id="viewJson">
            <pre><code id="jsonCode"></code></pre>
        </div>

        <!-- VUE 5 : ONLINE DRAWDB -->
        <div class="online-view" id="viewOnline">
            <iframe src="https://www.drawdb.app/editor" title="drawDB Web Editor"></iframe>
        </div>
    </div>

    <div class="toast" id="toast">Notification</div>

    <script>
        const DIAGRAMS = {json.dumps(diagrams, ensure_ascii=False)};
        const RAW_DBML = {json.dumps(raw_content, ensure_ascii=False)};
        const TABLES_DATA = {json.dumps(tables_data, ensure_ascii=False)};
        const RAW_DRAWDB_JSON = {json.dumps(json.dumps(drawdb_json, ensure_ascii=False, indent=2))};

        let currentZoom = 1.0;
        let activeMainMode = "graph";
        let currentModule = "all";

        function switchMainMode(mode) {{
            activeMainMode = mode;
            
            document.querySelectorAll(".mode-btn").forEach(b => b.classList.remove("active"));
            const activeBtn = document.getElementById("btnMode" + mode.charAt(0).toUpperCase() + mode.slice(1));
            if (activeBtn) activeBtn.classList.add("active");

            document.getElementById("viewGraph").style.display = "none";
            document.getElementById("viewCards").style.display = "none";
            document.getElementById("viewDbml").style.display = "none";
            document.getElementById("viewJson").style.display = "none";
            document.getElementById("viewOnline").style.display = "none";

            const dropdownContainer = document.getElementById("graphDropdownContainer");

            if (mode === "graph") {{
                document.getElementById("viewGraph").style.display = "flex";
                if (dropdownContainer) dropdownContainer.style.display = "flex";
                selectDiagram(currentModule);
            }} else if (mode === "cards") {{
                document.getElementById("viewCards").style.display = "flex";
                if (dropdownContainer) dropdownContainer.style.display = "none";
                renderCardsUI();
            }} else if (mode === "dbml") {{
                document.getElementById("viewDbml").style.display = "block";
                if (dropdownContainer) dropdownContainer.style.display = "none";
                document.getElementById("dbmlCode").innerText = RAW_DBML;
            }} else if (mode === "json") {{
                document.getElementById("viewJson").style.display = "block";
                if (dropdownContainer) dropdownContainer.style.display = "none";
                document.getElementById("jsonCode").innerText = RAW_DRAWDB_JSON;
            }} else if (mode === "online") {{
                document.getElementById("viewOnline").style.display = "flex";
                if (dropdownContainer) dropdownContainer.style.display = "none";
            }}
        }}

        function onModuleDropdownChange(modKey) {{
            selectDiagram(modKey);
        }}

        function selectDiagram(modKey) {{
            currentModule = modKey;
            const selectEl = document.getElementById("erdModuleSelect");
            if (selectEl && selectEl.value !== modKey) {{
                selectEl.value = modKey;
            }}
            resetZoom();
            if (DIAGRAMS[modKey]) {{
                renderMermaid(DIAGRAMS[modKey].code);
            }}
        }}

        async function renderMermaid(code) {{
            const container = document.getElementById("mermaidContainer");
            container.innerHTML = "";
            try {{
                const id = "erd-" + Math.random().toString(36).substring(2, 9);
                const {{ svg }} = await mermaid.render(id, code);
                container.innerHTML = svg;
            }} catch (err) {{
                console.error("Erreur de rendu Mermaid :", err);
                container.innerHTML = "<div style='color:#f87171; padding:2rem;'>Erreur de rendu du schéma relationnel.</div>";
            }}
        }}

        function renderCardsUI() {{
            const sidebar = document.getElementById("sidebarList");
            const grid = document.getElementById("cardsGrid");
            sidebar.innerHTML = "";
            grid.innerHTML = "";

            TABLES_DATA.forEach(tbl => {{
                const item = document.createElement("div");
                item.className = "sidebar-item";
                item.id = `sidebar-item-${{tbl.name}}`;
                item.onclick = () => {{
                    const el = document.getElementById(`card-${{tbl.name}}`);
                    if (el) el.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                }};
                item.innerHTML = `<span>${{tbl.name}}</span><span style="font-size:0.7rem; color:var(--text-muted);">${{tbl.fields.length}} col.</span>`;
                sidebar.appendChild(item);

                const card = document.createElement("div");
                card.className = "db-card";
                card.id = `card-${{tbl.name}}`;
                card.style.borderTop = `3px solid ${{tbl.color}}`;

                let rowsHtml = "";
                tbl.fields.forEach(f => {{
                    let badges = "";
                    if (f.pk) badges += '<span class="badge-mini badge-pk">PK</span> ';
                    if (f.fk) badges += '<span class="badge-mini badge-fk">FK</span> ';
                    const comment = f.comment ? `<span style="font-size:0.7rem; color:#94a3b8; display:block; margin-top:2px;">// ${{f.comment}}</span>` : '';
                    rowsHtml += `
                        <div class="db-row">
                            <div class="field-meta">
                                ${{badges}}
                                <div>
                                    <span class="field-name">${{f.name}}</span>
                                    ${{comment}}
                                </div>
                            </div>
                            <span class="field-type">${{f.type}}</span>
                        </div>
                    `;
                }});

                card.innerHTML = `
                    <div class="db-card-header">
                        <div class="db-card-title">
                            <span style="display:inline-block; width:8px; height:8px; border-radius:50%; background:${{tbl.color}};"></span>
                            ${{tbl.name}}
                        </div>
                        <span style="font-size:0.72rem; color:var(--text-muted);">${{tbl.fields.length}} col.</span>
                    </div>
                    <div class="db-card-body">
                        ${{rowsHtml}}
                    </div>
                `;
                grid.appendChild(card);
            }});
        }}

        function filterCards() {{
            const q = document.getElementById("searchInput").value.toLowerCase();
            TABLES_DATA.forEach(tbl => {{
                const match = tbl.name.toLowerCase().includes(q) || tbl.fields.some(f => f.name.toLowerCase().includes(q));
                const item = document.getElementById(`sidebar-item-${{tbl.name}}`);
                const card = document.getElementById(`card-${{tbl.name}}`);
                if (item) item.style.display = match ? "flex" : "none";
                if (card) card.style.display = match ? "flex" : "none";
            }});
        }}

        function zoomIn() {{
            currentZoom += 0.15;
            applyZoom();
        }}
        function zoomOut() {{
            if (currentZoom > 0.3) {{
                currentZoom -= 0.15;
                applyZoom();
            }}
        }}
        function resetZoom() {{
            currentZoom = 1.0;
            applyZoom();
        }}
        function applyZoom() {{
            const wrapper = document.getElementById("diagramWrapper");
            if (wrapper) wrapper.style.transform = `scale(${{currentZoom}})`;
        }}

        function showToast(msg) {{
            const t = document.getElementById("toast");
            t.innerText = msg;
            t.style.display = "block";
            setTimeout(() => {{ t.style.display = "none"; }}, 2500);
        }}

        function copyActiveCode() {{
            if (activeMainMode === "graph") {{
                const currentCode = DIAGRAMS[currentModule] ? DIAGRAMS[currentModule].code : "";
                navigator.clipboard.writeText(currentCode).then(() => showToast("✅ Code Mermaid copié !"));
            }} else if (activeMainMode === "json") {{
                navigator.clipboard.writeText(RAW_DRAWDB_JSON).then(() => showToast("✅ JSON drawDB copié !"));
            }} else {{
                navigator.clipboard.writeText(RAW_DBML).then(() => showToast("✅ Code DBML copié !"));
            }}
        }}

        function copyDbml() {{
            navigator.clipboard.writeText(RAW_DBML).then(() => showToast("✅ DBML SSOT copié !"));
        }}

        window.onload = () => {{
            selectDiagram("all");
        }};
    </script>
</body>
</html>
"""
    OUT_HTML.write_text(html, encoding="utf-8")
    print(f"Visualizer SSOT avec dropdown restauré généré avec succès.")

if __name__ == "__main__":
    build_visualizer()
