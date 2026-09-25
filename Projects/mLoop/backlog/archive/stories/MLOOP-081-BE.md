---
id: MLOOP-081-BE
jira_key: '-'
epic_key: EPIC-8-BUILD-HARNESS-GOVERNANCE
status: SHIPPED
type: Feature
title: Moteur de Tournoi de Code Multi Draft et Matrice Pareto
tags: [core, tournament, pareto, quality]
layer: backend
invest_score: 6/6
macrostructure: "workbench"
---
# [EPIC-8-BUILD-HARNESS-GOVERNANCE] Moteur de Tournoi de Code Multi Draft et Matrice Pareto (MLOOP-081-BE)

## Description
**En tant qu'** Orchestrateur de Synthèse de Code mLoop,  
**je veux** soumettre les ébauches concurrentes de code à un banc d'épreuves physiques et une matrice multicritère de Pareto,  
**afin de** sélectionner mathématiquement le meilleur candidat en Golden Master tout en archivant les alternatives pour le Replay Simulator Dream RSI.

---

## Contexte & Périmètre

### Contexte Métier
Dans le développement agentique, le tir unique souffre du biais de premier jet (*first-token bias*).
Pour les composants critiques du Système 1 (Core Engine), la génération de 2 à 3 candidats concurrents physiques (Candidat A: Minimaliste standard library, Candidat B: Robuste et modulaire) permet d'arbitrer objectivement selon une fonction d'utilité Pareto combinant robustesse, sobriété et performance.

### In-Scope
- Pipeline déterministe `src/pipelines/code_tournament.py` évaluant les candidats stockés dans `Projects/<P>/memory/drafts/code/<STORY>/`.
- Filtrage éliminatoire par Hard Gates (100% Pytest vert et 0 violation AST `code-check`).
- Calcul de la fonction de fitness Pareto $S_{\text{pareto}} = 0.40R + 0.35S + 0.25P$.
- Promotion automatique du vainqueur en cible définitive dans `src/` et scellement contrefactuel des perdants.

### Out-of-Scope
- Jugement qualitatif ou subjectif par un LLM lors de l'évaluation (l'évaluation est 100% physique et déterministe).
- Compilation de langages autres que Python.

---

## Critères d'acceptation

### Opérations Métier & Logique Backend

#### 1. Exécution du Tournoi de Candidats et Promotion Golden Master
* **Entrée Métier** : Identifiant du récit (`story_id: str`), chemin de destination (`target_path: Path`).
* **Règles d'admissibilité & Validation** : Le dossier `memory/drafts/code/<story_id>/` doit contenir au minimum 2 fichiers candidats (`candidate_A_*.py`, `candidate_B_*.py`). Le banc de test associé doit être disponible sous `tests/`.
* **Traitement & Algorithme Métier** :
  1. Pour chaque candidat : substitution temporaire ou import dynamique, exécution du banc unitaire pytest, exécution du linter AST.
  2. Rejet immédiat de tout candidat échouant au test ou au linter (`DISQUALIFIED`).
  3. Pour les candidats qualifiés, calcul de $R$ (complexité cyclomatique, annotations de types), $S$ (lignes physiques), $P$ (vitesse relative d'exécution).
  4. Calcul du score $S_{\text{pareto}}$ pondéré.
  5. Copie du candidat gagnant vers `target_path`.
* **Résultat Métier & Mutations** : Fichier promu dans `src/`, rapport de tournoi persisté dans `Projects/<P>/memory/evidence/<story_id>_tournament.json`.
* **Cas de Rejet Métier** : Aucun candidat n'a réussi les tests unitaires (`NoQualifiedCandidateError`), dossier de drafts introuvable (`DraftFolderNotFoundError`).

---

## Parcours Interactif & API

### Contrats d'Échange CLI
- `python src/swarm.py code-tournament --story <ID> --target <chemin>` : Lancement du tournoi pour le récit spécifié et promotion du vainqueur.

---

## Règles d'affaires
* **[Inviolabilité des Portes Dures]** : Un candidat qui échoue à un seul test unitaire ou présente une seule violation AST ne peut jamais être promu, quel que soit son score de vitesse ou de compacité.
* **[Conservation Contrefactuelle]** : Tout candidat éliminé ou non retenu est conservé dans le registre de drafts pour alimenter la simulation d'apprentissage par renforcement hors-ligne (Dream RSI / ADR-0372).

---

## Scénarios de test

```gherkin
# language: fr
Fonctionnalité: Moteur de Tournoi de Code Multi Draft et Matrice Pareto

  # 1. CHEMIN NOMINAL (Tournoi avec 2 Candidats et Promotion du Vainqueur)
  Scénario: Évaluation de 2 candidats valides et promotion du meilleur score Pareto
    Étant donné un dossier de drafts contenant "candidate_A_minimal.py" et "candidate_B_robust.py"
    Et que les deux candidats passent avec succès 100% des tests unitaires
    Et qu'ils présentent 0 violation au linter AST
    Quand le moteur de tournoi évalue les deux candidats
    Alors le score Pareto est calculé pour chacun selon la pondération constitutionnelle
    Et le candidat ayant obtenu le score le plus élevé est promu dans le répertoire cible
    Et un rapport de tournoi est généré dans les évidences

  # 2. EXCEPTIONS & REJETS MÉTIER (Élimination d'un Candidat Défaillant)
  Scénario: Disqualification immédiate d'un candidat échouant aux tests
    Étant donné un candidat "candidate_A" passant tous les tests
    Et un candidat "candidate_B" causant un échec de test ou une violation AST
    Quand le tournoi est exécuté
    Alors le candidat "candidate_B" est marqué comme disqualifié
    Et le candidat "candidate_A" est déclaré vainqueur par forfait

  # 3. RÉSILIENCE TECHNIQUE & MODE DÉGRADÉ (Aucun Candidat Qualifié)
  Scénario: Échec global lorsqu'aucun candidat ne franchit les portes dures
    Étant donné un ensemble de candidats où chacun échoue aux tests unitaires
    Quand le tournoi est exécuté
    Alors le système lève l'exception NoQualifiedCandidateError
    Et aucun fichier de production n'est écrasé ni modifié dans src/

  # 4. UX & OBSERVABILITÉ (Matrice Comparative Déterministe)
  Scénario: Affichage détaillé de la matrice de décision Pareto
    Étant donné la fin d'un tournoi réussi
    Quand les résultats sont affichés dans la console
    Alors un tableau comparatif affiche pour chaque candidat son score de robustesse, simplicité et vélocité
    Et le nom du fichier promu en Golden Master est mis en évidence
```
