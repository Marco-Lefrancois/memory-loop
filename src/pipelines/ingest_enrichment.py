"""
ingest_enrichment.py - Markdown enrichment logic for Ingest Agent (ADR-0202 <=300L).

Extracted from ingest_agent.py to comply with modular ceiling.
"""

import json
import re
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Optional

from src.cli import ZeroFluffConsole
from src.utils.logger import get_logger

logger = get_logger("ingest_enrichment")
from src.state import ProjectLayout


def enrich_markdown(
    raw_text: str, filepath: Path, project_name: str, terms: Optional[List[str]] = None
) -> str:
    """
    Enrich Markdown document with normative YAML Frontmatter (Pattern pdf-brain & DeepPaperNote).
    """
    if raw_text.lstrip().startswith("---"):
        return raw_text

    lines = [l.strip() for l in raw_text.splitlines() if l.strip()]
    title = filepath.stem.replace("_", " ").replace("-", " ").title()
    for line in lines[:5]:
        if line.startswith("# "):
            title = line[2:].strip()
            break

    summary_lines = [l for l in lines if not l.startswith("#") and len(l) > 20][:3]
    summary = (
        " ".join(summary_lines)[:300]
        if summary_lines
        else f"Document de référence pour {filepath.name}."
    )

    doc_type = "general_doc"
    fname_lower = filepath.name.lower()
    if "api" in fname_lower or "reference" in fname_lower:
        doc_type = "api_reference"
    elif "adr" in fname_lower or "arch" in fname_lower or "design" in fname_lower:
        doc_type = "architecture_doc"
    elif "story" in fname_lower or "us-" in fname_lower or "rec-" in fname_lower:
        doc_type = "user_story"
    elif "spec" in fname_lower or "req" in fname_lower:
        doc_type = "spec"

    concepts = []
    full_lower = raw_text.lower() + " " + fname_lower
    taxonomy_file = Path("docs") / "05-knowledge" / "taxonomy.json"
    if taxonomy_file.exists():
        try:
            tax_data = json.loads(taxonomy_file.read_text(encoding="utf-8"))
            for c in tax_data.get("concepts", []):
                c_id = c.get("id")
                label = c.get("prefLabel", "").lower()
                alts = [a.lower() for a in c.get("altLabels", [])]
                if label in full_lower or any(a in full_lower for a in alts):
                    concepts.append(c_id)
        except Exception as e:
            logger.debug(
                "Échec lecture taxonomy.json (non-bloquant).",
                exc_info=True,
                extra={"file": str(taxonomy_file), "error": str(e)},
            )

    if not concepts:
        concepts = ["general/reference"]

    tags = [filepath.suffix.lstrip(".").lower(), doc_type]
    if project_name.lower() not in tags:
        tags.append(project_name.lower())

    terms_list = terms or []

    frontmatter = (
        "---\n"
        f'title: "{title}"\n'
        f'summary: "{summary}"\n'
        f'document_type: "{doc_type}"\n'
        f"tags: {json.dumps(tags, ensure_ascii=False)}\n"
        f"concepts: {json.dumps(concepts, ensure_ascii=False)}\n"
        f"terms: {json.dumps(terms_list, ensure_ascii=False)}\n"
        f'ingested_at: "{datetime.now().isoformat()}"\n'
        "---\n\n"
    )
    return frontmatter + raw_text


def determine_target_subfolder(filepath: Path, ref_root: Path, ext: str) -> str:
    """
    Determine target thematic subfolder under docs/00-ingested/ (ADR-0102).
    1. If file is in a subfolder of reference/, preserve and map the tree.
    2. Otherwise, use typological heuristic based on filename and extension.
    """
    try:
        rel_parent = filepath.parent.relative_to(ref_root)
        if str(rel_parent) != ".":
            p_str = str(rel_parent).lower()
            if any(k in p_str for k in ["sow", "contrat", "brief", "kickoff"]):
                return "01-sow-et-contrats"
            elif any(k in p_str for k in ["guide", "spec", "fonctionnel", "exigences"]):
                return "02-guides-et-specs"
            elif any(k in p_str for k in ["scan", "inventaire", "onetrust", "audit"]):
                return "03-scans-et-inventaires"
            elif any(k in p_str for k in ["api", "technique", "swagger", "openapi", "sdk"]):
                return "04-api-et-techniques"
            elif any(k in p_str for k in ["maquette", "ecran", "ui", "ux", "svg"]):
                return "05-maquettes-notes"
            else:
                return str(rel_parent).replace("\\", "/")
    except Exception as e:
        logger.debug(
            "Échec résolution chemin relatif (non-bloquant, repli sur heuristique nom).",
            exc_info=True,
            extra={"file": str(filepath), "error": str(e)},
        )

    name_lower = filepath.stem.lower()
    if ext == ".svg":
        return "05-maquettes-notes"
    elif any(k in name_lower for k in ["sow", "contrat", "brief", "kickoff"]):
        return "01-sow-et-contrats"
    elif any(k in name_lower for k in ["guide", "spec", "fonctionnel", "requirement"]):
        return "02-guides-et-specs"
    elif any(k in name_lower for k in ["scan", "inventaire", "onetrust", "audit", "rapport"]):
        return "03-scans-et-inventaires"
    elif any(k in name_lower for k in ["api", "technique", "swagger", "openapi", "sdk", "schema"]):
        return "04-api-et-techniques"
    elif ext in [".xlsx", ".csv"]:
        return "03-scans-et-inventaires"

    return "02-guides-et-specs"
