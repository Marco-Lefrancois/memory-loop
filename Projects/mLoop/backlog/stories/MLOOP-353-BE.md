---
id: MLOOP-353-BE
jira_key: ''
epic_key: EPIC-35-REFIGBENCH-ARTIFACT-HARNESS-V2
type: Feature
title: Adaptateur de Dev Handoff Multi-Harnais Dédié (Claude Code, OpenCode, Codex & Cursor)
tags:
- core
- handoff
- harness
- multi-agent
- prompt-engineering
- backend
status: DRAFT
grill_me: PENDING
invest_score: 6/6
layer: backend
blocked_by:
- MLOOP-351-BE
created_at: '2026-09-25'
ttl_cycles: 3
---

# Adaptateur de Dev Handoff Multi-Harnais Dédié (Claude Code, OpenCode, Codex & Cursor)

---

## Description
**En tant qu'** Moteur Universal Dev Handoff mLoop (Phase 5 : Ship & Sync),  
**je veux** disposer d'un adaptateur de profils de harnais capable de formater les dossiers de handoff et les instructions d'implémentation selon le runtime cible (Claude Code, OpenCode, Codex, Cursor), en y injectant les garde-fous anti-aplatissement découverts dans ReFigBench,  
**afin de** maximiser le taux de succès au premier essai des agents de codage avals en tirant parti de la primauté du harnais (*Harness Primacy*) démontrée dans ReFigBench (*arXiv:2609.18844*).

---

## Contexte & Périmètre

### Contexte Métier
L'étude ReFigBench apporte une démonstration expérimentale majeure : **le harnais d'exécution fait le succès ou l'échec d'un modèle**. À modèle strictement identique (GPT-5.5) et prompt invariant mot-à-mot, les scores et comportements divergent sensiblement entre Claude Code et Codex (+1.4 pt en direct, bascule de +3.2 à -2.2 sur les outils spécialisés). Aujourd'hui, `src/pipelines/handoff.py` génère un export générique monolithique. Ce récit introduit des profils de harnais adaptatifs calibrés pour exploiter les forces de chaque agent aval sans subir ses faiblesses.

### In-Scope
- Implémentation du module `src/pipelines/harness_adapter.py` (strictement $\le 300$L, `RULE-AST-01`).
- Définition de l'énumération des profils : `HarnessProfile.CLAUDE_CODE`, `HarnessProfile.OPENCODE`, `HarnessProfile.CODEX`, `HarnessProfile.CURSOR`, `HarnessProfile.GENERIC`.
- Moteur de génération de bundle calibré : `generate_harness_optimized_bundle(story_id: str, target_harness: HarnessProfile) -> Path`.
- Spécificités par profil :
  - **Claude Code** : Priorisation des consignes directes concises, fichiers Markdown liés via `[[WikiLinks]]`, exécution native de tests `uv run pytest`, limitation du bruit d'outils annexes.
  - **OpenCode** : Schémas JSON IR déclaratifs, découpage séquentiel de sous-tâches, variables d'environnement explicites.
  - **Codex** : Primitives de code typées, stubs de signatures AST et assertions de tests unitaires formelles.
  - **Cursor** : Commentaires d'ancrage contextuel, chemins de fichiers absolus et liens vers les symboles.
- Injection universelle de la directive **Anti-Flattening / Anti-Collapse** : interdiction formelle pour l'agent aval d'aplatir un module en un script monolithique ou de remplacer une abstraction par du code dupliqué.

### Out-of-Scope
- Invocation automatique des APIs payantes des agents tiers.
- Création de nouveaux agents en interne.

---

## Critères d'acceptation

### Opérations Métier & Logique Backend *(backend)*
#### 1. Génération de Bundle de Handoff par Profil de Harnais (`build_harness_bundle`)
* **Entrée Métier** : Identifiant de la story certifiée (`story_id`), profil de harnais sélectionné (`target_harness`).
* **Règles d'admissibilité & Validation** : La story doit être au statut `QA_CERTIFIED` ou `READY_TO_SHIP` (Gate 4 validée).
* **Traitement & Algorithme Métier** :
  1. Extraction des spécifications fonctionnelles, de la matrice de traçabilité AST (ADR-0394) et des scénarios Gherkin.
  2. Application du template d'instruction adapté aux biais connus du harnais cible.
  3. Adjonction de la directive d'intégrité topologique anti-effondrement.
  4. Packaging dans `backlog/handoff/<STORY_ID>/<HARNESS>/`.
* **Résultat Métier & Mutations** : Répertoire de handoff scellé prêt pour consommation par l'agent aval.
* **Cas de Rejet Métier** : Échec si la story n'a pas validé son EvidencePack ou son Vibe-Check.

---

## Parcours Interactif & API

### Contrats d'Échange API (Backend / Services)
- `src.pipelines.harness_adapter:build_harness_bundle(story_id: str, harness: str) -> dict`

#### Matrice des Contrats API
| Méthode | Route / Point d'Entrée | Finalité | Contrat |
| :--- | :--- | :--- | :--- |
| `build_harness_bundle` | `src.pipelines.harness_adapter:build_harness_bundle` | Génération de bundle optimisé par harnais | `(story_id: str, harness: str) -> dict` |

---

## Règles d'affaires

- **Souveraineté du Profil de Harnais** : Aucun bundle ne peut être exporté sans mentionner explicitement le harnais cible et la version de prompt associée.
- **Clause Anti-Flattening Obligatoire** : Tout livrable de handoff comporte impérativement l'avertissement de non-aplatissement sous peine de rejet au commit pre-check.

---

## Références

### 1. Preuves Amont & Traçabilité Factuelle
- 📂 **Dossier de Preuves** : [`memory/evidence/EPIC-35_refigbench_fact_dossier.md`](../../memory/evidence/EPIC-35_refigbench_fact_dossier.md)
- 📄 **Publication de Référence** : ReFigBench (*arXiv:2609.18844*, Section 1 & Section 5 : *Capability and the Harness Decide the Return on Workflow Effort*, Table 2).

### 2. Spécifications & Modèles de Données SSOT
- 🏛️ **Architecture Runtimes Avals** : [`standards/adr-system/0377-runtimes-agents-aval-et-herdr-operationnels.md`](../../standards/adr-system/0377-runtimes-agents-aval-et-herdr-operationnels.md)
- 📜 **ADR Associé** : [ADR-0396](../../standards/adr-system/0396-audit-artefacts-5-axes-et-anti-inversion-causale-refigbench.md)

---

## Scénarios de test

```gherkin
# language: fr
Fonctionnalité: Adaptateur de Dev Handoff Multi-Harnais Dédié

  # CHEMIN NOMINAL (Happy Path & Persistance)
  Scénario: Génération d'un bundle optimisé pour le harnais Claude Code
    Étant donné une story certifiée "MLOOP-300-BE"
    Quand le générateur de handoff est invoqué avec le profil "CLAUDE_CODE"
    Alors le dossier généré contient des instructions concises et des liens WikiLinks
    Et la directive de conservation des connecteurs natifs est incluse
    Et les commandes d'exécution directe "uv run" sont pré-configurées

  # EXCEPTIONS & REJETS MÉTIER (Règles d'affaires)
  Scénario: Rejet de génération de handoff si la story n'a pas franchi la Gate 4
    Étant donné une story encore en statut "IN_DEV"
    Quand une tentative d'export de handoff est demandée
    Alors l'opération est refusée avec le code "GATE_VALIDATION_REQUIRED"
    Et aucun bundle n'est généré sur disque

  # RÉSILIENCE TECHNIQUE & MODE DÉGRADÉ (Timeouts, Idempotence, Concurrence)
  Scénario: Bascule transparente sur le profil générique en cas de harnais inconnu
    Étant donné une requête spécifiant un harnais inexistant "HARNAIS_EXOTIQUE"
    Quand l'adaptateur résout le profil
    Alors un profil générique sécurisé conforme aux standards mLoop est appliqué
    Et un avertissement est consigné dans le journal

  # UX, OBSERVABILITÉ & EMPTY STATE (Spinners, Retours Écran, Logs)
  Scénario: Empreinte SHA-256 du bundle de handoff pour traçabilité radicale
    Étant donné la génération d'un livrable de handoff
    Quand le bundle est finalisé
    Alors une empreinte de scellement est enregistrée dans le manifeste du projet
```
