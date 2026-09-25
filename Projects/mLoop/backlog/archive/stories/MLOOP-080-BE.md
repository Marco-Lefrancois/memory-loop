---
id: MLOOP-080-BE
jira_key: '-'
epic_key: EPIC-8-BUILD-HARNESS-GOVERNANCE
status: SHIPPED
type: Feature
title: Linter Statique Déterministe AST code-check CLI
tags: [core, linter, ast, quality]
layer: backend
invest_score: 6/6
macrostructure: "workbench"
---
# [EPIC-8-BUILD-HARNESS-GOVERNANCE] Linter Statique Déterministe AST code-check CLI (MLOOP-080-BE)

## Description
**En tant que** Développeur et Gardien de la Qualité du framework mLoop,  
**je veux** disposer d'un outil CLI déterministe d'analyse syntaxique AST locale,  
**afin de** vérifier instantanément (<50 ms) la conformité du code Python aux règles de modularité ADR-0202 et aux standards senior ADR-0369 sans dépendance externe.

---

## Contexte & Périmètre

### Contexte Métier
En Phase 3 (Build), les modules produits par les agents peuvent dériver silencieusement : inflation de taille, oubli de gestion de contextes `with`, absence de timeouts sur les commandes système ou suppression d'erreurs via `except: pass`.
Ce composant fournit une commande d'audit statique `python src/swarm.py code-check` basée exclusivement sur le module standard `ast`, assurant une validation physique immédiate et opposable.

### In-Scope
- Analyseur syntaxique AST `src/core/ast_checker.py` auditant les 5 règles `RULE-AST-01` à `RULE-AST-05`.
- Commande CLI `python src/swarm.py code-check` supportant les arguments `--file`, `--story` et `--all`.
- Rapport d'audit standardisé indiquant la règle enfreinte, le fichier, le numéro de ligne et la correction attendue.

### Out-of-Scope
- Linters tiers lourds (Ruff, Flake8, Pylint) ou analyseurs de type statique externes (Mypy).
- Formatage automatique ou modification du code source inspecté.

---

## Critères d'acceptation

### Opérations Métier & Logique Backend

#### 1. Audit Statique AST d'un Fichier Source
* **Entrée Métier** : Chemin du fichier Python à auditer (`file_path: Path`).
* **Règles d'admissibilité & Validation** : Le fichier doit exister sur disque et être un fichier syntaxiquement valide (`.py`).
* **Traitement & Algorithme Métier** : Analyse AST visitant les nœuds pour détecter les violations aux 5 règles :
  - `RULE-AST-01` : Lignes physiques $\le 300$ et taille physique $\le 15\,360$ octets.
  - `RULE-AST-02` : Ressources nues interdites (`sqlite3.connect`, `open`, `httpx.Client`) hors bloc `with`/`async with`.
  - `RULE-AST-03` : Timeout obligatoire sur `subprocess.run`, `subprocess.Popen`, `requests.*`, `httpx.*`.
  - `RULE-AST-04` : Interdiction de `except: pass` sans fonction de log.
  - `RULE-AST-05` : `stacklevel=2` obligatoire sur `warnings.warn`.
* **Résultat Métier & Mutations** : Objet structuré `AstAuditReport(passed: bool, violations: list[AstViolation], duration_ms: float)`.
* **Cas de Rejet Métier** : Fichier inexistant (`FileNotFoundError`), erreur de syntaxe empêchant la construction de l'arbre AST (`SyntaxError`).

---

## Parcours Interactif & API

### Contrats d'Échange CLI
- `python src/swarm.py code-check --file <chemin>` : Audit direct d'un fichier source unique.
- `python src/swarm.py code-check --story <ID>` : Audit de tous les fichiers de production et de tests associés à un récit.
- `python src/swarm.py code-check --all` : Audit exhaustif du répertoire `src/`.

---

## Règles d'affaires
* **[Tolérance Zéro sur la Modularité]** : Tout module dépassant 300 lignes physiques ou 15 Ko est déclaré non conforme et bloque le passage de Gate 3.
* **[Sécurité des Ressources & Deadlines]** : Tout appel d'E/S bloquantes sans gestion de contexte ou sans temporisation maximale explicite est bloquant.
* **[Interdiction du Silence d'Erreur]** : Toute exception interceptée doit obligatoirement émettre une trace de journalisation.

---

## Scénarios de test

```gherkin
# language: fr
Fonctionnalité: Linter Statique Déterministe AST code-check CLI

  # 1. CHEMIN NOMINAL (Audit Conforme d'un Module mLoop)
  Scénario: Audit réussi d'un fichier conforme aux standards
    Étant donné un fichier Python respectant les plafonds ADR-0202 et les standards ADR-0369
    Quand le linter AST exécute l'analyse statique du fichier
    Alors le rapport indique 0 violation
    Et le statut d'audit est validé avec succès
    Et la durée d'exécution est inférieure à 50 millisecondes

  # 2. EXCEPTIONS & REJETS MÉTIER (Détection des 5 Règles AST)
  Scénario: Détection des violations de ressources nues et de timeouts manquants
    Étant donné un fichier Python contenant un appel "subprocess.run" sans argument timeout
    Et un bloc "except: pass" sans journalisation
    Quand le linter AST analyse le fichier
    Alors le linter remonte explicitement les violations RULE-AST-03 et RULE-AST-04
    Et le code de retour CLI signale l'échec de conformité

  # 3. RÉSILIENCE TECHNIQUE & MODE DÉGRADÉ (Fichier Inexistant ou Syntaxe Invalide)
  Scénario: Gestion d'une erreur de syntaxe ou d'un fichier manquant
    Étant donné un chemin pointant vers un fichier inexistant ou corrompu
    Quand la commande code-check est exécutée
    Alors le système capture l'anomalie sans planter
    Et un message d'erreur explicite est renvoyé sur la sortie d'erreur

  # 4. UX & OBSERVABILITÉ (Rapport Synthétique & Métadonnées)
  Scénario: Affichage du rapport tabulaire structuré
    Étant donné l'exécution de code-check sur un ensemble de fichiers
    Quand l'audit est terminé
    Alors la console affiche un tableau récapitulatif par fichier
    Et le nombre total de lignes et la conformité sont clairement visibles
```
