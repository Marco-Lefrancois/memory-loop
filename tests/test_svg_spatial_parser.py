import pytest
from pathlib import Path
from src.converters.svg_to_md import SvgSpatialParser, generate_ascii_wireframe, parse_svg_to_md_text, convert_svg_file_to_md

def test_svg_spatial_sorting_and_classification():
    # SVG avec éléments volontairement désordonnés dans le code XML
    # Le bouton bas de page est déclaré en premier, l'en-tête en dernier
    sample_svg = """<svg width="390" height="844" viewBox="0 0 390 844" xmlns="http://www.w3.org/2000/svg">
      <!-- 1. Bouton en bas de page (Y=760) -->
      <rect x="20" y="760" width="350" height="50" rx="8" fill="#007AFF" />
      <text x="160" y="790" font-size="16" fill="#FFFFFF">Valider la saisie</text>

      <!-- 2. Corps de page (Y=250) -->
      <rect x="20" y="250" width="350" height="120" rx="12" fill="#F2F2F7" />
      <text x="35" y="280" font-size="16" font-weight="bold">Section Inventaire</text>

      <!-- 3. En-tête (Y=45) -->
      <text x="30" y="45" font-size="20" font-weight="bold">Dossier Santé</text>
      <circle cx="340" cy="45" r="12" fill="#34C759" />
      <text x="335" y="50" font-size="10">OK</text>
    </svg>"""

    parser = SvgSpatialParser(sample_svg, "00_test_screen.svg")
    elements = parser.parse()

    # Vérification du tri spatial strict (Y croissant)
    assert len(elements) >= 3
    # Le premier élément doit être l'en-tête (Y ≈ 45)
    assert elements[0].text == "Dossier Santé"
    assert elements[0].elem_type == "heading"

    # Le dernier élément doit être le bouton de validation (Y ≈ 760)
    assert any(e.text == "Valider la saisie" and e.elem_type == "button" for e in elements)

def test_ascii_wireframe_generation():
    sample_svg = """<svg width="390" height="844" viewBox="0 0 390 844" xmlns="http://www.w3.org/2000/svg">
      <text x="30" y="45" font-size="20" font-weight="bold">Tableau de Bord</text>
      <rect x="20" y="760" width="350" height="50" rx="8" fill="#007AFF" />
      <text x="160" y="790" font-size="16">Enregistrer</text>
    </svg>"""

    md_output = parse_svg_to_md_text(sample_svg, "dashboard.svg")
    assert "## 🖥️ Wireframe Spatial Déclaratif" in md_output
    assert "Tableau de Bord" in md_output
    assert "Enregistrer" in md_output
    assert "## 🎛️ Matrice des Call-to-Actions (CTA)" in md_output
    assert "Enregistrer" in md_output

def test_convert_svg_file_to_md(tmp_path):
    svg_file = tmp_path / "test_screen.svg"
    svg_file.write_text("""<svg width="390" height="844" xmlns="http://www.w3.org/2000/svg">
      <text x="20" y="50" font-size="18">Ecran Paramètres</text>
    </svg>""", encoding="utf-8")

    out_md = tmp_path / "docs" / "00-ingested" / "test_screen.md"
    success = convert_svg_file_to_md(svg_file, out_md)
    assert success
    assert out_md.exists()
    
    content = out_md.read_text(encoding="utf-8")
    assert "Ecran Paramètres" in content
    assert "Spécification UI" in content
