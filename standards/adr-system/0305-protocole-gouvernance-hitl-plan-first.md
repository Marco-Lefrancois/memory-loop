# ADR-0305 : Protocole de Gouvernance HITL, Phase 1 & Plan-First
## Statut : Accepté (Série 03xx - Governance & Plan-First)

---

## 1. Contexte & Problématique

L'application initiale et uniforme du principe *Plan-First* à toute modification de fichier risquait de créer des frictions disproportionnées sur des micro-tâches triviales (typos, linting, requêtes documentaires), tout en manquant de clarté sur l'interopérabilité entre les différents environnements d'exécution (**Antigravity IDE**, **OpenCode / Claude Code / Pi** avec **Plannotator**, et **mLoop CLI**).

---

## 2. Décision Retenue

### 2.1 Matrice de Criticité & Déclenchement du Plan-First

Le déclenchement d'un plan bloquant obéit désormais à une **matrice de criticité à 3 niveaux** :

| Niveau | Périmètre & Critères | Protocole Requis | Exemples |
| :--- | :--- | :--- | :--- |
| **Niveau 1 : Trivial** | • 1 seul fichier impacté<br>• Typo, orthographe, correction de syntaxe/linting<br>• Consultation/investigation en lecture seule<br>• Mise à jour de statut dans un backlog existant | **Exécution Directe (Zero-Gate)**<br>Aucun artefact de plan bloquant requis. | Correction d'une coquille, mise à jour d'un statut dans `sprint_backlog.md`. |
| **Niveau 2 : Moyen** | • 1 à 2 fichiers modifiés<br>• Ajustement d'une règle d'affaires ou d'un scénario de test<br>• Évolution mineure de script dans `src/` | **Micro-Plan dans le Chat**<br>L'agent résume en 2 à 4 puces son intention avant d'appliquer. | Ajout d'une clause Gherkin, retouche d'un script d'ingestion. |
| **Niveau 3 : Critique / Architecture** | • $\ge 3$ fichiers modifiés<br>• Création / révision majeure d'une Story<br>• Nouvelle ADR ou arbitrage d'architecture structurant<br>• Découpage d'Epic ou refonte de composant | **Plan Formel Bloquant (Plan-First)**<br>Soumission d'un plan complet au gabarit SSOT et attente de validation explicite. | Découpage d'un Epic, rédaction d'une Story verticale, refonte de workflow. |

### 2.2 Gabarit Unique & Dualité Transparente (Antigravity ↔ Plannotator)

1. **SSOT Blueprint Unique** : Tous les plans formels (Niveau 3) DOIVENT respecter le gabarit unique [`standards/blueprints/plan_template.md`](file:///c:/Memory%20Loop/standards/blueprints/plan_template.md).
2. **Expérience de Revue Native & Cycle Plannotator Étendu** :
   - **Antigravity IDE** : Rendu et annotation interactive via le panneau d'artefact natif (`implementation_plan.md`, sélection de texte, commentaires inline, bouton *Proceed*).
   - **OpenCode / Claude Code / Pi / mLoop CLI** : Intégration bidirectionnelle native avec **Plannotator** (`@plannotator/opencode`, `@plannotator/pi-extension` et `python src/swarm.py`) couvrant 4 rituels majeurs :
     - **Cadrage & Plans** : Annotation et validation visuelle du plan d'action (`plannotator annotate --gate`).
     - **Gating de Spécifications (Phase 2 Spec)** : `python src/swarm.py annotate --story <KEY> --gate --require-approval` pour valider visuellement les critères d'acceptation Gherkin avec l'humain.
     - **Revue de Code Git (Phase 4 Validate)** : `python src/swarm.py review` (`plannotator review --git`) pour inspecter les diffs visuellement avec commentaires inline avant tout commit ou merge.
     - **Inspection UI Web en Direct (ADR-0340)** : `python src/swarm.py annotate --url http://localhost:...` pour crayonner et annoter directement les interfaces utilisateur en cours d'exécution.
     - **Export de Livrable Portable (Phase 5 Ship)** : `python src/swarm.py guide-export` pour générer un artefact de revue HTML autonome partageable ou chiffré E2EE.
3. **Workers Autonomes (`worker-spawn`)** : Les sous-agents créés pour des tâches de Niveau 3 produisent leur plan dans leur espace de travail isolé avant moissonnage (`worker-harvest`).
4. **Phase 1 Fragmentée** : Respect strict du séquencement `init` $\rightarrow$ dépôt physique des intrants par l'humain dans `reference/` $\rightarrow$ `grill` $\rightarrow$ `ingest` via MarkItDown.
5. **Confirmation Gate des ADRs** : L'agent a l'obligation de demander confirmation avant de créer ou de modifier une ADR dans `standards/adr-system/`.

---

## 3. Conséquences

- **Agilité et Efficacité** : Suppression des frictions inutiles sur les tâches triviales sans compromettre la sécurité sur les tâches critiques.
- **Souveraineté Humaine Préservée** : L'utilisateur conserve le contrôle décisionnel absolu sur l'architecture et les spécifications.
- **Interopérabilité Parfaite** : 100% de compatibilité des plans entre Antigravity et Plannotator sans divergence de format.
