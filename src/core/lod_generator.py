"""
Moteur de Génération de Sidecars LOD (Level of Detail L0/L1/L2) et Fraîcheur OKF pour mLoop.
Standardisé selon l'ADR-0335 & Architecture de Contexte Progressive Disclosure.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class LODGenerator:
    """
    Générateur déterministe de sidecars sémantiques L0 (.abstract.md) et L1 (.overview.md)
    pour les répertoires documentaires de mLoop (notamment docs/00-ingested/ et docs/06-knowledge/).
    """

    DEFAULT_ABSTRACT_MAX_CHARS = 280
    DEFAULT_OVERVIEW_MAX_CHARS = 4000

    @classmethod
    def compute_file_hash(cls, file_path: Path) -> str:
        """Calcule le SHA-256 d'un fichier."""
        if not file_path.exists() or not file_path.is_file():
            return ""
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        return hasher.hexdigest()

    @classmethod
    def compute_directory_signature(cls, directory_path: Path) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Calcule une signature combinée déterministe de tous les fichiers enfants non-sidecars
        dans un répertoire.
        """
        if not directory_path.exists() or not directory_path.is_dir():
            return "", []

        children = sorted([
            f for f in directory_path.iterdir()
            if f.is_file() and not f.name.startswith(".") and f.name not in [".abstract.md", ".overview.md"]
        ], key=lambda x: x.name)

        combined_hasher = hashlib.sha256()
        entries = []

        for child in children:
            f_hash = cls.compute_file_hash(child)
            combined_hasher.update(f"{child.name}:{f_hash}".encode("utf-8"))
            mtime = datetime.fromtimestamp(child.stat().st_mtime, tz=timezone.utc).isoformat()
            entries.append({
                "name": child.name,
                "size_bytes": child.stat().st_size,
                "sha256": f_hash,
                "mtime": mtime
            })

        return combined_hasher.hexdigest(), entries

    @classmethod
    def extract_document_summary(cls, content: str) -> str:
        """Extrait un résumé concis du document (H1 + premier paragraphe significatif)."""
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        title = ""
        first_p = ""

        for line in lines:
            if line.startswith("# ") and not title:
                title = line.lstrip("# ").strip()
            elif not line.startswith("#") and not line.startswith("---") and not line.startswith("```") and not first_p:
                if len(line) > 20:
                    first_p = line

        summary = f"{title}: {first_p}" if title and first_p else (title or first_p or "Documentation technique.")
        if len(summary) > cls.DEFAULT_ABSTRACT_MAX_CHARS:
            summary = summary[:cls.DEFAULT_ABSTRACT_MAX_CHARS - 3] + "..."
        return summary

    @classmethod
    def generate_lod_sidecars(
        cls,
        directory_path: Path,
        source_info: Optional[Dict[str, Any]] = None,
        project_name: Optional[str] = None
    ) -> Tuple[Path, Path]:
        """
        Génère les fichiers .abstract.md (L0) et .overview.md (L1) avec frontmatter OKF dans directory_path.
        """
        directory_path.mkdir(parents=True, exist_ok=True)
        dir_hash, child_entries = cls.compute_directory_signature(directory_path)

        source_meta = source_info or {
            "kind": "local_ingest",
            "uri": f"mloop://docs/{directory_path.name}"
        }

        # 1. Extraction des métadonnées des enfants
        nav_entries = []
        abstract_summaries = []

        for entry in child_entries:
            c_path = directory_path / entry["name"]
            c_text = ""
            try:
                c_text = c_path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                pass

            doc_summary = cls.extract_document_summary(c_text)
            nav_entries.append(f"- [`{entry['name']}`]({entry['name']}) : {doc_summary}")
            abstract_summaries.append(f"{entry['name']} ({doc_summary})")

        # 2. Construction du L0 (Abstract)
        abstract_body = f"Module '{directory_path.name}' : Contient {len(child_entries)} document(s) technique(s)."
        if abstract_summaries:
            first_items = "; ".join(abstract_summaries[:3])
            abstract_body = f"Documentation {directory_path.name} : {first_items}"
            if len(abstract_body) > cls.DEFAULT_ABSTRACT_MAX_CHARS:
                abstract_body = abstract_body[:cls.DEFAULT_ABSTRACT_MAX_CHARS - 3] + "..."

        abstract_frontmatter = (
            "---\n"
            f"directory: \"{directory_path.as_posix()}\"\n"
            f"source:\n"
            f"  kind: \"{source_meta.get('kind', 'ingest')}\"\n"
            f"  uri: \"{source_meta.get('uri', directory_path.as_posix())}\"\n"
            f"generated_by:\n"
            f"  component: \"LODGenerator\"\n"
            f"  version: \"1.0.0\"\n"
            f"freshness:\n"
            f"  total_entries: {len(child_entries)}\n"
            f"  sha256_hash: \"{dir_hash}\"\n"
            f"  pending_child_changes: 0\n"
            f"  last_updated: \"{datetime.now(timezone.utc).isoformat()}\"\n"
            "---\n\n"
        )

        abstract_file = directory_path / ".abstract.md"
        abstract_file.write_text(abstract_frontmatter + abstract_body + "\n", encoding="utf-8")

        # 3. Construction du L1 (Overview)
        nav_section = "\n".join(nav_entries) if nav_entries else "*Aucun document physique enfant.*"
        overview_body = (
            f"# Vue d'Ensemble : {directory_path.name}\n\n"
            f"{abstract_body}\n\n"
            "## 🧭 Navigation Rapide (LOD Index)\n\n"
            f"{nav_section}\n\n"
            "## 📋 Inventaire Déterministe\n\n"
            f"Total de {len(child_entries)} fichier(s) physique(s) sous gestion de version Git.\n"
        )

        overview_frontmatter = (
            "---\n"
            f"directory: \"{directory_path.as_posix()}\"\n"
            f"project: \"{project_name or 'mLoop'}\"\n"
            f"source:\n"
            f"  kind: \"{source_meta.get('kind', 'ingest')}\"\n"
            f"  uri: \"{source_meta.get('uri', directory_path.as_posix())}\"\n"
            f"generated_by:\n"
            f"  component: \"LODGenerator\"\n"
            f"  version: \"1.0.0\"\n"
            f"freshness:\n"
            f"  total_entries: {len(child_entries)}\n"
            f"  sha256_hash: \"{dir_hash}\"\n"
            f"  pending_child_changes: 0\n"
            f"  last_updated: \"{datetime.now(timezone.utc).isoformat()}\"\n"
            "---\n\n"
        )

        overview_file = directory_path / ".overview.md"
        overview_file.write_text(overview_frontmatter + overview_body, encoding="utf-8")

        return abstract_file, overview_file

    @classmethod
    def check_directory_freshness(cls, directory_path: Path) -> Dict[str, Any]:
        """
        Vérifie si le sidecar .overview.md est synchronisé avec les fichiers physiques présents.
        """
        if not directory_path.exists() or not directory_path.is_dir():
            return {"status": "ERROR", "message": f"Répertoire introuvable: {directory_path}"}

        overview_file = directory_path / ".overview.md"
        if not overview_file.exists():
            # Si le dossier a des fichiers mais pas de sidecar
            dir_hash, child_entries = cls.compute_directory_signature(directory_path)
            if child_entries:
                return {
                    "status": "MISSING",
                    "directory": directory_path.as_posix(),
                    "pending_child_changes": len(child_entries),
                    "message": "Sidecar .overview.md manquant."
                }
            return {
                "status": "PASS",
                "directory": directory_path.as_posix(),
                "pending_child_changes": 0,
                "message": "Répertoire vide ou sans fichiers enfants."
            }

        # Lecture du frontmatter
        content = overview_file.read_text(encoding="utf-8", errors="ignore")
        match = re.search(r"^---\n(.*?)\n---", content, re.DOTALL)
        stored_hash = ""
        stored_entries_count = -1

        if match:
            fm_text = match.group(1)
            hash_m = re.search(r'sha256_hash:\s*["\']?([a-fA-F0-9]+)["\']?', fm_text)
            if hash_m:
                stored_hash = hash_m.group(1)
            entries_m = re.search(r'total_entries:\s*(\d+)', fm_text)
            if entries_m:
                stored_entries_count = int(entries_m.group(1))

        current_hash, current_entries = cls.compute_directory_signature(directory_path)

        if stored_hash and stored_hash == current_hash:
            return {
                "status": "PASS",
                "directory": directory_path.as_posix(),
                "pending_child_changes": 0,
                "total_entries": len(current_entries),
                "message": "Sidecar LOD synchronisé."
            }

        # Détection du nombre de modifications
        return {
            "status": "OUTDATED",
            "directory": directory_path.as_posix(),
            "pending_child_changes": abs(len(current_entries) - max(0, stored_entries_count)) or 1,
            "stored_hash": stored_hash,
            "current_hash": current_hash,
            "message": "Sidecar LOD obsolète par rapport aux fichiers physiques enfants."
        }

    @classmethod
    def split_markdown_chapters(
        cls,
        file_path: Path,
        output_dir: Path,
        min_chars_per_chapter: int = 1200
    ) -> List[Path]:
        """
        Découpe un document Markdown massif par chapitres (# ou ##) sous output_dir
        et génère les sidecars LOD .abstract.md et .overview.md.
        """
        if not file_path.exists() or not file_path.is_file():
            return []

        text = file_path.read_text(encoding="utf-8", errors="ignore")
        lines = text.splitlines()

        chapters: List[Tuple[str, List[str]]] = []
        current_title = "00_Introduction"
        current_lines: List[str] = []

        for line in lines:
            # Détection d'un titre de chapitre de niveau 1 ou 2
            if re.match(r"^#{1,2}\s+[A-Za-z0-9]", line.strip()):
                if current_lines and len("\n".join(current_lines)) >= min_chars_per_chapter:
                    chapters.append((current_title, current_lines))
                    current_title = line.strip().lstrip("#").strip()
                    current_lines = [line]
                else:
                    if not current_lines:
                        current_title = line.strip().lstrip("#").strip()
                    current_lines.append(line)
            else:
                current_lines.append(line)

        if current_lines:
            chapters.append((current_title, current_lines))

        output_dir.mkdir(parents=True, exist_ok=True)
        created_files: List[Path] = []

        for idx, (title, ch_lines) in enumerate(chapters, start=1):
            clean_name = re.sub(r'[^a-zA-Z0-9_\-]', '_', title).strip('_').lower()
            if not clean_name:
                clean_name = f"section_{idx}"
            file_name = f"{idx:02d}_{clean_name}.md"
            out_file = output_dir / file_name
            out_file.write_text("\n".join(ch_lines) + "\n", encoding="utf-8")
            created_files.append(out_file)

        # Génération des sidecars LOD
        cls.generate_lod_sidecars(
            directory_path=output_dir,
            source_info={"kind": "split_chapter", "source_file": file_path.name}
        )

        return created_files
