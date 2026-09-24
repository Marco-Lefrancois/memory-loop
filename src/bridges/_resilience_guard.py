"""
_resilience_guard.py — Garde-fou OWASP MCP Top 10 (MCP-01 à MCP-04) + digests.

Extraction du cœur d'intégrité (ADR-0374 / ADR-0202, plafond modulaire) :
aucune dépendance au protocole MCP — la poignée de main et la boucle stdio
restent dans ``mcp_resilience_guard``.
"""

import hashlib
import json
import re
import sys
from typing import Any, Dict, List, Optional, Set


class MCPGuardError(Exception):
    """Exception de base pour les violations de sécurité MCP."""
    pass


class MCPValidationError(MCPGuardError):
    """Levée lorsqu'un schéma d'arguments d'outil est invalide ou violé (MCP-01)."""
    pass


class MCPScopeViolationError(MCPGuardError):
    """Levée lors d'une violation de permissions ou de périmètre d'exécution (MCP-03)."""
    pass


class MCPResilienceGuard:
    """Garde-fou souverain OWASP MCP Top 10 pour l'infrastructure agentique mLoop."""

    # Outils destructifs ou à fort impact nécessitant des privilèges élevés
    DESTRUCTIVE_ACTIONS: Set[str] = {
        "rollback",
        "purge",
        "delete",
        "write_file",
        "execute_code",
        "restart_service",
        "kill_agent",
    }

    # Rôles en lecture seule stricts
    READ_ONLY_ROLES: Set[str] = {
        "read_only",
        "investigation",
        "auditor",
        "sentinel_observer",
    }

    def __init__(self, max_payload_chars: int = 16000):
        self.max_payload_chars = max_payload_chars

    def validate_tool_arguments(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        schema: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Valide les arguments d'un appel d'outil MCP selon un schéma strict (MCP-01).
        Rejette tout argument inattendu ou type incompatible.
        """
        if not isinstance(arguments, dict):
            raise MCPValidationError(
                f"[MCP-01] Les arguments de l'outil '{tool_name}' doivent être un dictionnaire JSON valide."
            )

        if not schema:
            return arguments

        required_props = set(schema.get("required", []))
        properties = schema.get("properties", {})

        # 1. Vérification des champs obligatoires
        missing = required_props - set(arguments.keys())
        if missing:
            raise MCPValidationError(
                f"[MCP-01] Outil '{tool_name}' : arguments obligatoires manquants : {sorted(list(missing))}"
            )

        # 2. Interdiction des propriétés non déclarées (Anti-Tampering / Zero Extra Args)
        if not schema.get("additionalProperties", False):
            unexpected = set(arguments.keys()) - set(properties.keys())
            if unexpected:
                raise MCPValidationError(
                    f"[MCP-01] Outil '{tool_name}' : arguments non autorisés détectés : {sorted(list(unexpected))}"
                )

        # 3. Validation basique des types primitifs
        type_mapping = {
            "string": str,
            "integer": int,
            "number": (int, float),
            "boolean": bool,
            "array": list,
            "object": dict,
        }

        for arg_name, arg_val in arguments.items():
            prop_def = properties.get(arg_name, {})
            expected_type = prop_def.get("type")
            if expected_type and expected_type in type_mapping:
                expected_py_type = type_mapping[expected_type]
                # Spécificité bool sous-classe de int en Python
                if expected_type in ("integer", "number") and isinstance(arg_val, bool):
                    raise MCPValidationError(
                        f"[MCP-01] Outil '{tool_name}' : '{arg_name}' attend {expected_type}, bool reçu."
                    )
                if not isinstance(arg_val, expected_py_type):
                    raise MCPValidationError(
                        f"[MCP-01] Outil '{tool_name}' : '{arg_name}' attend {expected_type}, "
                        f"reçu {type(arg_val).__name__}."
                    )

        return arguments

    def check_execution_permission(
        self,
        tool_name: str,
        role: str,
        is_destructive: Optional[bool] = None
    ) -> bool:
        """
        Vérifie la parité des permissions RBAC et prévient l'agence excessive (MCP-03).
        """
        clean_role = (role or "").strip().lower()
        clean_tool = (tool_name or "").strip().lower()

        is_destr = is_destructive if is_destructive is not None else any(
            destr in clean_tool for destr in self.DESTRUCTIVE_ACTIONS
        )

        if clean_role in self.READ_ONLY_ROLES and is_destr:
            raise MCPScopeViolationError(
                f"[MCP-03] Viol de portée : Le rôle en lecture seule '{role}' "
                f"ne peut pas exécuter l'outil destructif '{tool_name}'."
            )

        return True

    def encapsulate_tool_result(
        self,
        content: str,
        tool_name: str,
        max_chars: Optional[int] = None
    ) -> str:
        """
        Encapsule hermétiquement le résultat d'un outil MCP dans des balises isolées (MCP-02).
        Applique une troncature déterministe avec empreinte SHA-256 pour prévenir MCP-04.
        """
        limit = max_chars or self.max_payload_chars
        raw_bytes = (content or "").encode("utf-8")
        full_hash = hashlib.sha256(raw_bytes).hexdigest()[:16]

        is_truncated = False
        payload = content or ""
        if len(payload) > limit:
            is_truncated = True
            payload = payload[:limit] + f"\n... [TRONQUÉ : Limite de sécurité MCP-04 {limit} caractères atteinte]"

        # Neutralisation des fermetures de balises malveillantes dans le payload
        safe_payload = payload.replace("</mcp_untrusted_data>", "<\\/mcp_untrusted_data>")

        return (
            f'<mcp_untrusted_data tool="{tool_name}" sha256="{full_hash}" truncated="{str(is_truncated).lower()}">\n'
            f'{safe_payload}\n'
            f'</mcp_untrusted_data>'
        )

    @staticmethod
    def compute_workflow_digest(steps: List[Dict[str, Any]]) -> str:
        """
        Calcule l'empreinte canonique d'une séquence d'actions multi-étapes pour
        la cristallisation sous forme de macro-outil déterministe (ADR-0374).
        """
        normalized = []
        for step in steps:
            normalized.append({
                "tool": str(step.get("tool", "")),
                "args": step.get("args", {}),
                "order": step.get("order", 0),
            })
        serialized = json.dumps(normalized, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()
