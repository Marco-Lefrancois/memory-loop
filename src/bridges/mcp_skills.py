"""
src/bridges/mcp_skills.py — Extension officielle Skills over MCP (MLOOP-214-BE).

Pont à double pile permanent vers le catalogue de compétences du framework :

- **voie moderne** ``skills/list`` / ``skills/get`` — servie au client qui déclare
  ``capabilities.extensions["io.modelcontextprotocol/skills"]`` ;
- **voie historique** — inventaire dérivé de ``resources/list`` et lecture déléguée
  à l'outil ``read_skill``, déjà en service et servie à tout client qui ne déclare
  pas l'espace de noms (le repli n'est jamais un échec).

Les deux voies passent par la découverte unique ``mcp_resources.discover_skills()`` :
un seul catalogue, aucun code mort, aucune seconde maintenance.

**Contrat SEP-2640** (spécification vérifiée le 2026-09-24 — OQ-214-01 résolue,
*conformité confirmée*) : entrée ``Skill {uri, frontmatter, resources}``, enveloppe
``{resultType: "complete", ttlMs, cacheScope}``, refus ``-32602`` pour une
compétence non servie, ``resources/directory/read`` non déclaré (``directoryRead``
absent de l'annonce serveur, ``{}`` = support sans option).

**Écarts consignés sans bloquer** (sur-ensembles non brisants) :
1. ``skills/get`` ajoute le champ ``content`` — le récit §2 impose le contenu
   intégral du fichier sous ce contrat de chargement ;
2. chaque entrée porte ``priorityHint`` — l'indice de priorité informatif du
   récit §1, déclaré par l'auteur (`priority` / `priority_hint`) ou ``null``,
   **jamais synthétisé** et sans autorité d'override.

**Sécurité par échec bloqué** : seul le schéma local ``skill://`` est servi ;
tout schéma distant (``https://``, ``github://``, ``git@``…) ou toute compétence
déclarant une origine distante dans son frontmatter est refusé, sans écriture.
"""

from __future__ import annotations

import hashlib
import logging
import re
import time
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

import yaml

from src.bridges import mcp_resources, mcp_tools
from src.bridges._mcp_protocol_core import register_known_method
from src.bridges._mcp_skills_rules import (
    HIERARCHY,
    RuleConflict,
    arbitrate_skill,
    conflicts_as_dicts,
    find_conflicts,
)

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
_REMOTE_PATTERN = re.compile(r"^(?:https?|git|ssh|s?ftp|ftps)://|^git@", re.IGNORECASE)
_FRONTMATTER_PATTERN = re.compile(r"^---\s*\n(.*?)\n---\s*(?:\n|$)", re.DOTALL)
_DIGEST_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")
_MISSING_LEGACY_PREFIX = "Compétence '"

# Couture 214 : les méthodes doivent figurer au registre pour être acheminées.
register_known_method(SKILLS_LIST_METHOD)
register_known_method(SKILLS_GET_METHOD)

_CLIENT_DECLARES = False


# ── Négociation de capacité (état de session, symétrique à mcp_ui) ───────────


def reset_skills_state() -> None:
    """Remet à zéro la négociation (appelée avant chaque note de capacité)."""
    global _CLIENT_DECLARES
    _CLIENT_DECLARES = False


def note_client_capabilities(capabilities: Any) -> None:
    """Note la déclaration de l'espace de noms par le client (absence = voie historique)."""
    global _CLIENT_DECLARES
    declared = False
    if isinstance(capabilities, Mapping):
        extensions = capabilities.get("extensions")
        if isinstance(extensions, Mapping):
            declared = SKILLS_EXTENSION_ID in extensions
    _CLIENT_DECLARES = declared
    logger.debug(
        "skills_capability_negotiated",
        extra={
            "component": "bridges.mcp_skills",
            "operation": "note_client_capabilities",
            "declared": _CLIENT_DECLARES,
        },
    )


def client_supports_skills() -> bool:
    """True uniquement si le client a déclaré l'extension officielle."""
    return _CLIENT_DECLARES


def skills_server_capabilities() -> dict[str, Any]:
    """Annonce serveur : support sans ``directoryRead`` (objet vide, SEP-2640)."""
    return {SKILLS_EXTENSION_ID: {}}


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


# ── Résolution d'identifiant & catalogue ──────────────────────────────────────


def _resolve_identifier(raw: str) -> tuple[Optional[str], Optional[str]]:
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
            return (
                None,
                "Adresse skill:// sans nom de compétence : demande hors des deux voies du pont.",
            )
        if "/" in path:
            return None, (
                f"Préfixe de chemin non servi ({path}) : ce catalogue est plat "
                f"({SKILL_URI_SCHEME}<compétence>{URI_SUFFIX})."
            )
        return path, None
    name = value.strip("/")
    if not name:
        return None, "Nom de compétence vide : demande hors des deux voies du pont."
    if "/" in name:
        return None, f"Nom de compétence non plat non servi : {name}"
    return name, None


def _lookup(name: str) -> Optional[dict[str, Any]]:
    """Recherche **uniquement** dans la découverte locale (jamais de concaténation de chemin)."""
    for skill in mcp_resources.discover_skills():
        if skill["name"] == name:
            return skill
    return None


def _error(req_id: Any, message: str, *, code: int = ERROR_INVALID_PARAMS) -> dict[str, Any]:
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


def _mloop_meta(
    bridge: str,
    conflicts: Sequence[RuleConflict] | None = None,
    excluded: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
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


def _list_result(
    entries: list[dict],
    *,
    bridge: str,
    excluded: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    return {
        "resultType": "complete",
        "skills": entries,
        "ttlMs": TTL_MS,
        "cacheScope": CACHE_SCOPE,
        "_meta": {"mloop": _mloop_meta(bridge, excluded=excluded)},
    }


def _get_result(entry: dict, content: str, bridge: str, conflicts: Sequence[RuleConflict]) -> dict:
    return {
        "resultType": "complete",
        "skill": {**entry, "content": content},
        "ttlMs": TTL_MS,
        "cacheScope": CACHE_SCOPE,
        "_meta": {"mloop": _mloop_meta(bridge, conflicts)},
    }


def _response(req_id: Any, result: dict[str, Any]) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": req_id, "result": result}


# ── Voie moderne ──────────────────────────────────────────────────────────────


def _entries_from_discovery(excluded: list[dict]) -> list[dict]:
    entries: list[dict] = []
    for skill in mcp_resources.discover_skills():
        entry, motif = build_skill_entry(skill)
        if entry is None:
            excluded.append({"skill": skill["name"], "reason": motif})
            logger.debug(
                "skill_entry_excluded",
                extra={
                    "component": "bridges.mcp_skills",
                    "operation": "_entries_from_discovery",
                    "skill": skill["name"],
                    "reason": motif,
                },
            )
            continue
        entries.append(entry)
    return entries


def _modern_list(req_id: Any) -> dict[str, Any]:
    excluded: list[dict] = []
    entries = _entries_from_discovery(excluded)
    logger.debug(
        "skills_list_served",
        extra={
            "component": "bridges.mcp_skills",
            "operation": "handle_skills_list",
            "bridge": "namespace",
            "count": len(entries),
            "excluded": len(excluded),
        },
    )
    return _response(req_id, _list_result(entries, bridge="namespace", excluded=excluded))


def _read_content(skill_md: Path, name: str) -> tuple[Optional[str], Optional[str]]:
    started = time.perf_counter()
    try:
        content = skill_md.read_text(encoding="utf-8")
    except OSError as exc:
        logger.debug(
            "skill_content_unreadable",
            exc_info=True,
            extra={
                "component": "bridges.mcp_skills",
                "operation": "_read_content",
                "path": str(skill_md),
                "error": str(exc),
            },
        )
        return None, f"Compétence '{name}' illisible : {exc}"
    elapsed_ms = (time.perf_counter() - started) * 1000
    logger.debug(
        "skill_content_loaded",
        extra={
            "component": "bridges.mcp_skills",
            "operation": "_read_content",
            "skill": name,
            "bridge": "namespace",
            "elapsed_ms": round(elapsed_ms, 3),
            "bytes": len(content.encode("utf-8")),
        },
    )
    return content, None


def _modern_get(req_id: Any, name: str) -> dict[str, Any]:
    skill = _lookup(name)
    if skill is None:
        return _error(
            req_id,
            f"Aucune compétence n'est servie à {SKILL_URI_SCHEME}{name}{URI_SUFFIX} "
            "(découverte locale uniquement).",
        )
    entry, motif = build_skill_entry(skill)
    if entry is None:
        return _error(req_id, motif or f"Compétence '{name}' écartée.")
    content, motif = _read_content(Path(skill["path"]), name)
    if content is None:
        return _error(req_id, motif or "Lecture impossible.", code=ERROR_INTERNAL)
    conflicts = arbitrate_skill(name, content, bridge="namespace")
    return _response(req_id, _get_result(entry, content, "namespace", conflicts))


# ── Voie historique (repli du pont à double pile) ─────────────────────────────


def _historical_records(req_id: Any) -> dict[str, dict[str, Any]]:
    """Inventaire littéral de l'exposition ``skill://`` déjà en service."""
    response = mcp_resources.handle_resources_list(req_id)
    records: dict[str, dict[str, Any]] = {}
    for resource in response.get("result", {}).get("resources", []):
        uri = str(resource.get("uri", ""))
        if uri.startswith(SKILL_URI_SCHEME):
            records[uri[len(SKILL_URI_SCHEME) :]] = resource
    return records


def _legacy_list(req_id: Any) -> dict[str, Any]:
    records = _historical_records(req_id)
    excluded: list[dict] = []
    entries: list[dict] = []
    for name in records:
        skill = _lookup(name)
        if skill is None:
            excluded.append({"skill": name, "reason": "hors découverte locale"})
            continue
        entry, motif = build_skill_entry(skill)
        if entry is None:
            excluded.append({"skill": name, "reason": motif})
            continue
        entries.append(entry)
    logger.debug(
        "skills_list_served",
        extra={
            "component": "bridges.mcp_skills",
            "operation": "handle_skills_list",
            "bridge": "legacy",
            "count": len(entries),
            "excluded": len(excluded),
        },
    )
    return _response(req_id, _list_result(entries, bridge="legacy", excluded=excluded))


def _legacy_get(req_id: Any, name: str) -> dict[str, Any]:
    records = _historical_records(req_id)
    if name not in records:
        return _error(
            req_id,
            f"Compétence '{name}' absente de l'exposition historique "
            f"({SKILL_URI_SCHEME}{name}{URI_SUFFIX} non servie).",
        )
    skill = _lookup(name)
    if skill is None:
        return _error(req_id, f"Compétence '{name}' hors découverte locale.")
    content = mcp_tools.execute_read_skill({"skill_name": name})
    if not content or (
        content.startswith(_MISSING_LEGACY_PREFIX) and "introuvable" in content[:200]
    ):
        return _error(req_id, f"Compétence '{name}' introuvable sur l'outil de lecture historique.")
    entry, motif = build_skill_entry(skill)
    if entry is None:
        return _error(req_id, motif or f"Compétence '{name}' écartée.")
    # L'outil historique journalise déjà le conflit : ici, seul le verdict est calculé.
    conflicts = find_conflicts(name, content)
    return _response(req_id, _get_result(entry, content, "legacy", conflicts))


# ── Point d'entrée du pont ────────────────────────────────────────────────────


def handle_skills_list(req_id: Any, params: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Inventaire typé : voie moderne si déclarée, repli historique sinon."""
    del params  # signature SEP-2640 (pagination non requise par le récit)
    if client_supports_skills():
        return _modern_list(req_id)
    return _legacy_list(req_id)


def handle_skills_get(req_id: Any, params: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Chargement à la volée d'une compétence, avec arbitrage d'autorité."""
    source = params if isinstance(params, Mapping) else {}
    raw = source.get("uri") or source.get("name") or source.get("skill_name")
    if not isinstance(raw, str) or not raw.strip():
        return _error(
            req_id,
            "skills/get exige params.uri (skill://<compétence>/SKILL.md) : "
            "demande hors des deux voies du pont à double pile.",
        )
    name, motif = _resolve_identifier(raw)
    if name is None or motif:
        return _error(req_id, motif or "Identifiant de compétence invalide.")
    if client_supports_skills():
        return _modern_get(req_id, name)
    return _legacy_get(req_id, name)


def dispatch(method: str, req_id: Any, params: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Route ``skills/list`` / ``skills/get`` ; tout autre objet est refusé."""
    if method == SKILLS_LIST_METHOD:
        return handle_skills_list(req_id, params)
    if method == SKILLS_GET_METHOD:
        return handle_skills_get(req_id, params)
    return _error(req_id, f"Objet hors pont à double pile : '{method}' (skills/list | skills/get).")
