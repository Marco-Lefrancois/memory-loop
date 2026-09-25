---
id: MLOOP-205-BE
jira_key: ''
epic_key: EPIC-20-PORTFOLIO-GOVERNANCE
type: Feature
title: Normalisation des vocabulaires module et phase dans les tableaux de bord de sprint des projets Metro
tags:
- portfolio
- governance
- modular
- metro
- backlog
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
# Normalisation des vocabulaires module et phase dans les tableaux de bord de sprint des projets Metro

---

## Description
**En tant qu'** Orchestrateur mLoop,
**je veux** doter les tableaux de bord de sprint des trois projets Metro d'une colonne de module fonctionnel alimentée par le vocabulaire d'initiatives réellement inventorié sur disque, d'une colonne de phase dérivée par correspondance déterministe depuis le statut existant, sans jamais renommer un dossier de récit ni réécrire un statut,
**afin d'** rendre homogène la lecture du portefeuille Metro, d'alimenter des requêtes de graphe cohérentes sur les modules métier, et d'éliminer la dette de vocabulaire inégal sans exposer les tableaux hétérogènes des dépôts santé à une régression d'information.

---

## Contexte & Périmètre

### Contexte Métier
Les trois tableaux de bord de sprint des dépôts Metro (FOOD, COMMERCE, SANTÉ) partagent le même rôle d'index maître mais n'exposent aucune colonne de module fonctionnel ni aucune colonne de phase : la lecture croisée du portefeuille repose sur la mémoire des initiatives, pas sur le tableau. Les dossiers de récits portent déjà un vocabulaire d'initiatives de fait (OneTrust par codebase, Offers, RBC Avion, Accès Dossier) qui n'est nulle part consigné comme vocabulaire canonique. L'ADR-0342 modulaire décrit un motif d'arborescence numérotée mais ne fournit — vérification faite — aucune liste fermée de noms de modules : le draft initial prétendait l'inverse. Un second défaut documentaire accompagne le chantier : deux fichiers d'architecture portent le même numéro 0342 et l'index du catalogue n'en référence qu'un seul. Tant que ces deux trous ne sont pas comblés, toute requête « modules Metro » dépend d'une connaissance tacite et tout travail déclaré « conforme ADR-0342 » s'appuie sur un index menteur.

### In-Scope
- Ajout d'une colonne `module` aux tableaux de chaque initiative des `sprint_backlog.md` de Metro_FOOD, Metro_COMMERCE et Metro_SANTE, renseignée exclusivement à partir du vocabulaire fermé d'initiatives inventoriées sur disque (dossiers `backlog/stories/*`), jamais inventé.
- Ajout d'une colonne `phase` aux mêmes tableaux, dérivée du statut existant par table de correspondance déterministe documentée dans le présent récit, sans altération de la colonne Statut.
- Préservation intégrale des colonnes existantes de chaque dépôt, y compris le schéma hétérogène de Metro_SANTE (Taille, Effort, Valeur) : l'ajout est purement additif.
- Correction minimale de l'index du catalogue des décisions d'architecture pour référencer les deux fichiers portant le numéro 0342, sans renumérotation d'aucun fichier.
- Contrôle déterministe par recherche de texte sur les trois tableaux avant synchronisation, puis synchronisation séquentielle de chaque projet cible et requête de graphe de confirmation.
- Production du dossier de preuves et du paquet de preuve couvrant l'inventaire du vocabulaire, la table de phase, la collision d'index et les contrôles.

### Out-of-Scope
- Renommage de dossiers de récits ou de fichiers de récits dans les trois dépôts Metro : le vocabulaire s'exprime dans le tableau de bord, l'arborescence héritée reste intacte.
- Ajout de champs de module ou de phase dans le frontmatter des récits : dette explicite et reportée, jamais exécutée sous couvert du présent récit.
- Extension de l'ADR-0342 modulaire par une nouvelle section de vocabulaire fermé : l'ADR n'est pas modifié ; seul son index est réparé.
- Renumérotation d'un des deux fichiers portant le numéro 0342 : dette de numérotation tracée séparément.
- Harmonisation forcée du schéma de tableau de Metro_SANTE sur celui de FOOD ou COMMERCE : les colonnes Taille, Effort et Valeur sont préservées telles quelles.
- Traitement des doublons transverses OneTrust ×3 et RBC ×2 (couvert par la story de grillage transverse dédiée de l'épopée).
- Normalisation des dépôts hors Metro (BoireFrere, Shopify, mLoop, Metro_SHARED, App_Sante).
- Synchronisation vers Jira des libellés de module : normalisation locale mLoop uniquement.
- Modification du code source des applications Metro (hermétique).

---

## Critères d'acceptation

### Opérations Métier & Logique Backend *(backend)*
#### 1. Inventaire du vocabulaire fermé de modules par dépôt
* **Entrée Métier** : Arborescence des dossiers de récits de chaque dépôt Metro, libellé d'initiative porté par chaque dossier.
* **Règles d'admissibilité & Validation** : Le vocabulaire de chaque dépôt est constitué exclusivement des libellés de dossiers physiquement présents ; un libellé absent du disque n'est jamais ajouté par inférence ; un libellé hérité non Metro est exclu.
* **Traitement & Algorithme Métier** : Balayage déterministe de `backlog/stories/` de chaque dépôt, extraction des noms de dossiers, normalisation en identifiant de module stable, consignation dans le dossier de preuves.
* **Résultat Métier & Mutations** : Un vocabulaire fermé par dépôt est consigné : modules FOOD, modules COMMERCE, modules SANTÉ, chacun adossé à un dossier réellement inventorié.
* **Cas de Rejet Métier** : Rejet de tout module sans dossier physique correspondant ; rejet d'un vocabulaire confondu entre dépôts sans distinction de codebase.

#### 2. Ajout additif des colonnes module et phase aux tableaux existants
* **Entrée Métier** : Trois tableaux de bord de sprint, vocabulaire de module du dépôt, table de correspondance statut → phase.
* **Règles d'admissibilité & Validation** : Les colonnes `module` et `phase` sont ajoutées sans supprimer ni réordonner aucune colonne existante ; la colonne Statut reste la source unique de la phase ; le module de chaque ligne doit appartenir au vocabulaire fermé du dépôt.
* **Traitement & Algorithme Métier** : Pour chaque ligne de chaque initiative : lecture de la section d'initiative, détermination du module par appartenance au dossier de l'initiative, dérivation de la phase par table de correspondance, écriture des deux nouvelles colonnes à côté des colonnes existantes.
* **Résultat Métier & Mutations** : Chaque tableau des trois dépôts porte les colonnes `module` et `phase` ; toutes les lignes sont renseignées ; les colonnes d'origine, y compris Taille, Effort et Valeur de Metro_SANTE, sont bit à bit préservées.
* **Cas de Rejet Métier** : Rejet d'une ligne dont le module sort du vocabulaire fermé ; rejet d'une dérivation de phase sans statut source ; rejet de toute suppression ou réécriture d'une colonne existante.

#### 3. Réparation minimale de l'index du catalogue des décisions d'architecture
* **Entrée Métier** : Index du catalogue, fichiers réellement présents portant le numéro 0342.
* **Règles d'admissibilité & Validation** : Seule la ligne d'index est modifiée ; aucun fichier d'architecture n'est créé, supprimé, renommé ni réécrit ; les deux fichiers existants sont référencés avec leur titre distinct.
* **Traitement & Algorithme Métier** : Vérification de la présence des deux fichiers, ajout de la référence manquante à l'index sous le même numéro, sans renumérotation.
* **Résultat Métier & Mutations** : L'index référence les deux décisions portant le numéro 0342 ; les fichiers eux-mêmes sont inchangés.
* **Cas de Rejet Métier** : Rejet d'une renumérotation de fichier ; rejet d'une modification du corps d'un fichier d'architecture ; rejet d'une entrée d'index pointant vers un fichier absent du disque.

#### 4. Contrôle déterministe puis synchronisation séquentielle et requête de graphe
* **Entrée Métier** : Trois tableaux normalisés, trois dépôts cibles, un identifiant de requête de graphe.
* **Règles d'admissibilité & Validation** : Le contrôle de texte précède toute synchronisation ; les synchronisations de dépôt s'exécutent une à une, jamais en parallèle ; la requête de graphe s'exécute après la dernière synchronisation.
* **Traitement & Algorithme Métier** : Recherche de texte vérifiant la présence des deux colonnes et l'absence de module hors vocabulaire sur chaque tableau ; synchronisation séquentielle FOOD puis COMMERCE puis SANTÉ ; requête de graphe ciblée sur les modules Metro.
* **Résultat Métier & Mutations** : Les trois contrôles de texte passent avant toute synchronisation ; les trois synchronisations complètent sans conflit de verrou ; la requête de graphe restitue les modules normalisés.
* **Cas de Rejet Métier** : Rejet d'une synchronisation lancée avant le contrôle de texte ; rejet de deux synchronisations concurrentes sur un même dépôt ; rejet d'une requête de graphe exécutée avant la dernière synchronisation.

#### 5. Conservation des statuts, des contenus métier et traçabilité des dettes
* **Entrée Métier** : État des récits avant et après normalisation, listes des dettes reportées.
* **Règles d'admissibilité & Validation** : Aucun statut de récit, aucun frontmatter de récit et aucun libellé métier de titre ne changent ; chaque élément hors périmètre explicitement écarté est consigné comme dette nominative.
* **Traitement & Algorithme Métier** : Comparaison déterministe des statuts et des frontmatter avant/après, consignation des dettes (frontmatter module/phase, renumérotation 0342, renommage de dossiers) dans le paquet de preuve.
* **Résultat Métier & Mutations** : Zéro mutation de récit ; les dettes reportées figurent au paquet de preuve avec leur story ou épique d'accueil.
* **Cas de Rejet Métier** : Rejet d'un statut modifié pendant la normalisation ; rejet d'une dette non nominative ; rejet d'une dette exécutée en sous-main.

#### Matrice des Contrats API
N/A — Récit de gouvernance documentaire 100 % local : aucune route réseau n'est exposée, consommée ou modifiée.
- **OQ-205 (Exemption Zéro Fausse Route)** : Exemption complète de la Matrice des Contrats API — édition de tableaux Markdown locaux, réparation d'un index de catalogue et synchronisation sémantique de dépôts, sans interface réseau `[API de soumission à définir]` ; toute extension de vocabulaire vers un système externe (Jira notamment) reste hors périmètre et deviendrait une question ouverte nominative, jamais simulée.
- **Admission of Limits** : Les avertissements de résilience d'interface hors domaine s'appliquent à un composant sans interface ; la robustesse de la séquence est couverte par le troisième pilier (module hors vocabulaire rejeté, contrôle avant synchronisation, synchronisations séquentielles, statuts intouchés).

---

## Règles d'affaires

- **Vocabulaire de fait, jamais inventé** : Le module d'une ligne provient exclusivement du nom du dossier d'initiative physiquement inventorié sous `backlog/stories/` du dépôt ; un module sans dossier réel est un défaut de livraison.
- **Phase dérivée, statut intact** : La colonne phase est un sous-produit déterministe de la colonne Statut selon la table documentée ; elle ne remplace, ne masque et ne réécrit jamais le statut.
- **Ajout purement additif** : Aucune colonne existante n'est supprimée, réordonnée ni reformée ; le schéma hétérogène de Metro_SANTE est un fait respecté, pas un défaut corrigé ici.
- **Zéro renommage d'arborescence** : Les dossiers et fichiers de récits hérités sont intouchés ; le vocabulaire normalisé vit dans le tableau de bord, pas dans les chemins.
- **Zéro mutation de récit** : Statuts, frontmatter et titres des récits sont bit à bit inchangés par le présent récit.
- **Index réparé sans renumérotation** : La réparation d'index ajoute la référence manquante ; elle ne crée, ne supprime ni ne renumérote aucun fichier d'architecture.
- **Contrôle avant synchronisation** : Aucune synchronisation de dépôt ne démarre avant le passage des contrôles de texte sur le tableau concerné.
- **Synchronisations strictement séquentielles** : Une seule synchronisation de dépôt à la fois ; toute concurrence est un risque de verrou de fichier et est proscrite.
- **Jira hors périmètre** : La normalisation est locale mLoop ; aucune poussée de libellés de module vers Jira n'est exécutée sous couvert du présent récit.
- **Dettes nominatives** : Frontmatter module/phase, renumérotation de la collision 0342 et renommage éventuel de dossiers sont reportés comme dettes tracées, jamais absorbés en sous-main.
- **Gestion des données invalides** : Un tableau illisible, un dossier de récit introuvable ou un statut absent est signalé dans le paquet de preuve et n'est jamais deviné ; une ligne hors vocabulaire est refusée et tracée.

---

## Références

### 1. Preuves Amont & Traçabilité Factuelle
- 📂 **Dossier de Preuves Factuelles** : [`memory/evidence/MLOOP-205-BE_fact_dossier.md`](../../memory/evidence/MLOOP-205-BE_fact_dossier.md)
- 🏛️ **Décisions de cadrage** : Q1 = C deux colonnes (module initiative + phase dérivée, zéro renommage) · prémisse « liste fermée §3 » rejetée comme fausse · Q2a = i colonnes sur les 3 tableaux seulement (zéro frontmatter) · Q2b = β préservation du schéma SANTE, ajout non régressif · Q2c = y réparation de l'index 0342 en deux références, zéro renumérotation · Q3a = P contrôle de texte, puis trois synchronisations séquentielles, puis requête de graphe · Q3b = XS macro révisée de M à XS (Grill-Me 2026-09-24)

### 2. Spécifications & Modèles de Données SSOT
- 📜 **Dossier de preuves** : [DOSSIER_DE_PREUVES_PROTOCOL.md](../../../standards/protocols/DOSSIER_DE_PREUVES_PROTOCOL.md)
- 📜 **Grill macro / micro** : [ADR-0320](../../../standards/adr-system/0320-grill-me-frontier-design-tree-alignment.md)
- 📜 **Gabarit de récit** : [story_template.md](../../../standards/blueprints/story_template.md)
- 📜 **ADR modulaire** : [0342-modular-project-architecture-and-subdomain-isolation.md](../../../standards/adr-system/0342-modular-project-architecture-and-subdomain-isolation.md)
- 📜 **ADR extraction** : [0342-declarative-yaml-extraction-blueprints.md](../../../standards/adr-system/0342-declarative-yaml-extraction-blueprints.md)

### 3. Paquet OpenSpec (Handoff Développeur)
- 📄 **Épopée de rattachement** : [`backlog/epics/epic_portfolio_governance_2026q4.md`](../epics/epic_portfolio_governance_2026q4.md)
- 📋 **Tableau FOOD cible** : `Projects/Metro_FOOD/backlog/sprint_backlog.md`
- 📋 **Tableau COMMERCE cible** : `Projects/Metro_COMMERCE/backlog/sprint_backlog.md`
- 📋 **Tableau SANTÉ cible** : `Projects/Metro_SANTE/backlog/sprint_backlog.md`
- 📇 **Index catalogue à réparer** : `standards/adr-system/README.md`

---

## Scénarios de test

```gherkin
# language: fr
Fonctionnalité: Normalisation des vocabulaires module et phase dans les tableaux de bord de sprint des projets Metro

  # 1. NOMINAL (Happy Path & Persistance)
  Scénario: Vocabulaire fermé inventorié pour chaque dépôt
    Étant donné l'arborescence des dossiers de récits de Metro_FOOD, Metro_COMMERCE et Metro_SANTE
    Quand le vocabulaire de module de chaque dépôt est constitué
    Alors chaque module listé correspond à un dossier physiquement présent
    Et les modules de chaque dépôt restent distincts de ceux des autres dépôts
    Et aucun module sans dossier réel n'apparaît dans le vocabulaire

  Scénario: Colonnes module et phase ajoutées sans perte de colonne
    Étant donné les trois tableaux de bord de sprint avec leurs colonnes existantes
    Quand les colonnes module et phase sont ajoutées à chaque initiative
    Alors chaque ligne porte un module du vocabulaire fermé et une phase dérivée
    Et toutes les colonnes d'origine demeurent présentes et inchangées
    Et les colonnes Taille, Effort et Valeur de Metro_SANTE sont préservées

  Scénario: Phase dérivée par table de correspondance déterministe
    Étant donné un récit portant un statut dans la colonne Statut
    Quand la phase est calculée par la table de correspondance documentée
    Alors la phase obtenue est exactement celle assignée au statut source
    Et la colonne Statut reste bit à bit identique à l'état d'origine

  Scénario: Index du catalogue réparé pour les deux décisions numérotées 0342
    Étant donné deux fichiers d'architecture portant le numéro 0342 sur disque
    Quand l'index du catalogue est complété
    Alors les deux fichiers y figurent avec leur titre respectif
    Et aucun fichier n'est renommé ni renuméroté
    Et le corps des deux fichiers reste inchangé

  Scénario: Contrôle de texte puis synchronisation séquentielle puis graphe
    Étant donné les trois tableaux normalisés et non encore synchronisés
    Quand les contrôles de texte passent sur chaque tableau
    Alors la synchronisation de Metro_FOOD s'exécute seule
    Et la synchronisation de Metro_COMMERCE s'exécute à la suite
    Et la synchronisation de Metro_SANTE s'exécute à la suite
    Et la requête de graphe sur les modules Metro rend les modules normalisés

  # 2. EXCEPTIONS (Cas d'erreur & Rejets métier)
  Scénario: Module hors vocabulaire fermé refusé
    Étant donné une ligne de tableau dont le module ne correspond à aucun dossier inventorié
    Quand la normalisation tente d'écrire cette ligne
    Alors l'écriture est refusée
    Et la ligne est tracée dans le paquet de preuve sans devinette de valeur de remplacement

  Scénario: Suppression d'une colonne existante refusée
    Étant donné un tableau comportant une colonne d'origine
    Quand une opération tente de supprimer ou de réordonner cette colonne
    Alors l'opération est refusée
    Et le tableau conserve toutes ses colonnes d'origine

  Scénario: Renumérotation d'un fichier d'architecture refusée
    Étant donné l'index du catalogue à réparer
    Quand une opération tente de renommer ou de renuméroter l'un des deux fichiers 0342
    Alors l'opération est interrompue
    Et seul l'index est mis à jour

  Scénario: Synchronisation concurrente refusée
    Étant donné une synchronisation de dépôt déjà en cours
    Quand une seconde synchronisation de dépôt est lancée
    Alors la seconde est refusée
    Et la file reprend l'exécution séquentielle

  # 3. RÉSILIENCE (Réseau / Timeout / Mode dégradé)
  Scénario: Tableau illisible signalé sans invention
    Étant donné un fichier de tableau de bord absent ou illisible
    Quand la normalisation tente de le lire
    Alors l'anomalie est signalée dans le paquet de preuve
    Et aucun tableau n'est reconstruit à partir de supposition

  Scénario: Statut absent sans dérivation de phase possible
    Étant donné une ligne dont la colonne Statut est vide ou inconnue
    Quand la phase tente d'être dérivée
    Alors la dérivation est refusée pour cette ligne
    Et l'anomalie est tracée sans attribuer de phase par défaut inventée

  Scénario: Échec de synchronisation stoppe la séquence
    Étant donné l'échec d'une synchronisation de dépôt
    Quand la séquence de synchronisation poursuit
    Alors l'échec est consigné
    Et aucune synchronisation suivante n'est lancée avant résolution

  # 4. UX / ACCESSIBILITÉ / ÉTAT VIDE
  Scénario: Lecture croisée du portefeuille Metro pour le décideur
    Étant donné les trois tableaux normalisés
    Quand le décideur compare les initiatives d'un dépôt à l'autre
    Alors chaque ligne affiche son module fonctionnel et sa phase
    Et le statut d'origine demeure visible à côté de la phase
    Et le schéma propre à chaque dépôt est intact

  Scénario: Vocabulaire découvert à partir du disque uniquement
    Étant donné un dépôt dont l'arborescence de récits est la seule source
    Quand le vocabulaire de module est reconstitué
    Alors il reflète exactement les dossiers présents
    Et aucun libellé d'initiative absent du disque n'est ajouté
```
