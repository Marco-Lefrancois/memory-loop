---
id: MLOOP-207-BE
jira_key: ''
epic_key: EPIC-20-PORTFOLIO-GOVERNANCE
type: Feature
title: Passivation formelle du projet HTC et consignation des décisions de gouvernance Metro_SHARED et App_Sante
tags:
- portfolio
- governance
- passivation
- archive
- registry
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
# Passivation formelle du projet HTC et consignation des décisions de gouvernance Metro_SHARED et App_Sante

---

## Description
**En tant qu'** Orchestrateur mLoop,
**je veux** formaliser la passivation du projet HTC déjà déposé sous l'archive du portefeuille, inventorier sans y toucher les références résiduelles qui en subsistent dans les espaces actifs, et consigner les décisions de gouvernance de Metro_SHARED et d'App_Sante au registre des projets,
**afin d'** éliminer tout fantôme du registre des projets vivants, de rendre traçable chaque dette de résidu sans l'effacer à la dérobée, et d'ancrer dans un registre durable le sort de chaque dépôt orphelin de backlog.

---

## Contexte & Périmètre

### Contexte Métier
Le portefeuille mLoop contient des dépôt hérités qui ne correspondent plus à la définition d'un projet vivant : HTC repose déjà dans l'archive sans marqueur formel de sépulture, Metro_SHARED vit sans tableau de bord de travaux parce que son rôle est la diffusion en amont plutôt que l'exécution, et App_Sante conserve une matière de référence sans parcours de développement. Tant que ces situations ne sont pas écrites quelque part, chaque session risque de les reprendre pour des actifs oubliés ou, à l'inverse, de les rayar à tort du radar. Un registre unique tranche : ce qui est enterré avec son épitaphe, ce qui reste en service sous une forme non standard, ce qui attend une initialisation prochaine.

### In-Scope
- Épitaphe d'archive du projet HTC déposé sous l'archive : marqueur de sépulture portant la date, le motif de passivation et le décideur identifié, déposé aux côtés du contenu existant.
- Notice de passivation locale du projet HTC : document de clôture rédigé dans le dépôt archivé lui-même, indexé à la marque de sépulture, sans rien ajouter au catalogue des décisions d'architecture du cadre commun.
- Audit en lecture seule des références résiduelles à HTC dans les espaces hors archive : inventaire ligne à ligne classé en potentiel de fantôme, actif bénin ou question ouverte, consigné dans le dossier de preuves du présent récit, sans exécuter le moindre nettoyage ici.
- Registre des projets du portefeuille : création du registre durable sous la couche transverse du projet de gouvernance, recensant chaque dépôt du portefeuille avec son état de service et sa justification.
- Décision de gouvernance Metro_SHARED : verdict motivé sur la grille de quatre critères, arrêté à l'état de service non standard sous lequel le dépôt demeure, avec la justification appuyée sur son rôle de diffusion en amont sans tableau de bord par conception.
- Décision de gouvernance App_Sante : verdict motivé sur la même grille, arrêté à l'état d'initialisation à venir en raison du projet de conformité Santé annoncé pour le dépôt de référence, l'initialisation complète demeurant hors du présent récit.
- Retrait de HTC de tout inventaire de projets actifs du cadre de gouvernance, après vérification de son absence des listes vivantes.
- Production du dossier de preuves et du paquet de preuve du présent récit couvrant l'épitaphe, l'audit résiduel, la grille et les deux verdicts.

### Out-of-Scope
- Nettoyage effectif des références résiduelles à HTC inventoriées en lecture seule : chaque retrait devient une dette explicite et tracée séparée, jamais exécutée sous le couvert du présent récit.
- Normalisation ou récupération du contenu legacy de HTC : le corps archivé reste intact, seul son marqueur de sépulture est apposé.
- Initialisation complète de Metro_SHARED ou d'App_Sante : un verdict d'initialisation ouvre un futur chantier dédié, sans squelette de projet ébauché ici.
- Ajout d'une entrée au catalogue commun des décisions d'architecture du cadre : la passivation de projet client n'entre pas dans ce catalogue ; sa notice vit dans le dépôt archivé.
- Arbitrage par appels de programmation externe des références résiduelles : l'inventaire s'arrête au disque ; toute sonde de suivi de travaux distants devient une question ouverte nominative.
- Passivation d'un dépôt du portefeuille non nommé par la présente épopée de gouvernance.
- Réouverture d'un projet archivé ou d'un dépôt de référence sans décision formelle ultérieure du registre.

---

## Critères d'acceptation

### Opérations Métier & Logique Backend *(backend)*
#### 1. Apposition de l'épitaphe d'archive du projet HTC
* **Entrée Métier** : Dépôt déjà déposé sous l'archive du portefeuille, date d'exécution, motif de passivation arrêté par le décideur, identité du décideur.
* **Règles d'admissibilité & Validation** : Le dépôt cible doit résider sous l'archive ; à défaut, l'opération est refusée sans créer de marqueur ailleurs ; le motif et le décideur sont obligatoires et non vide.
* **Traitement & Algorithme Métier** : Vérification du lieu du dépôt, écriture atomique du marqueur de sépulture aux côtés du contenu existant, liaison de la notice de passivation locale, sans mutation du contenu archivé préexistant.
* **Résultat Métier & Mutations** : Le dépôt archivé porte un marqueur de sépulture complet (date, motif, décideur) et une notice de passivation locale ; le contenu d'origine est bit à bit inchangé.
* **Cas de Rejet Métier** : Rejet si le dépôt visé ne réside pas sous l'archive ; rejet si le marqueur existerait déjà sans révision nommée ; rejet en cas de tentative de modification du contenu archivé sous couvert d'apposition.

#### 2. Audit en lecture seule des références résiduelles hors archive
* **Entrée Métier** : Espaces hors archive du portefeuille, trois motifs de recherche ciblés (mentions du nom du projet dans les tableaux de bord et états de cycle, clé du projet dans les graphes de connaissance, actifs portant le préfixe du nom de l'archive).
* **Règles d'admissibilité & Validation** : Le balayage exclut le dépôt archivé lui-même ; les actifs d'interface du domaine partagé portant un préfixe homonyme sont classés bénins et jamais requalifiés en fantôme ; l'absence de preuve disque n'est jamais comblée par supposition.
* **Traitement & Algorithme Métier** : Balayage déterministe des tableaux de bord, états de cycle, état de cadre et graphes hors archive ; classification de chaque occurrence en potentiel de fantôme, actif bénin ou question ouverte ; aucune écriture de suppression.
* **Résultat Métier & Mutations** : Un inventaire ligne à ligne consigné dans le dossier de preuves du présent récit, chaque ligne portant la référence, le fichier, la ligne, la classification et la suite tracée.
* **Cas de Rejet Métier** : Rejet de tout balayage s'attaquant au contenu archivé ; rejet de tout nettoyage exécuté au passage ; rejet d'une ligne d'inventaire sans classification.

#### 3. Création du registre des projets du portefeuille
* **Entrée Métier** : Liste des dépôt du portefeulement hors archive, rôle déclaré de chacun, verdict de gouvernance pour les dépôt sans tableau de bord de travaux.
* **Règles d'admissibilité & Validation** : Le registre est créé une seule fois sous la couche transverse du projet de gouvernance ; tout dépôt déjà doté d'un parcours de développement standard y figure sous l'état de service vivant ; un dépôt sans tableau de bord n'y figure jamais sous l'état vivant sans justification de rôle non standard.
* **Traitement & Algorithme Métier** : Constitution du registre déterministe : nom du dépôt, état de service arrêté, justification, date de verdict ; liaison vers la notice de passivation locale pour tout dépôt archivé.
* **Résultat Métier & Mutations** : Le registre durable existe et recense l'ensemble du portefeulement hors archive ; chaque ligne est complète et justifiée.
* **Cas de Rejet Métier** : Rejet d'un second registre concurrent créé ailleurs ; rejet d'une ligne sans état de service ni justification.

#### 4. Arrêt des décisions de gouvernance sur la grille de quatre critères
* **Entrée Métier** : Dépôt sans tableau de bord de travaux, présence effective d'un tableau de bord, fraîcheur de l'activité interne, consommation par des dépôt en service, valeur future identifiée, verdict du décideur humain.
* **Règles d'admissibilité & Validation** : Les quatre critères sont renseignés par inspection directe avant tout verdict ; un verdict d'initialisation n'autorise aucun squelette de projet dans le présent récit ; un verdict de maintien non standard exige la justification du rôle réel du dépôt.
* **Traitement & Algorithme Métier** : Application de la grille aux deux dépôt cibles, production d'une recommandation motivée, recueil du verdict humain, écriture du verdict final dans le registre avec sa justification.
* **Résultat Métier & Mutations** : Metro_SHARED porte au registre l'état de maintien non standard motivé par son rôle de diffusion en amont sans tableau de bord par conception ; App_Sante porte l'état d'initialisation à venir motivé par le projet de conformité Santé annoncé, sans exécution d'initialisation ici.
* **Cas de Rejet Métier** : Rejet d'un verdict sans grille complétée ; rejet d'une écriture d'initialisation exécutant un squelette de projet ; rejet d'un verdict humain non consigné.

#### 5. Retrait du registre des projets vivants et suites tracées
* **Entrée Métier** : Inventaires de projets vivants du cadre de gouvernance, inventaire résiduel de l'audit, dette de nettoyage.
* **Règles d'admissibilité & Validation** : Le dépôt passivé ne peut figurer dans aucune liste de projets vivants après exécution ; toute référence résiduelle inventoriée reste intacte et devient une dette nominative ; toute sonde de suivi distant non couverte par le disque devient une question ouverte nominative.
* **Traitement & Algorithme Métier** : Vérification de retrait sur les inventaires vivants, conversion de l'inventaire résiduel en dettes et questions ouvertes tracées, liaison de le tout au paquet de preuve.
* **Résultat Métier & Mutations** : Le dépôt passivé est absent des listes vivantes ; chaque résidu est une dette nommée ; chaque sonde distante manquante est une question ouverte nommée ; le paquet de preuve scelle l'ensemble.
* **Cas de Rejet Métier** : Rejet d'un retrait des listes vivantes sans apposition préalable de l'épitaphe ; rejet d'un résidu inventorié mais non converti en dette tracée ; rejet d'une question ouverte non nominative.

#### Matrice des Contrats API
N/A — Récit de gouvernance de portefeuille documentaire 100 % local : aucune route réseau n'est exposée, consommée ou modifiée.
- **OQ-207 (Exemption Zéro Fausse Route)** : Exemption complète de la Matrice des Contrats API — apposition de marqueurs markdown locaux, audit de fichiers et registre documentaire, sans interface réseau `[API de soumission à définir]` ; toute sonde de suivi de travaux distants est consignée en question ouverte nominative, jamais simulée.
- **Admission of Limits** : Les avertissements de résilience d'interface hors domaine pour un composant sans interface ; la robustesse de la séquence est couverte par le troisième pilier (refus hors archive, écriture atomique du marqueur, aucun nettoyage silencieux, verdict sans grille rejeté).

---

## Règles d'affaires

- **Sépulture uniquement sous archive** : Le marqueur de passivation n'est apposé que sur un dépôt déjà résidant sous l'archive ; ailleurs, l'opération est refusée sans création parasite.
- **Corps archivé intouché** : L'apposition ne modifie jamais le contenu hérité ; seuls le marqueur et la notice locale sont ajoutés.
- **Audit sans balai** : L'inventaire résiduel est strictement en lecture seule ; tout nettoyage est une dette explicite et tracée, jamais un sous-produit.
- **Classification exhaustive** : Chaque occurrence inventoriée est classée en potentiel de fantôme, actif bénin ou question ouverte ; une ligne sans classement est un défaut de livraison.
- **Actifs homonymes bénins** : Les actifs d'interface du domaine partagé portant un préfixe homonyme au dépôt archivé restent classés bénins et ne déclenchent aucune requalification.
- **Registre unique** : Un seul registre des projets du portefeulement vit sous la couche transverse du projet de gouvernance ; tout second registre concurrent est proscrit.
- **Verdict après grille** : Aucun verdict de gouvernance n'est écrit sans les quatre critères renseignés par inspection et le verdict humain consigné.
- **Initialisation hors récit** : Un verdict d'initialisation n'autorise aucun squelette de projet ici ; il ouvre un chantier dédié futur.
- **Rôle non standard justifié** : Un dépôt vivant sans tableau de bord de travaux n'est enregistré qu'avec la justification de son rôle réel, jamais comme projet d'exécution silencieux.
- **Passivé hors listes vivantes** : Après épitaphe, le dépôt ne peut figurer dans aucune liste de projets vivants du cadre de gouvernance.
- **Gestion des données invalides** : Un dépôt introuvable ou illisible au moment de l'apposition ou de l'audit est signalé dans le paquet de preuve et n'est jamais deviné ; un verdict sans grille est refusé et tracé.

---

## Références

### 1. Preuves Amont & Traçabilité Factuelle
- 📂 **Dossier de Preuves Factuelles** : [`memory/evidence/MLOOP-207-BE_fact_dossier.md`](../../memory/evidence/MLOOP-207-BE_fact_dossier.md)
- 🏛️ **Décisions de cadrage** : Q1 audit résiduel en lecture seule avec dette tracée · Q2 notice locale embarquée dans l'archive et registre des projets sous la couche transverse · Q3 grille de quatre critères à trois issues et verdict humain dans l'entretien · Q4 balayage hors archive sur trois motifs ciblés avec actifs homonymes bénins et sonde distante en question ouverte · Q5 registre créé à neuf et taille d'exécution maintenue à l'extrême petite (Grill-Me 2026-09-24) · Verdicts humains : Metro_SHARED maintien non standard · App_Sante initialisation à venir (projet de conformité Santé annoncé)

### 2. Spécifications & Modèles de Données SSOT
- 📜 **Dossier de preuves** : [DOSSIER_DE_PREUVES_PROTOCOL.md](../../../standards/protocols/DOSSIER_DE_PREUVES_PROTOCOL.md)
- 📜 **Grill macro / micro** : [ADR-0320](../../../standards/adr-system/0320-grill-me-frontier-design-tree-alignment.md)
- 📜 **Gabarit de récit** : [story_template.md](../../../standards/blueprints/story_template.md)

### 3. Paquet OpenSpec (Handoff Développeur)
- 📄 **Épopée de rattachement** : [`backlog/epics/epic_portfolio_governance_2026q4.md`](../epics/epic_portfolio_governance_2026q4.md)
- 📂 **Dépôt passivé** : `Projects/_archive/HTC/`
- 📂 **Dépôt à verdict maintien** : `Projects/Metro_SHARED/`
- 📂 **Dépôt à verdict initialisation** : `Projects/App_Sante/`
- 📋 **Registre cible** : `Projects/mLoop/docs/04-transverse/REGISTRE_PROJETS.md`

---

## Scénarios de test

```gherkin
# language: fr
Fonctionnalité: Passivation formelle du projet HTC et consignation des décisions de gouvernance Metro_SHARED et App_Sante

  # 1. NOMINAL (Happy Path & Persistance)
  Scénario: Épitaphe posée et notice locale liée sous l'archive
    Étant donné un dépôt résidant sous l'archive du portefeuille
    Et que le motif de passivation et le décideur sont renseignés
    Quand l'orchestrateur appose le marqueur de sépulture
    Alors le marqueur porte la date, le motif et le décideur
    Et la notice de passivation locale y est liée
    Et le contenu archivé préexistant est inchangé

  Scénario: Inventaire résiduel complet hors archive
    Étant donné les espaces hors archive du portefeuille
    Quand l'audit en lecture seule balaie les trois motifs ciblés
    Alors chaque occurrence est classée en potentiel de fantôme, actif bénin ou question ouverte
    Et l'inventaire ligne à ligne figure dans le dossier de preuves
    Et aucun fichier n'est supprimé ou modifié par l'audit

  Scénario: Registre créé et verdicts consignés après grille
    Étant donné la grille de quatre critères renseignée pour les deux dépôt sans tableau de bord
    Et que le verdict humain est consigné pour chacun
    Quand le registre des projets du portefeuille est créé
    Alors Metro_SHARED y porte le maintien non standard motivé par son rôle de diffusion en amont
    Et App_Sante y porte l'initialisation à venir motivée par le projet de conformité Santé annoncé
    Et aucun squelette de projet n'est ébauché pour l'initialisation

  # 2. EXCEPTIONS (Cas d'erreur & Rejets métier)
  Scénario: Apposition refusée hors archive
    Étant donné un dépôt ne résidant pas sous l'archive
    Quand l'apposition du marqueur de sépulture est tentée
    Alors l'opération est refusée
    Et aucun marqueur n'est créé ailleurs

  Scénario: Verdict sans grille refusé
    Étant donné un dépôt sans les quatre critères renseignés par inspection
    Quand une écriture de verdict est tentée dans le registre
    Alors l'écriture est refusée
    Et le refus est tracé dans le paquet de preuve

  Scénario: Écriture d'initialisation exécutant un squelette de projet
    Étant donné un verdict d'initialisation consigné
    Quand une tentative ébauche une structure de projet complète
    Alors l'opération est interrompue
    Et seul le verdict figure au registre

  # 3. RÉSILIENCE (Réseau / Timeout / Mode dégradé)
  Scénario: Dépôt cible introuvable sans devinette
    Étant donné un chemin de dépôt visé qui n'existe pas ou est illisible
    Quand l'apposition ou l'audit tente d'accéder au dépôt
    Alors l'anomalie est signalée dans le paquet de preuve
    Et aucun contenu n'est supposé ni écrit à la place

  Scénario: Aucun nettoyage silencieux pendant l'audit
    Étant donné l'inventaire résiduel en cours de constitution
    Quand une occurrence est détectée dans un espace hors archive
    Alors l'occurrence reste intacte dans son fichier d'origine
    Et elle apparaît convertie en dette nominative dans le paquet de preuve

  Scénario: Second registre concurrent rejeté
    Étant donné un registre des projets déjà créé sous la couche transverse
    Quand une création concurrente est tentée ailleurs
    Alors la seconde création est refusée
    Et le registre d'origine demeure la seule source

  # 4. UX / ACCESSIBILITÉ / ÉTAT VIDE
  Scénario: Bilan de passivation pour le décideur
    Étant donné la clôture de l'épitaphe, de l'audit, du registre et des verdicts
    Quand le bilan est présenté
    Alors le marqueur de sépulture est daté, motivé et signé du décideur
    Et chaque résidu inventorié affiche sa classification et sa dette de suite
    Et chaque verdict du registre affiche sa grille et sa justification

  Scénario: Portefeulement vivant sans fantôme
    Étant donné le retrait vérifié des listes de projets vivants
    Quand le registre est consulté
    Alors le dépôt passivé n'apparaît dans aucune liste vivante
    Et le dépôt à maintien non standard y figure avec son rôle de diffusion
    Et le dépôt à initialisation y figure sans structure ébauchée
```
