"""
mLoop Framework — Index & cartographie des maquettes SVG (extraction
MLOOP-176-BE, Q1-A).

Contient `generate_maquettes_index` : génère le tableau de bord récapitulatif
de toutes les maquettes converties sous `docs/00-ingested/`.
"""

import re
from pathlib import Path


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
        f"total_screens: {len(md_files)}",
        "---",
        "",
        "# 📑 Index & Cartographie des Maquettes UI (SSOT)",
        "",
        f"> **Périmètre :** {len(md_files)} spécification(s) d'écran(s) extraite(s) déterministement sous `docs/00-ingested/maquettes/` et versionnée(s) sous `docs/05-assets/maquettes/`.",
        "",
        "## 🗺️ Répertoire des Écrans de l'Application",
        "",
        "| Écran / Nom de Maquette | Spécification Markdown | Actif Visuel (SVG) | Boutons CTA | Champs Saisie | Badges / Statut |",
        "| :--- | :--- | :--- | :---: | :---: | :---: |",
    ]

    for f in md_files:
        svg_name = f.stem + ".svg"
        content = f.read_text(encoding="utf-8", errors="replace")

        # Extraire métadonnées
        title_m = re.search(r'title:\s*"([^"]+)"', content)
        title = title_m.group(1) if title_m else f.stem
        btn_m = re.search(r"buttons:\s*(\d+)", content)
        btn_c = btn_m.group(1) if btn_m else "0"
        inp_m = re.search(r"inputs:\s*(\d+)", content)
        inp_c = inp_m.group(1) if inp_m else "0"
        bdg_m = re.search(r"badges:\s*(\d+)", content)
        bdg_c = bdg_m.group(1) if bdg_m else "0"

        lines.append(
            f"| **{title}** | [`{f.name}`](./{f.name}) | [`{svg_name}`](../../05-assets/maquettes/{svg_name}) | {btn_c} | {inp_c} | {bdg_c} |"
        )

    lines.append("")
    index_file.write_text("\n".join(lines), encoding="utf-8")
    return index_file
