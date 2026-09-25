---
id: MLOOP-106-BE
jira_key: ''
epic_key: EPIC-10-SOVEREIGN-EXCELLENCE
type: Refactoring
title: Découpage Modulaire des Handlers CLI
origin: SPEC_SLICING
source_ref: 'MLOOP-101-BE Grill-Me 1:1 Arbitrage #1 (2026-09-20)'
macro_size: M
status: SHIPPED
grill_me: DONE
invest_score: 6/6
layer: backend
blocked_by: []
created_at: '2026-09-20'
updated_at: '2026-09-21'
ttl_cycles: 2
---
# Découpage Modulaire des Handlers CLI

---

## Description
**En tant qu'** Ingénieur Plateforme / Maintainer mLoop,  
**je veux** scinder les handlers CLI monolithiques (`project.py` 462L, `analysis.py` 525L, `export.py` 340L, `architecture.py` 320L) en modules restreints sous les plafonds d'architecture,  
**afin de** garantir que la couche d'orchestration CLI obéit aux mêmes normes de modularité que la couche utilitaire déjà rénovée.

---

## Contexte & Périmètre

### Contexte Métier
La couche d'orchestration en ligne de commande du framework concentre quatre familles de responsabilités dans des fichiers devenus trop volumineux pour être maintenables et auditables : le pilotage du cycle de vie projet, l'exploration sémantique et l'analyse, l'export documentaire et la génération d'architecture. Cette concentration rend la lecture du code difficile, multiplie les risques de régression croisée et complique l'isolation des responsabilités. Le présent récit rénove cette couche en respectant strictement le plafond de modularité interne du framework, sans modifier le comportement observable par l'opérateur : chaque commande doit continuer à répondre de manière identique.

### In-Scope
- **Découpage du handler de pilotage projet (462L / 24.3 Ko)** en package `project/` :
  - `project/__init__.py` — façade réexportant `handle_init`, `handle_resume`, `handle_focus`, `handle_vibe_check`, `handle_lifecycle_status`, `handle_lifecycle_clean`
  - `project/init.py` — `handle_init` (~80L)
  - `project/resume.py` — `handle_resume` (~60L)
  - `project/focus.py` — `handle_focus` (~70L)
  - `project/vibe_check.py` — `handle_vibe_check` (~80L)
  - `project/lifecycle.py` — `handle_lifecycle_status` + `handle_lifecycle_clean` (~90L)
  - `project/git_hooks.py` — extraction du bloc Git-hooks (~80L), nom imposé anti-collision avec `handlers/hook.py` existant (ADR-0364)
- **Découpage du handler d'analyse sémantique (525L)** en package `analysis/` :
  - `analysis/__init__.py` — façade réexportant 6 handlers
  - `analysis/code_explore.py` — `handle_code_explore`
  - `analysis/graph_query.py` — `handle_graph_query`
  - `analysis/fact_search.py` — `handle_fact_search`
  - `analysis/deep_search.py` — `handle_deep_search`
  - `analysis/code_impact.py` — `handle_code_impact` + `handle_code_affected`
- **Découpage du handler d'export documentaire (340L)** en package `export/` :
  - `export/__init__.py` — façade réexportant 3 handlers
  - `export/export.py` — `handle_export` (markdown/json/pdf)
  - `export/notebooklm.py` — `handle_notebooklm`
  - `export/archify.py` — `handle_archify`
- **Découpage du handler de génération d'architecture (320L)** en package `architecture/` :
  - `architecture/__init__.py` — façade réexportant 3 handlers
  - `architecture/architecture.py` — `handle_architecture` (SOW/TSHIRT/ADR)
  - `architecture/doc_gen.py` — `handle_doc_gen`
  - `architecture/blueprint.py` — `handle_blueprint`
- **Harnais de non-régression en 3 couches** : tests unitaires directs (~25), suite d'intégration CLI (16 commandes), extension du harnais de performance (p95 < 50 ms).
- **Validation par lots séquentiels** dans l'ordre : pilotage projet → analyse → export → architecture. Chaque lot inclut découpage, tests unitaires, intégration CLI, synchronisation du guide CLI et contrôle de conformité structurelle.

### Out-of-Scope
- La couche utilitaire de bas niveau (périmètre du récit de rénovation utilitaire déjà livré).
- Les pipelines d'analyse profonde hors couche CLI.
- Le registre central des commandes (2 000L) — traité dans un récit dédié pour isoler le risque de dérive CLI.
- Le nettoyage des clauses d'interception silencieuses de la couche CLI (audit de robustesse à séquencer séparément).
- Les handlers déjà conformes au plafond de modularité, y compris l'ingestion documentaire.
- Les handlers de cycle de vie pré-compaction existants — non modifiés.

---

## Critères d'acceptation

### Opérations Métier & Logique Backend

#### 1. Segmentation Modulaire de la Couche d'Orchestration CLI
* **Entrée Métier** : Une famille fonctionnelle de commandes CLI (pilotage projet, analyse, export, architecture) appelée par le registre central des commandes.
* **Règles d'admissibilité & Validation** : Chaque module produit doit respecter le plafond interne de 300 lignes physiques et 15 Ko sur disque. La signature publique de chaque point d'entrée doit rester strictement inchangée, afin que le registre central continue de résoudre les commandes sans adaptation.
* **Traitement & Algorithme Métier** : Extraction de chaque responsabilité atomique vers un module dédié, regroupement sous un package par famille fonctionnelle, et exposition d'une façade de réexport garantissant la compatibilité descendante des imports dynamiques. Le découpage est strictement structurel : aucune logique métier n'est ajoutée, modifiée ou supprimée.
* **Résultat Métier & Mutations** : Une couche d'orchestration dont chaque unité est isolement auditable et testable, avec un comportement observable identique à l'état initial pour l'opérateur.
* **Cas de Rejet Métier** : Tout module produit excédant le plafond de modularité ou toute signature de point d'entrée altérée est considéré comme un échec de conformité bloquant.

#### 2. Garantie de Non-Régression Fonctionnelle
* **Entrée Métier** : L'ensemble des seize commandes CLI impactées par le découpage.
* **Règles d'admissibilité & Validation** : Chaque point d'entrée découpé doit conserver son comportement observable : sortie console, code de retour et effets de bord identiques à l'état de référence.
* **Traitement & Algorithme Métier** : Exécution d'une stratégie de vérification en trois couches — tests unitaires directs par point d'entrée, suite d'intégration exerçant les commandes de bout en bout, et contrôle de performance sur l'import et l'exécution.
* **Résultat Métier & Mutations** : Un filet de sécurité automatisé couvrant l'intégralité des points d'entrée impactés, exploitable pour les rénovations ultérieures.
* **Cas de Rejet Métier** : Toute divergence de sortie, de code de retour ou de performance au-delà du seuil fixé bloque l'intégration du lot concerné.

#### Contrats d'échange API
- **Point d'entrée CLI unifié** : `handle_*(args, state, project_path) -> int` — signature immuable consommée par le registre central via import dynamique.
- **EXEMPTION-106 (Exemption Zéro Fausse Route)** : Récit d'orchestration 100% headless — aucune route REST/CTA n'est exposée, consommée ou modifiée. `[API de soumission à définir]`
- **Admission of Limits** : Les alertes génériques de résilience réseau (timeout API, expiration de session, validation de saisie, anti-rebond) sont hors domaine pour ce composant headless (ni interface utilisateur, ni API distante). La résilience E/S locale est couverte par le Pilier 3 des scénarios de test.

#### Matrice des Contrats API
| Méthode | Route / Point d'Entrée | Finalité | Contrat |
| :--- | :--- | :--- | :--- |
| `handle_*` | `src/commands/handlers/{project,analysis,export,architecture}/**/*.py` | Point d'entrée CLI unifié pour `_registry.py` | Signature immuable `(argparse.Namespace, LoopState, Path) -> int` |
| — | — | **Exemption OQ-106** : Composant backend headless sans interface HTTP. `[API de soumission à définir]` — toute exposition future reportée à récit dédié. | — |

### Maquettes SSOT
- 🔗 **Maquette Validée (SSOT)** : N/A - Composant Headless
- 📂 **Actif Local Ingéré** : N/A - Composant Headless
- 📌 **Ajustements Visuels Validés** : N/A - Composant Headless

---


## Parcours Interactif & API

### Parcours Interactif (Frontend / Déclencheurs UI)
> *N/A - Composant Headless : aucune interface graphique. Le déclencheur est l'invocation CLI par l'opérateur.*

### Contrats d'Échange API (Backend / Services)
> *Définition déclarative des contrats réseau. Règle anti-invention : interdiction d'inventer des routes non documentées.*

- **Pilotage du cycle de vie projet** : `init`, `resume`, `focus`, `vibe-check`, `lifecycle-status`, `lifecycle-clean`
- **Exploration et analyse sémantique** : `code-explore`, `graph-query`, `fact-search`, `deep-search`, `code-impact`
- **Export documentaire** : `export`, `notebooklm`, `archify`
- **Génération d'architecture** : `architecture`, `doc-gen`, `blueprint`

> 📄 **Spécifications formelles détaillées** : N/A — composant headless sans interface HTTP. `[API de soumission à définir]` (EXEMPTION-106).

---

## Règles d'affaires

- **Plafond de Modularité Interne** : Tout module Python du framework doit comporter au maximum 300 lignes physiques et 15 Ko sur disque. Un module excédant ce plafond constitue une violation bloquante.
- **Immuabilité du Point d'Entrée Unifié** : La signature `handle(args, state, project_path) -> int` ne doit jamais évoluer, afin que le registre central continue de résoudre les commandes sans adaptation.
- **Isomorphisme Structurel** : Le découpage est strictement structurel — aucune logique métier n'est ajoutée, modifiée ou supprimée. Le comportement observable par l'opérateur doit rester identique.
- **Parité du Guide CLI** : Toute modification de structure CLI doit maintenir la parité 100% entre le registre des commandes et le guide SSOT, sous peine de dérive bloquante.

---

## Références

### 1. Preuves Amont & Traçabilité Factuelle
- 📂 **Dossier de Preuves Factuelles** : [`memory/evidence/MLOOP-106-BE_fact_dossier.md`](../../memory/evidence/MLOOP-106-BE_fact_dossier.md)

### 2. Spécifications & Modèles de Données SSOT
- 📜 **Décision d'Architecture — Modularité Interne** : [ADR-0202 — Modularité Interne des Agents](../../../../standards/adr-system/0202-modularite-interne-agents.md)
- 📜 **Décision d'Architecture — Robustesse Python Senior** : [ADR-0369 — Python Senior Robustness & Resource Governance](../../../../standards/adr-system/0369-python-senior-robustness-and-resource-governance.md)
- 📜 **Décision d'Architecture — Anti-Dérive Guide CLI** : [ADR-0370 — CLI Pipeline SSOT Generator & Anti-Drift Governance](../../../../standards/adr-system/0370-cli-pipeline-ssot-generator-and-anti-drift-governance.md)

### 3. Paquet OpenSpec (Handoff Développeur)
- ✅ **Plan Formel d'Implémentation** : [`memory/plan/implementation_plan_MLOOP-106-BE.md`](../../memory/plan/implementation_plan_MLOOP-106-BE.md)
- 📄 **Paquet OpenSpec** : N/A — récit d'auto-développement du framework mLoop ; le plan formel ci-dessus tient lieu de paquet de handoff.

---


## Scénarios de test

```gherkin
# language: fr
Fonctionnalité: Découpage Modulaire des Handlers CLI

  # CHEMIN NOMINAL (Happy Path & Persistance)
  Scénario: Découpage complet des handlers monolithiques en packages conformes
    Étant donné les quatre handlers monolithiques de la couche d'orchestration CLI
    Quand le découpage structurel est exécuté selon les lots séquentiels (pilotage projet, analyse, export, architecture)
    Alors chaque package produit respecte le plafond de 300 lignes et 15 Ko
    Et chaque module handler individuel compte moins de 150 lignes
    Et la façade de réexport expose tous les points d'entrée sans changement de signature
    Et le contrôle de conformité structurelle retourne PASS avec zéro violation sur les quatre packages

  # EXCEPTIONS & REJETS MÉTIER (Règles d'affaires)
  Scénario: Rejet d'un module excédant le plafond de modularité
    Étant donné un module handler généré excédant 300 lignes
    Quand le contrôle de conformité structurelle analyse le package
    Alors la violation est signalée avec le chemin exact et le nombre de lignes
    Et le build est interrompu avec un code de retour non nul
    Et aucune interception silencieuse n'est tolérée

  Scénario: Blocage sur divergence de comportement d'une commande critique
    Étant donné une commande de pilotage du cycle de vie altérée par le découpage
    Quand la suite d'intégration CLI s'exécute
    Alors le test correspondant échoue avec un message d'erreur explicite
    Et l'intégration du lot est bloquée

  # RÉSILIENCE TECHNIQUE & MODE DÉGRADÉ (Timeouts, Idempotence, Concurrence)
  Scénario: Maintien de la performance sous sollicitations successives
    Étant donné un afflux de cent invocations CLI successives
    Quand les modules découpés sont sollicités via le registre central
    Alors la latence p95 d'import et d'exécution reste inférieure à 50 millisecondes
    Et l'empreinte mémoire demeure stable sans fuite

  Scénario: Robustesse face à un conflit de concurrence sur le fichier de verrouillage
    Étant donné un conflit de concurrence lors d'une opération d'écriture sur le module de hooks Git
    Quand l'écriture concurrente est tentée
    Alors le conflit est tracé dans les journaux d'audit avec son niveau d'exception
    Et le point d'entrée retourne un code de sortie non nul explicite
    Et l'état local du projet demeure intègre

  # UX, OBSERVABILITÉ & EMPTY STATE (Spinners, Retours Écran, Logs)
  Scénario: Comportement observable inchangé après le découpage
    Étant donné un opérateur exécutant les seize commandes impactées
    Quand chaque commande s'exécute
    Alors la sortie console, le code de retour et les effets de bord sont identiques à l'état de référence
    Et la synchronisation du guide CLI confirme la parité 100% sans dérive
    Et la traçabilité du harnais de vérification est consignée dans le pack de preuves
```

