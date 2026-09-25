---
id: MLOOP-332-BE
jira_key: ""
epic_key: EPIC-33-REQUIREMENT-TO-CODE-TRACEABILITY-AND-CODE-EVIDENCE
type: Feature
title: "Pipeline d'Harmonisation Synchrone EvidencePack 2.0 & Archivage des Preuves"
tags: [core, pipelines, evidencepack, openspec, synchronization, sha256]
status: READY_FOR_DEV
layer: backend
invest_score: 6/6
macrostructure: "workbench"
validated_by: Marco
validated_at: "2026-09-25T17:51:58.042995+00:00"

---
# Pipeline d'Harmonisation Synchrone EvidencePack 2.0 & Archivage des Preuves

---

## Description
**En tant qu'** Méta-Orchestrateur ou Développeur mLoop utilisant un agent de pair-programming IA (OpenSpec),  
**je veux** synchroniser et sceller automatiquement la matrice de traçabilité dans l'artefact sidecar `<STORY_ID>_evidence.json` lors de l'archivage du plan d'implémentation,  
**afin d'** assurer la persistance immuable et cryptographiquement vérifiable du lien entre chaque symbole de code et son exigence d'origine, sans saisie manuelle redondante.

---

## Contexte & Périmètre

### Contexte Métier
Dans l'architecture mLoop, le plan d'implémentation technique (`memory/plan/implementation_plan_<STORY_ID>.md`) contient la table Markdown vivante de traçabilité rédigée lors de la conception technique ou guidée par OpenSpec (`tasks.md`). Pour que les sondes d'audit déterministes (Check 29) et les linters puissent vérifier l'absence de Ghost Code à grande vitesse, ces informations doivent être extraites, validées et sérialisées dans le sidecar JSON `memory/evidence/<STORY_ID>_evidence.json` avec calcul des empreintes SHA-256 des fichiers réels.

### In-Scope
- Parseur de tableau Markdown (`PlanEvidenceParser`) extrayant les lignes de la section `Matrice de Traçabilité Code ↔ Exigences` vers des objets typés `CodeTraceabilityEntry`.
- Prise en charge de la syntaxe de tableau GitHub Flavored Markdown (pipes `|`, entêtes, délimiteurs).
- Calcul déterministe des empreintes SHA-256 de chaque fichier physique référencé dans les symboles AST et de tests.
- Pipeline d'harmonisation synchrone (`EvidenceSynchronizer`) orchestrant :
  - L'extraction de la matrice depuis le plan.
  - La validation stricte du quintuplet via `EvidencePackEngine.validate_code_traceability`.
  - Le calcul et l'insertion des empreintes dans `source_hashes`.
  - La fusion atomique non-destructrice préservant les blocs protégés (`tdd_cycle`, `fact_check_certificate`, etc.).
- Prise en charge d'un adaptateur de secours pour le format OpenSpec (`tasks.md`).

### Out-of-Scope
- Sonde d'audit CLI bloquante Check 29 (couverte par `MLOOP-333-BE`).
- Extraction dynamique à l'exécution ou instrumentation runtime.
- Insertion de code physique ou de snippets dans la User Story Markdown (strictement interdite par Gate G4).

---

## Critères d'acceptation

### Opérations Métier & Logique Backend

#### 1. Parsing Déterministe de la Table Markdown du Plan
* **Entrée Métier** : Chemin vers un fichier de plan d'implémentation Markdown (`Path`) ou contenu textuel brut.
* **Règles d'admissibilité & Validation** : 
  - Le document doit contenir une section identifiée `Matrice de Traçabilité Code ↔ Exigences`.
  - Le tableau Markdown doit comporter au moins les colonnes `Symbole AST Qualifié`, `Règle Métier Cible`, `Scénario Gherkin`, `Justification` et `Test Unitaire`.
* **Traitement & Algorithme Métier** : 
  - Détection de la section et extraction ligne par ligne des cellules du tableau Markdown.
  - Nettoyage des balises de formatage, backticks ou liens superflus.
  - Conversion directe vers la liste de `CodeTraceabilityEntry`.
* **Résultat Métier & Mutations** : Liste ordonnée d'entrées validées prêtes pour l'EvidencePack.
* **Cas de Rejet Métier** : Rejet avec message normé si le tableau est mal formé ou si une cellule obligatoire est absente.

#### 2. Synchronisation Atomique et Scellement Cryptographique SHA-256
* **Entrée Métier** : Identifiant du récit (`story_id`) et optionnellement chemin du plan d'implémentation.
* **Règles d'admissibilité & Validation** : 
  - L'EvidencePack existant ou cible doit être accessible en écriture dans `memory/evidence/`.
* **Traitement & Algorithme Métier** : 
  - Extraction de la matrice via `PlanEvidenceParser`.
  - Validation formelle de conformité via `EvidencePackEngine.validate_code_traceability`.
  - Pour chaque fichier source distinct extrait (`chemin/fichier.py`), calcul de son empreinte SHA-256 sur disque s'il existe.
  - Injection des hashes dans le dictionnaire `source_hashes` du pack.
  - Sauvegarde sécurisée tout-ou-rien sans altération des champs tiers préservés (`pack_preserver`).
* **Résultat Métier & Mutations** : Fichier `memory/evidence/<STORY_ID>_evidence.json` mis à jour avec `code_traceability_matrix` et `source_hashes`.
* **Cas de Rejet Métier** : Annulation complète de la mise à jour si la validation de la matrice échoue, sans laisser d'état corrompu ou partiel sur disque.

---

## Parcours Interactif & API

### Contrats d'Échange API (Backend / Services)
* **Parseur de Plan Markdown** :  
  `PlanEvidenceParser.extract_matrix_from_plan(plan_path: Path) -> List[CodeTraceabilityEntry]`  
  `PlanEvidenceParser.extract_matrix_from_text(content: str) -> List[CodeTraceabilityEntry]`
* **Synchronisateur Synchrone** :  
  `EvidenceSynchronizer.sync_story_evidence(story_id: str, plan_path: Optional[Path] = None, base_dir: Optional[Path] = None) -> Path`

---

## Règles d'affaires

- **Idempotence et Atomicité de la Synchronisation** : La synchronisation peut être rejouée indéfiniment ; elle produit toujours un état identique sur disque et n'écrit le fichier que si la validation est totale.
- **Scellement Cryptographique des Fichiers Physiques** : Tout fichier physique référencé dans les symboles de code ou de tests doit voir son empreinte SHA-256 consignée pour figer l'état au moment de l'audit.
- **Préservation Intégrale des Blocs Protégés** : L'actualisation de la traçabilité ne doit jamais altérer le sceau TDD (`tdd_cycle`), le certificat de fact-checking ou les extraits verbatim amont.
- **Double Passerelle Declarative** : Le système ingère prioritairement `memory/plan/implementation_plan_<STORY_ID>.md` et reste compatible en fallback avec la décomposition `tasks.md` issue d'OpenSpec.

---

## Scénarios de test

```gherkin
# language: fr
Fonctionnalité: Pipeline d'Harmonisation Synchrone EvidencePack 2.0 et Archivage des Preuves

  # CHEMIN NOMINAL (Happy Path & Synchronisation Complète)
  Scénario: Synchronisation nominale d'un plan d'implémentation vers l'EvidencePack
    Étant donné un plan d'implémentation valide contenant un tableau de traçabilité conforme
    Quand le synchronisateur EvidenceSynchronizer exécute la synchronisation pour le récit
    Alors le fichier memory/evidence/<STORY_ID>_evidence.json contient la matrice de traçabilité complète
    Et les empreintes SHA-256 des fichiers sources référencés sont scellées dans source_hashes
    Et le statut d'intégrité est confirmé

  # EXCEPTIONS & REJETS MÉTIER (Tableau Invalide & Rationale Trop Court)
  Scénario: Rejet lors de l'extraction d'une table Markdown corrompue
    Étant donné un plan d'implémentation dont le tableau de traçabilité comporte une justification de moins de 10 caractères
    Quand le synchronisateur tente de parser et valider la matrice
    Alors une exception de validation est levée
    Et l'EvidencePack existant sur disque reste strictement inchangé

  # RÉSILIENCE TECHNIQUE & MODE DÉGRADÉ (Préservation des Blocs Tiers)
  Scénario: Préservation intégrale du sceau TDD et du certificat Fact-Check
    Étant donné un EvidencePack existant comportant un bloc tdd_cycle certifié et un certificat fact-check
    Quand une nouvelle synchronisation de traçabilité est appliquée
    Alors la section code_traceability_matrix est mise à jour avec les dernières données du plan
    Et le bloc tdd_cycle ainsi que le certificat fact-check sont intégralement conservés sans corruption

  # UX, OBSERVABILITÉ & LOGGING (Rapport Synchrone de Traçabilité)
  Scénario: Traçabilité transparente avec retour console normé
    Étant donné l'exécution de la synchronisation via le pipeline mLoop
    Quand le traitement se termine avec succès
    Alors un journal d'information indique le nombre d'entrées synchronisées et le chemin absolu du sidecar généré
```

---

## Références

### 1. Preuves Amont & Traçabilité Factuelle
- 📂 **Dossier de Preuves Factuelles** : [`memory/evidence/MLOOP-332-BE_fact_dossier.md`](../../memory/evidence/MLOOP-332-BE_fact_dossier.md)

### 2. Spécifications & Modèles de Données SSOT
- 🏛️ **Décision d'Architecture SSOT** : [`standards/adr-system/0394-tracabilite-bidirectionnelle-code-exigences-preuves-programmation-ast.md`](../../../../standards/adr-system/0394-tracabilite-bidirectionnelle-code-exigences-preuves-programmation-ast.md)
- 📐 **Gabarit de Plan Normalisé** : [`standards/blueprints/plan_template.md`](../../../../standards/blueprints/plan_template.md)
- 📋 **Standard Handoff OpenSpec** : [`standards/adr-system/0319-dual-agent-handoff-openspec-ready.md`](../../../../standards/adr-system/0319-dual-agent-handoff-openspec-ready.md)
- 🔧 **Schéma EvidencePack & Preserver** : [`src/pipelines/evidence_pack.py`](../../../../src/pipelines/evidence_pack.py) & [`src/pipelines/pack_preserver.py`](../../../../src/pipelines/pack_preserver.py)
