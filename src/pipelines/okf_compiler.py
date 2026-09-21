import datetime
import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple
import yaml

logger = logging.getLogger(__name__)

REQUIRED_OKF_FIELDS = {"type", "title", "description", "tags"}


class OKFValidationError(ValueError):
    """Erreur levée en cas de non-conformité au standard OKF v0.1."""
    pass


class OKFCompiler:
    """Compilateur Open Knowledge Format (OKF v0.1) et Usine de Compétences Typées (ADR-0003)."""

    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.skills_dir = project_path / ".agents" / "skills"
        self.skills_index_file = self.skills_dir / "index.json"

    def parse_frontmatter(self, text: str) -> Tuple[Dict[str, Any], str]:
        if not text.startswith("---"):
            return {}, text
        parts = text.split("---", 2)
        if len(parts) < 3:
            return {}, text
        try:
            data = yaml.safe_load(parts[1])
            return (data if isinstance(data, dict) else {}), parts[2].strip()
        except Exception as exc:
            logger.debug(f"Erreur parsing YAML frontmatter: {exc}", exc_info=True)
            return {}, text

    def validate_manifest(self, frontmatter: Dict[str, Any]) -> Tuple[bool, str]:
        missing = [field for field in REQUIRED_OKF_FIELDS if field not in frontmatter or not frontmatter[field]]
        if missing:
            err = f"ERR_OKF_INVALID_MANIFEST: Champs requis manquants ({', '.join(missing)})"
            return False, err
        return True, ""

    def extract_typed_entities(self, text: str) -> Dict[str, List[str]]:
        """Extrait les entités typées en 4 catégories fondamentales."""
        entities: Dict[str, List[str]] = {
            "People": [],
            "Organizations": [],
            "Places": [],
            "Products/Features": [],
        }

        # 1. Organizations
        org_patterns = [r"\b(Google(?:\s+Cloud)?|Microsoft|Metro|Apple|AWS|Azure|OpenAI|Anthropic)\b"]
        for p in org_patterns:
            for match in re.finditer(p, text, re.IGNORECASE):
                val = match.group(0).strip()
                if val and val not in entities["Organizations"]:
                    entities["Organizations"].append(val)

        # 2. People (Heuristique basée sur les salutations et titres)
        people_patterns = [r"\b(?:M\.|Mme|Dr|PO|Dev|Agent)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b"]
        for p in people_patterns:
            for match in re.finditer(p, text):
                val = match.group(1).strip()
                if val and val not in entities["People"]:
                    entities["People"].append(val)

        # 3. Places (Régions cloud, villes, pays)
        place_patterns = [r"\b(Montréal|Québec|Canada|US-East|Europe|North-America|Cloud)\b"]
        for p in place_patterns:
            for match in re.finditer(p, text, re.IGNORECASE):
                val = match.group(0).strip()
                if val and val not in entities["Places"]:
                    entities["Places"].append(val)

        # 4. Products & Features (Acronymes, PascalCase et noms d'outils)
        feat_patterns = [r"\b(mLoop|MarkItDown|Graphify|WikiFix|StoryGuard|Wayfinder|FTS5|SQLite|DAG|API)\b"]
        for p in feat_patterns:
            for match in re.finditer(p, text, re.IGNORECASE):
                val = match.group(0).strip()
                if val and val not in entities["Products/Features"]:
                    entities["Products/Features"].append(val)

        return entities

    def compile_to_skill(self, source_file: Path, skill_name: str) -> Path:
        """Compile un document source OKF en paquet de compétence .agents/skills/<skill_name>/SKILL.md."""
        if not source_file.exists():
            raise FileNotFoundError(f"Fichier source introuvable: {source_file}")

        raw_content = source_file.read_text(encoding="utf-8")
        frontmatter, body = self.parse_frontmatter(raw_content)

        is_valid, err_msg = self.validate_manifest(frontmatter)
        if not is_valid:
            raise OKFValidationError(err_msg)

        entities = self.extract_typed_entities(body)

        target_dir = self.skills_dir / skill_name
        target_dir.mkdir(parents=True, exist_ok=True)
        target_skill_md = target_dir / "SKILL.md"

        skill_frontmatter = {
            "name": skill_name,
            "title": frontmatter.get("title", skill_name),
            "description": frontmatter.get("description", ""),
            "type": frontmatter.get("type", "Skill"),
            "tags": frontmatter.get("tags", []),
            "source_uri": f"skill://{skill_name}",
            "compiled_at": datetime.datetime.now().isoformat(),
            "okf_version": "0.1",
        }

        content_lines = [
            "---",
            yaml.dump(skill_frontmatter, sort_keys=False).strip(),
            "---",
            f"# Compétence {skill_frontmatter['title']}\n",
            f"> {skill_frontmatter['description']}\n",
            "## Entités Typées Extraites",
        ]
        for cat, items in entities.items():
            content_lines.append(f"- **{cat}** : {', '.join(items) if items else 'Aucune'}")

        content_lines.extend(["\n## Instructions & Spécifications", body])

        target_skill_md.write_text("\n".join(content_lines), encoding="utf-8")
        self._update_skills_index(skill_name, skill_frontmatter)
        return target_skill_md

    def _update_skills_index(self, skill_name: str, meta: Dict[str, Any]) -> None:
        index_data = {}
        if self.skills_index_file.exists():
            try:
                index_data = json.loads(self.skills_index_file.read_text(encoding="utf-8"))
            except Exception as exc:
                logger.debug(f"Erreur lecture index compétences: {exc}", exc_info=True)
        index_data[skill_name] = {
            "uri": f"skill://{skill_name}",
            "title": meta.get("title", skill_name),
            "description": meta.get("description", ""),
            "compiled_at": meta.get("compiled_at"),
        }
        try:
            self.skills_dir.mkdir(parents=True, exist_ok=True)
            self.skills_index_file.write_text(json.dumps(index_data, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception as exc:
            logger.debug(f"Erreur écriture index compétences: {exc}", exc_info=True)
