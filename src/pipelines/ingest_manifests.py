"""
ingest_manifests.py - Manifest writing logic for Ingest Agent (ADR-0202 <=300L).

Extracted from ingest_agent.py to comply with modular ceiling.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

from src.cli import ZeroFluffConsole
from src.utils.logger import get_logger

logger = get_logger("ingest_manifests")
from src.state import ProjectLayout


def write_source_manifest(state, project_root: Path, initiative: Optional[str] = None) -> None:
    """Generate canonical source manifest under docs/00-ingested/source_manifest.json (ADR-0335)."""
    project_name = state.project_name
    if initiative:
        ingested_dir = project_root / "docs" / initiative / "00-ingested"
    else:
        ingested_dir = project_root / "docs" / "00-ingested"
    ingested_dir.mkdir(parents=True, exist_ok=True)
    manifest_file = ingested_dir / "source_manifest.json"

    manifest_data = {
        "manifest_version": "1.0.0",
        "project_name": project_name,
        "generated_at": datetime.now().isoformat(),
        "total_sources": len(state.ingested_sources),
        "sources": [
            {
                "filename": s.get("filename", Path(s.get("filepath", "")).name),
                "filepath": s.get("filepath"),
                "file_type": s.get("file_type"),
                "sha256": s.get("sha256"),
                "char_count": s.get("char_count", len(s.get("extracted_text_summary", ""))),
                "word_count": s.get("word_count", 0),
                "sections_count": len(s.get("sections", [])),
                "sections": s.get("sections", []),
                "terms": s.get("terms", []),
                "ingested_at": s.get("timestamp"),
            }
            for s in state.ingested_sources
        ],
    }

    try:
        with open(manifest_file, "w", encoding="utf-8") as f:
            json.dump(manifest_data, f, indent=2, ensure_ascii=False)
        ZeroFluffConsole.info(f"Source Manifest canonique synchronisé : {manifest_file}")
    except Exception as e:
        ZeroFluffConsole.warning(f"Impossible d'écrire source_manifest.json : {e}")


def write_anomalies_manifest_direct(
    anomalies: list, project_name: str, initiative: Optional[str] = None
) -> None:
    """Record ingestion anomalies registry directly with anomalies list."""
    project_root = Path("Projects") / project_name
    if initiative:
        ingested_dir = project_root / "docs" / initiative / "00-ingested"
    else:
        ingested_dir = project_root / "docs" / "00-ingested"
    anomalies_file = ingested_dir / "ingest_anomalies.json"

    if anomalies:
        data = {
            "project_name": project_name,
            "recorded_at": datetime.now().isoformat(),
            "total_anomalies": len(anomalies),
            "anomalies": anomalies,
        }
        try:
            with open(anomalies_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            ZeroFluffConsole.warning(
                f"Registre des anomalies d'ingestion consigné : {anomalies_file}"
            )
        except Exception as e:
            ZeroFluffConsole.warning(f"Impossible d'écrire ingest_anomalies.json : {e}")
    else:
        anomalies_file = (
            Path("Projects") / project_name / "docs" / "00-ingested" / "ingest_anomalies.json"
        )
        if anomalies_file.exists():
            try:
                anomalies_file.unlink()
            except Exception as e:
                logger.debug(
                    "Impossible de supprimer le fichier d'anomalies existant.",
                    exc_info=True,
                    extra={"file": str(anomalies_file), "error": str(e)},
                )
