import json
from pathlib import Path
import pytest
from src.converters.markitdown_converter import MarkItDownPipeline


def test_markitdown_convert_file_success(tmp_path: Path):
    pipeline = MarkItDownPipeline(tmp_path)
    ref_dir = tmp_path / "reference"
    ref_dir.mkdir(parents=True, exist_ok=True)

    src_file = ref_dir / "document_spec.txt"
    src_file.write_text("Spécification technique du composant mLoop.", encoding="utf-8")

    out_md = pipeline.convert_file(src_file)
    assert out_md is not None
    assert out_md.exists()
    assert out_md.name == "document_spec.md"

    content = out_md.read_text(encoding="utf-8")
    assert "source: document_spec.txt" in content
    assert "sha256:" in content
    assert "Spécification technique" in content

    # Vérification dans le registre
    registry_file = tmp_path / "memory" / "ingest_registry.json"
    assert registry_file.exists()
    registry = json.loads(registry_file.read_text(encoding="utf-8"))
    assert len(registry) == 1


def test_markitdown_anti_duplicate_idempotence(tmp_path: Path):
    pipeline = MarkItDownPipeline(tmp_path)
    ref_dir = tmp_path / "reference"
    ref_dir.mkdir(parents=True, exist_ok=True)

    src_file = ref_dir / "contrat.md"
    src_file.write_text("# Contrat SOW initial", encoding="utf-8")

    out1 = pipeline.convert_file(src_file)
    assert out1 is not None

    # Modification artificielle pour tester qu'il ne réécrit pas si même sha256
    out1.write_text("MARKER_CACHED", encoding="utf-8")

    out2 = pipeline.convert_file(src_file)
    assert out2 == out1
    assert out2.read_text(encoding="utf-8") == "MARKER_CACHED"


def test_markitdown_convert_directory(tmp_path: Path):
    pipeline = MarkItDownPipeline(tmp_path)
    ref_dir = tmp_path / "reference"
    ref_dir.mkdir(parents=True, exist_ok=True)

    (ref_dir / "doc1.txt").write_text("Contenu 1", encoding="utf-8")
    (ref_dir / "doc2.csv").write_text("col1,col2\nval1,val2", encoding="utf-8")
    (ref_dir / "ignore.unknown").write_bytes(b"\x00\x01\x02")

    results = pipeline.convert_directory(ref_dir)
    assert len(results) == 2
    names = {r.name for r in results}
    assert "doc1.md" in names
    assert "doc2.md" in names
