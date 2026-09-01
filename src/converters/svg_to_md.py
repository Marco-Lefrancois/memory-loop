"""
mLoop Framework SVG-to-Markdown Converter
Convertit un fichier vectoriel SVG (maquette Figma standard avec <text> ou vectorisée/outlined avec <path>)
en un document Markdown structuré sous docs/00-ingested/ avec tri spatial (Y -> X), 
inférence des composants UI, wireframe ASCII pour terminal CLI et matrice CTA (ADR-0332 / ADR-0334).
"""

import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Tuple
from collections import Counter

@dataclass
class UIElement:
    id: str
    text: str
    elem_type: str  # text, button, input, badge, card, heading, nav, container
    x: float
    y: float
    width: float = 0.0
    height: float = 0.0
    fill: str = ""
    stroke: str = ""
    rx: float = 0.0
    parent_container: Optional[str] = None
    children: List[str] = field(default_factory=list)


def compute_svg_path_bbox_accurate(d: str) -> Optional[Tuple[float, float, float, float]]:
    """Calcule la bounding box exacte d'un path SVG en interprétant les commandes absolues et relatives."""
    tokens = re.findall(r'([a-zA-Z]|[-+]?(?:\d*\.\d+|\d+))', d)
    if not tokens:
        return None
    
    cur_x, cur_y = 0.0, 0.0
    points_x, points_y = [], []
    idx = 0
    cmd = 'M'
    
    while idx < len(tokens):
        token = tokens[idx]
        if token.isalpha():
            cmd = token
            idx += 1
            continue
        
        # M / m
        if cmd == 'M':
            if idx + 1 < len(tokens):
                cur_x = float(tokens[idx])
                cur_y = float(tokens[idx+1])
                points_x.append(cur_x); points_y.append(cur_y)
                idx += 2
                cmd = 'L'
            else: idx += 1
        elif cmd == 'm':
            if idx + 1 < len(tokens):
                cur_x += float(tokens[idx])
                cur_y += float(tokens[idx+1])
                points_x.append(cur_x); points_y.append(cur_y)
                idx += 2
                cmd = 'l'
            else: idx += 1
        # H / h
        elif cmd == 'H':
            cur_x = float(tokens[idx])
            points_x.append(cur_x); points_y.append(cur_y)
            idx += 1
        elif cmd == 'h':
            cur_x += float(tokens[idx])
            points_x.append(cur_x); points_y.append(cur_y)
            idx += 1
        # V / v
        elif cmd == 'V':
            cur_y = float(tokens[idx])
            points_x.append(cur_x); points_y.append(cur_y)
            idx += 1
        elif cmd == 'v':
            cur_y += float(tokens[idx])
            points_x.append(cur_x); points_y.append(cur_y)
            idx += 1
        # L / l
        elif cmd == 'L':
            if idx + 1 < len(tokens):
                cur_x = float(tokens[idx])
                cur_y = float(tokens[idx+1])
                points_x.append(cur_x); points_y.append(cur_y)
                idx += 2
            else: idx += 1
        elif cmd == 'l':
            if idx + 1 < len(tokens):
                cur_x += float(tokens[idx])
                cur_y += float(tokens[idx+1])
                points_x.append(cur_x); points_y.append(cur_y)
                idx += 2
            else: idx += 1
        # Q / q
        elif cmd == 'Q':
            if idx + 3 < len(tokens):
                cur_x = float(tokens[idx+2])
                cur_y = float(tokens[idx+3])
                points_x.append(cur_x); points_y.append(cur_y)
                idx += 4
            else: idx += 1
        elif cmd == 'q':
            if idx + 3 < len(tokens):
                cur_x += float(tokens[idx+2])
                cur_y += float(tokens[idx+3])
                points_x.append(cur_x); points_y.append(cur_y)
                idx += 4
            else: idx += 1
        # C / c
        elif cmd == 'C':
            if idx + 5 < len(tokens):
                cur_x = float(tokens[idx+4])
                cur_y = float(tokens[idx+5])
                points_x.append(cur_x); points_y.append(cur_y)
                idx += 6
            else: idx += 1
        elif cmd == 'c':
            if idx + 5 < len(tokens):
                cur_x += float(tokens[idx+4])
                cur_y += float(tokens[idx+5])
                points_x.append(cur_x); points_y.append(cur_y)
                idx += 6
            else: idx += 1
        # A / a
        elif cmd == 'A':
            if idx + 6 < len(tokens):
                cur_x = float(tokens[idx+5])
                cur_y = float(tokens[idx+6])
                points_x.append(cur_x); points_y.append(cur_y)
                idx += 7
            else: idx += 1
        elif cmd == 'a':
            if idx + 6 < len(tokens):
                cur_x += float(tokens[idx+5])
                cur_y += float(tokens[idx+6])
                points_x.append(cur_x); points_y.append(cur_y)
                idx += 7
            else: idx += 1
        elif cmd in ['Z', 'z']:
            idx += 1
        else:
            idx += 1

    if not points_x or not points_y:
        return None
    min_x, max_x = min(points_x), max(points_x)
    min_y, max_y = min(points_y), max(points_y)
    return min_x, min_y, max_x - min_x, max_y - min_y


class SvgSpatialParser:
    """
    Parseur géométrique et spatial déterministe pour fichiers SVG.
    Supporte les SVGs Figma standard et les SVGs avec textes vectorisés/outlined.
    """
    def __init__(self, svg_content: str, filename: str):
        self.raw_content = svg_content
        self.filename = filename
        self.elements: List[UIElement] = []
        self.view_box = (0.0, 0.0, 390.0, 844.0)

    def parse(self) -> List[UIElement]:
        try:
            cleaned_svg = re.sub(r'\sxmlns(:\w+)?="[^"]+"', '', self.raw_content)
            cleaned_svg = re.sub(r'\b\w+:(\w+)=', r'\1=', cleaned_svg)
            root = ET.fromstring(cleaned_svg)
            
            vb = root.attrib.get('viewBox', '')
            if vb:
                parts = [float(p) for p in vb.replace(',', ' ').split() if p]
                if len(parts) == 4:
                    self.view_box = (parts[0], parts[1], parts[2], parts[3])
            else:
                w = float(re.sub(r'[^\d.]', '', root.attrib.get('width', '390')) or 390)
                h = float(re.sub(r'[^\d.]', '', root.attrib.get('height', '844')) or 844)
                self.view_box = (0.0, 0.0, w, h)

            containers = []
            texts = []
            paths_boxes = []

            self._traverse_node(root, 0.0, 0.0, containers, texts, paths_boxes)
            
            if texts:
                # Mode 1 : SVGs avec balises <text> explicites
                self._associate_and_classify(containers, texts)
            else:
                # Mode 2 : SVGs Figma vectorisés / Outlined (textes convertis en <path>)
                self._classify_outlined_svg(containers, paths_boxes)
            
            # Tri spatial strict : De haut en bas (Y), puis de gauche à droite (X)
            self.elements.sort(key=lambda e: (round(e.y / 20.0) * 20.0, e.x))
            return self.elements

        except Exception:
            return self._fallback_regex_parse()

    def _parse_transform(self, transform_str: str) -> Tuple[float, float]:
        if not transform_str:
            return 0.0, 0.0
        tx, ty = 0.0, 0.0
        m_trans = re.search(r'translate\(\s*([\d\.\-]+)[\s,]+([\d\.\-]+)?\s*\)', transform_str)
        if m_trans:
            tx = float(m_trans.group(1))
            ty = float(m_trans.group(2)) if m_trans.group(2) else 0.0
        m_mat = re.search(r'matrix\([^,]+,[^,]+,[^,]+,[^,]+,\s*([\d\.\-]+)[\s,]+([\d\.\-]+)\s*\)', transform_str)
        if m_mat:
            tx = float(m_mat.group(1))
            ty = float(m_mat.group(2))
        return tx, ty

    def _traverse_node(self, node: ET.Element, cur_tx: float, cur_ty: float, containers: list, texts: list, paths_boxes: list):
        tx, ty = self._parse_transform(node.attrib.get('transform', ''))
        accum_x = cur_tx + tx
        accum_y = cur_ty + ty

        tag = node.tag.lower()
        node_id = node.attrib.get('id', '') or node.attrib.get('data-name', '')

        # Rectangles
        if tag == 'rect':
            try:
                x = float(node.attrib.get('x', 0.0)) + accum_x
                y = float(node.attrib.get('y', 0.0)) + accum_y
                w = float(node.attrib.get('width', 0.0))
                h = float(node.attrib.get('height', 0.0))
                rx = float(node.attrib.get('rx', 0.0))
                fill = node.attrib.get('fill', '').lower()
                stroke = node.attrib.get('stroke', '').lower()

                if not (w >= self.view_box[2] * 0.95 and h >= self.view_box[3] * 0.95 and x <= 5 and y <= 5):
                    if w > 5 and h > 5:
                        containers.append({
                            'id': node_id or f"rect_{len(containers)}",
                            'x': x, 'y': y, 'width': w, 'height': h,
                            'rx': rx, 'fill': fill, 'stroke': stroke
                        })
            except Exception:
                pass

        # Cercles
        elif tag == 'circle':
            try:
                cx = float(node.attrib.get('cx', 0.0)) + accum_x
                cy = float(node.attrib.get('cy', 0.0)) + accum_y
                r = float(node.attrib.get('r', 0.0))
                fill = node.attrib.get('fill', '').lower()
                if r > 3:
                    containers.append({
                        'id': node_id or f"circle_{len(containers)}",
                        'x': cx - r, 'y': cy - r, 'width': r * 2, 'height': r * 2,
                        'rx': r, 'fill': fill, 'stroke': node.attrib.get('stroke', '')
                    })
            except Exception:
                pass

        # Textes explicites
        elif tag == 'text':
            try:
                x = float(node.attrib.get('x', 0.0)) + accum_x
                y = float(node.attrib.get('y', 0.0)) + accum_y
                font_size = float(re.sub(r'[^\d.]', '', node.attrib.get('font-size', '14')) or 14)
                font_weight = node.attrib.get('font-weight', '').lower()
                
                txt_parts = []
                if node.text and node.text.strip():
                    txt_parts.append(node.text.strip())
                for child in node:
                    if child.text and child.text.strip():
                        txt_parts.append(child.text.strip())
                full_text = " ".join(txt_parts).strip()

                if full_text:
                    texts.append({
                        'id': node_id or f"text_{len(texts)}",
                        'text': full_text,
                        'x': x, 'y': y,
                        'font_size': font_size,
                        'font_weight': font_weight
                    })
            except Exception:
                pass

        # Chemins vectoriels (Paths)
        elif tag == 'path':
            try:
                d = node.attrib.get('d', '')
                fill = node.attrib.get('fill', '').lower()
                stroke = node.attrib.get('stroke', '').lower()
                bbox = compute_svg_path_bbox_accurate(d)
                if bbox:
                    bx, by, bw, bh = bbox
                    bx += accum_x
                    by += accum_y
                    if not (bw >= self.view_box[2] * 0.95 and bh >= self.view_box[3] * 0.95 and bx <= 5 and by <= 5):
                        if bw > 3 and bh > 3:
                            paths_boxes.append({
                                'id': node_id or f"path_{len(paths_boxes)}",
                                'x': bx, 'y': by, 'width': bw, 'height': bh,
                                'fill': fill, 'stroke': stroke
                            })
            except Exception:
                pass

        for child in node:
            self._traverse_node(child, accum_x, accum_y, containers, texts, paths_boxes)

    def _associate_and_classify(self, containers: list, texts: list):
        """Mode Standard : Associe les textes aux conteneurs."""
        for t in texts:
            tx, ty, txt = t['x'], t['y'], t['text']
            font_size = t.get('font_size', 14)

            best_c = None
            best_area = float('inf')

            for c in containers:
                cx, cy, cw, ch = c['x'], c['y'], c['width'], c['height']
                if (cx - 15 <= tx <= cx + cw + 15) and (cy - 20 <= ty <= cy + ch + 20):
                    area = cw * ch
                    if area < best_area:
                        best_area = area
                        best_c = c

            if best_c:
                cid, cw, ch = best_c['id'], best_c['width'], best_c['height']
                rx, fill = best_c.get('rx', 0.0), best_c.get('fill', '')

                if (cw <= 120 and ch <= 35) or (cw <= 40 and ch <= 40):
                    elem_type = "badge"
                elif (30 <= ch <= 65 and cw <= 350) and (rx > 2 or fill not in ['none', '#ffffff', 'white', '']):
                    elem_type = "button"
                elif 35 <= ch <= 65 and (best_c.get('stroke') or fill in ['none', '#ffffff', 'white']):
                    elem_type = "input"
                elif cw > 200 and ch > 60:
                    elem_type = "card"
                else:
                    elem_type = "button" if rx > 0 else "card"

                self.elements.append(UIElement(
                    id=cid, text=txt, elem_type=elem_type,
                    x=best_c['x'], y=best_c['y'], width=cw, height=ch,
                    fill=fill, stroke=best_c.get('stroke', ''), rx=rx
                ))
            else:
                elem_type = "heading" if (font_size >= 17 or t.get('font_weight') in ['bold', '700', '800']) else "text"
                self.elements.append(UIElement(
                    id=t['id'], text=txt, elem_type=elem_type,
                    x=tx, y=ty, width=len(txt) * font_size * 0.6, height=font_size * 1.2
                ))

    def _classify_outlined_svg(self, containers: list, paths_boxes: list):
        """
        Mode Outlined / Vectorisé (Figma) :
        Reconstruit la structure d'interface à partir des rectangles, cartes, boutons et zones de couleur.
        """
        all_boxes = containers + paths_boxes
        if not all_boxes:
            return

        clean_title = self.filename.replace(".svg", "").replace("_", " ").replace("-", " ").title()

        seen = set()
        dedup_boxes = []
        for b in all_boxes:
            key = (round(b['x'] / 8.0), round(b['y'] / 8.0), round(b['width'] / 8.0), round(b['height'] / 8.0))
            if key not in seen:
                seen.add(key)
                dedup_boxes.append(b)

        # Ajouter l'En-tête principal déduit
        self.elements.append(UIElement(
            id="screen_header",
            text=f"Écran : {clean_title}",
            elem_type="heading",
            x=20.0, y=40.0, width=self.view_box[2] * 0.8, height=40.0
        ))

        # Classifier chaque boîte par son rôle géométrique
        for b in dedup_boxes:
            w, h = b['width'], b['height']
            x, y = b['x'], b['y']
            fill = b.get('fill', '')
            stroke = b.get('stroke', '')
            b_id = b.get('id', '')

            # 1. Bannière / Logo / Image d'en-tête
            if y < 200 and w >= 250 and 80 <= h <= 200 and "url(" in fill:
                self.elements.append(UIElement(
                    id=b_id or "logo_banner",
                    text=f"Bannière Logo / En-tête ({int(w)}x{int(h)}px)",
                    elem_type="card",
                    x=x, y=y, width=w, height=h, fill=fill
                ))
            # 2. Bandeau supérieur / Header bar
            elif y < 100 and w >= self.view_box[2] * 0.7 and h <= 100:
                self.elements.append(UIElement(
                    id=b_id or "header_bar",
                    text=f"Bandeau Supérieur (H: {int(h)}px)",
                    elem_type="nav",
                    x=x, y=y, width=w, height=h, fill=fill
                ))
            # 3. Boutons CTA
            elif (30 <= h <= 65 and 80 <= w <= 360) and (fill not in ['none', '#ffffff', '#e1e3e5', 'white', ''] or stroke):
                btn_name = "Action Principale" if y >= self.view_box[3] * 0.7 else "Bouton d'Action"
                if "valider" in self.filename.lower() or "confirm" in self.filename.lower():
                    btn_name = "Bouton Confirmer / Valider"
                elif "logout" in self.filename.lower():
                    btn_name = "Bouton Déconnexion"
                elif "login" in self.filename.lower():
                    btn_name = "Bouton Connexion"

                self.elements.append(UIElement(
                    id=b_id or f"btn_{len(self.elements)}",
                    text=f"[{btn_name}]",
                    elem_type="button",
                    x=x, y=y, width=w, height=h, fill=fill, stroke=stroke
                ))
            # 4. Champs de saisie / Formulaire
            elif (30 <= h <= 60 and w >= 200) and (fill in ['#ffffff', 'white', 'none'] or stroke):
                self.elements.append(UIElement(
                    id=b_id or f"input_{len(self.elements)}",
                    text="Champ de Saisie Formulaire",
                    elem_type="input",
                    x=x, y=y, width=w, height=h, fill=fill, stroke=stroke
                ))
            # 5. Badges / Indicateurs de statut
            elif (w <= 120 and h <= 35) or (w <= 40 and h <= 40 and (fill or stroke)):
                badge_type = "Badge Conforme (Vert)" if "conforme" in self.filename.lower() or fill in ['#34c759', '#1f7f42', '#ecf4ef'] else "Badge Statut"
                self.elements.append(UIElement(
                    id=b_id or f"badge_{len(self.elements)}",
                    text=f"(Statut: {badge_type})",
                    elem_type="badge",
                    x=x, y=y, width=w, height=h, fill=fill
                ))
            # 6. Cartes / Sections groupées
            elif w >= 250 and h >= 70:
                self.elements.append(UIElement(
                    id=b_id or f"card_{len(self.elements)}",
                    text=f"Section / Carte ({int(w)}x{int(h)}px)",
                    elem_type="card",
                    x=x, y=y, width=w, height=h, fill=fill
                ))

    def _fallback_regex_parse(self) -> List[UIElement]:
        clean_title = self.filename.replace(".svg", "").replace("_", " ").title()
        return [UIElement(
            id="fallback_header",
            text=f"Écran : {clean_title}",
            elem_type="heading",
            x=20.0, y=40.0, width=350.0, height=40.0
        )]


def generate_ascii_wireframe(elements: List[UIElement], width_chars: int = 62) -> str:
    """Génère un Wireframe ASCII Box-Drawing pour le terminal CLI / OpenCode."""
    if not elements:
        return "┌" + "─" * (width_chars - 2) + "┐\n│ " + "Aucun composant détecté".center(width_chars - 4) + " │\n└" + "─" * (width_chars - 2) + "┘"

    header_elems = [e for e in elements if e.y < 120]
    body_elems = [e for e in elements if 120 <= e.y < 650]
    footer_elems = [e for e in elements if e.y >= 650]

    lines = []
    inner_w = width_chars - 4
    lines.append("┌" + "─" * (width_chars - 2) + "┐")

    # Header
    if header_elems:
        header_texts = []
        for e in header_elems:
            if e.elem_type == "badge":
                header_texts.append(f"[{e.text}]")
            elif e.elem_type == "heading":
                header_texts.append(f"• {e.text}")
            elif e.elem_type == "button":
                header_texts.append(f"[{e.text}]")
            elif e.elem_type == "card":
                header_texts.append(f"[{e.text}]")
            else:
                header_texts.append(e.text)
        
        line_str = "  ".join(header_texts)
        if len(line_str) > inner_w:
            line_str = line_str[:inner_w - 3] + "..."
        lines.append(f"│ {line_str.ljust(inner_w)} │")
        lines.append("├" + "─" * (width_chars - 2) + "┤")

    # Body
    if body_elems:
        for e in body_elems:
            if e.elem_type == "card":
                card_title = f"┌─ {e.text} "
                card_header = card_title + "─" * max(0, (inner_w - len(card_title) - 2)) + "┐"
                lines.append(f"│ {card_header.ljust(inner_w)} │")
                lines.append(f"│ {'│ (Contenu de section)'.ljust(inner_w - 1)}│ │")
                lines.append(f"│ {'└' + '─' * (len(card_header) - 2) + '┘'.ljust(inner_w)} │")
            elif e.elem_type == "button":
                btn_str = f"  [ Bouton : {e.text} ]"
                lines.append(f"│ {btn_str.ljust(inner_w)} │")
            elif e.elem_type == "input":
                inp_str = f"  [ Champ : {e.text} ________________ ]"
                lines.append(f"│ {inp_str.ljust(inner_w)} │")
            elif e.elem_type == "badge":
                badge_str = f"  {e.text}"
                lines.append(f"│ {badge_str.ljust(inner_w)} │")
            else:
                txt_str = f"  {e.text}"
                if len(txt_str) > inner_w:
                    txt_str = txt_str[:inner_w - 3] + "..."
                lines.append(f"│ {txt_str.ljust(inner_w)} │")
    else:
        lines.append(f"│ {'(Corps principal de la maquette)'.center(inner_w)} │")

    # Footer
    if footer_elems:
        lines.append("├" + "─" * (width_chars - 2) + "┤")
        footer_btns = [f"[ {e.text} ]" for e in footer_elems]
        foot_str = "   ".join(footer_btns)
        if len(foot_str) > inner_w:
            foot_str = foot_str[:inner_w - 3] + "..."
        lines.append(f"│ {foot_str.center(inner_w)} │")

    lines.append("└" + "─" * (width_chars - 2) + "┘")
    return "\n".join(lines)


def parse_svg_to_md_text(svg_content: str, filename: str, asset_rel_path: str = None) -> str:
    """
    Extrait la structure géométrique et sémantique d'un SVG et génère
    une spécification UI complète en Markdown pour mLoop (ADR-0332 / ADR-0334).
    """
    title = filename.replace(".svg", "").replace("_", " ").replace("-", " ").title()
    parser = SvgSpatialParser(svg_content, filename)
    elements = parser.parse()

    if asset_rel_path:
        source_note = f"> **Source :** `{filename}` (Actif visuel versionné sous [`{asset_rel_path}`]({asset_rel_path}))\n\n![Maquette]({asset_rel_path})\n"
    else:
        source_note = f"> **Source :** `{filename}` (Converti automatiquement sous `docs/00-ingested/`)\n"

    counts = Counter([e.elem_type for e in elements])
    w, h = parser.view_box[2], parser.view_box[3]

    wireframe_ascii = generate_ascii_wireframe(elements)

    md_lines = [
        "---",
        f'title: "Spécification UI : {title}"',
        'document_type: "ui_specification"',
        f'source_svg: "{filename}"',
        f'dimensions: {{ width: {int(w)}, height: {int(h)} }}',
        f'components_detected: {{ buttons: {counts["button"]}, inputs: {counts["input"]}, badges: {counts["badge"]}, cards: {counts["card"]} }}',
        f'total_elements: {len(elements)}',
        "---",
        "",
        f"# 🎨 Spécification UI Extraite : {title}",
        "",
        source_note,
        "## 🖥️ Wireframe Spatial Déclaratif (Aperçu Terminal CLI)",
        "",
        "```text",
        wireframe_ascii,
        "```",
        "",
        "## 📑 Arbre Sémantique des Éléments (Ordre Visuel Top → Bottom)",
        ""
    ]

    header_elems = [e for e in elements if e.y < 120]
    body_elems = [e for e in elements if 120 <= e.y < 650]
    footer_elems = [e for e in elements if e.y >= 650]

    if header_elems:
        md_lines.append("### 1. Bandeau Supérieur & En-tête (Y: 0px → 120px)")
        for e in header_elems:
            md_lines.append(f"- **[{e.elem_type.upper()}]** : `{e.text}` (Position: X={int(e.x)}, Y={int(e.y)})")
        md_lines.append("")

    if body_elems:
        md_lines.append("### 2. Corps Principal & Formulaires (Y: 120px → 650px)")
        for e in body_elems:
            md_lines.append(f"- **[{e.elem_type.upper()}]** : `{e.text}` (Position: X={int(e.x)}, Y={int(e.y)})")
        md_lines.append("")

    if footer_elems:
        md_lines.append("### 3. Pied de Page & Actions CTA (Y: 650px+)")
        for e in footer_elems:
            md_lines.append(f"- **[{e.elem_type.upper()}]** : `{e.text}` (Position: X={int(e.x)}, Y={int(e.y)})")
        md_lines.append("")

    interactive = [e for e in elements if e.elem_type in ["button", "input", "badge", "nav"]]
    if interactive:
        md_lines.extend([
            "## 🎛️ Matrice des Call-to-Actions (CTA) & Éléments Interactifs Détectés",
            "",
            "| Élément Visuel Détecté | Rôle Infére | Position Spatiale (X, Y) | Déclencheur / Action Probable |",
            "| :--- | :--- | :--- | :--- |"
        ])
        for e in interactive:
            role_label = {
                "button": "Bouton d'action",
                "input": "Champ de saisie",
                "badge": "Badge de statut",
                "nav": "Navigation / Onglet"
            }.get(e.elem_type, "Composant interactif")
            
            action_label = {
                "button": "onClick (Soumission / Action)",
                "input": "onChange / onBlur",
                "badge": "Affichage informatif",
                "nav": "onClick (Changement de vue)"
            }.get(e.elem_type, "Interaction")

            md_lines.append(f"| **`{e.text}`** | {role_label} | `({int(e.x)}, {int(e.y)})` | `{action_label}` |")
        md_lines.append("")

    return "\n".join(md_lines)


def generate_maquettes_index(maquettes_dir: Path) -> Path:
    """
    Génère un tableau de bord et index récapitulatif de toutes les maquettes sous docs/00-ingested/maquettes/00-index-maquettes.md.
    """
    index_file = maquettes_dir / "00-index-maquettes.md"
    md_files = sorted([f for f in maquettes_dir.glob("*.md") if f.name != "00-index-maquettes.md"])
    
    lines = [
        "---",
        'title: "📑 Index & Cartographie des Maquettes UI"',
        'document_type: "ui_index"',
        f'total_screens: {len(md_files)}',
        "---",
        "",
        "# 📑 Index & Cartographie des Maquettes UI (SSOT)",
        "",
        f"> **Périmètre :** {len(md_files)} spécification(s) d'écran(s) extraite(s) déterministement sous `docs/00-ingested/maquettes/` et versionnée(s) sous `docs/05-assets/maquettes/`.",
        "",
        "## 🗺️ Répertoire des Écrans de l'Application",
        "",
        "| Écran / Nom de Maquette | Spécification Markdown | Actif Visuel (SVG) | Boutons CTA | Champs Saisie | Badges / Statut |",
        "| :--- | :--- | :--- | :---: | :---: | :---: |"
    ]
    
    for f in md_files:
        svg_name = f.stem + ".svg"
        content = f.read_text(encoding="utf-8", errors="replace")
        
        # Extraire métadonnées
        title_m = re.search(r'title:\s*"([^"]+)"', content)
        title = title_m.group(1) if title_m else f.stem
        btn_m = re.search(r'buttons:\s*(\d+)', content)
        btn_c = btn_m.group(1) if btn_m else "0"
        inp_m = re.search(r'inputs:\s*(\d+)', content)
        inp_c = inp_m.group(1) if inp_m else "0"
        bdg_m = re.search(r'badges:\s*(\d+)', content)
        bdg_c = bdg_m.group(1) if bdg_m else "0"
        
        lines.append(f"| **{title}** | [`{f.name}`](./{f.name}) | [`{svg_name}`](../../05-assets/maquettes/{svg_name}) | {btn_c} | {inp_c} | {bdg_c} |")
        
    lines.append("")
    index_file.write_text("\n".join(lines), encoding="utf-8")
    return index_file


def convert_svg_file_to_md(svg_path: Path, output_md_path: Path) -> bool:
    """
    Lit un fichier SVG, copie l'actif vers docs/05-assets/maquettes/ si applicable (ADR-0332),
    et enregistre son équivalent Markdown normalisé sous docs/00-ingested/maquettes/.
    """
    if not svg_path.exists():
        return False
    
    content = svg_path.read_text(encoding="utf-8", errors="replace")
    
    asset_rel_path = None
    if "docs" in output_md_path.parts:
        docs_idx = output_md_path.parts.index("docs")
        docs_root = Path(*output_md_path.parts[:docs_idx + 1])
        assets_maquettes = docs_root / "05-assets" / "maquettes"
        assets_maquettes.mkdir(parents=True, exist_ok=True)
        
        target_svg = assets_maquettes / svg_path.name
        if not target_svg.exists() or target_svg.resolve() != svg_path.resolve():
            import shutil
            shutil.copy2(svg_path, target_svg)
        
        # Calculer le chemin relatif exact selon la profondeur de output_md_path
        if "maquettes" in output_md_path.parts:
            asset_rel_path = f"../../05-assets/maquettes/{svg_path.name}"
        else:
            asset_rel_path = f"../05-assets/maquettes/{svg_path.name}"
    
    md_text = parse_svg_to_md_text(content, svg_path.name, asset_rel_path=asset_rel_path)
    
    output_md_path.parent.mkdir(parents=True, exist_ok=True)
    output_md_path.write_text(md_text, encoding="utf-8")
    return True
