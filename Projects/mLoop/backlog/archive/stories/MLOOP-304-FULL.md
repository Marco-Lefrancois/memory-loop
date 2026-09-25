---
id: MLOOP-304-FULL
jira_key: ""
epic_key: EPIC-30-MULTIMODAL-ARTIFACT-HARNESS
type: Feature
title: "Contrats de Dev Handoff Multi-Harnais & Commande CLI artifact-check (MultimodalArtifactHarness)"
tags: [core, cli, vibe-check, handoff, opencode, fullstack]
status: DONE_TESTED
grill_me: DONE
invest_score: 6/6
layer: fullstack
blocked_by:
  - MLOOP-300-BE
  - MLOOP-301-BE
  - MLOOP-302-BE
  - MLOOP-303-BE
created_at: "2026-09-25"
validated_by: Marco
validated_at: "2026-09-25T12:08:50.485909+00:00"

---

# Contrats de Dev Handoff Multi-Harnais & Commande CLI artifact-check (MultimodalArtifactHarness)

---

## Description
**En tant qu'** Ingénieur Logiciel ou Agent d'Implémentation Aval (OpenCode, Claude Code, Cursor),  
**je veux** disposer d'un contrat de Dev Handoff dual (spécification abstraite JSON IR + rendu SVG sémantique annoté) et d'une commande CLI `mloop artifact-check` intégrée au guardrail Vibe-Check (Check 27),  
**afin de** certifier de bout en bout l'intégrité des livrables d'architecture et de garantir que les agents d'implémentation physique disposent de spécifications visuelles et relationnelles exploitables sans ambiguïté.

---

## Contexte & Périmètre

### Contexte Métier
Dans l'écosystème de développement autonome, Memory Loop produit les spécifications et schémas d'architecture que consomment ensuite les développeurs et les agents de codage physique. Si un schéma d'architecture est corrompu, non éditable ou relationnellement ambigu, les agents d'implémentation génèrent du code incohérent avec les règles métier. L'étude ReFigBench a démontré la *Harness Primacy* : la qualité finale dépend avant tout de la rigueur des contrats et des barrières de vérification fournis par le harnais. Cette story intègre l'ensemble des modules d'EPIC-30 dans une commande CLI unifiée et dans le guardrail Vibe-Check.

### In-Scope
- Implémentation du handler CLI `src/commands/handlers/artifact_check.py` (strictement ≤ 300L, `RULE-AST-01`).
- Enregistrement de la commande CLI `python src/swarm.py artifact-check [--project <projet>] [--file <chemin>] [--json]`.
- Implémentation du **Check 27 (Fidélité Topologique & Intégrité des Artefacts)** dans la suite `src/pipelines/vibe_check.py` :
  - Phase 2 (`STAGE_2_PLAN_ANALYSE`) : bloquant pour franchir la Gate 2 (DoR).
  - Phase 4 (`STAGE_4_VALIDATE`) : bloquant pour franchir la Gate 4 (Recette QA).
- Génération du standard de Dev Handoff dual :
  1. `docs/05-assets/diagrams/<NOM>.ir.json` (Spécification abstraite des nœuds et arêtes typées).
  2. `docs/05-assets/diagrams/<NOM>.semantic.svg` (SVG vectoriel enrichi d'attributs `data-node-id`, `data-edge-from`, `data-edge-to`).
- Harnais de tests d'intégration E2E `tests/test_artifact_harness.py`.

### Out-of-Scope
- Déploiement sur un CDN externe.
- Modification des runtimes agents tiers eux-mêmes.

---

## Critères d'acceptation

### Spécifications de l'Interface & UX *(frontend)*
- **Affichage Console Zero-Fluff** : Présentation claire et compacte des artefacts audités avec statut unitaire (`PASS`, `FAIL`), ratio raster et score topologique.
- **Visualisation Dashboard mLoop** : Intégration de la jauge d'intégrité des artefacts dans la section Architecture du Dashboard.

### Opérations Métier & Logique Backend *(backend)*
#### 1. Audit Global des Artefacts (`run_artifact_check`)
* **Entrée Métier** : Nom du projet (`project_name: str`), filtre optionnel de fichier, mode d'export JSON.
* **Règles d'admissibilité & Validation** : Le projet doit exister sous `Projects/` avec des artefacts sous `docs/` ou `backlog/`.
* **Traitement & Algorithme Métier** :
  1. Moisson de tous les fichiers schémas et maquettes (`.svg`, `.html`, `.json`, `.canvas`).
  2. Soumission de chaque fichier à la porte déterministe `DeterministicArtifactGate` (MLOOP-300-BE).
  3. Vérification de l'adhérence topologique Archify `ConnectorIntegrityValidator` (MLOOP-301-BE).
  4. Calcul de la note composite via `ArchitecturalAuditDecoupler` (MLOOP-303-BE).
  5. Génération du rapport consolidé et émission du code retour (0 si tout est vert, 1 si violation bloquante).
* **Résultat Métier & Mutations** : Fichier `memory/reports/artifact_audit_report.json` et restitution console.
* **Cas de Rejet Métier** : Échec bloquant si un artefact critique échoue à la porte ou présente une inversion de flux.

---

## Parcours Interactif & API

### Contrats d'Échange API (Backend / Services)
- **Commande CLI Principale** : `python src/swarm.py artifact-check --project mLoop`
- **Options CLI** :
  - `--file <path>` : Audit ciblé sur un unique fichier d'artefact.
  - `--json` : Sortie brute formatée JSON pour les pipelines CI/CD.
  - `--strict` : Seuil topologique maximal ($S_{\text{topo}} = 1.0$ obligatoire).

#### Matrice des Contrats API
| Méthode | Route / Point d'Entrée | Finalité | Contrat |
| :--- | :--- | :--- | :--- |
| `handle_artifact_check` | `src/commands/handlers/artifact_check.py:handle_artifact_check` | Point d'entrée de la commande CLI unifiée `mloop artifact-check` | `(argparse.Namespace, LoopState, Path) -> int` |
| `check_artifact_topology` | `src/pipelines/vibe_check.py:check_artifact_topology` | Contrôle d'intégrité Check 27 pour Vibe-Check (Phase 2 et Phase 4) | `(project_path: Path, stage: str) -> VibeCheckStepResult` |

**Question Ouverte (Exemption ADR-0319)** :
- **OQ-304-01** : Ce composant fullstack intègre des interfaces CLI console et guardrails Python (aucune route HTTP/REST externe exposée). `[API de soumission à définir]` — toute future exposition par passerelle d'API réseau est reportée et à confirmer dans un récit dédié.

- **Admission of Limits & Résilience Système** :
  - **Absence de réseau / Timeout** : Harnais et commande CLI 100 % locaux (in-memory / file system), insensibles aux coupures réseau et timeouts distants (503/408).
  - **Concurrence & Anti-Rebond** : Protection contre les exécutions concurrentes ou invocations multiples rapides via écriture de rapport isolée et lecture sans verrou bloquant.
  - **Session & Authentification** : Commande locale exécutée dans le contexte du shell opérateur sans session utilisateur ni token d'authentification (hors domaine 401/session expirée).
  - **Validation des Entrées Extrêmes** : Tout projet vide (champ vide), fichier d'artefact avec caractère spécial ou valeur null est géré sans plantage avec émission d'un code retour standardisé.

---

## Règles d'affaires

- **Intégration Stricte au Vibe-Check (Check 27)** : Tout schéma d'architecture violant la barrière déterministe ou présentant un effondrement de connecteurs bloque le contrôle pré-vol Vibe-Check en mode RUN.
- **Parité Duale Obligatoire** : Tout schéma exporté pour l'implémentation doit impérativement comporter sa version vectorielle `.svg` et sa spécification machine `.json`.
- **Zéro Crash Policy** : Une anomalie sur un artefact particulier est isolée et journalisée sans provoquer l'arrêt brutal de l'audit global du projet.

---

## Références

### 1. Preuves Amont & Traçabilité Factuelle
- 📂 **Dossier de Preuves Factuelles** : [`memory/evidence/MLOOP-304-FULL_fact_dossier.md`](../../memory/evidence/MLOOP-304-FULL_fact_dossier.md)

### 2. Spécifications & Modèles de Données SSOT
- 📜 **ADR Projet** : [ADR-016 : Harnais de Fidélité Visuelle](../../docs/01-architecture/ADR-016_epic-30_harnais_fidelite_visuelle_et_integrite_artefacts_topologiques.md)
- 📜 **ADR Système** : [ADR-0392 : Standard Topologique des Artefacts](../../standards/adr-system/0392-harnais-fidelite-visuelle-integrite-artefacts-topologiques.md)
- 🔬 **Référence Scientifique** : *ReFigBench* (arXiv:2609.18844, Harnais de Réfutation & Handoff).

---

## Scénarios de test

```gherkin
# language: fr
Fonctionnalité: Contrats de Dev Handoff Multi-Harnais & Commande CLI artifact-check (MultimodalArtifactHarness)

  # CHEMIN NOMINAL (Audit Global 100% PASS)
  Scénario: Exécution de la commande CLI artifact-check sur un ensemble d'artefacts conformes
    Étant donné un projet mLoop comportant des diagrammes Archify et schémas vectoriels valides
    Quand la commande python src/swarm.py artifact-check est exécutée sur le projet
    Alors le bilan affiche 100 % d'artefacts conformes
    Et le code de retour CLI est 0
    Et le rapport memory/reports/artifact_audit_report.json est scellé

  # EXCEPTIONS & REJETS MÉTIER (Blocage Vibe-Check Check 27)
  Scénario: Échec du contrôle pré-vol Vibe-Check lors de la présence d'un artefact corrompu
    Étant donné un projet en Phase 2 (PLAN & ANALYSE)
    Et qu'un diagramme d'architecture sous docs/ viole la règle du graphe fermé
    Quand le guardrail python src/swarm.py vibe-check est lancé
    Alors le Check 27 échoue avec le statut FAIL
    Et le projet est bloqué pour le passage de la Gate 2 (DoR)

  # HANDOFF MULTI-HARNAIS (Export Dual Certifié)
  Scénario: Génération du contrat dual JSON IR et SVG sémantique
    Étant donné un schéma d'architecture certifié par le harnais
    Quand l'export de handoff est déclenché
    Alors le système produit simultanément le fichier déclaratif .ir.json
    Et le fichier vectoriel .semantic.svg portant les attributs data-node-id et data-edge-*
    Et les deux livrables partagent la même empreinte de cohérence

  # UX, OBSERVABILITÉ & LOGS (Sortie JSON pour CI/CD)
  Scénario: Restitution structurée lors de l'appel avec l'option --json
    Étant donné l'appel de artifact-check avec l'option --json
    Quand le traitement se termine
    Alors la console produit un objet JSON valide contenant le verdict, la liste des fichiers et les scores détaillés
```