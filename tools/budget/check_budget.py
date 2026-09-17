# -*- coding: utf-8 -*-
"""
Outil utilitaire de suivi du budget LiteLLM (Nmédia Cloud).
Permet de visualiser en temps réel la consommation et le solde restant pour toutes les clés configurées ou un projet spécifique.

Usage:
    python tools/budget/check_budget.py
    python tools/budget/check_budget.py --project boire
    python tools/budget/check_budget.py --project metro
    python tools/budget/check_budget.py --key sk-...
"""

import os
import sys
import argparse
from pathlib import Path
import httpx
from datetime import datetime, timedelta

def load_env():
    """Charge le fichier .env de la racine s'il existe (3 niveaux au-dessus)."""
    env_file = Path(__file__).parent.parent.parent / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                os.environ[key.strip()] = val.strip().strip('"\'')

def get_secret_file_key(secret_name: str) -> str:
    """Lit une clé depuis ~/.secrets/<secret_name> si existante."""
    secret_path = Path.home() / ".secrets" / secret_name
    if secret_path.exists():
        try:
            return secret_path.read_text(encoding="utf-8").strip()
        except Exception:
            return ""
    return ""

def format_iso_date(raw_date):
    if not raw_date:
        return "Jamais"
    try:
        clean_date = raw_date.replace("Z", "+00:00")
        dt = datetime.fromisoformat(clean_date)
        return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
    except Exception:
        return raw_date

def calculate_time_left(raw_date):
    if not raw_date:
        return "N/A"
    try:
        clean_date = raw_date.replace("Z", "+00:00")
        dt = datetime.fromisoformat(clean_date)
        now = datetime.now(dt.tzinfo)
        delta = dt - now
        if delta.total_seconds() <= 0:
            return "Expiré"
        days = delta.days
        hours = delta.seconds // 3600
        return f"{days} jours et {hours} heures restants"
    except Exception:
        return "N/A"

def fetch_key_info(api_key: str, base_url: str) -> dict:
    url = f"{base_url}/key/info"
    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        response = httpx.get(url, headers=headers, timeout=15.0)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        return {"error": f"Status {e.response.status_code}: {e.response.text}"}
    except Exception as e:
        return {"error": str(e)}

def fetch_spend_breakdown(api_key: str, key_token: str, base_url: str) -> list:
    """Récupère l'historique de consommation ventilé par modèle et par jour."""
    url = f"{base_url}/spend/logs"
    headers = {"Authorization": f"Bearer {api_key}"}
    now = datetime.now()
    start_date = now.strftime("%Y-%m-01")
    end_date = (now + timedelta(days=1)).strftime("%Y-%m-%d")
    params = {
        "start_date": start_date,
        "end_date": end_date,
        "api_key": key_token
    }
    try:
        response = httpx.get(url, headers=headers, params=params, timeout=15.0)
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    return []

def print_spend_breakdown(logs: list):
    if not logs or not isinstance(logs, list):
        return

    model_totals = {}
    daily_totals = {}
    total_spend = 0.0

    for day in logs:
        date = day.get("startTime", "N/A")
        day_spend = day.get("spend", 0.0)
        if day_spend > 0:
            daily_totals[date] = day_spend
        total_spend += day_spend

        for model, mspend in day.get("models", {}).items():
            if mspend > 0:
                model_totals[model] = model_totals.get(model, 0.0) + mspend

    if not model_totals:
        return

    print(" 📊 VENTILATION DE LA CONSOMMATION (CYCLE EN COURS) :")
    print(" ----------------------------------------------------")
    print(" Modèles les plus consommateurs :")
    sorted_models = sorted(model_totals.items(), key=lambda x: x[1], reverse=True)
    for model, spend in sorted_models:
        pct = (spend / total_spend * 100) if total_spend > 0 else 0
        clean_model = model.replace("gemini/", "").replace("anthropic/", "").replace("openai/", "")
        print(f"   • {clean_model:32} : {spend:7.4f} $ ({pct:4.1f} %)")

    print("\n Dépenses par jour d'activité :")
    for date, spend in sorted(daily_totals.items()):
        bars = "█" * int(min(25, spend))
        print(f"   • {date:10} : {spend:7.4f} $  {bars}")
    print("="*58 + "\n")

def print_key_report(label: str, key: str, info_data: dict, show_details: bool = False, base_url: str = ""):
    masked_key = key[:7] + "..." + key[-4:] if len(key) > 12 else key
    print("\n" + "="*58)
    print(f" 🔑 SUIVI DU BUDGET IA - {label.upper()}")
    print("="*58)
    print(f" - Clé API             : {masked_key}")

    if "error" in info_data:
        print(f" [!] Erreur d'interrogation : {info_data['error']}")
        print("="*58 + "\n")
        return

    info = info_data.get("info", {})
    key_token = info_data.get("key", "")
    if not info:
        print(" [!] Réponse inattendue (champ 'info' manquant).")
        print("="*58 + "\n")
        return

    key_alias = info.get("key_alias", "Non défini")
    spend = info.get("spend", 0.0)
    max_budget = info.get("max_budget")
    budget_duration = info.get("budget_duration", "N/A")
    budget_reset_at_raw = info.get("budget_reset_at")
    expires_raw = info.get("expires")
    models = info.get("models", [])
    meta = info.get("metadata", {}) or {}

    if max_budget is not None:
        remaining = max_budget - spend
        max_budget_str = f"{max_budget:.2f} $"
        remaining_str = f"{remaining:.2f} $"
    else:
        max_budget_str = "Illimité"
        remaining_str = "Illimité"

    reset_date = format_iso_date(budget_reset_at_raw)
    reset_left = calculate_time_left(budget_reset_at_raw)
    expire_date = format_iso_date(expires_raw)
    expire_left = calculate_time_left(expires_raw)

    print(f" - Alias de la clé     : {key_alias}")
    if meta.get("client") or meta.get("projet"):
        print(f" - Client / Projet     : {meta.get('client', 'N/A')} / {meta.get('projet', 'N/A')}")
    if meta.get("nmedien"):
        print(f" - Titulaire           : {meta.get('nmedien')}")
    print(f" - Solde Restant       : {remaining_str}")
    print(f" - Budget Consommé     : {spend:.4f} $")
    print(f" - Budget Maximum      : {max_budget_str}")
    print(f" - Durée du Cycle      : {budget_duration}")
    print(f" - Prochain Reset      : {reset_date} ({reset_left})")
    print(f" - Expiration Clé      : {expire_date} ({expire_left})")
    print(f" - Modèles autorisés   : {', '.join(models) if models else 'all-team-models'}")

    if show_details and spend > 0 and key_token and base_url:
        logs = fetch_spend_breakdown(key, key_token, base_url)
        print_spend_breakdown(logs)
    else:
        print("="*58 + "\n")

def main():
    parser = argparse.ArgumentParser(description="Vérification du budget LiteLLM (Nmédia Cloud)")
    parser.add_argument("project_pos", nargs="?", default=None, help="Nom du projet (ex: perso, boire, metro)")
    parser.add_argument("--project", "-p", default=None, help="Filtrer sur un projet spécifique")
    parser.add_argument("--key", "-k", default=None, help="Vérifier une clé API spécifique directement")
    parser.add_argument("--details", "-d", action="store_true", help="Afficher la ventilation détaillée de consommation")
    args = parser.parse_args()

    load_env()
    base_url = os.getenv("LITELLM_BASE_URL", "https://api-ia.nmedia.ca").rstrip("/")

    target_project = (args.project or args.project_pos or "").lower()

    if args.key:
        print(f"[*] Interrogation du proxy LiteLLM ({base_url})...")
        res = fetch_key_info(args.key, base_url)
        print_key_report("Clé Fournie", args.key, res, show_details=args.details, base_url=base_url)
        return

    # Inventaire des clés connues
    known_keys = {}

    # 1. Clé Perso / Générale
    perso_key = (
        os.getenv("LITELLM_API_KEY_PERSO")
        or get_secret_file_key("litellm-key-perso")
        or get_secret_file_key("nmedia-key-perso")
    )
    if perso_key:
        known_keys["Perso (Générale)"] = perso_key

    # 2. Clé Metro
    metro_key = (
        os.getenv("LITELLM_API_KEY_METRO")
        or get_secret_file_key("litellm-key-metro")
        or get_secret_file_key("nmedia-key-metro")
    )

    # 3. Clé Boire et Frère
    boire_key = (
        os.getenv("LITELLM_API_KEY_BOIRE")
        or get_secret_file_key("litellm-key-boire")
        or get_secret_file_key("nmedia-key-boire")
    )

    active_key = os.getenv("LITELLM_API_KEY") or get_secret_file_key("litellm-key")
    if active_key in ["LITELLM_API_KEY_BOIRE", "${LITELLM_API_KEY_BOIRE}", "boire", "BOIRE"]:
        active_key = boire_key
    elif active_key in ["LITELLM_API_KEY_METRO", "${LITELLM_API_KEY_METRO}", "metro", "METRO"]:
        active_key = metro_key
    elif active_key in ["LITELLM_API_KEY_PERSO", "${LITELLM_API_KEY_PERSO}", "perso", "PERSO"]:
        active_key = perso_key

    metro_label = "Metro [ACTIVE]" if (active_key and metro_key and active_key == metro_key) else "Metro"
    if metro_key:
        known_keys[metro_label] = metro_key

    boire_label = "Boire et Frère [ACTIVE]" if (active_key and boire_key and active_key == boire_key) else "Boire et Frère"
    if boire_key:
        known_keys[boire_label] = boire_key

    if not known_keys and active_key:
        known_keys["Active"] = active_key

    if not known_keys:
        print("[!] Erreur : Aucune clé API trouvée dans l'environnement, le fichier .env ou ~/.secrets/.")
        sys.exit(1)

    # Filtrage si demandé
    if target_project:
        filtered = {}
        for label, key in known_keys.items():
            if target_project in label.lower():
                filtered[label] = key
        if not filtered:
            print(f"[!] Aucun projet correspondant à '{target_project}'. Projets disponibles : {list(known_keys.keys())}")
            sys.exit(1)
        known_keys = filtered

    print(f"[*] Interrogation du proxy LiteLLM ({base_url}) pour {len(known_keys)} clé(s)...")
    for label, key in known_keys.items():
        res = fetch_key_info(key, base_url)
        print_key_report(label, key, res, show_details=args.details, base_url=base_url)

if __name__ == "__main__":
    main()

