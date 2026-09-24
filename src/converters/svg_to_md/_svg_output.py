"""
mLoop Framework — Rendu Markdown/ASCII du convertisseur SVG (extraction
MLOOP-176-BE, Q1-A).

Contient `generate_ascii_wireframe`, `parse_svg_to_md_text` (orchestration
principale + pont OCR Phase 1) et `convert_svg_file_to_md` (I/O disque,
copie d'actifs ADR-0332).

Résolution OCR (contrat de test préservé — MLOOP-176-BE §0) : l'appel à
`ocr_vectorized_svg` se fait par lookup dynamique paresseux sur le module
shim `src.converters.svg_to_md`, afin que
`unittest.mock.patch("src.converters.svg_to_md.ocr_vectorized_svg", ...)`
(tests historiques, inchangés) continue d'intercepter l'appel réel.
"""

from collections import Counter
from pathlib import Path
from typing import List, Optional

from src.converters.svg_to_md._svg_models import UIElement


def generate_ascii_wireframe(elements: List[UIElement], width_chars: int = 62) -> str:
    """Génère un Wireframe ASCII Box-Drawing pour le terminal CLI / OpenCode."""
    if not elements:
        return (
            "┌"
            + "─" * (width_chars - 2)
            + "┐\n│ "
            + "Aucun composant détecté".center(width_chars - 4)
            + " │\n└"
            + "─" * (width_chars - 2)
            + "┘"
        )

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
            line_str = line_str[: inner_w - 3] + "..."
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
                    txt_str = txt_str[: inner_w - 3] + "..."
                lines.append(f"│ {txt_str.ljust(inner_w)} │")
    else:
        lines.append(f"│ {'(Corps principal de la maquette)'.center(inner_w)} │")

    # Footer
    if footer_elems:
        lines.append("├" + "─" * (width_chars - 2) + "┤")
        footer_btns = [f"[ {e.text} ]" for e in footer_elems]
        foot_str = "   ".join(footer_btns)
        if len(foot_str) > inner_w:
            foot_str = foot_str[: inner_w - 3] + "..."
        lines.append(f"│ {foot_str.center(inner_w)} │")

    lines.append("└" + "─" * (width_chars - 2) + "┘")
    return "\n".join(lines)


def parse_svg_to_md_text(
    svg_content: str,
    filename: str,
    asset_rel_path: Optional[str] = None,
    svg_path: Optional[Path] = None,
) -> str:
    """
    Extrait la structure géométrique et sémantique d'un SVG et génère
    une spécification UI complète en Markdown pour mLoop (ADR-0332 / ADR-0334).

    Phase 1 (Enforcement Déterministe du Grounding Visuel) : si le SVG est détecté
    en Mode 2 (texte vectorisé/outlined, aucune balise <text>/<tspan>), le pont OCR
    (`svg_ocr_bridge.ocr_vectorized_svg`) est invoqué pour extraire le contenu textuel
    réel de la maquette. En cas d'indisponibilité (Chromium/OCR absents, timeout,
    `MLOOP_SVG_OCR=0`), dégradation gracieuse : le comportement historique (placeholder
    de wireframe) est conservé, avec un flag `ocr_status: "UNAVAILABLE"` traçable.
    """
    # Import paresseux du package du module shim lui-même (résolution dynamique
    # de `ocr_vectorized_svg` afin que le patch de test sur
    # `src.converters.svg_to_md.ocr_vectorized_svg` reste effectif — voir docstring module).
    import src.converters.svg_to_md as _svg_to_md_shim
    from src.converters.svg_to_md._svg_parser_core import SvgSpatialParserCore  # noqa: F401

    title = filename.replace(".svg", "").replace("_", " ").replace("-", " ").title()
    parser = _svg_to_md_shim.SvgSpatialParser(svg_content, filename)
    elements = parser.parse()

    if asset_rel_path:
        source_note = f"> **Source :** `{filename}` (Actif visuel versionné sous [`{asset_rel_path}`]({asset_rel_path}))\n\n![Maquette]({asset_rel_path})\n"
    else:
        source_note = (
            f"> **Source :** `{filename}` (Converti automatiquement sous `docs/00-ingested/`)\n"
        )

    counts = Counter([e.elem_type for e in elements])
    w, h = parser.view_box[2], parser.view_box[3]

    wireframe_ascii = generate_ascii_wireframe(elements)

    # ── Pont OCR (Phase 1) : uniquement si Mode 2 vectorisé détecté ──────────
    ocr_text: Optional[str] = None
    ocr_status = "N_A"  # SVG Mode 1 (<text> natif) : OCR non requis, texte déjà lisible.
    if parser.is_vectorized:
        ocr_text = _svg_to_md_shim.ocr_vectorized_svg(svg_path) if svg_path is not None else None
        ocr_status = "DONE" if ocr_text else "UNAVAILABLE"

    md_lines = [
        "---",
        f'title: "Spécification UI : {title}"',
        'document_type: "ui_specification"',
        f'source_svg: "{filename}"',
        f"dimensions: {{ width: {int(w)}, height: {int(h)} }}",
        f"components_detected: {{ buttons: {counts['button']}, inputs: {counts['input']}, badges: {counts['badge']}, cards: {counts['card']} }}",
        f"total_elements: {len(elements)}",
        f"is_vectorized: {str(parser.is_vectorized).lower()}",
        f'ocr_status: "{ocr_status}"',
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
    ]

    if parser.is_vectorized:
        md_lines.append("## 🔍 Contrat Visuel — Texte Réel Extrait (OCR)")
        md_lines.append("")
        if ocr_text:
            md_lines.append(
                "> ⚠️ **Texte reconnu par OCR natif** (`Windows.Media.Ocr`) sur rendu Chromium headless. "
                "Les accents peuvent être mal encodés — transcription indicative à recouper avec la "
                "maquette source, jamais à recopier verbatim dans du code (skill `svg-ocr`)."
            )
            md_lines.append("")
            md_lines.append("```text")
            md_lines.append(ocr_text)
            md_lines.append("```")
        else:
            md_lines.append(
                "> ⚠️ **OCR indisponible** pour cette maquette à texte vectorisé (Chromium/Windows.Media.Ocr "
                "non exécutable dans cet environnement, ou `MLOOP_SVG_OCR=0`). Le contenu textuel réel n'a "
                "PAS pu être extrait automatiquement — invoquer manuellement le skill `svg-ocr` avant de "
                "considérer cette maquette comme lue (Contrat Visuel = SSOT, AGENTS.md)."
            )
        md_lines.append("")

    md_lines.extend(
        [
            "## 📑 Arbre Sémantique des Éléments (Ordre Visuel Top → Bottom)",
            "",
        ]
    )

    header_elems = [e for e in elements if e.y < 120]
    body_elems = [e for e in elements if 120 <= e.y < 650]
    footer_elems = [e for e in elements if e.y >= 650]

    if header_elems:
        md_lines.append("### 1. Bandeau Supérieur & En-tête (Y: 0px → 120px)")
        for e in header_elems:
            md_lines.append(
                f"- **[{e.elem_type.upper()}]** : `{e.text}` (Position: X={int(e.x)}, Y={int(e.y)})"
            )
        md_lines.append("")

    if body_elems:
        md_lines.append("### 2. Corps Principal & Formulaires (Y: 120px → 650px)")
        for e in body_elems:
            md_lines.append(
                f"- **[{e.elem_type.upper()}]** : `{e.text}` (Position: X={int(e.x)}, Y={int(e.y)})"
            )
        md_lines.append("")

    if footer_elems:
        md_lines.append("### 3. Pied de Page & Actions CTA (Y: 650px+)")
        for e in footer_elems:
            md_lines.append(
                f"- **[{e.elem_type.upper()}]** : `{e.text}` (Position: X={int(e.x)}, Y={int(e.y)})"
            )
        md_lines.append("")

    interactive = [e for e in elements if e.elem_type in ["button", "input", "badge", "nav"]]
    if interactive:
        md_lines.extend(
            [
                "## 🎛️ Matrice des Call-to-Actions (CTA) & Éléments Interactifs Détectés",
                "",
                "| Élément Visuel Détecté | Rôle Infére | Position Spatiale (X, Y) | Déclencheur / Action Probable |",
                "| :--- | :--- | :--- | :--- |",
            ]
        )
        for e in interactive:
            role_label = {
                "button": "Bouton d'action",
                "input": "Champ de saisie",
                "badge": "Badge de statut",
                "nav": "Navigation / Onglet",
            }.get(e.elem_type, "Composant interactif")

            action_label = {
                "button": "onClick (Soumission / Action)",
                "input": "onChange / onBlur",
                "badge": "Affichage informatif",
                "nav": "onClick (Changement de vue)",
            }.get(e.elem_type, "Interaction")

            md_lines.append(
                f"| **`{e.text}`** | {role_label} | `({int(e.x)}, {int(e.y)})` | `{action_label}` |"
            )
        md_lines.append("")

    return "\n".join(md_lines)


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
        docs_root = Path(*output_md_path.parts[: docs_idx + 1])
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

    md_text = parse_svg_to_md_text(
        content, svg_path.name, asset_rel_path=asset_rel_path, svg_path=svg_path
    )

    output_md_path.parent.mkdir(parents=True, exist_ok=True)
    output_md_path.write_text(md_text, encoding="utf-8")
    return True
