# -*- coding: utf-8 -*-
"""
Lexical Integrity Guard & Tokenizer Signature Engine (mLoop Core - ADR-0327).

Inspiré de l'architecture OKF Token Injection (Towards Data Science / Aug 2026) :
- Vérifie l'intégrité lexicale via la phrase étalon Rosetta Canary Phrase.
- Impose la normalisation Unicode NFC sur tous les transferts de connaissances.
- Détecte et neutralise les fuites de tokens de contrôle inter-modèles (<|im_start|>, [INST]).
- Protège le pipeline contre le "Syndrome de Babel Silencieux".
"""

from __future__ import annotations

import hashlib
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Any, Optional


ROSETTA_CANARY_PHRASE = "mLoop SSOT: Règles RM-01 & isolation d'état. BPE-Check [!NOTE] 🚀"

# Balises de contrôle des principales familles de modèles (Qwen, Llama, Gemma, DeepSeek, OpenAI)
SENSITIVE_CONTROL_TOKENS = [
    r"<\|im_start\|>",
    r"<\|im_end\|>",
    r"<\|endoftext\|>",
    r"\[INST\]",
    r"\[/INST\]",
    r"<start_of_turn>",
    r"<end_of_turn>",
    r"<｜begin of sentence｜>",
    r"<｜end of sentence｜>",
]


@dataclass
class LexicalCheckResult:
    """Résultat du contrôle d'intégrité lexicale."""
    canary_hash: str
    is_unicode_nfc: bool
    control_token_leaks: List[str]
    is_valid: bool
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "canary_hash": self.canary_hash,
            "is_unicode_nfc": self.is_unicode_nfc,
            "control_token_leaks": self.control_token_leaks,
            "is_valid": self.is_valid,
            "details": self.details,
        }


class LexicalIntegrityGuard:
    """Moteur de garde d'intégrité lexicale et anti-dérive d'encodage."""

    @staticmethod
    def get_canary_hash(phrase: str = ROSETTA_CANARY_PHRASE) -> str:
        """Calcule le hash SHA-256 canonique de la phrase Rosetta après normalisation NFC."""
        normalized = unicodedata.normalize("NFC", phrase)
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]

    @staticmethod
    def normalize_to_nfc(text: str) -> str:
        """Normalise strictement un texte en Unicode NFC (Canonical Composition)."""
        if not text:
            return ""
        return unicodedata.normalize("NFC", text)

    @staticmethod
    def is_nfc_normalized(text: str) -> bool:
        """Vérifie si le texte est strictement normalisé en NFC."""
        if not text:
            return True
        return unicodedata.is_normalized("NFC", text)

    @classmethod
    def detect_control_token_leaks(cls, text: str) -> List[str]:
        """Détecte les balises de contrôle de modèles injectées sans échappement."""
        if not text:
            return []
        leaks = []
        for pattern in SENSITIVE_CONTROL_TOKENS:
            if re.search(pattern, text, re.IGNORECASE):
                clean_name = pattern.replace("\\", "")
                leaks.append(clean_name)
        return leaks

    @classmethod
    def escape_control_tokens(cls, text: str) -> str:
        """Échappe les balises de contrôle pour un transit passif sécurisé entre agents."""
        if not text:
            return ""
        sanitized = text
        for pattern in SENSITIVE_CONTROL_TOKENS:
            def repl(m):
                val = m.group(0)
                return val.replace("<", "&lt;").replace(">", "&gt;").replace("[", "\\[").replace("]", "\\]")
            sanitized = re.sub(pattern, repl, sanitized)
        return sanitized

    @classmethod
    def inspect_text(cls, text: str) -> LexicalCheckResult:
        """Exécute l'inspection lexicale complète sur un contenu textuel."""
        canary = cls.get_canary_hash()
        is_nfc = cls.is_nfc_normalized(text)
        leaks = cls.detect_control_token_leaks(text)

        is_valid = is_nfc and len(leaks) == 0

        return LexicalCheckResult(
            canary_hash=canary,
            is_unicode_nfc=is_nfc,
            control_token_leaks=leaks,
            is_valid=is_valid,
            details={
                "chars_count": len(text),
                "leaks_count": len(leaks),
            },
        )

    @classmethod
    def inspect_project_evidence(cls, project_path: Path | str) -> LexicalCheckResult:
        """Inspecte tous les EvidencePacks et Stories du projet pour s'assurer de l'absence de fuites."""
        path = Path(project_path)
        all_text = []
        
        if path.exists():
            for f in path.rglob("*.json"):
                if "evidence" in str(f) or "supersession" in str(f):
                    try:
                        all_text.append(f.read_text(encoding="utf-8", errors="ignore"))
                    except Exception:
                        pass
            for f in path.rglob("*.md"):
                if "backlog" in str(f) or "docs" in str(f):
                    try:
                        all_text.append(f.read_text(encoding="utf-8", errors="ignore"))
                    except Exception:
                        pass

        combined = "\n".join(all_text)
        return cls.inspect_text(combined)
