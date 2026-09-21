"""
MLOOP-135-BE — Benchmark Multi-Dépôts (small/medium/large).
Protocole CodeGraph sur 3 dépôts + rapport de scalabilité.
"""

from __future__ import annotations

import json
import logging
import re
import subprocess
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)
_HERE = Path(__file__).parent
SCRATCH = _HERE.parent.parent / "scratch" / "multi-repo-benchmark"
RESULTS = SCRATCH / "results"
SEED = 42


def _load_datasets():
    with open(_HERE / "multi_repo_datasets.json", encoding="utf-8") as f:
        raw = json.load(f)
    repos = {}
    for key, d in raw.items():
        repos[key] = {
            "name": d["name"],
            "url": d["url"],
            "commit": d["commit"],
            "size": d["size"],
            "files": d["files"],
            "bugs": d["bugs"],
        }
    return repos


_RAW = _load_datasets()
ALL = {}
for _size_label in ("small", "medium", "large"):
    for _d in _RAW.values():
        if _d["size"] == _size_label:
            ALL[_size_label] = _d
            break


def _shell(cmd, cwd, timeout=30):
    t0 = time.perf_counter()
    try:
        r = subprocess.run(
            ["powershell", "-NoProfile", "-Command", cmd],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="replace",
        )
        return r.stdout, r.stderr, round(time.perf_counter() - t0, 3), r.returncode
    except subprocess.TimeoutExpired:
        return "", "TIMEOUT", float(timeout), -1


def _extract(text):
    return sorted(set(re.findall(r"(?:src/|tests/|httpx/|flask/)\S+\.py", text)))


def _pr(found, gt):
    fs, gs = set(found), set(gt)
    if not gs:
        return {"precision": 0, "recall": 0, "f1": 0, "tp": 0, "fp": len(fs), "fn": 0}
    tp = len(fs & gs)
    p = tp / len(fs) if fs else 0
    r = tp / len(gs)
    f1 = 2 * p * r / (p + r) if (p + r) else 0
    return {
        "precision": round(p, 3),
        "recall": round(r, 3),
        "f1": round(f1, 3),
        "tp": tp,
        "fp": len(fs - gs),
        "fn": len(gs - fs),
    }


def _clone(url, commit, dst, timeout=120):
    if dst.exists():
        return True
    dst.mkdir(parents=True, exist_ok=True)
    _, err, _, ec = _shell(f"git clone {url} .", str(dst), timeout)
    if ec != 0:
        logger.error("Clone %s: %s", url, err[:200])
        return False
    _shell(f"git checkout {commit}", str(dst))
    return True


def _init_cg(d, timeout=60):
    _, err, _, ec = _shell("npx codegraph init", str(d), timeout)
    return ec == 0


def _bench_bug(bug, corpus):
    gt, sym = bug["gt"], bug.get("sym", "")
    q = bug["q"].replace('"', '\\"')
    out, err, lat, ec = _shell(f'npx codegraph explore "{q}"', str(corpus))
    ef = _extract(out + err)
    res = {"bug": bug["id"], "explore": {"files": ef, "lat": lat, "exit": ec, **_pr(ef, gt)}}
    if sym:
        o2, e2, l2, ec2 = _shell(f'npx codegraph callers "{sym}"', str(corpus))
        cf = _extract(o2 + e2)
        res["callers"] = {"files": cf, "lat": l2, "exit": ec2, **_pr(cf, gt)}
    else:
        res["callers"] = {"files": [], "lat": 0, "exit": -1, **_pr([], gt)}
    logger.info(
        "[%s] explore R=%.3f callers R=%.3f",
        bug["id"],
        res["explore"]["recall"],
        res["callers"]["recall"],
    )
    return res


def _agg(runs):
    a = {}
    for eng in ("explore", "callers"):
        rs = [r[eng] for r in runs if eng in r]
        n = len(rs)
        if not n:
            continue
        a[eng] = {
            k: round(sum(x[k] for x in rs) / n, 3) for k in ("precision", "recall", "f1", "lat")
        }
        a[eng]["success_rate"] = round(sum(1 for x in rs if x["exit"] == 0) / n, 3)
    return a


def _report(all_r):
    L = [
        f"# MLOOP-135-BE — Scalabilité Multi-Dépôts\n\n**Date** {time.strftime('%Y-%m-%d %H:%M')} | **Seed** {SEED}\n",
        "## 1. Dépôts\n| Nom | Taille | Fichiers | Bugs |\n|:---|:---|:---:|:---:|",
    ]
    for c in ALL.values():
        L.append(f"| `{c['name']}` | {c['size']} | {c['files']} | {len(c['bugs'])} |")
    L += ["\n## 2. Résultats\n"]
    for lbl, res in all_r.items():
        cfg = ALL[lbl]
        a = res.get("aggregated", {})
        L.append(f"### {cfg['name']} ({cfg['size']}, {cfg['files']}f)\n")
        if not a:
            L.append("*Échec*\n")
            continue
        L += ["| Moteur | P | R | F1 | Lat(s) | Fiab |\n|:---|:---:|:---:|:---:|:---:|:---:|"]
        for e, m in a.items():
            L.append(
                f"| {e} | {m['precision']:.3f} | {m['recall']:.3f} "
                f"| {m['f1']:.3f} | {m['lat']:.3f} | {m['success_rate'] * 100:.0f}% |"
            )
        L.append("")
    L += ["\n## 3. Tendances\n| Métrique | S | M | L |\n|:---|:---:|:---:|:---:|"]
    for k in ("recall", "f1", "lat"):
        vs = {
            l: all_r.get(l, {}).get("aggregated", {}).get("explore", {}).get(k, 0)
            for l in ("small", "medium", "large")
        }
        L.append(f"| {k} | {vs['small']:.3f} | {vs['medium']:.3f} | {vs['large']:.3f} |")
    return "\n".join(L)


def run_multi_repo_benchmark(repo_labels=None, skip_clone=False, timeout_per_bug=30):
    SCRATCH.mkdir(parents=True, exist_ok=True)
    RESULTS.mkdir(parents=True, exist_ok=True)
    labels = repo_labels or list(ALL.keys())
    out = {}
    for lbl in labels:
        cfg = ALL[lbl]
        corp = SCRATCH / f"corpus-{lbl}"
        logger.info("=== %s: %s (%df) ===", lbl.upper(), cfg["name"], cfg["files"])
        if not skip_clone and not (corp / ".git").exists():
            if not _clone(cfg["url"], cfg["commit"], corp):
                out[lbl] = {"error": "clone_failed", "aggregated": {}}
                continue
        if not (corp / ".codegraph").exists():
            _init_cg(corp)
        runs = [_bench_bug(b, corp) for b in cfg["bugs"]]
        out[lbl] = {
            "config": {"name": cfg["name"], "size": cfg["files"]},
            "runs": runs,
            "aggregated": _agg(runs),
        }
    rpt = _report(out)
    (RESULTS / "multi_repo_results.json").write_text(
        json.dumps(out, indent=2, default=str), encoding="utf-8"
    )
    (RESULTS / "scalability_report.md").write_text(rpt, encoding="utf-8")
    return {"results": out, "report": str(RESULTS / "scalability_report.md")}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    r = run_multi_repo_benchmark()
    print(f"\nRapport: {r['report']}")
