"""
Parseur de plan d'implémentation Markdown pour extraction de la matrice de traçabilité.
Conforme ADR-0394, ADR-0369 (Senior Python, zéro dépendance externe).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING, List, Optional

from src.pipelines.evidence_types import CodeTraceabilityEntry

if TYPE_CHECKING:
    from src.pipelines.evidence_pack import EvidencePackEngine
else:
    EvidencePackEngine = "EvidencePackEngine"

_EvidencePackEngine = EvidencePackEngine


class PlanEvidenceParser:
    """
    Parseur déterministe de la section 'Matrice de Traçabilité Code ↔ Exigences'
    depuis un plan d'implémentation Markdown (GFM table syntax).
    """

    # En-têtes attendus du tableau (insensibles à la casse et aux espaces)
    REQUIRED_HEADERS = [
        "symbole ast qualifié",
        "règle métier cible",
        "scénario gherkin",
        "justification",
        "test unitaire",
    ]

    # Alias acceptés pour chaque colonne (insensibles à la casse)
    HEADER_ALIASES = {
        "symbole ast qualifié": ["symbole ast qualifié", "symbole ast", "ast symbol", "ast_symbol"],
        "règle métier cible": [
            "règle métier cible",
            "règle métier",
            "requirement ref",
            "requirement_ref",
        ],
        "scénario gherkin": [
            "scénario gherkin",
            "scenario gherkin",
            "gherkin scenario",
            "gherkin_scenario",
        ],
        "justification": [
            "justification",
            "rationale",
            "justification de l'implémentation",
        ],
        "test unitaire": [
            "test unitaire",
            "test unitaire associé",
            "test symbol",
            "test_symbol",
        ],
    }

    # Pattern pour ligne de délimiteur Markdown complète (ex: | --- | --- | --- |)
    # N'utilise PAS \s qui inclut \n, utilise [ \t\-\:]+ pour le contenu des cellules
    DELIMITER_ROW_PATTERN = r"\|(?:[ \t\-\:]+\|)+"

    @staticmethod
    def _normalize_header(header: str) -> str:
        """Normalise un en-tête pour comparaison (minuscules, espaces, accents)."""
        h = header.strip().lower()
        h = h.replace("é", "e").replace("è", "e").replace("ê", "e")
        h = h.replace("à", "a").replace("â", "a").replace("î", "i").replace("ô", "o")
        h = h.replace("ù", "u").replace("û", "u").replace("ç", "c")
        return re.sub(r"\s+", " ", h).strip()

    @staticmethod
    def _match_header(normalized: str) -> Optional[str]:
        """Trouve l'en-tête canonique correspondant à un en-tête normalisé."""
        for canonical, aliases in PlanEvidenceParser.HEADER_ALIASES.items():
            for alias in aliases:
                if PlanEvidenceParser._normalize_header(alias) == normalized:
                    return canonical
        return None

    @classmethod
    def extract_matrix_from_plan(cls, plan_path: Path) -> List[CodeTraceabilityEntry]:
        """
        Extrait la matrice de traçabilité depuis un fichier plan Markdown.

        Args:
            plan_path: Chemin vers le fichier plan d'implémentation (.md)

        Returns:
            Liste d'entrées CodeTraceabilityEntry validées

        Raises:
            FileNotFoundError: si le fichier plan n'existe pas
            ValueError: si la section ou le tableau est mal formé
        """
        if not plan_path.exists():
            raise FileNotFoundError(f"Plan d'implémentation introuvable : {plan_path}")

        content = plan_path.read_text(encoding="utf-8")
        return cls.extract_matrix_from_text(content)

    @classmethod
    def extract_matrix_from_text(cls, content: str) -> List[CodeTraceabilityEntry]:
        """
        Extrait la matrice de traçabilité depuis du texte Markdown brut.

        Args:
            content: Contenu textuel du plan d'implémentation

        Returns:
            Liste d'entrées CodeTraceabilityEntry validées

        Raises:
            ValueError: si la section ou le tableau est mal formé
        """
        # 1. Localiser la section "Matrice de Traçabilité Code ↔ Exigences"
        section_pattern = re.compile(
            r"(?im)^\s*#{1,3}\s*Matrice de Traçabilité Code\s*↔\s*Exigences\s*\n", re.MULTILINE
        )
        section_match = section_pattern.search(content)
        if not section_match:
            # Essayer variantes d'en-tête
            alt_pattern = re.compile(r"(?im)^\s*#{1,3}\s*Matrice de Traçabilité\s*\n", re.MULTILINE)
            section_match = alt_pattern.search(content)
            if not section_match:
                raise ValueError(
                    "[PlanEvidenceParser] Section 'Matrice de Traçabilité Code ↔ Exigences' "
                    "introuvable dans le plan d'implémentation."
                )

        # 2. Extraire le contenu après la section jusqu'à la prochaine section de même niveau ou fin
        start_pos = section_match.end()
        next_section = re.search(r"(?m)^\s*#{1,3}\s+\S", content[start_pos:])
        end_pos = start_pos + next_section.start() if next_section else len(content)
        section_content = content[start_pos:end_pos]

        # 3. Trouver le premier tableau Markdown (pipes) dans la section
        # Autorise des lignes vides optionnelles entre l'en-tête de section et le tableau
        # Utilise DELIMITER_CELL_PATTERN pour éviter que \s ne capture les newlines
        delimiter_pat = cls.DELIMITER_ROW_PATTERN
        table_match = re.search(
            rf"(?ms)\|.+\|\s*\n\s*{delimiter_pat}\s*\n(?:\s*\|.+\|\s*\n?)+", section_content
        )
        if not table_match:
            raise ValueError(
                "[PlanEvidenceParser] Aucun tableau Markdown valide trouvé dans la section "
                "'Matrice de Traçabilité Code ↔ Exigences'."
            )

        table_text = table_match.group(0)
        return cls._parse_gfm_table(table_text)

    @classmethod
    def _parse_gfm_table(cls, table_text: str) -> List[CodeTraceabilityEntry]:
        """
        Parse un tableau GFM (GitHub Flavored Markdown) en entrées de traçabilité.

        Format attendu :
        | Symbole AST Qualifié | Règle Métier Cible | Scénario Gherkin | Justification | Test Unitaire |
        | --- | --- | --- | --- | --- |
        | src/core/auth.py::TokenVerifier.verify_expiration | RM-012 | Pilier 2 | Justification... | tests/test_auth.py::test_expired |
        """
        lines = [line.strip() for line in table_text.strip().splitlines() if line.strip()]

        if len(lines) < 3:
            raise ValueError(
                "[PlanEvidenceParser] Tableau trop court : il faut au minimum "
                "une ligne d'en-tête, une ligne de délimiteur et une ligne de données."
            )

        # Ligne 0 : en-têtes
        header_line = lines[0]
        # Ligne 1 : délimiteur (--- | --- | ---)
        delimiter_line = lines[1]
        # Lignes 2+ : données
        data_lines = lines[2:]

        # Parser les en-têtes
        raw_headers = [
            cell.strip() for cell in header_line.split("|")[1:-1]
        ]  # ignore premier/dernier vide
        if len(raw_headers) < 5:
            raise ValueError(
                f"[PlanEvidenceParser] En-têtes insuffisants ({len(raw_headers)}/5). "
                f"Attendus : {', '.join(cls.REQUIRED_HEADERS)}"
            )

        # Mapper chaque colonne à son en-tête canonique
        header_map = {}
        for idx, raw in enumerate(raw_headers):
            norm = cls._normalize_header(raw)
            canonical = cls._match_header(norm)
            if canonical is None:
                raise ValueError(
                    f"[PlanEvidenceParser] En-tête non reconnu à la colonne {idx + 1} : '{raw}'. "
                    f"Attendus : {', '.join(cls.REQUIRED_HEADERS)}"
                )
            if canonical in header_map:
                raise ValueError(f"[PlanEvidenceParser] En-tête dupliqué : '{canonical}'")
            header_map[canonical] = idx

        # Vérifier que tous les en-têtes requis sont présents
        missing = set(cls.REQUIRED_HEADERS) - set(header_map.keys())
        if missing:
            raise ValueError(f"[PlanEvidenceParser] En-têtes manquants : {', '.join(missing)}")

        # Parser les lignes de données
        entries: List[CodeTraceabilityEntry] = []
        for row_idx, data_line in enumerate(data_lines, start=1):
            cells = [cell.strip() for cell in data_line.split("|")[1:-1]]
            if len(cells) != len(raw_headers):
                raise ValueError(
                    f"[PlanEvidenceParser] Ligne {row_idx} : nombre de cellules ({len(cells)}) "
                    f"différent du nombre d'en-têtes ({len(raw_headers)})"
                )

            # Extraire les valeurs par en-tête canonique
            ast_symbol = cells[header_map["symbole ast qualifié"]].strip("` \t")
            requirement_ref = cells[header_map["règle métier cible"]].strip("` \t")
            gherkin_scenario = cells[header_map["scénario gherkin"]].strip("` \t")
            rationale = cells[header_map["justification"]].strip("` \t")
            test_symbol_raw = cells[header_map["test unitaire"]].strip("` \t")

            # Nettoyer les backticks et liens markdown résiduels
            ast_symbol = re.sub(r"`+", "", ast_symbol).strip()
            requirement_ref = re.sub(r"`+", "", requirement_ref).strip()
            gherkin_scenario = re.sub(r"`+", "", gherkin_scenario).strip()
            rationale = re.sub(r"`+", "", rationale).strip()
            test_symbol = re.sub(r"`+", "", test_symbol_raw).strip() if test_symbol_raw else None

            # Ignorer les lignes vides (ex: lignes de séparation visuelle)
            if not any([ast_symbol, requirement_ref, gherkin_scenario, rationale]):
                continue

            entry: CodeTraceabilityEntry = {
                "ast_symbol": ast_symbol,
                "requirement_ref": requirement_ref,
                "gherkin_scenario": gherkin_scenario,
                "rationale": rationale,
                "test_symbol": test_symbol,
            }

            # Validation via le moteur EvidencePack (lève ValueError si invalide)
            # Import at runtime to avoid circular import
            from src.pipelines.evidence_pack import EvidencePackEngine

            EvidencePackEngine._validate_code_traceability_entry(entry)
            entries.append(entry)

        if not entries:
            raise ValueError(
                "[PlanEvidenceParser] Aucune entrée de traçabilité valide trouvée dans le tableau."
            )

        return entries
