import json
from pathlib import Path
import pytest
from src.pipelines.okf_compiler import OKFCompiler, OKFValidationError


def test_okf_compile_valid_skill(tmp_path: Path):
    compiler = OKFCompiler(tmp_path)
    src_file = tmp_path / "guide_architecture.md"
    content = """---
type: Architecture
title: Authentification Multi-Facteurs Google Cloud
description: Spécification du flux MFA et rôles IAM pour Metro.
tags: [auth, security, cloud]
---
# Authentification et Sécurité

M. Tremblay a validé l'architecture pour Metro et Google Cloud à Montréal.
Le composant mLoop assure la validation déterministe via SQLite et l'API OAuth2.
"""
    src_file.write_text(content, encoding="utf-8")

    out_skill = compiler.compile_to_skill(src_file, "metro_auth")
    assert out_skill.exists()
    assert out_skill.name == "SKILL.md"

    skill_text = out_skill.read_text(encoding="utf-8")
    assert "name: metro_auth" in skill_text
    assert "okf_version: '0.1'" in skill_text
    assert "Entités Typées Extraites" in skill_text
    assert "Metro" in skill_text
    assert "Google Cloud" in skill_text

    # Vérification de l'index des compétences
    index_file = tmp_path / ".agents" / "skills" / "index.json"
    assert index_file.exists()
    idx = json.loads(index_file.read_text(encoding="utf-8"))
    assert "metro_auth" in idx
    assert idx["metro_auth"]["uri"] == "skill://metro_auth"


def test_okf_compile_invalid_manifest_rejection(tmp_path: Path):
    compiler = OKFCompiler(tmp_path)
    src_file = tmp_path / "bad_manifest.md"
    # Il manque les tags et le type
    content = """---
title: Titre Unique
---
Contenu sans description ni tags requis.
"""
    src_file.write_text(content, encoding="utf-8")

    with pytest.raises(OKFValidationError) as exc_info:
        compiler.compile_to_skill(src_file, "bad_skill")
    assert "ERR_OKF_INVALID_MANIFEST" in str(exc_info.value)


def test_okf_extract_typed_entities(tmp_path: Path):
    compiler = OKFCompiler(tmp_path)
    sample_text = (
        "Mme Dupont a présenté le projet mLoop et Graphify chez Microsoft à Québec. "
        "Le pipeline MarkItDown convertit les documents via l'API."
    )
    entities = compiler.extract_typed_entities(sample_text)

    assert "Microsoft" in entities["Organizations"]
    assert "Dupont" in entities["People"]
    assert "Québec" in entities["Places"]
    assert any(p in entities["Products/Features"] for p in ["mLoop", "Graphify", "MarkItDown"])
