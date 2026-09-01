import re
from typing import List, Tuple

DANGEROUS_PATTERNS: List[Tuple[str, str]] = [
    (r"\bgit\s+push\s+.*--force\b", "Commandes 'git push --force' strictement interdites par les guardrails mLoop."),
    (r"\bgit\s+reset\s+--hard\b", "Commandes 'git reset --hard' récursives interdites par précaution."),
    (r"\brm\s+-rf\s+/\b", "Effacement racine interdit."),
    (r"\bformat\s+[a-zA-Z]:\b", "Formatage de disque interdit.")
]

def check_command_safety(command_line: str) -> bool:
    """
    Vérifie l'absence de motifs de commandes destructrices dans la ligne de commande.
    Retourne True si la commande est sûre, lance une exception ValueError sinon.
    """
    if not command_line:
        return True

    for pattern, reason in DANGEROUS_PATTERNS:
        if re.search(pattern, command_line, re.IGNORECASE):
            raise ValueError(f"🛑 [SAFETY INTERCEPTOR] Commande bloquée par les guardrails mLoop : {reason}")

    return True
