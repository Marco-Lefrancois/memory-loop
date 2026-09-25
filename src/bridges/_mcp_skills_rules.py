"""
src/bridges/_mcp_skills_rules.py — Hiérarchie stricte & arbitrage des conflits (MLOOP-214-BE).

SSOT de la règle d'affaires « Hiérarchie stricte et non négociable » du récit
([`Projects/mLoop/backlog/stories/MLOOP-214-BE.md`](file:///C:/Memory%20Loop/Projects/mLoop/backlog/stories/MLOOP-214-BE.md)) :

1. **règle permanente** — tout fichier ``.agents/rules/*.md`` (règle 214-Q1 de
   l'ADR-009 : un garde-fou ne peut jamais être abrogé par une compétence) ;
2. **compétence chargée** — contenu d'une ``SKILL.md`` du catalogue local ;
3. **contenu historique** — ``AGENTS.md``, le fichier de règles principales.

Le module **ne modifie jamais** le contenu servi (le récit exige le contenu
exact de la compétence) : il constate le conflit, le journalise en DEBUG
structuré et retourne le verdict ``permanent_rule_wins`` que le pont attache à
``_meta.mloop``. Détection déterministe et ligne à ligne : une ligne est un
conflit si elle (a) nomme une règle permanente (fichier, souche ou vocabulaire
de garde-fou) **et** (b) affirme son abrogation, sans négation en vis-à-
direct.

Garanties ADR-0369 : aucune exception n'est engloutie — chaque lecture
échouée est journalisée avec ``exc_info=True`` avant d'être propagée ou
convertie en refus explicite.
"""

from __future__ import annotations

import logging
import re
import unicodedata
from dataclasses import asdict, dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

logger = logging.getLogger(__name__)

# ── Hiérarchie publiée (ordre d'autorité décroissante) ─────────────────────────
HIERARCHY: tuple[str, ...] = ("permanent_rule", "loaded_skill", "main_rules_file")
RULES_DIR = Path(".agents/rules")
MAIN_RULES_FILE = Path("AGENTS.md")
RESOLUTION = "permanent_rule_wins"
# Références non nominatives : la règle en cause est le répertoire tout entier.
UNNAMED_RULE = "règle permanente non nommée (.agents/rules/*.md)"

# Bornes de détection (un conflit = un journal, jamais un raz-de-marée).
MAX_CONFLICTS_PER_SKILL = 20
EXCERPT_LIMIT = 200

# Vocabulaire d'abrogation — normalisé (casse + accents + apostrophes retirés).
_ABROGATION_MARKERS: tuple[str, ...] = (
    "abrog",
    "ignore la regle",
    "ignorer la regle",
    "ignore les regles",
    "ignorer les regles",
    "ignore cette regle",
    "ignorer cette regle",
    "ne s'applique pas",
    "ne s applique pas",
    "contourne la regle",
    "contourner la regle",
    "contourne les regles",
    "contourner les regles",
    "outrepass",
    "outrepasse",
    "deroge",
    "leve l'interdiction",
    "lever l'interdiction",
    "leve l interdiction",
    "remplace la regle",
    "remplace cette regle",
    "remplace les regles",
    "prime sur la regle",
    "prime sur les regles",
    "override la regle",
    "override des regles",
    "bypass la regle",
    "bypass des regles",
    "sans appliquer la regle",
    "sans tenir compte de la regle",
    "hors du controle des regles",
    "habilite a ignorer la regle",
)

# Négations : la ligne énonce l'inverse d'une abrogation → aucun conflit.
_NEGATION_MARKERS: tuple[str, ...] = (
    "ne deroge pas",
    "ne deroge en rien",
    "ne prime pas",
    "ne remplace pas",
    "ne contourne pas",
    "n'ignore pas",
    "ne peut ignorer",
    "ne peut abroger",
    "ne peut pas abroger",
    "ne peut contourner",
    "ne contredit pas",
    "ne s'applique pas a l'inverse",
)

# Vocabulaire de référence quand aucun fichier n'est nommé.
_REFERENCE_MARKERS: tuple[str, ...] = (
    ".agents/rules",
    "regle permanente",
    "regles permanentes",
    "regle(s) permanente(s)",
    "regles always-on",
    "always-on",
    "garde-fou",
    "garde-fous",
    "fichier de regles principales",
)


@dataclass(frozen=True)
class RuleConflict:
    """Conflit constaté entre une compétence et une règle permanente."""

    skill: str
    rule: str
    excerpt: str
    line: int
    resolution: str = RESOLUTION

    def as_dict(self) -> dict[str, Any]:
        """Représentation JSON du verdict (attachée à ``_meta.mloop``)."""
        return asdict(self)


def _normalize(text: str) -> str:
    """Casse minuscule, apostrophes droites et accents retirés (marqueurs ASCII)."""
    lowered = text.lower().replace("\u2019", "'").replace("\u2018", "'")
    decomposed = unicodedata.normalize("NFD", lowered)
    return "".join(char for char in decomposed if unicodedata.category(char) != "Mn")


@lru_cache(maxsize=64)
def _stem_pattern(stem: str) -> re.Pattern[str]:
    """Mot entier ``stem`` (souche de fichier de règle) dans une ligne normalisée."""
    return re.compile(rf"(?<![a-z0-9]){re.escape(stem)}(?![a-z0-9])")


def load_permanent_rules(rules_dir: Path | str | None = None) -> dict[str, Path]:
    """Répertoire canonique des règles permanentes : tout ``*.md`` y est permanent."""
    directory = Path(rules_dir) if rules_dir else RULES_DIR
    if not directory.is_dir():
        logger.debug(
            "permanent_rules_directory_absent",
            extra={
                "component": "bridges.mcp_skills",
                "operation": "load_permanent_rules",
                "directory": str(directory),
            },
        )
        return {}
    return {path.name: path for path in sorted(directory.glob("*.md"))}


def _rule_in_charge(normalized: str, rules: Mapping[str, Path]) -> str | None:
    """Règle permanente visée par la ligne, ou ``None`` si la ligne n'en vise aucune."""
    for filename in rules:
        stem = Path(filename).stem
        if filename in normalized or f"{stem}.md" in normalized:
            return filename
        if len(stem) >= 6 and _stem_pattern(stem).search(normalized):
            return filename
    if any(marker in normalized for marker in _REFERENCE_MARKERS):
        return UNNAMED_RULE
    return None


def find_conflicts(
    skill_name: str,
    content: str,
    rules_dir: Path | str | None = None,
) -> list[RuleConflict]:
    """Détecte les lignes d'une compétence qui prétendent abroger une règle permanente.

    Retourne ``[]`` quand le répertoire de règles est absent ou sans conflit :
    l'absence de règle permanente n'est jamais un silence masqué.
    """
    rules = load_permanent_rules(rules_dir)
    if not rules or not content:
        return []
    conflicts: list[RuleConflict] = []
    for line_no, raw in enumerate(content.splitlines(), start=1):
        normalized = _normalize(raw)
        if not any(marker in normalized for marker in _ABROGATION_MARKERS):
            continue
        if any(marker in normalized for marker in _NEGATION_MARKERS):
            continue
        rule = _rule_in_charge(normalized, rules)
        if rule is None:
            continue
        conflicts.append(
            RuleConflict(
                skill=skill_name,
                rule=rule,
                excerpt=raw.strip()[:EXCERPT_LIMIT],
                line=line_no,
            )
        )
        if len(conflicts) >= MAX_CONFLICTS_PER_SKILL:
            break
    return conflicts


def log_conflicts(conflicts: Sequence[RuleConflict], *, bridge: str) -> None:
    """Émet un journal structuré **par conflit** (niveau debug, jamais silencieux)."""
    for conflict in conflicts:
        logger.debug(
            "skill_rule_conflict",
            extra={
                "component": "bridges.mcp_skills",
                "operation": "arbitrate_skill",
                "event": "skill_rule_conflict",
                "bridge": bridge,
                "skill": conflict.skill,
                "rule": conflict.rule,
                "line": conflict.line,
                "excerpt": conflict.excerpt,
                "resolution": conflict.resolution,
                "hierarchy": list(HIERARCHY),
            },
        )


def arbitrate_skill(
    skill_name: str,
    content: str,
    *,
    bridge: str,
    rules_dir: Path | str | None = None,
    log: bool = True,
) -> list[RuleConflict]:
    """Constate, journalise et retourne le verdict d'arbitrage d'une compétence.

    La compétence reste servie intégralement (ses parties non conflictuelles
    demeurent utilisables) ; seule l'autorité est tranchée, jamais le contenu.
    """
    conflicts = find_conflicts(skill_name, content, rules_dir=rules_dir)
    if conflicts and log:
        log_conflicts(conflicts, bridge=bridge)
    return conflicts


def conflicts_as_dicts(conflicts: Sequence[RuleConflict]) -> list[dict[str, Any]]:
    """Verdicts serialisables pour ``_meta.mloop.ruleConflicts``."""
    return [conflict.as_dict() for conflict in conflicts]
