"""Opérations CSV avancées : anonymisation, diff et transformation (MLOOP-145-BE — extraction ADR-0202)."""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.utils.logger import get_logger

logger = get_logger("converters.csv_ops")


class CSVAnonymizer:
    """Anonymisation PII déterministe avec hachage salé et préservation relationnelle."""

    def __init__(self, project_salt: str = "mLoop_Default_Salt"):
        self.project_salt = project_salt

    def _pseudonymize(self, value: str) -> str:
        if not value:
            return ""
        salted = f"{self.project_salt}:{value}".encode("utf-8")
        h = hashlib.sha256(salted).hexdigest()[:12]
        return f"ANON_{h}"

    def anonymize_file(
        self,
        input_path: Path,
        output_path: Path,
        sensitive_columns: List[str],
        sample_size: Optional[int] = None,
    ) -> Dict[str, Any]:
        with open(input_path, "r", encoding="utf-8", errors="replace") as in_f:
            reader = csv.DictReader(in_f)
            fieldnames = list(reader.fieldnames or [])

            rows = []
            for row in reader:
                rows.append(row)

            if sample_size is not None and len(rows) > sample_size:
                rows = rows[:sample_size]

            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8", newline="") as out_f:
                writer = csv.DictWriter(out_f, fieldnames=fieldnames)
                writer.writeheader()
                for row in rows:
                    for col in sensitive_columns:
                        if col in row and row[col]:
                            row[col] = self._pseudonymize(row[col])
                    writer.writerow(row)

        return {
            "anonymized_rows": len(rows),
            "rows_processed": len(rows),
            "columns": sensitive_columns,
            "sensitive_columns_masked": sensitive_columns,
        }


class CSVRowDiff:
    """Détecte les ajouts, suppressions et modifications entre deux versions de CSV par clé primaire."""

    def __init__(self, key_column: str):
        self.key_column = key_column

    def compare_files(self, v1_path: Path, v2_path: Path) -> Dict[str, Any]:
        def read_keyed(path: Path) -> Dict[str, Dict[str, str]]:
            data = {}
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    k = row.get(self.key_column)
                    if k:
                        data[k] = row
            return data

        v1_data = read_keyed(v1_path)
        v2_data = read_keyed(v2_path)

        v1_keys = set(v1_data.keys())
        v2_keys = set(v2_data.keys())

        added_keys = sorted(list(v2_keys - v1_keys))
        removed_keys = sorted(list(v1_keys - v2_keys))
        common_keys = sorted(list(v1_keys & v2_keys))

        modified_rows = []
        for k in common_keys:
            r1 = v1_data[k]
            r2 = v2_data[k]
            changes = {}
            all_cols = set(r1.keys()) | set(r2.keys())
            for col in all_cols:
                if col == self.key_column:
                    continue
                old_v = r1.get(col)
                new_v = r2.get(col)
                if old_v != new_v:
                    changes[col] = {"old": old_v, "new": new_v}

            if changes:
                modified_rows.append({"key": k, "changes": changes})

        return {
            "added_keys": added_keys,
            "removed_keys": removed_keys,
            "modified_rows": modified_rows,
        }


class CSVColumnTransformer:
    """Applique des transformations déclaratives (renommages, suppressions, dérivations)."""

    def __init__(
        self,
        renames: Optional[Dict[str, str]] = None,
        drops: Optional[List[str]] = None,
        derives: Optional[Dict[str, str]] = None,
    ):
        self.renames = renames or {}
        self.drops = set(drops or [])
        self.derives = derives or {}

    def transform_file(self, input_path: Path, output_path: Path) -> None:
        with open(input_path, "r", encoding="utf-8", errors="replace") as in_f:
            reader = csv.DictReader(in_f)
            in_fields = list(reader.fieldnames or [])

            out_fields = []
            for col in in_fields:
                if col in self.drops:
                    continue
                out_fields.append(self.renames.get(col, col))

            for new_col in self.derives.keys():
                if new_col not in out_fields:
                    out_fields.append(new_col)

            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8", newline="") as out_f:
                writer = csv.DictWriter(out_f, fieldnames=out_fields)
                writer.writeheader()

                for row in reader:
                    derived_vals = {}
                    for target_col, template in self.derives.items():
                        try:
                            derived_vals[target_col] = template.format(**row)
                        except KeyError as e:
                            logger.debug(
                                "Colonne manquante pour le template de dérivation, valeur vide assignée",
                                exc_info=True,
                                extra={
                                    "component": "converters.csv_ops",
                                    "operation": "transform_derive",
                                    "target_col": target_col,
                                    "error": str(e),
                                },
                            )
                            derived_vals[target_col] = ""

                    new_row = {}
                    for col in in_fields:
                        if col in self.drops:
                            continue
                        new_col_name = self.renames.get(col, col)
                        new_row[new_col_name] = row[col]

                    new_row.update(derived_vals)
                    writer.writerow(new_row)


def csv_to_markdown_summary(csv_file: Path, max_preview_rows: int = 5) -> str:
    """Génère un résumé Markdown propre avec aperçu et métadonnées d'un CSV."""
    with open(csv_file, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        if not header:
            return "Fichier CSV vide."

        preview_rows = []
        total_rows = 0
        for row in reader:
            total_rows += 1
            if len(preview_rows) < max_preview_rows:
                preview_rows.append(row)

    md_lines = [
        f"### Aperçu du fichier `{csv_file.name}`",
        f"- **Total de lignes** : {total_rows}",
        f"- **Colonnes** ({len(header)}) : {', '.join(header)}",
        "",
        "| " + " | ".join(header) + " |",
        "| " + " | ".join(["---"] * len(header)) + " |",
    ]

    for r in preview_rows:
        md_lines.append("| " + " | ".join(r) + " |")

    if total_rows > max_preview_rows:
        md_lines.append(
            f"\n*(... et {total_rows - max_preview_rows} lignes supplémentaires non affichées)*"
        )

    return "\n".join(md_lines)
