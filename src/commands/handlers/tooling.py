"""Handlers Tooling : optimize, svg-optimize, hill-climb, drawdb."""
from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

from src.cli import ZeroFluffConsole

if TYPE_CHECKING:
    import argparse
    from src.state import LoopState


def handle_drawdb(args: argparse.Namespace, state: LoopState | None, project_path: Path | None) -> int:
    """Pipeline DrawDB (serveur, export, import, sync)."""
    from src.pipelines.drawdb_pipeline import run_drawdb_pipeline
    run_drawdb_pipeline(args.action, args.input, args.output, args.port, args.project)
    return 0


def handle_optimize(args: argparse.Namespace, state: LoopState, project_path: Path) -> int:
    """Optimisation RHO."""
    from src.pipelines.rho_optimizer import optimize_rho
    optimize_rho(args.project, args.keyword, args.msg, args.scope)
    return 0


def handle_svg_optimize(args: argparse.Namespace, state: LoopState, project_path: Path) -> int:
    """Optimisation et minification des fichiers SVG."""
    from src.pipelines.svg_optimizer import SVGOptimizerEngine

    engine = SVGOptimizerEngine(project_path)
    input_val = getattr(args, "input", None)

    if not input_val:
        target_path = project_path / "reference"
        ZeroFluffConsole.info(f"Optimisation des fichiers SVG sous : {target_path}")
        res = engine.optimize_directory(target_path)
    elif "*" in input_val or "?" in input_val:
        p = Path(input_val)
        if p.is_absolute():
            search_dir = p.parent
            pattern = p.name
        else:
            search_dir = project_path
            pattern = input_val
        matched_files = list(search_dir.glob(pattern)) if search_dir.exists() else list(project_path.glob(input_val))
        ZeroFluffConsole.info(f"Optimisation de {len(matched_files)} fichier(s) correspondant au motif : {input_val}")
        res = engine.optimize_files(matched_files)
    else:
        target_path = Path(input_val) if Path(input_val).is_absolute() else (project_path / input_val)
        ZeroFluffConsole.info(f"Optimisation des fichiers SVG sous : {target_path}")
        if target_path.is_file():
            res = engine.optimize_file(target_path)
        else:
            res = engine.optimize_directory(target_path)

    print(json.dumps(res, indent=2, ensure_ascii=False))
    return 0 if res.get("success") else 1


def handle_hill_climb(args: argparse.Namespace, state: LoopState, project_path: Path) -> int:
    """Test Hill-Climbing (mutation-évaluation)."""
    from src.pipelines.test_hillclimbing import TestHillClimbingEngine

    thc = TestHillClimbingEngine(args.project)
    initial_score = thc.evaluate_state()
    ZeroFluffConsole.info(f"Score de départ: {initial_score:.2f}")
    mutation = thc.propose_mutation()
    ZeroFluffConsole.info(f"Mutation proposée: {mutation}")
    thc.apply_mutation(mutation)
    new_score = thc.evaluate_state()
    if new_score > initial_score:
        ZeroFluffConsole.success(f"Amélioration validée : {new_score:.2f} > {initial_score:.2f}. Mutation conservée.")
    else:
        ZeroFluffConsole.warning(f"Régression ou statut quo : {new_score:.2f} <= {initial_score:.2f}. Rollback.")
        thc.rollback_mutation(mutation)
    return 0


def handle_archify(args: argparse.Namespace, state: LoopState | None, project_path: Path | None) -> int:
    """Validation et rendu de diagrammes d'architecture interactifs Archify."""
    from tools.archify.archify_runner import (
        find_archify_bin,
        normalize_diagram_type,
        run_archify_command,
        run_archify_doctor,
    )
    import os

    if getattr(args, "doctor", False):
        ZeroFluffConsole.info("Vérification de la santé du moteur Archify...")
        return run_archify_doctor()

    input_file = getattr(args, "file", None)
    if not input_file:
        ZeroFluffConsole.error("L'argument --file <chemin_json> est obligatoire (ou utilisez --doctor).")
        return 1

    input_path = Path(input_file)
    if not input_path.is_absolute() and project_path:
        input_path = project_path / input_file

    if not input_path.exists():
        ZeroFluffConsole.error(f"Fichier de spécification introuvable : {input_path}")
        return 1

    d_type = normalize_diagram_type(getattr(args, "type", None), str(input_path))

    if args.validate_only:
        ZeroFluffConsole.info(f"Validation Showcase de la spécification Archify [{d_type}] : {input_path}")
        return run_archify_command("validate", d_type, str(input_path), quality=args.quality)

    output_file = args.output
    if not output_file:
        output_file = str(input_path).replace(".json", ".html")

    output_path = Path(output_file)
    if not output_path.is_absolute() and project_path:
        output_path = project_path / output_file

    ZeroFluffConsole.info(f"Compilation Archify Showcase [{d_type}] : {input_path} -> {output_path}")
    code = run_archify_command("deliver", d_type, str(input_path), output_path=str(output_path), quality=args.quality)
    if code == 0:
        ZeroFluffConsole.success(f"Artefact HTML généré avec succès : {output_path}")
        if getattr(args, "open", False):
            import sys
            if sys.platform == "win32":
                os.startfile(output_path.resolve())
    return code


def handle_drawdb(args: argparse.Namespace, state: LoopState | None, project_path: Path | None) -> int:
    """Lancement du hub souverain de visualisation des schémas de base de données (drawDB / ERD)."""
    from tools.drawdb.runner import serve_drawdb
    port = getattr(args, "port", 8080)
    auto_open = not getattr(args, "no_open", False)
    ZeroFluffConsole.info(f"Démarrage du visualiseur relationnel de base de données sur le port {port}...")
    serve_drawdb(port=port, auto_open=auto_open)
    return 0


def handle_csv_normalize(args: argparse.Namespace, state: LoopState | None, project_path: Path | None) -> int:
    """Normalise l'encodage et les délimiteurs d'un fichier CSV vers UTF-8 propre (ADR-0368)."""
    from src.converters.csv_engine import CSVNormalizer

    file_path = Path(args.file)
    if not file_path.is_absolute() and project_path:
        file_path = project_path / args.file

    if not file_path.exists():
        ZeroFluffConsole.error(f"Fichier CSV introuvable : {file_path}")
        return 1

    out_path = Path(args.out) if getattr(args, "out", None) else file_path.with_name(f"{file_path.stem}_clean.csv")
    if not out_path.is_absolute() and project_path:
        out_path = project_path / out_path

    normalizer = CSVNormalizer()
    report = normalizer.normalize_file(file_path, out_path)
    count = report.get("rows", report.get("row_count", 0))
    ZeroFluffConsole.success(f"Normalisation terminée ({report['encoding']}, délimiteur: '{report['delimiter']}', {count} lignes) -> {out_path}")
    return 0


def handle_csv_validate(args: argparse.Namespace, state: LoopState | None, project_path: Path | None) -> int:
    """Valide un CSV en streaming selon un schéma JSON de règles (ADR-0368)."""
    import json
    from src.converters.csv_engine import CSVSchemaValidator

    file_path = Path(args.file)
    schema_path = Path(args.schema)
    if not file_path.is_absolute() and project_path:
        file_path = project_path / args.file
    if not schema_path.is_absolute() and project_path:
        schema_path = project_path / args.schema

    if not file_path.exists():
        ZeroFluffConsole.error(f"Fichier CSV introuvable : {file_path}")
        return 1
    if not schema_path.exists():
        ZeroFluffConsole.error(f"Fichier de schéma introuvable : {schema_path}")
        return 1

    schema_data = json.loads(schema_path.read_text(encoding="utf-8"))
    validator = CSVSchemaValidator(schema_data)
    result = validator.validate_file(file_path)

    if result["valid"]:
        ZeroFluffConsole.success(f"Validation réussie : {result['total_rows']} lignes conformes.")
        return 0

    ZeroFluffConsole.warning(f"Validation échouée : {len(result['errors'])} anomalie(s) détectée(s) :")
    for err in result["errors"][:10]:
        ZeroFluffConsole.error(f"  [Ligne {err['row']}, Colonne '{err['column']}'] : {err['error']}")
    if len(result["errors"]) > 10:
        ZeroFluffConsole.info(f"  ... et {len(result['errors']) - 10} autre(s) erreur(s).")
    return 1


def handle_csv_anonymize(args: argparse.Namespace, state: LoopState | None, project_path: Path | None) -> int:
    """Anonymise les colonnes sensibles par hachage déterministe et échantillonne en mémoire constante (ADR-0368)."""
    from src.converters.csv_engine import CSVAnonymizer

    file_path = Path(args.file)
    if not file_path.is_absolute() and project_path:
        file_path = project_path / args.file

    if not file_path.exists():
        ZeroFluffConsole.error(f"Fichier CSV introuvable : {file_path}")
        return 1

    out_path = Path(args.out) if getattr(args, "out", None) else file_path.with_name(f"{file_path.stem}_anonymized.csv")
    if not out_path.is_absolute() and project_path:
        out_path = project_path / out_path

    sensitive = [c.strip() for c in args.fields.split(",") if c.strip()]
    sample_size = getattr(args, "sample", None)
    salt = (state.project_name if state else "mLoop_Default") + "_Salt"

    anonymizer = CSVAnonymizer(project_salt=salt)
    res = anonymizer.anonymize_file(file_path, out_path, sensitive_columns=sensitive, sample_size=sample_size)
    ZeroFluffConsole.success(f"Anonymisation terminée ({res['rows_processed']} lignes, colonnes masquées: {sensitive}) -> {out_path}")
    return 0


def handle_csv_diff(args: argparse.Namespace, state: LoopState | None, project_path: Path | None) -> int:
    """Compare deux instantanés de CSV et génère un rapport différentiel basé sur clé primaire (ADR-0368)."""
    from src.converters.csv_engine import CSVRowDiff

    v1_path = Path(args.old)
    v2_path = Path(args.new)
    if not v1_path.is_absolute() and project_path:
        v1_path = project_path / args.old
    if not v2_path.is_absolute() and project_path:
        v2_path = project_path / args.new

    if not v1_path.exists():
        ZeroFluffConsole.error(f"Fichier CSV ancien introuvable : {v1_path}")
        return 1
    if not v2_path.exists():
        ZeroFluffConsole.error(f"Fichier CSV récent introuvable : {v2_path}")
        return 1

    diff_engine = CSVRowDiff(key_column=args.key)
    report = diff_engine.compare_files(v1_path, v2_path)

    ZeroFluffConsole.info(f"Diff basé sur la clé '{args.key}' :")
    ZeroFluffConsole.info(f"  + Ajouts : {len(report['added_keys'])} ({', '.join(report['added_keys'][:5])})")
    ZeroFluffConsole.info(f"  - Suppressions : {len(report['removed_keys'])} ({', '.join(report['removed_keys'][:5])})")
    ZeroFluffConsole.info(f"  ~ Modifications : {len(report['modified_rows'])}")
    for mod in report["modified_rows"][:5]:
        ZeroFluffConsole.info(f"    [{mod['key']}] : {mod['changes']}")
    return 0



