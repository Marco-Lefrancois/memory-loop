# -*- coding: utf-8 -*-
"""
Package bridge Cline pour mLoop (ADR-0377, ADR-0346, EPIC-26).
Fournit l'intégration Memory Bank, la parité .clinerules et l'adaptateur de worker.
"""

from src.bridges.cline.memory_bank_bridge import MemoryBankBridge
from src.bridges.cline.rules_mirror import ClineRulesMirror

__all__ = ["MemoryBankBridge", "ClineRulesMirror"]
