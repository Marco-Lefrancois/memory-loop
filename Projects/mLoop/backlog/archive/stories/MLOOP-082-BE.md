---
id: MLOOP-082-BE
jira_key: '-'
epic_key: EPIC-8-BUILD-HARNESS-GOVERNANCE
status: SHIPPED
type: Feature
title: Protocole TDD Red Green Enforcement et Verrouillage Gate 3
tags: [core, tdd, evidence, gatekeeper]
layer: backend
invest_score: 6/6
macrostructure: "workbench"
---
# [EPIC-8-BUILD-HARNESS-GOVERNANCE] Protocole TDD Red Green Enforcement et Verrouillage Gate 3 (MLOOP-082-BE)

## Description
**En tant que** Gatekeeper de la Définition de Terminé (DoD) du framework mLoop,  
**je veux** exiger et sceller cryptographiquement la signature d'échec initial (Red) puis de succès final (Green) pour chaque récit,  
**afin d'** interdire physiquement l'approbation de Gate 3 sans la preuve formelle et irréfutable du cycle TDD.

---

## Contexte & Périmètre

### Contexte Métier
Dans le développement logiciel autonome, il est fréquent que les agents écrivent des tests unitaires simultanément ou après le code de production sans jamais éprouver l'échec initial du test. Cette pratique annule la barrière de régression en favorisant des tests tautologiques.
Ce composant matérialise le protocole TDD en scellant deux empreintes SHA-256 dans l'EvidencePack du récit : la capture `RedSnapshot` avant implémentation, puis la capture `GreenSnapshot` après implémentation. L'orchestrateur refuse toute transition vers `DONE_TESTED` sans ces deux sceaux.

### In-Scope
- Moteur d'enforcement TDD `src/core/tdd_enforcer.py`.
- Enregistrement des signatures `RedSnapshot` et `GreenSnapshot` dans `Projects/<P>/memory/evidence/<STORY>_evidence.json`.
- Verrou de sécurité bloquant `swarm.py gate-approve --gate 3` si le couple Red/Green est absent ou invalide.
- Commande CLI `python src/swarm.py tdd-enforce --phase [red|green] --story <ID> --test-file <path>`.

### Out-of-Scope
- Génération automatique des cas de test (couverte par les récits amont ou l'ingénieur de test).
- Modification de la structure de pytest.

---

## Critères d'acceptation

### Opérations Métier & Logique Backend

#### 1. Enregistrement de la Preuve Red (Échec Initial Obligatoire)
* **Entrée Métier** : Identifiant du récit (`story_id: str`), chemin du fichier de test (`test_path: Path`).
* **Règles d'admissibilité & Validation** : Le fichier de test doit exister et être syntaxiquement valide.
* **Traitement & Algorithme Métier** : Exécution de `pytest` sur le fichier de test. Si le code de retour est non nul (échec ou test non implémenté), calcul du hash SHA-256 du banc de test et génération de `RedSnapshot`.
* **Résultat Métier & Mutations** : Sceau Red persisté dans le dictionnaire `tdd_cycle.red` du fichier d'évidence.
* **Cas de Rejet Métier** : Si tous les tests passent dès le premier run alors qu'aucun composant n'est censé exister (`UnexpectedPassingTestError`).

#### 2. Enregistrement de la Preuve Green (Succès Intégral & Clôture)
* **Entrée Métier** : Identifiant du récit (`story_id: str`), chemin du fichier de test (`test_path: Path`), chemin du code de production (`source_path: Path`).
* **Règles d'admissibilité & Validation** : Une empreinte `RedSnapshot` valide doit déjà être scellée pour le récit.
* **Traitement & Algorithme Métier** : Exécution de `pytest` et de `ast_checker`. Les deux doivent être à 100% verts. Calcul des hashes SHA-256 du code et des tests.
* **Résultat Métier & Mutations** : Sceau Green persisté dans `tdd_cycle.green`. Le récit est autorisé pour l'approbation de Gate 3.
* **Cas de Rejet Métier** : Échec unitaire (`TestFailureError`) ou violation de règle AST (`AstViolationError`).

---

## Parcours Interactif & API

### Contrats d'Échange CLI
- `python src/swarm.py tdd-enforce --phase red --story <ID> --test-file <path>` : Capture et scellement de la signature d'échec initial.
- `python src/swarm.py tdd-enforce --phase green --story <ID> --test-file <path> --source-file <path>` : Validation et scellement du succès final.

---

## Règles d'affaires
* **[Obligation d'Échec Initial Réel]** : Un récit ne peut pas enregistrer de sceau Green sans avoir préalablement scellé un sceau Red sur le même identifiant de story.
* **[Inviolabilité du Verrou de Gate 3]** : La commande `swarm.py gate-approve --gate 3` rejette immédiatement tout récit dont le bloc `tdd_cycle` est incomplet ou falsifié.

---

## Scénarios de test

```gherkin
# language: fr
Fonctionnalité: Protocole TDD Red Green Enforcement et Verrouillage Gate 3

  # 1. CHEMIN NOMINAL (Cycle Complet Red puis Green et Validation Gate 3)
  Scénario: Déroulement nominal du protocole TDD avec passage au vert
    Étant donné un nouveau récit et son fichier de test unitaire
    Quand la commande tdd-enforce est exécutée avec la phase "red"
    Alors le système constate l'échec attendu des tests
    Et un RedSnapshot est scellé dans l'EvidencePack
    Quand le code de production est implémenté et réussit tous les tests
    Et que la commande tdd-enforce est exécutée avec la phase "green"
    Alors un GreenSnapshot est enregistré
    Et l'approbation de Gate 3 est autorisée

  # 2. EXCEPTIONS & REJETS MÉTIER (Tentative d'Enregistrement Green sans Sceau Red)
  Scénario: Rejet de l'enregistrement Green sans preuve Red préalable
    Étant donné un récit sans RedSnapshot enregistré
    Quand un agent tente d'exécuter tdd-enforce avec la phase "green"
    Alors le système bloque l'opération avec l'erreur MissingRedSnapshotError
    Et aucun sceau Green n'est consigné

  # 3. RÉSILIENCE TECHNIQUE & MODE DÉGRADÉ (Blocage Physique de Gate 3)
  Scénario: Rejet de Gate 3 pour manquement au cycle TDD
    Étant donné un récit dont le fichier d'évidence n'a pas validé le cycle TDD
    Quand l'orchestrateur tente de valider la Gate 3
    Alors la transition est bloquée net
    Et un message d'erreur signale l'absence de certification Red-Green

  # 4. UX & OBSERVABILITÉ (Traçabilité Cryptographique dans l'EvidencePack)
  Scénario: Consultation des signatures SHA-256 du cycle TDD
    Étant donné un récit certifié TDD
    Quand l'EvidencePack est consulté
    Alors le bloc "tdd_cycle" présente les hashes SHA-256 du banc de test et du code
    Et les durées et horodatages UTC sont clairement consultables
```
