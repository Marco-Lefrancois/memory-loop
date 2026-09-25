---
id: MLOOP-211-BE
jira_key: ''
epic_key: EPIC-21-MCP-MODERN-SUITE
type: Feature
title: 'Extension Tasks (io.modelcontextprotocol/tasks) : Handles Asynchrones & Call-Now-Fetch-Later
  pour Herdr'
origin: DIRECT_REQUIREMENT
source_ref: ADR-0387
macro_size: M
status: DONE_TESTED
layer: backend
invest_score: 6/6
blocked_by:
- MLOOP-210-BE
created_at: '2026-09-24'
ttl_cycles: 4
---

# Extension Tasks (io.modelcontextprotocol/tasks) : Handles Asynchrones & Call-Now-Fetch-Later pour Herdr

---

## Description
**En tant qu'** Orchestrateur mLoop et Agent Worker,
**je veux** que les opérations longues (lancement de compagnons de travail, exécutions de tests étendus, audits multi-récits) me remettent immédiatement un identifiant de tâche durable au lieu de captiver la session jusqu'au verdict,
**afin d'** éliminer définitivement les dépassements de délais et de pouvoir suivre, interrompre ou consulter à mon rythme un travail poursuivi hors de la conversation.

---

## Contexte & Périmètre

### Contexte Métier
Une part croissante des travaux confiés aux agents dépasse le temps de réponse qu'un échange simple supporte. Tant que ce travail n'a pas rendu son verdict, la session qui l'a déclenchée reste captive : elle peut ni constater l'avancement, ni solliciter une réponse à mi-parcours, ni retirer une demande devenue inutile. Le mode « appeler maintenant, consulter ensuite » met fin à cette captivité : l'orchestrateur reçoit à l'instant un identifiant de tâche durable, le travail poursuit sa route hors de la conversation, et l'orchestrateur reprend la main quand bon lui semble — lire l'avancement, répondre à une sollicitation, désister la demande ou recueillir le verdict. Chaque changement d'état lui est poussé dès qu'il survient, sans qu'il ait jamais à sonder. Le récit établit également la date au-delà de laquelle un verdict éteint devient jetable, tout en laissant le nettoyage physique à un chantier de rétention distinct.

### In-Scope
- Les quatre primitives d'échange de l'extension `io.modelcontextprotocol/tasks` : `tasks/create`, `tasks/status`, `tasks/cancel`, `tasks/result`, en JSON-RPC.
- Le vocabulaire fermé des cinq états de cycle de vie : `working`, `input_required`, `completed`, `failed`, `cancelled`, en mapping direct avec le cycle de vie des compagnons de travail déjà en service.
- L'enregistrement durable des identifiants de tâches sous `Projects/<projet>/memory/tasks/`, avec horodatage d'ouverture, état courant, échéance de rétention, identifiant du sous-processus et rattachement au récit traité.
- La déclaration du contrat d'échéance de rétention (date d'ouverture augmentée de la durée nommée dans le registre de constantes partagé avec le socle protocolaire), calculée uniquement à l'atteinte d'un état terminal.
- La poussée de l'évènement `notifications/tasks/updated` (charge utile : identifiant de tâche, état, échéance) sur le bus d'évènements en flux continu déjà en service, avec repli de transport par piggyback dans les métadonnées de routage (`_meta.routing`) pour un client sans abonnement.
- L'intégration transparente à la commande de lancement de compagnons de travail (`worker-spawn`) sans faire régresser le cycle de lancement, de collecte et de nettoyage existant.

### Out-of-Scope
- La suppression physique des fichiers de tâches et la politique globale de rétention : le présent récit se borne à rendre l'échéance lisible, sans exécuter, planifier ni déléguer la moindre purge.
- Les webhooks push distants : la première mouture s'appuie exclusivement sur l'échange JSON-RPC local et sur la poussée d'évènements du bus existant.
- Tout sondage proactif d'état : l'orchestrateur ne sollicite jamais l'état de manière périodique, il reçoit les transitions ou lit l'état à sa demande.
- L'interface de saisie des réponses d'arbitrage elle-même : seul l'état d'attente d'une réponse humaine et sa notification entrent dans le présent récit.
- Toute interface graphique : le récit est un composant sans surface visuelle.
- L'ouverture de la moindre route réseau au-delà des primitives de l'extension Tasks.

---

## Critères d'acceptation

### Opérations Métier & Logique Backend *(backend / fullstack)*
#### 1. Ouverture d'une tâche et remise immédiate d'un identifiant durable
* **Entrée Métier** : demande d'exécution d'un travail long, rattachement au récit traité, paramètres d'exécution déclarés, commande de lancement d'un compagnon de travail.
* **Règles d'admissibilité & Validation** : la demande ne peut viser qu'une tâche nouvelle ; toute ouverture s'appuyant sur une tâche déjà venue à un état terminal ou dont l'état déclaré appartient au vocabulaire fermé est refusée ; la réponse doit être rendue sous le seuil des cinq cents millisecondes, sans quoi le travail n'est pas engagé.
* **Traitement & Algorithme Métier** : déclaration immédiate de la tâche, lancement du sous-processus par le cycle de lancement existant sans attendre sa fin, écriture atomique de l'enregistrement (identifiant unique, état initial, horodatage d'ouverture, échéance nulle, identifiant du sous-processus, rattachement), sans verrou sur la session appelante.
* **Résultat Métier & Mutations** : un identifiant de tâche unique est retourné dans la foulée ; l'état initial est `working`, ou `input_required` si une réponse humaine est déjà requise ; l'échéance reste nulle tant que la tâche vit ; le sous-processus poursuit sa route de façon autonome.
* **Cas de Rejet Métier** : rejet si la demande s'appuie sur une tâche à état terminal ; rejet si l'état déclaré sort du vocabulaire fermé des cinq états ; rejet si le seuil de réponse immédiate est franchi, auquel cas aucune tâche n'est enregistrée et aucun sous-processus n'est lancé.

#### 2. Interrogation d'avancement sans blocage
* **Entrée Métier** : identifiant de la tâche suivie, position de lecture déjà connue par l'interrogateur.
* **Règles d'admissibilité & Validation** : l'identifiant doit désigner une tâche encore conservée ; l'interrogation n'attend jamais le verdict et ne pose aucun verrou sur le sous-processus.
* **Traitement & Algorithme Métier** : lecture de l'état courant et restitution du fragment de journal produit depuis la position de lecture connue (lecture incrémentale), sans consommation ni altération du journal.
* **Résultat Métier & Mutations** : l'état courant et le fragment de journal nouveau sont rendus immédiatement ; la tâche n'est en rien modifiée.
* **Cas de Rejet Métier** : rejet si l'identifiant est inconnu ou si la tâche a été emportée par le chantier de rétention ; rejet de toute interrogation exigeant le verdict : elle renvoie l'état, jamais le verdict.

#### 3. Désistement d'une tâche en cours
* **Entrée Métier** : identifiant de la tâche, motif de désistement.
* **Règles d'admissibilité & Validation** : le désistement n'est recevable que sur une tâche encore active (`working` ou `input_required`) ; le verdict d'une tâche déjà éteinte fait foi et ne peut être défait ; seul un sous-processus rattaché au cycle de suivi peut être arrêté, jamais un processus étranger.
* **Traitement & Algorithme Métier** : ordre d'arrêt transmis au sous-processus, attente bornée de son extinction, libération des ressources suivies, transition vers `cancelled`, puis calcul de l'échéance de rétention à partir de l'horodatage d'ouverture.
* **Résultat Métier & Mutations** : la tâche porte l'état `cancelled`, son échéance de rétention est renseignée, aucun sous-processus orphelin ne subsiste, et l'évènement de transition est publié.
* **Cas de Rejet Métier** : rejet du désistement d'une tâche déjà venue à un état terminal ; rejet si le sous-processus n'appartient plus au cycle de suivi ; rejet si l'identifiant est inconnu.

#### 4. Récupération du verdict d'une tâche éteinte
* **Entrée Métier** : identifiant de la tâche, échéance de rétention encore valide.
* **Règles d'admissibilité & Validation** : réservée aux tâches à état terminal ; tant que la tâche vit, le verdict n'est pas délivré ; une tâche dont l'échéance est dépassée n'est plus en mesure de livrer son verdict.
* **Traitement & Algorithme Métier** : collecte des livrables et preuves du travail achevé, restitution du journal complet, sans modification de l'état ni report de l'échéance.
* **Résultat Métier & Mutations** : le verdict est rendu selon l'état terminal — livrables en cas d'achèvement, cause en cas d'échec, motif en cas de désistement ; la tâche demeure telle quelle.
* **Cas de Rejet Métier** : rejet si la tâche est encore active ; rejet si l'identifiant est inconnu ; rejet si l'échéance de rétention est dépassée.

#### 5. Déclaration de l'échéance de rétention et notification de transition
* **Entrée Métier** : tâche venant de changer d'état, nouvel état, horodatage d'ouverture conservé, état d'abonnement du destinataire.
* **Règles d'admissibilité & Validation** : l'échéance n'est calculée que sur transition vers un état terminal, fixée à l'horodatage d'ouverture augmentée de la durée portée par le registre de constantes partagé avec le socle protocolaire, et recalculée à chaque nouvelle transition vers un état terminal ; les états actifs conservent une échéance nulle et ne sont jamais présentés comme purgeables ; une seule notification est émise par transition.
* **Traitement & Algorithme Métier** : écriture atomique de l'échéance dans l'enregistrement de la tâche, puis publication de l'évènement de transition (identifiant, état, échéance) sur le bus d'évènements en flux continu ; pour un client sans abonnement, l'état actualisé est piggybacké dans les métadonnées de routage de la prochaine réponse ; aucun sondage n'est initié à la place.
* **Résultat Métier & Mutations** : l'enregistrement de la tâche reflète l'échéance applicable ; l'orchestrateur abonné reçoit la poussée au moment exact de la transition ; le client silencieux est rattrapé à son prochain échange ; le flux principal n'attend jamais la file de notifications.
* **Cas de Rejet Métier** : rejet d'un calcul d'échéance sur un état actif ; rejet d'une seconde notification pour une même transition ; rejet de tout canal de notification hors du bus existant ; rejet d'une échéance calculée à partir d'une autre date que l'horodatage d'ouverture.

---

## Parcours Interactif & API

### Contrats d'Échange API (Backend / Services)
> *Définition déclarative des contrats réseau. Règle anti-invention : interdiction d'inventer des routes non documentées.*

- **Ouverture d'une tâche** : `tasks/create` (JSON-RPC) — retourne immédiatement le `task_id` unique ; commande de lancement d'un compagnon de travail déclenchée sans attendre le verdict.
- **Suivi d'avancement** : `tasks/status` (JSON-RPC) — rend l'état courant et les journaux incrémentaux, sans bloquer le sous-processus.
- **Désistement** : `tasks/cancel` (JSON-RPC) — termine le sous-processus et fait passer la tâche à l'état `cancelled`.
- **Verdict** : `tasks/result` (JSON-RPC) — livre les preuves du travail une fois la tâche parvenue à un état terminal.
- **États exposés** : `working`, `input_required`, `completed`, `failed`, `cancelled` (vocabulaire fermé, mapping direct avec le cycle de vie des compagnons de travail).
- **Évènement de transition** : `notifications/tasks/updated` avec pour charge utile le `task_id`, le `status` et l'`expires_at`, poussé sur le bus d'évènements en flux continu (SSE) au moment exact du changement d'état — en particulier à l'entrée en `input_required`, qui invite l'orchestrateur à répondre.
- **Repli de transport sans abonnement** : piggyback de l'état actualisé dans `_meta.routing` de la prochaine réponse JSON-RPC (transport stdio), réutilisant le mécanisme de routage du socle protocolaire.
- **Interdits déclarés** : aucun sondage proactif d'état, aucun webhook distant.

> 📄 **Spécifications formelles détaillées** : Pilier 1 de [ADR-0387 — Intégration des Standards MCP Modernes 2026-07-28](../../../../standards/adr-system/0387-mcp-modern-spec-2026-07-28-tasks-ui-elicitation-architecture.md). Aucune route REST n'est ouverte par le présent récit.

> ⚠️ **Exemption de matrice REST (ADR-0319)** : ce récit n'ouvre aucune route HTTP REST — seules les primitives JSON-RPC `tasks/*` déclarées ci-dessus s'appliquent. L'étendue exacte du bus d'évènements sur l'ensemble des ponts fait l'objet d'une question ouverte **OQ-211-01** (portée du bus à confirmer avant le build ; éventuel écart consigné sans bloquer, conformément au cadrage macro de l'épopée).

---

## Règles d'affaires

- **Échéance portée par le verdict** : à chaque transition vers un état terminal, l'échéance de rétention est fixée à la date d'ouverture de la tâche augmentée de sept jours ; chaque nouvelle transition vers un état terminal recalcule cette échéance à partir de la même date d'ouverture, le dernier verdict faisant foi.
- **Aucune échéance sur les tâches vivantes** : les états `working` et `input_required` portent une échéance nulle et ne sont jamais purgeables ; ils matérialisent une attente d'arbitrage humain dont la perte serait irrémédiable.
- **Durée nommée dans le socle partagé** : la durée de rétention est portée par la constante `TASK_HANDLE_TTL_DAYS = 7`, déposée dans le registre de constantes partagé avec le socle protocolaire, de sorte que le chantier de rétention la relise sans jamais la dupliquer.
- **Purge hors périmètre du présent récit** : seuls le contrat d'échéance et sa déclaration sont livrés ici ; la purge physique des fichiers appartient au chantier de rétention dédié (EPIC-23), seul habilité à supprimer un fichier de tâche — le présent récit n'exécute ni ne planifie aucune suppression.
- **Persistance des identifiants de tâches** : chaque tâche vit sous `Projects/<projet>/memory/tasks/` sous forme d'enregistrement unique portant identifiant, état courant, horodatage d'ouverture, échéance de rétention, identifiant du sous-processus et rattachement au récit traité ; l'écriture d'un état et de son échéance est tout-ou-rien.
- **Une notification par transition, zéro sondage** : l'évènement `notifications/tasks/updated` est poussé sur le bus d'évènements en flux continu dès la survenance du changement d'état, pour les entrées en `input_required` comme pour les états terminaux ; aucun canal de notification parallèle n'est ouvert et aucun sondage périodique n'est lancé.
- **Repli sans abonnement** : un client de transport qui ne s'est pas abonné aux évènements est rattrapé par piggyback de l'état dans les métadonnées de routage de sa prochaine requête ; cette latence résiduelle est assumée, jamais compensée par un sondage.
- **Un seul moteur d'état** : les cinq états de l'extension Tasks se calquent en mapping direct sur le cycle de vie des compagnons de travail déjà en service ; tout second vocabulaire d'état parallèle est proscrit.
- **Gestion des données invalides** : un identifiant inconnu, un état hors du vocabulaire fermé, une ouverture s'appuyant sur une tâche éteinte, un verdict réclamé sur une tâche vivante ou une purge visant une tâche sans échéance sont tous refusés avec un motif explicite, sans laisser d'écriture partielle.

---

## Références

### 1. Preuves Amont & Traçabilité Factuelle
- 📂 **Dossier de Preuves Factuelles** : [`memory/evidence/MLOOP-211-BE_fact_dossier.md`](../../memory/evidence/MLOOP-211-BE_fact_dossier.md)
- 🏛️ **Décisions du micro-grill du récit** : [ADR-006 — Micro-grill MLOOP-211-BE (2 décisions)](../../../docs/01-architecture/ADR-006_micro-grill_mloop-211-be__2_decisions.md)

### 2. Spécifications & Modèles de Données SSOT
- 📜 **SSOT technique** : [ADR-0387 — Intégration des Standards MCP Modernes 2026-07-28 (Tasks, MCP Apps, Elicitation & Header Routing)](../../../../standards/adr-system/0387-mcp-modern-spec-2026-07-28-tasks-ui-elicitation-architecture.md)
- 📜 **Cadrage macro de l'épopée** : [ADR-004 — EPIC-21-MCP-MODERN-SUITE : cadrage macro Grill (6 décisions)](../../../docs/01-architecture/ADR-004_epic-21-mcp-modern-suite_-_cadrage_macro_grill__6_decisions.md)
- 🏛️ **Modèle de Données SSOT** : structure du traitement et de son évènement de transition dans le dossier de preuves (§ Schéma de données)

### 3. Épopée de rattachement
- 📄 **Épopée** : [`backlog/epics/epic_mcp_modern_suite_2026q4.md`](../epics/epic_mcp_modern_suite_2026q4.md)

---

## Scénarios de test

```gherkin
# language: fr
Fonctionnalité: Extension Tasks (io.modelcontextprotocol/tasks) : Handles Asynchrones & Call-Now-Fetch-Later pour Herdr

  # 1. CHEMIN NOMINAL (Happy Path & Persistance)
  Scénario: Ouverture immédiate d'une tâche par lancement d'un compagnon de travail
    Étant donné un orchestrateur lançant un travail long par la commande "worker-spawn"
    Quand il ouvre la tâche par la primitive "tasks/create"
    Alors la primitive répond en moins de 500 millisecondes avec un identifiant de tâche unique
    Et la tâche est enregistrée avec son horodatage d'ouverture, son sous-processus et son rattachement
    Et son échéance de rétention est nulle tant qu'elle vit

  Scénario: Suivi d'avancement non bloquant puis verdict
    Étant donné une tâche ouverte et en cours d'exécution
    Quand l'orchestrateur l'interroge par la primitive "tasks/status"
    Alors l'état courant lui est rendu avec les journaux produits depuis sa dernière lecture
    Et l'interrogation ne retient ni ne bloque le sous-processus
    Quand le travail arrive à son terme
    Alors la primitive "tasks/result" lui livre le résultat du travail achevé

  # 2. EXCEPTIONS & REJETS MÉTIER (Règles d'affaires)
  Scénario: Désistement propre sans sous-processus orphelin
    Étant donné une tâche active dont le sous-processus est suivi
    Quand l'orchestrateur la désiste par la primitive "tasks/cancel"
    Alors la tâche passe à l'état "cancelled"
    Et son sous-processus est exténué sans laisser de processus orphelin
    Et son échéance de rétention est renseignée à partir de sa date d'ouverture

  Scénario: Refus de purge d'une tâche vivante
    Étant donné une tâche en état "working" ou "input_required" dont l'échéance est nulle
    Quand une purge lui est appliquée
    Alors la purge est refusée
    Et la tâche demeure intacte en attente d'un arbitrage humain

  Scénario: Rejet d'une ouverture s'appuyant sur un état terminal ou inconnu
    Étant donné une tâche déjà venue à un état terminal ou déclarée dans un état hors vocabulaire
    Quand une ouverture est tentée en s'appuyant sur elle
    Alors l'ouverture est rejetée avec un motif explicite
    Et aucune nouvelle tâche n'est enregistrée

  # 3. RÉSILIENCE TECHNIQUE & MODE DÉGRADÉ (Timeouts, Idempotence, Concurrence)
  Scénario: Échéance recalculée à chaque verdict
    Étant donné une tâche ouverte à une date connue
    Quand elle atteint un état terminal
    Alors son échéance vaut la date d'ouverture augmentée de sept jours
    Et chaque transition ultérieure vers un état terminal recalcule l'échéance à partir de la même date d'ouverture

  Scénario: Client sans abonnement rattrapé au prochain échange
    Étant donné un client de transport sans abonnement aux évènements
    Quand la tâche change d'état en son absence
    Alors l'état actualisé lui est piggybacké dans les métadonnées de routage de sa prochaine requête
    Et aucun sondage n'est lancé à la place

  Scénario: Vague de notifications sans encombrement du flux principal
    Étant donné un bus d'évènements à file d'attente limitée soumis à une forte charge
    Quand plusieurs tâches changent d'état en même temps
    Alors l'évènement de transition reste émis sans retenir le traitement principal
    Et le flux principal continue sans attendre la file de notifications

  # 4. UX, OBSERVABILITÉ & EMPTY STATE (adapté backend : poussée d'évènements, journaux, zéro polling)
  Scénario: Arbitrage humain sollicité par poussée d'évènement
    Étant donné une tâche qui exige une réponse humaine
    Quand elle bascule dans l'état "input_required"
    Alors l'évènement "notifications/tasks/updated" est poussé à l'orchestrateur abonné avec l'identifiant, l'état et l'échéance
    Et l'orchestrateur est invité à répondre
    Et aucun sondage proactif n'apparaît dans les journaux

  Scénario: Journal de transition traçable sans sondage
    Étant donné le déroulement d'une tâche de son ouverture jusqu'à son verdict
    Quand les journaux de la tâche sont consultés
    Alors chaque changement d'état y figure avec sa date et sa valeur
    Et aucun appel de sondage périodique n'y figure
```