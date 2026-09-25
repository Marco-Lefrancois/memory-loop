"""
src/bridges/_mcp_skills_catalog.py — Catalogue & enveloppe SEP-2640 (MLOOP-214-BE).

Couche de données du pont ``skills/list`` | ``skills/get`` :

- **constant partagées** du schéma officiel `io.modelcontextprotocol/skills` ;
- **lecture de métadonnées locales** (frontmatter, origine distante, priorité
  déclarée, manifeste sha256/size) et construction de l'entrée `Skill` ;
- **résolution d'identifiant** (schéma local `skill://` seul) et recherche
  **uniquement** dans la découverte unique `mcp_resources.discover_skills()` ;
- **enveloppe de réponse** (``resultType`` / ``ttlMs`` / ``cacheScope`` / `_meta.mloop`).

Toute compétence déclarant une origine distante, dont le frontmatter est incomplet
ou dont le manifeste dépasse les limites est **écartée avec motif** (échec bloqué,
jamais de téléchargement tiers — conformité *Universal Dev Handoff*).

Aucune écriture disque ici : ce module est purement lecture/serialisation.
"""

from __future__ import annotations

import hashlib
import logging
import re
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

import yaml

from src.bridges import mcp_resources
from src.bridges._mcp_skills_rules import HIERARCHY, RuleConflict, conflicts_as_dicts

logger = logging.getLogger(__name__)

SKILLS_EXTENSION_ID = "io.modelcontextprotocol/skills"
SKILLS_LIST_METHOD = "skills/list"
SKILLS_GET_METHOD = "skills/get"
SKILLS_METHODS = frozenset({SKILLS_LIST_METHOD, SKILLS_GET_METHOD})
SKILL_URI_SCHEME = "skill://"
SKILL_MD = "SKILL.md"
URI_SUFFIX = "/SKILL.md"
TTL_MS = 300_000
CACHE_SCOPE = "public"
ERROR_INVALID_PARAMS = -32602
ERROR_INTERNAL = -32603
MAX_RESOURCES_PER_SKILL = 512
MAX_BYTES_PER_SKILL = 16 * 1024 * 1024
PRIORITY_KEYS = ("priorityHint", "priority_hint", "priority")
REQUIRED_FRONTMATTER = ("name", "description")
REMOTE_ORIGIN_KEYS = ("origin", "source", "repository", "repo", "url", "remote", "homepage")
_MISSING_LEGACY_PREFIX = "Compétence '"
_REMOTE_PATTERN = re.compile(r"^(?:https?|git|ssh|s?ftp|ftps)://|^git@", re.IGNORECASE)
_FRONTMATTER_PATTERN = re.compile(r"^---\s*\n(.*?)\n---\s*(?:\n|$)", re.DOTALL)


# ── Lecture de métadonnées locales ────────────────────────────────────────────


def skill_frontmatter(skill_md: Path) -> dict[str, Any]:
    """Frontmatter YAML de la ``SKILL.md`` (``{}`` si absent ou illisible)."""
    try:
        raw = skill_md.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        logger.debug(
            "skill_frontmatter_unreadable",
            exc_info=True,
            extra={
                "component": "bridges.mcp_skills",
                "operation": "skill_frontmatter",
                "path": str(skill_md),
                "error": str(exc),
            },
        )
        return {}
    match = _FRONTMATTER_PATTERN.match(raw)
    if not match:
        return {}
    try:
        loaded = yaml.safe_load(match.group(1))
    except yaml.YAMLError as exc:
        logger.debug(
            "skill_frontmatter_invalid_yaml",
            exc_info=True,
            extra={
                "component": "bridges.mcp_skills",
                "operation": "skill_frontmatter",
                "path": str(skill_md),
                "error": str(exc),
            },
        )
        return {}
    return loaded if isinstance(loaded, dict) else {}


def remote_origin(skill_dir: Path, frontmatter: Mapping[str, Any]) -> Optional[str]:
    """Origine distante déclarée dans le frontmatter, ou ``None`` si locale."""
    for key in REMOTE_ORIGIN_KEYS:
        value = frontmatter.get(key)
        if isinstance(value, str) and _REMOTE_PATTERN.search(value.strip()):
            return f"{key}={value.strip()}"
    return None


def _json_safe(value: Any) -> Any:
    """Frontmatter toujours serialisable en JSON (dates YAML → chaîne)."""
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def _priority_hint(frontmatter: Mapping[str, Any]) -> Any:
    """Indice de priorité **déclaré par l'auteur** — aucun n'est synthétisé."""
    for key in PRIORITY_KEYS:
        if key in frontmatter:
            return _json_safe(frontmatter[key])
    return None


def _manifest(skill_dir: Path, skill_name: str) -> tuple[Optional[list[dict]], Optional[str]]:
    """Manifeste complet ``{uri, digest, size}`` — ``None`` + motif au-delà des limites."""
    try:
        files = [path for path in skill_dir.rglob("*") if path.is_file()]
    except OSError as exc:
        logger.debug(
            "skill_directory_unreadable",
            exc_info=True,
            extra={
                "component": "bridges.mcp_skills",
                "operation": "_manifest",
                "path": str(skill_dir),
                "error": str(exc),
            },
        )
        return None, f"répertoire de compétence illisible : {exc}"
    if len(files) > MAX_RESOURCES_PER_SKILL:
        return None, f"manifeste au-delà de {MAX_RESOURCES_PER_SKILL} fichiers ({len(files)})"
    ordered = sorted(files, key=lambda path: (path.name != SKILL_MD, path.as_posix().lower()))
    resources: list[dict] = []
    total = 0
    for path in ordered:
        try:
            data = path.read_bytes()
        except OSError as exc:
            logger.debug(
                "skill_file_unreadable",
                exc_info=True,
                extra={
                    "component": "bridges.mcp_skills",
                    "operation": "_manifest",
                    "path": str(path),
                    "error": str(exc),
                },
            )
            return None, f"fichier de compétence illisible : {path.name}"
        total += len(data)
        if total > MAX_BYTES_PER_SKILL:
            return None, f"poids du manifeste au-delà de {MAX_BYTES_PER_SKILL} octets"
        relative = path.relative_to(skill_dir).as_posix().replace("\\", "/")
        resources.append(
            {
                "uri": f"{SKILL_URI_SCHEME}{skill_name}/{relative}",
                "digest": f"sha256:{hashlib.sha256(data).hexdigest()}",
                "size": len(data),
            }
        )
    return resources, None


def build_skill_entry(skill: Mapping[str, Any]) -> tuple[Optional[dict], Optional[str]]:
    """Entrée SEP-2640 d'une compétence découverte — ``None`` + motif si écartée."""
    name = str(skill["name"])
    skill_md = Path(skill["path"])
    frontmatter = skill_frontmatter(skill_md)
    origin = remote_origin(skill_md.parent, frontmatter)
    if origin:
        return None, f"source distante non approuvée ({origin}) : échec bloqué"
    missing = [key for key in REQUIRED_FRONTMATTER if not frontmatter.get(key)]
    if missing:
        return None, f"frontmatter incomplet (champs requis : {', '.join(missing)})"
    manifest, motif = _manifest(skill_md.parent, name)
    if manifest is None:
        return None, motif
    safe_frontmatter = {str(key): _json_safe(value) for key, value in frontmatter.items()}
    return (
        {
            "uri": f"{SKILL_URI_SCHEME}{name}/SKILL.md",
            "frontmatter": safe_frontmatter,
            "resources": manifest,
            "priorityHint": _priority_hint(frontmatter),
        },
        None,
    )


# ── Résolution d'identifiant & découverte unique ──────────────────────────────


def resolve_identifier(raw: str) -> tuple[Optional[str], Optional[str]]:
    """Nom de compétence local ou refus explicite (schéma distant / hors catalogue)."""
    value = raw.strip()
    if "://" in value:
        scheme, _, rest = value.partition("://")
        if scheme.lower() != "skill":
            return None, (
                f"Source distante ou schéma non approuvé '{scheme}://' : seules les "
                f"compétences découvertes localement sous {SKILL_URI_SCHEME} sont servies "
                "(sécurité par échec bloqué)."
            )
        path = rest.split("?", 1)[0].rstrip("/")
        if path.endswith(URI_SUFFIX):
            path = path[: -len(URI_SUFFIX)]
        if not path:
            return None, "Adresse skill:// sans nom de compétence : demande hors catalogue."
        if "/" in path:
            return None, (
                f"Préfixe de chemin non servi ({path}) : ce catalogue est plat "
                f"({SKILL_URI_SCHEME}<compétence>{URI_SUFFIX})."
            )
        return path, None
    name = value.strip("/")
    if not name:
        return None, "Nom de compétence vide : demande hors catalogue."
    if "/" in name:
        return None, f"Nom de compétence non plat non servi : {name}"
    return name, None


def lookup_skill(name: str) -> Optional[dict[str, Any]]:
    """Recherche **uniquement** dans la découverte locale (jamais de concaténation de chemin)."""
    for skill in mcp_resources.discover_skills():
        if skill["name"] == name:
            return skill
    return None


def entries_from_discovery(excluded: list[dict]) -> list[dict]:
    """Entrées SEP-2640 du catalogue local ; chaque écart est consigné dans ``excluded``."""
    entries: list[dict] = []
    for skill in mcp_resources.discover_skills():
        entry, motif = build_skill_entry(skill)
        if entry is None:
            excluded.append({"skill": skill["name"], "reason": motif})
            logger.debug(
                "skill_entry_excluded",
                extra={
                    "component": "bridges.mcp_skills",
                    "operation": "entries_from_discovery",
                    "skill": skill["name"],
                    "reason": motif,
                },
            )
            continue
        entries.append(entry)
    return entries


# ── Enveloppe de réponse (SEP-2640) ───────────────────────────────────────────


def error_response(
    req_id: Any, message: str, *, code: int = ERROR_INVALID_PARAMS
) -> dict[str, Any]:
    """Erreur JSON-RPC explicite (jamais un échec muet — ADR-0369)."""
    logger.debug(
        "skills_request_refused",
        extra={
            "component": "bridges.mcp_skills",
            "operation": "handle_skills",
            "code": code,
            "reason": message,
        },
    )
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}


def mloop_meta(
    bridge: str,
    conflicts: Sequence[RuleConflict] | None = None,
    excluded: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    """Métadonnées décisionnelles : voie servie, hiérarchie, arbitrage, écartements."""
    meta: dict[str, Any] = {
        "bridge": bridge,
        "hierarchy": list(HIERARCHY),
        "priorityOverride": False,
        "catalogue": "local-discovery",
    }
    if conflicts is not None:
        meta["ruleConflicts"] = conflicts_as_dicts(conflicts)
    if excluded:
        meta["excluded"] = [dict(item) for item in excluded]
    return meta


def list_result(
    entries: list[dict],
    *,
    bridge: str,
    excluded: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    """Enveloppe de ``skills/list`` (inventaire ``complete``)."""
    return {
        "resultType": "complete",
        "skills": entries,
        "ttlMs": TTL_MS,
        "cacheScope": CACHE_SCOPE,
        "_meta": {"mloop": mloop_meta(bridge, excluded=excluded)},
    }


def get_result(entry: dict, content: str, bridge: str, conflicts: Sequence[RuleConflict]) -> dict:
    """Enveloppe de ``skills/get`` : entrée SEP-2640 + ``content`` (contrat récit §2)."""
    return {
        "resultType": "complete",
        "skill": {**entry, "content": content},
        "ttlMs": TTL_MS,
        "cacheScope": CACHE_SCOPE,
        "_meta": {"mloop": mloop_meta(bridge, conflicts)},
    }


def response(req_id: Any, result: dict[str, Any]) -> dict[str, Any]:
    """Message JSON-RPC de succès."""
    return {"jsonrpc": "2.0", "id": req_id, "result": result}
