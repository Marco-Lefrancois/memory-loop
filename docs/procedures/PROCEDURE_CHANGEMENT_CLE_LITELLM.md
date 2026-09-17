# 🔐 Procédure Standardisée : Changement & Bascule de Clé LiteLLM (Nmédia Cloud)

> **Document de Référence Opérationnelle (SOP)**  
> **Date de mise à jour :** 17 septembre 2026  
> **Statut :** Officiel, Appliqué & Testé  
> **Projets concernés :** Boire et Frère, Metro, Personnel, Memory Loop (mLoop)

---

## 🎯 Pourquoi cette procédure existe-t-elle ?

Pour éliminer définitivement le risque de mélange des clés brutes (`sk-...`) et la désynchronisation entre sous-systèmes. Dans notre environnement, la clé LiteLLM est consommée par **4 composants distincts** :

1. **OpenCode (`opencode.json`)** : Le runtime Go/Rust lit la clé active via le pointeur dynamique `"{file:~/.secrets/litellm-key}"`.
2. **Framework mLoop Python (`src/core/llm_client.py`, `src/swarm.py`, `token_ledger.py`)** : Résout la variable `LITELLM_API_KEY` depuis [`.env`](file:///C:/Memory%20Loop/.env) avec support du **déréférencement automatique de variable**.
3. **Processus & Shells Windows** : Héritent de la variable d'environnement utilisateur Windows (`User` scope `LITELLM_API_KEY`).
4. **Sous-projets / Exports (`tools/export/mloop-lite/.env`)** : Contiennent une variable locale `NMEDIA_CLOUD_API_KEY`.

---

## 💡 Le Standard Anti-Erreur dans `.env` : Le Déréférencement

Pour ne plus **JAMAIS** mélanger les clés brutes (`sk-...`) ni coller une clé Metro sous un commentaire Boire, la variable `LITELLM_API_KEY` dans [`.env`](file:///C:/Memory%20Loop/.env) prend désormais directement le **nom de la variable inventaire** :

```env
# ==============================================
# 🤖 LiteLLM Cloud (Proxy IA)
# ==============================================
LITELLM_BASE_URL=https://api-ia.nmedia.ca

# Clé active du moment (Boire et Frère)
LITELLM_API_KEY=LITELLM_API_KEY_BOIRE

# Inventaire des 3 clés disponibles (définies dans votre .env local ou ~/.secrets/) :
LITELLM_API_KEY_PERSO=sk-perso-xxxxxx
LITELLM_API_KEY_METRO=sk-metro-xxxxxx
LITELLM_API_KEY_BOIRE=sk-boire-xxxxxx
MLOOP_ALLOW_CROSS_KEY=0
```

> ⚡ **Comment ça marche ?**  
> Le socle mLoop (`LLMClient`, `TokenLedger`, `check_budget.py`, `switch_key.py`) résout automatiquement `LITELLM_API_KEY_BOIRE` (ou `METRO`, `PERSO`) vers sa vraie valeur `sk-...`. **Aucune copie manuelle de clé brute n'est requise.**

---

## ⚡ Méthode 1 : La Commande Unique (Recommandée à 100%)

L'outil unifié gère les 5 synchronisations de manière atomique en une seule ligne :

### Syntaxe PowerShell / CMD :

```powershell
# Pour basculer sur Boire et Frère :
python tools/budget/switch_key.py boire

# Pour basculer sur Metro :
python tools/budget/switch_key.py metro

# Pour basculer sur la clé Perso :
python tools/budget/switch_key.py perso

# Mode interactif (menu avec solde en direct) :
python tools/budget/switch_key.py

# Bascule + test d'inférence en direct (HTTP 200) :
python tools/budget/switch_key.py boire --test
```

*(Ou directement via le raccourci Windows : `tools\budget\switch_key.bat boire`)*

### Ce que la commande exécute automatiquement :
- ✅ **`[1/5]` `~/.secrets/litellm-key` & `nmedia-key`** : Réécriture de la clé brute active pour OpenCode.
- ✅ **`[2/5]` `.env` (racine)** : Référencement propre `LITELLM_API_KEY=LITELLM_API_KEY_<CIBLE>` avec le bon libellé.
- ✅ **`[3/5]` `opencode.json`** : Pointeur dynamique `"{file:~/.secrets/litellm-key}"` garanti.
- ✅ **`[4/5]` Variable Windows** : Mise à jour de `[System.Environment]::SetEnvironmentVariable('LITELLM_API_KEY', ..., 'User')`.
- ✅ **`[5/5]` `mloop-lite/.env`** : Mise à jour de `NMEDIA_CLOUD_API_KEY` si présent.
- 📊 **Validation en direct** : Interrogation immédiate du solde auprès du proxy `https://api-ia.nmedia.ca/key/info`.

---

## 🛠️ Méthode 2 : Procédure Manuelle

Si vous préférez modifier manuellement :

### Étape 1 : Ajuster `.env` à la racine
Dans [`.env`](file:///C:/Memory%20Loop/.env), changez simplement la référence de la variable active :
```env
# Pour Boire :
LITELLM_API_KEY=LITELLM_API_KEY_BOIRE

# Pour Metro :
LITELLM_API_KEY=LITELLM_API_KEY_METRO

# Pour Perso :
LITELLM_API_KEY=LITELLM_API_KEY_PERSO
```

### Étape 2 : Synchroniser le secret OpenCode
Dans PowerShell (en copiant directement depuis le secret existant, sans afficher la clé) :
```powershell
# Pour Boire :
Copy-Item "$HOME\.secrets\litellm-key-boire" "$HOME\.secrets\litellm-key" -Force

# Pour Metro :
Copy-Item "$HOME\.secrets\litellm-key-metro" "$HOME\.secrets\litellm-key" -Force

# Pour Perso :
Copy-Item "$HOME\.secrets\litellm-key-perso" "$HOME\.secrets\litellm-key" -Force
```

### Étape 3 : Mettre à jour la variable d'environnement Windows
Dans PowerShell (résout directement depuis le secret sans exposer la clé) :
```powershell
[System.Environment]::SetEnvironmentVariable('LITELLM_API_KEY', (Get-Content "$HOME\.secrets\litellm-key" -Raw).Trim(), 'User')
$env:LITELLM_API_KEY = (Get-Content "$HOME\.secrets\litellm-key" -Raw).Trim()
```

---

## 📊 Vérification Immédiate du Statut

Pour vérifier à tout moment l'état des budgets et valider quelle clé est active :

```powershell
python tools/budget/check_budget.py
```

Résultat attendu :
- La clé active est signalée par la balise `[ACTIVE]` (ex: `BOIRE ET FRÈRE [ACTIVE]`).
- Le solde restant et le budget consommé sont affichés en direct.
