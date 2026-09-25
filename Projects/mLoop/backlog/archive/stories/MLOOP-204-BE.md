---
id: MLOOP-204-BE
jira_key: ''
epic_key: EPIC-20-PORTFOLIO-GOVERNANCE
type: Feature
title: Clôture de la cinquième porte de gouvernance du framework mLoop sous feu vert
  humain
tags:
- portfolio
- governance
- gate5
- jira-sync
- ship
status: DONE
grill_me: DONE
layer: backend
invest_score: 6/6
macro_size: S
origin: DIRECT_REQUIREMENT
source_ref: epic_portfolio_governance_2026q4.md
blocked_by:
- MLOOP-200-BE
- MLOOP-201-BE
- MLOOP-202-BE
- MLOOP-207-BE
created_at: '2026-09-23'
ttl_cycles: 2
---
# Clôture de la cinquième porte de gouvernance du framework mLoop sous feu vert humain

---

## Description
**En tant qu'** Orchestrateur mLoop,
**je veux** exécuter la séquence de clôture de la cinquième porte du projet mLoop lui-même — synchronisation Jira ciblée en mode échec-fermé d'abord en simulation puis en écriture, archivage local des connaissances obsolètes, validation de la sous-suite de tests de phase, et poussée du dépôt —,
**afin de** sceller officiellement les cinq portes de gouvernance du framework, de garantir un état de dépôt reproductible et traçable, et de n'effectuer aucune écriture externe ni aucune diffusion sans feu vert humain explicite et distinct à chaque étape irréversible.

---

## Contexte & Périmètre

### Contexte Métier
Le framework mLoop a franchi les portes 1 à 4 (cadrage, prêts, fini, recette) et son état de cycle de vie affiche déjà la phase de distribution. Il manque la clôture formelle de la porte 5 : la synchronisation contrôlée vers le gestionnaire de tickets, l'archivage des connaissances remplacées, la preuve que la chaîne de vérification de phase est verte, et la poussée du dépôt sous accord explicite. Tant que cette séquence n'est pas menée à son terme sous supervision humaine, le framework reste dans un état semi-ouvert : les portes précédentes sont approuvées mais rien n'atteste qu'un dépôt propre, une synchronisation sans violation de garde et une suite de vérification de phase validée coexistent au même instant. La décision de Grill a écarté deux faux problèmes du brouillon : l'archivage local des connaissances n'écrit aucun ticket distant, et la diffusion externe n'est jamais déclenchée par la simple transition d'état — toute écriture ou annonce reste une commande séparée sous feu vert dédié.

### In-Scope
- Inventaire déterministe des récits de l'épopée de gouvernance du portefeuille dont la clé de ticket est réelle et non vide, servant de liste de ciblage pour la synchronisation.
- Exécution de la synchronisation Jira en mode simulation (échec-fermé, sans écriture) et restitution intégrale du rapport au décideur.
- Feu vert humain explicite et distinct sur le rapport de simulation avant toute bascule en écriture.
- Exécution de la synchronisation Jira en écriture sur la liste de ciblage uniquement, jamais sur l'intégralité du projet en balayage.
- Exécution de l'archivage local des connaissances obsolètes vers le registre d'archives du projet.
- Exécution de la sous-suite de vérification de phase documentée (fichiers de vérification relatifs à la synchronisation Jira, au nettoyage Markdown de ticket, à la résilience de synchronisation, au cycle de révision et à l'archivage de connaissances) avec exigence de zéro échec.
- Rapport best-effort de la suite de vérification complète, les échecs hors périmètre de phase étant consignés comme dette nominative et non bloquants.
- Poussée du dépôt vers la branche principale uniquement après feu vert humain explicite et distinct.
- Consignation de la cinquième porte comme approuvée dans l'état de cycle de vie du projet avec horodatage et signature d'approbation.
- Production du dossier de preuves et du paquet de preuve couvrant l'inventaire de ciblage, chaque rapport d'étape et les feu verts.

### Out-of-Scope
- Modification du code source du framework, des gabarits, des protocoles ou des directives (aucune écriture sous les sources du moteur).
- Clôture de porte des projets clients : leurs cycles de vie sont indépendants et ne sont pas touchés par la présente séquence.
- Création de nouvelles récits, de nouvelles épopées ou de nouvelles décisions d'architecture après la clôture.
- Balayage de synchronisation de l'intégralité des récits du projet sans liste de ciblage explicite.
- Archivage de connaissances depuis d'autres dépôts que le projet courant.
- Exigence de zéro échec sur la suite de vérification complète hors des fichiers de phase documentés : les échecs legacy sont une dette tracée, pas un blocage de porte.
- Toute écriture vers un système externe ou toute notification à une partie prenante sans feu vert humain distinct et explicite.
- Exécution de commandes d'export de carnet de notes ou d'autres diffusions sous couvert de la présente séquence.

---

## Critères d'acceptation

### Opérations Métier & Logique Backend *(backend)*
#### 1. Inventaire de ciblage des récits à clé de ticket réelle
* **Entrée Métier** : Ensemble des récits de l'épopée de gouvernance du portefeuille, valeur de clé de ticket portée par chaque frontmatter.
* **Règles d'admissibilité & Validation** : Un récit n'entre dans la liste de ciblage que si sa clé de ticket est non vide, non blanche et distincte du marqueur de clé vide ; une clé vide ou illisible exclut le récit du ciblage sans le modifier.
* **Traitement & Algorithme Métier** : Balayage déterministe des fichiers de récits de l'épopée, lecture de la clé de ticket, constitution de la liste ordonnée des clés éligibles, consignation des exclusions motivées dans le dossier de preuves.
* **Résultat Métier & Mutations** : Une liste de ciblage est produite et consignée ; chaque inclusion est adossée à une clé non vide vérifiée ; aucune modification de récit n'est effectuée à ce stade.
* **Cas de Rejet Métier** : Rejet d'une clé de ticket vide ou composée uniquement d'espaces pour le ciblage ; rejet d'une liste de ciblage vide exécutée comme si elle était valide ; rejet d'une clé inventée par inférence.

#### 2. Simulation de synchronisation Jira en mode échec-fermé puis restitution du rapport
* **Entrée Métier** : Liste de ciblage consignée, commande officielle de synchronisation en mode simulation, projet courant.
* **Règles d'admissibilité & Validation** : La simulation s'exécute sans aucun drapeau d'écriture ; elle doit se terminer sans violation de garde échec-fermée ; le rapport intégral est restitué au décideur avant toute suite.
* **Traitement & Algorithme Métier** : Invocation de la commande officielle de synchronisation en mode simulation sur la liste de ciblage, collecte du code de sortie, du rapport horodaté et du journal cumulatif, transmission intégrale au décideur.
* **Résultat Métier & Mutations** : Un rapport de simulation existe sous la mémoire du projet ; le décideur dispose du détail complet ; aucun ticket distant n'a été écrit.
* **Cas de Rejet Métier** : Rejet d'une bascule en écriture avant approbation humaine du rapport de simulation ; rejet d'une simulation terminée par une violation de garde ; rejet d'une poursuite de séquence sur code de sortie non nul.

#### 3. Écriture de synchronisation Jira sous feu vert, strictement ciblée
* **Entrée Métier** : Rapport de simulation approuvé, feu vert humain explicite, liste de ciblage inchangée.
* **Règles d'admissibilité & Validation** : L'écriture n'est lancée qu'après feu vert distinct et explicite ; elle porte exclusivement sur la liste de ciblage ; le balayage de l'intégralité du projet sans confirmation dédiée est interdit dans la présente séquence.
* **Traitement & Algorithme Métier** : Invocation de la commande officielle en mode écriture avec confirmation de portée sur la liste de ciblage, vérification du code de sortie, mise à jour du rapport horodaté et du journal cumulatif.
* **Résultat Métier & Mutations** : Les tickets de la liste de ciblage sont alignés côté gestionnaire distant ; le rapport d'écriture est consigné ; les récits hors ciblage sont intacts.
* **Cas de Rejet Métier** : Rejet d'une écriture sans feu vert préalable ; rejet d'une écriture en balayage total non confirmé ; rejet d'une écriture poursuivie après violation de garde.

#### 4. Archivage local des connaissances obsolètes
* **Entrée Métier** : Décisions d'architecture du projet candidates à l'archivage, registre d'archives local du projet.
* **Règles d'admissibilité & Validation** : L'archivage ne touche que le registre local du projet ; aucune connexion au gestionnaire de tickets n'est effectuée ; seules les connaissances formellement remplacées sont archivées.
* **Traitement & Algorithme Métier** : Invocation de la commande officielle d'archivage, scan des décisions, mise à jour du registre local, restitution du nombre d'éléments archivés.
* **Résultat Métier & Mutations** : Le registre d'archives local est à jour ; le nombre d'éléments archivés est affiché et consigné ; aucun état distant n'est modifié.
* **Cas de Rejet Métier** : Rejet d'un archivage ciblant un dépôt autre que le projet courant ; rejet d'une commande d'archivage utilisée comme substitut à la synchronisation de tickets.

#### 5. Validation de la sous-suite de phase, rapports best-effort, poussée sous feu vert et scellement de porte
* **Entrée Métier** : Séquence de simulation, écriture et archivage complétées, sous-suite de vérification de phase documentée, dépôt git, état de cycle de vie du projet.
* **Règles d'admissibilité & Validation** : La sous-suite de phase doit atteindre zéro échec avant toute poussée ; la suite complète n'est exigée qu'en best-effort avec consignation des échecs comme dette ; la poussée exige un feu vert humain explicite et distinct ; le scellement de porte exige une entrée d'approbation horodatée et signée.
* **Traitement & Algorithme Métier** : Exécution de la sous-suite de phase, exécution best-effort de la suite complète avec rapport des échecs, sous feu vert poussée du dépôt vers la branche principale, puis écriture de l'entrée de cinquième porte dans l'état de cycle de vie avec horodatage et approbateur.
* **Résultat Métier & Mutations** : Sous-suite verte ; dettes d'échec legacy consignées ; dépôt poussé sous feu vert ; cinquième porte enregistrée comme approuvée avec signature ; séquence de clôture close.
* **Cas de Rejet Métier** : Rejet d'une poussée avant feu vert distinct ; rejet d'une poussée alors qu'un échec subsiste dans la sous-suite de phase ; rejet d'un scellement de porte sans approbation horodatée ; rejet d'un scellement traitant un échec best-effort comme bloquant silencieusement ou, à l'inverse, comme inexistant.

#### Matrice des Contrats API
N/A — Récit d'orchestration de séquence de clôture : les écritures vers le gestionnaire de tickets transitent exclusivement par la commande officielle du framework, sans définition ni invention de route réseau dans le présent récit.
- **OQ-204 (Exemption Zéro Fausse Route)** : Exemption de la Matrice des routes déclaratives — le récit orchestre des commandes CLI officielles (simulation/écriture de synchronisation, archivage local, vérification, poussée), sans interface réseau `[API de soumission à définir]` ; les routes du gestionnaire de tickets sont celles du moteur interne déjà implémenté et ne sont ni inventées ni spécifiées ici ; toute extension vers un nouveau point d'échange deviendrait une question ouverte nominative `[API de soumission à définir]`, jamais simulée.
- **Admission of Limits** : La résilience d'interface couverte par le troisième pilier porte sur l'arrêt de séquence en cas de code de sortie non nul et sur l'interdiction d'écriture sans feu vert, non sur la disponibilité du service distant dont le comportement est délégué aux gardes échec-fermées de la commande officielle.

---

## Règles d'affaires

- **Échec-fermé par défaut** : Toute synchronisation de tickets démarre en simulation sans écriture ; la bascule en écriture est une décision humaine explicite, jamais une conséquence implicite d'un code de sortie nul.
- **Ciblage explicite, jamais de balayage total** : La synchronisation porte sur une liste de clés inventoriée ; le balayage de l'intégralité du projet exige une confirmation dédiée qui fait hors du présent récit.
- **Feu vert distinct par étape irréversible** : Simulation approuvée, écriture approuvée et poussée approuvée sont trois feu verts séparés ; un feu vert ne présume pas du suivant.
- **Archivage local strictement local** : L'archivage des connaissances obsolètes n'écrit aucun ticket distant et ne se substitue jamais à la synchronisation de tickets.
- **Sous-suite de phase bloquante, suite complète en dette** : Zéro échec sur les fichiers de vérification de phase documentés est requis pour la porte ; les échecs legacy hors périmètre sont une dette nominative rapportée, ni masqués ni érigés en blocage silencieux.
- **Aucune notification externe automatique** : La transition d'état de cycle de vie et la poussée de dépôt ne déclenchent aucune diffusion à une partie prenante ; toute annonce ou export reste une commande séparée sous feu vert dédié.
- **Zéro modification de source** : Aucun fichier des sources du moteur, des gabarits, des protocoles ou des directives n'est écrit pendant la séquence de clôture.
- **Zéro création après clôture** : Aucun récit, aucune épopée et aucune décision d'architecture ne sont créés dans le cadre de la séquence de porte.
- **Arrêt sur anomalie** : Un code de sortie non nul à n'importe quelle étape stoppe la séquence ; la cause est consignée ; aucune étape suivante n'est lancée avant résolution ou décision humaine explicite de report.
- **Gestion des données invalides** : Une liste de ciblage vide, une clé de ticket illisible ou un rapport de simulation absent est signalé dans le dossier de preuves et n'est jamais comblé par supposition ; une sous-suite non verte empêche la poussée et est tracée.

---

## Références

### 1. Preuves Amont & Traçabilité Factuelle
- 📂 **Dossier de Preuves Factuelles** : [`memory/evidence/MLOOP-204-BE_fact_dossier.md`](../../memory/evidence/MLOOP-204-BE_fact_dossier.md)
- 🏛️ **Décisions de cadrage** : Q1 = sous-suite de phase documentée comme seuil bloquant, suite complète en best-effort dette · prémisse « l'archivage touche les tickets Jira » éliminée par les faits (registre local uniquement) · Q2 = ciblage explicite par clé, zéro balayage total · Q3 = aucune notification externe automatique, diffusion = commande séparée sous feu vert distinct (Grill-Me 2026-09-24)

### 2. Spécifications & Modèles de Données SSOT
- 📜 **Dossier de preuves** : [DOSSIER_DE_PREUVES_PROTOCOL.md](../../../standards/protocols/DOSSIER_DE_PREUVES_PROTOCOL.md)
- 📜 **Grill macro / micro** : [ADR-0320](../../../standards/adr-system/0320-grill-me-frontier-design-tree-alignment.md)
- 📜 **Gabarit de récit** : [story_template.md](../../../standards/blueprints/story_template.md)
- 📜 **Gouvernance de la synchronisation** : [ADR-0304](../../../standards/adr-system/0304-gouvernance-synchronisation-jira.md)
- 📜 **Archivage de connaissances** : [ADR-0324](../../../standards/adr-system/0324-auto-eval-harvesting-context-guard.md)
- 📜 **Garde-fous de porte** : [ADR-0386](../../../standards/adr-system/0386-gouvernance-github-rulesets-pull-requests-et-garde-fous-phase-5-ship.md)
- 📜 **Cycle de vie** : [PROJECT_LIFECYCLE_STAGES.md](../../../standards/protocols/PROJECT_LIFECYCLE_STAGES.md)
- 📜 **Plan de vérification de phase** : [PHASE_FILES_AND_TEST_PLAN.md](../../../standards/protocols/PHASE_FILES_AND_TEST_PLAN.md)
- 📜 **Guide de commande** : [CLI_PIPELINE_GUIDE.md](../../../standards/protocols/CLI_PIPELINE_GUIDE.md)

### 3. Paquet OpenSpec (Handoff Développeur)
- 📄 **Épopée de rattachement** : [`backlog/epics/epic_portfolio_governance_2026q4.md`](../epics/epic_portfolio_governance_2026q4.md)
- 📋 **État de cycle de vie à sceller** : `Projects/mLoop/memory/lifecycle_state.json`
- 📋 **État de cadre à vérifier** : `Projects/mLoop/memory/FRAMEWORK_STATE.md`
- 📋 **Rapport de synchronisation** : `Projects/mLoop/memory/jira_sync_report.md`
- 📋 **Journal de synchronisation** : `Projects/mLoop/memory/jira_sync_history.md`
- 📋 **Registre d'archives** : `Projects/mLoop/memory/supersession_ledger.json`
- 🎯 **Sous-suite de phase** : `tests/test_jira_sync_safe.py`, `tests/test_jira_md_cleaner.py`, `tests/test_sync_resilience.py`, `tests/test_in_review_lifecycle.py`, `tests/test_memory_supersession.py`

---

## Scénarios de test

```gherkin
# language: fr
Fonctionnalité: Clôture de la cinquième porte de gouvernance du framework mLoop sous feu vert humain

  # 1. NOMINAL (Happy Path & Persistance)
  Scénario: Inventaire de ciblage constitué à partir des clés de ticket réelles
    Étant donné les récits de l'épopée de gouvernance du portefeuille
    Quand la liste de ciblage est constituée
    Alors chaque récit inclus porte une clé de ticket non vide et non blanche
    Et chaque récit à clé vide figure parmi les exclusions motivées
    Et aucun récit n'est modifié pendant l'inventaire

  Scénario: Simulation de synchronisation puis approbation puis écriture ciblée
    Étant donné une liste de ciblage consignée et aucun feu vert d'écriture
    Quand la synchronisation s'exécute en mode simulation
    Alors aucun ticket distant n'est écrit
    Et le rapport de simulation est restitué intégralement
    Quand le décideur approuve explicitement le rapport
    Et que la synchronisation s'exécute en mode écriture sur la liste de ciblage uniquement
    Alors les tickets ciblés sont alignés côté distant
    Et les récits hors ciblage demeurent intacts

  Scénario: Archivage local des connaissances remplacées
    Étant donné des décisions du projet candidates à l'archivage
    Quand la commande d'archivage local s'exécute
    Alors le registre d'archives du projet est mis à jour
    Et le nombre d'éléments archivés est restitué
    Et aucun ticket distant n'est contacté

  Scénario: Sous-suite de phase verte puis poussée sous feu vert puis scellement de porte
    Étant donné la simulation, l'écriture et l'archivage complétés
    Quand la sous-suite de vérification de phase s'exécute
    Alors elle affiche zéro échec
    Et la suite complète est exécutée en best-effort avec rapport des échecs
    Quand le décideur donne un feu vert de poussée explicite et distinct
    Alors le dépôt est poussé vers la branche principale
    Et l'entrée de cinquième porte est écrite avec horodatage et approbateur

  # 2. EXCEPTIONS (Cas d'erreur & Rejets métier)
  Scénario: Bascule en écriture avant approbation du rapport refusée
    Étant donné un rapport de simulation non approuvé
    Quand une écriture de synchronisation est initiée
    Alors l'écriture est refusée
    Et aucun ticket distant n'est modifié

  Scénario: Balayage de l'intégralité du projet sans confirmation dédiée refusé
    Étant donné une demande de synchronisation sans liste de ciblage
    Quand la commande s'exécute sans confirmation de balayage total dédiée
    Alors l'exécution est refusée par la garde
    Et la séquence s'arrête avec consignation

  Scénario: Poussée de dépôt sans feu vert distinct refusée
    Étant donné une sous-suite verte mais aucun feu vert de poussée
    Quand une poussée est initiée
    Alors la poussée est refusée
    Et le dépôt local reste inchangé côté distant

  Scénario: Poussée alors qu'un échec subsiste en sous-suite refusée
    Étant donné au moins un échec dans la sous-suite de phase
    Quand une poussée est initiée sous feu vert
    Alors la poussée est bloquée
    Et l'échec est consigné comme facteur bloquant

  Scénario: Archivage utilisé comme substitut à la synchronisation de tickets refusé
    Étant donné une intention d'aligner des tickets distants
    Quand seule la commande d'archivage local est invoquée
    Alors aucun ticket distant n'est écrit
    Et l'inadéquation de la commande est signalée

  # 3. RÉSILIENCE (Réseau / Timeout / Mode dégradé)
  Scénario: Code de sortie non nul stoppe la séquence
    Étant donné une étape de la séquence de clôture terminée par un code de sortie non nul
    Quand la séquence tente de poursuivre
    Alors l'étape suivante n'est pas lancée
    Et l'anomalie est consignée dans le dossier de preuves
    Et aucune poussée ni aucun scellement n'a lieu

  Scénario: Liste de ciblage vide signalée sans exécution silencieuse
    Étant donné un ensemble de récits dont aucun ne porte de clé de ticket réelle
    Quand la liste de ciblage est constituée
    Alors la liste vide est signalée
    Et aucune simulation ni écriture n'est lancée comme si la liste était valide

  Scénario: Échec best-effort de la suite complète traité comme dette non bloquante
    Étant donné une sous-suite de phase verte et au moins un échec dans la suite complète hors périmètre
    Quand le rapport de clôture est produit
    Alors les échecs hors périmètre figurent comme dette nominative
    Et ils ne bloquent pas le scellement de porte
    Et ils ne sont pas déclarés inexistants

  Scénario: Interruption réseau pendant l'écriture sans état partiel déclaré à tort
    Étant donné une écriture de synchronisation en cours
    Quand le service distant devient indisponible
    Alors la commande s'arrête sur garde ou code de sortie non nul
    Et le rapport consigne l'état atteint
    Et aucune poussée ni aucun scellement n'est enclenché en sous-main

  # 4. UX / ACCESSIBILITÉ / ÉTAT VIDE
  Scénario: Rapport de simulation restitué intégralement au décideur
    Étant donné une simulation terminée sans violation de garde
    Quand le décideur prend connaissance du rapport
    Alors le détail complet de la simulation est disponible
    Et la décision d'approbation est tracée comme feu vert explicite

  Scénario: Aucune notification externe automatique à la clôture
    Étant donné la cinquième porte scellée et le dépôt poussé
    Quand l'état de cycle de vie est mis à jour
    Alors aucune diffusion n'est émise vers une partie prenante
    Et toute annonce reste une commande séparée sous feu vert dédié

  Scénario: État de cinquième porte traçable avec approbateur
    Étant donné le scellement de la cinquième porte
    Quand l'état de cycle de vie est consulté
    Alors l'entrée de porte affiche un horodatage et un approbateur
    Et les portes précédentes demeurent inchangées
```
