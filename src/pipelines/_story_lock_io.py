# -*- coding: utf-8 -*-
"""
I/O et parsing des récits pour le verrou anti-promotion (MLOOP-270-BE / ADR-011).

Module de support extrait de `story_status_lock.py` — même logique que
l'extraction prévue de `_struct_c13.py` : isoler les helpers volumineux d'une
logique métier pour respecter le plafond ADR-0202 (≤300 lignes / ≤15 Ko par
fichier) sans comprimer la lecture du code.

Fournit :
  - la résolution déterministe des fichiers de récit (`resolve_story_file`) ;
  - le parse tolérant et la variante résiliente du frontmatter YAML ;
  - l'écriture chirurgicale d'une seule ligne de frontmatter (`write_field`) ;
  - la transaction « écriture récit + journal » à rollback (`commit_with_rollback`) ;
  - le chemin du verrou inter-processus et les constantes d'exemption ;
  - les aides de refus (`require_approval`) et de signalement (`make_issue`).
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict

import yaml

from src.core.transition_journal import append_entry, build_entry
from src.pipelines.state_machine import StateTransitionError
from src.state import StoryStatus
from src.utils.logger import get_logger

logger = get_logger("pipelines.story_lock_io")

# Verrou inter-processus unique couvrant récit + journal d'un projet.
LOCK_FILENAME = ".story_status.lock"

# Champs frontmatter qui prouvent une approbation humaine.
# Seul écrivain : `story-approve` (apply_human_approval).
APPROVAL_KEYS = ("validated_by", "validated_at")

# Exemption terminale — motif exact de `scratch_prune.py` L155 : un récit livré
# n'est jamais rétrogradé et n'est jamais bloquant pour un contrôle.
TERMINAL_STATUSES = frozenset(
    {"DONE_TESTED", "SHIPPED", "DONE", "ACCEPTED", "QA_CERTIFIED", "READY_TO_SHIP"}
)

# Ré « engagés » : membres du tuple `gated_statuses` de
# `StateMachineEngine.validate_fact_dossier_gate()` (state_machine.py).
# La FSM n'est PAS un ordre total — ON_HOLD et ERROR sont accessibles et
# quittables depuis presque tous les états. Aucune comparaison ">" ou ">=" n'est
# donc valide : seule l'appartenance à cet ensemble distingue un récit engagé
# d'un récit encore en création.
GATED_STATUSES = frozenset(
    {"READY_FOR_DEV", "READY_FOR_GROOMING", "IN_DEV", "READY_FOR_QA", "IN_QA", "QA_CERTIFIED"}
)

# Motif consigné dans toute entrée de sanction (`origin: sanction`).
SANCTION_REASON = "raw_promotion_without_human_approval"

# Détection du frontmatter YAML (4 variantes tolérées dans le codebase) et
# reconnaissance des scalaires YAML purs (non quotés).
_FM_RE = re.compile(r"^---[ \t]*\n(.*?)\n---[ \t]*\n", re.DOTALL)
_PLAIN = re.compile(r"[A-Za-z0-9_]+")


def lock_path(project: Path) -> Path:
    """Chemin du verrou inter-processus du projet (`memory/.story_status.lock`)."""
    return Path(project) / "memory" / LOCK_FILENAME


def stories_root(project: Path) -> Path:
    """Racine des récits du projet (`backlog/stories/`)."""
    return Path(project) / "backlog" / "stories"


def parse_frontmatter(text: str) -> Dict[str, Any]:
    """Parse tolérant du frontmatter (split en repli) — {} si absent ou YAML invalide."""
    match = _FM_RE.match(text)
    if match:
        raw = match.group(1)
    elif text.startswith("---") and len(text.split("---", 2)) >= 3:
        raw = text.split("---", 2)[1]
    else:
        return {}
    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError:
        logger.debug(
            "Frontmatter YAML illisible — dict vide retourné",
            exc_info=True,
            extra={"snippet": raw[:120]},
        )
        return {}
    return data if isinstance(data, dict) else {}


def read_frontmatter(path: Path) -> Dict[str, Any]:
    """Lit et parse le frontmatter d'un récit. Propage OSError/UnicodeDecodeError."""
    return parse_frontmatter(path.read_text(encoding="utf-8"))


def safe_frontmatter(path: Path) -> Dict[str, Any]:
    """Variante résiliente destinée aux scans project-wide.

    Un récit illisible n'interrompt jamais un scan : l'échec est journalisé en
    DEBUG avec `exc_info=True` (ADR-0369 — zéro silent-pass) puis le fichier est
    écarté. Aucune purge, aucune interruption.
    """
    try:
        return read_frontmatter(path)
    except (OSError, UnicodeDecodeError):
        logger.debug(
            "Lecture d'un récit impossible — fichier ignoré",
            exc_info=True,
            extra={"file": str(path)},
        )
        return {}


def write_field(text: str, key: str, value: str) -> str:
    """Remplace (ou ajoute) UNE seule ligne du frontmatter.

    Écriture chirurgicale : le reste du fichier — corps Markdown, séparateurs
    `---`, ordre et formatage des clés — est préservé à l'identique, contrairement
    à un `yaml.dump()` complet qui réécrirait tout le bloc.

    Raises:
        StateTransitionError : le texte ne contient pas de frontmatter.
    """
    match = _FM_RE.match(text)
    if not match:
        raise StateTransitionError(
            f"[VERROU STATUT] Frontmatter YAML absent : écriture de '{key}' impossible."
        )
    frontmatter = match.group(1)
    val = str(value).strip()
    if not _PLAIN.fullmatch(val):
        # Les valeurs à espace ou caractère spécial sont quotées en JSON,
        # syntaxe YAML-compatible (validated_by: "Marco Lefrancois").
        val = json.dumps(val, ensure_ascii=False)
    replacement = f"{key}: {val}"
    line_re = re.compile(rf"(?m)^{re.escape(key)}:[ \t]*.*$")
    if line_re.search(frontmatter):
        frontmatter = line_re.sub(lambda _m: replacement, frontmatter, count=1)
    else:
        frontmatter = frontmatter.rstrip("\n") + "\n" + replacement + "\n"
    return text[: match.start(1)] + frontmatter + text[match.end(1) :]


def resolve_story_file(project: Path, story_id: str) -> Path:
    """Résolution déterministe d'un récit, dans l'ordre :

    1. chemin relatif sous `backlog/stories/` (avec ou sans extension `.md`) ;
    2. nom de fichier unique en `**/<ID>.md` (sous-dossiers inclus) ;
    3. `id:` ou `jira_key:` déclarés dans le frontmatter.

    Raises:
        FileNotFoundError : répertoire absent, ou récit introuvable.
    """
    root = stories_root(project)
    if not root.exists():
        raise FileNotFoundError(f"[VERROU STATUT] Aucun répertoire de récits : {root}")
    query = str(story_id).strip().replace("\\", "/")
    name = Path(query).name
    name = name if name.endswith(".md") else f"{name}.md"
    direct = root / query
    direct = direct if direct.suffix else direct.with_suffix(".md")
    if direct.is_file():
        return direct
    matches = sorted(root.glob(f"**/{name}"))
    if matches:
        return matches[0]
    for candidate in sorted(root.glob("**/*.md")):
        frontmatter = safe_frontmatter(candidate)
        if query in (str(frontmatter.get("id", "")), str(frontmatter.get("jira_key", ""))):
            return candidate
    raise FileNotFoundError(f"[VERROU STATUT] Récit introuvable sous backlog/stories/ : {story_id}")


def require_approval(frontmatter: Dict[str, Any], story_id: str) -> None:
    """Refuse toute promotion en READY_FOR_DEV sans approbation humaine tracée.

    Raises:
        StateTransitionError : `validated_by` ou `validated_at` absent/vide.
    """
    missing = [k for k in APPROVAL_KEYS if not str(frontmatter.get(k) or "").strip()]
    if missing:
        raise StateTransitionError(
            f"[VERROU ANTI-PROMOTION] Le récit '{story_id}' est en READY_FOR_DEV sans "
            f"approbation humaine (champs manquants : {', '.join(missing)}).\n"
            f"➡ Action obligatoire : python src/swarm.py story-approve --project <projet> "
            f'--story {story_id} --approver "<Nom>"'
        )


def make_issue(story_id: str, kind: str, detail: str) -> Dict[str, Any]:
    """Normalise un écart détecté par `scan_transitions` (forme stable pour les contrôles)."""
    severity = "WARNING" if kind == "unjournaled" else "BLOCKING"
    return {"story_id": story_id, "kind": kind, "severity": severity, "detail": detail}


def commit_with_rollback(
    story: Path, project: Path, original: str, updated: str, entry: Dict[str, Any]
) -> None:
    """Écrit le récit puis journalise ; échec du journal ⇒ restauration + relance.

    Contrat « tout-ou-rien » partagé par la transition, l'approbation et la
    sanction : un statut n'est jamais modifié sans que le journal en porte trace,
    et le journal n'est jamais modifié pour un récit dont l'écriture a échoué.
    """
    story.write_text(updated, encoding="utf-8")
    try:
        append_entry(project, entry)
    except BaseException:
        story.write_text(original, encoding="utf-8")
        logger.error(
            "Échec du journal — écriture du récit annulée (rollback)",
            exc_info=True,
            extra={"story_id": entry.get("story_id"), "file": str(story)},
        )
        raise
    logger.info(
        "Transaction récit + journal validée",
        extra={
            "story_id": entry.get("story_id"),
            "to": entry.get("to_status"),
            "origin": entry.get("origin"),
            "actor": entry.get("actor"),
            "kind": entry.get("kind"),
        },
    )


def apply_sanction_downgrade(
    project: Path,
    story: Path,
    story_id: str,
    current_status: str,
    actor: str,
    source_cmd: str,
) -> Dict[str, Any]:
    """Rétrograde un récit promu illégalement vers `READY_FOR_GROOMING` (OQ-270-1).

    Chemin de sanction explicite hors table FSM, journalisé `origin: sanction`
    avec `reason: SANCTION_REASON`. Le récit et le journal sont **jamais** supprimés.

    ⚠ Le verrou inter-processus doit être détenu par l'appelant : il n'est pas
    réentrant et `scan_transitions` en détient déjà un sur le même chemin.
    """
    original = story.read_text(encoding="utf-8")
    target = StoryStatus.READY_FOR_GROOMING.value
    updated = write_field(original, "status", target)
    entry = build_entry(
        story_id,
        current_status,
        target,
        actor,
        source_cmd,
        "sanction",
        reason=SANCTION_REASON,
    )
    commit_with_rollback(story, project, original, updated, entry)

    logger.warning(
        "Rétrogradation sanctionnée (promotion brute détectée)",
        extra={"story_id": story_id, "from": current_status, "to": target},
    )
    return entry
