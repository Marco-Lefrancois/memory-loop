"""
Handlers CSV — normalize / validate / anonymize / diff (ADR-0368).

Extrait de `tooling.py` (découpage ADR-0202) pour maintenir chaque module sous
le plafond de 300 lignes. Consommé via la façade `tooling.py`.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from src.cli import ZeroFluffConsole, LoggingConsole

if TYPE_CHECKING:
    import argparse
    from src.state import LoopState


def _log_err(command: str, msg: str, args: Any = None, **ctx: Any) -> None:
    """Route une erreur handler CSV vers LoggingConsole.error avec contexte standardise (MLOOP-142-BE)."""
    LoggingConsole.error(msg, command=command, project=getattr(args, "project", None), **ctx)


def handle_csv_normalize(
    args: argparse.Namespace, state: LoopState | None, project_path: Path | None
) -> int:
    """Normalise l'encodage et les délimiteurs d'un fichier CSV vers UTF-8 propre (ADR-0368)."""
    from src.converters.csv_engine import CSVNormalizer

    file_path = Path(args.file)
    if not file_path.is_absolute() and project_path:
        file_path = project_path / args.file

    if not file_path.exists():
        _log_err(
            "csv-normalize",
            f"Fichier CSV introuvable : {file_path}",
            args,
            target_keys=str(file_path),
        )
        return 1

    out_path = (
        Path(args.out)
        if getattr(args, "out", None)
        else file_path.with_name(f"{file_path.stem}_clean.csv")
    )
    if not out_path.is_absolute() and project_path:
        out_path = project_path / out_path

    normalizer = CSVNormalizer()
    report = normalizer.normalize_file(file_path, out_path)
    count = report.get("rows", report.get("row_count", 0))
    ZeroFluffConsole.success(
        f"Normalisation terminée ({report['encoding']}, délimiteur: '{report['delimiter']}', "
        f"{count} lignes) -> {out_path}"
    )
    return 0


def handle_csv_validate(
    args: argparse.Namespace, state: LoopState | None, project_path: Path | None
) -> int:
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
        _log_err(
            "csv-validate",
            f"Fichier CSV introuvable : {file_path}",
            args,
            target_keys=str(file_path),
        )
        return 1
    if not schema_path.exists():
        _log_err(
            "csv-validate",
            f"Fichier de schéma introuvable : {schema_path}",
            args,
            target_keys=str(schema_path),
        )
        return 1

    schema_data = json.loads(schema_path.read_text(encoding="utf-8"))
    validator = CSVSchemaValidator(schema_data)
    result = validator.validate_file(file_path)

    if result["valid"]:
        ZeroFluffConsole.success(f"Validation réussie : {result['total_rows']} lignes conformes.")
        return 0

    ZeroFluffConsole.warning(
        f"Validation échouée : {len(result['errors'])} anomalie(s) détectée(s) :"
    )
    for err in result["errors"][:10]:
        _log_err(
            "csv-validate",
            f"  [Ligne {err['row']}, Colonne '{err['column']}'] : {err['error']}",
            args,
            target_keys=str(file_path),
            subcommand=str(err.get("column")),
        )
    if len(result["errors"]) > 10:
        ZeroFluffConsole.info(f"  ... et {len(result['errors']) - 10} autre(s) erreur(s).")
    return 1


def handle_csv_anonymize(
    args: argparse.Namespace, state: LoopState | None, project_path: Path | None
) -> int:
    """Anonymise les colonnes sensibles par hachage déterministe en mémoire constante (ADR-0368)."""
    from src.converters.csv_engine import CSVAnonymizer

    file_path = Path(args.file)
    if not file_path.is_absolute() and project_path:
        file_path = project_path / args.file

    if not file_path.exists():
        _log_err(
            "csv-anonymize",
            f"Fichier CSV introuvable : {file_path}",
            args,
            target_keys=str(file_path),
        )
        return 1

    out_path = (
        Path(args.out)
        if getattr(args, "out", None)
        else file_path.with_name(f"{file_path.stem}_anonymized.csv")
    )
    if not out_path.is_absolute() and project_path:
        out_path = project_path / out_path

    sensitive = [c.strip() for c in args.fields.split(",") if c.strip()]
    sample_size = getattr(args, "sample", None)
    salt = (state.project_name if state else "mLoop_Default") + "_Salt"

    anonymizer = CSVAnonymizer(project_salt=salt)
    res = anonymizer.anonymize_file(
        file_path, out_path, sensitive_columns=sensitive, sample_size=sample_size
    )
    ZeroFluffConsole.success(
        f"Anonymisation terminée ({res['rows_processed']} lignes, colonnes masquées: {sensitive}) -> {out_path}"
    )
    return 0


def handle_csv_diff(
    args: argparse.Namespace, state: LoopState | None, project_path: Path | None
) -> int:
    """Compare deux instantanés de CSV et génère un rapport différentiel basé sur clé primaire (ADR-0368)."""
    from src.converters.csv_engine import CSVRowDiff

    v1_path = Path(args.old)
    v2_path = Path(args.new)
    if not v1_path.is_absolute() and project_path:
        v1_path = project_path / args.old
    if not v2_path.is_absolute() and project_path:
        v2_path = project_path / args.new

    if not v1_path.exists():
        _log_err(
            "csv-diff",
            f"Fichier CSV ancien introuvable : {v1_path}",
            args,
            target_keys=str(v1_path),
        )
        return 1
    if not v2_path.exists():
        _log_err(
            "csv-diff",
            f"Fichier CSV récent introuvable : {v2_path}",
            args,
            target_keys=str(v2_path),
        )
        return 1

    diff_engine = CSVRowDiff(key_column=args.key)
    report = diff_engine.compare_files(v1_path, v2_path)

    ZeroFluffConsole.info(f"Diff basé sur la clé '{args.key}' :")
    ZeroFluffConsole.info(
        f"  + Ajouts : {len(report['added_keys'])} ({', '.join(report['added_keys'][:5])})"
    )
    ZeroFluffConsole.info(
        f"  - Suppressions : {len(report['removed_keys'])} ({', '.join(report['removed_keys'][:5])})"
    )
    ZeroFluffConsole.info(f"  ~ Modifications : {len(report['modified_rows'])}")
    for mod in report["modified_rows"][:5]:
        ZeroFluffConsole.info(f"    [{mod['key']}] : {mod['changes']}")
    return 0
