---
id: MLOOP-214-BE
jira_key: ''
epic_key: EPIC-21-MCP-MODERN-SUITE
type: Feature
title: 'Standard Skills over MCP (io.modelcontextprotocol/skills) : Exposition Dynamique
  des Compétences mLoop'
origin: DIRECT_REQUIREMENT
source_ref: ADR-0387
macro_size: S
status: DONE_TESTED
grill_me: DONE
invest_score: 6/6
layer: backend
blocked_by:
- MLOOP-210-BE
created_at: '2026-09-24'
content_hash: 3d5ef1a1f3b135fc
---

# Standard Skills over MCP (io.modelcontextprotocol/skills) : Exposition Dynamique des Compétences mLoop

---

## Description
**En tant qu'** architecte système et concepteur de prompts mLoop,
**je veux** exposer le catalogue de compétences du framework à travers l'extension officielle Skills over MCP, **afin de** décharger le fichier de règles principales de ses consignes secondaires et de charger les compétences à la volée, préservant ainsi le budget d'attention et la précision des modèles de langage.

---

## Contexte & Périmètre

### Contexte Métier
Le fichier de règles principales de l'écosystème accumule consignes permanentes et procédures détaillées, au point de consommer une part croissante du budget d'attention dès l'ouverture de chaque session, sans que l'essentiel en soit mobilisé. Le chargement à la volée des compétences — bibliothèques de méthodes activables selon la phase de travail — permet de n'apporter à l'agent que la consigne utile au moment où elle l'est. Le catalogue existant de compétences est déjà découvert et lisible ; le présent récit l'adapte à l'espace de noms officiel de l'extension, sans double maintenance, et soumet toute compétence à l'autorité supérieure des règles permanentes, lesquelles ne peuvent jamais être abrogées.

### In-Scope
- La découverte dynamique des fichiers de compétences stockés dans le répertoire dédié du framework, partagée avec l'exposition déjà en service.
- L'exposition des métadonnées de chaque compétence — nom, description, indice de priorité informatif — via l'espace de noms officiel de l'extension.
- Le chargement du contenu complet d'une compétence uniquement lorsque l'agent décide de l'activer pour sa phase courante.
- La hiérarchie stricte entre règles permanentes, compétences chargées et contenu historique du fichier de règles principales, avec journalisation structurée de tout conflit.
- Le pont à double pile permanent : espace de noms officiel lorsque le client le déclare, repli sur l'exposition de ressources déjà en service dans le cas contraire — les deux voies partageant la découverte unique.
- La mesure du budget de démarrage du fichier de règles principales et des règles permanentes sur les deux canaux d'exposition, avec l'exécution de la trousse de vérification des compétences.

### Out-of-Scope
- Le téléchargement de compétences depuis des dépôts tiers non approuvés : la sécurité par échec bloqué interdit toute source distante.
- L'abrogation d'une règle permanente par une compétence : l'autorité des règles est hors du périmètre discutable du récit.
- L'allègement effectif du fichier de règles principales : il devient un résultat observé de la nouvelle exposition, non un critère de sortie autonome.
- La vérification du support natif de l'espace de noms par les environnements d'exécution : fait relatif à la vérification documentaire du socle.
- Toute interface graphique : le récit est un composant sans surface visuelle.

---

## Critères d'acceptation

*Règle conditionnelle `layer: backend` (ADR-0366) : seules les Opérations Métier & Logique Backend (5 sous-titres normés) et les Contrats d'Échange API sont renseignés ; les sections frontend sont non applicables — composant headless.*

### Opérations Métier & Logique Backend *(backend / fullstack)*
#### 1. Inventaire des compétences par l'espace de noms officiel
* **Entrée Métier** : la demande d'inventaire d'un client déclarant l'espace de noms officiel de l'extension.
* **Règles d'admissibilité & Validation** : la demande n'est servie que par le pont à double pile lorsque le client déclare l'espace de noms ; l'inventaire est exclusivement celui des compétences découvertes localement ; toute source distante est écartée.
* **Traitement & Algorithme Métier** : appel de la découverte unique partagée avec l'exposition de ressources en service, puis habillage de chaque fiche en entrée typée de l'espace de noms officiel (nom, description, indice de priorité informatif) sans autorité d'override.
* **Résultat Métier & Mutations** : l'inventaire typé des compétences actives est retourné ; aucun fichier n'est modifié ; l'exposition de ressources historique reste intacte.
* **Cas de Rejet Métier** : rejet d'une demande formulée hors des deux voies du pont à double pile ; rejet de toute entrée ne provenant pas de la découverte locale.

#### 2. Chargement du contenu d'une compétence
* **Entrée Métier** : le nom de la compétence dont l'agent requiert le chargement pour sa phase courante.
* **Règles d'admissibilité & Validation** : le nom doit désigner une compétence présente dans l'inventaire découvert ; le chargement n'intervient qu'à activation explicite par l'agent, jamais en préchargement ; le contenu rendu est celui du fichier de la compétence, sans mutation.
* **Traitement & Algorithme Métier** : lecture du fichier de compétence correspondant et restitution intégrale de son contenu, sous le seuil de cent millisecondes, sans réécriture ni mise en cache au-delà de la seule lecture.
* **Résultat Métier & Mutations** : le contenu exact de la compétence est remis à l'agent ; aucun état permanent n'est modifié.
* **Cas de Rejet Métier** : rejet d'un nom de compétence absent de l'inventaire ; rejet de toute tentative de chargement depuis une source distante non approuvée.

#### 3. Arbitrage d'un conflit entre règle permanente et compétence
* **Entrée Métier** : une situation où le contenu d'une compétence chargeable contredit une règle permanente du répertoire de règles.
* **Règles d'admissibilité & Validation** : la hiérarchie est stricte et non négociable — règle permanente, puis compétence chargée, puis contenu historique du fichier de règles principales ; une compétence ne peut jamais abroger un garde-fou.
* **Traitement & Algorithme Métier** : en cas de conflit, la règle permanente l'emporte ; un journal structuré de niveau debug consignant le conflit est émis — l'engloutissement silencieux d'une exception étant proscrit ; l'indice de priorité exposé par l'inventaire demeure informatif, sans autorité d'override.
* **Résultat Métier & Mutations** : l'application effective suit la règle permanente, le conflit est tracé dans le journal, et la compétence reste chargée pour ses parties non conflictuelles.
* **Cas de Rejet Métier** : rejet de toute tentative d'application d'une compétence contre une règle permanente ; rejet d'un conflit non journalisé.

#### 4. Repli sur l'exposition historique faute de déclaration d'espace de noms
* **Entrée Métier** : une demande d'inventaire ou de lecture émise par un client qui ne déclare pas l'espace de noms officiel.
* **Règles d'admissibilité & Validation** : le repli est engagé uniquement sur constat d'absence de déclaration ; les deux voies partagent la découverte unique ; le repli ne constitue jamais un échec.
* **Traitement & Algorithme Métier** : bascule sur l'exposition de ressources et l'outil de lecture déjà en service, servant les mêmes fichiers de compétences par le même chemin de découverte — sans code mort ni seconde maintenance du catalogue.
* **Résultat Métier & Mutations** : l'inventaire ou le contenu est servi par la voie historique ; le catalogue de compétences demeure unique ; aucune non-régression n'est introduite pour les compétences déjà en service.
* **Cas de Rejet Métier** : rejet d'un repli qui dupliquerait le catalogue ; rejet de toute rupture de la voie historique alors que le client ne déclare pas l'espace de noms.

---

## Parcours Interactif & API

### Parcours Interactif (Frontend / Déclencheurs UI)
N/A — Composant Headless : aucun déclencheur d'interface.

### Contrats d'Échange API (Backend / Services)
> *Définition déclarative des contrats réseau. Règle anti-invention : seuls les échanges du protocole MCP déclarés ci-dessus s'appliquent.*

- **Inventaire des compétences** : `skills/list` (espace de noms officiel) — inventaire typé partageant la découverte unique, avec nom, description et indice de priorité informatif.
- **Lecture d'une compétence** : `skills/get` (espace de noms officiel) — contenu intégral du fichier de compétence sous le seuil de cent millisecondes.
- **Voie historique sans déclaration d'espace de noms** : exposition de ressources sous l'ancien schéma d'URI et outil de lecture de compétence, déjà en service, servant les mêmes fichiers.
- **Budget de démarrage mesuré** : budget cumulé du fichier de règles principales et des règles permanentes inférieur ou égal à quinze mille jetons, mesuré sur les deux canaux d'exposition, avec la trousse de vérification des compétences exécutée à cent pour cent sans échec.
- **Interdits déclarés** : aucune route REST ouverte, aucun téléchargement distant, aucune autorité d'override pour l'indice de priorité.

> ⚠️ **Exemption de matrice REST (ADR-0319)** : ce récit n'ouvre aucune route HTTP REST — seuls les échanges de compétences du protocole MCP déclarés ci-dessus s'appliquent. Le support natif de l'espace de noms officiel par les environnements d'exécution, non vérifié, fait l'objet d'une question ouverte **OQ-214-01** (conformité à confirmer avant le build, dans le cadre de la vérification documentaire unique du socle ; éventuel écart consigné sans bloquer).

---

## Règles d'affaires

- **Hiérarchie stricte et non négociable** : la règle permanente l'emporte sur la compétence chargée, qui l'emporte sur le contenu historique du fichier de règles principales ; une compétence ne peut à aucun moment abroger un garde-fou permanent.
- **Conflit toujours journalisé** : tout conflit entre règle permanente et compétence émet un journal structuré de niveau debug ; l'engloutissement silencieux d'une exception est proscrit.
- **Priorité informative, jamais d'override** : l'indice de priorité exposé par l'inventaire renseigne sans conférer d'autorité ; l'application effective suit la hiérarchie, jamais l'indice.
- **Pont à double pile permanent** : le client déclarant l'espace de noms officiel est servi par les méthodes modernes ; tout autre client est servi par l'exposition historique ; les deux voies partagent la découverte unique et aucun code mort n'est toléré.
- **Chargement à la volée uniquement** : le contenu d'une compétence n'est remis qu'à activation explicite pour la phase courante, sans préchargement systématique.
- **Budget de démarrage mesuré sur les deux canaux** : le budget cumulé du fichier de règles principales et des règles permanentes reste inférieur ou égal à quinze mille jetons, vérifié sur les deux voies d'exposition, la trousse de vérification des compétences étant exécutée à cent pour cent sans échec ; l'allègement du fichier de règles principales n'est qu'un résultat observé, jamais un critère autonome.
- **Sécurité par échec bloqué** : toute compétence issue d'un dépôt distant non approuvé est refusée ; seules les compétences découvertes localement sont exposées.
- **Gestion des données invalides** : un nom de compétence absent de l'inventaire, une demande hors des deux voies du pont, une source distante ou un conflit non journalisé sont refusés avec un motif explicite, sans écriture partielle ni rupture de la voie historique.

---

## Références

### 1. Preuves Amont & Traçabilité Factuelle
- 📂 **Dossier de Preuves Factuelles** : [`memory/evidence/MLOOP-214-BE_fact_dossier.md`](../../memory/evidence/MLOOP-214-BE_fact_dossier.md)
- 🏛️ **Décisions du micro-grill du récit** : [ADR-009 — Micro-grill MLOOP-214-BE (2 décisions)](../../../docs/01-architecture/ADR-009_micro-grill_mloop-214-be__2_decisions.md)

### 2. Spécifications & Modèles de Données SSOT
- 📜 **SSOT technique** : [ADR-0387 — Intégration des Standards MCP Modernes 2026-07-28 (Tasks, MCP Apps, Elicitation & Header Routing)](../../../../standards/adr-system/0387-mcp-modern-spec-2026-07-28-tasks-ui-elicitation-architecture.md)
- 📜 **Cadrage macro de l'épopée** : [ADR-004 — EPIC-21-MCP-MODERN-SUITE : cadrage macro Grill (6 décisions)](../../../docs/01-architecture/ADR-004_epic-21-mcp-modern-suite_-_cadrage_macro_grill__6_decisions.md)
- 🏛️ **Modèle de Données SSOT** : structure du catalogue de compétences et de la règle permanente dans le dossier de preuves (§ Schéma de données)

### 3. Épopée de rattachement
- 📄 **Épopée** : [`backlog/epics/epic_mcp_modern_suite_2026q4.md`](../epics/epic_mcp_modern_suite_2026q4.md)

---

## Scénarios de test

```gherkin
# language: fr
Fonctionnalité: Standard Skills over MCP (io.modelcontextprotocol/skills) : Exposition Dynamique des Compétences mLoop

  # 1. CHEMIN NOMINAL (Happy Path & Persistance)
  Scénario: Inventaire typé servi par l'espace de noms officiel
    Étant donné un client déclarant l'espace de noms officiel de l'extension
    Quand il demande l'inventaire des compétences
    Alors l'inventaire typé est servi par la voie moderne du pont
    Et chaque entrée porte son nom, sa description et son indice de priorité informatif
    Et l'inventaire provient de la découverte locale unique partagée avec l'exposition historique

  Scénario: Chargement à la volée du contenu d'une compétence
    Étant donné un agent en phase de planification
    Quand il active explicitement une compétence de l'inventaire
    Alors le contenu intégral de son fichier est remis en dessous du seuil de cent millisecondes
    Et aucun fichier n'est modifié

  # 2. EXCEPTIONS & REJETS MÉTIER (Règles d'affaires)
  Scénario: Conflit entre règle permanente et compétence
    Étant donné une compétence chargeable contredisant une règle permanente
    Quand l'agent tente d'appliquer la compétence
    Alors la règle permanente l'emporte
    Et un journal structuré de niveau debug consigne le conflit
    Et la compétence demeure chargée pour ses parties non conflictuelles

  Scénario: Compétence issue d'une source distante non approuvée
    Étant donné un catalogue contenant une compétence provenant d'un dépôt distant non approuvé
    Quand une demande de chargement la cible
    Alors le chargement est refusé par sécurité par échec bloqué
    Et aucune écriture n'est produite

  Scénario: Nom de compétence absent de l'inventaire
    Étant donné un nom de compétence inconnu de la découverte locale
    Quand une lecture est demandée
    Alors la lecture est refusée avec un motif explicite
    Et aucun contenu n'est restitué

  # 3. RÉSILIENCE TECHNIQUE & MODE DÉGRADÉ (Timeouts, Idempotence, Concurrence)
  Scénario: Repli automatique du client sans espace de noms déclaré
    Étant donné un client qui ne déclare pas l'espace de noms officiel
    Quand il demande l'inventaire ou le contenu d'une compétence
    Alors le pont bascule sur l'exposition historique déjà en service
    Et les mêmes fichiers sont servis par la découverte unique
    Et aucun échec n'est produit

  Scénario: Non-régression des deux voies du pont à double pile
    Étant donné les deux types de clients émettant la même demande
    Quand les deux voies sont exercées successivement
    Alors chacune sert le même catalogue issu d'une découverte unique
    Et aucun code mort ni doublon de maintenance n'est introduit

  Scénario: Budget de démarrage contenu sur les deux canaux
    Étant donné le cumul du fichier de règles principales et des règles permanentes
    Quand le budget est mesuré sur chacun des deux canaux d'exposition
    Alors il demeure inférieur ou égal à quinze mille jetons
    Et la trousse de vérification des compétences s'exécute à cent pour cent sans échec

  # 4. UX, OBSERVABILITÉ & EMPTY STATE (adapté backend : journaux de conflit, priorité, traçabilité)
  Scénario: Conflit traçable sans engloutissement d'exception
    Étant donné un conflit survenu entre une règle permanente et une compétence
    Quand les journaux structurés sont consultés
    Alors l'évènement de conflit y figure avec sa règle et sa compétence en cause
    Et aucun engloutissement silencieux d'exception n'y figure

  Scénario: Priorité exposée sans autorité d'override
    Étant donné un inventaire exposant des indices de priorité
    Quand une compétence à indice élevé contredit une règle permanente
    Alors l'indice demeure informatif
    Et l'application effective suit la hiérarchie stricte
```