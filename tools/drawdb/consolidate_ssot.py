import re
from pathlib import Path

models_dir = Path(r"Projects/BoireFrere_Segment2/docs/03-models")
modules = [
    ("00-core", "modele-referentiels.md", "2. RÉFÉRENTIELS OPÉRATIONNELS & ÉLEVAGE (CORE)"),
    ("01-reception", "modele-reception.md", "3. RÉCEPTION, CABANES & INSPECTIONS (MODULE 01)"),
    ("02-incubation", "modele-incubation.md", "4. INCUBATION, ÉCLOSOIRS & LOTS (MODULE 02)"),
    ("03-ventes", "modele-ventes.md", "5. VENTES, EXPÉDITIONS & COMMANDES (MODULE 03)"),
    ("04-inventaire", "modele-inventaire.md", "6. INVENTAIRE TRANSACTIONNEL & TRAÇABILITÉ (MODULE 04)")
]

all_enums = {}
sections = []
seen_tables = set()

for mod_dir, fname, sec_title in modules:
    p = models_dir / mod_dir / fname
    content = p.read_text(encoding="utf-8")
    
    for em in re.finditer(r'Enum\s+([A-Za-z0-9_]+)\s*\{(.*?)\}', content, re.DOTALL):
        ename = em.group(1)
        ebody = em.group(2).strip()
        if ename not in all_enums:
            all_enums[ename] = ebody
            
    tables_in_module = []
    for tm in re.finditer(r'Table\s+([A-Za-z0-9_]+)\s*\{(.*?)\}', content, re.DOTALL):
        tname = tm.group(1)
        if tname in seen_tables:
            continue
        seen_tables.add(tname)
        full_table = f"Table {tname} {{{tm.group(2)}}}"
        tables_in_module.append(full_table)
    
    sections.append((sec_title, tables_in_module))

dbml_parts = [
    "// ==========================================",
    "// 1. ENUMS GLOBAUX",
    "// =========================================="
]
for ename, ebody in all_enums.items():
    dbml_parts.append(f"Enum {ename} {{\n  {ebody}\n}}\n")

for sec_title, tbls in sections:
    dbml_parts.append("// ==========================================")
    dbml_parts.append(f"// {sec_title}")
    dbml_parts.append("// ==========================================\n")
    for tbl in tbls:
        dbml_parts.append(tbl + "\n")

consolidated_dbml = "\n".join(dbml_parts)

header = """---
title: "Structure de Données Globale (SSOT Modèles)"
summary: "Index et schéma DBML consolidé couvrant les 5 modules clés SIGPA : Référentiels (00), Réception & Cabanes (01), Incubation (02), Ventes (03) et Inventaire Transactionnel (04)."
document_type: "architecture_data_model"
tags: ["model", "dbml", "mermaid", "ssot", "sigpa", "drawdb"]
---

# Structure de Données Globale — SIGPA (Version de Travail SSOT)

Ce document constitue la source unique de vérité (SSOT) des modèles de données physiques et logiques du projet SIGPA (Segment 2) consolidant les **32 tables** et **31 relations**.

Pour les détails spécifiques et diagrammes Mermaid par domaine, consultez :
- 📂 [Modèle Référentiels Opérationnels (`00-core/`)](file:///C:/Memory%20Loop/Projects/BoireFrere_Segment2/docs/03-models/00-core/modele-referentiels.md)
- 📂 [Modèle Réception & Cabanes (`01-reception/`)](file:///C:/Memory%20Loop/Projects/BoireFrere_Segment2/docs/03-models/01-reception/modele-reception.md)
- 📂 [Modèle Incubation & Éclosoirs (`02-incubation/`)](file:///C:/Memory%20Loop/Projects/BoireFrere_Segment2/docs/03-models/02-incubation/modele-incubation.md)
- 📂 [Modèle Ventes & Expéditions (`03-ventes/`)](file:///C:/Memory%20Loop/Projects/BoireFrere_Segment2/docs/03-models/03-ventes/modele-ventes.md)
- 📂 [Modèle Inventaire Transactionnel (`04-inventaire/`)](file:///C:/Memory%20Loop/Projects/BoireFrere_Segment2/docs/03-models/04-inventaire/modele-inventaire.md)
- 📄 [Schéma DrawDB Importable (`schema_drawdb.json`)](file:///C:/Memory%20Loop/Projects/BoireFrere_Segment2/docs/03-models/schema_drawdb.json)

---

## Modèle DBML Consolidé (32 Tables, 5 Modules)

```dbml
"""

footer = "```\n"

full_file_content = header + consolidated_dbml.strip() + "\n" + footer

target_file = models_dir / "Structure-de-données.md"
target_file.write_text(full_file_content, encoding="utf-8")
print(f"Structure-de-données.md mis à jour avec {len(seen_tables)} tables.")
