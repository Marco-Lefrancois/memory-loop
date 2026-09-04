"""
Test TDD — Correction du bug de résolution de story par préfixe alphabétique
distinct (ex: 'INC-004-BE' résolu à tort vers 'REC-004-BE.md').

Bug constaté en session réelle : `resolve_story_query("INC-004-BE", stories_dir)`
retournait `01-reception/REC-004-BE.md` (Module Réception, désinfection) au lieu
de signaler l'absence du récit d'incubation demandé, car l'ancien algorithme
ne pondérait QUE le numéro extrait (`004`) sans jamais comparer le préfixe
alphabétique de l'identifiant (`INC` vs `REC`) — deux familles d'IDs totalement
différentes partageant juste le même suffixe numérique.
"""

from pathlib import Path

from src.utils.lexicon_resolver import SemanticLexiconResolver


def _write_story(
    stories_dir: Path, rel_path: str, story_id: str, jira_key: str, title: str
):
    p = stories_dir / rel_path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        f"""---
id: {story_id}
jira_key: {jira_key}
status: READY_FOR_DEV
---
# {title}
""",
        encoding="utf-8",
    )
    return p


def test_resolve_story_query_does_not_confuse_different_id_prefixes(tmp_path):
    """
    'INC-004-BE' (inexistant) ne doit JAMAIS résoudre vers 'REC-004-BE'
    (existant) uniquement parce que les deux partagent le suffixe numérique
    '004'. Les préfixes alphabétiques 'INC' et 'REC' désignent des familles
    d'identifiants totalement différentes (modules Incubation vs Réception).
    """
    stories_dir = tmp_path / "backlog" / "stories"
    _write_story(
        stories_dir,
        "01-reception/REC-004-BE.md",
        "REC-004-BE",
        "COUVBOIRE-712",
        "API Désinfection - Enregistrement CCP",
    )

    result = SemanticLexiconResolver.resolve_story_query("INC-004-BE", stories_dir)

    assert result is None, (
        f"'INC-004-BE' ne doit PAS résoudre vers un fichier existant d'un "
        f"préfixe différent ('REC-004-BE'). Résultat obtenu : {result}"
    )


def test_resolve_story_query_matches_correct_prefix_and_number(tmp_path):
    """Une requête avec le bon préfixe ET le bon numéro doit toujours résoudre correctement."""
    stories_dir = tmp_path / "backlog" / "stories"
    _write_story(
        stories_dir,
        "01-reception/REC-004-BE.md",
        "REC-004-BE",
        "COUVBOIRE-712",
        "API Désinfection - Enregistrement CCP",
    )
    _write_story(
        stories_dir,
        "02-incubation/INC-004-BE.md",
        "INC-004-BE",
        "COUVBOIRE-1066",
        "API Confirmation de la mise en incubation",
    )

    result = SemanticLexiconResolver.resolve_story_query("INC-004-BE", stories_dir)

    assert result is not None
    assert result.name == "INC-004-BE.md"


def test_resolve_story_query_still_matches_pure_numeric_query(tmp_path):
    """Une requête purement numérique (sans préfixe, ex: '14') doit continuer à fonctionner par recouvrement numérique."""
    stories_dir = tmp_path / "backlog" / "stories"
    _write_story(
        stories_dir,
        "01-reception/REC-014-BE.md",
        "REC-014-BE",
        "COUVBOIRE-999",
        "Changer la date d'incubation",
    )

    result = SemanticLexiconResolver.resolve_story_query("14", stories_dir)

    assert result is not None
    assert result.name == "REC-014-BE.md"
