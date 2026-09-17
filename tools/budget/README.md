# 📓 Outil de Suivi & Bascule de Budget LiteLLM (Nmédia Cloud)

Ce sous-répertoire regroupe l'utilitaire de monitoring, le script de bascule automatique de clé et la documentation opérationnelle pour vos clés virtuelles LiteLLM (Nmédia Cloud).

---

## 🔄 Bascule Rapide de Clé Active (Commande Unique)

Pour changer de clé sans risque de désynchronisation entre OpenCode, `.env` et Windows :

```bash
# Basculer vers Boire et Frère :
python tools/budget/switch_key.py boire

# Basculer vers Metro :
python tools/budget/switch_key.py metro

# Basculer vers la clé Perso :
python tools/budget/switch_key.py perso

# Mode interactif (menu avec solde) :
python tools/budget/switch_key.py

# Raccourci Windows natif :
tools\budget\switch_key.bat boire
```
> 📖 Consultez la [Procédure Opérationnelle Détaillée](../../docs/procedures/PROCEDURE_CHANGEMENT_CLE_LITELLM.md).

---

## 🛠️ Usage du Script de Monitoring (`check_budget.py`)

Vous pouvez interroger votre budget en direct depuis le terminal à la racine de votre workspace :

```bash
# Vérifier toutes les clés actives configurées (Perso, Metro, Boire)
python tools/budget/check_budget.py

# Afficher la ventilation détaillée de la consommation (par modèle et par jour)
python tools/budget/check_budget.py --details
python tools/budget/check_budget.py --project perso --details

# Filtrer sur un projet spécifique
python tools/budget/check_budget.py --project metro
python tools/budget/check_budget.py --project boire

# Interroger directement une clé spécifique
python tools/budget/check_budget.py --key sk-m3N2J1...
```

### 📋 Exemple de Sortie Détaillée (`--details`)

```text
[*] Interrogation du proxy LiteLLM (https://api-ia.nmedia.ca) pour 1 clé(s)...

==========================================================
 🔑 SUIVI DU BUDGET IA - PERSO (GÉNÉRALE)
==========================================================
 - Clé API             : sk-jeUj...7Uqw
 - Alias de la clé     : mlefrancois
 - Titulaire           : mlefrancois
 - Solde Restant       : 1.26 $
 - Budget Consommé     : 98.7404 $
 - Budget Maximum      : 100.00 $
 - Durée du Cycle      : 30d
 - Prochain Reset      : 2026-09-01 00:00:00 UTC (13 jours et 13 heures restants)
 - Expiration Clé      : 2027-01-26 19:29:17 UTC (161 jours et 8 heures restants)
 - Modèles autorisés   : all-team-models
 📊 VENTILATION DE LA CONSOMMATION (CYCLE EN COURS) :
 ----------------------------------------------------
 Modèles les plus consommateurs :
   • gemini-3.1-pro-preview           : 38.4081 $ (38.9 %)
   • gemini-3-flash-preview           : 23.6441 $ (23.9 %)
   • claude-opus-4-8                  : 21.3999 $ (21.7 %)
   • claude-opus-4-6                  :  9.3839 $ ( 9.5 %)
   • gpt-5.5                          :  2.8616 $ ( 2.9 %)
   • gemini-3.1-flash-lite            :  1.7504 $ ( 1.8 %)
   • claude-haiku-4-5-20251001        :  1.2919 $ ( 1.3 %)
   • gpt-5.4-mini                     :  0.0002 $ ( 0.0 %)

 Dépenses par jour d'activité :
   • 2026-08-03 : 26.5552 $  █████████████████████████
   • 2026-08-04 : 13.3677 $  █████████████
   • 2026-08-05 :  4.9355 $  ████
   • 2026-08-06 :  8.8296 $  ████████
   • 2026-08-07 :  0.8204 $  
   • 2026-08-10 : 13.9373 $  █████████████
   • 2026-08-11 : 24.2623 $  ████████████████████████
   • 2026-08-12 :  0.8957 $  
   • 2026-08-13 :  4.3875 $  ████
   • 2026-08-17 :  0.7492 $  
==========================================================
```

```text
[*] Interrogation du proxy LiteLLM (https://api-ia.nmedia.ca) pour 3 clé(s)...

==========================================================
 🔑 SUIVI DU BUDGET IA - GLOBAL (DÉFAUT)
==========================================================
 - Clé API             : sk-jeUj...7Uqw
 - Alias de la clé     : mlefrancois
 - Titulaire           : mlefrancois
 - Solde Restant       : 1.26 $
 - Budget Consommé     : 98.7404 $
 - Budget Maximum      : 100.00 $
 - Durée du Cycle      : 30d
 - Prochain Reset      : 2026-09-01 00:00:00 UTC (13 jours restants)
 - Expiration Clé      : 2027-01-26 19:29:17 UTC
 - Modèles autorisés   : all-team-models
==========================================================

==========================================================
 🔑 SUIVI DU BUDGET IA - BOIRE ET FRÈRE
==========================================================
 - Clé API             : sk-o2o1...pbwg
 - Alias de la clé     : mlefrancois - boire
 - Client / Projet     : Boire et frere / Boire
 - Titulaire           : mlefrancois
 - Solde Restant       : 100.00 $
 - Budget Consommé     : 0.0000 $
 - Budget Maximum      : 100.00 $
 - Durée du Cycle      : 30d
 - Prochain Reset      : 2026-09-01 00:00:00 UTC
 - Expiration Clé      : 2027-02-13 15:24:45 UTC (179 jours restants)
 - Modèles autorisés   : all-team-models
==========================================================

==========================================================
 🔑 SUIVI DU BUDGET IA - METRO
==========================================================
 - Clé API             : sk-m3N2...FdAA
 - Alias de la clé     : mlefrancois -Metro
 - Client / Projet     : Metro / Metro
 - Titulaire           : mlefrancois
 - Solde Restant       : 100.00 $
 - Budget Consommé     : 0.0000 $
 - Budget Maximum      : 100.00 $
 - Durée du Cycle      : 30d
 - Prochain Reset      : 2026-09-01 00:00:00 UTC
 - Expiration Clé      : 2027-02-13 15:26:51 UTC (179 jours restants)
 - Modèles autorisés   : all-team-models
==========================================================
```

---

## 📊 Analyse Détaillée de la Consommation (Modèles & Facteurs de Coût)

La commande `--details` interroge l'endpoint `/spend/logs` pour ventiler les coûts par modèle et identifier les pics d'activité.

### 💡 Pourquoi la consommation augmente rapidement ?

| Modèle IA | Famille | Ratio de Coût | Recommandation d'Usage |
| :--- | :--- | :---: | :--- |
| **`claude-opus-4-8` / `4-6`** | Anthropic Opus | 🔴 Très élevé | À réserver pour les arbitrages d'architecture et synthèses complexes. |
| **`gemini-3.1-pro-preview`** | Google Pro | 🟠 Élevé | À utiliser pour les analyses approfondies (Plan / DDD). |
| **`gemini-3-flash-preview`** | Google Flash | 🟡 Modéré | Bon compromis vitesse / capacité. |
| **`gemini-3.1-flash-lite`** | Google Flash Lite | 🟢 Très faible | ⚡ **Recommandé par défaut** pour le dev, QA, extraction et batch. |
| **`claude-haiku-4-5`** | Anthropic Haiku | 🟢 Très faible | ⚡ Idéal pour les petites tâches rapides et les tests. |

> [!TIP]
> **Bonne pratique** : Utiliser `gemini-3.1-flash-lite` pour 80% des tâches quotidiennes permet de traiter des millions de tokens pour moins de 2$/mois, tout en réservant **Gemini Pro** ou **Claude Opus** pour les étapes clés d'architecture.

---

## 🔐 Configuration requise

Le script résout automatiquement les variables d'environnement en inspectant le fichier `.env` à la racine ainsi que la voûte de secrets utilisateur `~/.secrets/`.

### Variables dans votre `.env` à la racine :
```env
# ==============================================
# 🤖 LiteLLM Cloud (Proxy IA)
# ==============================================
LITELLM_BASE_URL=https://api-ia.nmedia.ca

# Clé active du moment (Boire et Frère) — Référencement direct supporté
LITELLM_API_KEY=LITELLM_API_KEY_BOIRE

# Inventaire des 3 clés disponibles :
LITELLM_API_KEY_PERSO=sk-perso-xxxxxx
LITELLM_API_KEY_METRO=sk-metro-xxxxxx
LITELLM_API_KEY_BOIRE=sk-boire-xxxxxx
```

### Stockage dans la voûte de secrets (`~/.secrets/`) :
- `~/.secrets/litellm-key` : Clé brute active (utilisée dynamiquement par `opencode.json`)
- `~/.secrets/litellm-key-perso` : Clé Personnelle / Générale
- `~/.secrets/litellm-key-metro` : Clé Metro
- `~/.secrets/litellm-key-boire` : Clé Boire et Frère

---

## 📡 Documentation Technique de l'API LiteLLM

Le script interroge deux endpoints du proxy LiteLLM :

1. **`/key/info`** : Reçoit les métadonnées de la clé, les plafonds et la date de renouvellement.
2. **`/spend/logs`** : Historique journalier et répartition par modèle (activé avec `--details`).

### Schéma des métadonnées exploitées par l'API :

| Champ API | Endpoint | Rôle |
| :--- | :---: | :--- |
| `info.key_alias` | `/key/info` | Alias de l'utilisateur ou du projet associé à la clé (ex: `mlefrancois`). |
| `info.spend` | `/key/info` | Somme cumulée dépensée sur le cycle actuel en USD. |
| `info.max_budget` | `/key/info` | Plafond de dépenses autorisé pour le cycle (ex: `100.00`). |
| `info.budget_duration` | `/key/info` | Durée de vie d'une enveloppe budgétaire (ex: `30d`). |
| `info.budget_reset_at` | `/key/info` | Date ISO du prochain renouvellement à zéro du budget. |
| `info.expires` | `/key/info` | Date de péremption de la clé. |
| `info.models` | `/key/info` | Liste des groupes de modèles autorisés pour cette clé. |
| `startTime` / `models` | `/spend/logs` | Ventilation chronologique journalière et coût par modèle. |
