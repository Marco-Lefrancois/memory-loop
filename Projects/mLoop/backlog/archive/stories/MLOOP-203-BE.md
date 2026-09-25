---
id: MLOOP-203-BE
jira_key: ''
epic_key: EPIC-20-PORTFOLIO-GOVERNANCE
type: Feature
title: Triage des récits Shopify en attente de revue PO vers les statuts de gouvernance
tags:
- triage
- shopify
- backlog
- dor
- portfolio
status: DONE
grill_me: DONE
layer: backend
invest_score: 6/6
macro_size: M
origin: DIRECT_REQUIREMENT
source_ref: epic_portfolio_governance_2026q4.md
blocked_by: []
created_at: '2026-09-23'
ttl_cycles: 3
---
# Triage des récits Shopify en attente de revue PO vers les statuts de gouvernance

---

## Description
**En tant qu'** Orchestrateur mLoop,
**je veux** trier les quarante-et-un récits Shopify encore marqués en cours d'analyse en les répartissant entre prêts pour la revue du responsable produit, bloqués par une question ouverte critique, ou laissés en attente d'un contrôle de prontitude manquant,
**afin d'** éliminer la file sans suite du backlog, de rendre visible le vrai goulot (les questions critiques) et de préparer une revue de poche crédible sans réécrire le corps des récits.

---

## Contexte & Périmètre

### Contexte Métier
Le tableau de bord Shopify affiche l'intégralité du backlog produit en attente d'analyse, alors que chaque récit dispose déjà d'un dossier de preuves, d'un paquet de preuve et le plus souvent d'une revue contradictoire. Le responsable produit a besoin d'une carte clare : quels récits peuvent entrer en revue de poche maintenant, lesquels attendent une décision critique explicitement nommée, et lequel reste en attente d'un contrôle manquant. Sans ce tri, le projet laisse croire à zéro avancement réel et noyau le signal des seules questions qui bloquent vraiment.

### In-Scope
- Inventaire des quarante-et-un récits du tableau de bord Shopify et appariement à leur dossier de preuves, paquet de preuve et revue Sentinel existante.
- Application des seuls critères de sortie actés : score d'investissement complet, revue Sentinel présente et absence de question ouverte critique pour la cible de revue de poche.
- Écriture groupée des statuts de gouvernance dans le frontmatter de chaque récit et dans le tableau de bord de sprint du projet Shopify, sous feu vert sur le présent récit.
- Affectation du statut de bloqué avec référence à la question ouverte critique pour tout récit concerné.
- Conservation en attente d'analyse, avec justification nominative, du récit dont la revue Sentinel manque.
- Production du paquet de preuve du présent récit avec justification par récit et matrice d'éligibilité.
- Relance unique du contrôle de prontitude de la revue Sentinel pour le récit dont le rapport manque, avant toute transition de ce récit.

### Out-of-Scope
- Réécriture du corps fonctionnel, des critères d'acceptation ou des scénarios des quarante-et-un récits.
- Promotion vers la mise au travail : interdite sans entrevue contradictoire unitaire et définition de prontitude complète.
- Introduction de statuts absents de la matrice du projet cible, ni régression vers le fond du backlog pour un récit déjà cadré.
- Relance en masse des revues Sentinel ou des contrôles d'investissement déjà scellés, hors exception nominative du rapport manquant.
- Communication formelle externe vers le marchand ou le porteur de vision : la levée des questions se fait par le registre central et la revue de poche.
- Désignation de la boutique pilote ou arbitrage des questions ouvertes critiques elles-mêmes.
- Initialisation d'un projet distinct ou scission du dépôt Shopify.

---

## Critères d'acceptation

### Opérations Métier & Logique Backend *(backend)*
#### 1. Inventaire et appariement du socle des quarante-et-un
* **Entrée Métier** : Tableau de bord de sprint Shopify, répertoire des récits, dossiers de preuves, paquets de preuve et revues Sentinel.
* **Règles d'admissibilité & Validation** : Chaque récit du tableau est apparié de façon déterministe à son dossier, son paquet et sa revue ; aucun socle n'est présumé complet sans inspection de présence.
* **Traitement & Algorithme Métier** : Lecture croisée tableau / fichiers, marquage complet, partiel ou absent, détection des écarts de nommage entre identifiant de tableau et clé de suivi.
* **Résultat Métier & Mutations** : Matrice de quarante-et-un lignes tracée dans le paquet de preuve du présent récit.
* **Cas de Rejet Métier** : Rejet de tout récit du tableau sans fichier correspondant ; il est signalé socle inconnu et ne reçoit aucune transition automatique.

#### 2. Classification selon les seuls critères actés
* **Entrée Métier** : Matrice d'inventaire, registre central des questions ouvertes, scores d'investissement des frontmatter, présence des revues Sentinel.
* **Règles d'admissibilité & Validation** : Seule une question critique non levée pose veto ; les questions encore ouvertes sans marquage critique sont tolérées et tracées sans bloquer la revue de poche ; un score d'investissement incomplet ou une revue Sentinel absente exclut la cible de revue de poche.
* **Traitement & Algorithme Métier** : Croisement déterministe récit → questions critiques → score → revue, production des trois jeux : réviseables, bloqués par question critique, en attente de contrôle.
* **Résultat Métier & Mutations** : Trois listes disjointes et exhaustives couvrant les quarante-et-un, chacune justifiée phrase par récit.
* **Cas de Rejet Métier** : Rejet de toute classification invoquant un statut absent de la matrice du projet cible ou régressant un récit déjà cadré vers le fond du backlog.

#### 3. Écriture groupée des statuts de gouvernance
* **Entrée Métier** : Jeux classés, feu vert enregistré sur le présent récit, frontmatter des récits et tableau de bord Shopify.
* **Règles d'admissibilité & Validation** : L'écriture groupée n'est exécutée qu'après feu vert nommé sur le présent récit ; seuls les statuts valides de la matrice cible sont posés ; le corps des récits reste inchangé.
* **Traitement & Algorithme Métier** : Mise à jour frontmatter puis tableau de bord en une passe, journal des cibles avant et après, un seul contrôle de synchronisation final.
* **Résultat Métier & Mutations** : Chaque récit éligible passe en revue de poche ; chaque récit à question critique passe en attente d'arbitrage avec sa question ; aucun résidu non justifié ne subsiste en attente d'analyse.
* **Cas de Rejet Métier** : Rejet de l'écriture groupée sans feu vert ; rejet de toute transition d'un récit non conforme aux critères actés.

#### 4. Exception nominative du contrôle manquant
* **Entrée Métier** : Récit identifié sans revue Sentinel et sans question critique bloquante.
* **Règles d'admissibilité & Validation** : Ce récit ne reçoit aucune transition tant que la revue n'est pas produite ; la relance est unique et traçée.
* **Traitement & Algorithme Métier** : Exécution de la revue, recontrôle, bascule ultérieure selon les mêmes critères que le reste de la population.
* **Résultat Métier & Mutations** : Soit la revue manquante est scellée et le récit rejoint la cible de revue de poche, soit il reste justifié en attente d'analyse dans le paquet de preuve.
* **Cas de Rejet Métier** : Rejet de toute transition de ce récit sans revue Sentinel présente ; rejet d'un résidu en attente d'analyse sans justification nominative.

#### 5. Périmètre hors tri (exclusions)
* **Entrée Métier** : Questions critiques du registre, désignation de la boutique pilote, communication externe.
* **Règles d'admissibilité & Validation** : Aucune arbitrage de question n'est tranché dans le présent récit ; aucune relance client n'est émise ici ; la levée ultérieure suit le registre central.
* **Traitement & Algorithme Métier** : Exclusion déterministe, trace dans le paquet de preuve.
* **Résultat Métier & Mutations** : Liste des questions critiques ouvertes consignée pour décision du responsable produit.
* **Cas de Rejet Métier** : Rejet de toute tentative de trancher une question critique ou d'envoyer un message externe depuis ce récit.

#### Matrice des Contrats API
N/A — Récit de gouvernance de backlog documentaire 100 % local : aucune route REST/CTA n'est exposée, consommée ou modifiée.
- **OQ-203 (Exemption Zéro Fausse Route)** : Exemption complète de la Matrice des Contrats API — inventaire de fichiers markdown et paquets de preuve locaux, sans interface HTTP `[API de soumission à définir]` ; toute exposition future d'API du produit Shopify est à définir dans un récit dédié du dépôt cible (à définir dans le registre du projet concerné).
- **Admission of Limits** : Les avertissements de résilience d'interface (délais réseau, saisie) sont hors domaine pour un composant sans interface ; la robustesse de la séquence de tri est couverte par le troisième pilier (échec d'écriture sans publication partielle, résidu justifié, refus sans feu vert).

---

## Règles d'affaires

- **Matrice cible exclusive** : Seuls les statuts réellement présents dans la gouvernance du projet Shopify sont posés ; tout libellé absent de cette matrice est proscrit.
- **Veto unique à la question critique** : Une question encore ouverte sans marquage critique ne bloque pas la revue de poche ; elle reste tracée en transparence.
- **Héritage de prontitude** : Un score d'investissement complet et une revue Sentinel déjà scellées sont réutilisés ; aucun contrôle en masse n'est relancé.
- **Feu vert avant écriture groupée** : Toute mutation de statut en lot exige un feu vert nommé et journalisé sur le présent récit.
- **Corps intouché** : Le triage ne modifie ni la description, ni les critères, ni les scénarios des récits cibles.
- **Résidu justifié uniquement** : Toute attente d'analyse conservée porte une justification nominative ; un résidu non justifié est un défaut de livraison.
- **Levée interne par registre** : La sortie du bloqué passe par la décision enregistrée au registre central des questions, jamais par une relance externe depuis ce récit.
- **Exception de contrôle nominative** : Le récit privé de revue Sentinel est le seul maintenu en attente jusqu'à relance unique de ce contrôle.
- **Gestion des données invalides** : Un fichier de récit illisible empêche sa transition et le déclenche un signal dans le paquet de preuve ; un écart d'appariement est signalé, jamais résolu par devinette.

---

## Références

### 1. Preuves Amont & Traçabilité Factuelle
- 📂 **Dossier de Preuves Factuelles** : [`memory/evidence/MLOOP-203-BE_fact_dossier.md`](../../memory/evidence/MLOOP-203-BE_fact_dossier.md)
- 🏛️ **Décisions de cadrage** : Q1 statuts réels du projet cible · Q2 levée interne par registre · Q3 héritage du contrôle de prontitude existant · Q4 écriture groupée sous feu vert · Q5 veto à la question critique seule et résidu justifié (Grill-Me 2026-09-23)

### 2. Spécifications & Modèles de Données SSOT
- 📜 **Dossier de preuves** : [DOSSIER_DE_PREUVES_PROTOCOL.md](../../../standards/protocols/DOSSIER_DE_PREUVES_PROTOCOL.md)
- 📜 **Grill macro / micro** : [ADR-0320](../../../standards/adr-system/0320-grill-me-frontier-design-tree-alignment.md)
- 📜 **Gabarit de récit** : [story_template.md](../../../standards/blueprints/story_template.md)

### 3. Paquet OpenSpec (Handoff Développeur)
- 📄 **Épopée de rattachement** : [`backlog/epics/epic_portfolio_governance_2026q4.md`](../epics/epic_portfolio_governance_2026q4.md)
- 📋 **Tableau de bord cible** : `Projects/Shopify_AI_Item_Creator/backlog/sprint_backlog.md`
- 📋 **Registre des questions** : `Projects/Shopify_AI_Item_Creator/docs/04-transverse/questions_ouvertes.md`

---

## Scénarios de test

```gherkin
# language: fr
Fonctionnalité: Triage des récits Shopify en attente de revue PO vers les statuts de gouvernance

  # 1. NOMINAL (Happy Path & Persistance)
  Scénario: Carte complète des récits vers la revue de poche
    Étant donné le tableau de bord Shopify et le registre des questions du projet
    Et que chaque récit est apparié à son dossier, son paquet et sa revue Sentinel
    Quand l'orchestrateur applique les seuls critères actés
    Alors chaque récit éligible passe en revue de poche
    Et chaque récit à question critique passe en attente d'arbitrage avec sa question
    Et un récit sans revue Sentinel reste en attente avec une justification nominative
    Et les cent quarante-et-un résultats sont tracés dans le paquet de preuve

  Scénario: Écriture groupée après feu vert nommé
    Étant donné les trois jeux classés et un feu vert journalisé sur le triage
    Quand l'écriture groupée met à jour les frontmatter et le tableau de bord
    Alors les statuts posés appartiennent tous à la matrice du projet cible
    Et le corps des récits est inchangé
    Et un unique contrôle de synchronisation final est exécuté

  # 2. EXCEPTIONS (Cas d'erreur & Rejets métier)
  Scénario: Question ouverte non critique sans veto
    Étant donné un récit éligible portant une question encore ouverte sans marquage critique
    Quand la classification est calculée
    Alors le récit rejoint la cible de revue de poche
    Et la question restante est tracée en transparence sans bloquer

  Scénario: Statut hors matrice du projet cible refusé
    Étant donné une demande de transition vers un libellé absent de la gouvernance Shopify
    Quand l'écriture groupée est tentée
    Alors la transition est refusée
    Et aucune modification n'est persistée pour ce récit

  Scénario: Écriture groupée sans feu vert
    Étant donné les jeux classés mais aucun feu vert journalisé
    Quand l'écriture groupée démarre
    Alors l'opération est interrompue
    Et aucun statut n'est posé

  # 3. RÉSILIENCE (Réseau / Timeout / Mode dégradé)
  Scénario: Échec d'écriture sans publication partielle
    Étant donné une mise à jour de statut en cours sur un récit cible
    Quand l'accès au fichier échoue ou devient illisible
    Alors le récit conserve son statut d'origine
    Et l'échec est signalé dans le paquet de preuve
    Et les autres transitions déjà validées restent cohérentes

  Scénario: Contrôle manquant maintenu sans transition forcée
    Étant donné le récit privé de revue Sentinel
    Quand la séquence de tri se clôture
    Alors il ne reçoit aucune transition de revue de poche
    Et sa justification nominative figure dans le paquet de preuve

  Scénario: Résidu en attente non justifié rejeté
    Étant donné un récit laissé en attente d'analyse après le tri
    Quand le bilan est produit
    Alors toute attente résiduelle porte une justification nominative
    Et un résidu sans justification est signalé comme défaut de livraison

  # 4. UX / ACCESSIBILITÉ / ÉTAT VIDE
  Scénario: Bilan de triage pour la revue de poche
    Étant donné la clôture de l'écriture groupée et du contrôle de synchronisation
    Quand le bilan est présenté au responsable produit
    Alors chaque ligne indique le récit, la cible de statut et le motif
    Et la liste des questions critiques ouvertes est nommée pour arbitrage
    Et aucun récit n'apparaît deux fois dans deux cibles différentes

  Scénario: Projet sans feu vert
    Étant donné le tableau de bord après tentative de triage sans feu vert
    Quand le bilan est consulté
    Alors les statuts d'origine sont conservés
    Et l'absence de feu vert est documentée dans le paquet de preuve
```
