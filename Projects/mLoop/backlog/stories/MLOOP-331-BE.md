---
id: MLOOP-331-BE
jira_key: ''
epic_key: EPIC-33-REQUIREMENT-TO-CODE-TRACEABILITY-AND-CODE-EVIDENCE
type: Feature
title: Moteur d'Extraction AST & Résolution Déterministe des Symboles de Code
tags:
- core
- ast
- traceability
- evidencepack
- senior-python
status: READY_FOR_DEV
layer: backend
invest_score: 6/6
macrostructure: workbench
validated_by: Marco
validated_at: '2026-09-25T17:18:38.646725+00:00'
ttl_cycles: 4
---
# Moteur d'Extraction AST & Résolution Déterministe des Symboles de Code

---

## Description
**En tant qu'** Inspecteur Qualité ou Moteur d'Audit mLoop,  
**je veux** un analyseur statique AST capable d'extraire les symboles physiques de code (`chemin/fichier.py::NomClasse.methode` ou `chemin/fichier.py::fonction`) et de les confronter à la matrice de traçabilité,  
**afin d'** interdire le code fantôme (*Ghost Code*), d'éliminer la sur-ingénierie non auditée et de garantir que chaque fonction physique est formellement justifiée.

---

## Contexte & Périmètre

### Contexte Métier
Dans l'écosystème Memory Loop, la traçabilité des exigences doit s'étendre de bout en bout jusqu'au code physique sans rompre l'étanchéité no-code du récit fonctionnel. Tandis que `MLOOP-330-BE` a défini le schéma de données `code_traceability_matrix` dans l'EvidencePack, ce récit implémente le moteur d'analyse statique capable de parcourir le code source physique, d'extraire l'arborescence des symboles déclarés (classes, méthodes, fonctions autonomes) et de calculer le différentiel avec la matrice de traçabilité.

### In-Scope
- Moteur Python d'extraction statique utilisant exclusivement le module standard `ast` (zéro dépendance externe, standard Senior Python ADR-0369).
- Modélisation typée des symboles extraits (`ExtractedSymbol`) avec qualification canonique (`chemin/fichier.py::NomClasse.methode` ou `chemin/fichier.py::fonction`).
- Extraction récursive des classes, méthodes publiques/privées et fonctions de module.
- Prise en charge des fonctions asynchrones (`AsyncFunctionDef`) et synchrones (`FunctionDef`).
- Algorithme de réconciliation et de détection de dérive (`reconcile`) signalant :
  - Les symboles de code orphelins / non ancrés (*Ghost Code*).
  - Les entrées de traçabilité pendantes sans symbole physique correspondant (*Dangling Entries*).
- Tolérance contrôlée des fonctions utilitaires privées (`_helper`) imbriquées sous une fonction ou classe couverte.
- Architecture ouverte avec classe abstraite de base (`BaseAstExtractor`) permettant l'extension vers d'autres langages.

### Out-of-Scope
- Analyse dynamique à l'exécution ou instrumentation du bytecode (couvert par pytest/coverage).
- Parseur TypeScript physique dédié (réservé pour une story ultérieure sur le frontend).
- Commande CLI interactive et intégration dans la sonde Vibe-Check Check 29 (couvert par `MLOOP-333-BE`).
- Altération ou insertion de code dans les récits Markdown (strictement proscrite par Gate G4).

---

## Critères d'acceptation

### Opérations Métier & Logique Backend

#### 1. Extraction Déterministe des Symboles AST
* **Entrée Métier** : Chemin de fichier source ou contenu source sous forme de chaîne de caractères avec chemin relatif canonique.
* **Règles d'admissibilité & Validation** : 
  - Le chemin relatif doit être normalisé avec des séparateurs obliques (`/`).
  - Le code source doit être syntaxiquement valide pour le compilateur Python.
* **Traitement & Algorithme Métier** : 
  - Parcours de l'AST via un visiteur ou analyse récursive sans exécution de code.
  - Identification des classes de premier niveau et de leurs méthodes (`ClassDef` -> `FunctionDef`/`AsyncFunctionDef`).
  - Identification des fonctions libres définies au niveau du module.
  - Détection automatique de la visibilité privée (préfixe `_` hors méthodes spéciales dunder).
* **Résultat Métier & Mutations** : Liste ordonnée d'objets `ExtractedSymbol` contenant le symbole qualifié, le type de symbole, les bornes de lignes indicatives (non utilisées pour l'ancrage), et le statut privé.
* **Cas de Rejet Métier** : Levée d'une exception `SyntaxError` contextualisée si le code source ne peut pas être parsé, sans interruption silencieuse.

#### 2. Rapprochement et Détection du Ghost Code (Reconciliation)
* **Entrée Métier** : Liste de symboles extraits (`ExtractedSymbol`) et liste d'entrées de traçabilité (`CodeTraceabilityEntry`).
* **Règles d'admissibilité & Validation** : 
  - La matrice de traçabilité fournie doit être conforme au schéma validé par `EvidencePackEngine`.
* **Traitement & Algorithme Métier** : 
  - Indexation des symboles de la matrice par clé canonique `ast_symbol`.
  - Rapprochement exact des symboles extraits.
  - Application de la règle de tolérance des sous-fonctions privées : si un helper privé est imbriqué dans un symbole couvert, il n'est pas signalé comme non ancré.
  - Calcul de l'état de conformité global (`is_valid`).
* **Résultat Métier & Mutations** : Rapport typé `ReconciliationReport` contenant les listes `unanchored_symbols` (Ghost Code), `dangling_entries` (entrées sans code physique), et `matched_pairs`.
* **Cas de Rejet Métier** : Rapport marqué `is_valid: False` dès lors qu'au moins un symbole public ou une fonction de module modifiée ne dispose d'aucun ancrage dans la matrice.

---

## Parcours Interactif & API

### Contrats d'Échange API (Backend / Services)
* **Extraction de Symboles** :  
  `CodeEvidenceTracer.extract_symbols_from_source(source_code: str, relative_path: str) -> List[ExtractedSymbol]`  
  `CodeEvidenceTracer.extract_symbols_from_file(file_path: Path, base_dir: Optional[Path] = None) -> List[ExtractedSymbol]`
* **Rapprochement Symbolique** :  
  `CodeEvidenceTracer.reconcile(extracted: List[ExtractedSymbol], matrix: List[CodeTraceabilityEntry], allow_private_implicit: bool = True) -> ReconciliationReport`

---

## Règles d'affaires

- **Ancrage Canonique par Symbole Qualifié** : Tout symbole extrait ou comparé doit adopter la notation normalisée `chemin/fichier.py::NomClasse.methode` ou `chemin/fichier.py::fonction`.
- **Tolérance Contrôlée des Helpers Privés** : Une fonction privée (`_helper`) imbriquée sous une méthode ou fonction parente couverte est admise sans entrée distincte. Si elle est autonome au niveau module, elle doit être explicitement inscrite dans la matrice avec `requirement_ref: "INFRA"` ou `"TECH-FOUNDATION"`.
- **Zéro Dépendance Externe & Analyse Sécurisée** : L'analyse statique s'effectue exclusivement par inspection déclarative de l'AST sans importer ni exécuter le code cible (`ast.parse`), prévenant tout risque d'exécution de code arbitraire.
- **Règle Zéro Ghost Code** : Aucun symbole nouveau ou modifié ne doit exister dans la branche de développement sans justification par une exigence métier ou un besoin d'infrastructure.

---

## Scénarios de test

```gherkin
# language: fr
Fonctionnalité: Moteur d'Extraction AST et Résolution Déterministe des Symboles de Code

  # CHEMIN NOMINAL (Happy Path & Extraction Conforme)
  Scénario: Extraction complète des classes et méthodes d'un module Python
    Étant donné un fichier source Python contenant une classe avec deux méthodes et une fonction autonome
    Quand le moteur CodeEvidenceTracer extrait les symboles du fichier
    Alors la liste retournée contient exactement les symboles qualifiés de la classe, de ses méthodes et de la fonction
    Et chaque symbole est typé et marqué avec son chemin relatif normalisé

  # EXCEPTIONS & REJETS MÉTIER (Détection de Ghost Code & Erreurs de Syntaxe)
  Scénario: Détection de symboles physiques non ancrés dans la matrice
    Étant donné une liste de symboles extraits comportant une méthode non référencée dans la matrice de traçabilité
    Quand la méthode de réconciliation est exécutée
    Alors le rapport indique que la validation a échoué
    Et le symbole orphelin est listé dans les symboles non ancrés avec son niveau de visibilité

  # RÉSILIENCE TECHNIQUE & MODE DÉGRADÉ (Tolérance Helpers & Fonctions Asynchrones)
  Scénario: Prise en charge des fonctions asynchrones et tolérance des helpers privés
    Étant donné un module contenant une méthode asynchrone couverte par la matrice et une sous-fonction privée interne
    Quand le moteur extrait et réconcilie les symboles avec tolérance privée active
    Alors la méthode asynchrone est validée avec succès
    Et la sous-fonction interne ne lève aucune alerte de symbole non ancré

  # UX, OBSERVABILITÉ & LOGGING (Rapport Exhaustif Déterministe)
  Scénario: Génération d'un rapport de réconciliation exploitable par les linters
    Étant donné un ensemble de fichiers sources et une matrice EvidencePack complète
    Quand le rapprochement global est calculé
    Alors le rapport fournit un dictionnaire récapitulatif avec le nombre exact de correspondances, d'orphelins et d'entrées pendantes
    Et aucune exécution de code arbitraire n'a eu lieu
```

---

## Références

### 1. Preuves Amont & Traçabilité Factuelle
- 📂 **Dossier de Preuves Factuelles** : [`memory/evidence/MLOOP-331-BE_fact_dossier.md`](../../memory/evidence/MLOOP-331-BE_fact_dossier.md)

### 2. Spécifications & Modèles de Données SSOT
- 🏛️ **Décision d'Architecture SSOT** : [`standards/adr-system/0394-tracabilite-bidirectionnelle-code-exigences-preuves-programmation-ast.md`](../../../../standards/adr-system/0394-tracabilite-bidirectionnelle-code-exigences-preuves-programmation-ast.md)
- 📐 **Standard de Robustesse Python Senior** : [`standards/adr-system/0369-standards-robustesse-python-senior.md`](../../../../standards/adr-system/0369-standards-robustesse-python-senior.md)
- 📋 **Standard Handoff OpenSpec** : [`standards/adr-system/0319-dual-agent-handoff-openspec-ready.md`](../../../../standards/adr-system/0319-dual-agent-handoff-openspec-ready.md)
- 🔧 **Schéma EvidencePack Amont** : [`src/pipelines/evidence_pack.py`](../../../../src/pipelines/evidence_pack.py)
