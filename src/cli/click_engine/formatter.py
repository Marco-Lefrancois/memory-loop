"""
Aide CLI structurée par phases souveraines & assistants de typage (MLOOP-193-BE).

Module du moteur Click mLoop (EPIC-19 — étape 3b) — ADR-0202 (≤ 300L),
ADR-0369 (standards Python senior), ADR-0370 (SSOT CLI sans dérive).
Interne CLI, aucune route HTTP (ADR-0319).

Symboles publics (contrat d'import de la mission) :
  - ``PhaseHelpFormatter`` : sous-classe ``click.HelpFormatter`` instanciée via
    ``ctx.formatter_class`` ; expose ``write_phase_commands()`` qui écrit les
    sections de phases (en-tête en gras = Pilier 4, alignement = ``write_dl``).
  - ``path_exists(file_okay=True, dir_okay=False, exists=True)`` : type Click
    validant l'existence au parsing (CA-3 → exit 2 avant handler) et castant en
    ``pathlib.Path`` (CA-4).
  - ``dir_exists()`` : variante répertoire (``file_okay=False, dir_okay=True``).
  - ``choice_param(enum_or_list)`` : ``click.Choice`` insensible à la casse
    (CA-5) — valeurs listées dans l'aide, invalide rejetée en exit 2.
  - ``install_phase_help(cls)`` : branche ``format_commands`` + ``get_help`` sur
    le groupe racine sans réécrire ``router.py`` (MLOOP-191-BE intact, diff
    minimale compatible travail parallèle MLOOP-192-BE).
  - ``phase_of(name)`` : phase d'un id ou d'un alias (repli Pilier 3 → transverse).

SSOT de classification (zéro dérive ADR-0370) : ``src/pipelines/guide_data.py``
(``PHASE_MAPPING`` + ``PHASE_HEADERS``) — les mêmes structures que celles qui
compilent ``standards/protocols/CLI_PIPELINE_GUIDE.md`` (``guide --sync``) :
``--help`` et le guide SSOT partagent la taxonomie par construction. Les alias
(``jira-sync``, ``ui``, ``timeline``…) héritent de la phase de leur id canonique.
Règle Pilier 3 : toute commande absente de ``PHASE_MAPPING`` tombe sous
« Utilitaires transverses », sans exception levée — même code path que
``guide_generator.py`` (``PHASE_MAPPING.get(cname, "transverse")``).
"""

from __future__ import annotations

import enum
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Any

import click

from src.commands._registry import COMMANDS
from src.pipelines.guide_data import PHASE_HEADERS, PHASE_MAPPING

__all__ = [
    "PhaseHelpFormatter",
    "choice_param",
    "dir_exists",
    "format_phase_commands",
    "install_phase_help",
    "path_exists",
    "phase_of",
]

# Ordre des sections = ordre d'insertion de PHASE_HEADERS (parité guide_generator).
_PHASE_ORDER: tuple[str, ...] = tuple(PHASE_HEADERS)
_TRANSVERSE = "transverse"
# CA-2 / Pilier 3 : libellé littéral du récit (le document SSOT garde son intitulé
# « Commandes Transverses » ; la classification, elle, reste strictement guide_data).
_TRANSVERSE_TITLE = "⚙️ Utilitaires transverses (Observabilité, Mémoire, Tokens, Skills & Runtime)"


def _alias_id(command_name: str) -> str:
    """Id canonique d'un alias officiel du registre (sinon le nom lui-même)."""
    if command_name in COMMANDS:
        return command_name
    for canonical, definition in COMMANDS.items():
        if command_name in (definition.get("aliases") or ()):
            return canonical
    return command_name


def phase_of(command_name: str) -> str:
    """Clé de phase (``sow``…``transverse``) d'un id ou d'un alias — SSOT guide_data.

    Repli Pilier 3 (zéro exception) : id non classifié (commande fraîchement
    ajoutée, alias inconnu) → ``transverse``.
    """
    return PHASE_MAPPING.get(_alias_id(command_name), _TRANSVERSE)


def _phase_rows(
    group: Any, ctx: click.Context, formatter: click.HelpFormatter
) -> list[tuple[str, list[tuple[str, str]]]]:
    """Regroupe les commandes visibles par phase : ``[(titre, [(nom, aide)])]``."""
    entries_by_phase: dict[str, list[tuple[str, click.Command]]] = {}
    for name in group.list_commands(ctx):
        cmd = group.get_command(ctx, name)
        if cmd is None or cmd.hidden:
            continue
        entries_by_phase.setdefault(phase_of(name), []).append((name, cmd))
    order = [key for key in _PHASE_ORDER if entries_by_phase.get(key)]
    order += [key for key in entries_by_phase if key not in _PHASE_ORDER]
    rows: list[tuple[str, list[tuple[str, str]]]] = []
    for key in order:
        entries = entries_by_phase[key]
        # Parité Group.format_commands : largeur de colonne d'aide déduite du nom le plus long.
        limit = formatter.width - 6 - max(len(name) for name, _ in entries)
        title = _TRANSVERSE_TITLE if key == _TRANSVERSE else _title(key)
        rows.append((title, [(name, cmd.get_short_help_str(limit)) for name, cmd in entries]))
    return rows


def _title(phase_key: str) -> str:
    """Titre de phase du SSOT ``PHASE_HEADERS`` (repli : clé brute, zéro KeyError)."""
    return str((PHASE_HEADERS.get(phase_key) or {}).get("title", phase_key))


def _write_phase_sections(
    formatter: click.HelpFormatter, rows: Sequence[tuple[str, Sequence[tuple[str, str]]]]
) -> None:
    """Écrit chaque phase : paragraph + heading en gras + table alignée (``write_dl``)."""
    for title, phase_rows in rows:
        if not phase_rows:
            continue
        with formatter.section(click.style(title, bold=True)):
            formatter.write_dl(list(phase_rows))


class PhaseHelpFormatter(click.HelpFormatter):
    """HelpFormatter mLoop : sections de phases (CA-1) + en-têtes en gras (Pilier 4).

    Instanciée par ``ctx.formatter_class`` (voir :func:`install_phase_help`).
    ``click.echo`` retire les codes ANSI hors TTY : le rendu pipé (tests, CI)
    reste strictement identique au format de base, seul le terminal colorie.
    """

    def write_phase_commands(self, rows: Sequence[tuple[str, Sequence[tuple[str, str]]]]) -> None:
        """Écrit les sections de phases dans ce formatter (API de ``format_commands``)."""
        _write_phase_sections(self, rows)


def format_phase_commands(self: Any, ctx: click.Context, formatter: click.HelpFormatter) -> None:
    """Surcharge de ``Group.format_commands`` (assignée par :func:`install_phase_help`).

    Regroupe les 126 noms de surface (121 ids + 5 alias) sous les 6 phases
    souveraines puis sous « Utilitaires transverses » (CA-1/CA-2). Zéro import
    de handler : ``get_command`` n'instancie que le ``click.Command`` déclaratif
    (la non-lenteur CA-2 de MLOOP-191-BE reste donc garantie).
    """
    rows = _phase_rows(self, ctx, formatter)
    if isinstance(formatter, PhaseHelpFormatter):
        formatter.write_phase_commands(rows)
    else:
        _write_phase_sections(formatter, rows)  # repli : même rendu, API HelpFormatter de base


def install_phase_help(command_cls: type) -> None:
    """Branche l'aide par phases sur le groupe racine (CA-1 → CA-6).

    Choix technique documenté : **assignation externe plutôt que sous-classement**.
    ``router.py`` (livrable MLOOP-191-BE, fichier partagé avec MLOOP-192-BE) ne
    reçoit qu'un import + un appel en fin de fichier (235L → ~239L, ≤ 300L) :
    la classe ``MLoopMultiCommand``, son ``invoke`` et ``ArgsShim`` restent intacts.

    Deux points de branche :
      1. ``format_commands`` → :func:`format_phase_commands` (CA-1/CA-2, Pilier 3).
      2. ``get_help`` → ``ctx.formatter_class = PhaseHelpFormatter`` (Pilier 4).
    """
    command_cls.format_commands = format_phase_commands  # type: ignore[method-assign]
    base_get_help = command_cls.get_help

    def _get_help(self: Any, ctx: click.Context) -> str:
        ctx.formatter_class = PhaseHelpFormatter  # type: ignore[attr-defined]
        return base_get_help(self, ctx)  # type: ignore[arg-type]

    command_cls.get_help = _get_help  # type: ignore[method-assign]


def path_exists(file_okay: bool = True, dir_okay: bool = False, exists: bool = True) -> click.Path:
    """Type Click validant l'existence au parsing et retournant un ``pathlib.Path``.

    CA-3 : Click interrompt **avant** le handler avec
    ``Invalid value for '--input': Path '<chemin>' does not exist.`` (exit 2).
    CA-4 : le handler reçoit une instance native ``pathlib.Path``.
    """
    return click.Path(exists=exists, file_okay=file_okay, dir_okay=dir_okay, path_type=Path)


def dir_exists() -> click.Path:
    """Type Click validant l'existence d'un RÉPERTOIRE (retour ``pathlib.Path``)."""
    return click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path)


def choice_param(enum_or_list: type[enum.Enum] | Iterable[Any]) -> click.Choice:
    """``click.Choice`` insensible à la casse pour un Enum ou une séquence (CA-5).

    Les valeurs autorisées apparaissent dans l'aide (``[a|b|c]``) ; toute valeur
    hors liste est rejetée au parsing avec le code de sortie 2.
    """
    if isinstance(enum_or_list, type) and issubclass(enum_or_list, enum.Enum):
        values = [str(member.value) for member in enum_or_list]
    else:
        values = [str(value) for value in enum_or_list]
    return click.Choice(values, case_sensitive=False)
