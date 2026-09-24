# 🏛️ ADR-0386 : Gouvernance GitHub Rulesets, Flux de Pull Requests Obligatoire & Protocole de Livraison Phase 5 (SHIP)

- **Statut** : ACCEPTÉ
- **Date** : 24 septembre 2026
- **Décideurs** : Marco (Utilisateur) & Antigravity (Agentic Architect)
- **En lien avec** : 
  - [ADR-0202](0202-modularite-interne-agents.md) (Modularité Interne des Agents & Seuils ≤ 300L)
  - [ADR-0319](0319-dual-agent-handoff-openspec-ready.md) (Dual Agent Handoff & Dépôts Agnostiques)
  - [ADR-0369](0369-standards-robustesse-python-senior.md) (Standards de Robustesse Senior)
  - [ADR-0375](0375-project-lifecycle-5-phases-and-analysis-types.md) (Cycle de Vie Unifié en 5 Phases Universelles)
  - [ADR-0376](0376-standard-rigueur-360-zero-blindspot.md) (Standard Rigueur 360° Zéro Blindspot)
  - [ADR-0379](0379-standards-graph-and-runtime-confinement-shield.md) (StandardsGraph & Confinement Shield)
  - [ADR-0385](0385-protocole-falsification-frontieres-architecture-immunite-cognitive.md) (Protocole de Falsification des Frontières)

---

## 🧭 1. Contexte & Problématique

Lors des opérations d'ingénierie et de synchronisation vers le dépôt public GitHub (`https://github.com/Marco-Lefrancois/memory-loop.git`), le serveur distant a émis le rejet protecteur suivant :

```text
remote: Bypassed rule violations for refs/heads/main:
remote: - Changes must be made through a pull request.
```

Cette alerte a mis en évidence un point de friction critique dans le comportement des agents autonomes (Antigravity, GitHub Copilot, OpenCode, Claude Code, Herdr workers) :

1. **Le réflexe d'écriture directe sur `main`** :  
   Par commodité ou accélération d'exécution, les agents d'orchestration ont tendance à pousser leurs commits directement sur la branche principale (`main`), court-circuitant ainsi les règles de protection de branches (*Branch Protection Rules / GitHub Rulesets*).

2. **L'illusion du contournement administrateur (*Admin Bypass Bias*)** :  
   Parce que la clé SSH ou le jeton Git de l'utilisateur détient les droits d'administration sur le dépôt, le push direct réussit grâce au mécanisme de *Bypass*. Cependant, ce comportement est une **faille de gouvernance majeure** :
   - Il habitue l'agent à ignorer les règles déterministes de la forge logicielle.
   - Il empêche les collègues ou pairs de procéder à une revue contradictoire formelle.
   - Il court-circuite la validation CI/CD distante indépendante.
   - Il compromet l'intégrité de la **Phase 5 (SHIP & SYNC)** définie dans l'ADR-0375.

3. **Le besoin d'un protocole universel pour la Phase 5 (SHIP)** :  
   Dans l'architecture cognitive mLoop, la Phase 5 ne consiste pas simplement à « pousser du code ». C'est une porte de certification d'ingénierie tripartite : **Code Source Git + Backlog Jira/DevOps + Graphe de Connaissances Graphify**.

---

## 🏛️ 2. Décisions d'Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│             GOUVERNANCE GITHUB & PROTOCOLE PHASE 5 (SHIP)              │
│                              (ADR-0386)                                │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
       ┌────────────────────────────┼────────────────────────────┐
       ▼                            ▼                            ▼
┌──────────────┐             ┌──────────────┐             ┌──────────────┐
│  PILIER 1    │             │  PILIER 2    │             │  PILIER 3    │
│  Zero Direct │             │  Garde-Fous  │             │  Gabarit PR  │
│  Push `main` │             │  Porte 5     │             │  Standardisé │
└──────┬───────┘             └──────┬───────┘             └──────┬───────┘
       │                            │                            │
       └────────────────────────────┼────────────────────────────┘
                                    ▼
       ┌─────────────────────────────────────────────────────────┐
       │                       PILIER 4                          │
       │           Synchronisation Tripartite Post-Merge         │
       └─────────────────────────────────────────────────────────┘
```

### Pilier 1 : Interdiction Absolue de Direct Push sur `main` par les Agents
1. **Règle d'or** : Aucun agent autonome ou subagent n'est autorisé à exécuter `git push origin main`.
2. **Isolation par branche de travail** :
   Toute tâche, récit ou correctif doit OBLIGATOIREMENT être isolé dans une branche dédiée selon la nomenclature canonique :
   - `feat/<story-id>-<slug>` : Pour une User Story (ex: `feat/MLOOP-152-drawdb-export`).
   - `fix/<issue-id>-<slug>` : Pour un correctif de bug ou régression.
   - `refactor/<epic-id>-<slug>` : Pour une refactorisation modulaire (ex: `refactor/EPIC-17-modular-extraction`).
   - `docs/<scope>-<slug>` : Pour des mises à niveau documentaires pures.
3. **Bypass Exceptionnel (Sovereign Override)** :  
   Le bypass des règles GitHub n'est toléré que pour l'utilisateur humain agissant en souveraineté absolue pour un hotfix critique d'infrastructure, et doit être consigné dans le journal d'audit de session.

---

### Pilier 2 : Garde-Fous Pré-Vol Obligatoires de la Porte 5 (Gate 5 Pre-Flight)
Avant toute demande de création de Pull Request ou de livraison par un agent, les 4 contrôles suivants doivent être validés avec un code de retour `0` (Zero Exception) :

1. **Vibe-Check Déterministe (Contrôle 23/23)** :
   ```powershell
   uv run python src/swarm.py vibe-check --project <nom_projet>
   ```
   *Exigence* : 0 FAIL. Tout avertissement doit être explicité dans le corps de la PR.

2. **Harnais de Tests E2E & Unitaires** :
   ```powershell
   uv run pytest
   ```
   *Exigence* : 100 % de succès. Interdiction de désactiver ou sauter des tests (`@pytest.mark.skip`) sans ADR justificative.

3. **Linter AST Déterministe (Plafond ADR-0202 & Anti-Aggravation MLOOP-171-BE)** :
   ```powershell
   uv run python src/swarm.py code-check --all
   ```
   *Exigence* : Tous les modules doivent respecter ≤ 300 lignes / 15 Ko ou satisfaire la non-aggravation `ast_delta_checker`.

4. **Bouclier Anti-Leak & Zéro Donnée Privée** :
   - Vérification que `.env` et `opencode.json` sont strictement ignorés par `.gitignore`.
   - Vérification que les fichiers modèles (`.env.example`, `opencode.example.json`) ne contiennent aucune clé d'API, aucun domaine privé d'entreprise et aucun modèle non validé.

---

### Pilier 3 : Standardisation du Gabarit de Pull Request (`.github/pull_request_template.md`)
Tout dépôt mLoop intègre un gabarit de PR imposant la transparence totale sur les 4 Piliers Gherkin, le résultat du Vibe-Check et la traçabilité des modifications :

- **Contexte & Motivation** : Problème résolu, référence au ticket Jira / User Story.
- **Modifications Architecturales** : Liste des fichiers impactés, conformité ADR-0202.
- **Rapport de Preuve Déterministe** :
  - Sortie du Vibe-Check (`XX PASS / 0 FAIL`).
  - Sortie de Pytest (`XXXX passed`).
- **Checklist Zéro-Fuite** : Validation de l'absence de secrets, tokens ou endpoints privés.

---

### Pilier 4 : Synchronisation Tripartite Post-Merge (Phase 5 Ship & Sync)
La fermeture du cycle de vie d'un récit ne s'arrête pas au clic de merge sur GitHub. L'agent responsable de la Phase 5 doit exécuter la séquence mécanique suivante :

```
                ┌─────────────────────────────────────┐
                │          PR Mergée sur main         │
                └──────────────────┬──────────────────┘
                                   │
      ┌────────────────────────────┼────────────────────────────┐
      ▼                            ▼                            ▼
┌──────────────────┐      ┌──────────────────┐      ┌──────────────────┐
│   1. CODE & GIT  │      │   2. JIRA / ADO  │      │   3. GRAPHIFY    │
│  Checkout main   │      │   Transition     │      │   Auto-Healing   │
│  git pull        │      │   DONE_SHIPPED   │      │   Sync Graphe    │
└──────────────────┘      └──────────────────┘      └──────────────────┘
```

1. **Alignement Local** :
   ```powershell
   git checkout main
   git pull origin main
   ```
2. **Clôture Backlog & Récits** :
   Mise à jour du frontmatter du récit (`status: DONE_SHIPPED`), horodatage et clôture du ticket sur Jira / Azure DevOps (`python src/swarm.py jira_sync`).
3. **Pérennisation du Graphe de Connaissances** :
   Exécution de `python src/swarm.py sync --project <P>` pour mettre à jour SQLite FTS5 et le graphe Graphify.
4. **Enregistrement des Coûts & Jetons** :
   Consignation des tokens consommés dans le `token_ledger.jsonl` de projet et global.

---

## 🛠️ 3. Protocole Opérationnel pour les Agents (Cheatsheet)

Lorsqu'un agent ou coworker est mandaté pour implémenter un récit et le livrer en Phase 5, il applique la séquence stricte ci-dessous :

```bash
# --- ÉTAPE 1 : Isolation sur branche dédiée ---
git checkout -b feat/MLOOP-XXX-description

# --- ÉTAPE 2 : Cycle d'implémentation (Phase 3 Build & Phase 4 Validate) ---
# [Développement, tests TDD, exécution du code]
uv run pytest
uv run python src/swarm.py vibe-check --project mLoop

# --- ÉTAPE 3 : Commit atomique conforme ---
git add <fichiers_modifies>
git commit -m "feat(scope): MLOOP-XXX description claire"

# --- ÉTAPE 4 : Push de la branche et création de la PR ---
git push -u origin feat/MLOOP-XXX-description

# Utilisation de GitHub CLI (gh) si disponible, ou guidage de l'utilisateur
gh pr create --title "feat(scope): MLOOP-XXX description" --body-file .github/pull_request_template.md

# --- ÉTAPE 5 : Post-Merge (Phase 5 Ship & Sync) ---
# Après merge de la PR :
git checkout main
git pull origin main
python src/swarm.py sync --project mLoop
```

---

## ⚖️ 4. Conséquences

### Positives
* **Zéro rupture de branche principale** : `main` reste en permanence verte, testée et déployable en production.
* **Respect déterministe des règles forges** : Fin des alertes d'avertissement `remote: Bypassed rule violations`.
* **Traçabilité exemplaire pour l'équipe** : Chaque collègue et chaque agent peut auditer l'historique des changements via des PRs documentées.
* **Sécurité & Étanchéité accrue** : Détection précoce des fuites de configuration avant toute fusion sur la branche par défaut.

### Négatives & Mitigations
* **Légère latence d'intégration** : Obligation de créer une branche et une PR plutôt que de pousser en un seul appel.  
  *Mitigation* : Utilisation fluide de `gh pr create` / `gh pr merge --auto` ou automatisation par l'orchestrateur mLoop en mode CI locale.
