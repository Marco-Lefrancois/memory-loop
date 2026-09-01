# -*- coding: utf-8 -*-
"""
Atomic Claim Extractor (mLoop Fact-Check Engine - ADR-0326).

Décompose les critères d'acceptation et scénarios Gherkin composites
en affirmations fonctionnelles atomiques et univalentes (AtomicClaim).
Évite les angles morts où une phrase contient à la fois du vrai et du faux.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any, Optional


@dataclass
class AtomicClaim:
    """Représente une affirmation fonctionnelle atomique à vérifier."""
    claim_id: str
    story_id: str
    section_type: str  # "acceptance_criteria", "gherkin_nominal", "gherkin_exception", "gherkin_resilience", "gherkin_ux"
    step_keyword: Optional[str]  # "GIVEN", "WHEN", "THEN", "CRITERION"
    raw_text: str
    atomic_statement: str
    line_number: int
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "story_id": self.story_id,
            "section_type": self.section_type,
            "step_keyword": self.step_keyword,
            "raw_text": self.raw_text,
            "atomic_statement": self.atomic_statement,
            "line_number": self.line_number,
            "metadata": self.metadata,
        }


class ClaimExtractor:
    """Extracteur et découpeur d'assertions atomiques."""

    GHERKIN_KEYWORDS = {
        "étant donné": "GIVEN", "soit": "GIVEN", "given": "GIVEN",
        "quand": "WHEN", "lorsque": "WHEN", "when": "WHEN",
        "alors": "THEN", "donc": "THEN", "then": "THEN",
        "et": "AND", "and": "AND", "mais": "BUT", "but": "BUT"
    }

    PILLAR_PATTERNS = {
        r"nominal": "gherkin_nominal",
        r"exception": "gherkin_exception",
        r"résilience|resilience": "gherkin_resilience",
        r"ux|accessibilité|accessibilite": "gherkin_ux",
    }

    @classmethod
    def extract_claims_from_story_file(cls, story_path: str | Path) -> List[AtomicClaim]:
        """Extrait toutes les affirmations atomiques d'un fichier Markdown de User Story."""
        path_obj = Path(story_path)
        if not path_obj.exists():
            return []

        content = path_obj.read_text(encoding="utf-8", errors="ignore")
        story_id = cls._extract_story_id(content, path_obj.stem)
        return cls.extract_claims_from_markdown(content, story_id=story_id)

    @classmethod
    def extract_claims_from_markdown(cls, markdown_text: str, story_id: str = "US-000") -> List[AtomicClaim]:
        """Analyse le Markdown et extrait les assertions atomiques des critères et scénarios."""
        lines = markdown_text.splitlines()
        claims: List[AtomicClaim] = []

        current_section = "general"
        current_pillar = "gherkin_nominal"
        claim_counter = 1

        for line_idx, line in enumerate(lines, start=1):
            stripped = line.strip()
            if not stripped:
                continue

            # 1. Détection des sections principales
            if re.match(r"^##\s+Critères d'acceptation", stripped, re.IGNORECASE):
                current_section = "acceptance_criteria"
                continue
            elif re.match(r"^##\s+Scénarios de test", stripped, re.IGNORECASE):
                current_section = "gherkin"
                continue
            elif stripped.startswith("## "):
                current_section = "other"
                continue

            # 2. Détection des sous-sections de piliers Gherkin (### Pilier 1 : Nominal...)
            if current_section == "gherkin" and stripped.startswith("###"):
                for pattern, pillar_key in cls.PILLAR_PATTERNS.items():
                    if re.search(pattern, stripped, re.IGNORECASE):
                        current_pillar = pillar_key
                        break
                continue

            # 3. Traitement des critères d'acceptation (puces simples)
            if current_section == "acceptance_criteria":
                bullet_m = re.match(r'^\s*[-*]\s+(.*)$', stripped)
                if bullet_m:
                    raw_text = bullet_m.group(1).strip()
                    atomic_texts = cls._split_into_atomic_statements(raw_text)
                    for atom in atomic_texts:
                        if len(atom) > 10:
                            claims.append(AtomicClaim(
                                claim_id=f"{story_id}_AC_{claim_counter:03d}",
                                story_id=story_id,
                                section_type="acceptance_criteria",
                                step_keyword="CRITERION",
                                raw_text=raw_text,
                                atomic_statement=atom,
                                line_number=line_idx,
                            ))
                            claim_counter += 1
                continue

            # 4. Traitement des étapes Gherkin
            if current_section == "gherkin":
                # Ignorer les blocs de code markdown et les en-têtes de scénarios/fonctionnalités
                if stripped.startswith("```") or stripped.startswith("#"):
                    continue
                if re.match(r"^(?:Fonctionnalité|Feature|Scénario|Scenario|Plan du scénario|Exemples)\s*:", stripped, re.IGNORECASE):
                    # Mettre à jour le pilier si le titre du scénario contient nominal/exception/résilience/ux
                    for pattern, pillar_key in cls.PILLAR_PATTERNS.items():
                        if re.search(pattern, stripped, re.IGNORECASE):
                            current_pillar = pillar_key
                            break
                    continue

                clean_step = re.sub(r'^\s*[-*]\s+', '', stripped)
                keyword, pure_statement = cls._parse_gherkin_step(clean_step)
                # N'extraire que les vraies étapes Gherkin (avec mot-clé valide ou puces)
                if keyword != "STEP" or re.match(r'^\s*[-*]\s+', stripped):
                    if pure_statement and len(pure_statement) > 8:
                        atomic_texts = cls._split_into_atomic_statements(pure_statement)
                        for atom in atomic_texts:
                            claims.append(AtomicClaim(
                                claim_id=f"{story_id}_GK_{claim_counter:03d}",
                                story_id=story_id,
                                section_type=current_pillar,
                                step_keyword=keyword,
                                raw_text=clean_step,
                                atomic_statement=atom,
                                line_number=line_idx,
                            ))
                            claim_counter += 1

        return claims

    @classmethod
    def _parse_gherkin_step(cls, text: str) -> tuple[str, str]:
        """Extrait le mot-clé Gherkin normalisé (GIVEN, WHEN, THEN) et l'énoncé."""
        lower = text.lower()
        for kw_phrase, norm_kw in cls.GHERKIN_KEYWORDS.items():
            if lower.startswith(kw_phrase + " "):
                statement = text[len(kw_phrase):].strip()
                return (norm_kw, statement)
        return ("STEP", text)

    @classmethod
    def _split_into_atomic_statements(cls, text: str) -> List[str]:
        """Décompose une phrase composite contenant des conjonctions en affirmations atomiques."""
        # Ne découpe pas si c'est un nom propre ou une expression fixe
        # Découpe sur : ", et ", " ainsi que ", " tout en ", " et affiche "
        delimiters = [
            r",\s+et\s+",
            r"\s+ainsi\s+que\s+",
            r",\s+and\s+",
            r"\s+tout\s+en\s+",
            r"\s+afin\s+de\s+",
        ]
        pattern = "|".join(delimiters)
        parts = re.split(pattern, text, flags=re.IGNORECASE)
        clean_parts = [p.strip().rstrip(".,;") for p in parts if len(p.strip()) > 8]
        return clean_parts if clean_parts else [text.strip().rstrip(".,;")]

    @classmethod
    def _extract_story_id(cls, content: str, default_id: str) -> str:
        """Extrait l'ID de la story depuis le frontmatter YAML ou le nom de fichier."""
        fm_m = re.search(r'^id:\s*([A-Za-z0-9_-]+)', content, re.MULTILINE)
        if fm_m:
            return fm_m.group(1).strip()
        jira_m = re.search(r'^jira_key:\s*([A-Za-z0-9_-]+)', content, re.MULTILINE)
        if jira_m:
            return jira_m.group(1).strip()
        return default_id
