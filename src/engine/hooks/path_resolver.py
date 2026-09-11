# -*- coding: utf-8 -*-
"""
mLoop Path Alias Resolver (ADR-0364).

Résolveur déterministe haute performance de Micro-URIs canoniques pour l'optimisation
de la fenêtre de contexte et la prévention du gaspillage de jetons.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Optional, Dict


class PathAliasResolver:
    """
    Mappeur bidirectionnel entre Micro-URIs condensées et chemins physiques réels.
    Divise par ~4 l'empreinte en jetons des références de fichiers dans les prompts.
    """

    SCHEME_MAPPINGS: Dict[str, str] = {
        "assets://": "docs/05-assets/maquettes",
        "evidence://": "memory/evidence",
        "story://": "backlog/stories",
        "model://": "docs/03-models",
        "source://": "docs/00-ingested",
        "rule://": "docs/02-business-rules",
    }

    @classmethod
    def get_project_root(
        cls, project_name: Optional[str] = None, base_dir: Optional[Path] = None
    ) -> Path:
        """Détermine le chemin racine du projet actif de manière déterministe."""
        root = base_dir or Path(".")

        # 1. Si base_dir est déjà un répertoire de projet concret
        if root.name != "Projects" and (root / "memory").exists() and root != Path("."):
            return root

        # 2. Si root est le dossier 'Projects'
        if root.name == "Projects":
            if project_name:
                cand = root / project_name
                if cand.exists():
                    return cand
            return root.parent

        # 3. Traitement standard
        if not project_name or project_name in ("Memory Loop", "mLoop", "default"):
            cand = root / "Projects" / (project_name or "Memory Loop")
            if cand.exists():
                return cand
            return root

        # 4. Projets clients sous Projects/<project_name>
        project_candidate = root / "Projects" / project_name
        if project_candidate.exists():
            return project_candidate

        direct_cand = root / project_name
        if direct_cand.exists():
            return direct_cand

        return project_candidate

    @classmethod
    def resolve(
        cls,
        uri: str,
        project_name: Optional[str] = None,
        base_dir: Optional[Path] = None,
    ) -> Path:
        """
        Convertit une Micro-URI (ex: assets://maquette.svg) en chemin physique Path.
        Supporte les extensions omises pour story:// (ex: story://REC-001 -> REC-001.md).
        """
        clean_uri = uri.strip()
        proj_root = cls.get_project_root(project_name, base_dir)

        # Vérification des schémas connus
        for scheme, rel_folder in cls.SCHEME_MAPPINGS.items():
            if clean_uri.startswith(scheme):
                target_rel = clean_uri[len(scheme):].lstrip("/\\")
                
                # Auto-complétion de l'extension .md pour les stories
                if scheme == "story://" and not target_rel.endswith(".md"):
                    target_rel = f"{target_rel}.md"
                # Auto-complétion de l'extension .md pour les dossiers de preuves si abrégé
                elif scheme == "evidence://" and not (target_rel.endswith(".md") or target_rel.endswith(".json")):
                    target_rel = f"{target_rel}_fact_dossier.md"

                resolved = proj_root / rel_folder / target_rel
                return resolved

        # Fallback pour chemins standards ou déjà relatifs
        if clean_uri.startswith("file:///"):
            raw_path = clean_uri.replace("file:///", "")
            return Path(raw_path)
            
        return proj_root / clean_uri

    @classmethod
    def to_micro_uri(
        cls,
        path: Path | str,
        project_name: Optional[str] = None,
        base_dir: Optional[Path] = None,
    ) -> str:
        """
        Convertit un chemin physique en Micro-URI condensée si éligible.
        """
        path_obj = Path(path)
        path_str = path_obj.as_posix()
        proj_root = cls.get_project_root(project_name, base_dir).as_posix()

        # Nettoyage du préfixe racine projet
        if path_str.startswith(proj_root):
            path_str = path_str[len(proj_root):].lstrip("/")

        # Normalisation si chemin contient Projects/<nom>
        if "Projects/" in path_str:
            parts = path_str.split("Projects/", 1)[-1].split("/", 1)
            if len(parts) > 1:
                path_str = parts[1]

        # Détection du schéma applicable
        for scheme, rel_folder in cls.SCHEME_MAPPINGS.items():
            if path_str.startswith(rel_folder + "/") or path_str.startswith(rel_folder):
                remainder = path_str[len(rel_folder):].lstrip("/")
                if scheme == "story://" and remainder.endswith(".md"):
                    remainder = remainder[:-3]
                return f"{scheme}{remainder}"

        return path_str
