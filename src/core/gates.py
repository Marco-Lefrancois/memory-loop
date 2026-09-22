"""
mLoop Core - Runnable Gates, Depth Tree Orchestration & Execution Fingerprints
Standard Normatif : ADR-0341 (Inspiré de unlazy v2.1.0)
Zéro dépendance externe lourde (Python standard library 3.11+).
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field
from fnmatch import fnmatch
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from src.utils.logger import get_logger

logger = get_logger("core.gates")

# Constantes de Configuration
DEFAULT_TIMEOUT_SEC = 120
MAX_OUTPUT_BYTES = 1024 * 1024  # 1 MiB
LOCK_DIR_NAME = ".unlazy_locks"

# Expressions Régulières pour le Parsing Strict
GATE_RE = re.compile(r"^- \[( |x|X)\] (.*)$")
ATTR_RE = re.compile(r"^(\s{2,}|\t+)(CHECK|EXPECT|EVIDENCE|CWD):\s?(.*)$")
UNINDENTED_ATTR_RE = re.compile(r"^(CHECK|EXPECT|EVIDENCE|CWD):\s?(.*)$")
ABANDON_RE = re.compile(r"^ABANDON:\s*(\S*)\s*(.*)$")
INDENTED_ABANDON_RE = re.compile(r"^\s+ABANDON:")
OWNS_RE = re.compile(r"^OWNS:\s*(.*)$")
FENCE_OPEN_RE = re.compile(r"^( {0,3})(`{3,}|~{3,})(.*)$")
REGEX_EXPECT_RE = re.compile(r"^/([\s\S]*)/([a-z]*)$")
ID_MATCH_RE = re.compile(r"^(\S+?):(?:\s+|$)")
VALID_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


@dataclass
class Gate:
    line_no: int
    id: str
    title: str
    checked: bool = False
    check: Optional[str] = None
    expect: Optional[str] = None
    cwd: Optional[str] = None
    evidence: Optional[str] = None
    evidence_line: int = -1

    @property
    def is_runnable(self) -> bool:
        return bool(self.check and self.expect)

    @property
    def is_manual(self) -> bool:
        return not self.check and not self.expect


@dataclass
class GateLedger:
    file_path: Optional[Path] = None
    title: str = "Gates"
    scope: Optional[str] = None
    owns: List[str] = field(default_factory=list)
    gates: List[Gate] = field(default_factory=list)
    abandoned: Dict[str, str] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    raw_text: str = ""
    eol: str = "\n"

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0 and len(self.gates) > 0


@dataclass
class GateResult:
    gate_id: str
    title: str
    passed: bool
    is_runnable: bool
    exit_code: int
    duration_ms: float
    expect_matched: bool
    output_digest: str = ""
    output_bytes: int = 0
    path_fingerprint: str = ""
    error_msg: Optional[str] = None
    abandon_reason: Optional[str] = None
    evidence_text: str = ""


@dataclass
class LedgerStatus:
    all_met: bool
    total_gates: int
    met_gates: int
    pending_gates: int
    abandoned_gates: int
    manual_gates: int
    handoff_required: bool
    results: List[GateResult] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


def compute_sha256(value: str | bytes) -> str:
    if isinstance(value, str):
        value = value.encode("utf-8")
    return hashlib.sha256(value).hexdigest()


def compute_path_fingerprint() -> str:
    path_env = os.environ.get("PATH", "")
    dirs = [d for d in path_env.split(os.pathsep) if d.strip()]
    digest = compute_sha256(path_env)[:6]
    return f"{digest} ({len(dirs)} dirs)"


def get_default_shell() -> Tuple[str, List[str]]:
    """Résout le shell par défaut du système hôte."""
    if sys.platform == "win32":
        powershell = shutil.which("pwsh") or shutil.which("powershell")
        if powershell:
            return "pwsh", [powershell, "-NoProfile", "-NonInteractive", "-Command"]
        comspec = os.environ.get("ComSpec", "cmd.exe")
        return "cmd", [comspec, "/d", "/s", "/c"]
    sh = shutil.which("bash") or shutil.which("sh") or "/bin/sh"
    return "sh", [sh, "-c"]


def parse_expect_pattern(expect_str: str) -> Tuple[str, str, bool]:
    """Parse l'expectation sous forme de regex (/pattern/flags) ou de texte brut."""
    match = REGEX_EXPECT_RE.match(expect_str.strip())
    if match:
        pattern, flags = match.groups()
        return "regex", pattern, ("i" in flags)
    return "text", expect_str.strip(), False


def parse_gates(text: str, file_path: Optional[Path] = None) -> GateLedger:
    """Parseur strict de fichiers de gates Markdown (conforme au standard unlazy)."""
    eol = "\r\n" if "\r\n" in text else "\n"
    lines = text.splitlines()
    ledger = GateLedger(file_path=file_path, raw_text=text, eol=eol)

    current_gate: Optional[Gate] = None
    seen_gate = False
    fence_char: Optional[str] = None
    fence_len = 0
    declared_ids: Dict[str, int] = {}
    declared_attrs: Dict[str, Set[str]] = {}

    for idx, line in enumerate(lines):
        line_no = idx + 1

        # Gestion des blocs de code clôturés (fences)
        if fence_char:
            close_match = re.match(r"^( {0,3})(`+|~+)[ \t]*$", line)
            if close_match and close_match.group(2)[0] == fence_char and len(close_match.group(2)) >= fence_len:
                fence_char = None
            continue

        fence_match = FENCE_OPEN_RE.match(line)
        if fence_match and not (fence_match.group(2)[0] == "`" and "`" in fence_match.group(3)):
            fence_char = fence_match.group(2)[0]
            fence_len = len(fence_match.group(2))
            continue

        # Détection d'un titre / Scope
        if line.startswith("# "):
            ledger.title = line[2:].strip()
            continue
        if line.startswith("Scope:"):
            ledger.scope = line[6:].strip()
            continue

        # Détection de l'entête OWNS
        owns_match = OWNS_RE.match(line)
        if owns_match:
            if seen_gate:
                ledger.errors.append(f"Ligne {line_no}: OWNS doit apparaître avant la première gate.")
                continue
            globs = [g.strip() for g in owns_match.group(1).split(",") if g.strip()]
            if not globs:
                ledger.errors.append(f"Ligne {line_no}: Entête OWNS présent mais sans chemin valide.")
            ledger.owns.extend(globs)
            continue

        # Détection d'une Gate (- [ ] ID: titre)
        gate_match = GATE_RE.match(line)
        if gate_match:
            seen_gate = True
            is_checked = gate_match.group(1).lower() == "x"
            raw_title = gate_match.group(2).strip()

            id_match = ID_MATCH_RE.match(raw_title)
            if not id_match:
                gate_id = f"L{line_no}"
                title = raw_title
                ledger.errors.append(f"Ligne {line_no}: La gate requiert un ID explicite suivi de ':' (ex: '- [ ] G1: Titre').")
            else:
                gate_id = id_match.group(1)
                title = raw_title[len(id_match.group(0)):].strip()
                if not VALID_ID_RE.match(gate_id):
                    ledger.errors.append(f"Ligne {line_no}: ID de gate invalide '{gate_id}'.")

            if not title:
                ledger.errors.append(f"Ligne {line_no}: L'intitulé de la gate '{gate_id}' est vide.")

            if gate_id in declared_ids:
                ledger.errors.append(f"Ligne {line_no}: ID de gate dupliqué '{gate_id}' (déjà défini ligne {declared_ids[gate_id]}).")
            else:
                declared_ids[gate_id] = line_no

            current_gate = Gate(line_no=line_no, id=gate_id, title=title, checked=is_checked)
            ledger.gates.append(current_gate)
            declared_attrs[gate_id] = set()
            continue

        # Contrôle des abandons (ABANDON: <id> <reason>)
        if INDENTED_ABANDON_RE.match(line):
            ledger.errors.append(f"Ligne {line_no}: ABANDON indenté détecté. ABANDON doit impérativement débuter en colonne 1.")
            current_gate = None
            continue

        abandon_match = ABANDON_RE.match(line)
        if abandon_match:
            ab_id = abandon_match.group(1).rstrip(":")
            ab_reason = abandon_match.group(2).strip()
            if not ab_id or not ab_reason:
                ledger.errors.append(f"Ligne {line_no}: ABANDON requiert un ID de gate et un motif explicite non-vide.")
            elif ab_id in ledger.abandoned:
                ledger.errors.append(f"Ligne {line_no}: Abandon dupliqué pour la gate '{ab_id}'.")
            else:
                ledger.abandoned[ab_id] = ab_reason
            current_gate = None
            continue

        # Contrôle des attributs non indentés
        unindented_match = UNINDENTED_ATTR_RE.match(line)
        if unindented_match:
            ledger.errors.append(f"Ligne {line_no}: Attribut '{unindented_match.group(1)}' non indenté. Indentez avec 2 espaces sous la gate.")
            current_gate = None
            continue

        # Attributs de la gate courante (CHECK, EXPECT, CWD, EVIDENCE)
        attr_match = ATTR_RE.match(line)
        if attr_match:
            if not current_gate:
                ledger.errors.append(f"Ligne {line_no}: Attribut orphelin '{attr_match.group(2)}' sans gate parente.")
                continue
            key = attr_match.group(2).upper()
            val = attr_match.group(3).strip()

            if key in declared_attrs[current_gate.id]:
                ledger.errors.append(f"Ligne {line_no}: Attribut dupliqué '{key}' pour la gate '{current_gate.id}'.")
            declared_attrs[current_gate.id].add(key)

            if key == "CHECK":
                current_gate.check = val
            elif key == "EXPECT":
                current_gate.expect = val
            elif key == "CWD":
                current_gate.cwd = val
            elif key == "EVIDENCE":
                current_gate.evidence = val
                current_gate.evidence_line = line_no
            continue

    # Validation finale du ledger
    if not ledger.gates:
        ledger.errors.append("Le grand livre ne contient aucune gate valide.")

    for g in ledger.gates:
        if (g.check and not g.expect) or (g.expect and not g.check):
            ledger.errors.append(f"Gate '{g.id}': Une gate exécutable doit obligatoirement définir CHECK: ET EXPECT:.")

    for ab_id in ledger.abandoned:
        if ab_id not in declared_ids:
            ledger.errors.append(f"ABANDON référence une gate inexistante '{ab_id}'.")

    return ledger


def execute_single_gate(gate: Gate, root_dir: Path, timeout: int = DEFAULT_TIMEOUT_SEC) -> GateResult:
    """Exécute l'oracle d'une gate et produit son empreinte cryptographique."""
    start_time = time.perf_counter()

    if not gate.is_runnable:
        evidence_str = gate.evidence or ""
        is_met = gate.checked and bool(evidence_str and evidence_str.lower() != "pending")
        return GateResult(
            gate_id=gate.id,
            title=gate.title,
            passed=is_met,
            is_runnable=False,
            exit_code=0 if is_met else 1,
            duration_ms=0.0,
            expect_matched=False,
            evidence_text=evidence_str or "pending (manual gate)"
        )

    shell_name, shell_cmd_prefix = get_default_shell()
    exec_cwd = root_dir
    if gate.cwd:
        exec_cwd = (root_dir / gate.cwd).resolve()

    cmd = shell_cmd_prefix + [gate.check]

    try:
        proc = subprocess.run(
            cmd,
            cwd=exec_cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        duration_ms = (time.perf_counter() - start_time) * 1000
        output = proc.stdout or ""
        exit_code = proc.returncode
    except subprocess.TimeoutExpired as te:
        duration_ms = (time.perf_counter() - start_time) * 1000
        output = (te.stdout or "") if hasattr(te, "stdout") else ""
        return GateResult(
            gate_id=gate.id,
            title=gate.title,
            passed=False,
            is_runnable=True,
            exit_code=124,
            duration_ms=duration_ms,
            expect_matched=False,
            error_msg=f"Timeout dépassé ({timeout}s)",
            evidence_text=f"failed | timeout ({timeout}s)"
        )
    except Exception as exc:
        duration_ms = (time.perf_counter() - start_time) * 1000
        return GateResult(
            gate_id=gate.id,
            title=gate.title,
            passed=False,
            is_runnable=True,
            exit_code=127,
            duration_ms=duration_ms,
            expect_matched=False,
            error_msg=str(exc),
            evidence_text=f"failed | exec error: {exc}"
        )

    # Calcul des empreintes
    output_bytes = len(output.encode("utf-8"))
    out_digest = compute_sha256(output)
    path_fp = compute_path_fingerprint()

    # Vérification du motif EXPECT
    kind, pattern, case_insensitive = parse_expect_pattern(gate.expect)
    expect_matched = False
    if kind == "regex":
        flags = re.IGNORECASE if case_insensitive else 0
        expect_matched = bool(re.search(pattern, output, flags=flags))
    else:
        expect_matched = pattern in output

    passed = (exit_code == 0) and expect_matched

    if passed:
        evidence_text = f"met | shell:{shell_name} | exit:0 | out:sha256:{out_digest[:8]} ({output_bytes}B) | path:{path_fp}"
    else:
        fail_reasons = []
        if exit_code != 0:
            fail_reasons.append(f"exit:{exit_code}")
        if not expect_matched:
            fail_reasons.append("expect_mismatch")
        evidence_text = f"failed | {' '.join(fail_reasons)} | shell:{shell_name} | out:sha256:{out_digest[:8]}"

    return GateResult(
        gate_id=gate.id,
        title=gate.title,
        passed=passed,
        is_runnable=True,
        exit_code=exit_code,
        duration_ms=duration_ms,
        expect_matched=expect_matched,
        output_digest=out_digest,
        output_bytes=output_bytes,
        path_fingerprint=path_fp,
        evidence_text=evidence_text
    )


def verify_ledger(
    ledger: GateLedger,
    root_dir: Path,
    reverify: bool = False,
    update_file: bool = True
) -> LedgerStatus:
    """Vérifie l'ensemble des portails d'un grand livre."""
    results: List[GateResult] = []
    total = len(ledger.gates)
    met_count = 0
    pending_count = 0
    abandoned_count = len(ledger.abandoned)
    manual_count = 0

    if not ledger.is_valid:
        return LedgerStatus(
            all_met=False,
            total_gates=total,
            met_gates=0,
            pending_gates=total,
            abandoned_gates=abandoned_count,
            manual_gates=0,
            handoff_required=True,
            errors=ledger.errors
        )

    for gate in ledger.gates:
        if gate.id in ledger.abandoned:
            res = GateResult(
                gate_id=gate.id,
                title=gate.title,
                passed=False,
                is_runnable=gate.is_runnable,
                exit_code=1,
                duration_ms=0.0,
                expect_matched=False,
                abandon_reason=ledger.abandoned[gate.id],
                evidence_text=f"abandoned: {ledger.abandoned[gate.id]}"
            )
            results.append(res)
            continue

        if gate.is_manual:
            manual_count += 1
            is_met = gate.checked and (gate.evidence and gate.evidence.lower() != "pending")
            if is_met:
                met_count += 1
            else:
                pending_count += 1
            results.append(GateResult(
                gate_id=gate.id,
                title=gate.title,
                passed=is_met,
                is_runnable=False,
                exit_code=0 if is_met else 1,
                duration_ms=0.0,
                expect_matched=False,
                evidence_text=gate.evidence or "pending"
            ))
            continue

        # Gate Exécutable
        should_run = reverify or not gate.checked or not gate.evidence or "met" not in gate.evidence
        if should_run:
            res = execute_single_gate(gate, root_dir=root_dir)
        else:
            res = GateResult(
                gate_id=gate.id,
                title=gate.title,
                passed=gate.checked,
                is_runnable=True,
                exit_code=0,
                duration_ms=0.0,
                expect_matched=True,
                evidence_text=gate.evidence or "met"
            )

        if res.passed:
            met_count += 1
        else:
            pending_count += 1
        results.append(res)

    all_met = (met_count == total) and (abandoned_count == 0)
    handoff_required = (abandoned_count > 0) or any(r.abandon_reason for r in results)

    if update_file and ledger.file_path and ledger.file_path.exists():
        apply_results_to_file(ledger.file_path, results, ledger.eol)

    return LedgerStatus(
        all_met=all_met,
        total_gates=total,
        met_gates=met_count,
        pending_gates=pending_count,
        abandoned_gates=abandoned_count,
        manual_gates=manual_count,
        handoff_required=handoff_required,
        results=results,
        errors=[]
    )


def apply_results_to_file(file_path: Path, results: List[GateResult], eol: str = "\n") -> None:
    """Met à jour atomiquement les cases à cocher et lignes EVIDENCE dans le fichier Markdown."""
    res_map = {r.gate_id: r for r in results}
    text = file_path.read_text(encoding="utf-8")
    lines = text.splitlines()
    new_lines = []

    current_id: Optional[str] = None
    fence_char: Optional[str] = None
    fence_len = 0

    for line in lines:
        # Fences
        if fence_char:
            close_match = re.match(r"^( {0,3})(`+|~+)[ \t]*$", line)
            if close_match and close_match.group(2)[0] == fence_char and len(close_match.group(2)) >= fence_len:
                fence_char = None
            new_lines.append(line)
            continue

        fence_match = FENCE_OPEN_RE.match(line)
        if fence_match and not (fence_match.group(2)[0] == "`" and "`" in fence_match.group(3)):
            fence_char = fence_match.group(2)[0]
            fence_len = len(fence_match.group(2))
            new_lines.append(line)
            continue

        gate_match = GATE_RE.match(line)
        if gate_match:
            raw_title = gate_match.group(2).strip()
            id_match = ID_MATCH_RE.match(raw_title)
            if id_match:
                current_id = id_match.group(1)
                if current_id in res_map:
                    box = "[x]" if res_map[current_id].passed else "[ ]"
                    new_lines.append(f"- {box} {raw_title}")
                    continue
            new_lines.append(line)
            continue

        attr_match = ATTR_RE.match(line)
        if attr_match and current_id and current_id in res_map:
            key = attr_match.group(2).upper()
            indent = attr_match.group(1)
            if key == "EVIDENCE":
                ev_val = res_map[current_id].evidence_text
                new_lines.append(f"{indent}EVIDENCE: {ev_val}")
                continue

        new_lines.append(line)

    updated_text = eol.join(new_lines) + (eol if text.endswith("\n") else "")
    temp_file = file_path.with_suffix(".tmp_" + compute_sha256(str(time.time()))[:8])
    temp_file.write_text(updated_text, encoding="utf-8")
    temp_file.replace(file_path)


# --- GESTION DES BAUX ET VERROUS OWNS ---

def claim_lease(scope: str, leaf_id: str, owns_globs: List[str], base_dir: Path) -> Tuple[bool, str]:
    """Tente de verrouiller les chemins exclusifs OWNS pour un worker/leaf."""
    locks_dir = base_dir / LOCK_DIR_NAME
    locks_dir.mkdir(parents=True, exist_ok=True)

    # Vérification des baux existants
    for lock_file in locks_dir.glob("*.lock.json"):
        try:
            data = json.loads(lock_file.read_text(encoding="utf-8"))
            existing_leaf = data.get("leaf_id")
            existing_globs = data.get("owns_globs", [])

            if existing_leaf == leaf_id:
                continue

            for new_g in owns_globs:
                for exist_g in existing_globs:
                    if patterns_overlap(new_g, exist_g):
                        return False, f"Collision OWNS: '{new_g}' chevauche '{exist_g}' possédé par '{existing_leaf}'."
        except Exception as e:
            logger.debug(
                "Collision OWNS : comparaison de globs échouée, itération suivante",
                exc_info=True,
                extra={
                    "component": "core.gates",
                    "operation": "check_ownership_globs",
                    "error": str(e),
                },
            )

    # Création du verrou atomique
    lock_target = locks_dir / f"{scope}_{leaf_id}.lock.json"
    payload = {
        "scope": scope,
        "leaf_id": leaf_id,
        "owns_globs": owns_globs,
        "pid": os.getpid(),
        "created_at": time.time()
    }
    lock_target.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return True, f"Bail accordé pour '{leaf_id}'."


def release_lease(scope: str, leaf_id: str, base_dir: Path) -> None:
    """Libère le verrou OWNS d'une feuille."""
    lock_target = base_dir / LOCK_DIR_NAME / f"{scope}_{leaf_id}.lock.json"
    if lock_target.exists():
        try:
            lock_target.unlink()
        except OSError as e:
            logger.warning(
                "Libération du verrou OWNS impossible, fichier verrou laissé en place",
                exc_info=True,
                extra={
                    "component": "core.gates",
                    "operation": "release_lease",
                    "error": str(e),
                },
            )


def patterns_overlap(pat1: str, pat2: str) -> bool:
    """Détecte les collisions potentielles entre deux globs de fichiers."""
    p1 = pat1.replace("\\", "/").rstrip("/")
    p2 = pat2.replace("\\", "/").rstrip("/")

    if p1 == p2:
        return True

    # Traitement des préfixes récursifs (** ou *)
    prefix1 = p1.replace("/**", "").replace("/*", "")
    prefix2 = p2.replace("/**", "").replace("/*", "")

    if p2 == prefix1 or p2.startswith(prefix1 + "/") or p1 == prefix2 or p1.startswith(prefix2 + "/"):
        return True

    if fnmatch(p1, p2) or fnmatch(p2, p1):
        return True

    return False


# --- LINTER ANTI-TAUTOLOGIE (gate-lint) ---

@dataclass
class LintIssue:
    gate_id: str
    line_no: int
    severity: str  # ERROR | WARNING
    message: str


def lint_ledger(ledger: GateLedger) -> List[LintIssue]:
    """Audit lexical contre les oracles tautologiques et les assertions creuses."""
    issues: List[LintIssue] = []

    for g in ledger.gates:
        if not g.is_runnable:
            continue

        cmd = (g.check or "").strip().lower()
        exp = (g.expect or "").strip().lower()

        # Règle 1: Tautologie 'echo ok' / 'echo pass'
        if cmd.startswith("echo ") and exp in cmd:
            issues.append(LintIssue(
                gate_id=g.id,
                line_no=g.line_no,
                severity="ERROR",
                message="Oracle tautologique détecté : la commande produit artificiellement sa propre expectation."
            ))

        # Règle 2: Expectation ultra-courte ou triviale
        if len(exp) < 2 or exp in ["ok", "0", "true", "yes"]:
            issues.append(LintIssue(
                gate_id=g.id,
                line_no=g.line_no,
                severity="WARNING",
                message=f"Expectation très faible ('{exp}'). Utilisez un marqueur précis (ex: '1 passed' ou motif regex)."
            ))

        # Règle 3: Titre décrivant une action au lieu d'une issue mesurable
        title_lower = g.title.lower()
        if any(title_lower.startswith(w) for w in ["tester ", "vérifier ", "exécuter ", "lancer ", "faire "]):
            issues.append(LintIssue(
                gate_id=g.id,
                line_no=g.line_no,
                severity="WARNING",
                message="Le titre décrit une activité plutôt qu'un résultat observable (ex: préférer 'Les tokens expirés sont rejetés avec 401')."
            ))

    return issues


# --- RENDU VISUEL & TEXTUALISATION ---

def render_progress_bar(met: int, total: int, width: int = 20) -> str:
    if total == 0:
        return "[" + " " * width + "] 0%"
    pct = int((met / total) * 100)
    filled = int((met / total) * width)
    bar = "█" * filled + "░" * (width - filled)
    return f"[{bar}] {pct}% ({met}/{total} Gates)"


def render_depth_tree_visual(
    title: str,
    status: LedgerStatus,
    scope: str = "default",
    owns: Optional[List[str]] = None
) -> str:
    """Génère un affichage structuré et lisible de l'arbre d'exécution des gates."""
    lines = []
    lines.append("╔" + "═" * 78 + "╗")
    lines.append(f"║  MLOOP DEPTH TREE & RUNNABLE GATES — {title[:40]:<40} ║")
    lines.append("╠" + "═" * 78 + "╣")
    lines.append(f"║  Scope : {scope:<68} ║")
    if owns:
        owns_str = ", ".join(owns)[:66]
        lines.append(f"║  OWNS  : {owns_str:<68} ║")
    lines.append("╟" + "─" * 78 + "╢")

    for res in status.results:
        if res.abandon_reason:
            icon = "⛔ [ABANDONED]"
            info = f"Raison: {res.abandon_reason[:45]}"
        elif res.passed:
            icon = "✔ [VERIFIED] "
            info = f"exit:0 ({res.duration_ms:.0f}ms)" if res.is_runnable else "manuel OK"
        elif not res.is_runnable:
            icon = "⏳ [PENDING]  "
            info = "revue manuelle requise"
        else:
            icon = "✖ [FAILED]   "
            info = f"exit:{res.exit_code} (non-conforme)"

        gate_line = f"║  {icon} {res.gate_id}: {res.title[:38]:<38} │ {info:<18} ║"
        lines.append(gate_line)

    lines.append("╠" + "═" * 78 + "╣")
    prog = render_progress_bar(status.met_gates, status.total_gates, width=24)
    overall_status = "ALL MET" if status.all_met else ("HANDOFF REQUIRED" if status.handoff_required else "IN-PROGRESS")
    summary = f"║  STATUS: {overall_status:<16} PROGRESS: {prog:<38} ║"
    lines.append(summary)
    lines.append("╚" + "═" * 78 + "╝")

    return "\n".join(lines)
