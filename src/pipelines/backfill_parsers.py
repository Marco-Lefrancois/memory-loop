"""
Parseurs purs du backfill retroactif EvidencePack (MLOOP-182-BE).

Extraction 100% structuree, zéro inférence (CA-2) — seuls motifs documentés :
  - fact_dossier : table des faits F-NN (verbatim + ancrage), arbitrages
    « Dx — ... », Admission of Limits.
  - implementation_plan : décisions « Déc. N » / « Décision », contrats
    méthodes HTTP, marqueurs « API à définir ».
  - récit : section « Règles d'affaires » (RM-XXX).

Chaque parseur lève SourceParseError sur structure corrompue (Pilier 3).
"""
from __future__ import annotations

import re
from typing import Any, Dict, List

import yaml

# Ligne de table : | **F-01** | `src:15` | « quote » | fait |
_FROW = re.compile(
    r"^\|\s*\*\*F-\d+\*\*\s*\|\s*`(?P<src>[^`]+)`\s*\|"
    r"\s*(?P<quote>[^|]+?)\s*\|\s*(?P<fait>[^|]+?)\s*\|\s*$"
)
_ORIGIN_LINES = re.compile(r"[:](\d+)(?:-(\d+))?$")
_ARBITRAGE = re.compile(r"^\s*\*\s+(?P<rid>[A-Z]\d+)\s*[—–-]\s*(?P<body>.+)$")
_ADMISSION = re.compile(r"\*\*Admission of Limits\*\*\s*:\s*(.+)$")
_DEC_BULLET = re.compile(
    r"^\s*[-*]\s+(?:\*\*)?(?:D[ée]c(?:ision)?\.?\s*\d+|Décision[^:*]*)"
    r"(?:\*\*)?\s*:\s*(?P<body>.+)$"
)
_HEADING_DEC = re.compile(r"^#{2,4}\s+.*[Dd]écisions?")
_ANY_HEADING = re.compile(r"^(#{1,4})\s+")
_CONTRACT = re.compile(r"\b(?P<m>GET|POST|PUT|PATCH|DELETE)\s+(?P<p>/[\w{}/.:\-]+)")
_TO_DEFINE = re.compile(r"(API de soumission à définir|\[API à définir\])")
_RM_BULLET = re.compile(r"^\s*[-*]\s+\*\*(?P<rm>RM-\d+)\*\*\s*:\s*(?P<body>.+)$")
_RULES_HEADING = re.compile(r"^#{2,6}\s+.*Règles d'affaires")


class SourceParseError(RuntimeError):
    """Structure de source corrompue (frontmatter YAML invalide, format inattendu)."""


def _strip_quotes(text: str) -> str:
    return text.strip().strip("«»").strip().strip('"')


def parse_dossier(text: str, relpath: str) -> Dict[str, Any]:
    """Parse un fact_dossier : citations (table F-NN), arbitrages, admissions."""
    story_id = None
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) < 3:
            raise SourceParseError(f"Frontmatter tronqué : {relpath}")
        try:
            fm = yaml.safe_load(parts[1])
        except yaml.YAMLError as exc:
            raise SourceParseError(f"Frontmatter YAML invalide : {relpath}") from exc
        if isinstance(fm, dict):
            story_id = fm.get("story_id")

    groups: Dict[str, Dict[str, Any]] = {}
    decisions: List[Dict[str, Any]] = []
    admissions: List[str] = []
    in_arbitrage = False

    for lineno, line in enumerate(text.splitlines(), start=1):
        m = _FROW.match(line)
        if m:
            origin = m.group("src")
            base = origin.rsplit(":", 1)[0] if ":" in origin else origin
            g = groups.setdefault(base, {"quotes": [], "facts": [], "rows": []})
            g["quotes"].append(_strip_quotes(m.group("quote")))
            lm = _ORIGIN_LINES.search(origin)
            provenance = (
                f"{origin}" if lm else origin
            )
            g["facts"].append(f"{m.group('fait')} (source d'origine: {provenance})")
            g["rows"].append(lineno)
            continue
        if "Arbitrages retenus" in line:
            in_arbitrage = True
            continue
        if line.startswith("#"):
            in_arbitrage = False
        if in_arbitrage:
            am = _ARBITRAGE.match(line)
            if am:
                decisions.append(
                    {
                        "rationale": f"{am.group('rid')} — {am.group('body').strip()}",
                        "hint": None,
                        "source": relpath,
                        "line": lineno,
                    }
                )
                continue
        adm = _ADMISSION.search(line)
        if adm:
            admissions.append(adm.group(1).strip())

    citations = [
        {
            "source_file": relpath,
            "lines": [min(g["rows"]), max(g["rows"])],
            "quote": "\n".join(g["quotes"]),
            "established_fact": "\n".join(g["facts"]),
        }
        for _, g in sorted(groups.items())
        if g["quotes"] and any(q.strip() for q in g["quotes"])
    ]
    return {
        "story_id": story_id,
        "citations": citations,
        "decisions": decisions,
        "admissions": admissions,
    }


def parse_plan(text: str, relpath: str) -> Dict[str, Any]:
    """Parse un plan d'implémentation : décisions « Déc. N » + contrats HTTP."""
    decisions: List[Dict[str, Any]] = []
    contracts: List[Dict[str, Any]] = []
    seen_rationales = set()
    in_dec_section = False

    for lineno, line in enumerate(text.splitlines(), start=1):
        heading = _ANY_HEADING.match(line)
        if heading:
            in_dec_section = bool(_HEADING_DEC.match(line)) and len(heading.group(1)) >= 2
            if not in_dec_section:
                continue

        dm = _DEC_BULLET.match(line)
        if dm:
            body = dm.group("body").strip()
            if body not in seen_rationales:
                seen_rationales.add(body)
                decisions.append(
                    {"rationale": body, "hint": None, "source": relpath, "line": lineno}
                )
            continue
        if in_dec_section:
            plain = re.match(r"^\s*[-*]\s+(?P<body>[^:]+)$", line)
            if plain:
                body = plain.group("body").strip()
                if body and body not in seen_rationales:
                    seen_rationales.add(body)
                    decisions.append(
                        {"rationale": body, "hint": None, "source": relpath, "line": lineno}
                    )
            continue

        cm = _CONTRACT.search(line)
        if cm:
            contracts.append(
                {
                    "method": cm.group("m"),
                    "path": cm.group("p"),
                    "hint": None,
                    "source": relpath,
                }
            )
            continue
        tm = _TO_DEFINE.search(line)
        if tm:
            contracts.append(
                {"method": "N/A", "path": None, "hint": line.strip(), "source": relpath}
            )

    return {"decisions": decisions, "contracts": contracts}


def parse_story_rules(text: str, relpath: str) -> Dict[str, Any]:
    """Parse la section « Règles d'affaires » d'un récit (RM-XXX). Zéro YAML."""
    body_lines = text.split("---", 2)
    if text.startswith("---") and len(body_lines) >= 3:
        text = body_lines[2]

    decisions: List[Dict[str, Any]] = []
    in_section = False
    section_level = 0

    for lineno, line in enumerate(text.splitlines(), start=1):
        heading = _ANY_HEADING.match(line)
        if heading:
            level = len(heading.group(1))
            if in_section and level <= section_level:
                in_section = False
            if _RULES_HEADING.match(line):
                in_section = True
                section_level = level
            continue
        if not in_section:
            continue
        rm = _RM_BULLET.match(line)
        if rm:
            decisions.append(
                {
                    "rationale": f"{rm.group('rm')} : {rm.group('body').strip()}",
                    "hint": "RM",
                    "source": relpath,
                    "line": lineno,
                }
            )

    return {"decisions": decisions}
