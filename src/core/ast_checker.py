"""
Linter statique AST déterministe pour le framework mLoop (ADR-0381 / MLOOP-080-BE).
Vérifie la conformité modulaire ADR-0202 (<=300 lignes, <=15 Ko) et les standards
de robustesse Python Senior ADR-0369 sans aucune dépendance externe.
"""
from __future__ import annotations

import ast
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Set


@dataclass
class AstViolation:
    """Représente une non-conformité structurelle détectée par l'AST."""
    rule_id: str
    line_number: int
    message: str
    corrective_action: str


@dataclass
class AstAuditReport:
    """Rapport d'audit statique complet d'un fichier source."""
    file_path: Path
    passed: bool
    line_count: int
    file_size_bytes: int
    violations: list[AstViolation] = field(default_factory=list)
    duration_ms: float = 0.0


class _AstRuleVisitor(ast.NodeVisitor):
    """Visiteur AST traquant les violations aux règles ADR-0202 et ADR-0369."""

    def __init__(self) -> None:
        self.violations: list[AstViolation] = []
        self._with_context_call_ids: Set[int] = set()

    def visit_With(self, node: ast.With) -> None:
        for item in node.items:
            if isinstance(item.context_expr, ast.Call):
                self._with_context_call_ids.add(id(item.context_expr))
        self.generic_visit(node)

    def visit_AsyncWith(self, node: ast.AsyncWith) -> None:
        for item in node.items:
            if isinstance(item.context_expr, ast.Call):
                self._with_context_call_ids.add(id(item.context_expr))
        self.generic_visit(node)

    def _get_call_name(self, node: ast.Call) -> str:
        """Résout le nom qualifié d'un appel (ex. 'subprocess.run', 'open')."""
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            parts = [node.func.attr]
            curr = node.func.value
            while isinstance(curr, ast.Attribute):
                parts.append(curr.attr)
                curr = curr.value
            if isinstance(curr, ast.Name):
                parts.append(curr.id)
            return ".".join(reversed(parts))
        return ""

    def visit_Call(self, node: ast.Call) -> None:
        call_name = self._get_call_name(node)

        # RULE-AST-02 : Ressources nues (ADR-0369 Standard 2)
        bare_targets = {"sqlite3.connect", "open", "httpx.Client", "httpx.AsyncClient"}
        if call_name in bare_targets and id(node) not in self._with_context_call_ids:
            self.violations.append(
                AstViolation(
                    rule_id="RULE-AST-02",
                    line_number=node.lineno,
                    message=f"Ressource nue '{call_name}' non encapsulée dans un gestionnaire de contexte.",
                    corrective_action="Encapsuler l'appel dans un bloc 'with' ou 'async with'."
                )
            )

        # RULE-AST-03 : Timeouts obligatoires (ADR-0369 Standard 3)
        timeout_targets = {
            "subprocess.run", "subprocess.Popen",
            "requests.get", "requests.post", "requests.put", "requests.delete", "requests.request",
            "httpx.get", "httpx.post", "httpx.put", "httpx.delete", "httpx.request"
        }
        if call_name in timeout_targets:
            has_timeout = any(kw.arg == "timeout" for kw in node.keywords)
            if not has_timeout:
                self.violations.append(
                    AstViolation(
                        rule_id="RULE-AST-03",
                        line_number=node.lineno,
                        message=f"Appel bloquant '{call_name}' dépourvu d'argument 'timeout'.",
                        corrective_action="Spécifier explicitement un argument 'timeout=...' (en secondes)."
                    )
                )

        # RULE-AST-05 : stacklevel=2 sur warnings.warn (ADR-0369 Standard 7)
        if call_name in {"warnings.warn", "warn"}:
            has_stacklevel_kw = any(kw.arg == "stacklevel" for kw in node.keywords)
            has_stacklevel_pos = len(node.args) >= 3
            if not (has_stacklevel_kw or has_stacklevel_pos):
                self.violations.append(
                    AstViolation(
                        rule_id="RULE-AST-05",
                        line_number=node.lineno,
                        message="Appel à 'warnings.warn' omettant 'stacklevel=2'.",
                        corrective_action="Ajouter l'argument 'stacklevel=2' pour désigner le code appelant."
                    )
                )

        self.generic_visit(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        # RULE-AST-04 : except: pass silencieux (ADR-0369 Standard 4)
        is_silent = False
        has_logger_call = False

        for stmt in node.body:
            if isinstance(stmt, ast.Pass):
                is_silent = True
            elif isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant):
                # Docstring or Ellipsis
                if stmt.value.value is ...:
                    is_silent = True
            elif isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
                call_name = self._get_call_name(stmt.value)
                if "log" in call_name.lower() or "print" in call_name.lower():
                    has_logger_call = True

        if is_silent and not has_logger_call:
            self.violations.append(
                AstViolation(
                    rule_id="RULE-AST-04",
                    line_number=node.lineno,
                    message="Clause 'except' silencieuse sans journalisation d'audit.",
                    corrective_action="Remplacer 'pass' par un appel logger contextuel avec exc_info=True."
                )
            )

        self.generic_visit(node)


class AstChecker:
    """Moteur de contrôle statique AST déterministe pour fichiers Python."""

    MAX_LINES: int = 300
    MAX_BYTES: int = 15360  # 15 Ko

    @classmethod
    def audit_file(cls, file_path: Path) -> AstAuditReport:
        t0 = time.perf_counter()
        if not file_path.exists():
            return AstAuditReport(
                file_path=file_path,
                passed=False,
                line_count=0,
                file_size_bytes=0,
                violations=[
                    AstViolation(
                        rule_id="RULE-AST-IO",
                        line_number=0,
                        message=f"Fichier introuvable sur le disque : {file_path}",
                        corrective_action="Vérifier le chemin d'accès au fichier source."
                    )
                ],
                duration_ms=(time.perf_counter() - t0) * 1000,
            )

        file_size = file_path.stat().st_size
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            return AstAuditReport(
                file_path=file_path,
                passed=False,
                line_count=0,
                file_size_bytes=file_size,
                violations=[
                    AstViolation(
                        rule_id="RULE-AST-IO",
                        line_number=0,
                        message=f"Erreur de lecture du fichier : {e}",
                        corrective_action="Vérifier l'encodage UTF-8 et les permissions."
                    )
                ],
                duration_ms=(time.perf_counter() - t0) * 1000,
            )

        lines = content.splitlines()
        line_count = len(lines)
        violations: list[AstViolation] = []

        # RULE-AST-01 : Modularité ADR-0202
        if line_count > cls.MAX_LINES:
            violations.append(
                AstViolation(
                    rule_id="RULE-AST-01",
                    line_number=line_count,
                    message=f"Plafond modulaire dépassé : {line_count} lignes (seuil strict = {cls.MAX_LINES}).",
                    corrective_action="Découper le module en composants spécialisés (ADR-0202)."
                )
            )

        if file_size > cls.MAX_BYTES:
            violations.append(
                AstViolation(
                    rule_id="RULE-AST-01",
                    line_number=line_count,
                    message=f"Taille de fichier excessive : {file_size} octets (seuil strict = {cls.MAX_BYTES} octets / 15 Ko).",
                    corrective_action="Alléger le contenu et extraire les fonctions secondaires."
                )
            )

        # Parse AST
        try:
            tree = ast.parse(content, filename=str(file_path))
        except SyntaxError as e:
            violations.append(
                AstViolation(
                    rule_id="RULE-AST-SYNTAX",
                    line_number=e.lineno or 0,
                    message=f"Erreur de syntaxe Python bloquante : {e.msg}",
                    corrective_action="Corriger la syntaxe Python du fichier source."
                )
            )
            return AstAuditReport(
                file_path=file_path,
                passed=False,
                line_count=line_count,
                file_size_bytes=file_size,
                violations=violations,
                duration_ms=(time.perf_counter() - t0) * 1000,
            )

        visitor = _AstRuleVisitor()
        visitor.visit(tree)
        violations.extend(visitor.violations)

        duration_ms = (time.perf_counter() - t0) * 1000
        return AstAuditReport(
            file_path=file_path,
            passed=len(violations) == 0,
            line_count=line_count,
            file_size_bytes=file_size,
            violations=violations,
            duration_ms=duration_ms,
        )


def check_file_ast(file_path: Path) -> AstAuditReport:
    """Point d'entrée fonctionnel pour auditer un fichier Python."""
    return AstChecker.audit_file(file_path)


def format_audit_report(report: AstAuditReport) -> str:
    """Formate le rapport d'audit pour un affichage console Zero-Fluff."""
    status_tag = "[PASS] OK" if report.passed else "[FAIL] VIOLATIONS"
    path_display = report.file_path.as_posix() if hasattr(report.file_path, "as_posix") else str(report.file_path)
    lines = [
        f"--- AUDIT AST : {path_display} ---",
        f"Statut : {status_tag} | {report.line_count} lignes | {report.file_size_bytes} octets | {report.duration_ms:.2f} ms",
    ]
    if report.violations:
        lines.append("Violations relevées :")
        for v in report.violations:
            loc = f"L{v.line_number}" if v.line_number > 0 else "N/A"
            lines.append(f"  * [{v.rule_id}] ({loc}) : {v.message}")
            lines.append(f"    └── Action : {v.corrective_action}")
    return "\n".join(lines)
