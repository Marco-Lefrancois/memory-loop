# -*- coding: utf-8 -*-
"""
mirror_sync.py - Moteur de Synchronisation Miroir des Personas OpenCode (MLOOP-250-BE).

Projette de manière déterministe les personas mLoop (.agents/agents/*.md) dans
le format déclaratif d'OpenCode (.opencode/agents/*.md).
Conforme ADR-0202 (<=300L), ADR-0377 (Runtimes Aval) et ADR-0379 (Confinement SSOT).
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import yaml

logger = logging.getLogger("mloop.bridges.opencode.mirror_sync")

FORBIDDEN_SKILLS = {"forbidden-skill-canary"}
PRIMARY_PERSONAS = {"worker", "craftsman"}


class PersonasSyncError(Exception):
    """Exception levée lors d'une erreur d'analyse ou d'écriture des personas."""


class PersonasSyncEngine:
    """Moteur de projection miroir bidirectionnelle des agents vers OpenCode."""

    def __init__(
        self,
        workspace_root: Optional[Path] = None,
        source_dir: Optional[Path] = None,
        target_dir: Optional[Path] = None,
    ) -> None:
        self.root = Path(workspace_root) if workspace_root else Path.cwd()
        self.source_dir = Path(source_dir) if source_dir else self.root / ".agents" / "agents"
        self.target_dir = Path(target_dir) if target_dir else self.root / ".opencode" / "agents"

    def ensure_target_dir(self) -> Path:
        """Assure la présence du dossier .opencode/agents/."""
        self.target_dir.mkdir(parents=True, exist_ok=True)
        return self.target_dir

    def parse_agent_manifest(self, file_path: Path) -> Dict[str, Any]:
        """Extrait le frontmatter YAML et le corps Markdown d'un manifeste d'agent."""
        content = file_path.read_text(encoding="utf-8")
        if not content.startswith("---"):
            raise PersonasSyncError(f"Format invalide (frontmatter absent) : {file_path.name}")

        parts = content.split("---", 2)
        if len(parts) < 3:
            raise PersonasSyncError(f"Structure de frontmatter incomplète dans {file_path.name}")

        try:
            meta = yaml.safe_load(parts[1]) or {}
        except Exception as e:
            raise PersonasSyncError(f"Erreur de syntaxe YAML dans {file_path.name} : {e}") from e

        meta["body"] = parts[2].strip()
        meta.setdefault("name", file_path.stem)
        meta.setdefault("skills", [])
        return meta

    def render_opencode_agent(self, agent_data: Dict[str, Any]) -> str:
        """Génère le texte Markdown déclaratif au format OpenCode."""
        name = agent_data.get("name", "agent").lower()
        is_primary = name in PRIMARY_PERSONAS
        raw_skills = agent_data.get("skills", [])

        # Confinement strict ADR-0379 : élimination des skills interdites
        filtered_skills = [s for s in raw_skills if s not in FORBIDDEN_SKILLS]

        frontmatter: Dict[str, Any] = {
            "name": name,
            "role": agent_data.get("role", "Assistant"),
            "description": agent_data.get("description", ""),
            "mode": "primary" if is_primary else "subagent",
        }

        if not is_primary:
            frontmatter["subagent_depth"] = 1

        if filtered_skills:
            frontmatter["tools"] = filtered_skills

        yaml_str = yaml.dump(frontmatter, allow_unicode=True, sort_keys=False).strip()
        body = agent_data.get("body", "").strip()

        return f"---\n{yaml_str}\n---\n\n{body}\n"

    def sync_all(self) -> Dict[str, Any]:
        """Synchronise tous les agents de façon idempotente."""
        self.ensure_target_dir()
        stats: Dict[str, Any] = {"synced": 0, "skipped": 0, "errors": []}

        if not self.source_dir.exists():
            logger.warning(f"Répertoire source introuvable : {self.source_dir}")
            return stats

        for src_file in sorted(self.source_dir.glob("*.md")):
            try:
                data = self.parse_agent_manifest(src_file)
                rendered = self.render_opencode_agent(data)
                target_file = self.target_dir / f"{data['name']}.md"

                if target_file.exists():
                    existing = target_file.read_text(encoding="utf-8")
                    if existing == rendered:
                        stats["skipped"] += 1
                        continue

                target_file.write_text(rendered, encoding="utf-8")
                stats["synced"] += 1
                logger.info(f"[OpenCodeMirror] Synchronisé : {target_file.name}")
            except Exception as e:
                logger.error(f"Erreur sur {src_file.name} : {e}")
                stats["errors"].append(src_file.name)

        return stats

    def check_mirror_parity(self) -> Tuple[bool, List[str]]:
        """Contrôle que chaque agent source est projeté dans .opencode/agents/."""
        if not self.source_dir.exists():
            return True, []

        missing: List[str] = []
        for src_file in self.source_dir.glob("*.md"):
            agent_name = src_file.stem
            target_file = self.target_dir / f"{agent_name}.md"
            if not target_file.exists():
                missing.append(agent_name)

        return len(missing) == 0, sorted(missing)
