---
id: MLOOP-213-BE
jira_key: ''
epic_key: EPIC-21-MCP-MODERN-SUITE
type: Feature
title: 'Extension Elicitation : Formulaire Interactif Form Mode pour le Protocole
  Grill-with-Docs'
origin: DIRECT_REQUIREMENT
source_ref: ADR-0387
macro_size: S
status: DONE_TESTED
grill_me: DONE
layer: backend
invest_score: 6/6
blocked_by:
- MLOOP-210-BE
created_at: '2026-09-24'
content_hash: b210d1a966224f9d
---

# Extension Elicitation : Formulaire Interactif Form Mode pour le Protocole Grill-with-Docs

---

## Description
**En tant qu'** Agent de Planification (`plan`) et Ingénieur d'Exécution mLoop,
**je veux** que le protocole contradictoire *Grill-with-Docs* soumette ses arbitrages par l'extension d'élicitation en mode formulaire (*Form Mode*),
**afin de** présenter les questions d'arbitrage d'architecture et les choix de profils d'API sous forme de formulaires interactifs dans l'environnement de travail, sans retenir les sous-processus derrière des invites de commande impératives, tout en conservant de chaque arbitrage une trace de décision durable et relisible.

---

## Contexte & Périmètre

### Contexte Métier
Le protocole contradictoire *Grill-with-Docs* soumet à l'humain des arbitrages structurés avant qu'une spécification ne soit promue : choix entre deux profils d'API, validation de l'état de préparation d'un récit, arbitrage de complexité. Ces questions sont aujourd'hui posées par des invites de commande qui retiennent le sous-processus jusqu'au verdict, ce qui gèle la séance et empêche tout travail autonome. L'extension d'élicitation du protocole moderne inverse le rapport : l'agent publie la question sous forme de formulaire, l'environnement de travail la rend, la réponse revient structurée et la séance reprend. Le récit couvre la face serveur de cet échange — publier la question, tenir une attente suffisante à reconstruire le formulaire, enregistrer la décision de façon durable, et retomber proprement sur une question textuelle lorsque l'environnement ne sait pas servir de formulaire. La trace ainsi produite alimente les preuves du récit et la recherche documentaire ; la rédaction d'écrits d'architecture demeure réservée à son circuit dédié.

### In-Scope
- La définition des schémas d'élicitation standard du protocole : choix de profil d'API (Profil A contre Profil B), validation de l'état de préparation d'un récit, arbitrage de complexité selon les critères INVEST.
- La prise en charge de l'émission de la demande d'élicitation et de la réception de la réponse structurée de l'utilisateur.
- La tenue d'un état d'attente régénérable — identifiant, schéma et contexte suffisants à reconstruire le formulaire — sans le moindre état d'interface persistant, et sa suppression dès réception de la réponse.
- Le régime d'attente borné à cinq minutes : à l'expiration, la tâche ciblée passe en attente de saisie puis le formulaire est régénéré à la reconnexion, sans perte de contexte.
- Le repli textuel en Markdown lisible, sans erreur bloquante, lorsque l'environnement n'offre pas l'élicitation.
- L'enregistrement synchrone d'une ligne de décision dans `Projects/<projet>/memory/evidence/decision_records.jsonl` (fichier ajouté en fin, jamais modifié), formule de formulaire et repli textuel empruntant le même chemin.
- La détection « déjà répondu » fondée sur la présence au registre de décisions, jamais sur l'état d'attente.
- L'intégration au module de grill existant `src/pipelines/grill_engine.py` et à son pont de conversation `src/bridges/mcp_loop_mem.py`, sans création de module parallèle.
- La livraison inchangée des consommateurs aval : le paquet de preuves du récit et le journal de recherche factuelle continuent de lire leurs sources sans modification de contrat.

### Out-of-Scope
- Le mode URL hors-bande (*URL Mode*), prévu pour des encaissements, sans objet dans le cycle de vie de mLoop.
- Le rendu du formulaire lui-même : la présentation appartient à l'environnement hôte ; le récit livre la demande structurée et recueille la réponse.
- La rédaction d'écrits d'architecture depuis un formulaire : le registre de décisions n'écrit jamais dans le catalogue des décisions d'architecture.
- La purge, la rétention et le découpage temporel du registre de décisions, confiés au chantier de rétention dédié.
- L'ouverture de la moindre route réseau : seuls les échanges du protocole de conversation entrent en jeu.

---

## Critères d'acceptation

*Règle conditionnelle `layer: backend` (ADR-0366) : seules les Opérations Métier & Logique Backend (5 sous-titres normés) et les Contrats d'Échange API sont renseignés ; les sections frontend sont non applicables — le widget est rendu par l'environnement hôte.*

### Opérations Métier & Logique Backend *(backend / fullstack)*
#### 1. Émission d'une question d'arbitrage en mode formulaire
* **Entrée Métier** : une question d'arbitrage issue du protocole contradictoire (profil d'API, état de préparation, complexité), le récit traité, le contexte documentaire qui l'appuie, et les capacités déclarées par l'environnement de travail.
* **Règles d'admissibilité & Validation** : l'environnement doit avoir négocié l'extension d'élicitation du socle protocolaire ; la question doit porter un schéma JSON-Schema complet à options fermées ; une question dont la réponse figure déjà au registre de décisions n'est jamais reposée.
* **Traitement & Algorithme Métier** : la charge utile est construite à partir de l'identifiant, du schéma et du contexte, puis remise à l'environnement ; en parallèle, l'état d'attente est conservé sous la même forme régénérable, sans aucun état de widget persistant ; seule la tâche ciblée reste suspendue — le compagnon de travail et le fil principal poursuivent leur route.
* **Résultat Métier & Mutations** : la question est servie en mode formulaire ; un état d'attente portable d'un environnement à l'autre subsiste, suffisant à reconstruire le formulaire à l'identique ; aucune donnée d'interface n'est persistée.
* **Cas de Rejet Métier** : un environnement dépourvu d'élicitation ne subit aucun refus — la question part immédiatement en repli textuel ; une question dépourvue de schéma complet ou d'options fermées n'est pas émise et reste en attente de cadrage.

#### 2. Attente bornée, expiration en attente de saisie et régénération
* **Entrée Métier** : une question émise et demeurée sans réponse, l'horodatage d'émission, le délai maximal de cinq minutes.
* **Règles d'admissibilité & Validation** : l'expiration ne survient qu'après l'écoulement intégral du délai sur une question toujours sans réponse ; elle ne vaut ni échec ni abandon ; la détection d'une réponse déjà tranchée interroge le registre de décisions, jamais l'état d'attente.
* **Traitement & Algorithme Métier** : à l'expiration, la tâche ciblée passe en attente de saisie et l'état d'attente est conservé intact ; à la reconnexion, le formulaire est reconstruit depuis l'identifiant, le schéma et le contexte ; une réponse tardive est traitée exactement comme une réponse ordinaire.
* **Résultat Métier & Mutations** : la tâche expose l'attente d'une réponse humaine, le formulaire est de nouveau servi, le contexte d'arbitrage est préservé ; la seule mutation est le changement d'état de la tâche ciblée.
* **Cas de Rejet Métier** : aucun rejet à l'expiration ; une reprise au cours de laquelle le registre porte déjà la réponse n'ouvre ni nouvelle attente ni seconde écriture.

#### 3. Réception de la réponse et levée de l'attente
* **Entrée Métier** : la réponse structurée remontée par le formulaire — identifiant d'élicitation, valeur retenue, auteur de la réponse.
* **Règles d'admissibilité & Validation** : la réponse doit correspondre à une attente en cours et respecter le schéma émis ; une question déjà inscrite au registre de décisions ne reçoit jamais d'ouverture complémentaire.
* **Traitement & Algorithme Métier** : contrôle de la réponse contre le schéma, écriture synchrone de la ligne de décision, suppression de l'état d'attente, remise en route de la tâche ciblée — cette séquence est tout-ou-rien, sans état intermédiaire visible.
* **Résultat Métier & Mutations** : la décision est durablement tracée, l'état d'attente disparaît, la continuation de l'agent reprend sans perte de contexte.
* **Cas de Rejet Métier** : valeur hors schéma, identifiant inconnu ou auteur absent → refus explicite, sans écriture aucune et sans suppression de l'attente.

#### 4. Écriture synchrone du registre de décisions
* **Entrée Métier** : l'achèvement d'un formulaire ou la réponse recueillie par repli textuel, accompagnés du récit traité.
* **Règles d'admissibilité & Validation** : la ligne porte obligatoirement l'identifiant d'élicitation, le récit, la question, la réponse, l'auteur, la date et l'indicateur de repli ; la référence d'architecture est facultative ; les deux provenances empruntent exactement le même chemin d'écriture.
* **Traitement & Algorithme Métier** : une ligne unique et immuable est ajoutée en fin du fichier `Projects/<projet>/memory/evidence/decision_records.jsonl`, en format déclaratif ligne à ligne, sans moteur de base de données, sans mise à jour ni remplacement d'une ligne antérieure ; l'écriture est synchrone et intervient avant le déblocage de la tâche.
* **Résultat Métier & Mutations** : le registre s'allonge d'une preuve d'audit par décision ; le paquet de preuves et le journal de recherche factuelle lisent ce registre sans changement de contrat ; aucune écriture d'architecture n'en découle.
* **Cas de Rejet Métier** : une ligne incomplète n'est pas ajoutée ; une seconde réponse à une question déjà tranchée n'ajoute aucune ligne ; aucun enregistrement n'est ouvert lorsqu'une réponse a été refusée.

#### 5. Repli textuel en l'absence d'élicitation
* **Entrée Métier** : une question à poser à un environnement qui n'a pas négocié l'élicitation.
* **Règles d'admissibilité & Validation** : la question doit être lisible seule en Markdown ; l'absence de capacité n'est jamais un refus et ne met jamais la séance en échec.
* **Traitement & Algorithme Métier** : la question est retranscrite dans la conversation, la réponse textuelle qui suit est recueillie, puis la même écriture de ligne de décision qu'en mode formulaire est exécutée avec l'indicateur de repli posé ; l'état d'attente est écarté puisque la question ne repose pas sur un formulaire.
* **Résultat Métier & Mutations** : l'arbitrage est tracé avec la même structure que s'il était servi en formulaire, la séance reprend, et aucune erreur bloquante n'est produite.
* **Cas de Rejet Métier** : aucun — le repli ne rejette jamais ; seule l'absence de réponse laisse la question ouverte.

### Maquettes SSOT *(frontend / fullstack)*
N/A — Composant Headless : le widget est rendu par l'environnement hôte à partir de la demande structurée.

---

## Parcours Interactif & API

### Parcours Interactif (Frontend / Déclencheurs UI)
N/A — Composant backend : aucun déclencheur d'interface n'est implémenté ici ; la présentation du formulaire et la remontée de la réponse appartiennent à l'environnement hôte.

### Contrats d'Échange API (Backend / Services)
> *Règle Zéro Fausse Route : aucune route REST n'est définie par ce récit. Les seuls contrats sont les échanges JSON-RPC du protocole MCP et le registre de décisions local.*

- **Demande d'élicitation (mode formulaire)** : `elicitation/create` (JSON-RPC) — charge utile portant l'identifiant d'élicitation, le schéma JSON-Schema de la question et le contexte d'arbitrage ; l'environnement hôte en déduit l'affichage du widget interactif.
- **Réponse d'élicitation** : retour de l'échange d'élicitation — identifiant repris et valeur retenue, validés contre le schéma émis avant toute écriture.
- **Suspension de la tâche ciblée** : passage à l'état `input_required` de l'extension de tâches à l'expiration des cinq minutes d'attente, puis régénération du formulaire à la reconnexion.
- **Registre de décisions** : `Projects/<projet>/memory/evidence/decision_records.jsonl` — artefact de persistance locale ajouté en fin, ligne portant identifiant d'élicitation, récit, question, réponse, auteur, date, indicateur de repli et, le cas échéant, référence d'architecture ; ce n'est ni une route ni un service réseau.
- **Repli textuel** : aucun contrat réseau dédié — la question est retranscrite dans la conversation et la réponse y est recueillie, puis écrite par le même chemin que le formulaire.

> 📄 **Spécifications formelles détaillées** : Pilier 3 de [ADR-0387 — Intégration des Standards MCP Modernes 2026-07-28 (Tasks, MCP Apps, Elicitation & Header Routing)](../../../../standards/adr-system/0387-mcp-modern-spec-2026-07-28-tasks-ui-elicitation-architecture.md). Aucune route REST n'est ouverte par le présent récit.

> ⚠️ **Exemption de matrice REST (ADR-0319)** : ce récit n'ouvre aucune route HTTP REST — seuls les échanges JSON-RPC du protocole MCP déclarés ci-dessus s'appliquent. Deux questions ouvertes demeurent : **OQ-213-01** — le payload exact `elicitation/create` de la spécification externe du 2026-07-28 n'a pas été vérifié en interne ; la charge utile exacte est **à définir** avant le build (falsification documentaire du cadrage macro), écart consigné sans bloquer. **OQ-213-02** — l'expiration réelle du minuteur de cinq minutes appartient au runtime de l'environnement hôte et n'est pas contrôlable depuis le pont ; le comportement réel de l'hôte est à confirmer sur les environnements cibles, sans bloquer le présent récit.

---

## Règles d'affaires

- **Entrée de formulaire exprimée en schéma** : toute question d'élicitation est remise comme schéma JSON-Schema — identifiant, schéma et contexte suffisent à reconstruire le formulaire ; aucun état d'interface n'est conservé d'une séance à l'autre.
- **Attente régénérable** : l'état d'attente survit à la fermeture de la séance ; à la reconnexion, le formulaire est régénéré à l'identique, sans perte du contexte d'arbitrage.
- **Attente levée par la réponse** : l'état d'attente est supprimé dès réception de la réponse ; il ne sert jamais de preuve qu'une question a été tranchée.
- **Preuve de réponse unique** : la détection « déjà répondu » s'appuie uniquement sur la présence d'une ligne au registre de décisions ; une question déjà tranchée n'est jamais reposée.
- **Registre de décisions ajouté en fin, jamais réécrit** : chaque décision ajoute une ligne unique et immuable portant identifiant d'élicitation, récit, question, réponse, auteur, date, indicateur de repli et, le cas échéant, la référence d'architecture ; aucune ligne n'est mise à jour, remplacée ni supprimée.
- **Un seul chemin d'écriture, deux provenances** : la complétion du formulaire et celle du repli textuel empruntent exactement le même chemin d'écriture ; seul l'indicateur de repli distingue les deux provenances.
- **Rédaction d'architecture réservée** : le registre de décisions n'écrit jamais dans le catalogue des décisions d'architecture ; la consignation d'un écrit d'architecture reste l'apanage de la fonction dédiée du module de grill.
- **Bornage de l'attente** : cinq minutes sans réponse font passer la tâche ciblée en attente de saisie, sans échec ni abandon ; la reprise régénère le formulaire et la réponse tardive vaut réponse ordinaire.
- **Repli jamais bloquant** : sans élicitation côté environnement, la question est retranscrite en Markdown lisible et la séance reprend sans la moindre erreur bloquante.
- **Consommateurs inchangés** : le paquet de preuves du récit et le journal de recherche factuelle lisent le registre de décisions sans modification de leur contrat.
- **Gestion des données invalides** : une réponse hors schéma, un identifiant inconnu, un auteur absent ou une ligne incomplète sont refusés sans écriture partielle ; une seconde réponse à la même question n'ajoute pas de ligne supplémentaire.

---

## Références

### 1. Preuves Amont & Traçabilité Factuelle
- 📂 **Dossier de Preuves Factuelles** : [`memory/evidence/MLOOP-213-BE_fact_dossier.md`](../../memory/evidence/MLOOP-213-BE_fact_dossier.md)
- 🏛️ **Décisions du micro-grill du récit** : [ADR-008 — Micro-grill MLOOP-213-BE (2 décisions)](../../../docs/01-architecture/ADR-008_micro-grill_mloop-213-be__2_decisions.md)

### 2. Spécifications & Modèles de Données SSOT
- 📜 **SSOT technique** : [ADR-0387 — Intégration des Standards MCP Modernes 2026-07-28 (Tasks, MCP Apps, Elicitation & Header Routing)](../../../../standards/adr-system/0387-mcp-modern-spec-2026-07-28-tasks-ui-elicitation-architecture.md)
- 📜 **Cadrage macro de l'épopée** : [ADR-004 — EPIC-21-MCP-MODERN-SUITE : cadrage macro Grill (6 décisions)](../../../docs/01-architecture/ADR-004_epic-21-mcp-modern-suite_-_cadrage_macro_grill__6_decisions.md)
- 🧩 **Ancrage code** : `src/pipelines/grill_engine.py` — module réel du protocole de grill, point d'intégration unique (drift de chemin du cadrage corrigé avant plan d'implémentation), et `src/bridges/mcp_loop_mem.py` pour la remise des échanges.
- 🏛️ **Modèle de Données SSOT** : structure de l'état d'attente et de la ligne de décision dans le dossier de preuves (§ Schéma de données).

### 3. Épopée de rattachement
- 📄 **Épopée** : [`backlog/epics/epic_mcp_modern_suite_2026q4.md`](../epics/epic_mcp_modern_suite_2026q4.md)

---

## Scénarios de test

```gherkin
# language: fr
Fonctionnalité: Extension Elicitation : Formulaire Interactif Form Mode pour le Protocole Grill-with-Docs

  # 1. CHEMIN NOMINAL (Happy Path & Persistance)
  Scénario: Question d'arbitrage servie en formulaire puis décision tracée
    Étant donné un environnement de travail ayant négocié l'extension d'élicitation
    Et qu'une question du protocole contradictoire porte un schéma JSON-Schema complet à options fermées
    Quand l'agent émet la demande d'élicitation en mode formulaire
    Alors l'environnement affiche un widget interactif bloquant uniquement la tâche ciblée
    Et un état d'attente régénérable conserve l'identifiant, le schéma et le contexte
    Quand l'utilisateur retient une option et confirme la soumission
    Alors la réponse est contrôlée contre le schéma émis
    Et une ligne de décision est écrite de façon synchrone dans le registre de décisions avec l'indicateur de repli à faux
    Et l'état d'attente est supprimé
    Et la continuation de l'agent reprend sans perte de contexte

  # 2. EXCEPTIONS & REJETS MÉTIER (Règles d'affaires)
  Scénario: Expiration de l'attente après cinq minutes puis reprise du formulaire
    Étant donné une question d'élicitation émise et demeurée sans réponse
    Quand le délai maximal de cinq minutes est atteint
    Alors la tâche ciblée passe en attente de saisie
    Et l'état d'attente demeure persistant sans échec ni abandon
    Quand l'utilisateur revient après expiration
    Alors le formulaire est régénéré à l'identique depuis l'identifiant, le schéma et le contexte
    Et la réponse tardive écrit une ligne de décision unique

  Scénario: Rejet d'une réponse incompatible avec le schéma émis
    Étant donné une question en attente définissant des options fermées
    Quand une réponse propose une valeur hors schéma ou porte un identifiant inconnu
    Alors la réponse est refusée avec un motif explicite
    Et aucune ligne n'est ajoutée au registre de décisions
    Et l'état d'attente demeure en place

  # 3. RÉSILIENCE TECHNIQUE & MODE DÉGRADÉ (Timeouts, Idempotence, Concurrence)
  Scénario: Régénération du formulaire après reconnexion de la séance
    Étant donné un état d'attente conservé après la fermeture de la séance
    Quand l'agent se reconnecte avant toute réponse
    Alors le formulaire est régénéré à l'identique depuis l'identifiant, le schéma et le contexte
    Et aucun état d'interface persistant n'est requis pour cette régénération

  Scénario: Repli textuel sur un environnement sans élicitation
    Étant donné un environnement qui n'a pas négocié l'élicitation
    Quand une question d'arbitrage doit être posée
    Alors la question est retranscrite en Markdown lisible sans erreur bloquante
    Et la réponse textuelle est écrite dans le registre de décisions par le même chemin que le formulaire
    Et l'indicateur de repli vaut vrai

  Scénario: Question déjà tranchée jamais reposée
    Étant donné une question dont la réponse figure déjà au registre de décisions
    Quand l'agent prépare une nouvelle sollicitation pour ce même arbitrage
    Alors la présence au registre fait foi de réponse
    Et aucune nouvelle demande d'élicitation n'est émise
    Et aucun état d'attente n'est rouvert

  # 4. UX, OBSERVABILITÉ & EMPTY STATE (Spinners, Retours Écran, Logs)
  Scénario: Widget interactif et retour de soumission
    Étant donné une question servie en mode formulaire dans un environnement compatible
    Quand l'utilisateur sélectionne une option et confirme la soumission
    Alors le widget présente un retour de soumission puis se referme
    Et la tâche ciblée reprend sans geler le compagnon de travail ni le fil principal
    Et la décision figure au registre de décisions avec son auteur et sa date

  Scénario: Traçabilité unifiée des deux provenances de décision
    Étant donné un jeu de décisions mêlant complétions de formulaire et replis textuels
    Quand le registre de décisions est consulté
    Alors chaque ligne porte l'identifiant d'élicitation, le récit, la question, la réponse, l'auteur et la date
    Et l'indicateur de repli distingue les deux provenances
    Et aucune ligne n'a été mise à jour ni supprimée
```