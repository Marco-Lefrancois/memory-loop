"""
Tests unitaires du convertisseur Markdown -> ADF (Atlassian Document Format).
Cible : src/pipelines/jira/adf_converter.py

Objectifs de bonification (choix de format PO) :
  - Q1(a) : titres de règles en gras dans une puce  -> `- **[Titre]** : texte`
  - Q2(b) : logique en puces simples (bulletList)
  - Q3(a) : note source en blockquote (hors callout [!NOTE])

Bugs ciblés :
  - Bug 1 : orderedList séparées par un bloc redémarrent à 1 (numérotation cassée)
  - Bug 3 : double tiret `- -` parasite sur les sous-items
"""

import pytest

from src.pipelines.jira.adf_converter import markdown_to_adf, parse_inline_text


def _nodes(adf):
    return adf.get("content", [])


def _find(adf, node_type):
    return [n for n in _nodes(adf) if n.get("type") == node_type]


def _text_of(node):
    """Concatène récursivement tout le texte d'un node ADF."""
    if node.get("type") == "text":
        return node.get("text", "")
    return "".join(_text_of(c) for c in node.get("content", []) or [])


# ---------------------------------------------------------------------------
# Q2(b) — Puces simples
# ---------------------------------------------------------------------------
def test_bullet_list_renders_as_bulletlist():
    md = "- item un\n- item deux\n- item trois\n"
    adf = markdown_to_adf(md)
    bullets = _find(adf, "bulletList")
    assert len(bullets) == 1, "Une seule bulletList attendue"
    assert len(bullets[0]["content"]) == 3, "3 listItem attendus"


# ---------------------------------------------------------------------------
# Q1(a) — Titre de règle en gras dans une puce
# ---------------------------------------------------------------------------
def test_bold_lead_in_bullet_preserved():
    md = "- **[Déterminisme thermique centralisé]** : La durée est calculée par le backend.\n"
    adf = markdown_to_adf(md)
    bullets = _find(adf, "bulletList")
    assert len(bullets) == 1
    li = bullets[0]["content"][0]
    para = li["content"][0]
    # Le premier fragment doit porter la mark strong
    strong_nodes = [
        c
        for c in para["content"]
        if any(m.get("type") == "strong" for m in c.get("marks", []))
    ]
    assert strong_nodes, "Le titre de règle doit être en gras (strong)"
    assert "Déterminisme thermique" in strong_nodes[0]["text"]


# ---------------------------------------------------------------------------
# Q3(a) — Note source en blockquote (hors callout)
# ---------------------------------------------------------------------------
def test_blockquote_note_renders_as_blockquote():
    md = "> 📎 **Source de la formule** : PLAN-006 (lignes 23-31).\n"
    adf = markdown_to_adf(md)
    assert _find(adf, "blockquote"), "Un blockquote attendu"
    assert not _find(adf, "panel"), "Pas de panel pour un blockquote simple"


def test_callout_note_renders_as_panel():
    """Non-régression : un callout [!NOTE] reste un panel."""
    md = "> [!NOTE] Ceci est une note importante\n"
    adf = markdown_to_adf(md)
    assert _find(adf, "panel"), "Un callout [!NOTE] doit rester un panel"


# ---------------------------------------------------------------------------
# Bug 3 — Pas de double tiret parasite
# ---------------------------------------------------------------------------
def test_no_double_bullet_dash():
    md = "- item parent\n- sous item\n"
    adf = markdown_to_adf(md)
    for bl in _find(adf, "bulletList"):
        for li in bl["content"]:
            txt = _text_of(li)
            assert not txt.lstrip().startswith("- "), f"Double tiret parasite: {txt!r}"


# ---------------------------------------------------------------------------
# Non-régression parse_inline_text
# ---------------------------------------------------------------------------
def test_inline_code_and_link_marks():
    nodes = parse_inline_text("Voir `batch_id` et [le doc](https://ex.com/x).")
    code_nodes = [
        n for n in nodes if any(m.get("type") == "code" for m in n.get("marks", []))
    ]
    link_nodes = [
        n for n in nodes if any(m.get("type") == "link" for m in n.get("marks", []))
    ]
    assert code_nodes and code_nodes[0]["text"] == "batch_id"
    assert (
        link_nodes and link_nodes[0]["marks"][0]["attrs"]["href"] == "https://ex.com/x"
    )


# ---------------------------------------------------------------------------
# Non-régression tables
# ---------------------------------------------------------------------------
def test_table_headers_and_cells():
    md = "| A | B |\n| --- | --- |\n| 1 | 2 |\n"
    adf = markdown_to_adf(md)
    tables = _find(adf, "table")
    assert tables, "Une table attendue"
    rows = tables[0]["content"]
    assert rows[0]["content"][0]["type"] == "tableHeader"
    assert rows[1]["content"][0]["type"] == "tableCell"


# ---------------------------------------------------------------------------
# Bug 1 — Numérotation continue des listes ordonnées séparées par un bloc
# ---------------------------------------------------------------------------
def test_ordered_list_split_by_codeblock_stays_coherent():
    """
    Deux items numérotés séparés par un bloc de code.
    Comportement attendu après bonification : la reprise de numérotation
    ne doit pas casser (l'item 2 ne doit pas réafficher '1').
    On vérifie via l'attribut 'order' si présent, sinon la structure.
    """
    md = "1. Premier point\n```\ncode\n```\n2. Deuxième point\n"
    adf = markdown_to_adf(md)
    ordered = _find(adf, "orderedList")
    # Après correction : soit une seule liste, soit la seconde porte order=2
    if len(ordered) == 1:
        assert len(ordered[0]["content"]) == 2
    else:
        # Deux listes : la seconde doit démarrer à 2 (attrs.order)
        assert ordered[-1].get("attrs", {}).get("order") == 2, (
            "La seconde orderedList doit reprendre à order=2 (numérotation continue)"
        )
