---
id: MLOOP-202-BE
jira_key: ''
epic_key: EPIC-20-PORTFOLIO-GOVERNANCE
type: Feature
title: Conduire la séquence de revues contradictoires des récits Metro_FOOD en attente de définition de prontitude
tags:
- grill
- onetrust
- food
- dor
- portfolio
status: DONE
grill_me: DONE
layer: backend
invest_score: 6/6
macro_size: L
origin: DIRECT_REQUIREMENT
source_ref: epic_portfolio_governance_2026q4.md
blocked_by: []
created_at: '2026-09-23'
ttl_cycles: 3
---
# Conduire la séquence de revues contradictoires des récits Metro_FOOD en attente de définition de prontitude

---

## Description
**En tant qu'** Orchestrateur mLoop,
**je veux** conduire la séquence complète de revues contradictoires 1:1 sur les douze récits Metro_FOOD encore en attente de définition de prontitude,
**afin de** valider une définition de prontitude complète pour chacun, de les promouvoir légitimement vers le développement et de débloquer le handoff vers les agents aval sans auto-approbation.

---

## Contexte & Périmètre

### Contexte Métier
Le tableau de bord Metro_FOOD affiche douze récits du programme de conformité au consentement déjà positionnés en revue, sans définition de prontitude close. Ces récits conditionnent le passage en développement de la chaîne de conformité ; laisser la porte ouverte expose le handoff aval à des spécifications non contredites en session de revue. Une décision de cadrage macro existe déjà pour l'initiative papercuts du même codebase, mais son périmètre déclaré ne couvre pas le programme de consentement : une session transverse ciblée reste requise avant les revues unitaires.

### In-Scope
- Session de cadrage macro transverse ciblée sur les axes consentement, synchronisation de consentement et circulaire en vue externe du programme OneTrust FOOD, sans réouverture des décisions macro déjà clôturées sur l'initiative papercuts.
- Inventaire et qualification du socle de preuves des douze récits : appariement clé de suivi / identifiant historique, complétude du dossier de preuves existant, présence des paquets d'evidence et des revues Sentinel antérieures.
- Douze sessions de revue contradictoire 1:1, une question atomique par tour, sur les douze récits en attente de définition de prontitude.
- Réécriture des quatre piliers de scénarios pour tout récit dont le socle qualifié présente un trou ; aucun critère d'acceptation existant n'est auto-validé.
- Relance de la revue Sentinel après chaque session de revue unitaire, puis contrôle de définition de prontitude complet.
- Promotion vers le développement uniquement après feu vert humain explicite par récit.
- Mise à jour du tableau de bord de sprint du projet après validation.
- Production ou mise à jour des paquets d'evidence et des dossiers de preuves pour les douze récits.

### Out-of-Scope
- Traitement unitaire des sept récits en attente de décision de l'initiative offres : leur sort reste porté par le registre de décisions papercuts déjà clôturé.
- Tout travail sur l'ébauche de mode hors-ligne tant que le département légal n'a pas tranché la question ouverte de synchronisation de consentement hors-ligne ; toute reprise fera l'objet d'un récit dédié.
- Correction du corps des récits legacy déjà arbitrés en non-correction.
- Auto-approbation d'un récit vers le développement sans revue contradictoire interactive.
- Sessions de revue sur d'autres projets du portefeuille.
- Réouverture des décisions macro papercuts déjà actées et datées.

---

## Critères d'acceptation

### Opérations Métier & Logique Backend *(backend)*
#### 1. Session de cadrage macro transverse ciblée
* **Entrée Métier** : Registre de décisions macro existant, périmètre des douze récits et questions ouvertes du programme de consentement.
* **Règles d'admissibilité & Validation** : Les décisions macro déjà clôturées et datées ne sont pas réouvertes ; seuls les axes non tranchés par le registre existant et directement portés par les douze récits sont posés.
* **Traitement & Algorithme Métier** : Recoupement registre / périmètre / questions ouvertes, liste des axes vierges, session à question atomique par tour, consignation datée des arbitrages.
* **Résultat Métier & Mutations** : Registre de décisions transverses du programme de consentement, consultable avant toute revue unitaire.
* **Cas de Rejet Métier** : Rejet d'une question dont la réponse figure déjà dans le registre macro existant ; elle est référencée au lieu d'être reposée.

#### 2. Qualification du socle de preuves des douze récits
* **Entrée Métier** : Douze récits en attente, répertoire des dossiers de preuves et paquets d'evidence du projet.
* **Règles d'admissibilité & Validation** : Chaque récit est apparié à son dossier et à son paquet ; le socle est qualifié complet, partiel ou absent ; aucun dossier n'est réputé complet sans inspection des extraits ancrés.
* **Traitement & Algorithme Métier** : Appariement déterministe, comptage des extraits doublement ancrés, détection des trous, tableau de qualification.
* **Résultat Métier & Mutations** : Tableau de qualification douze lignes tracé dans les preuves du récit.
* **Cas de Rejet Métier** : Rejet d'un appariement ambigu ; le récit est signalé socle inconnu et passe en revue comme s'il était absent.

#### 3. Revue contradictoire unitaire des douze récits
* **Entrée Métier** : Récit cible, socle qualifié, registre transverse et corpus documentaire du projet.
* **Règles d'admissibilité & Validation** : Une question atomique par tour ; aucun critère existant n'est validé par défaut ; toute zone d'ombre tranchée est consignée avec sa recommandation.
* **Traitement & Algorithme Métier** : Déconstruction à froid, question, arbitrage, amendement du récit, réécriture des quatre piliers si trou de socle.
* **Résultat Métier & Mutations** : Récit amendé, décisions de revue tracées, socle complété le cas échéant.
* **Cas de Rejet Métier** : Rejet de toute promotion sans revue complète du récit ; le récit reste en attente de définition de prontitude.

#### 4. Relance Sentinel et contrôle de prontitude
* **Entrée Métier** : Récit amendé après revue et paquet d'evidence associé.
* **Règles d'admissibilité & Validation** : La revue Sentinel est relancée après amendement ; le contrôle de définition de prontitude ne s'exécute qu'après verdict Sentinel sans défaut bloquant ; le feu vert humain est enregistré par récit avant toute promotion.
* **Traitement & Algorithme Métier** : Exécution de la revue, correction des rejets, exécution du contrôle, journalisation du feu vert, mise à jour du tableau de bord.
* **Résultat Métier & Mutations** : Douze verdicts de prontitude ou liste résiduelle d'échecs motivés ; tableau de bord aligné uniquement sur les récits feu vertés.
* **Cas de Rejet Métier** : Rejet de la promotion si Sentinel, le contrôle de prontitude ou le feu vert manque ; aucune levée partielle non tracée.

#### 5. Périmètre hors séquence (exclusions)
* **Entrée Métier** : Sept récits en attente de décision de l'initiative offres et ébauche hors-ligne.
* **Règles d'admissibilité & Validation** : Aucun travail unitaire n'est produit sur ces périmètres dans le présent récit ; l'ébauche hors-ligne reste bloquée tant que la question légale est ouverte.
* **Traitement & Algorithme Métier** : Exclusion déterministe à l'inventaire des douze, trace d'exclusion.
* **Résultat Métier & Mutations** : Liste d'exclusion documentée dans les preuves.
* **Cas de Rejet Métier** : Rejet de toute tentative d'inclusion de ces récits dans la séquence des douze.

#### Matrice des Contrats API
N/A — Récit de gouvernance de revues documentaires 100 % local : aucune route REST/CTA n'est exposée, consommée ou modifiée.
- **OQ-202 (Exemption Zéro Fausse Route)** : Exemption complète de la Matrice des Contrats API — séances de revue et fichiers markdown/JSON locaux, sans interface HTTP `[API de soumission à définir]` ; toute future exposition d'API est à confirmer dans un récit dédié avec sa propre matrice.
- **Admission of Limits** : Les avertissements génériques de revue (anti-rebond, expiration de session, saisie) sont hors domaine pour ce composant sans interface ; la résilience de la séquence est couverte par le Pilier 2 (échec unitaire sans cascade, socle absent, refus de promotion).

---

## Règles d'affaires

- **Macro avant micro** : Aucune revue unitaire des douze ne s'ouvre avant la clôture de la session transverse ciblée du présent récit.
- **Registre macro non réouvrable** : Les décisions macro déjà actées et datées sur l'initiative papercuts sont référencées, jamais reposées.
- **Qualification avant réutilisation** : Un dossier, un paquet ou une revue antérieure n'entre dans la revue qu'après qualification explicite du socle.
- **Zéro auto-validation de critères** : Tout critère d'acceptation existant est relu en session ; les quatre piliers sont réécrits dès qu'un trou de socle est détecté.
- **Feu vert humain par récit** : La promotion vers le développement exige un feu vert nommé et journalisé par récit ; l'absence de feu vert maintient le récit en attente.
- **Échec unitaire sans cascade** : L'échec d'une revue isole le récit fautif sans bloquer les autres ni le bilan de séquence.
- **Porte légale séparée** : L'ébauche hors-ligne n'entre jamais dans la séquence tant que la question de synchronisation de consentement hors-ligne est ouverte auprès du département légal.
- **Gestion des données invalides** : Un paquet illisible est réinitialisé avec trace ; un dossier corrompu est régénéré depuis les sources, jamais édité pour masquer la corruption.

---

## Références

### 1. Preuves Amont & Traçabilité Factuelle
- 📂 **Dossier de Preuves Factuelles** : [`memory/evidence/MLOOP-202-BE_fact_dossier.md`](../../memory/evidence/MLOOP-202-BE_fact_dossier.md)
- 🏛️ **Décisions de cadrage** : Q1 hybride macro ciblée · Q2 qualification du socle · Q3 hors périmètre offres et porte légale séparée (Grill-Me 2026-09-23)

### 2. Spécifications & Modèles de Données SSOT
- 📜 **Dossier de preuves** : [DOSSIER_DE_PREUVES_PROTOCOL.md](../../../standards/protocols/DOSSIER_DE_PREUVES_PROTOCOL.md)
- 📜 **Architecture modulaire** : [ADR-0342](../../../standards/adr-system/0342-modular-project-architecture-and-subdomain-isolation.md)
- 📜 **Grill macro / micro** : [ADR-0320](../../../standards/adr-system/0320-grill-me-frontier-design-tree-alignment.md)

### 3. Paquet OpenSpec (Handoff Développeur)
- 📄 **Épopée de rattachement** : [`backlog/epics/epic_portfolio_governance_2026q4.md`](../epics/epic_portfolio_governance_2026q4.md)

---

## Scénarios de test

```gherkin
# language: fr
Fonctionnalité: Conduire la séquence de revues contradictoires des récits Metro_FOOD en attente de définition de prontitude

  # 1. NOMINAL (Happy Path & Persistance)
  Scénario: Séquence complète des douze récits vers la prontitude
    Étant donné la session transverse ciblée clôturée et le registre de décisions consigné
    Et que la qualification du socle couvre les douze récits
    Quand l'orchestrateur conduit les douze revues contradictoires
    Alors chaque récit dispose des quatre piliers complets
    Et chaque relance Sentinel est close sans défaut bloquant
    Et chaque promotion est précédée d'un feu vert humain journalisé

  Scénario: Registre transverse consultable avant les revues unitaires
    Étant donné les arbitrages de la session transverse ciblée
    Quand la première revue unitaire démarre
    Alors le registre transverse est référencé dans les preuves du récit
    Et aucune décision macro papercuts n'est reposée

  # 2. EXCEPTIONS (Cas d'erreur & Rejets métier)
  Scénario: Question macro déjà tranchée
    Étant donné une question dont la réponse figure dans le registre macro existant
    Quand l'orchestrateur tente de la poser en session transverse
    Alors la question est rejetée
    Et la décision existante est référencée à la place

  Scénario: Socle ambigu ou absent pour un récit
    Étant donné un récit dont l'appariement dossier ou paquet est ambigu
    Quand la qualification du socle est exécutée
    Alors le récit est traité comme socle absent
    Et il passe en revue sans réutilisation d'un socle non inspecté

  Scénario: Refus de promotion sans feu vert
    Étant donné un récit amendé et Sentinel vert
    Mais sans feu vert humain journalisé
    Quand la mise à jour du tableau de bord est tentée
    Alors le récit reste en attente de définition de prontitude
    Et l'absence de feu vert est documentée

  # 3. RÉSILIENCE (Réseau / Timeout / Mode dégradé)
  Scénario: Échec d'une revue sans cascade
    Étant donné la séquence des douze récits
    Quand une revue unitaire échoue ou est interrompue
    Alors les autres revues se poursuivent indépendamment
    Et le bilan de séquence isole le récit fautif

  Scénario: Relance Sentinel rejetée
    Étant donné un récit amendé soumis à la revue Sentinel
    Mais que la revue retourne un défaut bloquant
    Quand le contrôle de prontitude est enchaîné
    Alors le contrôle n'est pas levé
    Et le récit revient en correction avant nouvelle relance

  Scénario: Tentative d'inclusion des récits hors séquence
    Étant donné un récit de l'initiative offres ou l'ébauche hors-ligne
    Quand l'inventaire des douze est figé
    Alors ce récit n'entre pas dans la séquence
    Et l'exclusion est tracée dans les preuves

  # 4. UX / ACCESSIBILITÉ / ÉTAT VIDE
  Scénario: Bilan de séquence pour le pilote de gouvernance
    Étant donné la fin de la séquence des douze revues
    Quand le bilan est produit
    Alors chaque ligne indique récit, verdict de prontitude et feu vert
    Et la liste résiduelle des échecs est motivée, jamais masquée

  Scénario: Projet sans feu vert résiduel
    Étant donné le tableau de bord de sprint après séquence
    Quand aucun récit n'a reçu de feu vert
    Alors aucun statut de développement n'est posé
    Et le tableau de bord reflète l'attente réelle
```
