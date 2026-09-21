import datetime
import hashlib
import json
import logging
from pathlib import Path
from typing import Optional, List

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {
    ".pdf", ".docx", ".xlsx", ".pptx", ".csv", ".txt", ".md", ".json", ".xml"
}


class MarkItDownPipeline:
    """Pipeline d'ingestion multimodale locale et sandboxed (ADR-0101)."""

    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.registry_file = project_path / "memory" / "ingest_registry.json"
        self.default_output_dir = project_path / "docs" / "00-ingested"

    def _load_registry(self) -> dict:
        if self.registry_file.exists():
            try:
                return json.loads(self.registry_file.read_text(encoding="utf-8"))
            except Exception as exc:
                logger.debug(f"Erreur lecture registry {self.registry_file}: {exc}", exc_info=True)
        return {}

    def _save_registry(self, registry: dict) -> None:
        try:
            self.registry_file.parent.mkdir(parents=True, exist_ok=True)
            self.registry_file.write_text(json.dumps(registry, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception as exc:
            logger.debug(f"Erreur écriture registry {self.registry_file}: {exc}", exc_info=True)

    def _compute_sha256(self, file_path: Path) -> str:
        return hashlib.sha256(file_path.read_bytes()).hexdigest()

    def _extract_content(self, file_path: Path) -> str:
        ext = file_path.suffix.lower()
        # 1. Tentative avec markitdown si disponible
        try:
            from markitdown import MarkItDown
            md = MarkItDown()
            res = md.convert(str(file_path))
            text = res.text_content if hasattr(res, "text_content") else str(res)
            if text and text.strip():
                return text
        except Exception as exc:
            logger.debug(f"markitdown indisponible ou en erreur sur {file_path.name}: {exc}", exc_info=True)

        # 2. Fallback textuel autonome
        if ext in (".txt", ".md", ".json", ".xml", ".csv"):
            try:
                return file_path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                try:
                    return file_path.read_text(encoding="cp1252")
                except Exception as exc:
                    logger.debug(f"Erreur décodage cp1252 pour {file_path.name}: {exc}", exc_info=True)
        return ""

    def convert_file(self, file_path: Path, output_dir: Optional[Path] = None) -> Optional[Path]:
        if not file_path.exists() or not file_path.is_file():
            return None
        if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            return None

        out_dir = output_dir or self.default_output_dir
        out_dir.mkdir(parents=True, exist_ok=True)
        sha256_hash = self._compute_sha256(file_path)

        registry = self._load_registry()
        # Contrôle anti-doublons (Idempotence)
        if sha256_hash in registry:
            cached_path = Path(registry[sha256_hash]["output_md"])
            if cached_path.exists():
                return cached_path

        content = self._extract_content(file_path)
        if not content or not content.strip():
            logger.debug(f"Extraction vide pour {file_path.name}")
            return None

        target_md = out_dir / f"{file_path.stem}.md"
        frontmatter = (
            f"---\n"
            f"source: {file_path.name}\n"
            f"sha256: {sha256_hash}\n"
            f"converted_at: {datetime.datetime.now().isoformat()}\n"
            f"char_count: {len(content)}\n"
            f"---\n\n"
        )
        try:
            target_md.write_text(frontmatter + content, encoding="utf-8")
        except Exception as exc:
            logger.debug(f"Erreur écriture target markdown {target_md}: {exc}", exc_info=True)
            return None

        registry[sha256_hash] = {
            "source_file": str(file_path),
            "output_md": str(target_md),
            "sha256": sha256_hash,
            "timestamp": datetime.datetime.now().isoformat(),
        }
        self._save_registry(registry)
        return target_md

    def convert_directory(self, input_dir: Path, output_dir: Optional[Path] = None) -> List[Path]:
        if not input_dir.exists() or not input_dir.is_dir():
            return []
        converted = []
        for file in sorted(input_dir.rglob("*")):
            if file.is_file() and file.suffix.lower() in SUPPORTED_EXTENSIONS:
                res = self.convert_file(file, output_dir=output_dir)
                if res:
                    converted.append(res)
        return converted
