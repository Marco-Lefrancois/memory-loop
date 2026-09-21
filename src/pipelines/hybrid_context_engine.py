"""Pipeline Séquentiel Hybride CodeGraph → Graft → Intersection (MLOOP-131-BE)."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional, Protocol, Tuple, Any

logger = logging.getLogger("hybrid_context")


class CodeGraphEngine(Protocol):
    def explore(self, query: str, project_path: Path, timeout: float = 30.0) -> Dict[str, Any]: ...


class GraftEngine(Protocol):
    def find_callers(
        self, symbols: List[str], project_path: Path, timeout: float = 30.0
    ) -> Dict[str, Any]: ...


@dataclass
class HybridResult:
    query: str
    mode: str  # "hybrid", "fallback_codegraph", "fallback_graft", "fallback_graft_to_codegraph"
    files: List[Dict[str, Any]] = field(default_factory=list)
    codegraph_count: int = 0
    graft_count: int = 0
    intersection_count: int = 0
    weights: Tuple[float, float] = (0.6, 0.4)
    elapsed_ms: float = 0.0
    warnings: List[str] = field(default_factory=list)
    graft_exit_code: Optional[int] = None
    fallback_triggered: bool = False


def _normalize_path(path: str) -> str:
    return path.replace("\\", "/").lower().strip()


def _compute_score(in_codegraph: bool, in_graft: bool, weights: Tuple[float, float]) -> float:
    w_cg, w_gr = weights
    score = 0.0
    if in_codegraph:
        score += w_cg
    if in_graft:
        score += w_gr
    return round(score, 4)


def _extract_files_from_codegraph(result: Dict[str, Any]) -> List[str]:
    files: List[str] = []
    for item in result.get("symbols", result.get("files", [])):
        if isinstance(item, dict):
            fp = item.get("file", item.get("path", ""))
            if fp:
                files.append(fp)
        elif isinstance(item, str):
            files.append(item)
    return files


def _extract_files_from_graft(result: Dict[str, Any]) -> List[str]:
    files: List[str] = []
    for item in result.get("callers", result.get("files", [])):
        if isinstance(item, dict):
            fp = item.get("file", item.get("path", ""))
            if fp:
                files.append(fp)
        elif isinstance(item, str):
            files.append(item)
    return files


def _extract_graft_exit_code(result: Dict[str, Any]) -> Optional[int]:
    return result.get("exit_code", result.get("returncode", None))


def _execute_codegraph_fallback(
    query: str,
    codegraph_fn: Callable[[str, Path, float], Dict[str, Any]],
    effective_path: Path,
    timeout: float,
    partial_graft_files: List[str],
) -> Tuple[List[str], List[str]]:
    """Exécute le fallback CodeGraph après échec Graft callers (MLOOP-133-BE)."""
    try:
        cg_result = codegraph_fn(query, effective_path, timeout)
        cg_files = _extract_files_from_codegraph(cg_result)
        all_files = list(partial_graft_files)
        new_cg_files = []
        graft_set = {_normalize_path(f) for f in partial_graft_files}
        for f in cg_files:
            if _normalize_path(f) not in graft_set:
                all_files.append(f)
                new_cg_files.append(f)
        return all_files, new_cg_files
    except Exception as exc:
        logger.warning(
            "[HybridContext] CodeGraph fallback failed: %s",
            exc,
            extra={"engine": "codegraph_fallback", "error": str(exc)},
        )
        return partial_graft_files, []


def hybrid_context_search(
    query: str,
    codegraph_fn: Optional[Callable[[str, Path, float], Dict[str, Any]]] = None,
    graft_fn: Optional[Callable[[str, Path, float], Dict[str, Any]]] = None,
    project_path: Optional[Path] = None,
    weights: Tuple[float, float] = (0.6, 0.4),
    timeout: float = 30.0,
) -> HybridResult:
    """Pipeline séquentiel hybride : CodeGraph → Graft → Intersection (MLOOP-131-BE)."""
    start = time.monotonic()
    result = HybridResult(query=query, mode="hybrid", weights=weights)
    effective_path = project_path or Path(".")

    if weights[0] + weights[1] > 1.01:
        result.warnings.append("Somme des poids > 1.0, normalisation appliquée")
        total = weights[0] + weights[1]
        weights = (weights[0] / total, weights[1] / total)
        result.weights = weights

    cg_files: List[str] = []
    gr_files: List[str] = []
    cg_available = codegraph_fn is not None
    gr_available = graft_fn is not None

    # Phase 1 : CodeGraph explore
    if cg_available and codegraph_fn is not None:
        try:
            cg_result = codegraph_fn(query, effective_path, timeout)
            cg_files = _extract_files_from_codegraph(cg_result)
            result.codegraph_count = len(cg_files)
            logger.info(
                "[HybridContext] CodeGraph返回 %d fichiers",
                len(cg_files),
                extra={"engine": "codegraph", "count": len(cg_files)},
            )
        except Exception as exc:
            cg_available = False
            result.warnings.append(f"CodeGraph indisponible: {exc}")
            logger.warning(
                "[HybridContext] CodeGraph indisponible: %s",
                exc,
                extra={"engine": "codegraph", "error": str(exc)},
            )

    # Phase 2 : Graft callers (si disponible)
    partial_graft_files: List[str] = []
    if gr_available and graft_fn is not None:
        try:
            gr_result = graft_fn(query, effective_path, timeout)
            gr_files = _extract_files_from_graft(gr_result)
            result.graft_count = len(gr_files)
            partial_graft_files = gr_files

            # Vérifier le code de retour (RM-133-01)
            exit_code = _extract_graft_exit_code(gr_result)
            result.graft_exit_code = exit_code

            if exit_code is not None and exit_code != 0:
                # Échec de Graft callers → fallback automatique vers CodeGraph
                result.fallback_triggered = True
                result.warnings.append(
                    f"Graft callers failed (exit={exit_code}), fallback to CodeGraph"
                )
                logger.warning(
                    "[HybridContext] Graft callers failed (exit=%d), fallback to CodeGraph",
                    exit_code,
                    extra={
                        "engine": "graft",
                        "exit_code": exit_code,
                        "fallback": "codegraph",
                        "partial_files": len(gr_files),
                    },
                )

                if cg_available and codegraph_fn is not None:
                    all_files, new_cg_files = _execute_codegraph_fallback(
                        query, codegraph_fn, effective_path, timeout, gr_files
                    )
                    gr_files = all_files
                    result.graft_count = len(gr_files)
                    result.codegraph_count = len(new_cg_files)
                    result.mode = "fallback_graft_to_codegraph"
                else:
                    result.mode = "fallback_graft_partial"
                    result.warnings.append("CodeGraph non disponible pour le fallback")
            else:
                logger.info(
                    "[HybridContext] Graft返回 %d fichiers",
                    len(gr_files),
                    extra={"engine": "graft", "count": len(gr_files)},
                )
        except Exception as exc:
            gr_available = False
            result.fallback_triggered = True
            result.warnings.append(f"Graft indisponible: {exc}")
            logger.warning(
                "[HybridContext] Graft indisponible: %s",
                exc,
                extra={"engine": "graft", "error": str(exc), "fallback": "codegraph"},
            )

            if cg_available and codegraph_fn is not None:
                all_files, new_cg_files = _execute_codegraph_fallback(
                    query, codegraph_fn, effective_path, timeout, []
                )
                gr_files = all_files
                result.graft_count = len(gr_files)
                result.codegraph_count = len(new_cg_files)
                result.mode = "fallback_graft_to_codegraph"

    # Phase 3 : Mode dégradé (si pas de fallback déjà déclenché)
    if not result.fallback_triggered:
        if not cg_available and not gr_available:
            result.mode = "fallback_none"
            result.warnings.append("Aucun moteur disponible")
            result.elapsed_ms = (time.monotonic() - start) * 1000
            return result

        if not gr_available:
            result.mode = "fallback_codegraph"
            result.warnings.append("Fallback CodeGraph seul (Graft indisponible)")
            scored = [{"file": f, "score": weights[0], "source": "codegraph"} for f in cg_files]
            result.files = scored
            result.elapsed_ms = (time.monotonic() - start) * 1000
            return result

        if not cg_available:
            result.mode = "fallback_graft"
            result.warnings.append("Fallback Graft seul (CodeGraph indisponible)")
            scored = [{"file": f, "score": weights[1], "source": "graft"} for f in gr_files]
            result.files = scored
            result.elapsed_ms = (time.monotonic() - start) * 1000
            return result

    # Phase 4 : Intersection hybride
    cg_set = {_normalize_path(f) for f in cg_files}
    gr_set = {_normalize_path(f) for f in gr_files}
    intersection = cg_set & gr_set
    result.intersection_count = len(intersection)

    scored_files: Dict[str, Dict[str, Any]] = {}
    for norm_path in intersection:
        original = next(
            (f for f in cg_files if _normalize_path(f) == norm_path),
            next((f for f in gr_files if _normalize_path(f) == norm_path), norm_path),
        )
        scored_files[norm_path] = {
            "file": original,
            "score": _compute_score(True, True, weights),
            "source": "intersection",
        }

    for f in cg_files:
        np = _normalize_path(f)
        if np not in scored_files:
            scored_files[np] = {
                "file": f,
                "score": _compute_score(True, False, weights),
                "source": "codegraph_only",
            }

    for f in gr_files:
        np = _normalize_path(f)
        if np not in scored_files:
            scored_files[np] = {
                "file": f,
                "score": _compute_score(False, True, weights),
                "source": "graft_only",
            }

    result.files = sorted(scored_files.values(), key=lambda x: x["score"], reverse=True)
    result.elapsed_ms = (time.monotonic() - start) * 1000

    logger.info(
        "[HybridContext] Pipeline hybride terminé: mode=%s, total=%d, intersection=%d",
        result.mode,
        len(result.files),
        result.intersection_count,
        extra={
            "mode": result.mode,
            "total_files": len(result.files),
            "intersection": result.intersection_count,
            "elapsed_ms": result.elapsed_ms,
        },
    )

    return result
