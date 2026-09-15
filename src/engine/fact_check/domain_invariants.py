# -*- coding: utf-8 -*-
"""
Domain Invariants Engine — Couche «Gros Bon Sens» (ADR-0352).

Validateur déterministe 3 piliers, zéro appel LLM :
  P1 — Detection de Polarite et Negation Deontique (anti-faux-positif lexical)
  P2 — Invariants Physiques et Temporels (bornes, sequences, etats exclusifs)
  P3 — Integrite d intention CRUD (GET sans effet de bord)

Toutes les regles sont deterministes, inviolables, et ne dependent d aucun
score de pertinence BM25.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional, List, Tuple
from enum import Enum


# ─── Enums & Dataclasses ─────────────────────────────────────────────────────

class InvariantSeverity(str, Enum):
    BLOCKING = "BLOCKING"
    WARNING  = "WARNING"


class InvariantCode(str, Enum):
    """Codes officiels des violations de bon sens (prefixe DI = Domain Invariant)."""
    DI_POL_NEGATION_INVERSION = "DI-POL-001"
    DI_POL_PERMISSION_DENIED  = "DI-POL-002"
    DI_TMP_CAUSAL_ORDER       = "DI-TMP-001"
    DI_PHY_TEMP_OUT_OF_RANGE  = "DI-PHY-001"
    DI_PHY_CAPACITY_EXCEEDED  = "DI-PHY-002"
    DI_PHY_SLOT_OUT_OF_RANGE  = "DI-PHY-003"
    DI_STATE_MUTUAL_EXCLUSION = "DI-STA-001"
    DI_CRUD_GET_MUTATION      = "DI-CRD-001"


@dataclass
class InvariantViolation:
    code: InvariantCode
    severity: InvariantSeverity
    pillar: str
    message: str
    detail: Optional[str] = None

    def __repr__(self) -> str:
        return f"[{self.severity.value}] {self.code.value} ({self.pillar}): {self.message}"


@dataclass
class InvariantReport:
    """Resultat complet de l audit d invariants sur un texte ou claim."""
    passed: bool
    violations: List[InvariantViolation] = field(default_factory=list)

    @property
    def blocking_violations(self) -> List[InvariantViolation]:
        return [v for v in self.violations if v.severity == InvariantSeverity.BLOCKING]

    @property
    def warnings(self) -> List[InvariantViolation]:
        return [v for v in self.violations if v.severity == InvariantSeverity.WARNING]

    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "blocking_count": len(self.blocking_violations),
            "warning_count": len(self.warnings),
            "violations": [
                {
                    "code": v.code.value,
                    "severity": v.severity.value,
                    "pillar": v.pillar,
                    "message": v.message,
                    "detail": v.detail,
                }
                for v in self.violations
            ],
        }


# ─── P1 : Modalites negatives / positives ─────────────────────────────────────

_NEGATIVE_MODALS: List[str] = [
    r"ne\s+doit\s+pas", r"ne\s+peut\s+pas", r"ne\s+sont?\s+pas",
    r"interdit[e]?", r"d[eé]fendu[e]?", r"prohib[eé][e]?", r"bloqu[eé][e]?",
    r"rejet[eé][e]?", r"exclu[e]?", r"impossible", r"aucun[e]?",
    r"jamais", r"sans\s+exception", r"lecture\s+seule", r"non\s+modifiable",
    r"immutable", r"read[- ]only", r"strictly\s+forbidden", r"must\s+not",
    r"shall\s+not", r"cannot", r"must never",
]

_POSITIVE_MODALS: List[str] = [
    r"peut\b", r"autoris[eé][e]?", r"permis[e]?", r"doit\b", r"obligatoire",
    r"requis[e]?", r"necessary", r"allowed", r"may\b", r"must\b",
    r"is\s+required", r"est\s+requis", r"can\b", r"should\b",
]

_RE_NEGATIVE = re.compile(r"(?:" + "|".join(_NEGATIVE_MODALS) + r")", re.IGNORECASE)
_RE_POSITIVE = re.compile(r"(?:" + "|".join(_POSITIVE_MODALS) + r")", re.IGNORECASE)


def _detect_polarity(text: str) -> str:
    """Retourne NEGATIVE, POSITIVE ou NEUTRAL."""
    has_neg = bool(_RE_NEGATIVE.search(text))
    has_pos = bool(_RE_POSITIVE.search(text))
    if has_neg and not has_pos:
        return "NEGATIVE"
    if has_pos and not has_neg:
        return "POSITIVE"
    return "NEUTRAL"


# ─── P2 : Bornes physiques SIGPA ──────────────────────────────────────────────

_TEMP_MIN_F = 95.0    # Limite basse absolue en Fahrenheit (SIGPA)
_TEMP_MAX_F = 105.0   # Limite haute absolue en Fahrenheit (SIGPA)
_BUGGY_EGGS_MAX = 6000

_RE_TEMP_CONTEXT = re.compile(
    r'(?:temp(?:[eé]rature)?|temperature)(?:\s+\w+){0,6}\s+(?:de\s+|=\s*|:\s*)?(\d+(?:\.\d+)?)\s*[°]?([FC])\b'
    r'|(\d+(?:\.\d+)?)\s*°([FC])\b',
    re.IGNORECASE
)
_RE_EGG_COUNT = re.compile(r'(\d[\d\s]*)\s*(?:oeufs?|eggs?)', re.IGNORECASE)
_RE_SLOT = re.compile(r'\bslot[_\s#-]*(\d+)\b', re.IGNORECASE)
_RE_STATUS = re.compile(
    r'\b(PLANIFIE|EN_COURS|TRANSFERE_ECLOSOIR|TERMINE|ANNULE|'
    r'EN_INCUBATION|DESINFECTE|DISPONIBLE|AU_REBUT)\b'
)

_MUTEX_STATE_GROUPS: List[List[str]] = [
    ["PLANIFIE", "EN_COURS", "TRANSFERE_ECLOSOIR", "TERMINE", "ANNULE"],
    ["EN_INCUBATION", "DESINFECTE", "DISPONIBLE", "AU_REBUT"],
]

# Sequence causale des etapes d incubation (ordre physique obligatoire)
INCUBATION_STAGE_ORDER: List[Tuple[str, str]] = [
    ("ponte",        r'\b(?:ponte|pondu[e]?|pondus|lay(?:ing)?)\b'),
    ("reception",    r'\b(?:r[eé]ception|re[cg]u[e]?|livr[eé][e]?|received)\b'),
    ("desinfection", r'\b(?:d[eé]sinfect(?:ion|[eé][e]?)|disinfect(?:ion|ed?)?)\b'),
    ("chambre_oeuf", r'\b(?:chambre\s+(?:[aà]\s+)?oeuf|salle\s+(?:[aà]\s+)?oeuf|egg\s+room)\b'),
    ("prechauffage", r'\b(?:pr[eé]chauffage|pre[\-_]?heat(?:ing)?)\b'),
    ("incubation",   r'\b(?:incub(?:ation|ateur|ated?)|setter|mis\s+en\s+incubation)\b'),
    ("mirage",       r'\b(?:mirage|candl(?:ing|ed?)|miroir)\b'),
    ("transfert",    r'\b(?:transfert?|transf[eé]r[eé]|transfer(?:red)?|vaccination\s+in[\-_]?ovo)\b'),
    ("eclosion",     r'\b(?:[eé]clo(?:sion|soir)|hatch(?:er|ed?|ing)?)\b'),
]

_STAGE_PATTERNS = [
    (name, re.compile(pattern, re.IGNORECASE))
    for name, pattern in INCUBATION_STAGE_ORDER
]


# ─── P3 : Intention CRUD ──────────────────────────────────────────────────────

_RE_GET_INDICATOR = re.compile(
    r'\b(GET\b|consultations?|consulter|afficher|lister|visualiser|'
    r'lire\b|read[\-\s]?only|lecture\s+seule|read only)\b',
    re.IGNORECASE
)
_RE_MUTATION_INDICATOR = re.compile(
    r'\b(supprim(?:er|[eé][e]?)|effac(?:er|[eé][e]?)|modifi(?:er|[eé][e]?|cation)|'
    r'mis(?:e)?\s+[aà]\s+jour|updat(?:e|ed?|ing)|delet(?:e|ed?|ing)|'
    r'archiv(?:er|[eé][e]?)|cr[eé](?:er|[eé][e]?)|insert(?:er|ed?|ion)?|'
    r'sauvegard(?:er|[eé][e]?)|enregistr(?:er|[eé][e]?)|persist(?:er|[eé][e]?)|'
    r'POST\b|PUT\b|PATCH\b|DELETE\b)\b',
    re.IGNORECASE
)


# ─── DomainInvariantChecker ───────────────────────────────────────────────────

class DomainInvariantChecker:
    """
    Moteur de verification d invariants de domaine. Zero LLM.

    Usage:
        report = DomainInvariantChecker.check_claim(claim_text, ssot_snippet)
        report = DomainInvariantChecker.check_story_text(full_story_markdown)
    """

    @classmethod
    def check_polarity_conflict(
        cls, claim_text: str, ssot_snippet: str
    ) -> Optional[InvariantViolation]:
        """Detecte une inversion de polarite entre le claim et le snippet source."""
        claim_polarity = _detect_polarity(claim_text)
        ssot_polarity  = _detect_polarity(ssot_snippet)

        if ssot_polarity == "NEGATIVE" and claim_polarity == "POSITIVE":
            return InvariantViolation(
                code=InvariantCode.DI_POL_NEGATION_INVERSION,
                severity=InvariantSeverity.BLOCKING,
                pillar="P1",
                message=(
                    "Le SSOT exprime une interdiction ou restriction, "
                    "mais le claim affirme une permission ou obligation positive. "
                    "Inversion de polarite deontique."
                ),
                detail=(
                    f"SSOT polarity=NEGATIVE | Claim polarity=POSITIVE\n"
                    f"SSOT: <<{ssot_snippet[:120]}>>\n"
                    f"Claim: <<{claim_text[:120]}>>"
                ),
            )

        if ssot_polarity == "POSITIVE" and claim_polarity == "NEGATIVE":
            return InvariantViolation(
                code=InvariantCode.DI_POL_PERMISSION_DENIED,
                severity=InvariantSeverity.BLOCKING,
                pillar="P1",
                message=(
                    "Le SSOT autorise ou exige un comportement, "
                    "mais le claim l interdire ou le bloque. "
                    "Inversion de polarite deontique."
                ),
                detail=(
                    f"SSOT polarity=POSITIVE | Claim polarity=NEGATIVE\n"
                    f"SSOT: <<{ssot_snippet[:120]}>>\n"
                    f"Claim: <<{claim_text[:120]}>>"
                ),
            )

        return None

    @classmethod
    def check_temperature(cls, text: str) -> List[InvariantViolation]:
        """Detecte les temperatures aberrantes. Plage SIGPA : 95-105 F.

        Le regex _RE_TEMP_CONTEXT possede 4 groupes (2 alternatives) :
        - Alt 1 : mot 'temperature' ... valeur (group 1) + unite F/C (group 2)
        - Alt 2 : valeur (group 3) + unite F/C apres le degre (group 4)
        """
        violations: List[InvariantViolation] = []
        for m in _RE_TEMP_CONTEXT.finditer(text):
            try:
                # Choisir la bonne alternative
                if m.group(1):
                    val = float(m.group(1))
                    unit = (m.group(2) or "").upper()
                elif m.group(3):
                    val = float(m.group(3))
                    unit = (m.group(4) or "").upper()
                else:
                    continue
            except (ValueError, IndexError, TypeError):
                continue
            val_f = (val * 9 / 5 + 32) if unit == "C" else val
            if not (_TEMP_MIN_F <= val_f <= _TEMP_MAX_F):
                violations.append(InvariantViolation(
                    code=InvariantCode.DI_PHY_TEMP_OUT_OF_RANGE,
                    severity=InvariantSeverity.BLOCKING,
                    pillar="P2",
                    message=(
                        f"Temperature {val}{unit or 'F'} hors plage physique "
                        f"d incubation ({_TEMP_MIN_F}-{_TEMP_MAX_F} F)."
                    ),
                    detail=f"Valeur extraite : {val} -> {val_f:.1f} F",
                ))
        return violations


    @classmethod
    def check_egg_capacity(cls, text: str) -> List[InvariantViolation]:
        """Detecte les quantites d oeufs impossibles pour un buggy."""
        violations: List[InvariantViolation] = []
        for m in _RE_EGG_COUNT.finditer(text):
            raw = m.group(1).replace(" ", "")
            try:
                count = int(raw)
            except ValueError:
                continue
            if count > _BUGGY_EGGS_MAX:
                violations.append(InvariantViolation(
                    code=InvariantCode.DI_PHY_CAPACITY_EXCEEDED,
                    severity=InvariantSeverity.BLOCKING,
                    pillar="P2",
                    message=(
                        f"Quantite de {count:,} oeufs depasse la capacite physique "
                        f"maximale d un buggy ({_BUGGY_EGGS_MAX:,} oeufs)."
                    ),
                    detail=f"Extrait : <<{m.group(0)}>>",
                ))
        return violations

    @classmethod
    def check_slot_number(cls, text: str) -> List[InvariantViolation]:
        """Detecte les numeros de slot manifestement aberrants (< 1 ou > 99)."""
        violations: List[InvariantViolation] = []
        for m in _RE_SLOT.finditer(text):
            try:
                slot = int(m.group(1))
            except ValueError:
                continue
            if slot < 1 or slot > 99:
                violations.append(InvariantViolation(
                    code=InvariantCode.DI_PHY_SLOT_OUT_OF_RANGE,
                    severity=InvariantSeverity.BLOCKING,
                    pillar="P2",
                    message=f"Numero de slot {slot} hors plage valide (1-99).",
                    detail=f"Extrait : <<{m.group(0)}>>",
                ))
        return violations

    @classmethod
    def check_mutual_exclusion(cls, text: str) -> List[InvariantViolation]:
        """Detecte la co-occurrence de statuts mutuellement exclusifs."""
        violations: List[InvariantViolation] = []
        # Normaliser les accents pour la detection
        normalized = text.upper().replace("\u00c9", "E").replace("\u00e9", "E")
        found_statuses = set(_RE_STATUS.findall(normalized))

        for group in _MUTEX_STATE_GROUPS:
            present = [s for s in group if s in found_statuses]
            if len(present) >= 2:
                violations.append(InvariantViolation(
                    code=InvariantCode.DI_STATE_MUTUAL_EXCLUSION,
                    severity=InvariantSeverity.BLOCKING,
                    pillar="P2",
                    message=(
                        f"Etats mutuellement exclusifs co-presents : "
                        f"{' et '.join(present)}. Un lot/batch ne peut etre dans "
                        f"deux etats simultanement."
                    ),
                    detail=f"Groupe d exclusion : {group}",
                ))
        return violations

    @classmethod
    def check_stage_causal_order(cls, text: str) -> List[InvariantViolation]:
        """Detecte les inversions de causalite chronologique dans le pipeline d incubation."""
        violations: List[InvariantViolation] = []

        found_stages: List[Tuple[int, str, int]] = []
        for stage_idx, (stage_name, stage_re) in enumerate(_STAGE_PATTERNS):
            m = stage_re.search(text)
            if m:
                found_stages.append((stage_idx, stage_name, m.start()))

        found_stages.sort(key=lambda x: x[2])  # trier par position dans le texte

        for i in range(len(found_stages) - 1):
            curr_idx, curr_name, _ = found_stages[i]
            next_idx, next_name, _ = found_stages[i + 1]
            if curr_idx > next_idx:
                violations.append(InvariantViolation(
                    code=InvariantCode.DI_TMP_CAUSAL_ORDER,
                    severity=InvariantSeverity.BLOCKING,
                    pillar="P2",
                    message=(
                        f"Inversion de causalite temporelle : <<{next_name}>> "
                        f"(etape {next_idx + 1}) precede <<{curr_name}>> (etape {curr_idx + 1}) "
                        f"alors que l ordre physique est inverse."
                    ),
                    detail="Sequence physique : " + " -> ".join(s[0] for s in INCUBATION_STAGE_ORDER),
                ))
        return violations

    @classmethod
    def check_crud_intention(cls, text: str) -> List[InvariantViolation]:
        """Detecte un effet de bord dans un recit de consultation (GET / lecture seule)."""
        violations: List[InvariantViolation] = []
        is_read_context = bool(_RE_GET_INDICATOR.search(text))
        has_mutation    = bool(_RE_MUTATION_INDICATOR.search(text))

        if is_read_context and has_mutation:
            mutations_found = _RE_MUTATION_INDICATOR.findall(text)
            mutations_str = ", ".join(f"<<{m}>>" for m in mutations_found[:5])
            violations.append(InvariantViolation(
                code=InvariantCode.DI_CRUD_GET_MUTATION,
                severity=InvariantSeverity.WARNING,
                pillar="P3",
                message=(
                    f"Recit de consultation contient des verbes de mutation : {mutations_str}. "
                    f"Violation de la purete d intention (GET with side-effects)."
                ),
                detail=(
                    "Un endpoint GET ne doit avoir aucun effet de bord. "
                    "Si une action est requise, elle doit etre portee par un recit POST/PUT/DELETE."
                ),
            ))
        return violations

    @classmethod
    def check_claim(
        cls,
        claim_text: str,
        ssot_snippet: str = "",
    ) -> InvariantReport:
        """Audit complet d un claim atomique contre son snippet SSOT."""
        violations: List[InvariantViolation] = []

        if ssot_snippet:
            pol = cls.check_polarity_conflict(claim_text, ssot_snippet)
            if pol:
                violations.append(pol)

        violations.extend(cls.check_temperature(claim_text))
        violations.extend(cls.check_egg_capacity(claim_text))
        violations.extend(cls.check_slot_number(claim_text))
        violations.extend(cls.check_mutual_exclusion(claim_text))
        violations.extend(cls.check_stage_causal_order(claim_text))
        violations.extend(cls.check_crud_intention(claim_text))

        return InvariantReport(
            passed=len([v for v in violations if v.severity == InvariantSeverity.BLOCKING]) == 0,
            violations=violations,
        )

    @classmethod
    def check_story_text(cls, story_text: str) -> InvariantReport:
        """Audit complet d un texte de User Story (sans snippet SSOT)."""
        violations: List[InvariantViolation] = []

        violations.extend(cls.check_temperature(story_text))
        violations.extend(cls.check_egg_capacity(story_text))
        violations.extend(cls.check_slot_number(story_text))
        violations.extend(cls.check_mutual_exclusion(story_text))
        violations.extend(cls.check_stage_causal_order(story_text))
        violations.extend(cls.check_crud_intention(story_text))

        return InvariantReport(
            passed=len([v for v in violations if v.severity == InvariantSeverity.BLOCKING]) == 0,
            violations=violations,
        )

