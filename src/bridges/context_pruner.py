import re
from typing import List, Dict, Any

class ContextPruningEngine:
    """
    Moteur d'élagage contextuel dynamique (Pattern Dynamic Context Pruning / ADR-0310).
    Réduit la consommation de tokens en compactant les sorties d'outils volumineuses
    et les listings intermédiaires résolus sans altérer la mémoire sémantique ni les ADRs.
    """

    MAX_TOOL_OUTPUT_CHARS = 1200  # Seuil de compactage des sorties intermédiaires

    @classmethod
    def prune_tool_output(cls, tool_name: str, content: str) -> str:
        """Compacte chirurgicalement la sortie d'un outil si elle dépasse le seuil utile."""
        if not content or len(content) <= cls.MAX_TOOL_OUTPUT_CHARS:
            return content

        # Si c'est un listing de fichiers ou un diff volumineux
        if tool_name in ["run_command", "view_file", "grep_search", "list_dir"]:
            lines = content.splitlines()
            if len(lines) > 30:
                head = "\n".join(lines[:15])
                tail = "\n".join(lines[-10:])
                omitted = len(lines) - 25
                return f"{head}\n\n[... {omitted} lignes de sortie intermédiaire compactées par ContextPruner ...]\n\n{tail}"

        return content[:cls.MAX_TOOL_OUTPUT_CHARS] + "\n[... sortie tronquée pour optimisation de contexte ...]"

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
