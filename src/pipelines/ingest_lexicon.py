"""
ingest_lexicon.py - Term extraction and lexicon management for Ingest Agent (ADR-0202 <=300L).

Extracted from ingest_agent.py to comply with modular ceiling.
"""

import re
from pathlib import Path
from datetime import datetime
from collections import Counter
from typing import List, Dict, Any, Optional

from src.cli import ZeroFluffConsole
from src.state import ProjectLayout


def extract_sections(text: str) -> List[str]:
    """Extract hierarchical list of Markdown headings (#, ##, ###)."""
    sections = []
    for line in text.splitlines():
        line_str = line.strip()
        if line_str.startswith("#"):
            clean_title = line_str.lstrip("#").strip()
            if clean_title and clean_title not in sections:
                sections.append(clean_title)
    return sections


def extract_length_aware_terms(text: str) -> List[str]:
    """
    Extract named entities and technical terms with adaptive capping
    based on text volume (Standard DeepPaperNote / paper-glossary - ADR-0335).
    """
    char_count = len(text)
    if char_count < 10000:
        max_terms = 10
    elif char_count < 30000:
        max_terms = 18
    elif char_count < 60000:
        max_terms = 25
    else:
        max_terms = 35

    # Search for terminology patterns (Acronyms, PascalCase, CamelCase, [Terms])
    candidates = []

    # 1. Explicit terms in brackets or backticks
    bracketed = re.findall(r"`([A-Za-z0-9_\-\.\s]{2,40})`|\[([A-Za-z0-9_\-\.\s]{2,40})\]", text)
    for b1, b2 in bracketed:
        val = (b1 or b2).strip()
        if len(val) >= 2 and not val.startswith("http") and not val.startswith("/"):
            candidates.append(val)

    # 2. Acronyms (2 to 8 consecutive uppercase letters)
    acronyms = re.findall(r"\b[A-Z]{2,8}\b", text)
    stopwords_acronyms = {
        "LE",
        "LA",
        "LES",
        "DES",
        "DU",
        "UN",
        "UNE",
        "ET",
        "OU",
        "PAR",
        "POUR",
        "SUR",
        "DANS",
        "NON",
        "OUI",
        "PAS",
        "EST",
        "SONT",
        "QUE",
        "QUI",
        "CE",
        "CET",
        "CETTE",
    }
    candidates.extend([a for a in acronyms if a not in stopwords_acronyms])

    # 3. PascalCase / CamelCase words (ex: IngestAgent, ZeroFluffConsole, OAuth2)
    camel_pascal = re.findall(r"\b[A-Z][a-z0-9]+[A-Z][A-Za-z0-9]*\b", text)
    candidates.extend(camel_pascal)

    # Filtering and deduplication with frequency preservation
    counts = Counter(candidates)
    # Remove too short or parasitic candidates
    filtered = [
        term for term, count in counts.most_common() if len(term) >= 2 and not term.isdigit()
    ]

    return filtered[:max_terms]


def update_domain_lexicon(state, initiative: Optional[str] = None) -> None:
    """
    Auto-feed the Business Lexicon Dictionary under docs/04-transverse/lexique_domaine.md
    by aggregating terms extracted from ingested documents (ADR-0335 / paper-glossary).
    """
    if not state.ingested_sources:
        return

    term_sources: Dict[str, List[str]] = {}
    term_counts: Counter = Counter()

    for source in state.ingested_sources:
        source_name = source.get("filename", Path(source.get("filepath", "")).name)
        for t in source.get("terms", []):
            term_counts[t] += 1
            if t not in term_sources:
                term_sources[t] = []
            if source_name not in term_sources[t]:
                term_sources[t].append(source_name)

    if not term_counts:
        return

    project_name = state.project_name
    if initiative:
        transverse_dir = Path("Projects") / project_name / "docs" / initiative / "04-transverse"
    else:
        transverse_dir = Path("Projects") / project_name / "docs" / "04-transverse"
    transverse_dir.mkdir(parents=True, exist_ok=True)
    lexicon_file = transverse_dir / "lexique_domaine.md"

    lines = [
        "# Lexique & Vocabulaire du Domaine Métier (SSOT ADR-0335)",
        "",
        f"> **Statut :** Auto-consolidé par le Moteur d'Ingestion {project_name} | **Dernière mise à jour :** "
        + datetime.now().strftime("%Y-%m-%d %H:%M"),
        "",
        "Ce document recense les entités nommées, acronymes et concepts techniques découverts dans les documents sources de référence (`reference/`). Il constitue le vocabulaire officiel du projet.",
        "",
        "| Terme / Concept Métier | Fréquence d'Apparition | Documents Sources Associés |",
        "| :--- | :---: | :--- |",
    ]

    for term, freq in term_counts.most_common():
        docs = ", ".join(term_sources.get(term, []))
        lines.append(f"| **`{term}`** | {freq} | `{docs}` |")

    lines.append("")
    try:
        lexicon_file = (
            Path("Projects") / project_name / "docs" / "04-transverse" / "lexique_domaine.md"
        )
        lexicon_file.write_text("\n".join(lines), encoding="utf-8")
        ZeroFluffConsole.info(f"Dictionnaire de Lexique du Domaine synchronisé : {lexicon_file}")
    except Exception as e:
        ZeroFluffConsole.warning(f"Impossible d'écrire lexique_domaine.md : {e}")
