"""
Fusion des candidats de backfill dans l'EvidencePack (MLOOP-182-BE).

Dédoublonnage par hash (CA-3), granularité hybride D (CA-5 : 1 citation par
fichier source + 1 par décision extraite), recalcul richness_penalty (CA-6,
miroir Déc.5), écriture atomique uniquement si delta non nul, OQ-XXX pour tout
contrat à définir (Zéro Fausse Route).
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.core.decision_recorder import CONTRACT_TO_DEFINE

_RICHNESS_REF = 10  # miroir de extract_evidence (Déc.5, evidence_pack.py)

_CATEGORY_KEYWORDS = (
    ("security", r"sécurit|security|auth|rgpd|loi\s*25"),
    ("performance", r"performan|latence|cache|turbo"),
    ("testing", r"\btest|tdd|pytest"),
    ("refactoring", r"refactor"),
    ("tooling", r"outil|\bcli\b|\bscript\b|commande"),
    ("pattern", r"pattern|motif|structure"),
    ("architecture", r"architecture|composant|module|découpage|protocole|fichier autonome"),
)


def map_category(rationale: str, hint: Optional[str]) -> str:
    """Mappe une rationale extraite vers la liste fermée (miroir DecisionRecorder)."""
    if hint == "RM":
        return "pattern"
    text = rationale.lower()
    for category, pattern in _CATEGORY_KEYWORDS:
        if re.search(pattern, text):
            return category
    return "architecture"


def decision_id(category: str, rationale: str) -> str:
    """Même formule que DecisionRecorder._decision_hash (dédoublonnage partagé)."""
    raw = f"{category}::{rationale.strip()}"
    return f"DEC-{hashlib.sha256(raw.encode('utf-8')).hexdigest()[:16]}"


def richness_penalty(citations: int, decisions: int, contracts: int,
                     prev_score: float) -> Dict[str, Any]:
    """Recalcul Déc.5 — miroir strict de extract_evidence (0.7 + 0.3*min(1, r/10))."""
    richness = citations + decisions + contracts
    multiplier = round(0.7 + 0.3 * min(1.0, richness / _RICHNESS_REF), 4)
    reason = (
        "no_citations"
        if richness == 0
        else f"partial_richness ({richness}/{_RICHNESS_REF})"
        if richness < _RICHNESS_REF
        else "full_richness"
    )
    return {
        "richness": richness,
        "multiplier": multiplier,
        "score": prev_score,
        "reason": reason,
    }


def atomic_write_json(path: Path, data: Dict[str, Any]) -> None:
    """Écriture atomique (Pilier 3) : tmp + os.replace, zéro pack partiel."""
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, path)


def write_open_question(project_path: Path, sid: str, contract_src: Dict[str, Any]) -> None:
    """Consigne une OQ-XXX pour un contrat à définir (Zéro Fausse Route, CA-2)."""
    oq_dir = Path(project_path) / "docs" / "04-transverse"
    oq_dir.mkdir(parents=True, exist_ok=True)
    max_num = 0
    for candidate in oq_dir.glob("OQ-*.md"):
        m = re.match(r"OQ-(\d+)", candidate.name)
        if m:
            max_num = max(max_num, int(m.group(1)))
    oq_path = oq_dir / f"OQ-{max_num + 1:03d}.md"
    oq_path.write_text(
        "# Open Question — Contrat API à définir (backfill)\n\n"
        f"- **Origine** : backfill {sid} (MLOOP-182-BE)\n"
        f"- **Besoin** : {contract_src.get('hint') or contract_src.get('source')}\n"
        f"- **Route** : {CONTRACT_TO_DEFINE}\n"
        "- **Statut** : OUVERTE — aucune URI inventée (Zéro Fausse Route)\n",
        encoding="utf-8",
    )


def merge_and_maybe_write(
    project_path: Path,
    sid: str,
    pack: Dict[str, Any],
    pack_path: Path,
    cand_decisions: List[Dict[str, Any]],
    cand_citations: List[Dict[str, Any]],
    cand_contracts: List[Dict[str, Any]],
    admissions: List[str],
    dry_run: bool,
) -> Optional[int]:
    """Fusionne (dédoublonnage par hash) et n'écrit QUE si le delta est non nul."""
    now = datetime.now(timezone.utc).isoformat()
    audit = pack.setdefault("epistemic_audit", {})
    existing_decisions = pack.setdefault("implementation_decisions", [])
    existing_citations = pack.setdefault("verbatim_extracts", [])
    existing_contracts = pack.setdefault("declarative_contracts", [])
    proves = audit.setdefault("what_it_does_not_prove", [])

    known_ids = {d.get("decision_id") for d in existing_decisions}
    known_cits = {json.dumps(c, sort_keys=True, ensure_ascii=False)
                  for c in existing_citations}
    known_contracts = {(c.get("method"), c.get("path")) for c in existing_contracts}

    added_decisions = 0
    for item in cand_decisions:
        category = map_category(item["rationale"], item["hint"])
        decision = {
            "decision_id": decision_id(category, item["rationale"]),
            "category": category,
            "rationale": (
                f"{item['rationale']} (source: {item['source']}:{item['line']})"
            ),
            "alternatives_considered": [],
            "timestamp": now,
        }
        if decision["decision_id"] in known_ids:
            continue
        known_ids.add(decision["decision_id"])
        existing_decisions.append(decision)
        added_decisions += 1

    # Granularité hybride D (CA-5) : 1 citation/fichier source + 1/décision.
    decision_citations = [
        {
            "source_file": item["source"],
            "lines": [item["line"], item["line"]],
            "quote": item["rationale"],
            "established_fact": (
                "Décision extraite verbatim par le backfill MLOOP-182-BE "
                f"({item['source']}:{item['line']})."
            ),
        }
        for item in cand_decisions
    ]
    added_citations = 0
    for citation in cand_citations + decision_citations:
        key = json.dumps(citation, sort_keys=True, ensure_ascii=False)
        if key in known_cits:
            continue
        known_cits.add(key)
        existing_citations.append(citation)
        added_citations += 1

    added_contracts = 0
    for contract_src in cand_contracts:
        key = (contract_src["method"], contract_src["path"])
        if key in known_contracts:
            continue
        known_contracts.add(key)
        if contract_src["path"] is None:
            existing_contracts.append(
                {
                    "method": "N/A",
                    "path": CONTRACT_TO_DEFINE,
                    "status": "to_define",
                    "source": contract_src["source"],
                }
            )
            if not dry_run:
                write_open_question(project_path, sid, contract_src)
        else:
            existing_contracts.append(
                {
                    "method": contract_src["method"],
                    "path": contract_src["path"],
                    "status": "defined",
                    "source": contract_src["source"],
                }
            )
        added_contracts += 1

    added_admissions = 0
    for admission in admissions:
        if admission not in proves:
            proves.append(admission)
            added_admissions += 1

    changed = bool(
        added_decisions or added_citations or added_contracts or added_admissions
    )
    if not changed:
        return None

    # CA-6 : richness_penalty recalculé (Déc.5) après injection.
    prev_penalty = audit.get("richness_penalty") or {}
    audit["richness_penalty"] = richness_penalty(
        citations=len(existing_citations),
        decisions=len(existing_decisions),
        contracts=len(existing_contracts),
        prev_score=float(prev_penalty.get("score", 0.0)),
    )
    pack["timestamp"] = now
    if not dry_run:
        atomic_write_json(pack_path, pack)
    return added_citations
