"""
Sous-module Jira : adf_converter.py
Responsabilité : Conversion de Markdown vers l'Atlassian Document Format (ADF)
requis par l'API Jira Cloud v3 pour un rendu premium et fidèle.
"""
import re


def parse_inline_text(text: str) -> list:
    """
    Analyse une ligne de texte pour y détecter et structurer les éléments inline ADF
    (bold, italic, code, liens). Prévient tout conflit d'interprétation avec les crochets
    en utilisant la structure JSON sémantique d'ADF.
    """
    pattern = re.compile(
        r'(\*\*(.*?)\*\*)|'           # 1, 2: **bold**
        r'(\*(.*?)\*)|'               # 3, 4: *italic/bold*
        r'(_(.*?)_)|'                 # 5, 6: _italic_
        r'(`([^`]+)`)|'               # 7, 8: `code`
        r'(\[([^\]]+)\]\(([^)]+)\))'  # 9, 10, 11: [text](url)
    )

    nodes = []
    last_idx = 0

    for match in pattern.finditer(text):
        start, end = match.span()
        if start > last_idx:
            nodes.append({
                "type": "text",
                "text": text[last_idx:start]
            })

        g_bold = match.group(1)
        g_italic_star = match.group(3)
        g_italic_under = match.group(5)
        g_code = match.group(7)
        g_link = match.group(9)

        if g_bold:
            nodes.append({
                "type": "text",
                "text": match.group(2),
                "marks": [{"type": "strong"}]
            })
        elif g_italic_star:
            nodes.append({
                "type": "text",
                "text": match.group(4),
                "marks": [{"type": "em"}]
            })
        elif g_italic_under:
            nodes.append({
                "type": "text",
                "text": match.group(6),
                "marks": [{"type": "em"}]
            })
        elif g_code:
            nodes.append({
                "type": "text",
                "text": match.group(8),
                "marks": [{"type": "code"}]
            })
        elif g_link:
            nodes.append({
                "type": "text",
                "text": match.group(10),
                "marks": [{
                    "type": "link",
                    "attrs": {"href": match.group(11)}
                }]
            })

        last_idx = end

    if last_idx < len(text):
        nodes.append({
            "type": "text",
            "text": text[last_idx:]
        })

    return [n for n in nodes if n.get("text") != ""]


def markdown_to_adf(md: str) -> dict:
    """
    Convertit un document Markdown complet en Atlassian Document Format (ADF) JSON
    pour un rendu de très haute fidélité visuelle sous Jira Cloud (API v3).
    Accumule les lignes de texte consécutives dans un seul paragraphe séparé par des
    hardBreaks pour réduire l'interligne et obtenir un rendu compact premium.
    """
    lines = md.splitlines()
    adf_content = []

    in_code_block = False
    code_lang = ""
    code_lines = []

    in_table = False
    table_rows = []

    list_type = None
    list_items = []

    paragraph_nodes = []

    def flush_paragraph():
        nonlocal paragraph_nodes
        if not paragraph_nodes:
            return
        adf_content.append({
            "type": "paragraph",
            "content": paragraph_nodes
        })
        paragraph_nodes = []

    def flush_list():
        nonlocal list_type, list_items
        if not list_items:
            return

        def build_list(items, root_type):
            if not items:
                return None
            
            list_node = {"type": root_type, "content": []}
            
            i = 0
            while i < len(items):
                indent, text = items[i]
                
                # Regrouper tous les enfants ayant une indentation strictement supérieure
                children = []
                j = i + 1
                while j < len(items) and items[j][0] > indent:
                    children.append(items[j])
                    j += 1
                
                list_item = {
                    "type": "listItem",
                    "content": [
                        {
                            "type": "paragraph",
                            "content": parse_inline_text(text)
                        }
                    ]
                }
                
                if children:
                    # Les sous-listes sont toujours des bulletList par défaut dans ce parseur simplifié
                    child_list = build_list(children, "bulletList")
                    if child_list:
                        list_item["content"].append(child_list)
                        
                list_node["content"].append(list_item)
                i = j
                
            return list_node

        adf_node = build_list(list_items, list_type)
        if adf_node:
            adf_content.append(adf_node)
            
        list_items = []
        list_type = None

    def flush_table():
        nonlocal in_table, table_rows
        if not table_rows:
            return

        adf_rows = []
        for is_header, cells in table_rows:
            row_cells = []
            cell_type = "tableHeader" if is_header else "tableCell"
            for cell in cells:
                row_cells.append({
                    "type": cell_type,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": parse_inline_text(cell)
                        }
                    ]
                })
            adf_rows.append({
                "type": "tableRow",
                "content": row_cells
            })

        adf_content.append({
            "type": "table",
            "content": adf_rows
        })
        table_rows.clear()
        in_table = False

    for line in lines:
        stripped = line.strip()

        # 1. Code blocks
        if stripped.startswith("```"):
            flush_paragraph()
            flush_list()
            flush_table()

            if not in_code_block:
                in_code_block = True
                code_lang = stripped[3:].strip()
                code_lines = []
            else:
                in_code_block = False
                attrs = {}
                if code_lang:
                    attrs["language"] = code_lang

                content_text = "\n".join(code_lines)
                code_node = {
                    "type": "codeBlock",
                    "content": [{"type": "text", "text": content_text}]
                }
                if attrs:
                    code_node["attrs"] = attrs
                adf_content.append(code_node)
            continue

        if in_code_block:
            code_lines.append(line)
            continue

        # 2. Tables
        if stripped.startswith("|"):
            flush_paragraph()
            flush_list()
            if "---" in stripped:
                continue
            cells = [c.strip() for c in stripped.split("|")[1:-1]]
            is_header = not in_table
            in_table = True
            table_rows.append((is_header, cells))
            continue
        else:
            if in_table:
                flush_table()

        # 3. Headings
        if stripped.startswith("#"):
            flush_paragraph()
            flush_list()
            flush_table()
            match = re.match(r'^(#+)\s+(.*)$', stripped)
            if match:
                level = len(match.group(1))
                title_text = match.group(2)
                adf_content.append({
                    "type": "heading",
                    "attrs": {"level": level},
                    "content": parse_inline_text(title_text)
                })
                continue

        # 4. Bullet lists
        bullet_match = re.match(r'^(\s*)([-*])\s+(.*)$', line)
        if bullet_match:
            flush_paragraph()
            flush_table()
            indent = len(bullet_match.group(1))
            content = bullet_match.group(3)
            if list_type != "bulletList":
                flush_list()
                list_type = "bulletList"
            list_items.append((indent, content))
            continue

        # 5. Ordered lists
        ordered_match = re.match(r'^(\s*)\d+\.\s+(.*)$', line)
        if ordered_match:
            flush_paragraph()
            flush_table()
            indent = len(ordered_match.group(1))
            content = ordered_match.group(2)
            if list_type != "orderedList":
                flush_list()
                list_type = "orderedList"
            list_items.append((indent, content))
            continue

        # Non-list line
        flush_list()

        # 6. Horizontal Rules
        if stripped in ["---", "***", "___"]:
            flush_paragraph()
            flush_table()
            adf_content.append({"type": "rule"})
            continue

        # 7. Blockquotes
        if stripped.startswith(">"):
            flush_paragraph()
            flush_table()
            content = stripped[1:].strip()
            callout_match = re.match(
                r'^\[!(NOTE|WARNING|TIP|IMPORTANT|CAUTION)\]\s*(.*)$',
                content,
                re.IGNORECASE
            )
            if callout_match:
                adm_type = callout_match.group(1).upper()
                title = callout_match.group(2)

                panel_map = {
                    "NOTE": "info",
                    "TIP": "success",
                    "IMPORTANT": "info",
                    "WARNING": "note",
                    "CAUTION": "error"
                }
                panel_type = panel_map.get(adm_type, "info")

                panel_content = []
                if title:
                    panel_content.append({
                        "type": "paragraph",
                        "content": [{
                            "type": "text",
                            "text": f"{adm_type}: {title}",
                            "marks": [{"type": "strong"}]
                        }]
                    })

                adf_content.append({
                    "type": "panel",
                    "attrs": {"panelType": panel_type},
                    "content": panel_content
                })
            else:
                adf_content.append({
                    "type": "blockquote",
                    "content": [{
                        "type": "paragraph",
                        "content": parse_inline_text(content)
                    }]
                })
            continue

        # 8. Regular lines — groupées dans un paragraphe compact avec hardBreaks
        if stripped == "":
            flush_paragraph()
        else:
            inline_nodes = parse_inline_text(line)
            if inline_nodes:
                if paragraph_nodes:
                    paragraph_nodes.append({"type": "hardBreak"})
                paragraph_nodes.extend(inline_nodes)

    flush_paragraph()
    flush_list()
    flush_table()

    return {
        "version": 1,
        "type": "doc",
        "content": adf_content
    }
