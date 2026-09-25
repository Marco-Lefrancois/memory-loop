---
id: MLOOP-210-BE
jira_key: ''
epic_key: EPIC-21-MCP-MODERN-SUITE
type: Feature
title: 'Socle Protocolaire MCP 2026-07-28 : Négociation de Version, Header Routing
  & MCP-Protocol-Version'
origin: DIRECT_REQUIREMENT
source_ref: ADR-0387
macro_size: S
status: SHIPPED
layer: backend
invest_score: 6/6
created_at: '2026-09-24'
ttl_cycles: 4
---
# Socle Protocolaire MCP 2026-07-28 : Négociation de Version, Header Routing & MCP-Protocol-Version

---

## Description
**En tant qu'** orchestrateur et développeur d'agents mLoop,
**je veux** que les ponts MCP de mLoop négocient formellement la révision protocolaire `2026-07-28` et routent les échanges par en-têtes sur les transports réseau,
**afin de** garantir l'interopérabilité sans faille avec les clients modernes (OpenCode, Claude Code, Antigravity) tout en conservant une rétrocompatibilité descendante totale avec les clients hérités.

---

## Contexte & Périmètre

### Contexte Métier
mLoop expose localement des ponts MCP consommés par des agents hétérogènes : orchestrateurs, assistants d'édition et workers d'arrière-plan. La révision 2026-07-28 du protocole MCP impose une déclaration explicite de version protocolaire et un routage par en-têtes HTTP, permettant à la passerelle d'acheminement d'identifier la méthode et l'outil ciblés sans relire chaque message JSON-RPC. Le socle doit absorber ces exigences une fois pour toutes : négociation de version unique, en-têtes de routage à granularité maîtrisée, et une politique de repli commune que les extensions modernes réutiliseront par la suite, sans jamais pénaliser les clients hérités qui ignorent la révision moderne.

### In-Scope
- Négociation formelle de la révision `2026-07-28` à l'initialisation, avec publication d'un registre unique des versions prises en charge (révisions cible et admises).
- Routage par en-têtes HTTP (version protocolaire, méthode, nom d'outil) sur les transports HTTP et SSE, sans lecture du corps des requêtes.
- Exposition équivalente des informations de routage sur le transport stdio via les métadonnées de routage du message, sans jamais fabriquer d'en-tête HTTP sur ce transport.
- Politique de repli protocolaire unifiée, applicable par requête dans le même traitement, conduisant les clients non modernes en mode synchrone standard et réutilisable par les extensions bâties sur ce socle.
- Observabilité protocolaire : alerte structurée d'obsolescence, journal de décision de repli et métrique d'adoption de l'en-tête de version.
- Vérification documentaire de conformité des espaces de noms d'extensions officiels contre la spécification externe, avec constat d'écart consigné sans bloquer le socle.

### Out-of-Scope
- Migration vers un service distant multi-tenant (jalon ultérieur).
- Les comportements propres aux extensions modernes (tâches asynchrones, affichages embarqués, formulaires interactifs) qui s'appuieront sur ce socle ultérieurement.
- La certification multi-environnements des ponts.
- L'inventaire exhaustif des ponts exposés en réseau n'est pas clôturé à ce stade : il sera confirmé en construction, et aucun pont supplémentaire n'est présumé couvert (frontière active assumée).

---

## Critères d'acceptation

*Règle conditionnelle `layer: backend` (ADR-0366) : seules les Opérations Métier & Logique Backend (5 sous-titres normés) et les Contrats d'Échange API sont renseignés ; les sections frontend sont non applicables — composant headless.*

### Opérations Métier & Logique Backend *(backend / fullstack)*
#### 1. Négociation de version protocolaire à l'initialisation
* **Entrée Métier** : La demande d'initialisation du client MCP, avec ou sans version protocolaire souhaitée (champ facultatif ; son absence déclenche le repli gracieux du client hérité).
* **Règles d'admissibilité & Validation** : La version souhaitée est confrontée au registre unique des versions prises en charge, qui publie la révision cible `2026-07-28` et les révisions admises `2025-11-25` et `2024-11-05`. Une valeur absente du registre est inadmissible ; une valeur connue mais différente de la révision cible reste recevable avec alerte d'obsolescence.
* **Traitement & Algorithme Métier** : Le registre est lu depuis la déclaration unique partagée entre la négociation et le routage (anti-dérive du poignée de main). Si la version est connue et obsolète, la politique de repli protocolaire est armée pour la requête courante sans mise en échec de la session.
* **Résultat Métier & Mutations** : La réponse d'initialisation publie la liste des versions prises en charge et la révision retenue ; la session mémorise la version négociée pour la suite des échanges. Aucune persistance applicative n'est créée (état de transport uniquement).
* **Cas de Rejet Métier** : La demande est refusée lorsque la version déclarée est une valeur inconnue du registre ; le message est rejeté par l'erreur JSON-RPC `-32600` (requête invalide). Aucun refus n'est possible pour une version connue.

#### 2. Routage par en-têtes sur les transports HTTP et SSE
* **Entrée Métier** : La requête reçue par un pont exposé en réseau, portant la version protocolaire, le nom de la méthode et, le cas échéant, le nom de l'outil ciblé.
* **Règles d'admissibilité & Validation** : La valeur de l'en-tête de version suit les mêmes règles d'admissibilité que la négociation (registre unique). L'en-tête de méthode accompagne toute requête. L'en-tête de nom d'outil n'est admissible que sur un appel d'outil ; toute autre méthode l'exclut.
* **Traitement & Algorithme Métier** : La passerelle achemine la requête directement à partir des en-têtes, sans relire le corps JSON-RPC. Les noms d'en-têtes proviennent du registre partagé. Sur un appel d'outil, le nom d'outil est repris de la demande ; sur les notifications et les autres méthodes, il est omis. En l'absence d'en-tête de version, le pont traite la requête en client hérité et bascule gracieusement en mode synchrone standard.
* **Résultat Métier & Mutations** : La requête est acheminée vers la bonne opération et la réponse est rendue selon la version négociée ; le corps reste inchangé, sans transformation induite par le routage.
* **Cas de Rejet Métier** : Une valeur de version absente du registre provoque un refus dur du message (erreur JSON-RPC `-32600`). L'absence d'en-tête de version n'est jamais un rejet : elle déclenche le mode de compatibilité.

#### 3. Politique de repli protocolaire unifiée
* **Entrée Métier** : L'activation de la politique lorsqu'une requête n'atteint pas la révision cible (version connue obsolète) ou ne porte pas l'en-tête moderne.
* **Règles d'admissibilité & Validation** : Le repli n'est activable que pour des versions connues du registre ou des clients dépourvus d'en-tête moderne ; il ne se substitue jamais à un refus de version inconnue. Rejeter par politique de repli est interdit (rétrocompatibilité à 100 %).
* **Traitement & Algorithme Métier** : La politique s'applique par requête, dans le même traitement, sans service secondaire. Elle conduit le pont en mode synchrone standard lorsque les extensions modernes ne sont pas négociées, et émet une alerte structurée d'obsolescence à chaque occurrence. Elle est publiée dans la déclaration partagée afin d'être réutilisée par les extensions bâties sur ce socle.
* **Résultat Métier & Mutations** : La requête aboutit en mode compatibilité, une décision de repli est journalisée, et la politique commune reste disponible pour les fonctionnalités aval. Aucune mutation d'état persistant.
* **Cas de Rejet Métier** : Aucun — le repli ne rejette jamais. Seule une version inconnue du registre déclenche un refus, indépendamment de la politique de repli.

### Maquettes SSOT *(frontend / fullstack)*
N/A — Composant Headless.

---

## Parcours Interactif & API

### Parcours Interactif (Frontend / Déclencheurs UI)
N/A — Composant Headless : aucun déclencheur d'interface.

### Contrats d'Échange API (Backend / Services)
> *Règle Zéro Fausse Route : aucune route REST n'est définie par ce récit. Les seuls contrats sont les échanges JSON-RPC du protocole MCP.*

- **Négociation de version (initialisation)** : échange JSON-RPC `initialize` — le serveur publie `supportedVersions` : `2026-07-28`, `2025-11-25`, `2024-11-05`. Une version déclarée hors registre est refusée par l'erreur JSON-RPC `-32600`.
- **En-têtes HTTP/SSE — version** : `MCP-Protocol-Version: 2026-07-28` — toujours présent sur ce transport ; valeur inconnue du registre → refus `-32600` ; valeur connue ≠ cible → alerte `protocol_version_obsolete` + politique de repli ; en-tête absent → repli gracieux, jamais de refus.
- **En-têtes HTTP/SSE — méthode** : `MCP-Method: <méthode JSON-RPC>` — toujours présent (copie de la méthode), permettant l'acheminement par la passerelle sans lecture du corps.
- **En-têtes HTTP/SSE — outil** : `MCP-Tool-Name: <nom d'outil>` — conditionnel, présent uniquement sur un appel d'outil (nom repris de la demande), absent sur les notifications et les autres méthodes.
- **Transport stdio** : aucun en-tête HTTP. Les mêmes valeurs sont exposées dans les métadonnées de routage du message JSON-RPC : `_meta.routing = { protocolVersion, method, toolName? }`. Zéro faux en-tête sur ce transport.

> 📄 **Granularité et registre des en-têtes** : détail tranché en micro-grill 210-Q2 — voir [ADR-005](../../../docs/01-architecture/ADR-005_micro-grill_mloop-210-be__2_decisions.md).

> ⚠️ **Exemption de matrice REST (ADR-0319)** : ce récit ne consomme aucune route HTTP REST — seuls les contrats JSON-RPC du protocole MCP déclarés ci-dessus s'appliquent. L'inventaire exhaustif des transports HTTP du pont fait l'objet d'une question ouverte **OQ-210-01** (conformité de l'inventaire à confirmer avant le build du socle ; écart éventuel consigné sans bloquer, conformément au cadrage macro de l'épopée).

---

## Règles d'affaires

- **Tolérance des versions protocolaires** : toute version publiée au registre, de la révision la plus ancienne admise `2024-11-05` jusqu'à la révision cible `2026-07-28`, est recevable ; une version connue différente de la cible déclenche une alerte structurée d'obsolescence et l'application de la politique de repli, jamais un refus.
- **Refus réservé aux versions inconnues du registre** : seule une valeur d'en-tête ou de négociation absente du registre provoque un refus dur du message (erreur JSON-RPC `-32600`) ; une déclaration d'en-tête entièrement absente est traitée comme un client hérité et n'est jamais refusée.
- **Rétrocompatibilité non négociable** : aucune requête portant une version connue du registre ne peut échouer ; interdiction formelle de rejeter les révisions pré-2025 publiées.
- **Granularité du routage** : l'en-tête de version accompagne tout échange sur les transports réseau ainsi que la négociation d'initialisation ; l'en-tête de méthode accompagne toute requête ; l'en-tête de nom d'outil n'accompagne que les appels d'outils et est omis sur les notifications et les autres méthodes.
- **Honnêteté des transports** : les en-têtes HTTP n'existent que sur les transports HTTP et SSE ; sur le transport stdio, les mêmes valeurs sont portées par les métadonnées de routage du message, et fabriquer un en-tête HTTP sur ce transport est interdit.
- **Déclaration unique du registre** : la liste des versions prises en charge, la révision cible et les noms d'en-têtes sont déclarés une seule fois et partagés entre la négociation et le routage afin d'interdire toute dérive entre le poignée de main et les en-têtes.
- **Politique de repli unifiée et par requête** : le repli s'applique au niveau de la requête, dans le même traitement, conduit le client non moderne en mode synchrone standard, ne peut jamais rejeter, et constitue la politique commune réutilisée par les extensions bâties sur ce socle.
- **Observabilité de l'adoption** : chaque version obsolète émet un journal structuré d'obsolescence, chaque décision de repli est journalisée, et une métrique d'adoption de l'en-tête de version distingue les clients modernes des clients hérités.
- **Conformité des espaces de noms d'extensions** : les espaces de noms d'extensions officiels sont vérifiés contre la spécification externe avant toute construction d'extension ; un écart est consigné comme question ouverte sans bloquer le socle.
- **Gestion des échanges invalides** : une version inconnue, une méthode déclarée hors registre ou un nom d'outil porté hors appel d'outil constituent des échanges non conformes ; ils sont refusés ou ignorés selon les cas sans altérer l'état des sessions conformes.

---

## Références

### 1. Preuves Amont & Traçabilité Factuelle
- 📂 **Dossier de Preuves Factuelles** : [`memory/evidence/MLOOP-210-BE_fact_dossier.md`](../../memory/evidence/MLOOP-210-BE_fact_dossier.md)

### 2. Spécifications & Modèles de Données SSOT
- 🏛️ **ADR d'Architecture (SSOT technique)** : [ADR-0387 — Intégration des Standards MCP Modernes 2026-07-28](../../../../standards/adr-system/0387-mcp-modern-spec-2026-07-28-tasks-ui-elicitation-architecture.md)
- 📋 **Cadrage Macro Grill (6 décisions)** : [ADR-004 — EPIC-21-MCP-MODERN-SUITE](../../../docs/01-architecture/ADR-004_epic-21-mcp-modern-suite_-_cadrage_macro_grill__6_decisions.md)
- 📋 **Micro-Grill du récit (2 décisions)** : [ADR-005 — Micro-grill MLOOP-210-BE](../../../docs/01-architecture/ADR-005_micro-grill_mloop-210-be__2_decisions.md)
- 📚 **Épopée de rattachement** : [EPIC-21 — MCP Modern Suite 2026Q4](../epics/epic_mcp_modern_suite_2026q4.md)

---

## Scénarios de test

```gherkin
# language: fr
Fonctionnalité: Socle Protocolaire MCP 2026-07-28 : Négociation de Version, Header Routing & MCP-Protocol-Version

  # CHEMIN NOMINAL (Happy Path & Persistance)
  Scénario: Négociation et routage nominal d'un client 2026-07-28 sur transport HTTP/SSE
    Étant donné un client MCP déclarant la version protocolaire "2026-07-28" à l'initialisation
    Et que le registre des versions admet cette révision comme révision cible
    Quand le client émet une requête d'appel d'outil sur un transport HTTP ou SSE
    Alors la réponse d'initialisation publie la révision négociée et les versions prises en charge
    Et les en-têtes de version et de méthode accompagnent la requête
    Et l'en-tête de nom d'outil est présent puisque la requête est un appel d'outil
    Et la passerelle achemine la réponse sans relire le corps de la requête

  # EXCEPTIONS & REJETS MÉTIER (Règles d'affaires)
  Scénario: Rejet dur d'une version inconnue du registre
    Étant donné un client déclarant une version protocolaire absente du registre
    Quand la négociation compare la version déclarée au registre partagé
    Alors le message est refusé par l'erreur JSON-RPC -32600 de requête invalide
    Et aucune session ni aucune mutation n'est enregistrée

  Scénario: Version obsolète admise avec alerte structurée et repli sans rejet
    Étant donné un client déclarant la version connue mais obsolète "2024-11-05"
    Quand le registre reconnaît cette version comme admise mais non cible
    Alors une alerte structurée "protocol_version_obsolete" est émise
    Et la politique de repli macro s'applique à la requête courante
    Et la requête aboutit sans rejet conformément à l'interdiction de rejeter les versions connues

  # RÉSILIENCE TECHNIQUE & MODE DÉGRADÉ (Timeouts, Idempotence, Concurrence)
  Scénario: Repli gracieux d'un client sans en-tête moderne
    Étant donné un client émettant une requête sans en-tête de version protocolaire
    Quand le transport traite la requête comme un client hérité
    Alors le pont bascule gracieusement en mode synchrone standard
    Et la requête aboutit sans interruption ni rejet

  Scénario: Exposition honnête des informations de routage en transport stdio
    Étant donné un échange exécuté sur le transport stdio
    Quand le pont doit exposer la version protocolaire, la méthode et le cas échéant l'outil
    Alors ces valeurs sont portées dans les métadonnées de routage du message JSON-RPC
    Et aucun en-tête HTTP n'est fabriqué sur ce transport

  Scénario: Frontière active sur l'inventaire des transports exposés en réseau
    Étant donné que l'inventaire exhaustif des transports HTTP n'est pas clôturé
    Quand le socle est construit sans inventaire fermé
    Alors aucun pont réseau supplémentaire n'est présumé couvert
    Et la limite est consignée explicitement sans prétention d'exhaustivité

  # UX, OBSERVABILITÉ & EMPTY STATE (Spinners, Retours Écran, Logs)
  Scénario: Observabilité de l'obsolescence, du repli et de l'adoption des en-têtes
    Étant donné un jeu de requêtes mêlant clients modernes, clients obsolètes et clients hérités
    Quand les échanges sont traités par le socle protocolaire
    Alors chaque version obsolète génère un journal structuré "protocol_version_obsolete"
    Et chaque décision de repli est tracée dans le journal de décision de repli
    Et une métrique d'adoption de l'en-tête de version est alimentée pour distinguer les clients modernes des clients hérités
```