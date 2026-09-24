"""
Extracteur de citations verbatim ancrées depuis le diff git (MLOOP-181-BE / CA-4).

Granularité hybride D : 1 citation par fichier réellement modifié, ancrage
[start, end] réel calculé depuis les hunks du diff (-U0). Résilience :
fichier supprimé -> alerte 'source_deleted' ; deadline dépassée ->
sous-ensemble déterministe + alerte 'extraction_truncated' (ADR-0369).
"""
from __future__ import annotations

import json
import re
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from src.utils.logger import get_logger

logger = get_logger("core.citation_extractor")


class CitationExtractionError(RuntimeError):
    """Timeout ou échec lors de l'extraction des citations depuis le diff git."""


class CitationExtractor:
    """Extraction hybride D des verbatim_extracts depuis le diff git."""

    def __init__(self, project_path: Path) -> None:
        self.project_path = Path(project_path).resolve()

    def _changed_files_with_status(self, timeout: float) -> List[Tuple[str, str]]:
        """
        Liste déterministe des fichiers modifiés (dernier commit + worktree non commité).

        Returns:
            Liste triée de tuples (chemin_relatif, statut_git) — statut M/A/D.

        Raises:
            CitationExtractionError: si git échoue hors d'un dépôt valide.
        """
        hunk_map: Dict[str, str] = {}
        for cmd in (["git", "diff", "--name-status", "HEAD~1", "HEAD"],
                    ["git", "diff", "--name-status", "HEAD"]):
            try:
                res = subprocess.run(
                    cmd,
                    cwd=self.project_path,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                )
            except subprocess.TimeoutExpired as e:
                raise CitationExtractionError(
                    f"[MLOOP-181-BE] git diff dépassé le timeout de {timeout}s (ADR-0369)."
                ) from e
            # HEAD~1 absent (dépôt à 1 commit) → toléré, on garde le diff worktree.
            if res.returncode != 0 and "HEAD~1" not in cmd:
                raise CitationExtractionError(
                    f"[MLOOP-181-BE] Échec git diff (exit {res.returncode}) : "
                    f"{res.stderr.strip()[:200]}"
                )
            for line in res.stdout.splitlines():
                parts = line.strip().split("\t", 1)
                if len(parts) == 2 and parts[0] and parts[1]:
                    hunk_map[parts[1].replace('"', "")] = parts[0]
        return sorted(hunk_map.items())

    def _added_line_ranges(self, rel_path: str, timeout: float) -> List[Tuple[int, int]]:
        """Ranges [start, end] des lignes ajoutées dans le nouveau fichier (diff -U0)."""
        ranges: List[Tuple[int, int]] = []
        for cmd in (["git", "diff", "-U0", "HEAD~1", "HEAD", "--", rel_path],
                    ["git", "diff", "-U0", "HEAD", "--", rel_path]):
            try:
                res = subprocess.run(
                    cmd, cwd=self.project_path, capture_output=True, text=True, timeout=timeout
                )
            except subprocess.TimeoutExpired as e:
                raise CitationExtractionError(
                    f"[MLOOP-181-BE] git diff -U0 dépassé le timeout de {timeout}s."
                ) from e
            if res.returncode != 0:
                continue
            for m in re.finditer(r"@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@", res.stdout):
                start = int(m.group(1))
                count = int(m.group(2)) if m.group(2) is not None else 1
                if count > 0:
                    ranges.append((start, start + count - 1))
            if ranges:
                break
        return ranges

    def _extract_file_citation(
        self, rel_path: str, timeout: float
    ) -> Optional[Dict[str, Any]]:
        """Construit un VerbatimExtract ancré depuis un fichier modifié existant."""
        target = self.project_path / rel_path
        if not target.is_file():
            return None
        try:
            with open(target, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
        except OSError as e:
            logger.debug(
                "Lecture du fichier modifié impossible, citation skippée",
                exc_info=True,
                extra={
                    "component": "core.citation_extractor",
                    "operation": "_extract_file_citation",
                    "source_file": rel_path,
                    "error": str(e),
                },
            )
            return None
        if not lines:
            return None

        ranges = self._added_line_ranges(rel_path, timeout)
        if ranges:
            start, end = ranges[0]
        else:
            start, end = 1, min(10, len(lines))
        start = max(1, start)
        end = min(end, len(lines))
        if start > end:
            start, end = 1, min(10, len(lines))
        quote = "".join(lines[start - 1 : end]).rstrip("\n")
        if not quote.strip():
            return None
        return {
            "source_file": rel_path.replace("\\", "/"),
            "lines": [start, end],
            "quote": quote,
            "established_fact": (
                f"Code modifié verbatim extrait du diff git build MLOOP-181-BE ({rel_path})."
            ),
        }

    def extract_citations_from_diff(
        self,
        story_id: str,
        timeout: float = 30.0,
        max_files: int = 20,
        return_warnings: bool = False,
        evidence_path: Optional[Path] = None,
    ):
        """
        Extraction hybride D (CA-4) : 1 citation/fichier modifié, ancrage [start, end] réel.

        Résilience : fichier supprimé -> alerte 'source_deleted' et poursuite ;
        deadline dépassée -> sous-ensemble déterministe + alerte 'extraction_truncated'.

        Raises:
            CitationExtractionError: si git lui-même échoue (dépôt invalide, timeout subprocess).
        """
        warnings: List[Dict[str, Any]] = []
        changed = self._changed_files_with_status(timeout=timeout)
        truncated = len(changed) > max_files
        extracts: List[Dict[str, Any]] = []
        deadline = time.monotonic() + timeout

        for rel_path, status in changed[:max_files]:
            if time.monotonic() > deadline:
                warnings.append(
                    {"alert": "extraction_truncated", "detail": "deadline dépassée (ADR-0369)"}
                )
                logger.debug(
                    "extraction_truncated: deadline dépassée, sous-ensemble déterministe conservé",
                    extra={
                        "component": "core.citation_extractor",
                        "operation": "extract_citations_from_diff",
                        "story_id": story_id,
                        "processed": len(extracts),
                        "total_changed": len(changed),
                    },
                )
                break
            if status in ("D", "DELETED") or not (self.project_path / rel_path).exists():
                warnings.append({"alert": "source_deleted", "source": rel_path})
                continue
            extract = self._extract_file_citation(rel_path, timeout=timeout)
            if extract:
                extracts.append(extract)

        if truncated and not any(w["alert"] == "extraction_truncated" for w in warnings):
            warnings.append(
                {
                    "alert": "extraction_truncated",
                    "detail": f"{len(changed)} fichiers modifiés, {max_files} traités (max_files)",
                }
            )

        if evidence_path is not None and extracts:
            data = self._load_pack(evidence_path)
            existing = data.setdefault("verbatim_extracts", [])
            seen = {json.dumps(e, sort_keys=True) for e in existing}
            for ext in extracts:
                key = json.dumps(ext, sort_keys=True)
                if key not in seen:
                    existing.append(ext)
                    seen.add(key)
            if warnings:
                data.setdefault("alerts", []).extend(warnings)
            self._save_pack(evidence_path, data)

        return (extracts, warnings) if return_warnings else extracts

    def _load_pack(self, evidence_path: Path) -> Dict[str, Any]:
        """Charge le pack existant ou crée une structure minimale (résilience)."""
        if evidence_path.exists():
            try:
                with open(evidence_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.debug(
                    "EvidencePack illisible, régénération d'une structure minimale",
                    exc_info=True,
                    extra={
                        "component": "core.citation_extractor",
                        "operation": "_load_pack",
                        "path": str(evidence_path),
                        "error": str(e),
                    },
                )
        return {"implementation_decisions": [], "declarative_contracts": [], "alerts": []}

    def _save_pack(self, evidence_path: Path, data: Dict[str, Any]) -> None:
        evidence_path.parent.mkdir(parents=True, exist_ok=True)
        with open(evidence_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
