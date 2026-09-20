# -*- coding: utf-8 -*-
"""
Algorithmes de matching flou et détection des préfixes de tickets.
Sous-module du package lexicon (ADR-0202 / MLOOP-101-BE).
"""

from __future__ import annotations

import re
import unicodedata
from typing import List, Optional, Tuple


class EntityMatcher:
    """Moteur de normalisation, tokenisation et correspondance sémantique floue."""

    @classmethod
    def normalize_string(cls, text: str) -> str:
        """Supprime accents, ponctuation et espaces pour comparaison floue uniforme."""
        if not text:
            return ""
        normalized = unicodedata.normalize("NFD", str(text))
        clean = "".join(c for c in normalized if unicodedata.category(c) != "Mn")
        return re.sub(r"[^a-zA-Z0-9]", "", clean).lower()

    @classmethod
    def tokenize(cls, text: str) -> List[str]:
        """Découpe un texte en jetons de mots signifiants normalisés (support CamelCase, symboles, tirets)."""
        if not text:
            return []
        # 1. Découpage CamelCase (ex: BoireEtFrere -> Boire Et Frere, MetroFoodOffers -> Metro Food Offers)
        text_str = str(text)
        spaced = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", text_str)
        spaced = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", spaced)

        # 2. Normalisation accents & minuscules
        normalized = unicodedata.normalize("NFD", spaced)
        clean = "".join(c for c in normalized if unicodedata.category(c) != "Mn")

        # 3. Extraction des tokens alphanumériques
        tokens = re.findall(r"[a-zA-Z0-9]+", clean.lower())
        stopwords = {
            "de",
            "la",
            "le",
            "les",
            "du",
            "des",
            "et",
            "un",
            "une",
            "en",
            "pour",
            "au",
            "aux",
            "and",
            "the",
            "of",
            "in",
            "for",
            "to",
            "with",
            "a",
            "an",
            "projet",
            "project",
        }
        res = []
        for t in tokens:
            if len(t) > 1 and t not in stopwords:
                res.append(t)
            # Découpage supplémentaire si un mot composé contient des stopwords collés
            if len(t) > 5 and any(sw in t for sw in ("et", "and", "de", "du")):
                sub_parts = [
                    p
                    for p in re.split(r"(?:et|and|de|du|des|le|la)", t)
                    if len(p) > 1 and p not in stopwords
                ]
                if len(sub_parts) > 1:
                    res.extend(sub_parts)
        return res

    @classmethod
    def extract_query_prefix(cls, query: str) -> Optional[str]:
        """
        Extrait le préfixe alphabétique explicite d'un identifiant de ticket.
        Ex: 'INC-004-BE' → 'INC'. Retourne None si aucun préfixe alpha explicite.
        """
        prefix_match = re.match(r"^([A-Za-z]{2,})[-_]", query.strip())
        return prefix_match.group(1).upper() if prefix_match else None

    @classmethod
    def compute_folder_score(
        cls,
        clean_query: str,
        query_tokens: set,
        folder_name: str,
    ) -> int:
        """
        Calcule le score de correspondance entre une requête et un nom de dossier.
        Retourne un entier (plus élevé = meilleure correspondance).
        """
        score = 0
        norm_folder = cls.normalize_string(folder_name)
        folder_tokens = set(cls.tokenize(folder_name))

        # 1. Recouvrement des tokens
        token_overlap = query_tokens.intersection(folder_tokens)
        if query_tokens and len(token_overlap) == len(query_tokens):
            score += 80
        elif token_overlap:
            score += len(token_overlap) * 25

        # 2. Correspondance par sous-chaîne
        clean_query_no_stopwords = re.sub(r"(?:et|and|de|du|des|le|la|les)", "", clean_query)
        if clean_query in norm_folder or (
            len(clean_query_no_stopwords) >= 4 and clean_query_no_stopwords in norm_folder
        ):
            score += 40
        elif (
            norm_folder in clean_query
            and len(norm_folder) >= 4
            and len(norm_folder) >= 0.7 * len(clean_query)
        ):
            score += 20

        return score

    @classmethod
    def score_story_candidate(
        cls,
        query: str,
        clean_query: str,
        query_tokens: set,
        target_num: Optional[int],
        query_prefix: Optional[str],
        story_id: str,
        jira_key: str,
        title_text: str,
        tags: List[str],
        filename_norm: str,
        content: str,
    ) -> int:
        """
        Calcule le score de correspondance entre une requête et les métadonnées d'un récit.
        """
        import re as _re

        score = 0

        # 1. Correspondance exacte sur ID logique ou Clé Jira
        if clean_query in cls.normalize_string(story_id) or clean_query in cls.normalize_string(
            jira_key
        ):
            score += 100

        # 2. Correspondance numérique stricte avec contrôle du préfixe
        if target_num is not None:
            prefix_ok = True
            if query_prefix is not None:
                candidate_prefixes = {
                    m.group(0).upper()
                    for m in _re.finditer(r"[A-Za-z]{2,}", f"{story_id} {filename_norm}")
                }
                prefix_ok = query_prefix in candidate_prefixes

            if prefix_ok:
                num_in_id = _re.findall(r"\d+", story_id)
                num_in_jira = _re.findall(r"\d+", jira_key)
                num_in_file = _re.findall(r"\d+", filename_norm)
                all_nums = [int(n) for n in (num_in_id + num_in_jira + num_in_file)]
                if target_num in all_nums:
                    score += 80

        # 3. Correspondance sémantique sur le Titre Métier & H1
        title_tokens = set(cls.tokenize(title_text))
        title_overlap = query_tokens.intersection(title_tokens)
        score += len(title_overlap) * 25

        # 4. Correspondance sur les Tags et Mots-clés Frontmatter
        tag_tokens: set = set()
        for tag in tags:
            tag_tokens.update(cls.tokenize(tag))
        tag_overlap = query_tokens.intersection(tag_tokens)
        score += len(tag_overlap) * 20

        # 5. Recherche textuelle dans la Description
        desc_match = _re.search(r"## Description(.*?)(?:---|\Z)", content, _re.DOTALL)
        if desc_match:
            desc_tokens = set(cls.tokenize(desc_match.group(1)))
            desc_overlap = query_tokens.intersection(desc_tokens)
            score += len(desc_overlap) * 10

        return score
