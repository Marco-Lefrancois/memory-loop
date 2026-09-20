# -*- coding: utf-8 -*-
"""
Sélection et résolution de la clé LiteLLM active.
Sous-module du package token_ledger (ADR-0202 / MLOOP-101-BE).
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict


def resolve_active_key_info() -> Dict[str, str]:
    """Identifie la clé active dans l'environnement ou ~/.secrets."""
    # 1. Charger .env en priorité absolue (SSOT)
    env_file = Path(".env")
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip().strip("'\"")

    key_metro = os.getenv("LITELLM_API_KEY_METRO", "")
    key_boire = os.getenv("LITELLM_API_KEY_BOIRE", "")
    key_perso = os.getenv("LITELLM_API_KEY_PERSO", "")

    active_key = os.getenv("LITELLM_API_KEY", "")
    # Déréférencement automatique si LITELLM_API_KEY pointe vers une variable ou un alias
    alias_map = {
        "LITELLM_API_KEY_BOIRE": key_boire,
        "${LITELLM_API_KEY_BOIRE}": key_boire,
        "BOIRE": key_boire,
        "boire": key_boire,
        "LITELLM_API_KEY_METRO": key_metro,
        "${LITELLM_API_KEY_METRO}": key_metro,
        "METRO": key_metro,
        "metro": key_metro,
        "LITELLM_API_KEY_PERSO": key_perso,
        "${LITELLM_API_KEY_PERSO}": key_perso,
        "PERSO": key_perso,
        "perso": key_perso,
    }
    if active_key in alias_map and alias_map[active_key]:
        active_key = alias_map[active_key]
    elif active_key and not active_key.startswith("sk-"):
        clean_ref = active_key.strip("${}").strip()
        if clean_ref in os.environ and os.environ[clean_ref].startswith("sk-"):
            active_key = os.environ[clean_ref]

    if not active_key:
        secret_active = Path.home() / ".secrets" / "nmedia-key"
        if secret_active.exists():
            try:
                active_key = secret_active.read_text(encoding="utf-8").strip()
            except OSError as e:
                # Fichier inaccessible — journalisation minimale, pas de silence
                import logging

                logging.getLogger("token_ledger.key_info").debug(
                    "Lecture du fichier secret échouée",
                    exc_info=True,
                    extra={"secret_path": str(secret_active), "error": str(e)},
                )

    label = "Inconnue"
    if active_key:
        if key_boire and active_key == key_boire:
            label = "Boire et Frère"
        elif key_metro and active_key == key_metro:
            label = "Metro"
        elif key_perso and active_key == key_perso:
            label = "Perso (Générale)"
        elif "sk-o2o1" in active_key:
            label = "Boire et Frère"
        elif "sk-m3N2" in active_key:
            label = "Metro"
        elif "sk-jeUj" in active_key:
            label = "Perso (Générale)"

    masked = active_key[:7] + "..." + active_key[-4:] if len(active_key) > 12 else active_key
    return {
        "key_label": label,
        "key_masked": masked,
        "key_raw": active_key,
    }
