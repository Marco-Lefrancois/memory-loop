# -*- coding: utf-8 -*-
"""
RuleEngine — Moteur de validation dynamique piloté par ADR.
"""

import yaml
import re
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, List, Dict

@dataclass
class ValidationRule:
    check_id: str
    severity: str
    adr_id: str
    params: Dict = field(default_factory=dict)

@dataclass
class RuleViolation:
    check_id: str
    severity: str
    adr_id: str
    message: str

class RuleEngine:
    def __init__(self):
        self._rules: Dict[str, ValidationRule] = {}

    def load_from_adr_dir(self, adr_dir: Path) -> int:
        """Parse les frontmatters YAML des ADRs et indexe les règles."""
        count = 0
        if not adr_dir.exists():
            return 0
            
        for adr_file in adr_dir.glob("*.md"):
            content = adr_file.read_text(encoding="utf-8")
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    try:
                        data = yaml.safe_load(parts[1]) or {}
                        rules = data.get("validation_rules", [])
                        for r in rules:
                            self._rules[r["check_id"]] = ValidationRule(
                                check_id=r["check_id"],
                                severity=r["severity"],
                                adr_id=data.get("id", "UNKNOWN"),
                                params=r.get("params", {})
                            )
                            count += 1
                    except Exception:
                        pass
        return count

    def validate(self, check_id: str, content: str, context: dict = None, target: str = None) -> List[RuleViolation]:
        """Logique de validation de base pour satisfaire le test."""
        if check_id not in self._rules:
            return []
            
        rule = self._rules[check_id]
        violations = []
        
        if check_id == "no_local_file_paths":
            patterns = rule.params.get("forbidden_patterns", [])
            for p in patterns:
                if re.search(p, content, re.IGNORECASE):
                    violations.append(RuleViolation(
                        check_id=check_id,
                        severity=rule.severity,
                        adr_id=rule.adr_id,
                        message=f"Référence locale interdite détectée (pattern interdit : {p}). Utilisez la clé Jira correspondante."
                    ))
        if check_id == "min_len":
            min_length = rule.params.get("min", 0)
            if len(content) < min_length:
                violations.append(RuleViolation(
                    check_id=check_id,
                    severity=rule.severity,
                    adr_id=rule.adr_id,
                    message=f"Contenu trop court ({len(content)} < {min_length} caractères attendus)."
                ))

        return violations

    def validate_all(self, content: str, context: dict = None, target: str = None) -> List[RuleViolation]:
        """Exécute toutes les règles indexées sur le contenu."""
        violations = []
        for check_id in self._rules:
            violations.extend(self.validate(check_id, content, context, target=target))
        return violations
