"""
Garde-fou anti-aggravation RULE-AST-01-DELTA (MLOOP-171-BE / OQ-171-02).

Regle :
  - Fichier deja > 300L OU > 15Ko en HEAD : accepter seulement si
      staged_lines <= head_lines ET staged_bytes <= head_bytes.
    Rejeter si l'un des deux croit (depassement aggrave).
  - Fichier conforme en HEAD (ou nouveau fichier stage) : comportement standard :
    rejeter si staged_lines > 300 OU staged_bytes > 15360.

Comparaison deterministe :
  - staged_lines  : comptage physique du fichier working-tree (readlines).
  - staged_bytes  : taille disque stat().st_size (octets UTF-8 on-disk).
  - head_lines    : len(head_content.splitlines())  -- contenu retourne par git show.
  - head_bytes    : len(head_content.encode("utf-8", errors="replace"))
                    -> homogene avec le contenu git (pas avec st_size qui inclut BOM/CRLF).
  Pour eviter la comparaison heterogene, on compare staged_lines vs head_lines
  et staged_bytes vs head_bytes (bytes git-encoded), les deux independamment.
  Un commit est autorise ssi NI les lignes NI les octets n'ont augmente.

Standards ADR-0369 appliques :
  - Timeouts explicites sur tout subprocess.run.
  - Context managers sur tout acces fichier.
  - Pas d'except silencieux nu.
  - Typage structurel via Protocol pour le collaborateur git.
"""

from __future__ import annotations

import logging
import os
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Protocol

logger = logging.getLogger("pipelines.ast_delta_checker")

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------
MAX_LINES: int = 300
MAX_BYTES: int = 15_360  # 15 Ko
_AUDIT_LOG_REL: str = "Projects/mLoop/memory/evidence/mloop_skip_hooks_audit.log"
_GIT_TIMEOUT: int = 30  # secondes (ADR-0369 Standard 3)


# ---------------------------------------------------------------------------
# Protocole d'injection (ADR-0369 Standard 1 — typage structurel)
# ---------------------------------------------------------------------------
class GitRunner(Protocol):
    """Abstraction du sous-processus Git ; injectable pour les tests."""

    def show_head(self, filepath: str, root: Path) -> Optional[str]:
        """Retourne le contenu HEAD du fichier ou None si introuvable/nouveau."""
        ...


# ---------------------------------------------------------------------------
# Implementation production
# ---------------------------------------------------------------------------
class DefaultGitRunner:
    """Implementation reelle avec subprocess timeout explicite (ADR-0369)."""

    def show_head(self, filepath: str, root: Path) -> Optional[str]:
        try:
            result = subprocess.run(
                ["git", "show", f"HEAD:{filepath}"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                cwd=str(root),
                timeout=_GIT_TIMEOUT,
            )
            if result.returncode != 0:
                return None  # fichier nouveau, pas encore en HEAD
            return result.stdout
        except FileNotFoundError:
            logger.debug(
                "git introuvable — impossible de recuperer HEAD:%s",
                filepath,
                extra={"filepath": filepath},
            )
            return None
        except subprocess.TimeoutExpired:
            logger.debug(
                "Timeout git show HEAD:%s (>%ss)",
                filepath,
                _GIT_TIMEOUT,
                extra={"filepath": filepath},
            )
            return None
        except Exception:
            logger.debug(
                "Erreur inattendue git show HEAD:%s",
                filepath,
                exc_info=True,
                extra={"filepath": filepath},
            )
            return None


# ---------------------------------------------------------------------------
# Resultat
# ---------------------------------------------------------------------------
@dataclass
class DeltaResult:
    """Resultat de l'analyse RULE-AST-01-DELTA pour un fichier stage."""

    filepath: str
    head_lines: Optional[int]  # None si fichier nouveau (absent de HEAD)
    staged_lines: int
    head_bytes: Optional[int]  # None si fichier nouveau
    staged_bytes: int  # octets git-encodes (homogene avec head_bytes)
    is_already_oversized: bool  # True si HEAD etait deja > 300L ou > 15Ko
    delta_ok: bool  # True = commit autorise
    violation_reason: Optional[str]  # Non-None si rejete
    method: str = "ast_line_count"


# ---------------------------------------------------------------------------
# Logique principale
# ---------------------------------------------------------------------------
def check_staged_file_delta(
    staged_path: Path,
    git_root: Path,
    git_runner: Optional[GitRunner] = None,
) -> DeltaResult:
    """
    Verifie si le fichier stage respecte RULE-AST-01-DELTA.

    Parameters
    ----------
    staged_path : chemin absolu du fichier dans le working-tree.
    git_root    : racine du depot Git.
    git_runner  : collaborateur Git injectable (production = DefaultGitRunner).

    Returns
    -------
    DeltaResult.delta_ok == True  → commit autorise.
    DeltaResult.delta_ok == False → commit a rejeter.
    """
    if git_runner is None:
        git_runner = DefaultGitRunner()

    # Chemin relatif POSIX pour git show HEAD:<path>
    try:
        rel_path = staged_path.relative_to(git_root).as_posix()
    except ValueError:
        rel_path = staged_path.as_posix()

    # ── Metriques du fichier stage (working-tree) ───────────────────────────
    with open(staged_path, "r", encoding="utf-8", errors="replace") as fh:
        staged_content = fh.read()
    staged_lines = len(staged_content.splitlines())
    # On re-encode pour etre homogene avec head_bytes (tous deux = UTF-8 encode)
    staged_bytes = len(staged_content.encode("utf-8", errors="replace"))

    # ── Metriques HEAD ──────────────────────────────────────────────────────
    head_content = git_runner.show_head(rel_path, git_root)
    if head_content is None:
        head_lines: Optional[int] = None
        head_bytes: Optional[int] = None
        is_already_oversized = False
    else:
        head_lines = len(head_content.splitlines())
        head_bytes = len(head_content.encode("utf-8", errors="replace"))
        is_already_oversized = head_lines > MAX_LINES or head_bytes > MAX_BYTES

    # ── Decision delta ──────────────────────────────────────────────────────
    violation_reason: Optional[str] = None

    if is_already_oversized:
        # Fichier deja en depassement : autoriser uniquement si neutre ou reducteur
        lines_grew = staged_lines > (head_lines or 0)
        bytes_grew = staged_bytes > (head_bytes or 0)
        if lines_grew or bytes_grew:
            parts: list[str] = []
            if lines_grew:
                diff = staged_lines - (head_lines or 0)
                parts.append(f"lignes {head_lines} → {staged_lines} (+{diff})")
            if bytes_grew:
                diff_b = staged_bytes - (head_bytes or 0)
                parts.append(f"octets {head_bytes} → {staged_bytes} (+{diff_b})")
            violation_reason = (
                f"[RULE-AST-01-DELTA] {rel_path} est deja en depassement "
                f"et a grossi : {', '.join(parts)}. "
                "Reduisez ce fichier avant de commiter, "
                "ou utilisez MLOOP_SKIP_HOOKS=1 (urgence souveraine)."
            )
    else:
        # Fichier conforme en HEAD (ou nouveau) : comportement standard
        if staged_lines > MAX_LINES or staged_bytes > MAX_BYTES:
            parts = []
            if staged_lines > MAX_LINES:
                parts.append(f"{staged_lines} lignes > {MAX_LINES}")
            if staged_bytes > MAX_BYTES:
                parts.append(f"{staged_bytes} octets > {MAX_BYTES}")
            violation_reason = (
                f"[RULE-AST-01] {rel_path} depasse le plafond modulaire : "
                f"{', '.join(parts)} (ADR-0202)."
            )

    return DeltaResult(
        filepath=rel_path,
        head_lines=head_lines,
        staged_lines=staged_lines,
        head_bytes=head_bytes,
        staged_bytes=staged_bytes,
        is_already_oversized=is_already_oversized,
        delta_ok=violation_reason is None,
        violation_reason=violation_reason,
    )


# ---------------------------------------------------------------------------
# Audit MLOOP_SKIP_HOOKS (OQ-171-02)
# ---------------------------------------------------------------------------
def record_skip_hooks_audit(framework_root: Path) -> None:
    """
    Append une ligne horodatee dans mloop_skip_hooks_audit.log
    quand MLOOP_SKIP_HOOKS est actif.

    Format : <ISO-8601-UTC> | <user> | MLOOP_SKIP_HOOKS=1 | reason=<raison>

    ADR-0369 : context manager obligatoire, pas d'except silencieux.
    """
    skip_val = os.environ.get("MLOOP_SKIP_HOOKS", "").strip().lower()
    if skip_val not in ("1", "true", "yes"):
        return

    audit_path = framework_root / _AUDIT_LOG_REL
    audit_path.parent.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(tz=timezone.utc).isoformat(timespec="seconds")
    user = os.environ.get("USER", "") or os.environ.get("USERNAME", "unknown")
    reason = os.environ.get("MLOOP_SKIP_HOOKS_REASON", "").strip() or "(aucune raison fournie)"
    line = f"{timestamp} | {user} | MLOOP_SKIP_HOOKS=1 | reason={reason}\n"

    try:
        with open(audit_path, "a", encoding="utf-8") as fh:
            fh.write(line)
    except OSError:
        logger.debug(
            "Impossible d'ecrire l'audit dans %s",
            audit_path,
            exc_info=True,
            extra={"audit_path": str(audit_path)},
        )


# ---------------------------------------------------------------------------
# Point d'entree CLI (appele par le hook shell : python -m src.pipelines.ast_delta_checker <file>)
# ---------------------------------------------------------------------------
def main() -> int:
    """
    Usage : python -m src.pipelines.ast_delta_checker <fichier_stage>
    Retourne 0 si autorise, 1 si rejete, 2 si erreur d'usage.
    """
    import sys

    if len(sys.argv) < 2:
        print(
            "Usage: python -m src.pipelines.ast_delta_checker <fichier>",
            file=sys.stderr,
        )
        return 2

    staged = Path(sys.argv[1]).resolve()
    if not staged.exists():
        print(f"[DELTA] Fichier introuvable : {staged}", file=sys.stderr)
        return 1

    # Remonter jusqu'a la racine Git
    git_root = staged.parent
    for _ in range(20):
        if (git_root / ".git").exists():
            break
        parent = git_root.parent
        if parent == git_root:
            git_root = Path.cwd()
            break
        git_root = parent

    result = check_staged_file_delta(staged, git_root)
    if not result.delta_ok:
        print(result.violation_reason, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
