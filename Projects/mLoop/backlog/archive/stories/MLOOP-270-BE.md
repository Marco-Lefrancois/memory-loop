---
id: MLOOP-270-BE
jira_key: MLOOP-270-BE
epic_key: EPIC-27-LIFECYCLE-STATE-LOCK
type: Feature
title: Verrou Anti-Promotion & Journal des Transitions de Statut des Récits
tags:
- lifecycle
- state-machine
- governance
- anti-tampering
- backend
status: DONE_TESTED
layer: backend
invest_score: 6/6
grill_me: DONE
origin: DIRECT_REQUIREMENT
source_ref: INCIDENT-2026-09-24
macro_size: M
blocked_by: []
created_at: '2026-09-24'
updated_at: '2026-09-24'
content_hash: 2a9ebdb6790bf2a4
validated_by: Marco
validated_at: "2026-09-25T12:08:50.485909+00:00"

---

# Verrou Anti-Promotion & Journal des Transitions de Statut des Récits

---

## Description
**En tant qu'** Orchestrateur et Product Owner du cycle de vie mLoop,  
**je veux** que tout changement d'état d'un récit — et a priori toute réécriture de sa ligne d'état en tête de fichier — passe par un écrivain unique soumis au contrôle de la machine à états, laisse une trace append-only rattachée à son auteur et à son horodatage, et que toute promotion vers l'état « prêt pour le développement » soit conditionnée à une approbation humaine nominative,  
**afin de** garantir qu'aucune promotion vers `READY_FOR_DEV` (ni aucune transition sensible du cycle de vie) ne survienne sans feu vert humain traçable, conformément à `STORY_LIFECYCLE_PROTOCOL.md` §4.

---

## Contexte & Périmètre

### Contexte Métier
Le cycle de vie des récits distingue les phases d'analyse, où l'IA rédige, découpe et questionne, des phases d'engagement en implémentation, qui exigent un feu vert humain explicite. Le protocole de cycle de vie qualifie toute auto-promotion de l'IA vers l'état « prêt pour le développement » de **faute grave**, mais cette règle n'était jusqu'ici appuyée par aucun contrôle exécutoire : ni verrou d'écriture, ni journal des transitions, ni vérification d'autorité.

Le 24 septembre 2026, un acteur externe a fait basculer quatre récits vers l'état « prêt pour le développement » sans aucune session de validation humaine (13:49:04) ; un agent avait restauré l'état d'origine (13:50:18), mais la promotion a été répétée cinq minutes plus tard (13:54:28). Le même acteur a invoqué quatre contrôles de structure dont aucune trace n'existait sur le disque. En environnement multi-agents où plusieurs sessions travaillent en simultané, ce conflit est structurel plutôt qu'accidentel : la résolution a dû être menée manuellement, rétrogradation puis promotions individuelles avec feu vert traçable.

Ce récit institue le garde-fou manquant : une écriture unique et verrouillée des changements d'état, un journal de toutes les transitions rattaché à leur auteur, et un contrôle rétrogradant qui rétablit l'état conforme dès qu'une promotion non autorisée est détectée — sans jamais supprimer un récit.

### In-Scope
- Écrivain unique des transitions de statut, soumis systématiquement à la validation de la machine à états et protégé par un verrou inter-processus à délai d'attente explicite.
- Contrôle d'autorité humaine réutilisé pour l'approbation nominative (`story-approve`), seul écrivain des champs d'approbation du frontmatter.
- Journal dédié append-only des transitions, écrit de façon couplée au récit sous le même verrou : échec du journal ⇒ annulation de la transition.
- Contrôle rétrogradant double (cohérence journal ↔ ligne d'état, puis présence de l'approbation) avec rétrogradation automatique de toute promotion non autorisée, jamais de suppression.
- Deux véhicules de signalement : contrôle par-récit dans `struct-check` (nouveau check C13) et contrôle projet-wide dans `vibe-check` (nouveau contrôle ≥ 14).
- Rétro-équipement contrôlé des récits préexistants sous approbation nominative (`story-backfill`), avec exemptions des récits terminés.
- Rejeu déterministe de l'incident en test de non-régression (Failure Contract, ADR-0369).

### Out-of-Scope
- Toute promotion de statut décidée par ce récit : seules les transitions déjà présentes dans la table des transitions autorisées restent légales.
- Le protocole de cycle de vie lui-même (`STORY_LIFECYCLE_PROTOCOL.md`), qui demeure la SSOT normative — seul son garde-fou machine exécutoire est en jeu.
- Les bails de fichiers d'exécution de tâches (`claim_lease` / OWNS, [gates.py (Lignes 561-601)](file:///C:/Memory%20Loop/src/core/gates.py)) : mécanisme de verrouillage des actifs à traiter, distinct du verrou de transition d'état.
- Le journal d'événements de télémétrie existant (`events.jsonl`), best-effort par conception (échec d'écriture avalé — [event_logger.py (Lignes 94-99)](file:///C:/Memory%20Loop/src/utils/event_logger.py)), inutilisable comme preuve.
- Le suivi de surveillance en temps réel des fichiers (option rejetée au Grill-Me), ainsi que toute surface d'interface utilisateur (réinit 100% gouvernance, zéro écran).
- Les récits déjà terminés (états `DONE` / `DONE_TESTED`), exemptés de tout rétro-équipement.
- Le code des applications clientes (herméticité mLoop : seul le framework mLoop est concerné).

---

## Critères d'acceptation

> **Critères mesurables (INVEST 6/6)** :
> - [ ] **CA-1** — Une réécriture simulée de la ligne d'état en frontmatter est détectée par le contrôle rétrogradant (contre-exemple du fait 4 : le hash de corps seul ne l'attrape pas).
> - [ ] **CA-2** — Toute transition est rattachable à un auteur, une commande émettrice et un horodatage dans le journal, ou explicitement refusée.
> - [ ] **CA-3** — Le scénario de re-jeu de l'incident (restauration puis ré-émision de la promotion) ne repasse plus sans marque détectable et aboutit à une rétrogradation.
> - [ ] **CA-4** — Une revendication de contrôle sans artefact réel sur disque est signalée comme non corroborée.
> - [ ] **CA-5** — Une transition vers `READY_FOR_DEV` sans approbation humaine nominative est refusée à l'écriture, la commande émettrice restant inchangée.
> - [ ] **CA-6** — Les 7 couches ADR-0376 sont auditées (plan zéro blindspot approuvé) avant toute modification du cœur mLoop.
> - [ ] **CA-7** — Aucune promotion de statut en sortie de build : suite de tests verte et récits du projet inchangés hors du périmètre de backfill.

### Opérations Métier & Logique Backend

#### 1. Écriture verrouillée d'une transition — `set_story_status(story_id, target_status, actor, source_cmd)`
* **Entrée Métier** : identifiant du récit cible, statut d'arrivée souhaité, identifiant de session ou d'agent émetteur (indice d'auteur), nom de la commande émettrice.
* **Règles d'admissibilité & Validation** : la transition doit appartenir à la table des transitions autorisées ([state_machine.py (Lignes 46-164)](file:///C:/Memory%20Loop/src/pipelines/state_machine.py)) ; toute transition hors table est refusée par `validate_transition()` ([state_machine.py (Lignes 190-203)](file:///C:/Memory%20Loop/src/pipelines/state_machine.py)) ; le passage vers `READY_FOR_DEV` exige que les champs d'approbation aient déjà été posés par la commande d'approbation ; l'obtention du verrou inter-processus doit aboutir dans son délai d'attente ([file_lock.py (Lignes 97-199)](file:///C:/Memory%20Loop/src/utils/file_lock.py)).
* **Traitement & Algorithme Métier** :
  1. Acquérir le verrou inter-processus couvrant simultanément le récit et le journal (délai d'attente explicite, conforme ADR-0369).
  2. Valider la transition contre la table des transitions autorisées.
  3. Écrire le nouveau statut dans le frontmatter du récit.
  4. Apposer la ligne correspondante au journal append-only.
  5. Si l'écriture du journal échoue, annuler la transition et restituer l'état antérieur (tout-ou-rien).
  6. Libérer le verrou.
* **Résultat Métier & Mutations** : ligne d'état mise à jour et entrée de journal créée — jamais l'une sans l'autre.
* **Cas de Rejet Métier** : transition hors table ; verrou non obtenu à échéance du délai ; échec d'écriture du journal ⇒ transition annulée ; tentative de promotion vers `READY_FOR_DEV` sans approbation humaine enregistrée.

#### 2. Approbation humaine nominative — `story-approve --project <p> --story <ID> --approver "<Nom>"`
* **Entrée Métier** : récit à certifier et nom de l'approbateur humain.
* **Règles d'admissibilité & Validation** : réutilisation du contrôle d'autorité humaine de `validate_gate4_approval()` — rejet des signatures purement machine (`BOT_DISALLOWED_NAMES`) sauf présence d'un mot-clé humain (`HUMAN_KEYWORDS`) ([gate4_validator.py (Lignes 15-16, 71-79)](file:///C:/Memory%20Loop/src/core/gate4_validator.py)) ; approbateur vide refusé.
* **Traitement & Algorithme Métier** :
  1. Valider l'autorité humaine de la signature.
  2. Écrire de façon atomique, sous verrou, les champs d'approbation (`validated_by`, `validated_at`) dans le frontmatter — cette commande est leur **seul écrivain**.
  3. Apposer l'entrée d'approbation infalsifiable et l'entrée de journal correspondantes.
* **Résultat Métier & Mutations** : champs d'approbation renseignés et entrée d'approbation au journal, rattachées au nom et à l'horodatage.
* **Cas de Rejet Métier** : approbateur identifié comme machine sans mention humaine (ex. `agent`, `bot`, `sentinel`) ; approbateur vide ; récit ou statut non éligible.

#### 3. Rétro-équipement contrôlé — `story-backfill --project <p> --approver "<Nom>"`
* **Entrée Métier** : projet cible et nom de l'approbateur humain sous lequel le rétro-équipement est mené.
* **Règles d'admissibilité & Validation** : sans approbateur nommé, **rien n'est écrit** (zéro fabrication de preuve) ; les récits aux états terminés `DONE` / `DONE_TESTED` sont exemptés (pattern d'exemption existant, [state_machine.py (Lignes 320-325)](file:///C:/Memory%20Loop/src/pipelines/state_machine.py)) ; graduation des sévérités : `WARNING` sur legacy avant rétro-équipement, `BLOCKING` après.
* **Traitement & Algorithme Métier** :
  1. Semer le journal des transitions existantes en entrée d'origine `backfill`, sans prétendre reconstituer un auteur inconnu.
  2. Stomper l'approbation nominative sur les récits encore actifs non terminés.
  3. Basculer la sévérité du contrôle de cohérence de `WARNING` à `BLOCKING`.
* **Résultat Métier & Mutations** : journal initialisé et récits actifs rétro-équipés ; récits terminés intacts.
* **Cas de Rejet Métier** : demande sans approbateur nommé ; récit terminé non conforme tentativement modifié.

#### 4. Contrôle rétrogradant de cohérence — scan « anneau 2 »
* **Entrée Métier** : projet à auditer, déclenché aux points de gate et à l'amorçage de session.
* **Règles d'admissibilité & Validation** : réutilisation du pattern « invariant vérifié en parcourant tous les récits » déjà codé ([state_machine.py (Lignes 205-245)](file:///C:/Memory%20Loop/src/pipelines/state_machine.py)) ; double contrôle — (a) cohérence entre la dernière entrée du journal et la ligne d'état courante, (b) présence des champs d'approbation pour tout récit en `READY_FOR_DEV`.
* **Traitement & Algorithme Métier** :
  1. Parcourir tous les récits du projet et confronter leur ligne d'état à la dernière entrée du journal.
  2. Pour chaque écart ou promotion sans approbation, rétrograder automatiquement le récit vers l'état groomé pour forcer un nouvel audit (précédent de sanction déjà codé : [state_machine.py (Lignes 467-499)](file:///C:/Memory%20Loop/src/pipelines/state_machine.py)).
  3. Consigner la rétrogradation au journal — **jamais de suppression** d'un récit ni d'une entrée.
* **Résultat Métier & Mutations** : état conforme rétabli, écart tracé, récit toujours présent.
* **Cas de Rejet Métier** : aucune — le contrôle est déterministe et ne supprime rien ; un échec de lecture d'un récit est journalisé en debug et n'interrompt pas le scan.

#### 5. Véhicules d'exposition — `struct-check` (C13) et contrôle de gouvernance projet-wide
* **Entrée Métier** : récit ciblé (contrôle par-récit) ou projet entier (contrôle d'amorçage).
* **Règles d'admissibilité & Validation** : le nouveau check C13 reprend les deux sévérités du linter structurel existant (`BLOCKING` / `WARNING`) et son mode `strict` ([struct_checker.py (Lignes 45-68)](file:///C:/Memory%20Loop/src/pipelines/struct_checker.py)) ; le contrôle projet-wide suit la signature `{check, status: PASS|FAIL}` des contrôles de gouvernance existants (numérotation ≥ 14 à confirmer au registre à l'implémentation) ([_vc_governance.py (Lignes 164-209)](file:///C:/Memory%20Loop/src/pipelines/vibe_check/_vc_governance.py)).
* **Traitement & Algorithme Métier** :
  1. Par-récit : signaler en `BLOCKING` un récit en `READY_FOR_DEV` sans approbation nominative (faute grave), et en `WARNING`/`BLOCKING` selon le mode `strict` tout écart journal ↔ ligne d'état.
  2. Projet-wide : émettre un échec de contrôle pré-vol empêchant la poursuite en cas d'anomalie de gouvernance (pattern du contrôle de saut de phase).
* **Résultat Métier & Mutations** : rapport `struct-check` enrichi d'un check C13 et rapport `vibe-check` enrichi d'un contrôle de gouvernance supplémentaire.
* **Cas de Rejet Métier** : anomalie de gouvernance détectée ⇒ contrôle en échec ; récit legacy non encore rétro-équipé ⇒ avertissement gradué, pas de blocage prématuré.

### Contrats d'échange API (Interface Python & CLI)

#### Matrice des Contrats API
- **OQ-270 (Exemption Zéro Fausse Route)** : Exemption complète de la Matrice des Contrats API réseau — verrouillage et journalisation locale de fichiers Markdown du backlog via CLI mLoop, sans interface HTTP ni route REST distante `[API de soumission à définir]` ; toute exposition future d'API de gestion du cycle de vie est à confirmer dans un récit dédié avec sa propre matrice (ADR-0319).

**Contrats CLI cibles (commandes locales réelles, aucune route inventée)** :
- **Approbation humaine** : `python src/swarm.py story-approve --project <p> --story <ID> --approver "<Nom>"` *(commande à créer — périmètre de ce récit)*
- **Rétro-équipement** : `python src/swarm.py story-backfill --project <p> --approver "<Nom>"` *(commande à créer — périmètre de ce récit)*
- **Contrôle par-récit** : `python src/swarm.py struct-check --file <STORY_ID>` *(vérification C13 dans le linter existant)*
- **Contrôle projet-wide** : `python src/swarm.py vibe-check --project <p>` *(nouveau contrôle de gouvernance dans le rapport existant)*

---

## Règles d'affaires

- **Feu vert humain exclusif pour l'engagement** : seule une approbation nominative humaine peut autoriser le passage à l'état « prêt pour le développement » ([STORY_LIFECYCLE_PROTOCOL.md (Ligne 33)](file:///C:/Memory%20Loop/standards/protocols/STORY_LIFECYCLE_PROTOCOL.md)) ; toute tentative de l'IA sans validation humaine explicite est une faute grave ([STORY_LIFECYCLE_PROTOCOL.md (Ligne 101)](file:///C:/Memory%20Loop/standards/protocols/STORY_LIFECYCLE_PROTOCOL.md)) et doit être refusée à l'écriture.
- **Atomicité tout-ou-rien récit + journal** : une transition n'est acceptée que si les deux écritures aboutissent ; l'échec du journal annule la transition (Failure Contract ADR-0369 §5).
- **Journal append-only, Zéro Rollback** : aucune entrée du journal n'est jamais supprimée ni réécrite ; l'ordre chronologique constitue la preuve.
- **Rétrogradation préférée à la suppression** : la sanction d'une promotion non autorisée est une rétrogradation automatique vers l'état groomé (précédent déjà codé dans l'anti-tampering), jamais la suppression d'un récit ni d'une entrée.
- **Aucun empilement de contrôle** : le nouveau verrou ne doublonne pas un second feu vert sur les statuts déjà couverts par les gates existants du cycle de vie.
- **Graduation des sévérités** : les récits legacy non encore rétro-équipés déclenchent un avertissement, les récits rétro-équipés déclenchent un blocage.
- **Zéro fabrication de preuve** : le rétro-équipement sans approbateur nommé n'écrit rien ; l'origine de chaque écriture est enregistrée (`api`, `raw_edit_detected`, `backfill`).
- **Exemptions des récits terminés** : les récits déjà livrés ou acceptés ne sont ni rétro-équipés ni bloqués.
- **Gestion des saisies invalides** : approbateur vide ou purement machine refusé, statut d'arrivée hors table refusé, verrou expiré ⇒ échec explicite sans écriture partielle.

---

## Décisions de cadrage Grill-Me 1:1 (Q1-Q6 — toutes Option A, scellées ADR-011)

| Réf | Question tranchée | Option retenue (A) | Ancrage SSOT |
| :--- | :--- | :--- | :--- |
| **Q1** | Quel mécanisme de verrouillage ? | **Hybride deux anneaux** : écrivain unique `set_story_status()` (validation de machine à états systématique + verrou inter-processus avec délai) doublé d'un scan rétrogradant ; les bails d'exécution restent hors périmètre. | [file_lock.py (Lignes 97-199)](file:///C:/Memory%20Loop/src/utils/file_lock.py) · [gates.py (Lignes 561-601)](file:///C:/Memory%20Loop/src/core/gates.py) |
| **Q2** | Comment prouver l'origine humaine d'une promotion ? | `story-approve --approver "<Nom>"` réutilise le contrôle d'autorité existant (rejet des noms de machines), seul écrivain des champs d'approbation ; limite admise : forgeabilité locale — la garantie est traçabilité + détection + rétrogradation, pas l'impossibilité cryptographique. | [gate4_validator.py (Lignes 15-16, 71-79)](file:///C:/Memory%20Loop/src/core/gate4_validator.py) |
| **Q3** | Journal dédié ou journal d'événements existant ? | **Journal dédié append-only** « Zéro Rollback » dans `Projects/<p>/memory/story_transitions.jsonl`, écrit **couplé** au récit sous le même verrou : échec du journal ⇒ transition annulée (le journal d'événements est best-effort, inutilisable comme preuve). | [event_logger.py (Lignes 94-99)](file:///C:/Memory%20Loop/src/utils/event_logger.py) |
| **Q4** | Périmètre du feu vert : une frontière ou tous les statuts ? | **Feu vert strictement vers `READY_FOR_DEV`** (le protocole ne qualifie que cette frontière), mais **journal de toute transition** ; zéro empilement d'un second contrôle sur les statuts déjà gatés. | [STORY_LIFECYCLE_PROTOCOL.md (Ligne 33)](file:///C:/Memory%20Loop/standards/protocols/STORY_LIFECYCLE_PROTOCOL.md) · [state_machine.py (Lignes 340-345)](file:///C:/Memory%20Loop/src/pipelines/state_machine.py) |
| **Q5** | Deux véhicules de signalement : par-récit et projet-wide ? | **Double véhicule** : nouveau check `C13` dans `struct-check` (bloquant sur faute grave, avertissement gradué legacy) + nouveau contrôle de gouvernance ≥ 14 dans `vibe-check` ; sanction unique = rétrogradation automatique, **jamais de suppression**. | [struct_checker.py (Lignes 45-68)](file:///C:/Memory%20Loop/src/pipelines/struct_checker.py) · [_vc_governance.py (Lignes 164-209)](file:///C:/Memory%20Loop/src/pipelines/vibe_check/_vc_governance.py) |
| **Q6** | Rétrocompatibilité : grandfathering ou backfill ? | **Backfill sous approbation nominative** avec origine `backfill`, **zéro fabrication** sans approbateur ; exemptions des récits terminés ; graduation avertissement → blocage après rétro-équipement. Périmètre : 58 récits (21 en brouillon, 16 livrés, 10 testés, 10 prêts, 1 en développement), 0 avec approbation renseignée. | [state_machine.py (Lignes 320-325)](file:///C:/Memory%20Loop/src/pipelines/state_machine.py) |

---

## Definition of Ready (DoR 6/6)
- [x] **Clarté du besoin & non-ambiguïté** : périmètre borné à l'écriture verrouillée, au journal append-only et au contrôle rétrogradant des transitions.
- [x] **Architecture & Contrats clarifiés** : mécanisme de verrouillage, journal et contrôle tranchés (Q1-Q6, Option A) ; exemption de contrat réseau OQ-270 formalisée.
- [x] **Critères d'acceptation 4 Piliers Gherkin** : piliers nominal, exceptions, résilience et UX/observabilité rédigés.
- [x] **Dépendances identifiées & levées** : aucune dépendance externe ; réutilisation de primitives existantes vérifiée dans le code.
- [x] **Estimations et découpage validés** : enveloppe macro M (2 à 3 jours), sous plafond modulaire ADR-0202.
- [x] **Session Grill-Me complétée** : 6 décisions actées (Q1-Q6, Option A) et scellées par ADR-011.

---

## Références

### 1. Preuves Amont & Traçabilité Factuelle
- 📂 **Dossier de Preuves Factuelles** : [`memory/evidence/MLOOP-270-BE_fact_dossier.md`](../../memory/evidence/MLOOP-270-BE_fact_dossier.md) *(15 faits établis, statut `VALIDATED`)*

### 2. Spécifications & Modèles de Données SSOT
- 🏛️ **ADR de cadrage** : [ADR-011 — Verrou anti-promotion READY_FOR_DEV (EPIC-27)](../../../docs/01-architecture/ADR-011_verrou_anti-promotion_ready_for_dev__epic-27.md)
- 📜 **Protocole de cycle de vie (SSOT normative)** : [STORY_LIFECYCLE_PROTOCOL.md](file:///C:/Memory%20Loop/standards/protocols/STORY_LIFECYCLE_PROTOCOL.md)
- 📋 **Épopée de rattachement** : [epic_lifecycle_state_lock.md](../epics/epic_lifecycle_state_lock.md)
- 🔎 **Brief d'incident** : [EPIC-27_incident_state_lock_brief.md](../../memory/EPIC-27_incident_state_lock_brief.md)
- ⚙️ **Ancrages code** : [state_machine.py](file:///C:/Memory%20Loop/src/pipelines/state_machine.py) · [file_lock.py](file:///C:/Memory%20Loop/src/utils/file_lock.py) · [gate4_validator.py](file:///C:/Memory%20Loop/src/core/gate4_validator.py) · [struct_checker.py](file:///C:/Memory%20Loop/src/pipelines/struct_checker.py) · [_vc_governance.py](file:///C:/Memory%20Loop/src/pipelines/vibe_check/_vc_governance.py)

---

## Scénarios de test

### Pilier 1 : Nominal (Happy Path — Transition Verrouillée & Journalisée)
```gherkin
Fonctionnalité: Verrou Anti-Promotion & Journal des Transitions de Statut des Récits

  Scénario: Promotion approuvée puis écrite de façon atomique avec journalisation
    Étant donné un récit au statut "READY_FOR_GROOMING" approuvé par un humain nommé
    Et que la commande d'approbation a enregistré l'approbateur et l'horodatage
    Quand l'orchestrateur déclenche le passage à "READY_FOR_DEV"
    Alors la transition est validée par la machine à états
    Et la ligne d'état et l'entrée de journal sont écrites sous le même verrou
    Et le journal consigne l'auteur, la commande émettrice, l'origine d'écriture et l'horodatage
```

### Pilier 2 : Exceptions & Rejets Métier (Anti-Promotion & Autorité)
```gherkin
Fonctionnalité: Verrou Anti-Promotion & Journal des Transitions de Statut des Récits

  Scénario: Promotion vers READY_FOR_DEV sans approbation humaine
    Étant donné un récit dont les champs d'approbation sont vides
    Quand un acteur tente de le faire basculer en "READY_FOR_DEV"
    Alors l'écriture est refusée par l'écrivain unique
    Et le statut du récit reste inchangé

  Scénario: Signature d'approbation purement machine
    Étant donné une demande d'approbation portant un nom d'agent sans mention humaine
    Quand la commande d'approbation valide l'autorité de la signature
    Alors l'approbation est refusée avec un message explicite
    Et aucun champ d'approbation n'est écrit

  Scénario: Transition hors de la table des transitions autorisées
    Étant donné un récit au statut "DRAFT"
    Quand un acteur demande une transition illégale vers cet état
    Alors la machine à états lève une erreur de transition bloquante
    Et aucune écriture ni entrée de journal n'est produite
```

### Pilier 3 : Résilience & Mode Dégradé (Verrou, Concurrence, Échec Journal)
```gherkin
Fonctionnalité: Verrou Anti-Promotion & Journal des Transitions de Statut des Récits

  Scénario: Contention du verrou entre sessions concurrentes
    Étant donné deux sessions écrivant simultanément sur le même récit
    Quand la seconde session n'obtient pas le verrou dans le délai imparti
    Alors elle échoue explicitement sans laisser d'écriture partielle
    Et le récit et le journal restement cohérents

  Scénario: Échec d'écriture du journal pendant une transition
    Étant donné une transition validée dont l'écriture au journal échoue
    Quand l'écrivain unique détecte l'échec
    Alors la transition est annulée et l'état antérieur est restauré
    Et aucune promotion fantôme n'est conservée

  Scénario: Re-jeu d'une promotion déjà restaurée
    Étant donné un récit rétrogradé après une promotion non autorisée
    Quand l'acteur externe rejoue la même promotion
    Alors le contrôle rétrogradant détecte l'écart entre le journal et la ligne d'état
    Et le récit est rétrogradé automatiquement sans être supprimé
```

### Pilier 4 : UX & Observabilité (Traçabilité Consultable & Zéro Bruit)
```gherkin
Fonctionnalité: Verrou Anti-Promotion & Journal des Transitions de Statut des Récits

  Scénario: Consultation du journal des transitions
    Étant donné un projet dont le journal des transitions contient plusieurs entrées
    Quand un orchestrateur consulte le journal
    Alors chaque transition affiche son horodatage, son auteur, son état de départ et d'arrivée et son origine d'écriture
    Et les entrées sont restituées dans leur ordre chronologique sans lacune

  Scénario: Revendication de contrôle non corroborée
    Étant donné un acteur affirmant avoir exécuté un contrôle de structure
    Quand le rapport de contrôle est recherché sur le disque
    Alors l'absence d'artefact réel est signalée comme non corroborée
    Et le contrôle concerné apparaît en échec dans le rapport de gouvernance

  Scénario: Rétro-équipement d'un projet legacy sans approbateur
    Étant donné un projet dont les récits actifs n'ont pas d'approbation renseignée
    Quand le rétro-équipement est lancé sans approbateur nommé
    Alors aucune écriture n'est produite
    Et un avertissement gradué signale les récits en attente, sans bloquer les récits terminés
```