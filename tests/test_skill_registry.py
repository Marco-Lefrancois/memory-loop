"""
Tests unitaires — Registre de compétences SEP-2640 (MLOOP-011-BE).

Couvre les 4 piliers Gherkin du récit :
1. Nominal    : Exposition et résolution correcte via skill://.
2. Exceptions : URI invalide, compétence introuvable, nom malformé.
3. Résilience : Registre vide, double enregistrement, clear/unregister.
4. UX (Observabilité) : list_skills() retourne un catalogue lisible.
"""
from __future__ import annotations

import pytest

from src.core.skill_registry import (
    InvalidSkillURIError,
    SkillNotFoundError,
    clear_registry,
    invoke_skill,
    list_skills,
    register_skill,
    resolve_skill,
    unregister_skill,
)


# ─── Fixture : isoler chaque test ────────────────────────────────────────────

@pytest.fixture(autouse=True)
def _clean_registry():
    """Vide le registre avant et après chaque test pour garantir l'isolation."""
    clear_registry()
    yield
    clear_registry()


# ─── Pilier 1 : Nominal ───────────────────────────────────────────────────────

def test_register_and_resolve_nominal():
    """Une compétence enregistrée est résolvable via skill://."""
    register_skill("preload-context", lambda: "ok")
    handler = resolve_skill("skill://preload-context")
    assert callable(handler)
    assert handler() == "ok"


def test_invoke_skill_nominal():
    """invoke_skill() appelle le handler et retourne sa valeur."""
    register_skill("echo", lambda x: f"echo:{x}")
    result = invoke_skill("skill://echo", "hello")
    assert result == "echo:hello"


def test_register_multiple_skills():
    """Plusieurs compétences peuvent coexister dans le registre."""
    register_skill("alpha", lambda: "alpha")
    register_skill("beta", lambda: "beta")
    assert resolve_skill("skill://alpha")() == "alpha"
    assert resolve_skill("skill://beta")() == "beta"


def test_overwrite_skill():
    """Un second register_skill sur le même nom écrase silencieusement le précédent."""
    register_skill("ping", lambda: "v1")
    register_skill("ping", lambda: "v2")
    assert resolve_skill("skill://ping")() == "v2"


# ─── Pilier 2 : Exceptions ────────────────────────────────────────────────────

def test_resolve_unknown_skill_raises():
    """SkillNotFoundError si l'URI est valide mais la compétence absente."""
    with pytest.raises(SkillNotFoundError, match="introuvable"):
        resolve_skill("skill://inexistant")


def test_invalid_uri_format_raises():
    """InvalidSkillURIError si l'URI n'est pas au format skill://."""
    with pytest.raises(InvalidSkillURIError, match="URI invalide"):
        resolve_skill("http://wrong-protocol")


def test_invalid_uri_empty_raises():
    """InvalidSkillURIError si l'URI est vide."""
    with pytest.raises(InvalidSkillURIError):
        resolve_skill("")


def test_invalid_uri_no_name_raises():
    """InvalidSkillURIError si l'URI est 'skill://' sans nom."""
    with pytest.raises(InvalidSkillURIError):
        resolve_skill("skill://")


def test_register_invalid_name_raises():
    """ValueError si le nom de la compétence contient des caractères interdits."""
    with pytest.raises(ValueError, match="invalide"):
        register_skill("invalid name!", lambda: None)


def test_register_empty_name_raises():
    """ValueError si le nom de la compétence est une chaîne vide."""
    with pytest.raises(ValueError, match="invalide"):
        register_skill("", lambda: None)


def test_invoke_unknown_skill_raises():
    """invoke_skill() propage SkillNotFoundError si la compétence est absente."""
    with pytest.raises(SkillNotFoundError):
        invoke_skill("skill://ghost")


# ─── Pilier 3 : Résilience ────────────────────────────────────────────────────

def test_resolve_on_empty_registry():
    """Le registre vide retourne le message 'registre vide' dans l'erreur."""
    with pytest.raises(SkillNotFoundError, match="registre vide"):
        resolve_skill("skill://any")


def test_unregister_removes_skill():
    """unregister_skill() supprime la compétence du registre."""
    register_skill("temp", lambda: None)
    unregister_skill("temp")
    with pytest.raises(SkillNotFoundError):
        resolve_skill("skill://temp")


def test_unregister_nonexistent_returns_none():
    """unregister_skill() retourne None si la compétence n'existe pas (pas d'exception)."""
    result = unregister_skill("ghost")
    assert result is None


def test_clear_registry_empties_all():
    """clear_registry() vide l'intégralité du registre."""
    register_skill("a", lambda: None)
    register_skill("b", lambda: None)
    clear_registry()
    assert list_skills() == {}


def test_skill_with_kwargs():
    """Les arguments nommés sont correctement transmis au handler."""
    register_skill("add", lambda x, y: x + y)
    result = invoke_skill("skill://add", x=3, y=4)
    assert result == 7


# ─── Pilier 4 : UX / Observabilité ───────────────────────────────────────────

def test_list_skills_empty():
    """list_skills() retourne un dict vide si le registre est vide."""
    assert list_skills() == {}


def test_list_skills_returns_catalogue():
    """list_skills() retourne un catalogue trié avec les qualnames des handlers."""
    def my_handler():
        pass

    register_skill("zeta", my_handler)
    register_skill("alpha", my_handler)
    catalogue = list_skills()

    assert "alpha" in catalogue
    assert "zeta" in catalogue
    # Trié alphabétiquement
    assert list(catalogue.keys()) == sorted(catalogue.keys())


def test_list_skills_shows_qualname():
    """list_skills() expose le __qualname__ du callable pour l'observabilité."""
    def observable_handler():
        pass

    register_skill("obs", observable_handler)
    catalogue = list_skills()
    assert "observable_handler" in catalogue["obs"]
