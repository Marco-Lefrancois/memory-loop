import re
from typing import List, Dict, Any, Optional
from pathlib import Path

from src.engine.artifacts.bus import OpaqueArtifactBus, ArtifactHandle


class ContextPruningEngine:
    """
    Moteur d'élagage contextuel dynamique (Pattern Dynamic Context Pruning / ADR-0310 & ADR-0354).
    Offloade automatiquement les sorties volumineuses vers l'OpaqueArtifactBus pour éviter
    l'épuisement de la fenêtre contextuelle tout en garantissant un adressage déterministe.
    """

    MAX_TOOL_OUTPUT_CHARS = 1500  # Seuil de compactage des sorties intermédiaires
    MAX_TOOL_OUTPUT_LINES = 30
    _bus: Optional[OpaqueArtifactBus] = None

    @classmethod
    def get_bus(cls) -> OpaqueArtifactBus:
        if cls._bus is None:
            cls._bus = OpaqueArtifactBus()
        return cls._bus

    @classmethod
    def prune_tool_output(cls, tool_name: str, content: str) -> str:
        """
        Compacte chirurgicalement la sortie d'un outil si elle dépasse le seuil utile
        en l'enregistrant dans l'OpaqueArtifactBus et en retournant un descripteur fenêtré.
        """
        if not content or (len(content) <= cls.MAX_TOOL_OUTPUT_CHARS and len(content.splitlines()) <= cls.MAX_TOOL_OUTPUT_LINES):
            return content

        bus = cls.get_bus()
        summary = f"Sortie de l'outil '{tool_name}' ({len(content)} car., {len(content.splitlines())} lignes)"
        offloaded, descriptor, handle = bus.offload_if_exceeds(
            content=content,
            max_chars=cls.MAX_TOOL_OUTPUT_CHARS,
            max_lines=cls.MAX_TOOL_OUTPUT_LINES,
            summary=summary,
            schema_type=f"tool_output/{tool_name}",
            metadata={"tool_name": tool_name},
        )

        if offloaded and descriptor:
            return descriptor

        # Fallback si l'écriture échoue
        lines = content.splitlines()
        head = "\n".join(lines[:10])
        tail = "\n".join(lines[-5:])
        omitted = len(lines) - 15
        return f"{head}\n\n[... {omitted} lignes compactées par ContextPruner ...]\n\n{tail}"

    @classmethod
    def prune_messages(cls, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Parcourt une liste de messages de session et élague les réponses d'outils
        anciennes (au-delà des 3 derniers tours) pour garder un contexte ultra-léger.
        """
        pruned_messages = []
        total_messages = len(messages)

        for idx, msg in enumerate(messages):
            # Conserver intacts les 6 derniers messages (3 derniers tours) et les messages système
            if idx >= total_messages - 6 or msg.get("role") == "system":
                pruned_messages.append(msg)
                continue

            # Pour les messages plus anciens de type 'tool' ou contenant des sorties volumineuses
            if msg.get("role") == "tool":
                content = msg.get("content", "")
                pruned_content = cls.prune_tool_output(msg.get("name", "tool"), content)
                pruned_msg = dict(msg)
                pruned_msg["content"] = pruned_content
                pruned_messages.append(pruned_msg)
            else:
                pruned_messages.append(msg)

        return pruned_messages
