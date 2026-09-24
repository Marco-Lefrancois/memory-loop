# -*- coding: utf-8 -*-
"""
Auto Eval Harvester Engine (mLoop Core - ADR-0326).

Standardisé selon le modèle Google Agents CLI Eval & Harness Engineering :
Moissonne automatiquement les anomalies et rejets de Sentinel (Rubber Duck / WikiFix)
et les convertit en cas d'évaluation (EvalTestCase) hybrides (déterministes + sémantiques)
pour tester la non-régression continue.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional


@dataclass
class EvalTestCase:
    """
    Cas de test d'évaluation unifié (Google Agents CLI Eval + mLoop Sentinel).
    Supporte les assertions déterministes Système 1 et la notation LLM-as-a-judge Système 2.
    """
    eval_id: str
    target_file: str
    category: str
    issue_description: str
    expected_rule: str
    severity: str  # "BLOCKING", "WARNING"
    discovered_at: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    description: str = ""
    inputs: Dict[str, Any] = field(default_factory=dict)
    ground_truth_facts: Dict[str, Any] = field(default_factory=dict)
    deterministic_assertions: Dict[str, Any] = field(default_factory=dict)
    evaluator_config: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.description:
            self.description = self.issue_description or f"Audit de {self.target_file}"
        if not self.inputs:
            self.inputs = {
                "story_artifact_path": self.target_file,
                "context_requirements": [self.issue_description] if self.issue_description else [],
            }
        if not self.ground_truth_facts:
            self.ground_truth_facts = {
                "official_endpoints": [],
                "strictly_forbidden_endpoints": ["/api/dummy", "/api/test", "/api/checkout/pay"],
                "mandatory_business_rules": [],
            }
        if not self.deterministic_assertions:
            self.deterministic_assertions = {
                "max_file_lines": 300,
                "frontmatter_required_keys": ["id", "jira_key", "epic_key", "layer", "status", "invest_score"],
                "gherkin_pillars_present": ["Nominal", "Exceptions", "Résilience", "UX"],
                "zero_code_snippets": True,
                "zero_local_hardcoded_paths": True,
            }
        if not self.evaluator_config:
            self.evaluator_config = {
                "judge_model": "claude-sonnet-4-6",
                "temperature": 0.0,
                "pass_threshold_score": 85,
            }

    @property
    def test_case_id(self) -> str:
        return self.eval_id

    def to_dict(self) -> Dict[str, Any]:
        """Sérialisation bivalente (compatible rétro mLoop et Google Agents CLI Eval)."""
        return {
            # Clés canoniques Google Agents CLI Eval
            "test_case_id": self.eval_id,
            "category": self.category,
            "description": self.description,
            "inputs": self.inputs,
            "ground_truth_facts": self.ground_truth_facts,
            "deterministic_assertions": self.deterministic_assertions,
            "evaluator_config": self.evaluator_config,
            # Clés de compatibilité mLoop historique
            "eval_id": self.eval_id,
            "target_file": self.target_file,
            "issue_description": self.issue_description,
            "expected_rule": self.expected_rule,
            "severity": self.severity,
            "discovered_at": self.discovered_at,
            "metadata": self.metadata,
        }


class AutoEvalHarvester:
    """Moteur de récolte et de synthèse des cas d'évaluation."""

    def __init__(self, project_path: Path | str) -> None:
        self.project_path = Path(project_path)
        self.evals_dir = self.project_path / "memory" / "evals"
        self.evals_dir.mkdir(parents=True, exist_ok=True)

    def harvest_from_wikifix(self, wikifix_report_path: Optional[Path | str] = None) -> List[EvalTestCase]:
        """Extrait les cas d'évaluation depuis le rapport WikiFix."""
        report_file = Path(wikifix_report_path) if wikifix_report_path else (self.project_path / "memory" / "wikifix_report.md")
        if not report_file.exists():
            alt = Path("memory") / "wikifix_report.md"
            if alt.exists():
                report_file = alt
            else:
                return []

        content = report_file.read_text(encoding="utf-8")
        return self.harvest_from_markdown(content, source="wikifix")

    def harvest_from_markdown(self, markdown_text: str, source: str = "sentinel") -> List[EvalTestCase]:
        """Parse un rapport d'audit Markdown pour en extraire les cas de test."""
        evals: List[EvalTestCase] = []
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        counter = 1

        lines = markdown_text.splitlines()
        current_file = "unknown"

        for line in lines:
            stripped = line.strip()

            # Format 1 : Section "### Fichier : `path`"
            file_match = re.search(r"###?\s+(?:Fichier|Story|Audit)\s*:\s*`?([^`\n]+)`?", stripped, re.IGNORECASE)
            if file_match:
                current_file = file_match.group(1).strip()
                continue

            # Format 2 : Ligne WikiFix standard "- **Fichier** : [path](link) (Type: description)"
            wikifix_line_match = re.search(r"^-\s+\*\*Fichier\*\*\s*:\s*\[([^\]]+)\]\([^)]+\)\s*\((?:Manquant|Terme|Erreur)\s*:\s*`?([^`\)]+)`?\)", stripped)
            if wikifix_line_match:
                f_path = wikifix_line_match.group(1).strip()
                desc = wikifix_line_match.group(2).strip()
                
                category = "blueprint_drift"
                desc_lower = desc.lower()
                if "invest" in desc_lower:
                    category = "invest_criteria"
                elif "gherkin" in desc_lower or "pilier" in desc_lower:
                    category = "gherkin_4_pillars"
                elif "fuite" in desc_lower or "tech" in desc_lower or "parenthèse" in desc_lower:
                    category = "technical_leak"

                eval_case = EvalTestCase(
                    eval_id=f"EVAL-{datetime.now().strftime('%Y%m%d')}-{counter:03d}",
                    target_file=f_path,
                    category=category,
                    issue_description=desc,
                    expected_rule="Conformité au Gold Standard story_template.md et aux 4 piliers Gherkin.",
                    severity="BLOCKING",
                    discovered_at=now_str,
                    metadata={"source": source},
                )
                evals.append(eval_case)
                counter += 1
                continue

            # Format 3 : Détection de rejets bloquants ou d'avertissements standards
            is_blocking = "[REJET]" in stripped or "FAIL" in stripped or "[GUARDRAIL" in stripped
            is_warning = "[AVERTISSEMENT]" in stripped or "WARN" in stripped

            if is_blocking or is_warning:
                clean_desc = re.sub(r"^[-*•\s]*\[(REJET|AVERTISSEMENT|GUARDRAIL[^\]]*)\]\s*", "", stripped).strip()
                clean_desc = clean_desc.lstrip("-*• :").strip()

                if len(clean_desc) > 5:
                    full_line_lower = stripped.lower()
                    category = "blueprint_drift"
                    if "invest" in full_line_lower:
                        category = "invest_criteria"
                    elif "gherkin" in full_line_lower or "pilier" in full_line_lower:
                        category = "gherkin_4_pillars"
                    elif "fuite" in full_line_lower or "tech" in full_line_lower or "code" in full_line_lower:
                        category = "technical_leak"

                    eval_case = EvalTestCase(
                        eval_id=f"EVAL-{datetime.now().strftime('%Y%m%d')}-{counter:03d}",
                        target_file=current_file,
                        category=category,
                        issue_description=clean_desc,
                        expected_rule="Conformité au Gold Standard story_template.md et aux 4 piliers Gherkin.",
                        severity="BLOCKING" if is_blocking else "WARNING",
                        discovered_at=now_str,
                        metadata={"source": source},
                    )
                    evals.append(eval_case)
                    counter += 1

        return evals

    def save_eval_pack(self, evals: List[EvalTestCase], filename: str = "harvested_evals.json") -> Path:
        """Sauvegarde les cas d'évaluation dans memory/evals/."""
        output_file = self.evals_dir / filename
        data = {
            "project": self.project_path.name,
            "generated_at": datetime.now().isoformat(),
            "total_evals": len(evals),
            "evals": [e.to_dict() for e in evals],
        }
        output_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        return output_file
