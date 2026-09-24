"""
mLoop Framework — Mixin de classification des composants SVG (extraction
MLOOP-176-BE, Q1-A).

Contient `ParserClassifyMixin` : association textes/conteneurs (Mode 1) et
reconstruction heuristique par géométrie pour SVGs vectorisés/outlined
(Mode 2). Combiné à `SvgSpatialParserCore` dans `__init__.py` pour former
l'API publique `SvgSpatialParser` (rétrocompatibilité stricte).
"""

from src.converters.svg_to_md._svg_models import UIElement


class ParserClassifyMixin:
    """Mixin de classification — attend `self.elements`, `self.filename`, `self.view_box` (fournis par SvgSpatialParserCore)."""

    def _associate_and_classify(self, containers: list, texts: list):
        """Mode Standard : Associe les textes aux conteneurs."""
        for t in texts:
            tx, ty, txt = t["x"], t["y"], t["text"]
            font_size = t.get("font_size", 14)

            best_c = None
            best_area = float("inf")

            for c in containers:
                cx, cy, cw, ch = c["x"], c["y"], c["width"], c["height"]
                if (cx - 15 <= tx <= cx + cw + 15) and (cy - 20 <= ty <= cy + ch + 20):
                    area = cw * ch
                    if area < best_area:
                        best_area = area
                        best_c = c

            if best_c:
                cid, cw, ch = best_c["id"], best_c["width"], best_c["height"]
                rx, fill = best_c.get("rx", 0.0), best_c.get("fill", "")

                if (cw <= 120 and ch <= 35) or (cw <= 40 and ch <= 40):
                    elem_type = "badge"
                elif (30 <= ch <= 65 and cw <= 350) and (
                    rx > 2 or fill not in ["none", "#ffffff", "white", ""]
                ):
                    elem_type = "button"
                elif 35 <= ch <= 65 and (
                    best_c.get("stroke") or fill in ["none", "#ffffff", "white"]
                ):
                    elem_type = "input"
                elif cw > 200 and ch > 60:
                    elem_type = "card"
                else:
                    elem_type = "button" if rx > 0 else "card"

                self.elements.append(
                    UIElement(
                        id=cid,
                        text=txt,
                        elem_type=elem_type,
                        x=best_c["x"],
                        y=best_c["y"],
                        width=cw,
                        height=ch,
                        fill=fill,
                        stroke=best_c.get("stroke", ""),
                        rx=rx,
                    )
                )
            else:
                elem_type = (
                    "heading"
                    if (font_size >= 17 or t.get("font_weight") in ["bold", "700", "800"])
                    else "text"
                )
                self.elements.append(
                    UIElement(
                        id=t["id"],
                        text=txt,
                        elem_type=elem_type,
                        x=tx,
                        y=ty,
                        width=len(txt) * font_size * 0.6,
                        height=font_size * 1.2,
                    )
                )

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
            key = (
                round(b["x"] / 8.0),
                round(b["y"] / 8.0),
                round(b["width"] / 8.0),
                round(b["height"] / 8.0),
            )
            if key not in seen:
                seen.add(key)
                dedup_boxes.append(b)

        # Ajouter l'En-tête principal déduit
        self.elements.append(
            UIElement(
                id="screen_header",
                text=f"Écran : {clean_title}",
                elem_type="heading",
                x=20.0,
                y=40.0,
                width=self.view_box[2] * 0.8,
                height=40.0,
            )
        )

        # Classifier chaque boîte par son rôle géométrique
        for b in dedup_boxes:
            w, h = b["width"], b["height"]
            x, y = b["x"], b["y"]
            fill = b.get("fill", "")
            stroke = b.get("stroke", "")
            b_id = b.get("id", "")

            # 1. Bannière / Logo / Image d'en-tête
            if y < 200 and w >= 250 and 80 <= h <= 200 and "url(" in fill:
                self.elements.append(
                    UIElement(
                        id=b_id or "logo_banner",
                        text=f"Bannière Logo / En-tête ({int(w)}x{int(h)}px)",
                        elem_type="card",
                        x=x,
                        y=y,
                        width=w,
                        height=h,
                        fill=fill,
                    )
                )
            # 2. Bandeau supérieur / Header bar
            elif y < 100 and w >= self.view_box[2] * 0.7 and h <= 100:
                self.elements.append(
                    UIElement(
                        id=b_id or "header_bar",
                        text=f"Bandeau Supérieur (H: {int(h)}px)",
                        elem_type="nav",
                        x=x,
                        y=y,
                        width=w,
                        height=h,
                        fill=fill,
                    )
                )
            # 3. Boutons CTA
            elif (30 <= h <= 65 and 80 <= w <= 360) and (
                fill not in ["none", "#ffffff", "#e1e3e5", "white", ""] or stroke
            ):
                btn_name = "Action Principale" if y >= self.view_box[3] * 0.7 else "Bouton d'Action"
                if "valider" in self.filename.lower() or "confirm" in self.filename.lower():
                    btn_name = "Bouton Confirmer / Valider"
                elif "logout" in self.filename.lower():
                    btn_name = "Bouton Déconnexion"
                elif "login" in self.filename.lower():
                    btn_name = "Bouton Connexion"

                self.elements.append(
                    UIElement(
                        id=b_id or f"btn_{len(self.elements)}",
                        text=f"[{btn_name}]",
                        elem_type="button",
                        x=x,
                        y=y,
                        width=w,
                        height=h,
                        fill=fill,
                        stroke=stroke,
                    )
                )
            # 4. Champs de saisie / Formulaire
            elif (30 <= h <= 60 and w >= 200) and (fill in ["#ffffff", "white", "none"] or stroke):
                self.elements.append(
                    UIElement(
                        id=b_id or f"input_{len(self.elements)}",
                        text="Champ de Saisie Formulaire",
                        elem_type="input",
                        x=x,
                        y=y,
                        width=w,
                        height=h,
                        fill=fill,
                        stroke=stroke,
                    )
                )
            # 5. Badges / Indicateurs de statut
            elif (w <= 120 and h <= 35) or (w <= 40 and h <= 40 and (fill or stroke)):
                badge_type = (
                    "Badge Conforme (Vert)"
                    if "conforme" in self.filename.lower()
                    or fill in ["#34c759", "#1f7f42", "#ecf4ef"]
                    else "Badge Statut"
                )
                self.elements.append(
                    UIElement(
                        id=b_id or f"badge_{len(self.elements)}",
                        text=f"(Statut: {badge_type})",
                        elem_type="badge",
                        x=x,
                        y=y,
                        width=w,
                        height=h,
                        fill=fill,
                    )
                )
            # 6. Cartes / Sections groupées
            elif w >= 250 and h >= 70:
                self.elements.append(
                    UIElement(
                        id=b_id or f"card_{len(self.elements)}",
                        text=f"Section / Carte ({int(w)}x{int(h)}px)",
                        elem_type="card",
                        x=x,
                        y=y,
                        width=w,
                        height=h,
                        fill=fill,
                    )
                )
