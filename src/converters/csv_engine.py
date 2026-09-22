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

from src.utils.logger import get_logger
from src.converters._csv_ops import (
    CSVAnonymizer,
    CSVColumnTransformer,
    CSVRowDiff,
    csv_to_markdown_summary,
)

logger = get_logger("converters.csv_engine")

__all__ = [
    "CSVNormalizer",
    "CSVSchemaValidator",
    "CSVAnonymizer",
    "CSVRowDiff",
    "CSVColumnTransformer",
    "csv_to_markdown_summary",
]


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
            except UnicodeDecodeError as e:
                logger.debug(
                    "Encodage non compatible, tentative du suivant",
                    exc_info=True,
                    extra={
                        "component": "converters.csv_engine",
                        "operation": "detect_encoding",
                        "encoding": enc,
                        "file": str(file_path),
                        "error": str(e),
                    },
                )
                continue

        return "latin-1", False

    def detect_delimiter(self, text_sample: str) -> str:
        try:
            sniffer = csv.Sniffer()
            dialect = sniffer.sniff(text_sample, delimiters=";,|\t,")
            return dialect.delimiter
        except Exception as e:
            logger.debug(
                "Sniffer CSV échoué, repli sur heuristique de détection manuelle",
                exc_info=True,
                extra={
                    "component": "converters.csv_engine",
                    "operation": "detect_delimiter",
                    "sample_len": len(text_sample),
                    "error": str(e),
                },
            )
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

        total_rows = 0
        with open(csv_file, "r", encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)
            for row_idx, row in enumerate(reader, start=2):
                total_rows += 1
                for col_name, rules in self.schema.items():
                    val = row.get(col_name)
                    is_required = rules.get("required", False)
                    col_type = rules.get("type", "string")

                    if val is None or val.strip() == "":
                        if is_required:
                            errors.append(
                                {
                                    "row": row_idx,
                                    "column": col_name,
                                    "message": f"Champ requis manquant : {col_name}",
                                    "error": f"Champ requis manquant : {col_name}",
                                }
                            )
                        continue

                    val_str = val.strip()
                    if col_type == "int":
                        try:
                            int(val_str)
                        except ValueError:
                            errors.append(
                                {
                                    "row": row_idx,
                                    "column": col_name,
                                    "message": f"Valeur non entière : {val_str}",
                                    "error": f"Valeur non entière : {val_str}",
                                }
                            )
                    elif col_type == "float":
                        try:
                            float(val_str)
                        except ValueError:
                            errors.append(
                                {
                                    "row": row_idx,
                                    "column": col_name,
                                    "message": f"Valeur décimale invalide : {val_str}",
                                    "error": f"Valeur décimale invalide : {val_str}",
                                }
                            )
                    elif col_type == "email":
                        if not self.EMAIL_REGEX.match(val_str):
                            errors.append(
                                {
                                    "row": row_idx,
                                    "column": col_name,
                                    "message": f"Format d'email invalide : {val_str}",
                                    "error": f"Format d'email invalide : {val_str}",
                                }
                            )
                    elif col_type == "regex" and "regex" in rules:
                        pattern = re.compile(rules["regex"])
                        if not pattern.match(val_str):
                            errors.append(
                                {
                                    "row": row_idx,
                                    "column": col_name,
                                    "message": f"Ne respecte pas le pattern {rules['regex']}: {val_str}",
                                    "error": f"Ne respecte pas le pattern {rules['regex']}: {val_str}",
                                }
                            )

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "total_rows": total_rows,
        }


# CSVAnonymizer, CSVRowDiff, CSVColumnTransformer, csv_to_markdown_summary
# : extraits vers src/converters/_csv_ops.py (ADR-0202).
