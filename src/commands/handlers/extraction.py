"""
Handler de la commande CLI `extract` (Standard ADR-0342).
Distille les documents bruts en Knowledge Abstracts structurés dans docs/.
"""

import json
from pathlib import Path
import sys
from typing import Optional

from src.cli import ZeroFluffConsole
from src.core.declarative_extractor import DeclarativeExtractor, KnowledgeAbstract


def handle_extract(args, state, project_path: Optional[Path]) -> int:
    """
    Exécute l'extraction déclarative sur un fichier source selon le template sélectionné.
    
    Arguments CLI supportés :
    --template : Nom du template (business_rules, data_models, api_contracts, ui_matrix)
    --source   : Fichier source à extraire (ex: docs/00-ingested/spec.md)
    --target   : Répertoire de destination personnalisé (optionnel)
    --format   : Format de sortie ('markdown' ou 'json', défaut: 'markdown')
    --list     : Liste les templates disponibles
    """
    extractor = DeclarativeExtractor()

    # Mode affichage de la liste des templates
    if getattr(args, "list", False) or not getattr(args, "template", None):
        if getattr(args, "list", False):
            templates = extractor.list_templates()
            ZeroFluffConsole.section("Templates d'Extraction Déclarative Disponibles (ADR-0342)")
            for t in templates:
                ZeroFluffConsole.info(f" • {t}")
            return 0

    template_name = args.template
    source_file_arg = args.source
    output_format = getattr(args, "format", "markdown") or "markdown"

    if not source_file_arg:
        ZeroFluffConsole.error("L'argument --source <chemin_fichier> est obligatoire pour l'extraction.")
        return 1

    # Résolution du fichier source
    source_path = Path(source_file_arg)
    if not source_path.is_absolute() and project_path:
        source_path = project_path / source_file_arg

    if not source_path.exists():
        ZeroFluffConsole.error(f"Fichier source introuvable : {source_path}")
        return 1

    ZeroFluffConsole.section(f"Extraction Déclarative mLoop — Template : {template_name}")
    ZeroFluffConsole.info(f"Source : {source_path}")

    try:
        template_def = extractor.load_template(template_name)
    except FileNotFoundError as e:
        ZeroFluffConsole.error(str(e))
        return 1

    raw_text = source_path.read_text(encoding="utf-8")
    ka = extractor.extract_from_text(raw_text, template_def, source_file=str(source_path.name))

    if not ka.entities:
        ZeroFluffConsole.warning(f"Aucune entité extraite correspondant au template '{template_name}'.")
        return 0

    ZeroFluffConsole.info(f"Entités extraites : {len(ka.entities)} entité(s).")

    # Détermination du répertoire de sortie
    if args.target:
        target_dir = Path(args.target)
        if not target_dir.is_absolute() and project_path:
            target_dir = project_path / args.target
    else:
        rel_target = template_def.get("target_directory", "docs/06-knowledge/")
        target_dir = (project_path / rel_target) if project_path else Path(rel_target)

    target_dir.mkdir(parents=True, exist_ok=True)

    # Écriture des fichiers de sortie
    if output_format == "json":
        json_file = target_dir / f"extracted_{template_name}.json"
        json_file.write_text(ka.to_json(indent=2), encoding="utf-8")
        ZeroFluffConsole.info(f"Knowledge Abstract JSON généré : {json_file}")
    else:
        for entity in ka.entities:
            md_content = extractor.format_markdown(entity, template_def)
            clean_id = entity.id.replace("/", "_")
            out_md_file = target_dir / f"{clean_id}.md"
            out_md_file.write_text(md_content, encoding="utf-8")
            ZeroFluffConsole.info(f" • Généré : {out_md_file.name} ({entity.id})")

    ZeroFluffConsole.info(f"✓ Extraction terminée avec succès dans : {target_dir}")
    return 0
