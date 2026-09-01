import sys
import json
from pathlib import Path
from src.cli import ZeroFluffConsole
from src.bridges.drawdb_bridge import parse_markdown_models, mloop_tables_to_drawdb, drawdb_to_markdown

def run_drawdb_pipeline(action: str, input_path_str: str, output_path_str: str, port: int, project_name: str) -> None:
    if action == "serve":
        from tools.drawdb.runner import serve_drawdb
        serve_drawdb(port=port)
        sys.exit(0)
    elif action == "export":
        input_path = Path(input_path_str) if input_path_str else Path("docs/02-data-models")
        output_path = Path(output_path_str) if output_path_str else Path("schema_drawdb.json")
        
        all_tables = []
        if input_path.is_file():
            content = input_path.read_text(encoding="utf-8")
            all_tables = parse_markdown_models(content)
        elif input_path.is_dir():
            for md_file in input_path.glob("*.md"):
                content = md_file.read_text(encoding="utf-8")
                all_tables.extend(parse_markdown_models(content))
        else:
            ZeroFluffConsole.error(f"Le chemin d'entrée {input_path} n'existe pas.")
            sys.exit(1)
        
        drawdb_json = mloop_tables_to_drawdb(all_tables, title=project_name or "mLoop Model")
        output_path.write_text(json.dumps(drawdb_json, indent=2, ensure_ascii=False), encoding="utf-8")
        ZeroFluffConsole.success(f"Schéma drawDB JSON exporté vers : {output_path}")
        sys.exit(0)
    elif action == "import":
        if not input_path_str:
            ZeroFluffConsole.error("Le paramètre --input est requis pour l'action import (ex: schema.json).")
            sys.exit(1)
        input_path = Path(input_path_str)
        output_path = Path(output_path_str) if output_path_str else Path("docs/02-data-models/imported_model.md")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        drawdb_data = json.loads(input_path.read_text(encoding="utf-8"))
        md_content = drawdb_to_markdown(drawdb_data)
        output_path.write_text(md_content, encoding="utf-8")
        ZeroFluffConsole.success(f"Modèle Markdown mLoop généré avec succès dans : {output_path}")
        sys.exit(0)
