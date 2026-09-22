"""Handler Memo Search : ALMA Meta-Learned Memory Strategy Selection."""
from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Dict, Any

from src.cli import ZeroFluffConsole
from src.utils.logger import get_logger

logger = get_logger("handler.memo_search")

if TYPE_CHECKING:
    import argparse
    from src.state import LoopState


DEFAULT_MEMO_PROFILES: Dict[str, Dict[str, Any]] = {
    "trajectory_retrieval": {
        "profile_id": "trajectory_retrieval",
        "name": "Trajectory Retrieval Strategy",
        "description": "Optimisé pour l'intégration d'APIs, SDKs et WebView SSO. Privilégie la traçabilité des appels et des preuves.",
        "target_domains": ["cmp/onetrust", "sso", "api_reference"],
        "max_context_chunks": 8,
        "confidence_threshold": 0.85,
        "score": 0.94
    },
    "reasoning_bank": {
        "profile_id": "reasoning_bank",
        "name": "Reasoning Bank Strategy",
        "description": "Optimisé pour les règles d'affaires complexes et la modélisation de domaines (RM-XXX, INVEST).",
        "target_domains": ["business_rules", "invest", "gherkin"],
        "max_context_chunks": 12,
        "confidence_threshold": 0.90,
        "score": 0.91
    },
    "dynamic_cheatsheet": {
        "profile_id": "dynamic_cheatsheet",
        "name": "Dynamic Cheatsheet Strategy",
        "description": "Optimisé pour le refactoring, les migrations .NET MAUI et les corrections techniques ciblées.",
        "target_domains": ["architecture/dotnet", "refactoring", "bugfix"],
        "max_context_chunks": 5,
        "confidence_threshold": 0.80,
        "score": 0.88
    }
}


def _seed_memo_archive(archive_dir: Path) -> None:
    """Initialise les profils mémoire par défaut s'ils n'existent pas."""
    archive_dir.mkdir(parents=True, exist_ok=True)
    for p_id, p_data in DEFAULT_MEMO_PROFILES.items():
        p_file = archive_dir / f"{p_id}.json"
        if not p_file.exists():
            p_file.write_text(json.dumps(p_data, indent=2, ensure_ascii=False), encoding="utf-8")


def handle_memo_search(args: argparse.Namespace, state: LoopState, project_path: Path) -> int:
    """Recherche et applique le profil mémoire ALMA optimal pour le projet."""
    ZeroFluffConsole.section(f"ALMA Memo-Search Engine ({state.project_name})")

    project_archive = project_path / "memory" / "memo_archive"
    global_archive = Path("memory") / "memo_archive"

    _seed_memo_archive(project_archive)
    _seed_memo_archive(global_archive)

    query = getattr(args, "query", None)
    profiles = []

    for f in sorted(list(project_archive.glob("*.json")) + list(global_archive.glob("*.json"))):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            if data not in profiles:
                profiles.append(data)
        except Exception as e:
            logger.debug(
                "Profil ALMA illisible, ignoré",
                exc_info=True,
                extra={
                    "component": "commands.handlers.memo_search",
                    "operation": "search_memo_profiles",
                    "error": str(e),
                },
            )

    ZeroFluffConsole.info(f"Trouvé {len(profiles)} profil(s) de stratégie mémoire dans l'archive ALMA.")

    matched_profile = None
    if query:
        q_lower = query.lower()
        for p in profiles:
            targets = [t.lower() for t in p.get("target_domains", [])]
            if q_lower in p.get("profile_id", "") or q_lower in p.get("name", "").lower() or any(q_lower in t for t in targets):
                matched_profile = p
                break

    if not matched_profile and profiles:
        matched_profile = profiles[0]

    if matched_profile:
        ZeroFluffConsole.success(f"Profil Mémoire Sélectionné : {matched_profile.get('name')} (ID: {matched_profile.get('profile_id')})")
        ZeroFluffConsole.value("Description", matched_profile.get("description"))
        ZeroFluffConsole.value("Score ALMA", f"{matched_profile.get('score', 0.9):.2f}")
        ZeroFluffConsole.value("Limites Chunks", matched_profile.get("max_context_chunks"))

        active_file = project_path / "memory" / "active_memo_profile.json"
        active_file.write_text(json.dumps(matched_profile, indent=2, ensure_ascii=False), encoding="utf-8")
        ZeroFluffConsole.info(f"Profil actif sauvegardé dans : {active_file.relative_to(project_path)}")

    return 0
