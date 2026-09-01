"""
Token Budget Guard Module - Context Window Truncation & Estimation for mLoop.

Guarantees that prompt payloads sent to LLM subagents stay strictly within
their declared context_budget_tokens (e.g. 8000 tokens), prioritizing CRITICAL/HIGH risk items.
"""

import json
import logging
from typing import Dict, List, Tuple, Any, Optional

from src.pipelines.evidence import EvidencePack, EvidenceItem

logger = logging.getLogger("token_budget")


class TokenBudgetGuard:
    """
    Estimates token footprint and performs semantic truncation on context payloads.
    Uses a standard heuristic (~4 characters per token) with safety margin.
    """

    CHARS_PER_TOKEN = 3.8

    @classmethod
    def estimate_tokens(cls, text: str) -> int:
        """Estimates token count of a string payload."""
        if not text:
            return 0
        return int(len(text) / cls.CHARS_PER_TOKEN) + 10

    @classmethod
    def truncate_evidence_pack(cls, pack: EvidencePack, available_tokens: int) -> EvidencePack:
        """
        Truncates an EvidencePack to fit within available_tokens.
        Prioritizes items by risk_level: CRITICAL > HIGH > MEDIUM > LOW.
        """
        if not pack.items:
            return pack

        # Sort items by risk priority (CRITICAL=4, HIGH=3, MEDIUM=2, LOW=1)
        risk_priority = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}
        sorted_items = sorted(
            pack.items,
            key=lambda item: risk_priority.get(item.risk_level.upper(), 1),
            reverse=True
        )

        kept_items: List[EvidenceItem] = []
        current_tokens = cls.estimate_tokens(pack.source_node) + 50

        for item in sorted_items:
            item_json = json.dumps(item.to_dict(), ensure_ascii=False)
            item_tokens = cls.estimate_tokens(item_json)

            if current_tokens + item_tokens <= available_tokens:
                kept_items.append(item)
                current_tokens += item_tokens
            else:
                logger.warning(
                    f"[TokenBudgetGuard] Evidence item '{item.evidence_id}' (risk: {item.risk_level}) "
                    f"truncated to respect token budget ({current_tokens}/{available_tokens} tokens)."
                )

        truncated_pack = EvidencePack(
            source_node=pack.source_node,
            initiative_name=pack.initiative_name,
            items=kept_items,
            metadata={
                **pack.metadata,
                "original_count": len(pack.items),
                "truncated_count": len(kept_items),
                "token_budget_applied": available_tokens
            }
        )
        return truncated_pack
