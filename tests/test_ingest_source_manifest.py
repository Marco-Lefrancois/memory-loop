import json
import pytest
from pathlib import Path
from src.state import LoopState, ProjectLayout
from src.pipelines.ingest_agent import IngestAgent

def test_extract_sections_and_terms():
    agent = IngestAgent()
    sample_text = """# Titre Principal
## Section Architecture
L'architecture utilise OAuth2 et EventBus pour synchroniser les données.
### Sous-section Sécurité
Un token JWT est validé via le composant IngestAgent.
"""
    sections = agent._extract_sections(sample_text)
    assert "Titre Principal" in sections
    assert "Section Architecture" in sections
    assert "Sous-section Sécurité" in sections

    terms = agent._extract_length_aware_terms(sample_text)
    assert any("OAuth" in t or "EventBus" in t or "JWT" in t or "IngestAgent" in t for t in terms)
    assert len(terms) <= 10  # Car texte < 10000 caractères

def test_length_aware_limits():
    agent = IngestAgent()
    # Générer un texte avec beaucoup de termes en majuscules
    short_text = " ".join([f"TERM{i}" for i in range(50)])
    terms_short = agent._extract_length_aware_terms(short_text)
    assert len(terms_short) <= 10

    medium_text = short_text + " " + ("X" * 15000)
    terms_medium = agent._extract_length_aware_terms(medium_text)
    assert len(terms_medium) <= 18

def test_source_manifest_and_lexicon_generation(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    proj_name = "TestProject"
    state = LoopState(project_name=proj_name)
    
    # Créer l'arborescence
    ref_dir = tmp_path / "Projects" / proj_name / ProjectLayout.REFERENCE
    ref_dir.mkdir(parents=True, exist_ok=True)
    
    doc1 = ref_dir / "Architecture_Spec.md"
    doc1.write_text("""# Spécification Architecture
## Module SyncEngine
Le composant SyncEngine traite les messages en FIFO via RabbitMQ.
""", encoding="utf-8")
    
    agent = IngestAgent()
    updated_state = agent.execute(state)
    
    # Vérifier que le fichier est bien ingéré
    assert len(updated_state.ingested_sources) == 1
    
    # Vérifier la présence de source_manifest.json
    manifest_file = tmp_path / "Projects" / proj_name / ProjectLayout.DOCS / ProjectLayout.DOCS_INGESTED / "source_manifest.json"
    assert manifest_file.exists()
    
    manifest_data = json.loads(manifest_file.read_text(encoding="utf-8"))
    assert manifest_data["total_sources"] == 1
    assert manifest_data["sources"][0]["filename"] == "Architecture_Spec.md"
    assert "Spécification Architecture" in manifest_data["sources"][0]["sections"]
    
    # Vérifier la présence de lexique_domaine.md
    lexicon_file = tmp_path / "Projects" / proj_name / ProjectLayout.DOCS / ProjectLayout.DOCS_TRANSVERSE / "lexique_domaine.md"
    assert lexicon_file.exists()
    lexicon_content = lexicon_file.read_text(encoding="utf-8")
    assert "# Lexique & Vocabulaire du Domaine Métier" in lexicon_content
    assert "Architecture_Spec.md" in lexicon_content
