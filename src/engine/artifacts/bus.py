"""
mLoop Engine - Opaque Artifact Bus (ADR-0354)
Gestion déterministe et immuable des artefacts volumineux par handles opaques.
Évite la saturation contextuelle des prompts LLM sur les exécutions longues.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional, Tuple


@dataclass
class ArtifactHandle:
    handle_id: str
    sha256: str
    summary: str
    size_bytes: int
    line_count: int
    schema_type: str
    created_at: float
    path: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ArtifactHandle:
        return cls(**data)


class OpaqueArtifactBus:
    """
    Bus de stockage immuable pour gros artefacts.
    Persiste sous 'memory/artifacts/<prefix>/<sha256>.dat' et fournit
    des descripteurs compacts pour les prompts ainsi que des projections fenêtrées.
    """

    DEFAULT_BASE_DIR = Path("memory") / "artifacts"

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = Path(base_dir) if base_dir else self.DEFAULT_BASE_DIR
        self.base_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _clean_handle_id(handle_or_hash: str) -> str:
        """Extrait le hash SHA-256 pur d'un handle_id 'mloop://artifacts/<sha256>'."""
        cleaned = handle_or_hash.strip()
        if cleaned.startswith("mloop://artifacts/"):
            return cleaned.replace("mloop://artifacts/", "")
        return cleaned

    def store(
        self,
        content: str | bytes,
        summary: str = "",
        schema_type: str = "text/plain",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ArtifactHandle:
        """
        Persiste un contenu dans le bus immuable, calcule son empreinte SHA-256
        et retourne son ArtifactHandle.
        """
        if isinstance(content, str):
            raw_bytes = content.encode("utf-8")
            text_content = content
        else:
            raw_bytes = content
            text_content = content.decode("utf-8", errors="replace")

        sha256_hash = hashlib.sha256(raw_bytes).hexdigest()
        prefix = sha256_hash[:2]
        dest_dir = self.base_dir / prefix
        dest_dir.mkdir(parents=True, exist_ok=True)

        data_file = dest_dir / f"{sha256_hash}.dat"
        meta_file = dest_dir / f"{sha256_hash}.meta.json"

        # Écriture atomique si non existant
        if not data_file.exists():
            tmp_data = dest_dir / f"{sha256_hash}.tmp"
            with open(tmp_data, "wb") as f:
                f.write(raw_bytes)
            os.replace(tmp_data, data_file)

        lines = text_content.splitlines()
        line_count = len(lines)
        size_bytes = len(raw_bytes)
        created_at = time.time()
        handle_id = f"mloop://artifacts/{sha256_hash}"

        # Résumé automatique si omis
        if not summary:
            first_line = lines[0].strip() if lines else "Empty artifact"
            summary = first_line[:120]

        handle = ArtifactHandle(
            handle_id=handle_id,
            sha256=sha256_hash,
            summary=summary,
            size_bytes=size_bytes,
            line_count=line_count,
            schema_type=schema_type,
            created_at=created_at,
            path=str(data_file),
            metadata=metadata or {},
        )

        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(handle.to_dict(), f, indent=2, ensure_ascii=False)

        return handle

    def get_handle(self, handle_or_hash: str) -> Optional[ArtifactHandle]:
        """Charge la métadonnée d'un handle."""
        sha256_hash = self._clean_handle_id(handle_or_hash)
        prefix = sha256_hash[:2]
        meta_file = self.base_dir / prefix / f"{sha256_hash}.meta.json"
        if not meta_file.exists():
            return None
        with open(meta_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return ArtifactHandle.from_dict(data)

    def get_content(self, handle_or_hash: str) -> str:
        """Lit l'intégralité du contenu textuel de l'artefact."""
        sha256_hash = self._clean_handle_id(handle_or_hash)
        prefix = sha256_hash[:2]
        data_file = self.base_dir / prefix / f"{sha256_hash}.dat"
        if not data_file.exists():
            raise FileNotFoundError(f"Artefact introuvable : {handle_or_hash}")
        with open(data_file, "r", encoding="utf-8", errors="replace") as f:
            return f.read()

    def get_slice(self, handle_or_hash: str, start_line: int = 1, end_line: int = 100) -> str:
        """
        Extrait une projection fenêtrée de lignes (1-indexed inclusive).
        Ne charge que les lignes requises.
        """
        sha256_hash = self._clean_handle_id(handle_or_hash)
        prefix = sha256_hash[:2]
        data_file = self.base_dir / prefix / f"{sha256_hash}.dat"
        if not data_file.exists():
            raise FileNotFoundError(f"Artefact introuvable : {handle_or_hash}")

        start_line = max(1, start_line)
        end_line = max(start_line, end_line)

        selected_lines = []
        with open(data_file, "r", encoding="utf-8", errors="replace") as f:
            for current_idx, line in enumerate(f, start=1):
                if current_idx >= start_line and current_idx <= end_line:
                    selected_lines.append(line.rstrip("\r\n"))
                elif current_idx > end_line:
                    break

        return "\n".join(selected_lines)

    def to_prompt_descriptor(self, handle: ArtifactHandle, preview_lines: int = 5) -> str:
        """
        Formate un descripteur compact pour injection dans le contexte prompt d'un agent.
        """
        lines = []
        try:
            full_text = self.get_content(handle.sha256)
            lines = full_text.splitlines()
        except Exception:
            pass

        if len(lines) <= preview_lines * 2:
            body = "\n".join(lines)
        else:
            head = "\n".join(lines[:preview_lines])
            tail = "\n".join(lines[-preview_lines:])
            omitted = len(lines) - (preview_lines * 2)
            body = (
                f"{head}\n"
                f"[... {omitted} lignes omises pour protéger le contexte | "
                f"Consultez via bus.get_slice('{handle.handle_id}', start, end) ...]\n"
                f"{tail}"
            )

        return (
            f"📦 [OPAQUE-ARTIFACT: {handle.handle_id}]\n"
            f"Type: {handle.schema_type} | Taille: {handle.size_bytes} octets | Lignes: {handle.line_count}\n"
            f"Résumé: {handle.summary}\n"
            f"Fichier local: {handle.path}\n"
            f"--- [Aperçu Fenêtré] ---\n"
            f"{body}\n"
            f"--- [/Aperçu Fenêtré] ---"
        )

    def offload_if_exceeds(
        self,
        content: str,
        max_chars: int = 2000,
        max_lines: int = 30,
        summary: str = "",
        schema_type: str = "text/plain",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bool, str, Optional[ArtifactHandle]]:
        """
        Évalue si un contenu dépasse les seuils de concision.
        Si oui, le persiste dans le bus et retourne un descripteur prompt.
        Si non, retourne le contenu d'origine inchangé.
        """
        if not content:
            return False, content, None

        lines = content.splitlines()
        if len(content) > max_chars or len(lines) > max_lines:
            handle = self.store(
                content=content,
                summary=summary,
                schema_type=schema_type,
                metadata=metadata,
            )
            descriptor = self.to_prompt_descriptor(handle)
            return True, descriptor, handle

        return False, content, None
