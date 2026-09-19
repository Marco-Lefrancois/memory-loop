"""
Registre de compétences SEP-2640 — Protocole `skill://`

Implémente le standard d'exposition uniforme des fonctionnalités mLoop via
le namespace `skill://`. Tout module ou capacité exposée via ce registre
est découvrable et invocable de façon déterministe par les agents IA.

ADR : MLOOP-011-BE / EPIC-2-HYBRID-MEMORY
"""
from __future__ import annotations

import re
from typing import Any, Callable, Dict, Optional

# ─── Format d'URI accepté ────────────────────────────────────────────────────
_SKILL_URI_PATTERN = re.compile(r"^skill://(?P<name>[a-zA-Z0-9_\-]+)$")

# ─── Registre interne ────────────────────────────────────────────────────────
_skill_registry: Dict[str, Callable[..., Any]] = {}


class SkillNotFoundError(KeyError):
    """Levée lorsqu'une URI `skill://` ne correspond à aucune compétence enregistrée."""


class InvalidSkillURIError(ValueError):
    """Levée lorsque le format de l'URI `skill://` est invalide."""


# ─── API publique ─────────────────────────────────────────────────────────────

def register_skill(name: str, handler: Callable[..., Any]) -> None:
    """
    Enregistre une compétence dans le registre global.

    Args:
        name:    Identifiant de la compétence (ex: ``preload-context``).
        handler: Callable Python qui sera invoqué lors de la résolution.

    Raises:
        ValueError: Si ``name`` est vide ou contient des caractères non autorisés.
    """
    if not name or not re.match(r"^[a-zA-Z0-9_\-]+$", name):
        raise ValueError(
            f"[SEP-2640] Nom de compétence invalide : '{name}'. "
            "Seuls les caractères alphanumériques, tirets et underscores sont autorisés."
        )
    _skill_registry[name] = handler


def resolve_skill(uri: str) -> Callable[..., Any]:
    """
    Résout une URI ``skill://`` en son handler callable.
    Applique le bouclier de confinement au runtime (ADR-0379).

    Args:
        uri: URI au format ``skill://<name>`` (ex: ``skill://preload-context``).

    Returns:
        Le callable associé à la compétence.

    Raises:
        InvalidSkillURIError: Si l'URI n'est pas au bon format.
        SkillNotFoundError:   Si aucune compétence n'est enregistrée sous ce nom.
        PermissionDeniedError: Si l'agent actif n'est pas autorisé à invoquer cette compétence.
    """
    match = _SKILL_URI_PATTERN.match(uri)
    if not match:
        raise InvalidSkillURIError(
            f"[SEP-2640] URI invalide : '{uri}'. Format attendu : skill://<name>"
        )

    name = match.group("name")

    # ─── 1. Bouclier de Confinement Runtime (ADR-0379) ───────────────────────
    try:
        from src.core.confinement_shield import ConfinementShield
        ConfinementShield.verify_skill_access(name)
    except ImportError:
        pass

    if name not in _skill_registry:
        available = ", ".join(sorted(_skill_registry)) or "(registre vide)"
        raise SkillNotFoundError(
            f"[SEP-2640] Compétence introuvable : '{name}'. "
            f"Compétences disponibles : {available}"
        )

    return _skill_registry[name]


def invoke_skill(uri: str, *args: Any, **kwargs: Any) -> Any:
    """
    Résout et invoque une compétence en un seul appel.

    Args:
        uri:    URI ``skill://`` cible.
        *args:  Arguments positionnels transmis au handler.
        **kwargs: Arguments nommés transmis au handler.

    Returns:
        La valeur de retour du handler de la compétence.
    """
    handler = resolve_skill(uri)
    return handler(*args, **kwargs)


def get_skill_catalog() -> Dict[str, Dict[str, Any]]:
    """
    Retourne le catalogue complet des compétences découvertes dynamiquement
    depuis StandardsGraphStore (.agents/skills/*/SKILL.md) avec leurs métadonnées.
    """
    try:
        from src.core.standards_graph import StandardsGraphStore
        store = StandardsGraphStore.get_instance()
        skills = store.get_skills()
        return {
            name: {
                "name": s.name,
                "description": s.description,
                "category": s.category,
                "file_path": s.file_path,
                "inputs": s.inputs,
                "outputs": s.outputs,
                "runtime_handler": getattr(_skill_registry.get(name), "__qualname__", None),
            }
            for name, s in sorted(skills.items())
        }
    except Exception:
        return {}


def list_skills(include_catalog: bool = False) -> Dict[str, str]:
    """
    Retourne le catalogue des compétences enregistrées.

    Args:
        include_catalog: Si True, inclut également les compétences déclaratives
                         découvertes dans StandardsGraph (.agents/skills/).

    Returns:
        Dictionnaire ``{name: handler_qualname_or_description}``.
    """
    skills: Dict[str, str] = {
        name: getattr(handler, "__qualname__", repr(handler))
        for name, handler in sorted(_skill_registry.items())
    }
    if include_catalog:
        catalog = get_skill_catalog()
        for name, meta in catalog.items():
            if name not in skills:
                skills[name] = meta["description"] or f"skill://{name}"
    return skills


def unregister_skill(name: str) -> Optional[Callable[..., Any]]:
    """
    Supprime une compétence du registre (usage test uniquement).

    Args:
        name: Identifiant de la compétence à retirer.

    Returns:
        Le handler retiré, ou ``None`` si absent.
    """
    return _skill_registry.pop(name, None)


def clear_registry() -> None:
    """Vide intégralement le registre (usage test uniquement)."""
    _skill_registry.clear()
