---
id: MLOOP-201-BE
jira_key: ''
epic_key: EPIC-20-PORTFOLIO-GOVERNANCE
type: Feature
title: Compléter les dossiers de preuves Gate C9 des récits prêts au développement de Metro_COMMERCE
tags:
- evidence
- gate-c9
- onetrust
- portfolio
status: DONE
grill_me: DONE
layer: backend
invest_score: 6/6
macro_size: M
origin: DIRECT_REQUIREMENT
source_ref: epic_portfolio_governance_2026q4.md
blocked_by:
- MLOOP-200-BE
created_at: '2026-09-23'
ttl_cycles: 3
---
# Compléter les dossiers de preuves Gate C9 des récits prêts au développement de Metro_COMMERCE

---

## Description
**En tant qu'** Orchestrateur mLoop,
**je veux** que chaque récit Metro_COMMERCE déjà prêt au développement dispose d'un dossier de preuves documentaires Gate C9 complet, sourcé et certifié,
**afin d'**éliminer le risque de porte béante qui invaliderait le handoff vers les agents aval et de garantir un ancrage épistémique unique avant toute exécution.

---

## Contexte & Périmètre

### Contexte Métier
Le portefeuille Metro_COMMERCE compte treize récits déjà positionnés comme prêts au développement dans le tableau de bord de sprint, sans dossier de preuves documentaires associé sous la mémoire d'evidence. La porte de gouvernance Gate C9 repose sur ces dossiers : sans eux, le handoff aval consomme des spécifications non ancrées dans les sources réelles du sous-domaine OneTrust, avec un risque d'invention sourcée non détectable en revue de code.

### In-Scope
- Inventaire systématique des treize récits prêts au développement de Metro_COMMERCE sans dossier de preuves correspondant sous `memory/evidence/`.
- Génération d'un fichier de dossier de preuves nommé d'après la clé de suivi de chaque récit, conforme au standard Passage-Level Grounding, sous `Projects/Metro_COMMERCE/memory/evidence/`.
- Ancrage hybride des extraits : au moins deux extraits issus des spécifications ingérées du sous-domaine OneTrust et au moins un extrait issu de l'architecture ou des règles d'affaires OneTrust, par dossier.
- Mise à jour du paquet d'evidence existant de chaque récit avec le champ référençant le dossier généré, sans renommage des paquets historiques.
- Traitement conditionnel des maquettes vectorielles du parcours de consentement : lecture directe si le fichier expose du texte lisible, pont de reconnaissance optique obligatoire sinon, question ouverte et limite admise en cas d'échec de l'extraction.
- Application du veto de revue : échantillon de trois dossiers (profil infrastructure, profil interface, profil maquette) soumis à revue humaine, plus tout dossier jugé trop mince ou non certifié.
- Validation post-backfill de la porte Gate C9 sur les treize récits.

### Out-of-Scope
- Modification du corps des treize récits prêts au développement (leur statut d'exécution ne change pas par ce récit).
- Création de nouveaux récits pour Metro_COMMERCE.
- Backfill de dossiers sur d'autres projets du portefeuille (alimentation alimentaire, santé, boutique en ligne, etc.).
- Promotion de récits vers un état de livraison ou de revue en cours.
- Levée de la porte de définition de prontitude du projet Metro_COMMERCE (l'écart entre la porte projet et le statut des récits est admis et hors périmètre).
- Renommage des paquets d'evidence historiques existants.
- Revision humaine des treize dossiers un par un (seul l'échantillon et les cas déclenchés par le veto sont revus).

---

## Critères d'acceptation

### Opérations Métier & Logique Backend *(backend)*
#### 1. Inventaire des récits éligibles
* **Entrée Métier** : Tableau de bord de sprint du projet cible et répertoire des paquets d'evidence.
* **Règles d'admissibilité & Validation** : Seuls les récits dont le statut d'exécution est « prêt au développement » et qui n'ont aucun dossier de preuves associé sont éligibles ; les récits archivés, remplacés ou encore ouverts sont exclus.
* **Traitement & Algorithme Métier** : Recoupement déterministe entre le tableau de bord, les en-têtes de récits et le répertoire d'evidence ; chaque couple récit / dossier manquant est listé une seule fois.
* **Résultat Métier & Mutations** : Liste d'inventaire figée des treize cibles, tracée dans les preuves du récit.
* **Cas de Rejet Métier** : Rejet silencieux d'un récit qui n'est plus prêt au développement au moment de l'inventaire ; l'écart est consigné sans création de dossier.

#### 2. Génération des dossiers de preuves ancrés
* **Entrée Métier** : Récit cible, corpus documentaire du sous-domaine OneTrust et règles du dossier de preuves.
* **Règles d'admissibilité & Validation** : Chaque dossier doit porter au moins cinq extraits verbatim doublement ancrés, dont au moins deux issus des spécifications ingérées et au moins un issu de l'architecture ou des règles d'affaires ; la matrice de résolution de conflits et la limite admise sont présentes.
* **Traitement & Algorithme Métier** : Recherche factuelle ciblée, extraction mot-à-mot avec numéros de ligne, arbitrage des conflits selon la hiérarchie de vérité, écriture du fichier nommé d'après la clé de suivi.
* **Résultat Métier & Mutations** : Un fichier de dossier par récit cible sous la mémoire d'evidence du projet, sans doublon.
* **Cas de Rejet Métier** : Rejet d'un dossier dont le socle d'extraits est insuffisant ou non ancré ; le récit est alors signalé pour revue humaine obligatoire.

#### 3. Liaison des paquets d'evidence
* **Entrée Métier** : Paquet d'evidence existant du récit et chemin du dossier généré.
* **Règles d'admissibilité & Validation** : Le champ de référence vers le dossier est renseigné ; aucun paquet n'est renommé ni supprimé ; les doublons de convention historique coexistent sans écrasement.
* **Traitement & Algorithme Métier** : Mise à jour ciblée du champ de liaison, persistance JSON, conservation des autres sections intactes.
* **Résultat Métier & Mutations** : Chaque paquet cible référence son dossier unique ; le bilan avant/après est tracé.
* **Cas de Rejet Métier** : Rejet si le paquet est illisible ou absent ; création du champ uniquement dans un paquet nouvellement initialisé, avec trace d'initialisation.

#### 4. Extraction conditionnelle des libellés de maquette
* **Entrée Métier** : Fichiers de maquette vectorielle du parcours de consentement et récits d'interface associés.
* **Règles d'admissibilité & Validation** : Si le fichier expose du texte lisible, lecture directe ; sinon, extraction optique obligatoire ; toute échec d'extraction ouvre une question ouverte et une limite admise, jamais un libellé inventé.
* **Traitement & Algorithme Métier** : Inspection du balisage, bascule déterministe vers la lecture directe ou l'extraction optique, capture des libellés réels uniquement.
* **Résultat Métier & Mutations** : Dossiers des récits d'interface contenant les libellés réels ou la question ouverte correspondante.
* **Cas de Rejet Métier** : Rejet de tout libellé non observé dans le fichier ou dans la sortie d'extraction.

#### 5. Veto de revue et validation de porte
* **Entrée Métier** : Ensemble des dossiers générés, seuil de veto et jeu d'échantillon défini.
* **Règles d'admissibilité & Validation** : Trois dossiers d'échantillon (infrastructure, interface, maquette) sont revus par un humain ; tout dossier sous le seuil d'extraits, sans certificat de contrôle ou avec matrice de conflits vide est revu en sus ; la porte ne se lève qu'à révision de l'échantillon et des cas veto, et à contrôle vert sur les treize.
* **Traitement & Algorithme Métier** : Calcul du veto, file de revue, collecte des verdicts, exécution du contrôle de porte sur l'ensemble.
* **Résultat Métier & Mutations** : Verdict de porte Gate C9 sur les treize récits, tracé dans les preuves.
* **Cas de Rejet Métier** : Rejet de la porte si un dossier de l'échantillon ou un cas veto échoue à la revue ; correction puis recontrôle, sans levée partielle.

#### Matrice des Contrats API
N/A — Récit de gouvernance documentaire 100 % local : aucune route REST/CTA n'est exposée, consommée ou modifiée.
- **OQ-201 (Exemption Zéro Fausse Route)** : Exemption complète de la Matrice des Contrats API — production de fichiers markdown et champs JSON locaux, sans interface HTTP `[API de soumission à définir]` ; toute future exposition d'API est à confirmer dans un récit dédié avec sa propre matrice.
- **Admission of Limits** : Les avertissements génériques de revue (anti-rebond, expiration de session, validation de saisie) sont hors domaine pour ce composant sans interface ; la résilience du lot est couverte par le Pilier 2 (échec partiel sans cascade, dossier insuffisant, extraction de maquette en échec).

---

## Règles d'affaires

- **Hybridation des identifiants** : Le dossier est nommé d'après la clé de suivi du récit ; le paquet d'evidence historique conserve son identifiant d'origine et référence le dossier par un champ dédié, sans migration de noms.
- **Ancrage hybride multi-couche** : Aucun dossier n'est validé sans ancrage croisé spécifications ingérées et couche architecture ou règles d'affaires du sous-domaine.
- **Veto sur dossier mince** : Sous le seuil d'extraits, sans certificat de contrôle ou avec matrice de conflits vide, le dossier passe en revue humaine obligatoire quelle que soit la composition de l'échantillon.
- **Zéro libellé inventé de maquette** : Un libellé d'interface n'entre dans un dossier que s'il est observé dans le fichier vectoriel ou dans la sortie d'extraction ; à défaut, question ouverte et limite admise.
- **Échec partiel sans cascade** : L'échec de production ou de revue d'un dossier isole le récit fautif sans bloquer la production des autres ni la constitution du bilan de lot.
- **Gestion des données invalides** : Un paquet d'evidence illisible est réinitialisé à partir des sections récupérables, avec trace explicite du remplacement ; un dossier corrompu est régénéré à partir des sources, jamais édité à la main pour masquer la corruption.

---

## Références

### 1. Preuves Amont & Traçabilité Factuelle
- 📂 **Dossier de Preuves Factuelles** : [`memory/evidence/MLOOP-201-BE_fact_dossier.md`](../../memory/evidence/MLOOP-201-BE_fact_dossier.md)
- 🏛️ **Décisions de cadrage** : Q1 hybridation identifiants · Q2 ancrage hybride multi-couche · Q3 veto de revue échantillonnée · Q4 extraction optique conditionnelle des maquettes (Grill-Me 2026-09-23)

### 2. Spécifications & Modèles de Données SSOT
- 📜 **Protocole des dossiers de preuves** : [DOSSIER_DE_PREUVES_PROTOCOL.md](../../../standards/protocols/DOSSIER_DE_PREUVES_PROTOCOL.md)
- 📜 **Architecture modulaire** : [ADR-0342](../../../standards/adr-system/0342-modular-project-architecture-and-subdomain-isolation.md)
- 📜 **Fact-search et revue sémantique** : [ADR-0326](../../../standards/adr-system/0326-fact-search-and-substantive-content-review.md)

### 3. Paquet OpenSpec (Handoff Développeur)
- 📄 **Épopée de rattachement** : [`backlog/epics/epic_portfolio_governance_2026q4.md`](../epics/epic_portfolio_governance_2026q4.md)

---

## Scénarios de test

```gherkin
# language: fr
Fonctionnalité: Compléter les dossiers de preuves Gate C9 des récits prêts au développement de Metro_COMMERCE

  # 1. NOMINAL (Happy Path & Persistance)
  Scénario: Génération complète des treize dossiers ancrés
    Étant donné l'inventaire des treize récits Metro_COMMERCE prêts au développement sans dossier de preuves
    Et que le corpus documentaire du sous-domaine OneTrust est disponible
    Quand l'orchestrateur produit les dossiers de preuves
    Alors chaque dossier existe sous la mémoire d'evidence du projet
    Et chaque dossier contient au moins cinq extraits verbatim doublement ancrés
    Et l'ancrage croise spécifications ingérées et architecture ou règles d'affaires

  Scénario: Liaison des paquets d'evidence sans renommage
    Étant donné un récit cible disposant d'un paquet d'evidence historique
    Quand le dossier du récit est généré
    Alors le paquet référence le dossier par son champ dédié
    Et le nom du paquet historique reste inchangé

  # 2. EXCEPTIONS (Cas d'erreur & Rejets métier)
  Scénario: Récit écarté de l'inventaire
    Étant donné un récit dont le statut n'est plus « prêt au développement »
    Quand l'inventaire des cibles est figé
    Alors ce récit n'apparaît pas comme cible
    Et aucun dossier n'est créé à son nom

  Scénario: Dossier jugé trop mince
    Étant donné un dossier produit avec un socle d'extraits sous le seuil requis
    Quand le contrôle de veto est exécuté
    Alors ce dossier est placé en file de revue humaine obligatoire
    Et la porte Gate C9 du lot reste non levée tant que la revue n'est pas close

  Scénario: Paquet d'evidence illisible
    Étant donné un paquet d'evidence corrompu ou hors schéma
    Quand l'orchestrateur tente la liaison vers le dossier
    Alors le paquet est réinitialisé à partir des sections récupérables
    Et le remplacement est tracé dans les preuves du récit

  # 3. RÉSILIENCE (Réseau / Timeout / Mode dégradé)
  Scénario: Échec partiel sans cascade
    Étant donné le lot des treize cibles
    Quand la génération échoue sur l'une d'elles
    Alors les autres dossiers sont produits indépendamment
    Et l'échec est isolé au récit fautif sans bloquer le bilan de lot

  Scénario: Extraction de maquette en échec
    Étant donné un fichier de maquette sans texte lisible
    Et que l'extraction optique échoue
    Quand le dossier du récit d'interface est produit
    Alors aucun libellé n'est inventé
    Et une question ouverte avec limite admise est consignée dans le dossier

  # 4. UX / ACCESSIBILITÉ / ÉTAT VIDE
  Scénario: Bilan de porte pour le pilote de gouvernance
    Étant donné le lot des treize dossiers produits et l'échantillon de revue clos
    Quand le contrôle Gate C9 est exécuté sur l'ensemble
    Alors le verdict de porte est tracé dans les preuves du récit
    Et les libellés réels de maquette ou les questions ouvertes sont lisibles dans les dossiers concernés

  Scénario: Récit cible sans corpus ancrable
    Étant donné un récit prêt au développement sans corpus documentaire exploitable
    Quand l'inventaire et la génération sont exécutés
    Alors le récit est signalé pour revue humaine
    Et aucun dossier fictionnel n'est créé
```
