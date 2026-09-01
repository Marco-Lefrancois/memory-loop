"""
Tests unitaires pour le pont de conversion drawDB dans mLoop.
"""

import json
from src.bridges.drawdb_bridge import (
    parse_markdown_models,
    mloop_tables_to_drawdb,
    drawdb_to_markdown,
    drawdb_to_sql,
    parse_sql_ddl
)

SAMPLE_MARKDOWN = """
# Modèle de Données Test

## Table : Users
Description: Table des utilisateurs du système.

| Champ | Type | Clé | Nullable | Description |
| --- | --- | --- | --- | --- |
| id | INT | PK | Non | Identifiant unique |
| email | VARCHAR(255) | UNIQUE | Non | Adresse e-mail |
| role_id | INT | FK(Roles.id) | Oui | Clé étrangère |

## Table : Roles
Description: Rôles utilisateurs.

| Champ | Type | Clé | Nullable | Description |
| --- | --- | --- | --- | --- |
| id | INT | PK | Non | Identifiant du rôle |
| name | VARCHAR(50) |  | Non | Nom du rôle |
"""

def test_parse_markdown_models():
    tables = parse_markdown_models(SAMPLE_MARKDOWN)
    assert len(tables) == 2
    assert tables[0]["name"] == "Users"
    assert tables[0]["comment"] == "Table des utilisateurs du système."
    assert len(tables[0]["fields"]) == 3
    assert tables[0]["fields"][0]["name"] == "id"
    assert tables[0]["fields"][0]["pk"] is True
    assert tables[0]["fields"][2]["fk"] is True
    assert tables[0]["fields"][2]["fk_ref"] == ("Roles", "id")

def test_mloop_tables_to_drawdb():
    tables = parse_markdown_models(SAMPLE_MARKDOWN)
    drawdb_json = mloop_tables_to_drawdb(tables, title="Test Model")
    
    assert drawdb_json["title"] == "Test Model"
    assert len(drawdb_json["tables"]) == 2
    assert drawdb_json["tables"][0]["name"] == "Users"
    assert len(drawdb_json["relationships"]) == 1
    rel = drawdb_json["relationships"][0]
    assert rel["name"] == "fk_Users_role_id"

def test_roundtrip_markdown():
    tables = parse_markdown_models(SAMPLE_MARKDOWN)
    drawdb_json = mloop_tables_to_drawdb(tables, title="Test Model")
    md_output = drawdb_to_markdown(drawdb_json)
    
    assert "## Table : Users" in md_output
    assert "## Table : Roles" in md_output
    assert "role_id" in md_output

def test_drawdb_to_sql():
    tables = parse_markdown_models(SAMPLE_MARKDOWN)
    drawdb_json = mloop_tables_to_drawdb(tables)
    sql = drawdb_to_sql(drawdb_json)
    
    assert "CREATE TABLE IF NOT EXISTS Users" in sql
    assert "id INT NOT NULL" in sql
    assert "FOREIGN KEY (role_id) REFERENCES Roles(id)" in sql

def test_parse_dbml():
    dbml_sample = """
    Table InventoryLot {
        id uuid [pk]
        flockId uuid [not null]
    }
    Table InventoryTransaction {
        id uuid [pk]
        lotId uuid [not null, ref: > InventoryLot.id]
    }
    """
    tables = parse_markdown_models(dbml_sample)
    assert len(tables) == 2
    assert tables[0]["name"] == "InventoryLot"
    assert tables[1]["name"] == "InventoryTransaction"
    assert tables[1]["fields"][1]["fk_ref"] == ("InventoryLot", "id")

