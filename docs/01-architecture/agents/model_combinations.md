# Combinaisons d'Agents mLoop v2

Voici 3 propositions d'architectures de modèles pour vos agents, selon vos priorités en matière de budget et de précision.

| Agent               | 💎 Combo 1 : "Qualité Absolue" | ⚖️ Combo 2 : "Sweet Spot" (Recommandé) | 🚀 Combo 3 : "Économique & Rapide" |
| :------------------ | :----------------------------- | :------------------------------------- | :--------------------------------- |
| 🔀 **Orchestrator** | `claude-sonnet-4.6-thinking`   | `gemini-3-flash-preview-thinking`      | `gpt-5-mini`                       |
| 🧠 **Plan**         | `claude-opus-4.7-thinking`     | `gemini-3.1-pro-preview-thinking`      | `claude-haiku-4.5-thinking`        |
| 💻 **Build**        | `gpt-5.3-codex`                | `claude-sonnet-4.6`                    | `codestral-2501`                   |
| 🛡️ **Sentinel**    | `gpt-5.5-thinking`             | `claude-opus-4.8`                      | `claude-haiku-4.5`                 |
| 💸 **Coût Relatif** | 🔴 **Élevé ($$$)**             | 🟡 **Modéré / Optimal ($$)**           | 🟢 **Très Faible ($)**             |
| ⏱️ **Vitesse**      | Modérée (Raisonnement lourd)   | Rapide                                 | Extrêmement rapide                 |

### Détail des consommations

#### 1. 💎 "Qualité Absolue" (Zéro-Compromis)
*   **Stratégie :** On utilise exclusivement les plus grands modèles existants avec l'option "thinking" activée partout (sauf pour le code pur).
*   **Consommation de tokens :** Massive. Le mode "thinking" d'Opus 4.7 et GPT-5.5 génère des milliers de tokens invisibles de réflexion qui sont facturés.
*   **Idéal pour :** Des architectures ultra-complexes ou des bases de code legacy sensibles où une erreur humaine/IA coûterait plus cher que le prix de l'API.

#### 2. ⚖️ "Sweet Spot" (Recommandé)
*   **Stratégie :** On alloue l'intelligence de pointe là où elle est vitale (Plan & Build avec Gemini/Claude, Sentinel avec Claude Opus 4.8). On utilise des modèles asymétriques efficients pour le reste.
*   **Consommation de tokens :** Contrôlée. `claude-opus-4.8` apporte un audit critique sans concession et un raisonnement approfondi pour le rôle Sentinel. `gemini-3-flash` est un des modèles les plus véloces et économiques du marché tout en étant excellent pour l'orchestration.
*   **Idéal pour :** Le développement quotidien. C'est le meilleur rapport Qualité/Prix.

#### 3. 🚀 "Économique & Rapide"
*   **Stratégie :** On privilégie la vitesse d'exécution et on minimise drastiquement les coûts en utilisant les modèles "légers" (Haiku, Mini, Codestral).
*   **Consommation de tokens :** Dérisoire. Ces modèles coûtent souvent 10 à 50 fois moins cher au million de tokens que les modèles "Qualité Absolue".
*   **Idéal pour :** Le prototypage rapide, les itérations intenses en mode brouillon, ou les petits scripts simples.
