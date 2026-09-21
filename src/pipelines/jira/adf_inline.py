"""
Sous-module Jira : adf_inline.py
Responsabilité : Analyse et structuration des éléments de texte inline pour l'Atlassian Document Format (ADF).
"""

import re


def parse_inline_text(text: str) -> list:
    """
    Analyse une ligne de texte pour y détecter et structurer les éléments inline ADF
    (bold, italic, code, liens). Prévient tout conflit d'interprétation avec les crochets
    en utilisant la structure JSON sémantique d'ADF.
    """
    pattern = re.compile(
        r"(\*\*(.*?)\*\*)|"  # 1, 2: **bold**
        r"(\*(.*?)\*)|"  # 3, 4: *italic/bold*
        r"(_(.*?)_)|"  # 5, 6: _italic_
        r"(`([^`]+)`)|"  # 7, 8: `code`
        r"(\[([^\]]+)\]\(([^)]+)\))"  # 9, 10, 11: [text](url)
    )

    nodes = []
    last_idx = 0

    for match in pattern.finditer(text):
        start, end = match.span()
        if start > last_idx:
            nodes.append({"type": "text", "text": text[last_idx:start]})

        g_bold = match.group(1)
        g_italic_star = match.group(3)
        g_italic_under = match.group(5)
        g_code = match.group(7)
        g_link = match.group(9)

        if g_bold:
            nodes.append(
                {"type": "text", "text": match.group(2), "marks": [{"type": "strong"}]}
            )
        elif g_italic_star:
            nodes.append(
                {"type": "text", "text": match.group(4), "marks": [{"type": "em"}]}
            )
        elif g_italic_under:
            nodes.append(
                {"type": "text", "text": match.group(6), "marks": [{"type": "em"}]}
            )
        elif g_code:
            nodes.append(
                {"type": "text", "text": match.group(8), "marks": [{"type": "code"}]}
            )
        elif g_link:
            nodes.append(
                {
                    "type": "text",
                    "text": match.group(10),
                    "marks": [{"type": "link", "attrs": {"href": match.group(11)}}],
                }
            )

        last_idx = end

    if last_idx < len(text):
        nodes.append({"type": "text", "text": text[last_idx:]})

    return [n for n in nodes if n.get("text") != ""]
