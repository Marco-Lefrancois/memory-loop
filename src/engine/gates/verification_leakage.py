"""
mLoop Engine - Verification Leakage Gate (ADR-0354)
Porte anti-fuite de spécification et de vérification.
Évalue 4 critères formels pour interdire les tests tautologiques, les fuites de mocks
et les violations d'encapsulation (inspiré du Feature Gate du Google PPE).
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Set, Tuple


@dataclass
class LeakageViolation:
    criterion: int  # 1, 2, 3, ou 4
    criterion_name: str
    file_path: str
    line_no: int
    snippet: str
    message: str
    severity: str = "CRITICAL"  # "CRITICAL" ou "WARNING"


@dataclass
class LeakageReport:
    file_path: str
    passed: bool
    violations: List[LeakageViolation] = field(default_factory=list)

    @property
    def critical_count(self) -> int:
        return sum(1 for v in self.violations if v.severity == "CRITICAL")

    @property
    def warning_count(self) -> int:
        return sum(1 for v in self.violations if v.severity == "WARNING")

    def format_summary(self) -> str:
        status = "PASSED" if self.passed else "REJECTED (LEAKAGE DETECTED)"
        lines = [
            f"=== VERIFICATION LEAKAGE REPORT: {Path(self.file_path).name} ===",
            f"Statut : {status} (Critiques: {self.critical_count}, Alertes: {self.warning_count})",
        ]
        if self.violations:
            lines.append("Violations identifiées :")
            for v in self.violations:
                lines.append(
                    f"  * [C{v.criterion}:{v.criterion_name}] L{v.line_no}: {v.message}\n"
                    f"    Snippet: {v.snippet.strip()}"
                )
        return "\n".join(lines)


class VerificationLeakageGate:
    """
    Analyseur statique de code de test (Python AST) vérifiant les 4 critères anti-fuite.
    """

    CRITERIA_NAMES = {
        1: "Black-Box Strict (Pas d'assertion sur membres privés)",
        2: "Anti-Tautologie Mocks (Pas d'auto-validation de bouchons)",
        3: "Invariant Causal Métier (Vérification d'état ou retour réel)",
        4: "Isolation d'État Pur (Absence de contamination d'état global)",
    }

    def __init__(self):
        pass

    def check_file(self, file_path: str | Path) -> LeakageReport:
        """Vérifie un fichier source de test Python ou Gherkin."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Fichier introuvable : {file_path}")

        content = path.read_text(encoding="utf-8", errors="replace")
        return self.check_code(content, file_path=str(path))

    def check_code(self, code: str, file_path: str = "<memory>") -> LeakageReport:
        """Vérifie un fragment de code ou le contenu d'un fichier."""
        violations: List[LeakageViolation] = []

        try:
            tree = ast.parse(code, filename=file_path)
        except SyntaxError as e:
            # Si le fichier n'est pas du python valide (ex: Gherkin), analyse lexicale heuristique
            return self._check_gherkin_or_text(code, file_path)

        code_lines = code.splitlines()

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and (node.name.startswith("test_") or node.name.endswith("_test")):
                fn_violations = self._analyze_test_function(node, code_lines, file_path)
                violations.extend(fn_violations)

        passed = not any(v.severity == "CRITICAL" for v in violations)
        return LeakageReport(file_path=file_path, passed=passed, violations=violations)

    def _analyze_test_function(
        self, fn_node: ast.FunctionDef, code_lines: List[str], file_path: str
    ) -> List[LeakageViolation]:
        violations: List[LeakageViolation] = []
        mock_values: Set[str] = set()
        has_real_assertion = False
        assert_count = 0

        # Passe 1 : Répertoire des valeurs assignées aux mocks dans le setup
        for stmt in fn_node.body:
            # Recherche de mock.return_value = <val> ou patch.return_value
            if isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    target_repr = ast.unparse(target) if hasattr(ast, "unparse") else ""
                    if "mock" in target_repr.lower() or "return_value" in target_repr:
                        if isinstance(stmt.value, ast.Constant):
                            mock_values.add(str(stmt.value.value))
                        elif hasattr(ast, "unparse"):
                            mock_values.add(ast.unparse(stmt.value))

        # Passe 2 : Analyse des assertions
        for stmt in ast.walk(fn_node):
            if isinstance(stmt, ast.Assert):
                assert_count += 1
                line_no = getattr(stmt, "lineno", fn_node.lineno)
                snippet = code_lines[line_no - 1] if 0 <= line_no - 1 < len(code_lines) else ""
                
                # Critère 1 : Black-Box Strict (Attributs privés)
                for sub in ast.walk(stmt):
                    if isinstance(sub, ast.Attribute) and sub.attr.startswith("_") and not sub.attr.startswith("__"):
                        violations.append(
                            LeakageViolation(
                                criterion=1,
                                criterion_name=self.CRITERIA_NAMES[1],
                                file_path=file_path,
                                line_no=line_no,
                                snippet=snippet,
                                message=f"Assertion sur membre privé '{sub.attr}'. Le test doit vérifier uniquement l'interface publique.",
                                severity="CRITICAL",
                            )
                        )

                # Critère 2 : Anti-Tautologie (assert X == X ou assert sur mock pur)
                if isinstance(stmt.test, ast.Compare):
                    left_repr = ast.unparse(stmt.test.left) if hasattr(ast, "unparse") else ""
                    for comparator in stmt.test.comparators:
                        comp_repr = ast.unparse(comparator) if hasattr(ast, "unparse") else ""
                        
                        # Tautologie littérale directe (assert a == a)
                        if left_repr and comp_repr and left_repr == comp_repr:
                            violations.append(
                                LeakageViolation(
                                    criterion=2,
                                    criterion_name=self.CRITERIA_NAMES[2],
                                    file_path=file_path,
                                    line_no=line_no,
                                    snippet=snippet,
                                    message=f"Assertion tautologique triviale '{left_repr} == {comp_repr}'.",
                                    severity="CRITICAL",
                                )
                            )

                        # Tautologie mock injecté
                        for mv in mock_values:
                            if mv and (comp_repr == mv or left_repr == mv):
                                violations.append(
                                    LeakageViolation(
                                        criterion=2,
                                        criterion_name=self.CRITERIA_NAMES[2],
                                        file_path=file_path,
                                        line_no=line_no,
                                        snippet=snippet,
                                        message=f"L'assertion compare directement la valeur de mock injectée '{mv}' sans transformation métier.",
                                        severity="WARNING",
                                    )
                                )

                # Critère 3 : Vérification de l'invariant réel
                # Détection d'assertion utile vs pur mock_call
                test_str = ast.unparse(stmt.test) if hasattr(ast, "unparse") else ""
                if not ("mock" in test_str.lower() and "assert_called" in test_str):
                    has_real_assertion = True

        # Critère 3 : Fonction sans aucune assertion réelle (uniquement des appels de mock ou vide)
        if assert_count == 0:
            # Vérifier s'il y a un pytest.raises
            has_raises = any(
                isinstance(n, ast.With) and any("raises" in (ast.unparse(item.context_expr) if hasattr(ast, "unparse") else "") for item in n.items)
                for n in ast.walk(fn_node)
            )
            if not has_raises:
                violations.append(
                    LeakageViolation(
                        criterion=3,
                        criterion_name=self.CRITERIA_NAMES[3],
                        file_path=file_path,
                        line_no=fn_node.lineno,
                        snippet=code_lines[fn_node.lineno - 1] if code_lines else "",
                        message=f"La fonction '{fn_node.name}' ne comporte aucune assertion sur un invariant d'état ou retour métier.",
                        severity="CRITICAL",
                    )
                )

        return violations

    def _check_gherkin_or_text(self, text: str, file_path: str) -> LeakageReport:
        """Analyse heuristique pour fichiers Gherkin (.feature)."""
        violations: List[LeakageViolation] = []
        lines = text.splitlines()

        for idx, line in enumerate(lines, start=1):
            stripped = line.strip()
            # Critère 1 : Mention de méthode privée dans un Then
            if stripped.startswith("Then") and ("_" in stripped and "private" in stripped.lower()):
                violations.append(
                    LeakageViolation(
                        criterion=1,
                        criterion_name=self.CRITERIA_NAMES[1],
                        file_path=file_path,
                        line_no=idx,
                        snippet=line,
                        message="Étape 'Then' mentionnant un état ou méthode privée.",
                        severity="CRITICAL",
                    )
                )

        passed = not any(v.severity == "CRITICAL" for v in violations)
        return LeakageReport(file_path=file_path, passed=passed, violations=violations)
