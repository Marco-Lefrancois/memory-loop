# -*- coding: utf-8 -*-
"""
Outil utilitaire de bascule automatique de cle LiteLLM (Nmedia Cloud).
Synchronise de facon atomique tous les points de contact :
1. ~/.secrets/litellm-key & ~/.secrets/nmedia-key (Source principale OpenCode)
2. .env (racine) -> LITELLM_API_KEY (Source Python mLoop / CLI)
3. opencode.json -> pointe vers {file:~/.secrets/litellm-key}
4. Variable d environnement Windows utilisateur (scope User & Process)
5. tools/export/mloop-lite/.env -> NMEDIA_CLOUD_API_KEY (si existant)

Usage:
    python tools/budget/switch_key.py boire
    python tools/budget/switch_key.py metro
    python tools/budget/switch_key.py perso
    python tools/budget/switch_key.py sk-...
    python tools/budget/switch_key.py --test
"""

import os
import sys
import json
import re
import argparse
import subprocess
from pathlib import Path
import httpx


KNOWN_KEY_MAPPING = {
    "boire": "LITELLM_API_KEY_BOIRE",
    "boirefrere": "LITELLM_API_KEY_BOIRE",
    "boire et frere": "LITELLM_API_KEY_BOIRE",
    "metro": "LITELLM_API_KEY_METRO",
    "perso": "LITELLM_API_KEY_PERSO",
    "personnel": "LITELLM_API_KEY_PERSO",
    "generale": "LITELLM_API_KEY_PERSO",
}

PROJECT_LABELS = {
    "LITELLM_API_KEY_BOIRE": "Boire et Frere",
    "LITELLM_API_KEY_METRO": "Metro",
    "LITELLM_API_KEY_PERSO": "Perso (Generale)",
}


def get_root_dir() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def load_env_inventory(root_dir: Path) -> dict:
    inventory = {}
    env_file = root_dir / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip("'\"")
                if k in ["LITELLM_API_KEY_BOIRE", "LITELLM_API_KEY_METRO", "LITELLM_API_KEY_PERSO", "LITELLM_API_KEY"]:
                    inventory[k] = v

    secrets_dir = Path.home() / ".secrets"
    for var_name, secret_suffix in [
        ("LITELLM_API_KEY_BOIRE", "litellm-key-boire"),
        ("LITELLM_API_KEY_METRO", "litellm-key-metro"),
        ("LITELLM_API_KEY_PERSO", "litellm-key-perso"),
    ]:
        if var_name not in inventory:
            sec_file = secrets_dir / secret_suffix
            if sec_file.exists():
                val = sec_file.read_text(encoding="utf-8").strip()
                if val:
                    inventory[var_name] = val

    return inventory


def fetch_key_info(api_key: str, base_url: str = "https://api-ia.nmedia.ca") -> dict:
    url = f"{base_url.rstrip('/')}/key/info"
    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        response = httpx.get(url, headers=headers, timeout=10.0)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}


def update_env_file(root_dir: Path, target_key: str, label: str, env_var_ref: str = "") -> bool:
    env_file = root_dir / ".env"
    if not env_file.exists():
        return False

    content = env_file.read_text(encoding="utf-8")
    pattern = r"(#\s*Cl[eé]\s+active\s+du\s+moment.*?\n)?(LITELLM_API_KEY=)([^\r\n]+)"
    val_to_write = env_var_ref if env_var_ref else target_key
    replacement = rf"# Clé active du moment ({label})\nLITELLM_API_KEY={val_to_write}"

    if re.search(pattern, content):
        new_content = re.sub(pattern, replacement, content, count=1)
    else:
        new_content = content + f"\nLITELLM_API_KEY={target_key}\n"

    env_file.write_text(new_content, encoding="utf-8")
    return True


def update_secrets_vault(target_key: str):
    secrets_dir = Path.home() / ".secrets"
    secrets_dir.mkdir(parents=True, exist_ok=True)
    for secret_name in ["litellm-key", "nmedia-key"]:
        target_path = secrets_dir / secret_name
        target_path.write_text(target_key, encoding="utf-8")


def update_opencode_json(root_dir: Path) -> bool:
    opencode_path = root_dir / "opencode.json"
    if not opencode_path.exists():
        return False

    try:
        data = json.loads(opencode_path.read_text(encoding="utf-8"))
        if "provider" in data and "nmedia_cloud" in data["provider"]:
            if "options" in data["provider"]["nmedia_cloud"]:
                data["provider"]["nmedia_cloud"]["options"]["apiKey"] = "{file:~/.secrets/litellm-key}"
                opencode_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
                return True
    except Exception as e:
        print(f"[!] Erreur mise a jour opencode.json: {e}")
    return False


def update_mloop_lite_env(root_dir: Path, target_key: str) -> bool:
    mloop_lite_env = root_dir / "tools" / "export" / "mloop-lite" / ".env"
    if not mloop_lite_env.exists():
        return False

    content = mloop_lite_env.read_text(encoding="utf-8")
    new_content = re.sub(r"NMEDIA_CLOUD_API_KEY=[^\r\n]+", f"NMEDIA_CLOUD_API_KEY={target_key}", content)
    mloop_lite_env.write_text(new_content, encoding="utf-8")
    return True


def update_windows_user_env(target_key: str):
    if sys.platform == "win32":
        try:
            ps_cmd = f"[System.Environment]::SetEnvironmentVariable('LITELLM_API_KEY', '{target_key}', 'User')"
            subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True, timeout=5)
        except Exception:
            pass


def test_llm_inference(target_key: str, base_url: str = "https://api-ia.nmedia.ca"):
    print("[*] Execution d un test d inference en direct (gemini-3.8-flash)...")
    url = f"{base_url.rstrip('/')}/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {target_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "gemini-3.8-flash",
        "messages": [
            {"role": "system", "content": "Assistant concis"},
            {"role": "user", "content": "Reponds uniquement par: PING_OK"},
        ],
        "max_tokens": 60,
        "temperature": 0.0,
    }
    try:
        resp = httpx.post(url, headers=headers, json=payload, timeout=15.0)
        if resp.status_code == 200:
            data = resp.json()
            msg = data.get("choices", [{}])[0].get("message", {})
            ans = (msg.get("content") or "").strip()
            print(f"    [PASS] Reponse LiteLLM recue : '{ans}' (Status 200 OK)")
        else:
            print(f"    [FAIL] Erreur API : {resp.status_code} - {resp.text}")
    except Exception as e:
        print(f"    [FAIL] Exception lors du test : {e}")


def switch_to_key(target_input: str, run_test: bool = False):
    root_dir = get_root_dir()
    inventory = load_env_inventory(root_dir)

    norm_target = target_input.strip().lower()
    target_key = None
    target_label = "Cle Specifique"
    target_env_var = None

    if norm_target in KNOWN_KEY_MAPPING:
        target_env_var = KNOWN_KEY_MAPPING[norm_target]
        target_key = inventory.get(target_env_var)
        target_label = PROJECT_LABELS.get(target_env_var, norm_target.capitalize())
    elif norm_target.startswith("sk-"):
        target_key = target_input.strip()
        for env_var, key_val in inventory.items():
            if key_val == target_key and env_var in PROJECT_LABELS:
                target_label = PROJECT_LABELS[env_var]
                target_env_var = env_var
                break
    else:
        for env_var, label in PROJECT_LABELS.items():
            if norm_target in label.lower() or norm_target in env_var.lower():
                target_key = inventory.get(env_var)
                target_label = label
                target_env_var = env_var
                break

    if not target_key:
        print(f"[!] Erreur : Cible inconnue '{target_input}'.")
        print("    Cibles valides : 'boire', 'metro', 'perso', ou une cle brute 'sk-...'")
        sys.exit(1)

    print(f"\n==========================================================")
    print(f" [BASCULE DE CLE LITELLM] -> {target_label.upper()}")
    print(f"==========================================================")
    masked = target_key[:7] + "..." + target_key[-4:] if len(target_key) > 12 else target_key
    print(f" - Cle cible           : {masked}")

    # 1. Update ~/.secrets/ (SSOT pour OpenCode)
    update_secrets_vault(target_key)
    print(f" [1/5] ~/.secrets/litellm-key  : [OK] Synchronise")

    # 2. Update .env (SSOT pour Python mLoop)
    ok_env = update_env_file(root_dir, target_key, target_label, env_var_ref=target_env_var)
    print(f" [2/5] Racine .env             : {'[OK] Synchronise' if ok_env else '[!] Non trouve'}")

    # 3. Update opencode.json ({file:~/.secrets/litellm-key})
    ok_opencode = update_opencode_json(root_dir)
    print(f" [3/5] opencode.json           : {'[OK] Pointeur dynamique configure' if ok_opencode else '[!] Non trouve'}")

    # 4. Update Windows User Env Var
    update_windows_user_env(target_key)
    print(f" [4/5] Windows Env (User)      : [OK] LITELLM_API_KEY synchronise")

    # 5. Update mloop-lite .env si present
    ok_mloop_lite = update_mloop_lite_env(root_dir, target_key)
    if ok_mloop_lite:
        print(f" [5/5] mloop-lite/.env         : [OK] Synchronise")
    else:
        print(f" [5/5] mloop-lite/.env         : Ignore (non present)")

    os.environ["LITELLM_API_KEY"] = target_key

    # Verification solde LiteLLM
    print("\n[*] Interrogation du proxy LiteLLM...")
    info = fetch_key_info(target_key)
    if "error" in info:
        print(f" [!] Avertissement API : {info['error']}")
    else:
        info_data = info.get("info", {})
        max_b = info_data.get("max_budget", 0) or 0
        spend = info_data.get("spend", 0) or 0
        remain = max_b - spend
        alias = info_data.get("key_alias", "N/A")
        print(f" [OK] Cle active validee sur Nmedia Cloud !")
        print(f"   - Alias             : {alias}")
        print(f"   - Solde Restant     : {remain:.2f} $ (Consomme: {spend:.4f} $ / {max_b:.2f} $)")
        if remain <= 0:
            print("   [!] ATTENTION : Cette cle a depasse son budget autorise !")

    if run_test:
        print("")
        test_llm_inference(target_key)

    print(f"\n==========================================================")
    print(f" BASCULE TERMINEE AVEC SUCCES")
    print(f"==========================================================\n")


def main():
    parser = argparse.ArgumentParser(description="Bascule automatique de la cle active LiteLLM")
    parser.add_argument("target", nargs="?", help="Cible : 'boire', 'metro', 'perso', ou cle 'sk-...'")
    parser.add_argument("--test", "-t", action="store_true", help="Executer une completion de test apres la bascule")
    args = parser.parse_args()

    if not args.target:
        root_dir = get_root_dir()
        inv = load_env_inventory(root_dir)
        print("\n==========================================================")
        print(" SELECTION DE LA CLE LITELLM ACTIVE")
        print("==========================================================")
        options = [
            ("boire", "Boire et Frere", inv.get("LITELLM_API_KEY_BOIRE", "")),
            ("metro", "Metro", inv.get("LITELLM_API_KEY_METRO", "")),
            ("perso", "Perso (Generale)", inv.get("LITELLM_API_KEY_PERSO", "")),
        ]
        for idx, (code, label, k) in enumerate(options, start=1):
            m = k[:7] + "..." + k[-4:] if len(k) > 12 else k
            print(f" [{idx}] {label:<18} ({code}) -> {m}")
        print("==========================================================")
        choice = input("Choisissez le numero (1-3) ou le nom du projet : ").strip().lower()
        if choice in ["1", "boire"]:
            target = "boire"
        elif choice in ["2", "metro"]:
            target = "metro"
        elif choice in ["3", "perso"]:
            target = "perso"
        else:
            target = choice
    else:
        target = args.target

    switch_to_key(target, run_test=args.test)


if __name__ == "__main__":
    main()
