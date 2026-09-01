"""
drawDB Bridge for mLoop Framework.
Provides bidirectional conversion between mLoop Data Model Markdown files / SQL DDL and drawDB JSON schema format.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional

DRAWDB_VERSION = "1.0.0"

def parse_dbml(content: str) -> List[Dict[str, Any]]:
    """
    Parse DBML (Database Markup Language) syntax into mLoop table dictionaries.
    """
    tables = []
    table_matches = re.finditer(r'Table\s+([A-Za-z0-9_]+)\s*\{(.*?)\}', content, re.DOTALL)
    for tm in table_matches:
        tbl_name = tm.group(1)
        body = tm.group(2)
        
        current_table = {
            "name": tbl_name,
            "comment": "",
            "fields": []
        }
        
        for raw_line in body.splitlines():
            line = raw_line.strip()
            if not line or line.startswith("//") or line.startswith("#"):
                continue
            
            parts = line.split(maxsplit=2)
            if len(parts) >= 2:
                f_name = parts[0]
                f_type = parts[1]
                opts_str = parts[2] if len(parts) > 2 else ""
                
                is_pk = "pk" in opts_str.lower()
                is_not_null = "not null" in opts_str.lower()
                is_unique = "unique" in opts_str.lower()
                
                fk_ref = None
                is_fk = False
                ref_match = re.search(r'ref:\s*>\s*([A-Za-z0-9_]+)\.([A-Za-z0-9_]+)', opts_str, re.IGNORECASE)
                if ref_match:
                    is_fk = True
                    fk_ref = (ref_match.group(1), ref_match.group(2))
                elif "ref:" in opts_str.lower():
                    is_fk = True
                
                note_str = ""
                note_match = re.search(r'note:\s*["\'](.*?)["\']', opts_str, re.IGNORECASE)
                if note_match:
                    note_str = note_match.group(1)
                
                current_table["fields"].append({
                    "name": f_name,
                    "type": f_type,
                    "pk": is_pk,
                    "fk": is_fk,
                    "fk_ref": fk_ref,
                    "not_null": is_not_null,
                    "unique": is_unique,
                    "comment": note_str
                })
        
        tables.append(current_table)
    return tables


def parse_markdown_models(md_content: str) -> List[Dict[str, Any]]:
    """
    Parse mLoop Markdown text or DBML containing data model definitions.
    """
    # If DBML syntax is present, parse DBML tables
    if "Table " in md_content and "{" in md_content:
        dbml_tables = parse_dbml(md_content)
        if dbml_tables:
            return dbml_tables

    tables = []
    current_table = None

    lines = md_content.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Check for table header
        table_match = re.match(r'^#{2,4}\s+(?:Table\s*:\s*)?([A-Za-z0-9_]+)', line, re.IGNORECASE)
        if table_match:
            table_name = table_match.group(1)
            # Avoid matching non-table headings like "Description" or "Vue d'ensemble"
            if table_name.lower() not in ["description", "vue", "overview", "notes", "relations", "contexte"]:
                current_table = {
                    "name": table_name,
                    "comment": "",
                    "fields": [],
                    "relationships": []
                }
                tables.append(current_table)

        # Check for table comment/description line right after heading
        elif current_table and (line.startswith("Description:") or line.startswith("Comment:")):
            current_table["comment"] = line.split(":", 1)[1].strip()

        # Check for Markdown table start
        elif current_table and line.startswith("|") and "---" not in line:
            # Check if this looks like a header line containing field/type/key
            headers = [h.strip().lower() for h in line.strip("|").split("|")]
            if any(h in ["champ", "field", "colonne", "column", "name", "nom"] for h in headers):
                # Process table rows
                i += 1
                while i < len(lines):
                    row_line = lines[i].strip()
                    if not row_line.startswith("|"):
                        break
                    if "---" in row_line:
                        i += 1
                        continue
                    
                    cells = [c.strip() for c in row_line.strip("|").split("|")]
                    if len(cells) >= 2:
                        field_name = cells[0]
                        field_type = cells[1] if len(cells) > 1 else "VARCHAR(255)"
                        raw_key = cells[2] if len(cells) > 2 else ""
                        key_type = raw_key.upper()
                        nullable_str = cells[3].lower() if len(cells) > 3 else "oui"
                        comment = cells[4] if len(cells) > 4 else ""

                        is_pk = "PK" in key_type or "PRIMARY" in key_type
                        is_fk = "FK" in key_type or "FOREIGN" in key_type
                        not_null = nullable_str in ["non", "no", "false", "0", "not null"]

                        # Check if foreign key reference is declared in key_type e.g. FK(Roles.id)
                        fk_ref = None
                        fk_match = re.search(r'FK\s*\(\s*([A-Za-z0-9_]+)\.([A-Za-z0-9_]+)\s*\)', raw_key, re.IGNORECASE)
                        if fk_match:
                            fk_ref = (fk_match.group(1), fk_match.group(2))

                        current_table["fields"].append({
                            "name": field_name,
                            "type": field_type if field_type else "VARCHAR(255)",
                            "pk": is_pk,
                            "fk": is_fk,
                            "fk_ref": fk_ref,
                            "not_null": not_null,
                            "unique": "UNIQUE" in key_type,
                            "comment": comment
                        })
                    i += 1
                continue
        i += 1

    return tables


def parse_sql_ddl(sql_content: str) -> List[Dict[str, Any]]:
    """
    Parse simple SQL DDL CREATE TABLE statements into mLoop table dictionaries.
    """
    tables = []
    # Find CREATE TABLE statements
    table_matches = re.finditer(r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?([`"]?([A-Za-z0-9_]+)[`"]?)\s*\((.*?)\);', sql_content, re.DOTALL | re.IGNORECASE)
    
    for tm in table_matches:
        table_name = tm.group(2)
        body = tm.group(3)

        current_table = {
            "name": table_name,
            "comment": "",
            "fields": [],
            "relationships": []
        }

        # Process lines in body
        for raw_line in body.splitlines():
            line = raw_line.strip().rstrip(',')
            if not line or line.upper().startswith("CONSTRAINT") or line.upper().startswith("PRIMARY KEY") or line.upper().startswith("FOREIGN KEY"):
                # Handle foreign key constraints if defined at table level
                fk_match = re.search(r'FOREIGN\s+KEY\s*\(([`"]?[A-Za-z0-9_]+[`"]?)\)\s*REFERENCES\s+([`"]?[A-Za-z0-9_]+[`"]?)\s*\(([`"]?[A-Za-z0-9_]+[`"]?)\)', line, re.IGNORECASE)
                if fk_match:
                    local_col = fk_match.group(1).replace('`', '').replace('"', '')
                    ref_table = fk_match.group(2).replace('`', '').replace('"', '')
                    ref_col = fk_match.group(3).replace('`', '').replace('"', '')
                    for f in current_table["fields"]:
                        if f["name"] == local_col:
                            f["fk"] = True
                            f["fk_ref"] = (ref_table, ref_col)
                continue

            parts = line.split()
            if len(parts) >= 2:
                field_name = parts[0].replace('`', '').replace('"', '')
                field_type = parts[1].upper()
                is_pk = "PRIMARY KEY" in line.upper()
                not_null = "NOT NULL" in line.upper()
                is_unique = "UNIQUE" in line.upper()

                current_table["fields"].append({
                    "name": field_name,
                    "type": field_type,
                    "pk": is_pk,
                    "fk": False,
                    "fk_ref": None,
                    "not_null": not_null,
                    "unique": is_unique,
                    "comment": ""
                })

        tables.append(current_table)

    return tables


def mloop_tables_to_drawdb(tables: List[Dict[str, Any]], title: str = "mLoop Data Model") -> Dict[str, Any]:
    """
    Convert mLoop table dictionaries to drawDB JSON schema.
    Applies automatic grid layout positioning for visual rendering.
    """
    drawdb_tables = []
    relationships = []

    # Grid layout configuration
    cols = 3
    col_width = 320
    row_height = 240
    start_x = 40
    start_y = 40

    table_name_to_id = {}
    table_field_to_id = {}

    # 1. Build DrawDB Tables
    for idx, tbl in enumerate(tables):
        table_id = idx
        table_name_to_id[tbl["name"].lower()] = table_id
        table_field_to_id[table_id] = {}

        grid_col = idx % cols
        grid_row = idx // cols
        pos_x = start_x + (grid_col * col_width)
        pos_y = start_y + (grid_row * row_height)

        drawdb_fields = []
        for f_idx, field in enumerate(tbl["fields"]):
            field_id = f_idx
            table_field_to_id[table_id][field["name"].lower()] = field_id

            # drawDB schema requires: id, name, type, default, check, primary, unique, notNull, increment, comment
            # NOTE: 'pk' must be mapped to 'primary' — that is the required field name in drawDB's validator
            drawdb_fields.append({
                "id": field_id,
                "name": field["name"],
                "type": field["type"],
                "primary": field.get("pk", False),
                "unique": field.get("unique", False),
                "notNull": field.get("not_null", False),
                "increment": False,
                "default": "",
                "check": "",
                "comment": field.get("comment", ""),
                "size": "",
                "values": []
            })

        drawdb_tables.append({
            "id": table_id,
            "name": tbl["name"],
            "x": pos_x,
            "y": pos_y,
            "fields": drawdb_fields,
            "comment": tbl.get("comment", ""),
            "indices": [],
            "color": "#175e54",
            "uniqueConstraints": []
        })

    # 2. Build Relationships
    rel_id = 0
    for tbl in tables:
        start_table_name = tbl["name"].lower()
        if start_table_name not in table_name_to_id:
            continue
        start_table_id = table_name_to_id[start_table_name]

        for field in tbl["fields"]:
            if field.get("fk_ref"):
                target_table_name, target_field_name = field["fk_ref"]
                target_table_name = target_table_name.lower()
                target_field_name = target_field_name.lower()

                if target_table_name in table_name_to_id:
                    end_table_id = table_name_to_id[target_table_name]
                    start_field_name = field["name"].lower()
                    
                    if (start_field_name in table_field_to_id[start_table_id] and 
                        target_field_name in table_field_to_id[end_table_id]):
                        
                        start_field_id = table_field_to_id[start_table_id][start_field_name]
                        end_field_id = table_field_to_id[end_table_id][target_field_name]

                        # drawDB requires: startTableId, startFieldId, endTableId, endFieldId, name, cardinality, updateConstraint, deleteConstraint, id
                        relationships.append({
                            "id": rel_id,
                            "name": f"fk_{tbl['name']}_{field['name']}",
                            "startTableId": start_table_id,
                            "startFieldId": start_field_id,
                            "endTableId": end_table_id,
                            "endFieldId": end_field_id,
                            "cardinality": "Many to one",
                            "updateConstraint": "No action",
                            "deleteConstraint": "No action"
                        })
                        rel_id += 1

    return {
        "author": "mLoop Agent",
        "title": title,
        "date": "2026-07-22",
        "description": "",
        "database": "generic",
        "tables": drawdb_tables,
        "relationships": relationships,
        "notes": [],
        "subjectAreas": [],
        "types": [],
        "customTypes": [],
        "pan": {"x": 0, "y": 0},
        "zoom": 1
    }


def drawdb_to_markdown(drawdb_data: Dict[str, Any]) -> str:
    """
    Convert a drawDB JSON dictionary back into mLoop Markdown specifications.
    """
    tables = drawdb_data.get("tables", [])
    relationships = drawdb_data.get("relationships", [])

    # Map IDs to names for lookup
    table_id_to_name = {t["id"]: t["name"] for t in tables}
    table_field_id_to_name = {}
    for t in tables:
        table_field_id_to_name[t["id"]] = {f["id"]: f["name"] for f in t.get("fields", [])}

    # Map relationships to FK references
    rel_map = {} # (startTableId, startFieldId) -> (endTableName, endFieldName)
    for rel in relationships:
        st_id = rel.get("startTableId")
        sf_id = rel.get("startFieldId")
        et_id = rel.get("endTableId")
        ef_id = rel.get("endFieldId")

        if (st_id in table_id_to_name and et_id in table_id_to_name and
            st_id in table_field_id_to_name and ef_id in table_field_id_to_name[et_id]):
            end_tbl = table_id_to_name[et_id]
            end_fld = table_field_id_to_name[et_id][ef_id]
            rel_map[(st_id, sf_id)] = (end_tbl, end_fld)

    md_lines = [
        f"# Modèle de Données : {drawdb_data.get('title', 'Spécification mLoop')}",
        "",
        "> Document généré automatiquement depuis drawDB JSON.",
        ""
    ]

    for tbl in tables:
        tbl_id = tbl["id"]
        tbl_name = tbl["name"]
        comment = tbl.get("comment", "")

        md_lines.append(f"## Table : {tbl_name}")
        if comment:
            md_lines.append(f"Description: {comment}")
        md_lines.append("")
        md_lines.append("| Champ | Type | Clé | Nullable | Description |")
        md_lines.append("| --- | --- | --- | --- | --- |")

        for fld in tbl.get("fields", []):
            fld_id = fld["id"]
            fld_name = fld["name"]
            fld_type = fld.get("type", "VARCHAR(255)")
            is_pk = fld.get("pk", False)
            is_fk = fld.get("fk", False)
            not_null = fld.get("notNull", False)
            fld_comment = fld.get("comment", "")

            key_parts = []
            if is_pk:
                key_parts.append("PK")
            if is_fk:
                if (tbl_id, fld_id) in rel_map:
                    ref_tbl, ref_fld = rel_map[(tbl_id, fld_id)]
                    key_parts.append(f"FK({ref_tbl}.{ref_fld})")
                else:
                    key_parts.append("FK")
            if fld.get("unique", False):
                key_parts.append("UNIQUE")

            key_str = ", ".join(key_parts)
            nullable_str = "Non" if not_null else "Oui"

            md_lines.append(f"| {fld_name} | {fld_type} | {key_str} | {nullable_str} | {fld_comment} |")

        md_lines.append("")

    return "\n".join(md_lines)


def drawdb_to_sql(drawdb_data: Dict[str, Any], dialect: str = "sqlite") -> str:
    """
    Convert a drawDB JSON dictionary into SQL DDL statements.
    """
    tables = drawdb_data.get("tables", [])
    relationships = drawdb_data.get("relationships", [])

    table_id_to_name = {t["id"]: t["name"] for t in tables}
    table_field_id_to_name = {t["id"]: {f["id"]: f["name"] for f in t.get("fields", [])} for t in tables}

    sql_statements = []

    for tbl in tables:
        tbl_id = tbl["id"]
        tbl_name = tbl["name"]

        fields_sql = []
        pk_fields = []
        fk_constraints = []

        for fld in tbl.get("fields", []):
            fld_name = fld["name"]
            fld_type = fld.get("type", "VARCHAR(255)")
            not_null = " NOT NULL" if fld.get("notNull", False) else ""
            unique = " UNIQUE" if fld.get("unique", False) else ""

            if fld.get("pk", False):
                pk_fields.append(fld_name)

            fields_sql.append(f"    {fld_name} {fld_type}{not_null}{unique}")

        if pk_fields:
            fields_sql.append(f"    PRIMARY KEY ({', '.join(pk_fields)})")

        for rel in relationships:
            if rel.get("startTableId") == tbl_id:
                sf_id = rel.get("startFieldId")
                et_id = rel.get("endTableId")
                ef_id = rel.get("endFieldId")

                if (sf_id in table_field_id_to_name[tbl_id] and et_id in table_id_to_name and
                    ef_id in table_field_id_to_name[et_id]):
                    src_col = table_field_id_to_name[tbl_id][sf_id]
                    target_tbl = table_id_to_name[et_id]
                    target_col = table_field_id_to_name[et_id][ef_id]
                    fk_constraints.append(f"    FOREIGN KEY ({src_col}) REFERENCES {target_tbl}({target_col})")

        all_defs = fields_sql + fk_constraints
        create_stmt = f"CREATE TABLE IF NOT EXISTS {tbl_name} (\n" + ",\n".join(all_defs) + "\n);"
        sql_statements.append(create_stmt)

    return "\n\n".join(sql_statements)
