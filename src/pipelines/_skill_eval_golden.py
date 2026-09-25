# -*- coding: utf-8 -*-
"""
_skill_eval_golden.py — Évaluation des cas de test Golden Datasets Système 1.
Conforme ADR-0202 (<= 300 lignes) et ADR-0369 (Python Senior).
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from src.utils.logger import get_logger

logger = get_logger("pipelines.skill_eval.golden")


def resolve_cases_file(
    skill_name: str,
    workspace_root: Path,
    cases_path: Optional[Path | str] = None,
) -> Optional[Path]:
    """Résout le chemin d'accès au fichier cases.json pour une compétence."""
    if cases_path:
        p = Path(cases_path)
        return p if p.exists() else None

    candidates = [
        workspace_root / "Projects" / "mLoop" / "memory" / "evals" / "skills" / skill_name / "cases.json",
        workspace_root / "memory" / "evals" / "skills" / skill_name / "cases.json",
    ]
    for c in candidates:
        if c.exists():
            return c
    return None


def load_golden_cases(cases_path: Optional[Path]) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Charge et valide le format JSON des cas de test Golden Dataset."""
    if not cases_path or not cases_path.exists():
        return None, "Fichier cases.json introuvable ou non spécifié."
    try:
        content = cases_path.read_text(encoding="utf-8")
        data = json.loads(content)
        if not isinstance(data, dict) or "cases" not in data or not isinstance(data["cases"], list):
            return None, f"Format JSON invalide dans {cases_path} : clé 'cases' de type liste requise."
        return data, None
    except Exception as exc:
        return None, f"Erreur de lecture du Golden Dataset {cases_path} : {exc}"


def evaluate_single_case(
    case: Dict[str, Any],
    manifest_content: str,
    skill_name: str,
    metadata: Dict[str, str],
) -> Tuple[bool, List[str]]:
    """Évalue un cas de test unique selon les assertions déterministes Système 1."""
    flaws: List[str] = []
    case_id = case.get("id", "UNKNOWN")
    user_input = case.get("input", "")
    expect_triggered = case.get("expect_triggered")
    expect_static = case.get("expect_static", {})

    # 1. Assertions statiques sur le manifeste
    if isinstance(expect_static, dict):
        content_lower = manifest_content.lower()
        for kw in expect_static.get("keywords_present", []):
            if kw.lower() not in content_lower:
                flaws.append(f"[{case_id}] Mot-clé requis absent du manifeste : '{kw}'.")
        for kw in expect_static.get("keywords_absent", []):
            if kw.lower() in content_lower:
                flaws.append(f"[{case_id}] Mot-clé interdit présent dans le manifeste : '{kw}'.")

    # 2. Détection déterministe Système 1 de déclenchement (Anti-Trigger-Pollution)
    if expect_triggered is not None and user_input:
        normalized_input = user_input.lower()
        skill_slug = skill_name.lower().replace("-", " ")
        name_tokens = [tok for tok in re.split(r"[\s\-_]+", skill_name.lower()) if len(tok) >= 3]

        desc_raw = metadata.get("description", "").lower()
        trigger_phrases = re.findall(
            r"(?:use when|trigger|quand utiliser|utiliser lorsque|déclencher)[\s:]+([^.\n]+)",
            desc_raw,
            re.IGNORECASE,
        )
        trigger_keywords = set()
        for phrase in trigger_phrases:
            for w in re.split(r"[\s,;]+", phrase):
                clean_w = re.sub(r"[^\w\-]", "", w).strip()
                if len(clean_w) >= 4:
                    trigger_keywords.add(clean_w)

        common_tokens = {"code", "test", "file", "data", "text", "tool", "mode", "spec", "pour", "avec", "sans"}
        substantive_tokens = [tok for tok in name_tokens if tok not in common_tokens]
        if substantive_tokens:
            name_tokens_hit = any(t in normalized_input for t in substantive_tokens)
        else:
            name_tokens_hit = all(t in normalized_input for t in name_tokens)

        direct_hit = skill_name.lower() in normalized_input or skill_slug in normalized_input
        trigger_hit = any(tk in normalized_input for tk in trigger_keywords)

        is_detected = direct_hit or (name_tokens_hit and trigger_hit)

        if expect_triggered and not is_detected:
            flaws.append(
                f"[{case_id}] Déclenchement attendu non détecté pour l'entrée : '{user_input[:80]}'."
            )
        elif not expect_triggered and is_detected:
            flaws.append(
                f"[{case_id}] Suractivation indue (trigger pollution) détectée pour : '{user_input[:80]}'."
            )

    return len(flaws) == 0, flaws


def evaluate_golden_dataset(
    skill_name: str,
    manifest_content: str,
    metadata: Dict[str, str],
    cases_path: Optional[Path],
    is_heavy_meta: bool = False,
) -> Tuple[Optional[float], Dict[str, Any], List[str], List[str]]:
    """
    Évalue une compétence contre son Golden Dataset.
    Retourne (score_float_or_None, breakdown_dict, flaws_list, recs_list).
    """
    if is_heavy_meta:
        return (
            None,
            {"status": "EXCLUDED", "reason": "HEAVY_META_SKILL (statique seule)"},
            [],
            [],
        )

    dataset_data, error_msg = load_golden_cases(cases_path)
    if not dataset_data:
        recs = [f"Configurer un Golden Dataset pour '{skill_name}' : {error_msg}"]
        breakdown = {
            "cases_file": str(cases_path) if cases_path else None,
            "total_cases": 0,
            "passed_cases": 0,
            "score": 0.0,
            "status": "MISSING_OR_INVALID",
        }
        return 0.0, breakdown, [], recs

    cases = dataset_data.get("cases", [])
    if not cases:
        return (
            0.0,
            {"cases_file": str(cases_path), "total_cases": 0, "passed_cases": 0, "score": 0.0, "status": "EMPTY"},
            [],
            [f"Le Golden Dataset pour '{skill_name}' ne contient aucun cas de test."],
        )

    passed_count = 0
    all_flaws: List[str] = []
    case_results: List[Dict[str, Any]] = []

    for c in cases:
        case_passed, case_flaws = evaluate_single_case(c, manifest_content, skill_name, metadata)
        if case_passed:
            passed_count += 1
        else:
            all_flaws.extend(case_flaws)
        case_results.append({
            "id": c.get("id"),
            "type": c.get("type", "nominal"),
            "passed": case_passed,
            "flaws": case_flaws,
        })

    score = round((passed_count / len(cases)) * 100.0, 1)
    breakdown = {
        "cases_file": str(cases_path),
        "total_cases": len(cases),
        "passed_cases": passed_count,
        "score": score,
        "status": "PASS" if score >= 80.0 else ("WARNING" if score >= 65.0 else "FAIL"),
        "cases_detail": case_results,
    }

    recs: List[str] = []
    if score < 80.0:
        recs.append(f"Améliorer la conformité Golden Dataset ({passed_count}/{len(cases)} cas réussis, score: {score}/100).")

    return score, breakdown, all_flaws, recs
