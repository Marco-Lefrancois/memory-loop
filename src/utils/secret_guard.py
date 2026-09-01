import re
from typing import Dict, Any, List

class SecretLeakGuard:
    """
    Guardrail déterministe anti-fuite de secrets (Pattern Envsitter / ADR-0310).
    Détecte et masque les clés API, jetons d'accès et tokens sensibles dans les chaînes,
    fichiers et objets sérialisés.
    """
    
    SECRET_PATTERNS = [
        (r'sk-[a-zA-Z0-9_\-]{20,}', '[REDACTED_API_KEY]'),
        (r'AIzaSy[a-zA-Z0-9_\-]{33}', '[REDACTED_GOOGLE_API_KEY]'),
        (r'ghp_[a-zA-Z0-9]{36}', '[REDACTED_GITHUB_TOKEN]'),
        (r'glpat-[a-zA-Z0-9_\-]{20,}', '[REDACTED_GITLAB_TOKEN]'),
        (r'ey[a-zA-Z0-9_\-]{30,}\.ey[a-zA-Z0-9_\-]{30,}\.[a-zA-Z0-9_\-]{20,}', '[REDACTED_JWT_TOKEN]'),
        (r'bearer\s+[a-zA-Z0-9_\-\.]{20,}', 'Bearer [REDACTED_TOKEN]', re.IGNORECASE),
        (r'(?:api[_-]?key|secret|token|password|auth)[\s:=]+([a-zA-Z0-9_\-\.]{16,})', '[REDACTED_SECRET]', re.IGNORECASE),
    ]

    @classmethod
    def sanitize_text(cls, text: str) -> str:
        """Remplace tous les tokens détectés par des placeholders sécurisés."""
        if not text or not isinstance(text, str):
            return text
            
        sanitized = text
        for pattern_tuple in cls.SECRET_PATTERNS:
            if len(pattern_tuple) == 3:
                pattern, replacement, flags = pattern_tuple
                sanitized = re.sub(pattern, replacement, sanitized, flags=flags)
            else:
                pattern, replacement = pattern_tuple
                sanitized = re.sub(pattern, replacement, sanitized)
        return sanitized

    @classmethod
    def scan_for_leaks(cls, text: str) -> List[str]:
        """Retourne la liste des types de secrets suspects détectés dans le texte."""
        if not text or not isinstance(text, str):
            return []
            
        found = []
        for pattern_tuple in cls.SECRET_PATTERNS:
            pattern = pattern_tuple[0]
            flags = pattern_tuple[2] if len(pattern_tuple) == 3 else 0
            if re.search(pattern, text, flags=flags):
                found.append(pattern)
        return found
