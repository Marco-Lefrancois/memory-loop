"""
Pipeline de test Graft Deep Build pour QA Sémantique (MLOOP-132-BE).
Exécute graft build --deep sur un corpus, teste graft ask, et compare
les performances avec le mode lexical (sans graphe).
"""

from __future__ import annotations

import importlib.util
import json
import logging
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

GRAFT_BUILD_TIMEOUT = 300
GRAFT_ASK_TIMEOUT = 30


@dataclass
class AskResult:
    files: list[str] = field(default_factory=list)
    raw_stdout: str = ""
    exit_code: int = -1


@dataclass
class Metrics:
    precision: float = 0.0
    recall: float = 0.0
    f1: float = 0.0
    tp: int = 0
    fp: int = 0
    fn: int = 0


@dataclass
class DeepTestReport:
    corpus_path: str = ""
    build_success: bool = False
    build_stderr: str = ""
    lexical_results: list[dict] = field(default_factory=list)
    deep_results: list[dict] = field(default_factory=list)
    lexical_agg: Optional[Metrics] = None
    deep_agg: Optional[Metrics] = None
    recall_delta: float = 0.0
    timestamp: str = ""


def _run_graft_command(args: list[str], cwd: str, timeout: float) -> subprocess.CompletedProcess:
    """Exécute une commande graft avec timeout strict (ADR-0369)."""
    cmd = ["graft"] + args
    use_shell = sys.platform == "win32"
    start = time.perf_counter()
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
            shell=use_shell,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
        elapsed = time.perf_counter() - start
        logger.info(
            "graft %s completed in %.2fs (exit=%d)",
            args[0],
            elapsed,
            result.returncode,
            extra={"graft_cmd": args[0], "elapsed_s": round(elapsed, 3)},
        )
        return result
    except subprocess.TimeoutExpired:
        elapsed = time.perf_counter() - start
        logger.error(
            "graft %s TIMEOUT after %.1fs (limit=%ds)",
            args[0],
            elapsed,
            timeout,
            extra={"graft_cmd": args[0], "elapsed_s": round(elapsed, 1)},
        )
        return subprocess.CompletedProcess(
            args=cmd,
            returncode=124,
            stdout="",
            stderr=f"[Timeout] graft {args[0]} exceeded {timeout}s",
        )


def _extract_files_from_json(stdout: str) -> list[str]:
    """Extrait les fichiers .py depuis la sortie JSON de graft ask."""
    try:
        data = json.loads(stdout)
        hits = data if isinstance(data, list) else data.get("hits", [])
        files = []
        for hit in hits:
            sym = hit.get("symbol", {})
            pointer = sym.get("pointer", "")
            if pointer:
                fp = pointer.split(":")[0]
                if fp.endswith(".py"):
                    files.append(fp)
            path = hit.get("path", "")
            if path and path.endswith(".py"):
                files.append(path)
        return sorted(set(files))
    except (json.JSONDecodeError, TypeError):
        return sorted(set(re.findall(r"(?:src/|tests/)\S+\.py", stdout)))


def compute_metrics(found: list[str], ground_truth: list[str]) -> Metrics:
    """Calcule Precision, Recall, F1 contre la vérité terrain."""
    fs, gs = set(found), set(ground_truth)
    if not gs:
        return Metrics()
    tp = len(fs & gs)
    p = tp / len(fs) if fs else 0.0
    r = tp / len(gs)
    f1 = 2 * p * r / (p + r) if (p + r) else 0.0
    return Metrics(
        precision=round(p, 3),
        recall=round(r, 3),
        f1=round(f1, 3),
        tp=tp,
        fp=len(fs - gs),
        fn=len(gs - fs),
    )


def run_graft_build_deep(
    corpus_path: str, timeout: float = GRAFT_BUILD_TIMEOUT
) -> tuple[bool, float, str]:
    """Exécute graft build --deep. Retourne (succès, exit_code, stderr)."""
    logger.info("Starting graft build --deep on %s (timeout=%ds)", corpus_path, timeout)
    result = _run_graft_command(["build", "--deep"], cwd=corpus_path, timeout=timeout)
    return result.returncode == 0, result.returncode, result.stderr


def run_graft_ask(
    question: str,
    corpus_path: str,
    deep: bool = True,
    timeout: float = GRAFT_ASK_TIMEOUT,
) -> AskResult:
    """Exécute graft ask et retourne les fichiers trouvés."""
    args = ["ask", question, "--json"]
    if not deep:
        args.append("--no-graph-rank")
    result = _run_graft_command(args, cwd=corpus_path, timeout=timeout)
    return AskResult(
        files=_extract_files_from_json(result.stdout),
        raw_stdout=result.stdout,
        exit_code=result.returncode,
    )


def _aggregate_metrics(results: list[dict]) -> Metrics:
    """Agrège les métriques moyennes sur un ensemble de résultats."""
    n = len(results) if results else 1
    return Metrics(
        precision=round(sum(r.get("precision", 0) for r in results) / n, 3),
        recall=round(sum(r.get("recall", 0) for r in results) / n, 3),
        f1=round(sum(r.get("f1", 0) for r in results) / n, 3),
        tp=sum(r.get("tp", 0) for r in results),
        fp=sum(r.get("fp", 0) for r in results),
        fn=sum(r.get("fn", 0) for r in results),
    )


def _load_default_bugs() -> list[dict]:
    """Charge les bugs depuis le dataset du spike MLOOP-130-BE."""
    ds = Path("scratch/mloop-130-benchmark/benchmark_dataset.py")
    if not ds.exists():
        logger.warning("Dataset not found at %s, using fallback", ds)
        return [{"id": f"BUG-{i:02d}", "question": "", "ground_truth": []} for i in range(1, 11)]
    spec = importlib.util.spec_from_file_location("benchmark_dataset", str(ds))
    if spec is None or spec.loader is None:
        return [{"id": f"BUG-{i:02d}", "question": "", "ground_truth": []} for i in range(1, 11)]
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return [
        {"id": b["id"], "question": b["question"], "ground_truth": b["ground_truth"]}
        for b in mod.BUGS
    ]


def run_deep_test_suite(
    corpus_path: str,
    bugs: Optional[list[dict]] = None,
    timeout: float = GRAFT_BUILD_TIMEOUT,
) -> DeepTestReport:
    """Point d'entrée principal : build deep, test ask lexical vs deep, rapport."""
    report = DeepTestReport(
        corpus_path=corpus_path,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )

    success, exit_code, stderr = run_graft_build_deep(corpus_path, timeout)
    report.build_success = success
    report.build_stderr = stderr
    if not success:
        logger.error("graft build --deep failed (exit=%d): %s", exit_code, stderr)
        return report

    if bugs is None:
        bugs = _load_default_bugs()

    lexical_runs, deep_runs = [], []
    for bug in bugs:
        bid, question, gt = bug["id"], bug["question"], bug["ground_truth"]
        ask_lex = run_graft_ask(question, corpus_path, deep=False)
        m_lex = compute_metrics(ask_lex.files, gt)
        lexical_runs.append(
            {
                "bug_id": bid,
                "files": ask_lex.files,
                "ground_truth": gt,
                "precision": m_lex.precision,
                "recall": m_lex.recall,
                "f1": m_lex.f1,
                "tp": m_lex.tp,
                "fp": m_lex.fp,
                "fn": m_lex.fn,
                "exit_code": ask_lex.exit_code,
            }
        )
        ask_deep = run_graft_ask(question, corpus_path, deep=True)
        m_deep = compute_metrics(ask_deep.files, gt)
        deep_runs.append(
            {
                "bug_id": bid,
                "files": ask_deep.files,
                "ground_truth": gt,
                "precision": m_deep.precision,
                "recall": m_deep.recall,
                "f1": m_deep.f1,
                "tp": m_deep.tp,
                "fp": m_deep.fp,
                "fn": m_deep.fn,
                "exit_code": ask_deep.exit_code,
            }
        )
        logger.info("%s — lexical R=%.3f | deep R=%.3f", bid, m_lex.recall, m_deep.recall)

    report.lexical_results = lexical_runs
    report.deep_results = deep_runs
    report.lexical_agg = _aggregate_metrics(lexical_runs)
    report.deep_agg = _aggregate_metrics(deep_runs)
    report.recall_delta = round((report.deep_agg.recall - report.lexical_agg.recall), 3)
    logger.info(
        "Final: lexical R=%.3f F1=%.3f | deep R=%.3f F1=%.3f | delta=%.3f",
        report.lexical_agg.recall,
        report.lexical_agg.f1,
        report.deep_agg.recall,
        report.deep_agg.f1,
        report.recall_delta,
    )
    return report


def format_report(report: DeepTestReport) -> str:
    """Formate le rapport en markdown lisible."""
    lines = [
        "# MLOOP-132-BE — Rapport Deep Build Test",
        "",
        f"**Corpus**: `{report.corpus_path}`",
        f"**Timestamp**: {report.timestamp}",
        f"**Build Deep**: {'OK' if report.build_success else 'FAILED'}",
    ]
    if report.build_stderr:
        lines.append(f"**Build STDERR**: {report.build_stderr[:500]}")
    if report.lexical_agg and report.deep_agg:
        lex_ok = sum(1 for r in report.lexical_results if r["exit_code"] == 0)
        deep_ok = sum(1 for r in report.deep_results if r.get("exit_code") == 0)
        n = len(report.lexical_results) or 1
        pd = round(report.deep_agg.precision - report.lexical_agg.precision, 3)
        fd = round(report.deep_agg.f1 - report.lexical_agg.f1, 3)
        lines.extend(
            [
                "",
                "## Agregats",
                "",
                "| Metrique | Lexical (no-graph) | Deep (graph) | Delta |",
                "|:---|:---:|:---:|:---:|",
                f"| Precision | {report.lexical_agg.precision} | {report.deep_agg.precision} | {pd} |",
                f"| **Recall** | {report.lexical_agg.recall} | **{report.deep_agg.recall}** | **{report.recall_delta}** |",
                f"| F1 | {report.lexical_agg.f1} | {report.deep_agg.f1} | {fd} |",
                f"| Success Rate | {lex_ok}/{n} | {deep_ok}/{n} | — |",
            ]
        )
    if report.deep_results:
        lines.extend(
            [
                "",
                "## Detail par Bug",
                "",
                "| Bug | Lexical R | Deep R | Deep Files |",
                "|:---|:---:|:---:|:---|",
            ]
        )
        for dr in report.deep_results:
            lex_r = next(
                (r["recall"] for r in report.lexical_results if r["bug_id"] == dr["bug_id"]), 0.0
            )
            fs = ", ".join(dr["files"][:3]) or "—"
            lines.append(f"| {dr['bug_id']} | {lex_r} | {dr['recall']} | {fs} |")
    lines.extend(["", "---", f"*Rapport genere le {report.timestamp}*"])
    return "\n".join(lines)
