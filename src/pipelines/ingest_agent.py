import hashlib
import json
import re
from pathlib import Path
from datetime import datetime
from collections import Counter
from typing import Optional

from src.state import LoopState, ProjectLayout
from src.cli import ZeroFluffConsole
from src.core.confinement_shield import AgentContext
from src.core.lod_generator import LODGenerator

from src.pipelines.ingest_file_processors import (
    compute_sha256,
    parse_svg,
    parse_vtt,
    parse_pdf,
    parse_xlsx,
    parse_docx,
    parse_pptx,
    parse_csv,
    try_markitdown,
    parse_text_file,
    process_image_asset,
)
from src.pipelines.ingest_manifests import write_source_manifest, write_anomalies_manifest_direct
from src.pipelines.ingest_indexers import (
    generate_ingested_index,
    generate_docs_root_index,
    generate_maquettes_index,
    generate_lod_sidecars,
)
from src.pipelines.ingest_lexicon import (
    extract_sections,
    extract_length_aware_terms,
    update_domain_lexicon,
)
from src.pipelines.ingest_enrichment import enrich_markdown, determine_target_subfolder
from src.pipelines.ingest_assets import (
    compute_sha256 as compute_sha256_asset,
    process_svg_asset,
    process_image_asset,
    sync_svg_asset,
)


class IngestAgent:
    """
    Système 1 : Ingest Agent.
    Analyse le répertoire reference/ pour parser les PDF, DOCX, XLSX, TXT, SVG, etc.
    et les consolider de manière déterministe avec Source Manifest canonique,
    extraction adaptative de vocabulaire (Length-Aware) et auto-alimentation du lexique (ADR-0335).
    """

    def __init__(self):
        self.name = "Ingest Engine"
        self.anomalies: list[dict] = []

    # ─── Résolution des racines de sortie (Voie B — routage par initiative) ───
    def _project_root(self, state: LoopState) -> Path:
        return Path("Projects") / state.project_name

    def _ref_root(self, state: LoopState) -> Path:
        """Racine de scan. Scopée à reference/<initiative>/ si une initiative est fournie."""
        base = self._project_root(state) / ProjectLayout.REFERENCE
        initiative = getattr(state, "ingest_initiative", None)
        return (base / initiative) if initiative else base

    def _ingested_root(self, state: LoopState) -> Path:
        """
        Racine d'écriture des documents ingérés.
        - Avec initiative : docs/<initiative>/00-ingested/ (projets à structure par module).
        - Sans initiative : docs/00-ingested/ (modèle plat ADR-0102).
        """
        docs = self._project_root(state) / ProjectLayout.DOCS
        initiative = getattr(state, "ingest_initiative", None)
        base = (docs / initiative) if initiative else docs
        return base / ProjectLayout.DOCS_INGESTED

    def _initiative_docs_root(self, state: LoopState) -> Path:
        """Racine docs de l'initiative (ou docs/ à plat si non scopé)."""
        docs = self._project_root(state) / ProjectLayout.DOCS
        initiative = getattr(state, "ingest_initiative", None)
        return (docs / initiative) if initiative else docs

    def execute(self, state: LoopState) -> LoopState:
        project_root = self._project_root(state)

        with AgentContext("explorer", project_path=project_root):
            initiative = getattr(state, "ingest_initiative", None)
            scope_label = (
                f"reference/{initiative}/" if initiative else f"{ProjectLayout.REFERENCE}/"
            )
            ZeroFluffConsole.step_s1(self.name, f"Démarrage du scan du répertoire {scope_label}...")
            self.anomalies = []
            ref_path = self._ref_root(state)

            if not ref_path.exists():
                ref_path.mkdir(parents=True, exist_ok=True)

            supported_extensions = [
                ".pdf",
                ".docx",
                ".xlsx",
                ".csv",
                ".txt",
                ".md",
                ".cs",
                ".pptx",
                ".ppt",
                ".svg",
                ".vtt",
                ".jpg",
                ".jpeg",
                ".png",
            ]

            files_to_process = [
                file
                for file in ref_path.rglob("*")
                if file.is_file() and file.suffix.lower() in supported_extensions
            ]

            if not files_to_process:
                ZeroFluffConsole.info(f"Aucun document source à ingérer dans {scope_label}.")
                return state

            for file in files_to_process:
                state = self._process_file(file, state)

            # Post-traitement déterministe (ADR-0102 & ADR-0335)
            write_source_manifest(
                state, self._project_root(state), getattr(state, "ingest_initiative", None)
            )
            update_domain_lexicon(state, getattr(state, "ingest_initiative", None))
            write_anomalies_manifest_direct(
                self.anomalies, state.project_name, getattr(state, "ingest_initiative", None)
            )
            generate_ingested_index(state)
            generate_maquettes_index(state)
            generate_lod_sidecars(state)
            # La carte d'orientation racine docs/index.md décrit le projet entier :
            # ne pas la (re)générer lors d'une ingestion scopée à une seule initiative.
            if not getattr(state, "ingest_initiative", None):
                generate_docs_root_index(state)

            return state

    def _process_file(self, filepath: Path, state: LoopState) -> LoopState:
        sha256_val = compute_sha256(filepath)
        if sha256_val is None:
            return state

        # Vérification si déjà ingéré
        for source in state.ingested_sources:
            if source.get("filepath") == str(filepath) and source.get("sha256") == sha256_val:
                return state

        initiative = getattr(state, "ingest_initiative", None)
        ZeroFluffConsole.step_s1(
            self.name, f"Parsing du fichier {filepath.name} ({filepath.suffix.upper()})..."
        )
        extracted_text = ""

        # Ingestion multimodale Microsoft MarkItDown & Parsers Déterministes
        ext = filepath.suffix.lower()
        if ext == ".svg":
            extracted_text = parse_svg(filepath)
            # Synchronisation de l'actif visuel sous docs/[<initiative>/]05-assets/maquettes/ (ADR-0332)
            sync_svg_asset(filepath, state, getattr(state, "ingest_initiative", None))
        elif ext == ".vtt":
            extracted_text = parse_vtt(filepath)
        elif ext in [".jpg", ".jpeg", ".png"]:
            extracted_text = process_image_asset(
                filepath, state, getattr(state, "ingest_initiative", None)
            )
        else:
            extracted_text = try_markitdown(filepath)

        if not extracted_text or (
            isinstance(extracted_text, str) and extracted_text.startswith("[Erreur")
        ):
            if ext == ".txt" or ext == ".md" or ext == ".cs":
                extracted_text = parse_text_file(filepath)
            elif ext == ".pdf":
                extracted_text = parse_pdf(filepath)
            elif ext == ".xlsx":
                extracted_text = self._parse_xlsx(filepath)
            elif ext == ".docx":
                extracted_text = parse_docx(filepath)
            elif ext in [".pptx", ".ppt"]:
                extracted_text = parse_pptx(filepath)
            elif ext == ".csv":
                extracted_text = parse_csv(filepath)

        if not extracted_text or (
            isinstance(extracted_text, str) and extracted_text.startswith("[Erreur")
        ):
            ZeroFluffConsole.error(f"ÉCHEC D'INGESTION pour {filepath.name} : Aucun texte extrait")
            self.anomalies.append(
                {
                    "filename": filepath.name,
                    "filepath": str(filepath),
                    "error": "Aucun texte extrait",
                    "timestamp": datetime.now().isoformat(),
                }
            )
            return state

        # Sauvegarde automatique de la version Markdown (racine dynamique selon initiative)
        ingested_dir = self._ingested_root(state)
        ingested_dir.mkdir(parents=True, exist_ok=True)
        ref_root = self._ref_root(state)

        if ext == ".svg":
            target_dir = ingested_dir / "05-maquettes-notes"
            target_dir.mkdir(parents=True, exist_ok=True)
            target_md = target_dir / f"{filepath.stem}.md"
        else:
            subfolder = determine_target_subfolder(filepath, ref_root, ext)
            target_dir = ingested_dir / subfolder if subfolder else ingested_dir
            target_dir.mkdir(parents=True, exist_ok=True)
            target_md = target_dir / f"{filepath.stem}.md"

        sections = extract_sections(extracted_text)
        terms = extract_length_aware_terms(extracted_text)
        enriched_text = enrich_markdown(extracted_text, filepath, state.project_name, terms=terms)
        try:
            target_md.write_text(enriched_text, encoding="utf-8")
            ZeroFluffConsole.info(f"Copie Markdown enrichie enregistrée dans : {target_md}")
        except Exception as e:
            ZeroFluffConsole.warning(f"Note: Écriture du Markdown dans 00-ingested : {e}")

        # Ajout à l'état consolidé uniquement en cas de succès
        source_meta = {
            "filename": filepath.name,
            "filepath": str(filepath),
            "file_type": ext.upper()[1:],
            "sha256": sha256_val,
            "char_count": len(extracted_text),
            "word_count": len(extracted_text.split()),
            "sections": sections,
            "terms": terms,
            "extracted_text_summary": extracted_text[:1000],
            "timestamp": datetime.now().isoformat(),
        }
        state.ingested_sources.append(source_meta)
        ZeroFluffConsole.success(
            f"Fichier {filepath.name} ingéré avec succès ({len(terms)} termes, {len(sections)} sections)."
        )

        return state

    # ─── Wrapper methods for backward compatibility with tests ───
    def _compat_extract_sections(self, text: str) -> list[str]:
        """Wrapper for backward compatibility."""
        return extract_sections(text)

    def _compat_extract_length_aware_terms(self, text: str) -> list[str]:
        """Wrapper for backward compatibility."""
        return extract_length_aware_terms(text)

    def _compat_try_markitdown(self, path: Path) -> str:
        """Wrapper for backward compatibility."""
        return try_markitdown(path)

    def _compat_process_image_asset(self, filepath: Path, state: LoopState) -> str:
        """Wrapper for backward compatibility."""
        return process_image_asset(filepath, state, getattr(state, "ingest_initiative", None))

    def _compat_parse_xlsx(self, path: Path) -> str:
        """Wrapper for backward compatibility - calls the real parser."""
        return parse_xlsx(path)

    # Aliases for test compatibility
    _extract_sections = _compat_extract_sections
    _extract_length_aware_terms = _compat_extract_length_aware_terms
    _try_markitdown = _compat_try_markitdown
    _process_image_asset = _compat_process_image_asset
    _parse_xlsx = _compat_parse_xlsx

    # ─── Wrapper methods for backward compatibility with tests ───
    def _extract_sections(self, text: str) -> list[str]:
        """Wrapper for backward compatibility."""
        return extract_sections(text)

    def _extract_length_aware_terms(self, text: str) -> list[str]:
        """Wrapper for backward compatibility."""
        return extract_length_aware_terms(text)

    def _try_markitdown(self, path: Path) -> str:
        """Wrapper for backward compatibility."""
        return try_markitdown(path)

    def _process_image_asset(self, filepath: Path, state: LoopState) -> str:
        """Wrapper for backward compatibility."""
        return process_image_asset(filepath, state, getattr(state, "ingest_initiative", None))

    def _parse_xlsx(self, path: Path) -> str:
        """Wrapper for backward compatibility."""
        return parse_xlsx(path)
