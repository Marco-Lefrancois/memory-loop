"""
Primitives partagees Jira Sync (MLOOP-142-BE / ADR-0202 decoupage modulaire).

Regroupe les constantes de securite, le parsing des cles cibles, la verification
du manifeste SHA-256 Fail-Closed et le routage d'erreurs instrumente
(LoggingConsole + logger structure ADR-0369) consommes par `export_story.py`.
Isole de la surface handler pour maintenir chaque module sous 300 lignes (ADR-0202).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any, List

from src.cli import LoggingConsole
from src.utils.logger import get_logger

logger = get_logger("handler.export_story")

if TYPE_CHECKING:
    import argparse

# ─── Constantes de sécurité ───────────────────────────────────────────────────
_TEMP_KEY_PREFIX = "TEMP-"
_BLOCKED_STATUSES_WITHOUT_FLAG = {"OPEN", "IN_ANALYZE"}


def _log_jira_err(msg: str, state: Any = None, **ctx: Any) -> None:
    """Route une erreur jira_sync vers LoggingConsole.error avec contexte standardise (MLOOP-142-BE)."""
    LoggingConsole.error(
        msg, command="jira_sync", project=getattr(state, "project_name", None), **ctx
    )


def _parse_target_keys(args: "argparse.Namespace") -> List[str]:
    """Retourne la liste normalisée des clés cibles à partir de --story ou --stories."""
    keys: List[str] = []
    if getattr(args, "story", None):
        keys.append(args.story.strip())
    if getattr(args, "stories", None):
        for k in args.stories.split(","):
            k = k.strip()
            if k:
                keys.append(k)
    # Dédupliquer en préservant l'ordre
    seen = set()
    result = []
    for k in keys:
        if k not in seen:
            seen.add(k)
            result.append(k)
    return result


def _verify_sha256_manifest(preview: dict, project_path: Path) -> bool:
    """
    Vérifie que les SHA-256 du manifeste preview correspondent aux fichiers actuels.
    Retourne True si tout est conforme (ou si aucun manifeste n'existe = premier run).
    Écrit le manifeste après vérification.
    """
    import hashlib

    manifest_path = project_path / "memory" / "sync" / "jira_sync_preview.json"

    # Si le manifeste existe, comparer
    if manifest_path.exists():
        try:
            saved = json.loads(manifest_path.read_text(encoding="utf-8"))
            saved_hashes = saved.get("file_hashes", {})
            for file_path_str, saved_hash in saved_hashes.items():
                fp = Path(file_path_str)
                if fp.exists():
                    current_hash = hashlib.sha256(fp.read_bytes()).hexdigest()
                    if current_hash != saved_hash:
                        return False
        except Exception as e:
            # Manifeste corrompu → on laisse passer (premier run effectif)
            logger.debug(
                "Lecture du manifeste SHA-256 existant echouee (non-bloquant, traite comme premier run).",
                exc_info=True,
                extra={
                    "command": "jira_sync",
                    "phase": "sha256_manifest_read",
                    "target_keys": str(manifest_path),
                    "error": str(e),
                },
            )

    # Écrire le nouveau manifeste
    try:
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(
            json.dumps(preview, indent=2, ensure_ascii=False), encoding="utf-8"
        )
    except Exception as e:
        logger.debug(
            "Ecriture du nouveau manifeste SHA-256 echouee (non-bloquant).",
            exc_info=True,
            extra={
                "command": "jira_sync",
                "phase": "sha256_manifest_write",
                "target_keys": str(manifest_path),
                "error": str(e),
            },
        )

    return True
