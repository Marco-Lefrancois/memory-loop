"""
mLoop Framework SVG-to-Markdown Converter (package — extraction MLOOP-176-BE).

Convertit un fichier vectoriel SVG (maquette Figma standard avec <text> ou vectorisée/outlined avec <path>)
en un document Markdown structuré sous docs/00-ingested/ avec tri spatial (Y -> X),
inférence des composants UI, wireframe ASCII pour terminal CLI et matrice CTA (ADR-0332 / ADR-0334).

Package découpé selon le Cas Général §2 de `standards/protocols/MODULAR_EXTRACTION_PROTOCOL.md`
(décision Grill-Me 1:1 Q1-A) :
  - `_svg_models`           : UIElement + compute_svg_path_bbox_accurate
  - `_svg_parser_core`      : SvgSpatialParserCore (parse, traverse, transform, fallback)
  - `_svg_parser_classify`  : ParserClassifyMixin (association textes/conteneurs, mode outlined)
  - `_svg_output`           : generate_ascii_wireframe, parse_svg_to_md_text, convert_svg_file_to_md
  - `_svg_index`            : generate_maquettes_index

`SvgSpatialParser` recompose ici l'API publique historique (Core + Mixin) pour
une rétrocompatibilité stricte avec les tests et les 2 callers lazy pipelines
(`parse_svg_to_md_text`, `generate_maquettes_index`).
"""

from src.converters.svg_ocr_bridge import ocr_vectorized_svg
from src.converters.svg_to_md._svg_models import UIElement, compute_svg_path_bbox_accurate
from src.converters.svg_to_md._svg_parser_core import SvgSpatialParserCore
from src.converters.svg_to_md._svg_parser_classify import ParserClassifyMixin
from src.converters.svg_to_md._svg_output import (
    generate_ascii_wireframe,
    parse_svg_to_md_text,
    convert_svg_file_to_md,
)
from src.converters.svg_to_md._svg_index import generate_maquettes_index


class SvgSpatialParser(SvgSpatialParserCore, ParserClassifyMixin):
    """
    Parseur géométrique et spatial déterministe pour fichiers SVG (API publique
    inchangée — recomposition Core + Mixin, décision Grill-Me Q1-A MLOOP-176-BE).
    """


__all__ = [
    "UIElement",
    "compute_svg_path_bbox_accurate",
    "SvgSpatialParser",
    "generate_ascii_wireframe",
    "parse_svg_to_md_text",
    "convert_svg_file_to_md",
    "generate_maquettes_index",
    "ocr_vectorized_svg",
]
