"""
mLoop Engine - Causal Proxy Discovery & Provenance Scoring (ADR-0354)
Inspiré du protocole de sélection intelligente de données du Google Planetary Prediction Engine.
Distingue les signaux directs des proxys causaux et applique une pondération 5x sur la provenance officielle.
"""

from __future__ import annotations

import re
import urllib.parse
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class SignalType(str, Enum):
    DIRECT = "DIRECT"              # Paramètre explicite, fonction ou colonne déjà existante
    CAUSAL_PROXY = "CAUSAL_PROXY"  # Standard d'architecture, RFC, substitut causal validé


@dataclass
class SignalHypothesis:
    name: str
    signal_type: SignalType
    rationale: str
    search_query: str
    target_domains: List[str] = field(default_factory=list)


class CausalProxyEngine:
    """
    Moteur de découverte et de qualification de signaux causaux.
    Attribue une priorité 5x aux sources faisant autorité institutionnelle ou technique.
    """

    # Domaines à autorité technique maximale (Pondération 5x)
    AUTHORITATIVE_DOMAINS = [
        "ietf.org",
        "rfc-editor.org",
        "w3.org",
        "docs.python.org",
        "developer.mozilla.org",
        "research.google",
        "arxiv.org",
        "github.com",
        "pypi.org",
        "npmjs.com",
        "ecma-international.org",
    ]

    @classmethod
    def formulate_hypotheses(cls, task_text: str) -> List[SignalHypothesis]:
        """
        Formule des hypothèses de signaux directs et de proxys causaux
        à partir d'une description de tâche ou d'une requête utilisateur.
        """
        hypotheses: List[SignalHypothesis] = []
        text_lower = task_text.lower()

        # Détection de requêtes de persistance / cache / DB
        if any(w in text_lower for w in ["cache", "store", "persist", "storage", "db", "sqlite"]):
            hypotheses.append(
                SignalHypothesis(
                    name="Persistence & Invalidation Strategy",
                    signal_type=SignalType.CAUSAL_PROXY,
                    rationale="Comportement d'invalidation et cohérence transactionnelle selon RFC/Standards.",
                    search_query=f"{task_text} RFC caching architecture standard",
                    target_domains=["ietf.org", "w3.org"],
                )
            )

        # Détection de requêtes de crawler / web / parsing
        if any(w in text_lower for w in ["crawl", "scrape", "http", "fetch", "html", "spa"]):
            hypotheses.append(
                SignalHypothesis(
                    name="HTTP & Crawling Specifications",
                    signal_type=SignalType.CAUSAL_PROXY,
                    rationale="Spécifications HTTP/1.1 et conformité robots/sitemap pour collecte éthique.",
                    search_query=f"{task_text} RFC 9110 specification W3C",
                    target_domains=["rfc-editor.org", "w3.org"],
                )
            )

        # Signal direct par défaut
        hypotheses.append(
            SignalHypothesis(
                name="Direct Functional Intent",
                signal_type=SignalType.DIRECT,
                rationale="Implémentation directe des spécifications fonctionnelles demandées.",
                search_query=task_text,
                target_domains=[],
            )
        )

        return hypotheses

    @classmethod
    def score_source_provenance(cls, url: str, title: str = "", snippet: str = "") -> float:
        """
        Calcule le score de provenance (1.0 à 5.0) en appliquant le barème PPE :
        - 5.0 si domaine officiel ou RFC
        - 3.0 si dépôt académique / doc officielle secondaire
        - 1.0 pour les blogs ou résultats génériques
        """
        if not url:
            return 1.0

        try:
            parsed = urllib.parse.urlparse(url)
            hostname = (parsed.hostname or "").lower()
        except Exception:
            return 1.0

        for auth_domain in cls.AUTHORITATIVE_DOMAINS:
            if hostname == auth_domain or hostname.endswith(f".{auth_domain}"):
                return 5.0  # Poids maximal

        # Domaines éducatifs / organisationnels
        if hostname.endswith(".edu") or hostname.endswith(".org") or hostname.endswith(".gov"):
            return 3.5

        return 1.5

    @classmethod
    def rank_sources(cls, sources: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """
        Réordonne les sources selon le score de provenance et annote chaque source.
        """
        ranked = []
        for src in sources:
            url = src.get("url", "")
            title = src.get("title", "")
            snippet = src.get("snippet", "")
            score = cls.score_source_provenance(url, title, snippet)
            item = dict(src)
            item["provenance_score"] = score
            item["is_authoritative"] = score >= 4.0
            ranked.append(item)

        # Tri décroissant par score
        ranked.sort(key=lambda x: x["provenance_score"], reverse=True)
        return ranked
