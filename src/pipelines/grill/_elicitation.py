"""
src/pipelines/grill/_elicitation.py — Contrat et fabrication des questions
d'élicitation Form Mode (MLOOP-213-BE).

Sous-module du module de grill existant (point d'intégration imposé par le
récit ``src/pipelines/grill_engine.py``) : aucun module parallèle n'est créé.
Le découpage en trois composants spécialisés est une exigence du plafond
modulaire ADR-0202 (300 lignes / 15 Ko) :

- ``_elicitation.py`` (ce module) : constantes du contrat, schémas d'élicitation
  standard, validation, rendu du repli textuel ;
- ``_elicitation_registry.py`` : registre de décisions immuable ;
- ``_elicitation_state.py`` : état d'attente régénérable et cycle de vie 5 min.

La négociation de capacité et l'enveloppe JSON-RPC vivent côté pont, dans
``src/bridges/_mcp_elicitation.py`` : la capacité client est un paramètre
explicite d'entrée, ce module n'importe aucun pont (zéro import circulaire).
"""

from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────
# CONSTANTES DE CONTRAT
# ──────────────────────────────────────────────────────────────────────────

ELICITATION_TIMEOUT_SECONDS: float = 300.0
"""Macro ADR-004 Q3 : cinq minutes sans réponse → tâche en attente de saisie.

Le délai est imposé à l'émission côté serveur (bornage déterministe) ; la
régulation timer fine de l'hôte lui revient (OQ-213-02, non bloquante)."""

DECISION_RECORDS_FILE = "decision_records.jsonl"
PENDING_FILE = "elicitation_pending.json"

PRIMITIVE_TYPES = frozenset({"string", "number", "integer", "boolean"})
STATUS_WAITING = "waiting"
STATUS_INPUT_REQUIRED = "input_required"

# Champs obligatoires de la ligne de décision (récit §4) : identifiant, récit,
# question, réponse, auteur, date et indicateur de repli.
# `adr_ref` reste facultatif et n'est **jamais** utilisé pour écrire un ADR.
REQUIRED_DECISION_FIELDS = (
    "elicitation_id",
    "story_id",
    "question",
    "answer",
    "answered_by",
    "answered_at",
    "fallback_used",
)


class ElicitationError(ValueError):
    """Refus explicite d'une demande ou d'une réponse d'élicitation."""

    def __init__(self, reasons: Sequence[str]):
        self.reasons: list[str] = [str(reason) for reason in reasons]
        super().__init__(", ".join(self.reasons))


def resolve_project_dir(project_path: Optional[Path] = None, project: Optional[str] = None) -> Path:
    """Résout ``Projects/<projet>`` — un chemin explicite prime toujours
    (tests, appels in-process), sinon le projet de session, sinon ``mLoop``."""
    if project_path is not None:
        return Path(project_path)
    cwd = Path.cwd()
    if (cwd / "backlog").is_dir() and (cwd / "docs").is_dir():
        return cwd
    return cwd / "Projects" / (project or "mLoop")


# ──────────────────────────────────────────────────────────────────────────
# 1. SCHÉMAS D'ÉLICITATION STANDARD (In-Scope §1)
# ──────────────────────────────────────────────────────────────────────────

STANDARD_QUESTIONS: dict[str, dict[str, Any]] = {
    "api_profile": {
        "property": "profil",
        "options": ["PROFIL_A", "PROFIL_B"],
        "message": "Quel profil d'API retenir pour ce récit ?",
    },
    "story_readiness": {
        "property": "preparation",
        "options": ["PRETE", "NON_PRETE"],
        "message": "Le récit est-il pret a developpement (Definition of Ready) ?",
    },
    "complexity_arbitrage": {
        "property": "complexite",
        "options": ["S", "M", "L", "XL"],
        "message": "Quelle taille INVEST retenir pour ce récit ?",
    },
}


def stable_elicitation_id(story_id: str, message: str) -> str:
    """Identifiant **déterministe** d'un arbitrage : même récit + même énoncé
    donnent toujours le même identifiant — seule condition pour que la
    détection « déjà répondu » puisse un jour reposer la question."""
    digest = hashlib.sha256(f"{story_id}|{message}".encode("utf-8")).hexdigest()
    return f"elic-{digest[:24]}"


def build_standard_question(
    kind: str,
    *,
    story_id: str,
    question: Optional[str] = None,
    context: Optional[Mapping[str, Any]] = None,
    elicitation_id: Optional[str] = None,
    task_id: Optional[str] = None,
) -> dict[str, Any]:
    """Construit une question d'arbitrage à schéma JSON-Schema **fermé**."""
    if kind not in STANDARD_QUESTIONS:
        raise ElicitationError([f"kind_inconnu:{kind}"])
    spec = STANDARD_QUESTIONS[kind]
    message = (question or spec["message"]).strip()
    if not message:
        raise ElicitationError(["message_absent"])
    schema = {
        "type": "object",
        "properties": {
            spec["property"]: {
                "type": "string",
                "title": spec["property"],
                "description": message,
                "enum": list(spec["options"]),
            }
        },
        "required": [spec["property"]],
    }
    payload: dict[str, Any] = {
        "elicitationId": elicitation_id or stable_elicitation_id(story_id, message),
        "storyId": story_id,
        "message": message,
        "requestedSchema": schema,
        "context": dict(context or {}),
    }
    if task_id:
        payload["taskId"] = task_id
    return payload


# ──────────────────────────────────────────────────────────────────────────
# 2. VALIDATION (schéma émis / réponse reçue)
# ──────────────────────────────────────────────────────────────────────────


def validate_requested_schema(schema: Any) -> list[str]:
    """Contrôle un schéma avant émission : objet plat, champs obligatoires
    cohérents et options **fermées**. Retourne les motifs (vide = valide)."""
    if not isinstance(schema, Mapping):
        return ["schema_absent"]
    if schema.get("type") != "object":
        return ["schema_type_non_object"]
    properties = schema.get("properties")
    if not isinstance(properties, Mapping) or not properties:
        return ["schema_proprietes_vides"]
    reasons: list[str] = []
    required = schema.get("required")
    if not isinstance(required, list) or not required:
        reasons.append("schema_obligatoires_absents")
    elif not set(required) <= set(properties):
        reasons.append("schema_obligatoires_inconnus")
    for name, subschema in properties.items():
        if not isinstance(subschema, Mapping):
            reasons.append(f"propriete_malformee:{name}")
            continue
        if subschema.get("type") not in PRIMITIVE_TYPES:
            reasons.append(f"propriete_non_primitive:{name}")
        options = subschema.get("enum")
        if not isinstance(options, list) or not options:
            reasons.append(f"options_ouvertes:{name}")
        elif any(not isinstance(option, str) for option in options):
            reasons.append(f"options_non_textuelles:{name}")
    return reasons


def validate_content(schema: Mapping[str, Any], content: Any) -> list[str]:
    """Contrôle une réponse contre le schéma émis (options fermées comprises)."""
    if not isinstance(content, Mapping):
        return ["reponse_non_structuree"]
    properties = schema.get("properties") or {}
    reasons: list[str] = []
    for name in schema.get("required") or []:
        if name not in content:
            reasons.append(f"champ_obligatoire_absent:{name}")
    for name, value in content.items():
        subschema = properties.get(name)
        if subschema is None:
            reasons.append(f"champ_hors_schema:{name}")
            continue
        options = subschema.get("enum")
        if isinstance(options, list) and value not in options:
            reasons.append(f"valeur_hors_options:{name}")
        expected = subschema.get("type")
        if expected == "string" and not isinstance(value, str):
            reasons.append(f"type_invalide:{name}")
        elif expected in ("number", "integer") and (
            isinstance(value, bool) or not isinstance(value, (int, float))
        ):
            reasons.append(f"type_invalide:{name}")
        elif expected == "boolean" and not isinstance(value, bool):
            reasons.append(f"type_invalide:{name}")
    return reasons


# ──────────────────────────────────────────────────────────────────────────
# 3. REPLI TEXTUEL (jamais bloquant)
# ──────────────────────────────────────────────────────────────────────────


def render_fallback_markdown(payload: Mapping[str, Any]) -> str:
    """Question lisible seule en Markdown, embarquant sa charge utile : la
    réponse textuelle qui suit peut être remontée à l'identique."""
    options: list[str] = []
    schema = payload.get("requestedSchema")
    if isinstance(schema, Mapping):
        for subschema in (schema.get("properties") or {}).values():
            if isinstance(subschema, Mapping):
                options.extend(str(option) for option in (subschema.get("enum") or []))
    lines = [
        "## Question d'arbitrage (repli textuel)",
        "",
        f"**Récit** : {payload.get('storyId', '')}",
        f"**Identifiant d'elicitation** : {payload.get('elicitationId', '')}",
        "",
        str(payload.get("message", "")),
        "",
    ]
    if options:
        lines.append(
            "Répondez par une seule option : " + " · ".join(f"`{option}`" for option in options)
        )
        lines.append("")
    lines.extend(
        [
            "Charge utile à remonter telle quelle :",
            "",
            "```json",
            json.dumps(dict(payload), ensure_ascii=False, indent=2),
            "```",
        ]
    )
    return "\n".join(lines)
