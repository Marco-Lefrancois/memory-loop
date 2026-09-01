# ADR-0308 : Modèle d'Évaluations Continue, MCP Prompts et Optimisation de l'Instruction Budget

> **Statut :** Accepté  
> **Date :** 2026-08-06  
> **Contexte :** Alignement mLoop avec les standards AI Hero / Matt Pocock Evals, MCP Prompts & Progressive Disclosure  

---

## 1. Contexte & Problématique

L'écosystème mLoop disposait de contrôles statiques solides (auto-étalonnage par `calibrate.py`, validation de schémas par `wikifix.py`), mais présentait trois limites d'ingénierie agentique :

1. **Absence d'Audit Sémantique Continu (Evals)** :
   `calibrate` contrôlait l'existence de fichiers sans évaluer la qualité sémantique réelle des histoires du backlog (INVEST, 4 piliers Gherkin, vecteurs de résilience). Bien que `RubberDuckEngine` fournisse cette critique, il n'était pas intégré comme moteur de scoring automatisé.
2. **Support Incomplet du Protocol MCP (Bridges)** :
   Les bridges mLoop exposaient des outils (`tools`), mais pas de modèles de prompts (`prompts/list`, `prompts/get`) permettant au client MCP d'invoquer directement des flux standardisés (`/grill-me`, `/triage`, `/vibe-check`, `/handoff`).
3. **Pression sur l'Instruction Budget (`AGENTS.md`)** :
   Le fichier `AGENTS.md` accumulait trop de directives secondaires, consommant une part importante du budget d'attention du modèle lors de l'initialisation du système.

---

## 2. Décisions d'Architecture

### A. Moteur d'Évaluations Sémantiques (`src/pipelines/evals.py`)
- Unification du moteur `RubberDuckEngine` avec la CLI via la commande `python src/swarm.py eval --project <nom>`.
- Génération d'un **Score de Santé Sémantique (0-100%)** basé sur les assertions Gherkin, les vecteurs de résilience et le rejet des formulations vagues (*Anti-Fluff*).
- Intégration d'Evals automatisés dans la pipeline `calibrate`.

### B. Standardisation des MCP Prompts (`src/bridges/mcp_server.py`)
- Implémentation du support JSON-RPC pour `prompts/list` et `prompts/get`.
- Exposition des templates de prompts officiels mLoop : `mloop_grill_me`, `mloop_triage`, `mloop_vibe_check`, `mloop_handoff`.

### C. Nouveaux Agent Skills Canoniques (`.agents/skills/`)
- Addition des skills réutilisables `.agents/skills/triage`, `.agents/skills/wait-what` et `.agents/skills/tdd`.

### D. Garde-fous CLI Safety Hooks (`src/core/hooks.py`)
- Interception pré-exécution pour bloquer les commandes destructrices (`git push --force`, `git reset --hard`, `rm -rf`).

### E. Optimisation Progressive Disclosure (`AGENTS.md`)
- Conservation dans `AGENTS.md` uniquement des règles universelles d'amorçage et de sécurité.
- Migration des détails opérationnels spécifiques vers leurs skills respectifs.

---

## 3. Impact sur l'Écosystème mLoop

- **Qualité des Récits** : Validation sémantique continue et mesurable avant le démarrage de la phase Build.
- **Interopérabilité MCP** : Compatibilité totale avec le standard Model Context Protocol.
- **Raisonnement Agentique** : Budget d'attention libéré pour un meilleur respect du prompt utilisateur et du code.
