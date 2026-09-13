"""
Tests unitaires et de non-régression pour le moteur tabulaire résilient mLoop (ADR-0368).
Vérifie la normalisation multi-encodage, le sniffing de séparateur, la validation de schéma,
le diff ligne à ligne et l'anonymisation PII déterministe.
"""

import tempfile
from pathlib import Path
import pytest

from src.converters.csv_engine import (
    CSVNormalizer,
    CSVSchemaValidator,
    CSVAnonymizer,
    CSVRowDiff,
    CSVColumnTransformer,
    csv_to_markdown_summary,
)


def test_csv_normalizer_cp1252_semicolon():
    """Vérifie la normalisation d'un fichier Windows CP1252 avec séparateur point-virgule."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_csv = Path(tmpdir) / "client_cp1252.csv"
        # Texte en encodage Windows avec accents et séparateurs ';'
        raw_text = "id;nom;rôle;ville\n1;Bélanger;Ingénieur;Montréal\n2;Lévesque;Analyste;Québec\n"
        input_csv.write_bytes(raw_text.encode("cp1252"))

        normalizer = CSVNormalizer()
        output_csv = Path(tmpdir) / "clean.csv"
        report = normalizer.normalize_file(input_csv, output_csv)

        assert report["encoding"].lower() in ["cp1252", "iso-8859-1"]
        assert report["delimiter"] == ";"
        assert output_csv.exists()

        # Lecture du fichier de sortie en UTF-8 standard
        content = output_csv.read_text(encoding="utf-8")
        assert "id,nom,rôle,ville" in content
        assert "1,Bélanger,Ingénieur,Montréal" in content


def test_csv_normalizer_utf8_bom_tab():
    """Vérifie le décapage du BOM UTF-8 et la conversion des séparateurs tabulation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_csv = Path(tmpdir) / "export_bom.csv"
        raw_text = "\ufeffcode\tdescription\tprix\nSKU1\tPièce auto\t19.99\nSKU2\tFiltre\t45.50\n"
        input_csv.write_bytes(raw_text.encode("utf-8-sig"))

        normalizer = CSVNormalizer()
        output_csv = Path(tmpdir) / "clean.csv"
        report = normalizer.normalize_file(input_csv, output_csv)

        assert report["has_bom"] is True
        assert report["delimiter"] == "\t"

        content = output_csv.read_text(encoding="utf-8")
        assert not content.startswith("\ufeff")
        assert "code,description,prix" in content


def test_csv_schema_validator_streaming():
    """Vérifie la validation de schéma en streaming et le rapport d'erreurs ligne par ligne."""
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_file = Path(tmpdir) / "dataset.csv"
        csv_file.write_text(
            "id,email,age\n"
            "1,alice@example.com,29\n"
            "2,bad-email,not-a-number\n"
            "3,,40\n",
            encoding="utf-8",
        )

        schema = {
            "id": {"type": "int", "required": True},
            "email": {"type": "email", "required": True},
            "age": {"type": "int", "required": False},
        }

        validator = CSVSchemaValidator(schema)
        result = validator.validate_file(csv_file)

        assert result["valid"] is False
        assert len(result["errors"]) >= 2
        # Erreur sur la ligne physique 3 (id=2) : bad-email et not-a-number
        line3_errors = [e for e in result["errors"] if e["row"] == 3]
        assert any(e["column"] == "email" for e in line3_errors)
        assert any(e["column"] == "age" for e in line3_errors)
        # Erreur sur la ligne physique 4 (id=3) : email requis vide
        line4_errors = [e for e in result["errors"] if e["row"] == 4]
        assert any(e["column"] == "email" for e in line4_errors)


def test_csv_anonymizer_and_reservoir_sampling():
    """Vérifie l'anonymisation PII déterministe et le respect de la consistance relationnelle."""
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_file = Path(tmpdir) / "users.csv"
        csv_file.write_text(
            "user_id,email,nom,score\n"
            "U1,jean@corp.com,Tremblay,100\n"
            "U2,marie@corp.com,Gagnon,200\n"
            "U3,jean@corp.com,Tremblay,150\n",  # Même personne (jean@corp.com)
            encoding="utf-8",
        )

        anonymizer = CSVAnonymizer(project_salt="mLoop_Test_Project_Salt")
        out_file = Path(tmpdir) / "anonymized.csv"
        anonymizer.anonymize_file(
            input_path=csv_file,
            output_path=out_file,
            sensitive_columns=["email", "nom"],
            sample_size=10,
        )

        content = out_file.read_text(encoding="utf-8")
        assert "jean@corp.com" not in content
        assert "Tremblay" not in content

        # Vérification de l'intégrité relationnelle :
        # Ligne 1 et Ligne 3 ayant le même email doivent avoir le même token anonymisé
        lines = content.strip().splitlines()[1:]  # ignorer entête
        row1_email_token = lines[0].split(",")[1]
        row3_email_token = lines[2].split(",")[1]
        assert row1_email_token == row3_email_token, "La pseudonymisation doit être déterministe pour préserver les jointures !"


def test_csv_row_diff_detection():
    """Vérifie la détection différentielle d'ajouts, suppressions et modifications."""
    with tempfile.TemporaryDirectory() as tmpdir:
        v1 = Path(tmpdir) / "v1.csv"
        v2 = Path(tmpdir) / "v2.csv"

        v1.write_text(
            "id,statut,prix\n"
            "REC-1,OPEN,100\n"
            "REC-2,OPEN,200\n"
            "REC-3,CLOSED,300\n",
            encoding="utf-8",
        )

        v2.write_text(
            "id,statut,prix\n"
            "REC-1,IN_PROGRESS,120\n"  # Modifié
            "REC-2,OPEN,200\n"         # Inchangé
            "REC-4,NEW,400\n",         # Ajouté (REC-3 supprimé)
            encoding="utf-8",
        )

        diff_tool = CSVRowDiff(key_column="id")
        report = diff_tool.compare_files(v1, v2)

        assert report["added_keys"] == ["REC-4"]
        assert report["removed_keys"] == ["REC-3"]
        assert len(report["modified_rows"]) == 1
        assert report["modified_rows"][0]["key"] == "REC-1"
        changes = report["modified_rows"][0]["changes"]
        assert changes["statut"] == {"old": "OPEN", "new": "IN_PROGRESS"}
        assert changes["prix"] == {"old": "100", "new": "120"}


def test_csv_column_transformer():
    """Vérifie les opérations déclaratives de renommage, suppression et dérivation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_file = Path(tmpdir) / "input.csv"
        csv_file.write_text(
            "first_name,last_name,unused_col,salary\n"
            "Alice,Smith,trash,50000\n"
            "Bob,Jones,trash,60000\n",
            encoding="utf-8",
        )

        transformer = CSVColumnTransformer(
            renames={"first_name": "prenom"},
            drops=["unused_col"],
            derives={"full_name": "{first_name} {last_name}"},
        )
        out_file = Path(tmpdir) / "transformed.csv"
        transformer.transform_file(csv_file, out_file)

        content = out_file.read_text(encoding="utf-8")
        assert "unused_col" not in content
        assert "prenom,last_name,salary,full_name" in content
        assert "Alice,Smith,50000,Alice Smith" in content


def test_csv_to_markdown_summary():
    """Vérifie la génération d'un résumé Markdown compact prêt pour l'ingestion."""
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_file = Path(tmpdir) / "summary.csv"
        csv_file.write_text(
            "id,nom,valeur\n"
            "1,A,10\n"
            "2,B,20\n",
            encoding="utf-8",
        )

        md = csv_to_markdown_summary(csv_file, max_preview_rows=5)
        assert "| id | nom | valeur |" in md
        assert "| 1 | A | 10 |" in md
        assert "Total de lignes" in md
