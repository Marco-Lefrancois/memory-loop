# -*- coding: utf-8 -*-
"""
Tests TDD pour le moteur d invariants de domaine (ADR-0352).
Couvre P1 (polarite), P2 (physique/temporel), P3 (CRUD intention).
Zero LLM - 100% deterministe.
"""

import pytest
from src.engine.fact_check.domain_invariants import (
    DomainInvariantChecker,
    InvariantCode,
    InvariantSeverity,
    InvariantReport,
    _detect_polarity,
)


# ─── Helper ───────────────────────────────────────────────────────────────────

def first_blocking(report: InvariantReport):
    """Retourne la premiere violation BLOCKING ou None."""
    bl = report.blocking_violations
    return bl[0] if bl else None


def first_warning(report: InvariantReport):
    """Retourne le premier WARNING ou None."""
    wn = report.warnings
    return wn[0] if wn else None


# ─── P1 : Polarite ────────────────────────────────────────────────────────────

class TestP1Polarity:

    def test_detect_polarity_negative(self):
        assert _detect_polarity("Cette operation est strictement interdite.") == "NEGATIVE"

    def test_detect_polarity_positive(self):
        assert _detect_polarity("L operateur peut modifier le lot.") == "POSITIVE"

    def test_detect_polarity_neutral(self):
        assert _detect_polarity("Le systeme affiche la liste.") == "NEUTRAL"

    def test_negation_inversion_blocking(self):
        """SSOT interdit, claim autorise -> BLOCKING DI-POL-001"""
        ssot = "Il est strictement interdit de modifier un lot scelle sans validation superviseur."
        claim = "L operateur peut modifier un lot scelle."
        report = DomainInvariantChecker.check_claim(claim, ssot)
        v = first_blocking(report)
        assert v is not None
        assert v.code == InvariantCode.DI_POL_NEGATION_INVERSION
        assert v.severity == InvariantSeverity.BLOCKING

    def test_permission_denied_blocking(self):
        """SSOT autorise, claim interdit -> BLOCKING DI-POL-002"""
        ssot = "L operateur peut annuler un coup depuis la liste de planification."
        claim = "Il est impossible d annuler un coup depuis la liste."
        report = DomainInvariantChecker.check_claim(claim, ssot)
        v = first_blocking(report)
        assert v is not None
        assert v.code == InvariantCode.DI_POL_PERMISSION_DENIED

    def test_no_polarity_conflict_when_both_neutral(self):
        """Pas de violation quand les deux textes sont neutres."""
        ssot = "Le systeme affiche la liste des coups planifies."
        claim = "Le systeme affiche la liste des coups planifies."
        report = DomainInvariantChecker.check_claim(claim, ssot)
        assert first_blocking(report) is None

    def test_no_polarity_conflict_when_same_polarity(self):
        """Pas de violation quand claim et SSOT ont la meme polarite."""
        ssot = "Il est interdit de creer un coup sans incubateur actif."
        claim = "Il est impossible de planifier sans incubateur."
        report = DomainInvariantChecker.check_claim(claim, ssot)
        # Les deux sont NEGATIVE -> pas de conflit de polarite
        assert first_blocking(report) is None or first_blocking(report).code != InvariantCode.DI_POL_NEGATION_INVERSION


# ─── P2 : Invariants Physiques ───────────────────────────────────────────────

class TestP2Temperature:

    def test_temperature_normal_no_violation(self):
        text = "La temperature de 99.5 F est maintenue par le setter."
        report = DomainInvariantChecker.check_claim(text)
        temp_viols = [v for v in report.violations if v.code == InvariantCode.DI_PHY_TEMP_OUT_OF_RANGE]
        assert len(temp_viols) == 0

    def test_temperature_too_low_blocking(self):
        text = "La temperature de 50 F est appliquee a l incubation."
        report = DomainInvariantChecker.check_claim(text)
        v = first_blocking(report)
        assert v is not None
        assert v.code == InvariantCode.DI_PHY_TEMP_OUT_OF_RANGE

    def test_temperature_too_high_blocking(self):
        text = "Le systeme maintient une temperature de 200F dans le hatcher."
        report = DomainInvariantChecker.check_claim(text)
        v = first_blocking(report)
        assert v is not None
        assert v.code == InvariantCode.DI_PHY_TEMP_OUT_OF_RANGE

    def test_no_false_positive_without_temp_keyword(self):
        """Un nombre comme 150 sans contexte de temperature ne genere pas de violation."""
        text = "Le lot numero 150 est assigne au setter."
        report = DomainInvariantChecker.check_claim(text)
        temp_viols = [v for v in report.violations if v.code == InvariantCode.DI_PHY_TEMP_OUT_OF_RANGE]
        assert len(temp_viols) == 0


class TestP2Capacity:

    def test_egg_count_normal_no_violation(self):
        text = "Un buggy contient 4200 oeufs pour ce coup d incubation."
        report = DomainInvariantChecker.check_claim(text)
        cap_viols = [v for v in report.violations if v.code == InvariantCode.DI_PHY_CAPACITY_EXCEEDED]
        assert len(cap_viols) == 0

    def test_egg_count_too_high_blocking(self):
        text = "Le chariot est charge avec 50000 oeufs."
        report = DomainInvariantChecker.check_claim(text)
        v = first_blocking(report)
        assert v is not None
        assert v.code == InvariantCode.DI_PHY_CAPACITY_EXCEEDED

    def test_slot_number_valid_no_violation(self):
        text = "L affectation est creee sur le slot 3 de l incubateur."
        report = DomainInvariantChecker.check_claim(text)
        slot_viols = [v for v in report.violations if v.code == InvariantCode.DI_PHY_SLOT_OUT_OF_RANGE]
        assert len(slot_viols) == 0

    def test_slot_number_out_of_range_blocking(self):
        text = "Le lot est assigne au slot 150 de l incubateur."
        report = DomainInvariantChecker.check_claim(text)
        v = first_blocking(report)
        assert v is not None
        assert v.code == InvariantCode.DI_PHY_SLOT_OUT_OF_RANGE


class TestP2CausalOrder:

    def test_valid_causal_order_no_violation(self):
        """Reception avant incubation -> ordre correct, pas de violation."""
        text = "Apres la reception des oeufs, le lot est mis en incubation dans le setter."
        report = DomainInvariantChecker.check_claim(text)
        causal_viols = [v for v in report.violations if v.code == InvariantCode.DI_TMP_CAUSAL_ORDER]
        assert len(causal_viols) == 0

    def test_invalid_causal_order_eclosion_before_incubation(self):
        """Eclosion mentionnee avant incubation dans le texte -> BLOCKING."""
        text = "Le hatcher produit les poussins avant d etre mis en incubation dans le setter."
        report = DomainInvariantChecker.check_claim(text)
        v = first_blocking(report)
        assert v is not None
        assert v.code == InvariantCode.DI_TMP_CAUSAL_ORDER

    def test_invalid_causal_order_mirage_before_reception(self):
        """Mirage avant reception -> BLOCKING."""
        text = "Le mirage est effectue avant la reception du lot."
        report = DomainInvariantChecker.check_claim(text)
        v = first_blocking(report)
        assert v is not None
        assert v.code == InvariantCode.DI_TMP_CAUSAL_ORDER


class TestP2MutualExclusion:

    def test_no_mutual_exclusion_single_status(self):
        text = "Le coup passe au statut PLANIFIE lors de la reservation."
        report = DomainInvariantChecker.check_claim(text)
        mutex_viols = [v for v in report.violations if v.code == InvariantCode.DI_STATE_MUTUAL_EXCLUSION]
        assert len(mutex_viols) == 0

    def test_mutex_planifie_and_termine_blocking(self):
        text = "Le coup est simultanément PLANIFIE et TERMINE."
        report = DomainInvariantChecker.check_claim(text)
        v = first_blocking(report)
        assert v is not None
        assert v.code == InvariantCode.DI_STATE_MUTUAL_EXCLUSION

    def test_mutex_planifie_and_annule_blocking(self):
        text = "Le batch reste PLANIFIE tout en etant ANNULE par l utilisateur."
        report = DomainInvariantChecker.check_claim(text)
        v = first_blocking(report)
        assert v is not None
        assert v.code == InvariantCode.DI_STATE_MUTUAL_EXCLUSION


# ─── P3 : Intention CRUD ──────────────────────────────────────────────────────

class TestP3CRUDIntention:

    def test_get_without_mutation_no_warning(self):
        text = "Consulter la liste des affectations actives du couple setter/slot."
        report = DomainInvariantChecker.check_claim(text)
        crud_viols = [v for v in report.violations if v.code == InvariantCode.DI_CRUD_GET_MUTATION]
        assert len(crud_viols) == 0

    def test_get_with_mutation_warning(self):
        text = "GET /api/incubation/assignments - Quand je consulte la liste, le lot est supprime."
        report = DomainInvariantChecker.check_claim(text)
        w = first_warning(report)
        assert w is not None
        assert w.code == InvariantCode.DI_CRUD_GET_MUTATION
        assert w.severity == InvariantSeverity.WARNING

    def test_post_with_mutation_no_warning(self):
        """Un recit de creation (POST) avec mutation est normal."""
        text = "POST /api/incubation/batches - Creer un nouveau coup d incubation."
        report = DomainInvariantChecker.check_claim(text)
        crud_viols = [v for v in report.violations if v.code == InvariantCode.DI_CRUD_GET_MUTATION]
        assert len(crud_viols) == 0

    def test_read_only_story_with_update_triggers_warning(self):
        text = "En lecture seule, l operateur peut modifier le statut du lot."
        report = DomainInvariantChecker.check_claim(text)
        w = first_warning(report)
        assert w is not None
        assert w.code == InvariantCode.DI_CRUD_GET_MUTATION


# ─── check_story_text (integration) ──────────────────────────────────────────

class TestCheckStoryText:

    def test_clean_story_passes(self):
        story = """
## Description
L operateur consulte la liste des affectations PLANIFIE pour le setter INC-01.
## Criteres d acceptation
- Le systeme affiche les coups planifies avec leur slot 3.
"""
        report = DomainInvariantChecker.check_story_text(story)
        assert report.passed is True
        assert len(report.blocking_violations) == 0

    def test_story_with_multiple_violations(self):
        story = """
## Description
Consulter et supprimer les lots.
## Criteres
- Le hatcher est ready avant l incubation.
- Temperature de 200F appliquee.
- Le lot contient 100000 oeufs.
"""
        report = DomainInvariantChecker.check_story_text(story)
        assert report.passed is False
        blocking_codes = {v.code for v in report.blocking_violations}
        assert InvariantCode.DI_TMP_CAUSAL_ORDER in blocking_codes
        assert InvariantCode.DI_PHY_TEMP_OUT_OF_RANGE in blocking_codes
        assert InvariantCode.DI_PHY_CAPACITY_EXCEEDED in blocking_codes

    def test_to_dict_structure(self):
        story = "Consulter et supprimer les lots PLANIFIE et TERMINE."
        report = DomainInvariantChecker.check_story_text(story)
        d = report.to_dict()
        assert "passed" in d
        assert "blocking_count" in d
        assert "violations" in d
        assert isinstance(d["violations"], list)
