"""
Tests TDD — Correction de l'angle mort de désambiguïsation du SemanticLexiconResolver
(scores ex-aequo entre projets candidats, ex: Metro_COMMERCE / Metro_FOOD / Metro_SANTE
lorsqu'une requête ambiguë comme "Metro One Trust" produit un score identique pour
plusieurs sous-projets modulaires — ADR-0342). Avant correctif, le premier projet itéré
par `Path.iterdir()` (ordre non garanti, dépendant du filesystem) gagnait arbitrairement.
Après correctif, le départage est déterministe (alphabétique) et enrichi par l'inspection
du contenu réel des documents ingérés (docs/00-ingested/) pour maximiser la couverture
des tokens de la requête, pas seulement le nom du dossier.
"""

from pathlib import Path

from src.utils.lexicon_resolver import SemanticLexiconResolver


def _make_minimal_project(base: Path, name: str) -> Path:
    p = base / name
    (p / "backlog").mkdir(parents=True, exist_ok=True)
    (p / "backlog" / "sprint_backlog.md").write_text("# Sprint", encoding="utf-8")
    return p


def test_tiebreak_is_deterministic_alphabetical_when_no_other_signal(tmp_path):
    """
    3 projets candidats produisent EXACTEMENT le même score (même structure SSOT,
    même recouvrement de tokens). Le départage doit être déterministe et reproductible
    (alphabétique), jamais dépendant de l'ordre d'itération du filesystem.
    """
    base = tmp_path / "Projects"
    base.mkdir()
    # Créées volontairement dans un ordre non-alphabétique pour détecter un
    # départage basé sur l'ordre de création/itération plutôt que le nom.
    for name in ["Zebra_Widget", "Middle_Widget", "Alpha_Widget"]:
        _make_minimal_project(base, name)

    result1 = SemanticLexiconResolver.resolve_project_alias(
        "Widget", base_dir=str(base)
    )
    result2 = SemanticLexiconResolver.resolve_project_alias(
        "Widget", base_dir=str(base)
    )

    assert result1 == result2, (
        "La résolution doit être stable entre deux appels identiques."
    )
    assert result1 == "Alpha_Widget", (
        f"Départage attendu : premier candidat par ordre alphabétique ('Alpha_Widget'), "
        f"obtenu : '{result1}'."
    )


def test_tiebreak_prefers_richer_ingested_content_match_over_folder_name_alone(
    tmp_path,
):
    """
    Lorsque deux projets ont un score de nom de dossier identique, celui dont les
    documents ingérés (docs/00-ingested/) couvrent le PLUS de tokens de la requête
    doit être préféré — pas seulement le nom du dossier tronqué.
    """
    base = tmp_path / "Projects"
    base.mkdir()
    proj_a = _make_minimal_project(base, "Metro_Alpha")
    proj_b = _make_minimal_project(base, "Metro_Beta")

    # Les deux dossiers partagent le token "metro" -> même score de nom de dossier.
    # Seul Metro_Beta a un document ingéré mentionnant explicitement "OneTrust".
    (proj_b / "docs" / "00-ingested").mkdir(parents=True, exist_ok=True)
    (proj_b / "docs" / "00-ingested" / "brief.md").write_text(
        "Intégration OneTrust Consent Management Platform pour Metro.", encoding="utf-8"
    )

    result = SemanticLexiconResolver.resolve_project_alias(
        "Metro OneTrust", base_dir=str(base)
    )
    assert result == "Metro_Beta", (
        f"Le projet dont les documents ingérés couvrent réellement 'OneTrust' doit "
        f"être préféré, obtenu : '{result}'."
    )


def test_tiebreak_alphabetical_fallback_unaffected_by_creation_order_reversed(tmp_path):
    """Contre-épreuve : inverser l'ordre de création ne doit pas changer le résultat déterministe."""
    base = tmp_path / "Projects"
    base.mkdir()
    for name in ["Alpha_Widget", "Middle_Widget", "Zebra_Widget"]:
        _make_minimal_project(base, name)

    result = SemanticLexiconResolver.resolve_project_alias("Widget", base_dir=str(base))
    assert result == "Alpha_Widget"
