---
id: MLOOP-206-BE
jira_key: ''
epic_key: EPIC-20-PORTFOLIO-GOVERNANCE
type: Feature
title: Cartographie de parenté des initiatives OneTrust multi-codebase et RBC Avion
tags:
- portfolio
- governance
- onetrust
- rbc
- parentage
- metro
status: DONE
grill_me: DONE
layer: backend
invest_score: 6/6
macro_size: XS
origin: DIRECT_REQUIREMENT
source_ref: epic_portfolio_governance_2026q4.md
blocked_by: []
created_at: '2026-09-23'
---
# Cartographie de parenté des initiatives OneTrust multi-codebase et RBC Avion

---

## Description
**En tant qu'** Orchestrateur mLoop,
**je veux** cartographier la parenté des trois initiatives OneTrust (FOOD, COMMERCE, SANTÉ) et des deux récits RBC Avion (ST-100, ST-101) par une matrice macro de correspondance thématique et un verdict d'arbitrage fondé sur la matrice §4 de l'ADR-0342, sans déprécier ni fusionner aucun récit,
**afin d**'éliminer l'ambiguïté du vocabulaire « doublon » du portefeuille Metro, de tracer des liens de parenté traçables entre variantes légitimes par bounded context, et de corriger la prémisse fausse d'une « matrice ADR-0342 §3 de déduplication » qui n'existe pas.

---

## Contexte & Périmètre

### Contexte Métier
L'épopée `EPIC-20` qualifie de « dette structurelle » la présence de « OneTrust ×3 » et « RBC ×2 » dans les dépôts Metro, et le draft initial de cette story proposait d'appliquer une « matrice ADR-0342 §3 (fusion / canonical owner / dépréciation) » pour éliminer les récits redondants. Deux constats documentaires contredisent ce diagnostic : (1) l'ADR-0342 modulaire, lu intégralement, ne contient aucune §3 de déduplication — sa §3 porte sur les baux de concurrence `OWNS:` et sa §4 est une matrice d'arbitrage « Projet Distinct vs Sous-Module » ; (2) « OneTrust ×3 » désigne trois initiatives par codebase totalisant environ 45 récits (FOOD 20, COMMERCE 16, SANTÉ 9), pas trois récits strictement identiques. Les deux récits RBC (ST-100 FOOD, ST-101 COMMERCE) partagent l'`epic_key: MMA-4629` et la même feature métier (affichage des conversions Avion dans l'historique) mais ciblent des applications physiquement séparées (MAUI FOOD vs Pharma.App COMMERCE) avec des composants et logos distincts. La grille §4 de l'ADR-0342, appliquée à ces faits, conduit à un verdict de **coexistence avec parenté documentée**, non de fusion ni de dépréciation. Le présent récit exécute ce verdict : matrice macro OneTrust, lien croisé RBC, correction du vocabulaire du draft.

### In-Scope
- Production d'une **matrice macro de correspondance thématique** (8–10 thèmes : bannière, centre de préférences, SSO Base64, Firebase C0001/C0002, AppInsights, spike .NET 10, refonte UX, GCM v2, hors-ligne…) alignant les IDs FOOD ↔ COMMERCE ↔ SANTÉ par ligne, `—` si absent.
- Application explicite de la **matrice §4 ADR-0342** (Projet Distinct vs Sous-Module) aux deux récits RBC, consignée comme verdict d'arbitrage.
- Ajout d'un **lien croisé `related:`** dans le frontmatter de ST-100 et ST-101 (seule écriture hors dépôt mLoop), sous feu vert humain.
- Correction du titre, du périmètre et des critères du récit pour refléter le verdict (C+i+α+a) plutôt que la purge initiale.
- Consignation des décisions de cadrage (Q1=C, Q2=i/α/a, Q3=I/α/XS) dans le fact_dossier et l'EvidencePack.
- Validation par rubber-duck et contrôle de conformité aux 4 piliers.

### Out-of-Scope
- **Dépréciation, fusion ou mutation de statut** d'un quelconque récit OneTrust ou RBC (zéro Won't Fix, zéro retrait de tableau).
- Normalisation globale du naming modules (couvert par MLOOP-205-BE).
- Modification du code source des intégrations OneTrust ou RBC.
- Création de nouveaux récits de remplacement.
- Poussée Jira des liens de parenté (hors périmètre, local mLoop).
- Traitement d'autres doublons potentiels non listés dans l'épopée.

---

## Critères d'acceptation

### Opérations Métier & Logique Backend *(backend)*
#### 1. Matrice macro de correspondance thématique OneTrust
* **Entrée Métier** : Les trois dossiers d'initiatives OneTrust (FOOD 20, COMMERCE 16, SANTÉ 9), titres et frontmatter de chaque récit.
* **Règles d'admissibilité & Validation** : Chaque ligne de la matrice porte un thème métier, un ID FOOD, un ID COMMERCE, un ID SANTÉ (ou `—` si absent du dépôt) ; seuls des IDs réellement présents sur disque sont listés ; aucun récit n'est omis du inventaire même s'il n'a pas de contrepartie thématique.
* **Traitement & Algorithme Métier** : Balayage des titres et descriptifs des 45 récits, regroupement par thème de haut niveau (8–10 lignes), consignation dans le fact_dossier.
* **Résultat Métier & Mutations** : Une matrice macro complète figure au fact_dossier, adossée aux IDs réels ; les 45 récits sont inventoriés (20+16+9) sans qu'aucun ne soit modifié.
* **Cas de Rejet Métier** : Rejet d'un ID absent du disque ; rejet d'une fusion de lignes thème sans preuve de correspondance ; rejet de toute mutation de récit sous couvert de la matrice.

#### 2. Verdict d'arbitrage RBC fondé sur la grille §4 ADR-0342
* **Entrée Métier** : ST-100 (FOOD, `BACKLOG`, `MMA-4630`), ST-101 (COMMERCE, `OPEN`, `MMA-4631`), grille §4 de l'ADR-0342.
* **Règles d'admissibilité & Validation** : Le verdict est explicitement dérivé de la colonne « Projet mLoop Distinct » de la grille (documentation/schéma partagés mais apps et backlogs distincts) ; la conclusion est **coexistence + parenté**, jamais fusion ; aucun statut, aucun titre, aucun corps des deux récits n'est modifié.
* **Traitement & Algorithme Métier** : Lecture des deux frontmatters et des contextes applicatifs ; application ligne à ligne de la grille §4 ; consignation du verdict dans le fact_dossier.
* **Résultat Métier & Mutations** : Le verdict « parenté sans fusion, zéro dépréciation » est documenté avec justification §4 ; ST-100 et ST-101 restent intacts sauf ajout de `related:`.
* **Cas de Rejet Métier** : Rejet d'un verdict de fusion contredisant la séparation des apps ; rejet d'une mutation de statut RBC ; rejet d'un verdict sans citation de la grille §4.

#### 3. Lien croisé de parenté RBC (seule écriture hors mLoop)
* **Entrée Métier** : Frontmatters de ST-100 et ST-101, feu vert humain explicite.
* **Règles d'admissibilité & Validation** : Un champ `related: [ST-101]` est ajouté à ST-100 et `related: [ST-100]` à ST-101 ; aucune autre ligne du frontmatter (statut, epic, jira, invest) n'est touchée ; l'écriture n'a lieu qu'après validation humaine du package.
* **Traitement & Algorithme Métier** : Édition chirurgicale du frontmatter YAML, vérification de non-régression des autres champs, consignation de l'avant/après dans l'EvidencePack.
* **Résultat Métier & Mutations** : Les deux récits RBC se référencent mutuellement ; tous les autres champs sont bit à bit identiques.
* **Cas de Rejet Métier** : Rejet d'une édition sans feu vert ; rejet d'une modification de `status` ou `epic_key` ; rejet d'un lien unidirectionnel.

#### 4. Correction du diagnostic « doublon » et rejet de la prémisse §3
* **Entrée Métier** : Texte du draft initial, ADR-0342 lu intégralement, comptage réel des récits.
* **Règles d'admissibilité & Validation** : Le récit haute fidélité ne contient aucune référence active à une « matrice ADR-0342 §3 de déduplication » ; le titre et le périmètre reflètent la cartographie de parenté ; la prémisse fausse est explicitement consignée comme rejetée.
* **Traitement & Algorithme Métier** : Réécriture complète du récit (titre métier pur, description, in/out-of-scope, CA) ; vérification qu'aucun « §3 déduplication » ni « canonical owner » ne subsiste comme stratégie active.
* **Résultat Métier & Mutations** : Le récit est cohérent avec le verdict C ; la prémisse rejetée est tracée au fact_dossier.
* **Cas de Rejet Métier** : Rejet d'un récit conservant la stratégie de purge ; rejet d'un titre métier contenant un identifiant technique.

#### Matrice des Contrats API
N/A — Récit de gouvernance documentaire 100 % local : aucune route réseau n'est exposée, consommée ou modifiée.
- **OQ-206 (Exemption Zéro Fausse Route)** : Exemption complète de la Matrice des Contrats API — lecture de frontmatters, production d'une matrice de correspondance Markdown et ajout de liens croisés YAML, sans interface réseau `[API de soumission à définir]` ; toute poussée Jira des liens reste hors périmètre et deviendrait une question ouverte nominative, jamais simulée.
- **Admission of Limits** : Les avertissements de résilience d'interface hors domaine s'appliquent à un composant sans interface ; la robustesse est couverte par le troisième pilier (zéro mutation de statut, feu vert requis pour les liens, prémisse fausse tracée).

---

## Règles d'affaires

- **Zéro dépréciation, zéro fusion** : Aucun récit OneTrust ou RBC n'est marqué BACKLOG, CANCELLED ou Won't Fix sous couvert du présent récit.
- **Variantes légitimes par bounded context** : Les trois initiatives OneTrust et les deux récits RBC sont des variantes par codebase (AGENTS.md le déclare explicitement), pas des doublons stricts à purger.
- **Prémisse §3 rejetée** : Toute référence à une « matrice ADR-0342 §3 de déduplication » est considérée comme fausse et corrigée ; la seule grille applicable est la §4 (Projet Distinct vs Sous-Module).
- **Matrice macro uniquement** : La correspondance OneTrust s'arrête à 8–10 thèmes de haut niveau ; l'alignement exhaustif 1:1 des 45 récits est hors périmètre.
- **Écritures limitées** : Seuls les deux frontmatters RBC (`related:`) et les artefacts mLoop (récit, fact_dossier, evidence) sont modifiés ; zéro écriture dans les dépôts OneTrust.
- **Feu vert humain** : Les liens croisés RBC ne sont appliqués qu'après validation explicite du package par l'humain.
- **Jira hors périmètre** : Aucune synchronisation de parenté vers Jira.
- **Dettes nominatives** : Alignement exhaustif 1:1, normalisation des titres SANTE legacy, poussée Jira sont reportés, jamais absorbés en sous-main.

---

## Références

### 1. Preuves Amont & Traçabilité Factuelle
- 📂 **Dossier de Preuves Factuelles** : [`memory/evidence/MLOOP-206-BE_fact_dossier.md`](../../memory/evidence/MLOOP-206-BE_fact_dossier.md)
- 🏛️ **Décisions de cadrage** : Q1 = C hybride ciblé (OneTrust parenté sans fusion, RBC audit strict, prémisse §3 corrigée vers §4) · Q2a = i parenté RBC sans fusion · Q2b = α matrice macro 8–10 thèmes · Q2c = a aucun Won't Fix ni retrait · Q3a = I titre « Cartographie de parenté » · Q3b = α liens croisés inclus au feu vert · Q3c = XS macro confirmée (Grill-Me 2026-09-24)

### 2. Spécifications & Modèles de Données SSOT
- 📜 **Dossier de preuves** : [DOSSIER_DE_PREUVES_PROTOCOL.md](../../../standards/protocols/DOSSIER_DE_PREUVES_PROTOCOL.md)
- 📜 **Grill macro / micro** : [ADR-0320](../../../standards/adr-system/0320-grill-me-frontier-design-tree-alignment.md)
- 📜 **Gabarit de récit** : [story_template.md](../../../standards/blueprints/story_template.md)
- 📜 **ADR modulaire** : [0342-modular-project-architecture-and-subdomain-isolation.md](../../../standards/adr-system/0342-modular-project-architecture-and-subdomain-isolation.md)

### 3. Paquet OpenSpec (Handoff Développeur)
- 📄 **Épopée de rattachement** : [`backlog/epics/epic_portfolio_governance_2026q4.md`](../epics/epic_portfolio_governance_2026q4.md)
- 📂 **OneTrust FOOD** : `Projects/Metro_FOOD/backlog/stories/OneTrust_FOOD/` (20 récits)
- 📂 **OneTrust COMMERCE** : `Projects/Metro_COMMERCE/backlog/stories/OneTrust_COMMERCE/` (16 récits)
- 📂 **OneTrust SANTÉ** : `Projects/Metro_SANTE/backlog/stories/OneTrust_SANTE/` (9 récits)
- 📄 **RBC ST-100** : `Projects/Metro_FOOD/backlog/stories/RBC_Avion/ST-100-historique-transactions-avion.md`
- 📄 **RBC ST-101** : `Projects/Metro_COMMERCE/backlog/stories/RBC_Avion/ST-101-historique-transactions-avion-commerce.md`

---

## Scénarios de test

```gherkin
# language: fr
Fonctionnalité: Cartographie de parenté des initiatives OneTrust multi-codebase et RBC Avion

  # 1. NOMINAL (Happy Path & Persistance)
  Scénario: Matrice macro de correspondance thématique complète
    Étant donné les trois dossiers OneTrust (FOOD, COMMERCE, SANTÉ) et leurs 45 récits
    Quand la matrice macro de correspondance est constituée
    Alors chaque ligne porte un thème et les IDs correspondants des trois dépôts ou un tiret
    Et les 45 récits sont inventoriés sans qu'aucun ne soit modifié
    Et aucun ID absent du disque n'apparaît dans la matrice

  Scénario: Verdict RBC fondé sur la grille §4 ADR-0342
    Étant donné ST-100 (FOOD) et ST-101 (COMMERCE) partageant l'épique MMA-4629
    Quand la grille Projet Distinct vs Sous-Module est appliquée
    Alors le verdict est coexistence avec parenté documentée
    Et aucun des deux récits n'est fusionné ni déprécié
    Et les statuts BACKLOG et OPEN demeurent inchangés

  Scénario: Lien croisé de parenté RBC sous feu vert
    Étant donné ST-100 et ST-101 et le feu vert humain
    Quand le lien related est ajouté aux deux frontmatters
    Alors ST-100 référence ST-101 et ST-101 référence ST-100
    Et les autres champs des deux frontmatters sont bit à bit identiques

  Scénario: Prémisse §3 rejetée et diagnostic corrigé
    Étant donné le draft initial invoquant une matrice ADR-0342 §3 de déduplication
    Quand le récit haute fidélité est rédigé
    Alors aucune stratégie active de purge ou de canonical owner ne subsiste
    Et la prémisse fausse est explicitement consignée comme rejetée
    Et le titre métier reflète la cartographie de parenté

  # 2. EXCEPTIONS (Cas d'erreur & Rejets métier)
  Scénario: Dépréciation d'un récit sous couvert de la cartographie refusée
    Étant donné un récit OneTrust ou RBC ciblé pour marquage BACKLOG ou CANCELLED
    Quand l'opération tente de muter le statut
    Alors l'opération est refusée
    Et l'intention est tracée dans le paquet de preuve

  Scénario: Fusion de ST-100 et ST-101 refusée
    Étant donné les deux récits RBC sur des apps distinctes
    Quand une opération tente de fusionner ou supprimer l'un d'eux
    Alors l'opération est interrompue
    Et les deux récits demeurent avec leurs statuts d'origine

  Scénario: Édition des liens croisés sans feu vert refusée
    Étant donné les frontmatters RBC non encore validés par l'humain
    Quand une écriture tente d'ajouter related sans validation
    Alors l'écriture est refusée
    Et les frontmatters restent inchangés jusqu'au feu vert

  Scénario: ID OneTrust hors disque dans la matrice refusé
    Étant donné une ligne de matrice citant un ID absent des dépôts
    Quand la matrice tente d'être validée
    Alors la ligne est rejetée
    Et aucun ID inventé n'est consigné

  # 3. RÉSILIENCE (Réseau / Timeout / Mode dégradé)
  Scénario: Récit SANTE legacy sans title YAML signalé
    Étant donné un récit SANTÉ sans champ title en frontmatter
    Quand la matrice tente d'extraire le titre
    Alors le titre est repris du H1 ou le cas est signalé
    Et aucun titre n'est inventé par inférence

  Scénario: Dossier OneTrust absent signalé sans reconstruction
    Étant donné un dossier d'initiative OneTrust inaccessible
    Quand l'inventaire tente de le lire
    Alors l'anomalie est consignée dans le paquet de preuve
    Et la matrice n'est pas reconstruite à partir de supposition

  Scénario: Échec d'édition frontmatter stoppe la séquence
    Étant donné un échec d'écriture YAML sur ST-100
    Quand la séquence poursuit vers ST-101
    Alors l'échec est consigné
    Et la seconde édition n'est pas lancée avant résolution

  # 4. UX / ACCESSIBILITÉ / ÉTAT VIDE
  Scénario: Lecture de la matrice par le décideur
    Étant donné la matrice macro et le verdict RBC au fact_dossier
    Quand le décideur consulte le paquet
    Alors chaque thème montre les IDs des trois codebases
    Et le verdict §4 est lisible avec sa justification
    Et aucune action de purge n'est proposée

  Scénario: Inventaire exhaustif des 45 récits OneTrust
    Étant donné les 20 récits FOOD, 16 COMMERCE et 9 SANTÉ
    Quand l'inventaire est consigné
    Alors le total correspond à la réalité disque
    Et les récits sans contrepartie thématique restent tracés
```
