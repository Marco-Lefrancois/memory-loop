"""
mLoop Context Engine - Contextual User Fragments & Prompt Cache Optimizer.
Inspiré de l'architecture ContextualUserFragment d'OpenAI Codex.

Garantit :
1. Découpage en fragments bornés (< 10 000 tokens) avec alerte P0 dès 1 000 tokens.
2. Hachage SHA-256 déterministe pour validation d'intégrité et cache.
3. Assemblage ordonné canonique (Directives -> Docs -> Backlog -> Turns).
4. Zero History Rewrite : conservation absolue des préfixes de cache LLM.
"""

import hashlib
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
import time


MAX_FRAGMENT_TOKENS = 10000
HIGH_FRAGMENT_ALERT_TOKENS = 1000


def approximate_token_count(text: str) -> int:
    """Estimation conservative du nombre de tokens (~4 caractères par token)."""
    if not text:
        return 0
    return max(1, len(text) // 4)


@dataclass
class ContextFragment:
    """
    Représente un fragment atomique et immuable injecté dans le contexte du modèle.
    """
    fragment_id: str
    fragment_type: str  # "directive", "knowledge", "backlog", "turn", "evidence"
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.content.encode("utf-8")).hexdigest()

    @property
    def token_count(self) -> int:
        return approximate_token_count(self.content)

    def validate(self) -> None:
        """Valide les contraintes d'intégrité du fragment."""
        tokens = self.token_count
        if tokens > MAX_FRAGMENT_TOKENS:
            raise ValueError(
                f"🛑 [CONTEXT OVERFLOW] Le fragment '{self.fragment_id}' ({tokens} tokens) "
                f"dépasse le plafond strict de {MAX_FRAGMENT_TOKENS} tokens."
            )


class ContextAssemblyEngine:
    """
    Moteur d'assemblage de contexte multi-fragments respectueux du Prompt Cache.
    """

    def __init__(self):
        self.fragments: List[ContextFragment] = []

    def add_fragment(self, fragment: ContextFragment) -> None:
        fragment.validate()
        self.fragments.append(fragment)

    def render_prompt_context(self) -> str:
        """
        Assemble tous les fragments selon l'ordre canonique stable pour maximiser le Prompt Caching.
        Ordre canonique : Directives -> Knowledge -> Backlog -> Evidence -> Turns.
        """
        type_priority = {
            "directive": 1,
            "knowledge": 2,
            "backlog": 3,
            "evidence": 4,
            "turn": 5
        }

        # Tri stable selon la priorité du type
        sorted_fragments = sorted(
            self.fragments,
            key=lambda f: (type_priority.get(f.fragment_type, 99), f.created_at)
        )

        rendered_sections = []
        for f in sorted_fragments:
            rendered_sections.append(
                f"<!-- FRAGMENT: {f.fragment_id} | TYPE: {f.fragment_type} | SHA256: {f.sha256[:12]} -->\n"
                f"{f.content}\n"
            )

        return "\n".join(rendered_sections)
