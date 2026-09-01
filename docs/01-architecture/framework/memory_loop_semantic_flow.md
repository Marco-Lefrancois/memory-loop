# Les Fondations Méthodologiques de Memory Loop (mLoop Flow v2.0.0)

Ce document cristallise le flux d'analyse de conception, de spécification technique, d'architecture et de validation de la méthodologie **Memory Loop**.

---

## 🔄 Le Flux Spec-Driven Global en 5 Phases

L'évolution de tout projet de développement au sein du swarm d'agents de Memory Loop suit une séquence stricte en 5 phases :

```text
[1] SPEC ──────► [2] PLAN ──────► [3] BUILD ──────► [4] VALIDATE ──────► [5] SHIP
(Ingestion)       (Grill &        (Implémentation     (Audit 4 Piliers    (Sync & Graphify
 Reference         Architecture    Client / Self-Dev   Gherkin, INVEST    Calibrate 8/8)
 docs/00-ingested)  Verticaux)     mLoop Kernel)       & EvidencePacks)
```

### Le Rôle des Agents dans le Flux
Dans l'architecture v2.0.0, les rôles sont distribués selon la matrice d'outillage :
1. **Agent `orchestrator`** : Supervise l'ensemble du flux, les 5 phases, les checkpoints et la livraison finale (`sync`, `cycle-status`).
2. **Agent `plan`** : Exécute les phases **[1] SPEC** et **[2] PLAN**. Il mène le *Grill with Docs*, gère `CONTEXT.md` et génère le Story Constraint Contract (SCC).
3. **Agent `build`** : réservé au développement TDD du framework mLoop (`src/`). Pour les projets clients, l'implémentation applicative est déléguée au développeur humain ou outils externes.
4. **Agent `sentinel / validate`** : Exécute la phase **[4] VALIDATE**. Audite les 4 Piliers Gherkin, génère l'EvidencePack (`memory/evidence/`), exécute `wikifix`, `aoep` et calcule le score INVEST.

---

## 👥 Déroulement de la Phase PLAN (Grill with Docs)

Le protocole **Grill with Docs** formalise l'interaction active entre l'utilisateur humain et l'agent `plan`.

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│                    PHASE D'ANALYSE DÉTAILLÉE : Grill with Docs              │
└──────────────────────────────────────┬───────────────────────────────────────┘
                                       │
         1. [PLAN] ANALYSE DES EXIGENCES & DIRECTIVES EXISTANTES
         - L'agent plan étudie les spécifications et directives (tech.md, business.md).
                                       │
                                       ▼
         2. [PLAN ──► HUMAIN] FORMULATION DU GRILL (1 Question + 1 Recommandation)
         - L'agent interroge le graphe (Search-First) puis pose 1 unique question ciblée.
         - L'agent formule une recommandation d'ingénierie et un cas limite.
                                       │
                                       ▼
         3. [HUMAIN ──► PLAN] ARBITRAGE & RETOUR
         - L'utilisateur apporte ses contraintes, valide ou modifie l'option.
                                       │
                                       ▼
         4. [PLAN] CRISTALLISATION INLINE & IMMÉDIATE
         - Les fichiers directives/business.md, tech.md et ADRs sont mis à jour.
                                       │
                                       ▼
         5. [PLAN] GÉNÉRATION DU SCC & EVIDENCEPACK
         - Spécification finale (backlog/stories/US-XXX.md).
         - Génération synchrone du pack d'évidence (memory/evidence/US-XXX_evidence.json).
```

### Étape A : Le Cadrage Global (Phase 1 SPEC & Phase 2 PLAN)
*   **Objectif** : Valider les choix d'architecture haut niveau via l'agent `plan`.
*   **Interaction** : L'agent pose des questions d'architecture, l'utilisateur arbitre. Consignation dans `CONTEXT.md` et dans le Graphe de Connaissances L3.

### Étape B : L'Analyse Récit par Récit (Stories Verticaux)
*   **Objectif** : Éplucher chaque story individuellement avant de transmettre à la phase BUILD.
*   **Interaction** : Affinement des règles d'affaires. Toute décision est inscrite dans le contrat protégé par `story_guard.py` pour interdire les modifications "YOLO".
