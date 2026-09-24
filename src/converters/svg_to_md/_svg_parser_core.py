"""
mLoop Framework — Noyau du parseur spatial SVG (extraction MLOOP-176-BE, Q1-A).

Contient `SvgSpatialParserCore` : parsing XML, traversée récursive de l'arbre
SVG (rect/circle/text/path), résolution des transformations et repli regex
en cas d'échec ElementTree. Combiné à `ParserClassifyMixin` dans `__init__.py`
pour former l'API publique `SvgSpatialParser` (rétrocompatibilité stricte).
"""

import re
import xml.etree.ElementTree as ET
from typing import Optional, List, Tuple

from src.converters.svg_to_md._svg_models import UIElement, compute_svg_path_bbox_accurate
from src.utils.logger import get_logger

logger = get_logger("converters.svg_to_md")


class SvgSpatialParserCore:
    """
    Parseur géométrique et spatial déterministe pour fichiers SVG.
    Supporte les SVGs Figma standard et les SVGs avec textes vectorisés/outlined.
    """

    def __init__(self, svg_content: str, filename: str):
        self.raw_content = svg_content
        self.filename = filename
        self.elements: List[UIElement] = []
        self.view_box = (0.0, 0.0, 390.0, 844.0)
        # True si le SVG ne contient aucune balise <text>/<tspan> (texte vectorisé/outlined,
        # ex. export Figma "Outline text") — condition de déclenchement du pont OCR (Phase 1).
        self.is_vectorized = False

    def parse(self) -> List[UIElement]:
        try:
            cleaned_svg = re.sub(r'\sxmlns(:\w+)?="[^"]+"', "", self.raw_content)
            cleaned_svg = re.sub(r"\b\w+:(\w+)=", r"\1=", cleaned_svg)
            root = ET.fromstring(cleaned_svg)

            vb = root.attrib.get("viewBox", "")
            if vb:
                parts = [float(p) for p in vb.replace(",", " ").split() if p]
                if len(parts) == 4:
                    self.view_box = (parts[0], parts[1], parts[2], parts[3])
            else:
                w = float(re.sub(r"[^\d.]", "", root.attrib.get("width", "390")) or 390)
                h = float(re.sub(r"[^\d.]", "", root.attrib.get("height", "844")) or 844)
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
                self.is_vectorized = True
                self._classify_outlined_svg(containers, paths_boxes)

            # Tri spatial strict : De haut en bas (Y), puis de gauche à droite (X)
            self.elements.sort(key=lambda e: (round(e.y / 20.0) * 20.0, e.x))
            return self.elements

        except Exception as e:
            logger.warning(
                "Échec du parse XML du SVG, repli sur le parseur regex de secours",
                exc_info=True,
                extra={
                    "component": "converters.svg_to_md",
                    "operation": "_parse_svg",
                    "error": str(e),
                },
            )
            return self._fallback_regex_parse()

    def _parse_transform(self, transform_str: str) -> Tuple[float, float]:
        if not transform_str:
            return 0.0, 0.0
        tx, ty = 0.0, 0.0
        m_trans = re.search(r"translate\(\s*([\d\.\-]+)[\s,]+([\d\.\-]+)?\s*\)", transform_str)
        if m_trans:
            tx = float(m_trans.group(1))
            ty = float(m_trans.group(2)) if m_trans.group(2) else 0.0
        m_mat = re.search(
            r"matrix\([^,]+,[^,]+,[^,]+,[^,]+,\s*([\d\.\-]+)[\s,]+([\d\.\-]+)\s*\)",
            transform_str,
        )
        if m_mat:
            tx = float(m_mat.group(1))
            ty = float(m_mat.group(2))
        return tx, ty

    def _traverse_node(
        self,
        node: ET.Element,
        cur_tx: float,
        cur_ty: float,
        containers: list,
        texts: list,
        paths_boxes: list,
    ):
        tx, ty = self._parse_transform(node.attrib.get("transform", ""))
        accum_x = cur_tx + tx
        accum_y = cur_ty + ty

        tag = node.tag.lower()
        node_id = node.attrib.get("id", "") or node.attrib.get("data-name", "")

        # Rectangles
        if tag == "rect":
            try:
                x = float(node.attrib.get("x", 0.0)) + accum_x
                y = float(node.attrib.get("y", 0.0)) + accum_y
                w = float(node.attrib.get("width", 0.0))
                h = float(node.attrib.get("height", 0.0))
                rx = float(node.attrib.get("rx", 0.0))
                fill = node.attrib.get("fill", "").lower()
                stroke = node.attrib.get("stroke", "").lower()

                if not (
                    w >= self.view_box[2] * 0.95
                    and h >= self.view_box[3] * 0.95
                    and x <= 5
                    and y <= 5
                ):
                    if w > 5 and h > 5:
                        containers.append(
                            {
                                "id": node_id or f"rect_{len(containers)}",
                                "x": x,
                                "y": y,
                                "width": w,
                                "height": h,
                                "rx": rx,
                                "fill": fill,
                                "stroke": stroke,
                            }
                        )
            except Exception as e:
                logger.debug(
                    "Attributs de rect SVG invalides, élément ignoré",
                    exc_info=True,
                    extra={
                        "component": "converters.svg_to_md",
                        "operation": "_traverse_node",
                        "node_tag": "rect",
                        "node_id": node_id,
                        "error": str(e),
                    },
                )

        # Cercles
        elif tag == "circle":
            try:
                cx = float(node.attrib.get("cx", 0.0)) + accum_x
                cy = float(node.attrib.get("cy", 0.0)) + accum_y
                r = float(node.attrib.get("r", 0.0))
                fill = node.attrib.get("fill", "").lower()
                if r > 3:
                    containers.append(
                        {
                            "id": node_id or f"circle_{len(containers)}",
                            "x": cx - r,
                            "y": cy - r,
                            "width": r * 2,
                            "height": r * 2,
                            "rx": r,
                            "fill": fill,
                            "stroke": node.attrib.get("stroke", ""),
                        }
                    )
            except Exception as e:
                logger.debug(
                    "Attributs de circle SVG invalides, élément ignoré",
                    exc_info=True,
                    extra={
                        "component": "converters.svg_to_md",
                        "operation": "_traverse_node",
                        "node_tag": "circle",
                        "node_id": node_id,
                        "error": str(e),
                    },
                )

        # Textes explicites
        elif tag == "text":
            try:
                x = float(node.attrib.get("x", 0.0)) + accum_x
                y = float(node.attrib.get("y", 0.0)) + accum_y
                font_size = float(re.sub(r"[^\d.]", "", node.attrib.get("font-size", "14")) or 14)
                font_weight = node.attrib.get("font-weight", "").lower()

                txt_parts = []
                if node.text and node.text.strip():
                    txt_parts.append(node.text.strip())
                for child in node:
                    if child.text and child.text.strip():
                        txt_parts.append(child.text.strip())
                full_text = " ".join(txt_parts).strip()

                if full_text:
                    texts.append(
                        {
                            "id": node_id or f"text_{len(texts)}",
                            "text": full_text,
                            "x": x,
                            "y": y,
                            "font_size": font_size,
                            "font_weight": font_weight,
                        }
                    )
            except Exception as e:
                logger.debug(
                    "Attributs de text SVG invalides, élément ignoré",
                    exc_info=True,
                    extra={
                        "component": "converters.svg_to_md",
                        "operation": "_traverse_node",
                        "node_tag": "text",
                        "node_id": node_id,
                        "error": str(e),
                    },
                )

        # Chemins vectoriels (Paths)
        elif tag == "path":
            try:
                d = node.attrib.get("d", "")
                fill = node.attrib.get("fill", "").lower()
                stroke = node.attrib.get("stroke", "").lower()
                bbox = compute_svg_path_bbox_accurate(d)
                if bbox:
                    bx, by, bw, bh = bbox
                    bx += accum_x
                    by += accum_y
                    if not (
                        bw >= self.view_box[2] * 0.95
                        and bh >= self.view_box[3] * 0.95
                        and bx <= 5
                        and by <= 5
                    ):
                        if bw > 3 and bh > 3:
                            paths_boxes.append(
                                {
                                    "id": node_id or f"path_{len(paths_boxes)}",
                                    "x": bx,
                                    "y": by,
                                    "width": bw,
                                    "height": bh,
                                    "fill": fill,
                                    "stroke": stroke,
                                }
                            )
            except Exception as e:
                logger.debug(
                    "BBox de path SVG non calculable, élément ignoré",
                    exc_info=True,
                    extra={
                        "component": "converters.svg_to_md",
                        "operation": "_traverse_node",
                        "node_tag": "path",
                        "node_id": node_id,
                        "error": str(e),
                    },
                )

        for child in node:
            self._traverse_node(child, accum_x, accum_y, containers, texts, paths_boxes)

    def _fallback_regex_parse(self) -> List[UIElement]:
        clean_title = self.filename.replace(".svg", "").replace("_", " ").title()
        return [
            UIElement(
                id="fallback_header",
                text=f"Écran : {clean_title}",
                elem_type="heading",
                x=20.0,
                y=40.0,
                width=350.0,
                height=40.0,
            )
        ]
