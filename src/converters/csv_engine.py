"""
Moteur Tabulaire Résilient & Étanche pour Memory Loop (ADR-0368).
Normalisation multi-encodage, streaming à mémoire constante, anonymisation PII déterministe,
diff sémantique et transformation déclarative.
"""

import csv
import hashlib
import io
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set


class CSVNormalizer:
    """Normalise les fichiers CSV hétérogènes vers un encodage UTF-8 pur avec séparateurs standard."""

    COMMON_ENCODINGS = ["utf-8-sig", "utf-8", "cp1252", "iso-8859-1"]
    COMMON_DELIMITERS = [",", ";", "\t", "|"]

    def detect_encoding_and_bom(self, file_path: Path) -> tuple[str, bool]:
        raw_bytes = file_path.read_bytes()
        has_bom = raw_bytes.startswith(b"\xef\xbb\xbf")

        if has_bom:
            return "utf-8-sig", True

        for enc in ["utf-8", "cp1252", "iso-8859-1"]:
            try:
                raw_bytes.decode(enc)
                return enc, False
            except UnicodeDecodeError:
                continue

        return "latin-1", False

    def detect_delimiter(self, text_sample: str) -> str:
        try:
            sniffer = csv.Sniffer()
            dialect = sniffer.sniff(text_sample, delimiters=";,|\t,")
            return dialect.delimiter
        except Exception:
            lines = [line for line in text_sample.splitlines() if line.strip()][:5]
            if not lines:
                return ","
            best_delim = ","
            best_count = 0
            for d in self.COMMON_DELIMITERS:
                counts = [line.count(d) for line in lines]
                if counts and min(counts) > 0 and min(counts) == max(counts):
                    if counts[0] > best_count:
                        best_count = counts[0]
                        best_delim = d
            return best_delim

    def normalize_file(self, input_path: Path, output_path: Path) -> Dict[str, Any]:
        encoding, has_bom = self.detect_encoding_and_bom(input_path)
        content = input_path.read_text(encoding=encoding, errors="replace").lstrip("\ufeff")

        delimiter = self.detect_delimiter(content[:4096])

        reader = csv.reader(io.StringIO(content), delimiter=delimiter)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        row_count = 0
        with open(output_path, "w", encoding="utf-8", newline="") as out_f:
            writer = csv.writer(out_f, delimiter=",")
            for row in reader:
                writer.writerow(row)
                row_count += 1

        return {
            "encoding": encoding,
            "has_bom": has_bom,
            "delimiter": delimiter,
            "row_count": row_count,
            "rows": row_count,
        }


class CSVSchemaValidator:
    """Valide les lignes de données d'un CSV en streaming flux avec typage strict."""

    EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

    def __init__(self, schema: Dict[str, Dict[str, Any]]):
        self.schema = schema

    def validate_file(self, csv_file: Path) -> Dict[str, Any]:
        errors: List[Dict[str, Any]] = []

        with open(csv_file, "r", encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)
            for row_idx, row in enumerate(reader, start=2):
                for col_name, rules in self.schema.items():
                    val = row.get(col_name)
                    is_required = rules.get("required", False)
                    col_type = rules.get("type", "string")

                    if val is None or val.strip() == "":
                        if is_required:
                            errors.append({
                                "row": row_idx,
                                "column": col_name,
                                "message": f"Champ requis manquant : {col_name}",
                            })
                        continue

                    val_str = val.strip()
                    if col_type == "int":
                        try:
                            int(val_str)
                        except ValueError:
                            errors.append({
                                "row": row_idx,
                                "column": col_name,
                                "message": f"Valeur non entière : {val_str}",
                            })
                    elif col_type == "float":
                        try:
                            float(val_str)
                        except ValueError:
                            errors.append({
                                "row": row_idx,
                                "column": col_name,
                                "message": f"Valeur décimale invalide : {val_str}",
                            })
                    elif col_type == "email":
                        if not self.EMAIL_REGEX.match(val_str):
                            errors.append({
                                "row": row_idx,
                                "column": col_name,
                                "message": f"Format d'email invalide : {val_str}",
                            })
                    elif col_type == "regex" and "regex" in rules:
                        pattern = re.compile(rules["regex"])
                        if not pattern.match(val_str):
                            errors.append({
                                "row": row_idx,
                                "column": col_name,
                                "message": f"Ne respecte pas le pattern {rules['regex']}: {val_str}",
                            })

        return {
            "valid": len(errors) == 0,
            "errors": errors,
        }


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

        return {"anonymized_rows": len(rows), "columns": sensitive_columns}


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
                        except KeyError:
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
        md_lines.append(f"\n*(... et {total_rows - max_preview_rows} lignes supplémentaires non affichées)*")

    return "\n".join(md_lines)
