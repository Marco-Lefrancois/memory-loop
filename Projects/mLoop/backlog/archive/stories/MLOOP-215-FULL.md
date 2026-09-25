---
id: MLOOP-215-FULL
jira_key: ''
epic_key: EPIC-21-MCP-MODERN-SUITE
type: Feature
title: Harnais de Certification & Conformité E2E MCP 2026-07-28 & Non-Régression Multi-IDE
origin: DIRECT_REQUIREMENT
source_ref: ADR-0387
macro_size: M
status: DONE_TESTED
grill_me: DONE
layer: fullstack
invest_score: 6/6
blocked_by:
- MLOOP-210-BE
- MLOOP-211-BE
- MLOOP-212-FE
- MLOOP-213-BE
- MLOOP-214-BE
created_at: '2026-09-24'
content_hash: 83855d980f171beb
---
# Harnais de Certification & Conformité E2E MCP 2026-07-28 & Non-Régression Multi-IDE

---

## Description
**En tant qu'** responsable qualité et architecte mLoop,
**je veux** disposer d'un harnais de certification de bout en bout qui vérifie, d'une part, la conformité des ponts mLoop à la révision moderne du protocole et à ses extensions (tâches asynchrones, affichage embarqué, élicitation, compétences) et, d'autre part, l'absence de régression des échanges déjà en service,
**afin de** publier un verdict unique, traçable et opposable avant toute mise à disposition, sans m'appuyer sur un chiffre de tests figé ni prétendre automatiser la vérification d'un IDE réel.

---

## Contexte & Périmètre

### Contexte Métier
mLoop expose localement des ponts consommés par plusieurs agents hétérogènes — OpenCode, Claude Code et Antigravity — qui n'adoptent pas tous la révision moderne du protocole ni ses extensions. Le socle protocolaire, les tâches asynchrones, l'affichage embarqué dans la conversation, l'élicitation de formulaires et l'exposition des compétences sont construits séparément : aucun d'eux ne peut être déclaré livré sans un verdict de conformité qui les prenne collectivement au même instant, ni sans la preuve qu'aucun échange hérité n'a régressé. Ce verdict a deux temps indissociables : une certification déterministe exécutée à chaque passage en intégration continue, puis un audit manuel périodique des IDE réels lorsque le comportement observé ne peut pas être fabriqué en laboratoire. Le contrôle pré-vol déterministe de l'écosystème devient l'endroit unique où ce verdict se lit, aux côtés de ses autres contrôles, sans créer une seconde porte d'entrée pour la qualité. Le harnais ne répare rien : il constate, il prouve, il rapporte, et il nomme ce qu'il n'a pas pu observer.

### In-Scope
- Certification nominale des échanges JSON-RPC conformes à la révision moderne, en-tête de version protocolaire compris, sur l'ensemble des ponts de l'épopée.
- Certification du cycle de vie complet des tâches asynchrones : ouverture, consultation d'état, collecte de verdict et annulation.
- Certification du rendu des deux ressources d'affichage officielles dans un cadre sandboxé reproduisant l'enveloppe de l'IDE, avec une interaction de base et un aller-retour de message de changement de projet sans rechargement.
- Certification de l'élicitation de formulaires et de la reprise d'exécution, ainsi que de l'exposition du catalogue de compétences.
- Certification de la dégradation gracieuse pour un client hérité ou un client dépourvu des extensions modernes.
- Certification de la non-régression de l'ensemble des tests du framework sur un compteur de collecte dynamique, ainsi que du respect de la limite d'isolement des modules de pont.
- Certification d'intégration du transport par sous-processus, bornée dans le temps et isolée par test.
- Intégration du contrôle des ponts au contrôle pré-vol déterministe et production du rapport de certification.
- Protocole d'audit manuel périodique des trois IDE réels, avec consignation des limites admises au rapport.

### Out-of-Scope
- L'automatisation de la simulation d'un IDE réel : la vérification d'un rendu produit par un client hôte demeure un audit manuel périodique, jamais un contrôle d'intégration continue.
- La répartition de la suite de tests en tranches parallèles (sharding) : la certification exécute la suite intégrale dans son périmètre.
- La correction des anomalies révélées par la certification : le harnais constate et rapporte, la réparation relève des récits concernés.
- Les tests de charge multi-nœuds distribués à grande échelle, qui dépassent le cadre d'un usage d'équipe locale.
- Toute surface applicative nouvelle : le harnais produit un rapport en sortie de commande, sans écran ni interface graphique propre.

---

## Critères d'acceptation

*Règle conditionnelle `layer: fullstack` (ADR-0366) : l'ensemble des sections est renseigné avec symétrie stricte interface / services (ADR-0319) — la surface de certification et les opérations de certification couvrent le même périmètre, niveau par niveau.*

### Spécifications de l'Interface & UX *(frontend / fullstack)*
- **Macrostructure & États de surface** : La surface de certification respecte les 4 états de surface : Initial/Vide (aucune certification exécutée : le rapport annonce l'absence d'exécution), Chargement (certification en cours, niveaux déroulés un à un avec compteurs vivants), Erreur (au moins un contrôle en échec : verdict non conforme, liste nominative des contrôles défaillants et diagnostic de chacun) et Succès (verdict conforme publié avec le compteur de collecte du moment).
- **États d'Interaction (signifiants)** : La certification se déclenche en une passe, sans formulaire ni saisie ; aucun état de survol ni de focus n'est contracté, la restitution étant une sortie de commande en lecture seule ; le re-lancement intégral reste possible après un verdict non conforme ; aucun contrôle isolé ne peut être acquitté pour faire basculer le verdict global.
- **Feedback Utilisateur** : Indicateur d'exécution et compteurs vivants pendant le déroulement, verdict final explicite en fin de passe, journal structuré détaillant chaque contrôle, rappel du compteur de collecte du moment, liste des limites admises (audit manuel de niveau 3, dépendance de navigateur à verrouiller) et diagnostic nominatif de tout contrôle non exécutable.

### Opérations Métier & Logique Backend *(backend / fullstack)*
#### 1. Certification nominale des échanges de la révision moderne (niveau 1, boucle en mémoire)
* **Entrée Métier** : Les jeux d'échanges des ponts de l'épopée, transmis avec la révision de référence, la méthode visée et le nom d'outil lorsqu'il s'agit d'un appel d'outil.
* **Règles d'admissibilité & Validation** : Tout échange réseau porte l'en-tête de version attendu ; toute version déclarée appartient au registre des versions prises en charge ; sur le transport stdio, les informations de routage accompagnent le message et aucun en-tête réseau n'y est fabriqué ; la révision antérieure reste recevable sans échec.
* **Traitement & Algorithme Métier** : Les entrées et sorties du pont sont simulées en mémoire et injectées dans sa boucle d'échanges ; les trames produites sont lues et confrontées aux contrats attendus, sans lancer de sous-processus, sans écrire le moindre fichier et sans poser le moindre verrou.
* **Résultat Métier & Mutations** : Un verdict par pont et par primitive certifiée, détaillé contrôle par contrôle ; aucun état persistant n'est créé et aucun artefact n'est laissé sur le disque.
* **Cas de Rejet Métier** : Un échange non conforme — version hors registre, en-tête absent là où il est obligatoire, information de routage manquante, charge non conforme — fait échouer le contrôle correspondant ; l'échec est signalé et les contrôles suivants poursuivent, sans interruption de la certification.

#### 2. Certification du rendu des ressources d'affichage en cadre sandboxé (niveau 1, fixture navigateur)
* **Entrée Métier** : Les deux ressources officielles d'affichage, servies avec leur contenu autonome, telles qu'un client hôte les recevrait.
* **Règles d'admissibilité & Validation** : Un test par ressource ; l'enveloppe du cadre reproduit fidèlement celle de l'IDE, scripts internes autorisés et politique de sécurité du contenu identique ; aucune requête sortante n'est tolérée en dehors des origines internes de la page ; une interaction de base doit aboutir sur chaque ressource ; un aller-retour de message de changement de projet doit être reçu sans rechargement.
* **Traitement & Algorithme Métier** : Le contenu est chargé dans une page vierge, le cadre sandboxé est ouvert, les requêtes réseau émises sont écoutées pendant toute la vie du test, l'interaction est déclenchée, puis le message de changement de projet est émis et sa prise en compte mesurée en l'absence de rechargement.
* **Résultat Métier & Mutations** : Un verdict par ressource, attestant du rendu, de l'isolation réseau, de l'interaction et de l'aller-retour du message ; aucun état n'est conservé d'un test à l'autre.
* **Cas de Rejet Métier** : Une ressource absente du registre des adresses, un contenu non autonome, une requête sortante détectée ou un rechargement inopiné font échouer le contrôle de la ressource concernée, avec diagnostic nominatif ; aucun contrôle n'est sauté silencieusement.

#### 3. Certification d'intégration du transport par sous-processus (niveau 2, un à deux contrôles)
* **Entrée Métier** : Une session de pont réellement lancée, avec ses entrées et ses sorties redirigées, telle qu'un client la verrait.
* **Règles d'admissibilité & Validation** : Chaque lancement porte un délai maximal d'exécution explicite ; chaque test dispose de son propre répertoire de travail ; l'usage d'un fichier de journal partagé et le recours au sous-système Linux sur Windows sont interdits.
* **Traitement & Algorithme Métier** : Le pont est démarré, les échanges sont écrits sur son entrée, les réponses sont lues depuis sa sortie, puis il est arrêté dans le délai imparti ; à l'issue, le répertoire de travail du test est libéré sans verrou résiduel.
* **Résultat Métier & Mutations** : La preuve que la boucle réelle du transport respecte les contrats déjà certifiés en mémoire ; aucun fichier commun n'est produit entre les exécutions.
* **Cas de Rejet Métier** : Le dépassement du délai maximal arrête le contrôle avec un constat et un diagnostic explicites ; jamais d'attente indéfinie, jamais d'échec muet.

#### 4. Certification de non-régression de la suite et de la dégradation gracieuse
* **Entrée Métier** : L'ensemble des tests du framework, plus les scénarios d'échange hérité et d'extension non négociée.
* **Règles d'admissibilité & Validation** : Le verdict de non-régression s'appuie exclusivement sur le compteur de collecte du moment, aucun chiffre de référence n'étant admis ; le client hérité obtient une réponse synchrone standard accompagnée d'une adresse locale ou du texte brut, sans échec d'appel ; chaque module de pont reste sous la limite d'isolement convenue en lignes et en poids.
* **Traitement & Algorithme Métier** : Les tests sont collectés puis exécutés intégralement ; le verdict de collecte et le verdict d'exécution sont rapprochés des scénarios de repli ; la structure de chaque module de pont est mesurée.
* **Résultat Métier & Mutations** : Un verdict unique de non-régression adossé au compteur du moment, complété par le constat de repli gracieux et par le respect de l'isolement des modules.
* **Cas de Rejet Métier** : Tout test en échec refuse le verdict de non-régression ; le rapport nomme le contrôle défaillant et le compteur constaté, sans jamais le figer dans un critère.

#### 5. Intégration au contrôle pré-vol & production du rapport de certification
* **Entrée Métier** : Le déclencheur habituel du contrôle pré-vol déterministe et l'issue des certifications des niveaux 1 et 2.
* **Règles d'admissibilité & Validation** : Le contrôle des ponts rejoint l'ensemble des contrôles déjà en service, sans porte d'entrée secondaire ; le rapport publie le verdict, les compteurs du moment, le journal structuré et les limites admises ; une dépendance d'exécution absente est un échec explicite, jamais un saut silencieux.
* **Traitement & Algorithme Métier** : Les issues des contrôles sont agrégées en un verdict unique, les compteurs sont relus à l'instant de la publication et les limites d'observation non couvertes par la machine sont recopiées dans le rapport.
* **Résultat Métier & Mutations** : Un rapport de certification opposable, conservé avec l'exécution qui l'a produit, lisible du même regard que les autres contrôles du pré-vol.
* **Cas de Rejet Métier** : Une dépendance d'exécution manquante ou un niveau non déclenchable produit un échec nominatif assorti de son diagnostic ; un rapport sans verdict publié est considéré comme non conforme.

### Maquettes SSOT *(frontend / fullstack)*
- 🔗 **Maquette Validée (SSOT)** : N/A — harnais de certification sans écran applicatif.
- 📂 **Actif Local Ingéré** : N/A — aucun actif de maquette n'est contracté pour ce récit.
- 📌 **Ajustements Visuels Validés** : N/A — aucune surface visuelle n'est à ajuster ; la restitution du verdict s'effectue en sortie de commande.

---

## Parcours Interactif & API

### Parcours Interactif (Frontend / Déclencheurs UI)
> *Cartographie exhaustive des composants interactifs de la surface de certification et de leurs transitions d'état.*

| Élément UI | Déclencheur | Action Déclarative (Navigation / API) | Feedback & Changement d'État |
| :--- | :--- | :--- | :--- |
| Déclenchement de la certification | Exécution de la commande de certification | Déroulement séquentiel du niveau mémoire, du contrôle d'intégration, du contrôle de non-régression | État Chargement avec compteurs vivants, puis verdict final |
| Contrôle pré-vol déterministe | Déclencheur habituel du contrôle pré-vol | Exécution du contrôle des ponts au milieu des contrôles existants | Intégration du verdict des ponts au verdict global du pré-vol |
| Contrôle en échec dans le rapport | Lecture du rapport de certification | Affichage du diagnostic nominatif et du compteur concerné | État Erreur circonscrit au contrôle, re-lancement intégral possible |
| Rapport de certification publié | Fin d'exécution | Restitution du verdict, des compteurs du moment, du journal et des limites admises | État Succès (verdict conforme) ou État Erreur (liste des contrôles défaillants) |
| Absence d'exécution antérieure | Ouverture du rapport sans certification | Affichage de l'absence d'exécution | État Initial/Vide explicite, sans verdict présumé |

### Contrats d'Échange API (Backend / Services)
> *Règle Zéro Fausse Route : aucune route REST n'est définie par ce récit. Les seuls échanges sous certification sont les contrats du protocole MCP et le pont de messages entre la conversation et le cadre rendu.*

- **Négociation & routage (certifiés)** : échange d'initialisation et en-tête `MCP-Protocol-Version: 2026-07-28` sur les transports réseau, en-têtes de méthode et d'outil, informations de routage du message sur le transport stdio.
- **Cycle de vie des tâches (certifié)** : ouverture d'une tâche, consultation d'état, collecte de verdict et annulation.
- **Affichage embarqué (certifié)** : outil d'affichage d'architecture vers `ui://archify/cockpit` ; outil d'affichage de schéma relationnel vers `ui://drawdb/schema`.
- **Synchronisation du projet actif (certifiée)** : message `project_changed` de la conversation vers le cadre, mise à jour en place sans rechargement.
- **Élicitation (certifiée)** : demande de formulaire structurée, réponse utilisateur et reprise d'exécution.
- **Compétences (certifiées)** : liste du catalogue de compétences et chargement à la demande.
- **Mode hybride (certifié)** : sans extension moderne, réponse synchrone standard et remise d'une adresse locale ou du texte brut, jamais un échec d'appel.

> 📄 **Niveaux et dispositif de certification** : détail tranché en micro-grill 215-Q1 et 215-Q2 — voir [ADR-010](../../../docs/01-architecture/ADR-010_micro-grill_mloop-215-full__2_decisions.md).

> ⚠️ **Limites admises & questions ouvertes** : la simulation d'un IDE réel n'est pas automatisée dans ce récit et relève d'un audit manuel périodique assorti d'une consignation de limites — **OQ-215-01, à définir** (modalités, périodicité et responsabilité de l'audit manuel des trois IDE réels). La dépendance de navigateur requise par le niveau 1 est actuellement apportée par une dépendance indirecte et non verrouillée — **OQ-215-02, à définir** (version exacte à verrouiller avant le premier passage en intégration continue).

---

## Règles d'affaires

- **Compteur dynamique comme unique critère de non-régression** : le verdict de non-régression se lit sur le compteur de collecte du moment de l'exécution ; tout chiffre de référence figé est proscrit, la suite évoluant en permanence.
- **Isolation stricte des niveaux de preuve** : le niveau mémoire ne lance aucun sous-processus, n'écrit aucun fichier et ne pose aucun verrou ; le niveau d'intégration est borné par un délai explicite et un répertoire de travail unique ; la simulation d'un IDE réel reste un audit manuel, jamais un contrôle automatisé.
- **Un contrôle par ressource d'affichage** : chaque ressource officielle bénéficie de son propre contrôle, couvrant le rendu, l'isolation réseau, une interaction de base et un aller-retour de message de changement de projet sans rechargement.
- **Enveloppe de rendu fidèle à l'IDE** : le cadre de certification reproduit les autorisations de l'enveloppe de l'IDE hôte, sans l'élargir ; toute requête sortante depuis le contenu rendu constitue un échec.
- **Dégradation gracieuse non négociable** : un client hérité ou un client sans extension moderne obtient une réponse synchrone standard et une adresse locale ou du texte brut ; aucun échec d'appel n'est admis pour absence de support.
- **Non-régression multi-IDE** : aucun contrôle n'est propre à un seul IDE ; les trois IDE supportés sont couverts par les mêmes contrats certifiés et par l'audit manuel commun.
- **Isolement des modules de pont** : chaque module de pont reste sous la limite de structure convenue en lignes et en poids, mesurée dans le cadre de la certification.
- **Observabilité du verdict** : la certification publie un verdict unique, un journal structuré, les compteurs du moment et la liste des limites admises ; tout contrôle non exécutable est un échec nominatif assorti de son diagnostic.
- **Gestion des contenus et dépendances invalides** : une ressource hors registre, un contenu non autonome ou une dépendance d'exécution absente échouent leur contrôle avec diagnostic, sans interrompre les autres contrôles et sans saut silencieux.
- **Zéro prétendu d'observation** : le harnais n'affirme jamais avoir observé ce que la machine n'a pas observé ; les comportements non fabriquables en laboratoire sont consignés comme limites admises dans le rapport.

---

## Références

### 1. Preuves Amont & Traçabilité Factuelle
- 📂 **Dossier de Preuves Factuelles** : [`memory/evidence/MLOOP-215-FULL_fact_dossier.md`](../../memory/evidence/MLOOP-215-FULL_fact_dossier.md)

### 2. Spécifications & Modèles de Données SSOT
- 🏛️ **ADR d'Architecture (SSOT technique)** : [ADR-0387 — Intégration des Standards MCP Modernes 2026-07-28](../../../../standards/adr-system/0387-mcp-modern-spec-2026-07-28-tasks-ui-elicitation-architecture.md), Pilier 4 et §Conséquences & Non-Régression (mode hybride, isolement des modules de pont)
- 📋 **Cadrage Macro Grill (6 décisions)** : [ADR-004 — EPIC-21-MCP-MODERN-SUITE](../../../docs/01-architecture/ADR-004_epic-21-mcp-modern-suite_-_cadrage_macro_grill__6_decisions.md), décision Q6 (certification à deux temps : intégration continue déterministe et audit manuel des IDE réels)
- 📋 **Micro-Grill du récit (2 décisions)** : [ADR-010 — Micro-grill MLOOP-215-FULL](../../../docs/01-architecture/ADR-010_micro-grill_mloop-215-full__2_decisions.md)
- ⚙️ **Standards d'exécution** : [ADR-0369 — Robustesse Python & Gouvernance des Ressources](../../../../standards/adr-system/0369-python-senior-robustness-and-resource-governance.md) (délais explicites, ressources bornées) · [ADR-0385 — Falsification des Frontières d'Architecture](../../../../standards/adr-system/0385-protocole-falsification-frontieres-architecture-immunite-cognitive.md) (échelle de preuve à 3 niveaux)
- 📚 **Épopée de rattachement** : [EPIC-21 — MCP Modern Suite 2026Q4](../epics/epic_mcp_modern_suite_2026q4.md)

---

## Scénarios de test

```gherkin
# language: fr
Fonctionnalité: Harnais de Certification & Conformité E2E MCP 2026-07-28 & Non-Régression Multi-IDE

  # CHEMIN NOMINAL (Happy Path & Persistance)
  Scénario: Certification nominale des extensions modernes et verdict conforme
    Étant donné un jeu d'échanges transmis aux ponts mLoop avec la révision "2026-07-28"
    Et que les deux ressources d'affichage sont déclarées sous leurs adresses officielles
    Quand le harnais exécute le niveau de certification en mémoire puis le contrôle d'intégration borné
    Alors les échanges de négociation, de tâches, d'affichage, d'élicitation et de compétences sont certifiés
    Et le cadre de rendu est ouvert avec les mêmes autorisations que celles de l'IDE
    Et une interaction de base aboutit sur chaque ressource sans requête sortante
    Et l'aller-retour de message de changement de projet est reçu sans rechargement
    Et la suite complète du framework affiche zéro échec sur son compteur de collecte du moment
    Et le rapport publie un verdict conforme accompagné de ce compteur

  # EXCEPTIONS & REJETS MÉTIER (Règles d'affaires)
  Scénario: Rendu d'une ressource d'affichage indisponible pour le client hôte
    Étant donné un client hôte qui ne négocie pas l'extension d'affichage embarqué
    Quand l'outil d'affichage est invoqué pour l'une des deux ressources
    Alors l'adresse locale correspondante ou le texte brut de la ressource est remis en solution de secours
    Et l'appel aboutit sans erreur bloquante
    Et aucun rendu dans le cadre n'est prétendu

  Scénario: Ressource hors registre ou contenu non autonome
    Étant donné une ressource absente du registre des adresses officielles ou un contenu dépendant d'une source externe
    Quand le harnais tente d'en certifier le rendu
    Alors le contrôle de cette ressource échoue avec un diagnostic nominatif
    Et les autres contrôles de la certification poursuivent leur exécution
    Et aucun saut silencieux n'est enregistré dans le rapport

  # RÉSILIENCE TECHNIQUE & MODE DÉGRADÉ (Timeouts, Idempotence, Concurrence)
  Scénario: Dépassement de délai lors du lancement d'un pont en sous-processus
    Étant donné un contrôle d'intégration lançant un pont dont les entrées et les sorties sont redirigées
    Mais que le pont ne répond pas dans le délai maximal autorisé
    Quand la temporisation expire
    Alors le contrôle s'arrête avec un constat de dépassement de délai et un diagnostic
    Et aucune attente indéfinie n'est laissée ouverte
    Et le répertoire de travail propre au test est libéré sans verrou résiduel

  Scénario: Client hérité sans extension moderne certifié sans régression
    Étant donné un client déclarant une révision antérieure, dépourvu des extensions de tâches et d'affichage
    Quand le pont traite ses échanges
    Alors il bascule en mode synchrone standard et remet une adresse locale ou du texte brut
    Et aucun échec d'appel n'est produit pour absence de support
    Et les contrôles restent identiques pour les trois IDE supportés, sans contrôle propre à un seul d'eux

  Scénario: Audit manuel de niveau 3 des IDE réels hors du socle automatisé
    Étant donné que la simulation d'un IDE réel n'est pas automatisée dans ce récit
    Quand l'audit périodique des trois IDE réels est exécuté manuellement
    Alors ses constats et ses limites admises sont consignés dans le rapport de certification
    Et aucun prétendu d'exécution automatisée n'est affiché

  # UX, OBSERVABILITÉ & EMPTY STATE (Spinners, Retours Écran, Logs)
  Scénario: Restitution du rapport de certification et compteurs dynamiques
    Étant donné le déclenchement d'une certification ou l'absence d'exécution antérieure
    Quand la certification progresse à travers ses niveaux
    Alors un indicateur d'exécution et des compteurs vivants accompagnent le déroulement
    Et à l'issue, le rapport publie le verdict, le compteur de collecte du moment et le journal structuré
    Et les limites admises, dont l'audit manuel de niveau 3 et la dépendance de navigateur à verrouiller, figurent dans le rapport
    Et une dépendance d'exécution absente est signalée par un échec nominatif plutôt que par un saut silencieux
```