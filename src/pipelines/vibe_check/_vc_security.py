"""
Sous-module vibe_check/_vc_security.py
Checks liés à la sécurité des secrets et à l'alignement des clés LiteLLM (Zero Cost-Leak).

Checks inclus :
  - check_07_secret_leak    : Étanchéité des secrets & tokens (Zero-Leak Envsitter Pattern) (Check 7)
  - check_08_litellm_key    : Alignement strict projet ↔ clé LiteLLM (Zero Cost-Leak) (Check 8)
"""

import os
import sys
from pathlib import Path

from src.utils.logger import get_logger

# Logger de secours propre à ce sous-module (utilisé si le module parent n'est pas encore chargé).
_fallback_logger = get_logger("pipelines.vibe_check._vc_security")


def _logger():
    """
    Retourne le logger de l'orchestrateur vibe_check si disponible (pour que
    patch.object(vibe_check, 'logger') soit visible ici), sinon le logger local.
    Évite l'import circulaire au niveau module grâce au chargement différé via sys.modules.
    """
    mod = sys.modules.get("src.pipelines.vibe_check")
    if mod is not None and hasattr(mod, "logger"):
        return mod.logger
    return _fallback_logger


def check_07_secret_leak(
    project_dir: Path, project_name: str, lifecycle_mode: str, stage_label: str
) -> dict:
    """
    Check 7 : Étanchéité des secrets & tokens (Zero-Leak Envsitter Pattern).
    Scanne les fichiers JSON du backlog et de memory/evidence/ à la recherche de
    fuites de secrets (clés API, tokens, etc.).
    """
    from src.utils.secret_guard import SecretLeakGuard

    secret_leaks = []
    if project_dir.exists():
        for check_path in [
            project_dir / "backlog",
            project_dir / "memory" / "evidence",
        ]:
            if check_path.exists():
                for f in check_path.rglob("*.json"):
                    try:
                        content = f.read_text(encoding="utf-8")
                        leaks = SecretLeakGuard.scan_for_leaks(content)
                        if leaks:
                            secret_leaks.append(f.name)
                    except Exception:
                        _logger().error(
                            f"Erreur de lecture du fichier '{f}' lors du scan de fuite de secrets.",
                            exc_info=True,
                            extra={
                                "check_name": "secret_leak_scan",
                                "violation_type": "file_read_error",
                                "file_path": str(f),
                            },
                        )
    return {
        "check": "Étanchéité des Secrets & Tokens (Zero-Leak Envsitter Pattern)",
        "status": "PASS" if len(secret_leaks) == 0 else "FAIL",
    }


def check_08_litellm_key(
    project_dir: Path, project_name: str, lifecycle_mode: str, stage_label: str
) -> dict:
    """
    Check 8 : Alignement strict projet ↔ clé LiteLLM (Zero Cost-Leak).
    Vérifie que la clé LiteLLM active est bien celle attendue pour le projet courant.
    La dérogation MLOOP_ALLOW_CROSS_KEY / ALLOW_CROSS_KEY est supportée.
    """
    from src.utils.token_ledger import TokenLedger

    key_info = TokenLedger.resolve_active_key_info()
    active_label = key_info.get("key_label", "Inconnue")

    allow_cross_key = os.getenv("MLOOP_ALLOW_CROSS_KEY", "").lower() in [
        "1",
        "true",
        "yes",
    ] or os.getenv("ALLOW_CROSS_KEY", "").lower() in ["1", "true", "yes"]
    key_alignment_ok = True
    key_reason = f"Clé active : {active_label}"
    p_lower = (project_name or "").lower()

    if "boire" in p_lower:
        if active_label != "Boire et Frère":
            if allow_cross_key:
                key_reason = f"Projet '{project_name}' avec clé '{active_label}' (Dérogation MLOOP_ALLOW_CROSS_KEY active)"
            else:
                key_alignment_ok = False
                key_reason = f"Projet '{project_name}' requiert la clé 'Boire et Frère' (active: '{active_label}')"
    elif "metro" in p_lower:
        if active_label != "Metro":
            if allow_cross_key:
                key_reason = f"Projet '{project_name}' avec clé '{active_label}' (Dérogation MLOOP_ALLOW_CROSS_KEY active)"
            else:
                key_alignment_ok = False
                key_reason = (
                    f"Projet '{project_name}' requiert la clé 'Metro' (active: '{active_label}')"
                )

    return {
        "check": f"Alignement Projet ↔ Clé LiteLLM ({key_reason})",
        "status": "PASS" if key_alignment_ok else "FAIL",
    }
