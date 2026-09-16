"""
Tests TDD pour la clause d'exemption OQ dans DevilAdvocateCritic.
Conformité : ADR-0319 (Contrats d'Interface & Anti-Invention) et ADR-0369.
Lacune : L-09 (Faux positifs Critic sur les OQ à 4 chiffres).
"""

import pytest
from src.engine.rubber_duck.critic import DevilAdvocateCritic


def test_oq_exemption_3_digits() -> None:
    """Vérifie l'exemption pour les OQ à 3 chiffres (ex. OQ-001, OQ-999)."""
    text_001 = "Route [API de soumission à définir] liée à OQ-001."
    text_999 = "Endpoint à confirmer sous OQ-999."
    
    assert DevilAdvocateCritic._has_oq_exemption(text_001) is True
    assert DevilAdvocateCritic._has_oq_exemption(text_999) is True


def test_oq_exemption_4_digits() -> None:
    """Vérifie l'exemption pour les OQ à 4 chiffres (ex. OQ-1001, OQ-9999) - L-09."""
    text_1001 = "Route [API de soumission à définir] liée à OQ-1001."
    text_9999 = "Endpoint à définir sous OQ-9999."

    assert DevilAdvocateCritic._has_oq_exemption(text_1001) is True
    assert DevilAdvocateCritic._has_oq_exemption(text_9999) is True


def test_oq_exemption_missing_oq() -> None:
    """Vérifie qu'en l'absence d'identifiant OQ valide, l'exemption est refusée."""
    text_no_oq = "Route [API de soumission à définir] sans référence formelle."
    assert DevilAdvocateCritic._has_oq_exemption(text_no_oq) is False


def test_oq_exemption_missing_marker() -> None:
    """Vérifie qu'un OQ sans mention de report (à définir / à confirmer) ne déclenche pas l'exemption."""
    text_unconfirmed = "Ce module résout OQ-1001 sans mention de route."
    assert DevilAdvocateCritic._has_oq_exemption(text_unconfirmed) is False


def test_oq_exemption_invalid_digits() -> None:
    """Vérifie que les OQ non conformes (2 chiffres ou 5 chiffres) ne sont pas exemptés."""
    text_2_digits = "Route à définir liée à OQ-12."
    text_5_digits = "Route à définir liée à OQ-12345."

    assert DevilAdvocateCritic._has_oq_exemption(text_2_digits) is False
    assert DevilAdvocateCritic._has_oq_exemption(text_5_digits) is False
