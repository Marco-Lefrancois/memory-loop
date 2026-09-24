"""
mLoop Framework — Modèles géométriques SVG (extraction MLOOP-176-BE, Q1-A).

Contient le modèle de données `UIElement` (composant d'interface inféré) et
la fonction pure de calcul de bounding box exacte de path SVG. Aucun effet de
bord à l'import (ADR-0369 / MODULAR_EXTRACTION_PROTOCOL §3.3).
"""

import re
from dataclasses import dataclass, field
from typing import Optional, List, Tuple


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


def compute_svg_path_bbox_accurate(
    d: str,
) -> Optional[Tuple[float, float, float, float]]:
    """Calcule la bounding box exacte d'un path SVG en interprétant les commandes absolues et relatives."""
    tokens = re.findall(r"([a-zA-Z]|[-+]?(?:\d*\.\d+|\d+))", d)
    if not tokens:
        return None

    cur_x, cur_y = 0.0, 0.0
    points_x, points_y = [], []
    idx = 0
    cmd = "M"

    while idx < len(tokens):
        token = tokens[idx]
        if token.isalpha():
            cmd = token
            idx += 1
            continue

        # M / m
        if cmd == "M":
            if idx + 1 < len(tokens):
                cur_x = float(tokens[idx])
                cur_y = float(tokens[idx + 1])
                points_x.append(cur_x)
                points_y.append(cur_y)
                idx += 2
                cmd = "L"
            else:
                idx += 1
        elif cmd == "m":
            if idx + 1 < len(tokens):
                cur_x += float(tokens[idx])
                cur_y += float(tokens[idx + 1])
                points_x.append(cur_x)
                points_y.append(cur_y)
                idx += 2
                cmd = "l"
            else:
                idx += 1
        # H / h
        elif cmd == "H":
            cur_x = float(tokens[idx])
            points_x.append(cur_x)
            points_y.append(cur_y)
            idx += 1
        elif cmd == "h":
            cur_x += float(tokens[idx])
            points_x.append(cur_x)
            points_y.append(cur_y)
            idx += 1
        # V / v
        elif cmd == "V":
            cur_y = float(tokens[idx])
            points_x.append(cur_x)
            points_y.append(cur_y)
            idx += 1
        elif cmd == "v":
            cur_y += float(tokens[idx])
            points_x.append(cur_x)
            points_y.append(cur_y)
            idx += 1
        # L / l
        elif cmd == "L":
            if idx + 1 < len(tokens):
                cur_x = float(tokens[idx])
                cur_y = float(tokens[idx + 1])
                points_x.append(cur_x)
                points_y.append(cur_y)
                idx += 2
            else:
                idx += 1
        elif cmd == "l":
            if idx + 1 < len(tokens):
                cur_x += float(tokens[idx])
                cur_y += float(tokens[idx + 1])
                points_x.append(cur_x)
                points_y.append(cur_y)
                idx += 2
            else:
                idx += 1
        # Q / q
        elif cmd == "Q":
            if idx + 3 < len(tokens):
                cur_x = float(tokens[idx + 2])
                cur_y = float(tokens[idx + 3])
                points_x.append(cur_x)
                points_y.append(cur_y)
                idx += 4
            else:
                idx += 1
        elif cmd == "q":
            if idx + 3 < len(tokens):
                cur_x += float(tokens[idx + 2])
                cur_y += float(tokens[idx + 3])
                points_x.append(cur_x)
                points_y.append(cur_y)
                idx += 4
            else:
                idx += 1
        # C / c
        elif cmd == "C":
            if idx + 5 < len(tokens):
                cur_x = float(tokens[idx + 4])
                cur_y = float(tokens[idx + 5])
                points_x.append(cur_x)
                points_y.append(cur_y)
                idx += 6
            else:
                idx += 1
        elif cmd == "c":
            if idx + 5 < len(tokens):
                cur_x += float(tokens[idx + 4])
                cur_y += float(tokens[idx + 5])
                points_x.append(cur_x)
                points_y.append(cur_y)
                idx += 6
            else:
                idx += 1
        # A / a
        elif cmd == "A":
            if idx + 6 < len(tokens):
                cur_x = float(tokens[idx + 5])
                cur_y = float(tokens[idx + 6])
                points_x.append(cur_x)
                points_y.append(cur_y)
                idx += 7
            else:
                idx += 1
        elif cmd == "a":
            if idx + 6 < len(tokens):
                cur_x += float(tokens[idx + 5])
                cur_y += float(tokens[idx + 6])
                points_x.append(cur_x)
                points_y.append(cur_y)
                idx += 7
            else:
                idx += 1
        elif cmd in ["Z", "z"]:
            idx += 1
        else:
            idx += 1

    if not points_x or not points_y:
        return None
    min_x, max_x = min(points_x), max(points_x)
    min_y, max_y = min(points_y), max(points_y)
    return min_x, min_y, max_x - min_x, max_y - min_y
