---
id: MLOOP-212-FE
jira_key: ''
epic_key: EPIC-21-MCP-MODERN-SUITE
type: Feature
title: Extension MCP Apps — Exposition ui:// pour Archify Cockpit & DrawDB ERD
origin: DIRECT_REQUIREMENT
source_ref: ADR-0387
macro_size: M
status: SHIPPED
grill_me: DONE
layer: frontend
invest_score: 6/6
blocked_by:
- MLOOP-210-BE
created_at: '2026-09-24'
content_hash: 3f107a53d86a86b5
---
# Extension MCP Apps — Exposition ui:// pour Archify Cockpit & DrawDB ERD

---

## Description
**En tant qu'** ingénieur logiciel et collaborateur utilisant un IDE agentique,
**je veux** que les visualisations d'architecture d'Archify Cockpit et les schémas relationnels DrawDB soient rendus directement dans l'interface de discussion de l'agent sous forme d'iframes interactives via l'extension officielle « MCP Apps »,
**afin de** inspecter instantanément la topologie du système et la structure des données sans basculer vers un navigateur web externe, tout en conservant le projet actif synchronisé entre le chat et la vue rendue.

---

## Contexte & Périmètre

### Contexte Métier
mLoop produit deux visualisations à forte valeur ajoutée pour l'ingénierie logicielle : une cartographie vivante d'architecture (Archify Cockpit) et un schéma relationnel de données (DrawDB ERD). Aujourd'hui, leur consultation impose une rupture de contexte : l'utilisateur doit quitter l'IDE et ouvrir un navigateur externe. L'extension officielle « MCP Apps » de la révision moderne du protocole permet d'exposer ces visualisations comme des ressources rendues dans un cadre interactif au sein même de la conversation avec l'agent. Le pont doit donc publier les deux ressources sous leurs adresses officielles, garantir que la vue affichée reflète toujours le projet actif sélectionné dans le chat, préserver l'isolation stricte du cadre (lecture seule, aucun accès réseau depuis l'intérieur), et proposer un repli honnête vers une adresse locale lorsque le client hôte ne sait pas rendre l'extension ou lorsque le cadre est trop étroit pour être exploitable.

### In-Scope
- Implémentation du schéma d'adresses `ui://` conforme à l'extension officielle `io.modelcontextprotocol/ui`.
- Déclaration des deux ressources visuelles sous leurs adresses officielles : `ui://archify/cockpit` et `ui://drawdb/schema`.
- Fourniture des contenus HTML enrichis et auto-contenus (zéro dépendance à un CDN externe), servis par le pont MCP Apps (`src/bridges/mcp_ui.py`) à partir des artefacts produits par `tools/archify/` et `tools/drawdb/`.
- Sécurisation du sandboxing du cadre rendu (`allow-scripts`, isolation des jetons, aucun accès au stockage local de l'IDE hôte, politique de connexion réseau refusée préservée).
- Synchronisation du projet actif : source de vérité unique sur l'état du pont, transmission par message côté chat lors d'un changement de projet et état initial transmis par paramètre d'adresse, mise à jour en place du cadre sans rechargement.
- Cadre 100 % lecture seule en première version : aucune écriture du cadre vers le chat.
- Politique de repli contractualisée : seuil de largeur `UI_MIN_WIDTH_PX = 320` déclaré dans un registre partagé (révisable sans libération de version), retour d'une adresse locale en solution de secours lorsque le client ne supporte pas l'extension, et bannière « ouvrir dans le navigateur » lorsque le cadre passe sous le seuil.

### Out-of-Scope
- Édition bidirectionnelle dans DrawDB depuis le cadre : la première vise uniquement le rendu et l'exploration interactive en lecture seule.
- Toute écriture ou commande remontant du cadre vers le chat ou le pont.
- Les autres extensions de la spécification moderne (tâches asynchrones, élicitations interactives) ne sont pas couvertes par ce récit.
- La certification multi-IDE au-delà des clients hôtes déjà couverts par le socle protocolaire en amont.

---

## Critères d'acceptation

*Règle conditionnelle `layer: frontend` (ADR-0366) : seules les Spécifications de l'Interface & UX, les Maquettes SSOT, le Parcours Interactif et les contrats d'échange applicables sont renseignés ; les Opérations Métier & Logique Backend sont non applicables — logique portée par le pont et le socle en amont.*

### Spécifications de l'Interface & UX *(frontend / fullstack)*
- **Macrostructure & États de surface** : L'affichage d'une ressource respecte les 4 états de surface : Initial/Vide (aucune ressource demandée, conversation seule), Chargement (cadre en cours de rendu avec indicateur de progression), Erreur (client hôte sans support de l'extension ou ressource indisponible : message explicite et proposition d'adresse locale de secours) et Succès (cadre interactif pleinement navigable : particules animées du cockpit d'architecture, zoom et déplacement sur le schéma relationnel).
- **États d'interaction (signifiants)** : Le cadre accepte le zoom et le déplacement au molette/glissé sur le schéma relationnel ; la bannière de repli expose un lien déclaratif « ouvrir dans le navigateur » avec états Default, Hover, Focus-Visible et Active ; aucun champ ni commande d'édition n'est exposé dans le cadre (lecture seule v1) et aucun état d'édition n'est donc contracté.
- **Feedback Utilisateur** : Bannière informative non bloquante affichée dès que la largeur du cadre passe sous le seuil partagé, avec action d'ouverture de l'adresse locale correspondante (serveur local du schéma relationnel ou page autonome du cockpit d'architecture) ; en cas de client sans support de l'extension, retour direct de l'adresse locale accompagné d'un message de dégradation gracieuse ; la mise à jour du projet actif s'effectue en place, sans rechargement visible ni perte de la navigation en cours.

### Opérations Métier & Logique Backend *(backend / fullstack)*
N/A — composant frontend : la négociation d'extension, le registre des versions et la politique de repli protocolaire sont portés par le socle en amont.

### Maquettes SSOT *(frontend / fullstack)*
N/A — cadre rendu par l'IDE hôte selon la spécification de l'extension officielle ; aucune maquette Figma ni actif local de maquette n'est contracté pour ce récit.

---

## Parcours Interactif & API

### Parcours Interactif (Frontend / Déclencheurs UI)
> *Cartographie exhaustive des composants interactifs de l'écran et de leurs transitions d'état.*

| Élément UI | Déclencheur | Action Déclarative (Navigation / API) | Feedback & Changement d'État |
| :--- | :--- | :--- | :--- |
| Ressource cockpit d'architecture | Appel de l'outil `show_architecture` | Rendu de la ressource `ui://archify/cockpit` dans le cadre de l'IDE, état initial du projet transmis par paramètre d'adresse | Cadre en Chargement puis Succès ; animation des particules et navigation libres |
| Ressource schéma relationnel | Appel de l'outil `show_database_schema` | Rendu de la ressource `ui://drawdb/schema` dans le cadre de l'IDE | Zoom et déplacement actifs dès le Chargement terminé |
| Cadre affiché (projet actif) | Message de changement de projet émis par le chat | Mise à jour en place du contenu du cadre sans rechargement | Conservation du zoom et du déplacement, aucun retour à l'état initial |
| Cadre affiché (redimensionnement) | Largeur du cadre inférieure au seuil partagé `UI_MIN_WIDTH_PX = 320` | Affichage de la bannière « ouvrir dans le navigateur » | Bannière non bloquante ; le cadre reste rendu mais signale l'étroit |
| Bannière de repli | Clic / Tap sur « ouvrir dans le navigateur » | Ouverture de l'adresse locale correspondante (serveur local du schéma relationnel ou page autonome du cockpit) dans le navigateur | Visualisation complète hors de l'IDE |
| Appel d'outil sur client sans support de l'extension | Appel de `show_architecture` ou `show_database_schema` | Retour de l'adresse locale correspondante en lieu et place de la ressource | Dégradation gracieuse : message d'information, aucun échec d'appel |

### Contrats d'Échange API (Backend / Services)
> *Règle Zéro Fausse Route : aucune route REST n'est définie par ce récit. Les seuls contrats sont les réponses d'outils du protocole MCP et le pont de messages entre le chat et le cadre.*

- **Affichage du cockpit d'architecture** : outil `show_architecture` → ressource `ui://archify/cockpit`.
- **Affichage du schéma relationnel** : outil `show_database_schema` → ressource `ui://drawdb/schema`.
- **État initial du projet** : paramètre d'adresse `?project=<nom>` porté par la ressource `ui://` au rendu initial du cadre.
- **Synchronisation du projet actif** : message `project_changed` émis du chat vers le cadre à chaque changement de projet, déclenchant une mise à jour en place.
- **Politique de repli** : sur client sans support de l'extension ou largeur de cadre sous le seuil, retour ou ouverture de l'adresse locale du visualiseur (port `8081` pour le schéma relationnel, route de page HTML autonome pour le cockpit).

> ⚠️ **Questions ouvertes à définir** : le contrat exact de livraison des ressources `ui://` (contenu HTML embarqué dans la réponse versus référence d'adresse) n'est pas vérifié dans la spécification externe — **OQ-212-01, à définir** avant le build. Le choix d'implémentation du rendu du schéma relationnel vivant (passerelle face au serveur local versus instantané HTML autonome) reste un point d'implémentation à trancher au plan — **OQ-212-02, à définir**. La vérification des dimensions nominales imposées par les clients hôte est batchée avec la tâche de conformité du socle en amont (délégation actée en micro-grill, sans question triviale posée à l'humain).

---

## Règles d'affaires

- **Source de vérité unique du projet actif** : l'état du pont fait seule foi pour le projet affiché dans le cadre ; aucune seconde source d'état n'est créée, l'état initial est transmis par paramètre d'adresse et les changements ultérieurs par message du chat vers le cadre.
- **Lecture seule absolue en première version** : le cadre n'émet aucune écriture vers le chat ni vers le pont, et n'effectue aucun appel réseau depuis son intérieur ; la politique de connexion refusée de son enveloppe de sécurité est préservée à l'identique.
- **Seuil de repli dimensionnel partagé** : la largeur minimale exploitable du cadre est `UI_MIN_WIDTH_PX = 320`, déclarée une seule fois dans un registre partagé et révisable sans libération de version ; tout passage sous ce seuil déclenche l'affichage de la bannière « ouvrir dans le navigateur ».
- **Repli par adresse locale** : si le client hôte ne supporte pas l'extension d'affichage embarqué, l'appel retourne gracieusement l'adresse locale du visualiseur (serveur local du schéma relationnel, page HTML autonome du cockpit) ; jamais d'échec d'appel pour défaut de support.
- **Adresses officielles conformes à la spécification** : seules `ui://archify/cockpit` et `ui://drawdb/schema` sont déclarées ; toute adresse divergente est non conforme.
- **Isolation du cadre** : le sandbox autorise le script interne mais interdit l'accès au stockage local de l'IDE hôte, l'isolement des jetons et toute connexion réseau sortante depuis le contenu rendu.
- **Mise à jour sans rechargement** : un changement de projet actualise le contenu du cadre en place et conserve la navigation (zoom, déplacement) en cours.
- **Gestion des contenus invalides** : une ressource inconnue du registre d'adresses ou un cadre rendu sous le seuil ne provoque jamais une erreur bloquante pour l'utilisateur ; le système dégrade gracieusement vers l'adresse locale ou la bannière, sans altérer l'état des autres affichages.

---

## Références

### 1. Preuves Amont & Traçabilité Factuelle
- 📂 **Dossier de Preuves Factuelles** : [`memory/evidence/MLOOP-212-FE_fact_dossier.md`](../../memory/evidence/MLOOP-212-FE_fact_dossier.md)

### 2. Spécifications & Modèles de Données SSOT
- 🏛️ **ADR d'Architecture (SSOT technique)** : [ADR-0387 — Intégration des Standards MCP Modernes 2026-07-28, Pilier 2 « MCP Apps »](../../../../standards/adr-system/0387-mcp-modern-spec-2026-07-28-tasks-ui-elicitation-architecture.md)
- 📋 **Micro-Grill du récit (2 décisions)** : [ADR-007 — Micro-grill MLOOP-212-FE](../../../docs/01-architecture/ADR-007_micro-grill_mloop-212-fe__2_decisions.md)
- 📋 **Cadrage Macro Grill** : [ADR-004 — EPIC-21-MCP-MODERN-SUITE](../../../docs/01-architecture/ADR-004_epic-21-mcp-modern-suite_-_cadrage_macro_grill__6_decisions.md)
- 📚 **Épopée de rattachement** : [EPIC-21 — MCP Modern Suite 2026Q4](../epics/epic_mcp_modern_suite_2026q4.md)

---

## Scénarios de test

```gherkin
# language: fr
Fonctionnalité: Extension MCP Apps — Exposition ui:// pour Archify Cockpit & DrawDB ERD

  # CHEMIN NOMINAL (Happy Path & Persistance)
  Scénario: Affichage nominal des deux ressources ui:// dans l'IDE
    Étant donné un utilisateur actif sur un projet dans la conversation de l'agent
    Quand l'outil "show_architecture" est appelé
    Alors la ressource "ui://archify/cockpit" est rendue dans le cadre de l'IDE
    Et l'état initial du projet est transmis par paramètre d'adresse
    Et l'animation du cockpit est active sans requête réseau sortante depuis le cadre
    Quand l'outil "show_database_schema" est appelé
    Alors la ressource "ui://drawdb/schema" est rendue dans le cadre de l'IDE
    Et le zoom et le déplacement du schéma sont opérationnels

  # EXCEPTIONS & REJETS MÉTIER (Règles d'affaires)
  Scénario: Appel d'outil sur client hôte sans support de l'extension ui://
    Étant donné un client hôte qui ne négocie pas l'extension d'affichage embarqué
    Quand l'outil "show_architecture" ou "show_database_schema" est appelé
    Alors l'adresse locale correspondante est retournée en solution de secours
    Et l'appel aboutit sans erreur bloquante
    Et aucune ressource ui:// n'est prétendue rendue

  Scénario: Adresse de ressource hors registre des adresses officielles
    Étant donné une demande visant une adresse absente du registre "ui://archify/cockpit" et "ui://drawdb/schema"
    Quand le pont contrôle l'adresse déclarée
    Alors la demande est refusée comme non conforme
    Et aucun cadre n'est rendu à partir d'une adresse divergente

  # RÉSILIENCE TECHNIQUE & MODE DÉGRADÉ (Timeouts, Idempotence, Concurrence)
  Scénario: Repli par bannière lorsque la largeur du cadre passe sous le seuil
    Étant donné un cadre affichant une ressource ui:// valide
    Quand la largeur du cadre devient inférieure à UI_MIN_WIDTH_PX fixé à 320 dans le registre partagé
    Alors la bannière "ouvrir dans le navigateur" s'affiche sans bloquer le cadre
    Et un clic sur la bannière ouvre l'adresse locale du visualiseur correspondant
    Et le cadre reste rendu en mode dégradé sans erreur

  Scénario: Isolement réseau préservé à l'intérieur du cadre
    Étant donné un contenu rendu dans le cadre sandboxé
    Quand le contenu tente une connexion réseau sortante
    Alors la politique de connexion refusée bloque la tentative
    Et le rendu et la navigation locale continuent sans interruption

  Scénario: Mise à jour en place lors d'un changement de projet
    Étant donné un cadre affichant la ressource du projet actif
    Quand le chat émet le message de changement de projet
    Alors le contenu du cadre est actualisé sans rechargement
    Et le zoom et le déplacement en cours sont conservés
    Et l'état du pont demeure la source de vérité unique du projet affiché

  # UX, OBSERVABILITÉ & EMPTY STATE (Spinners, Retours Écran, Logs)
  Scénario: Indicateurs de progression, états de surface et traçabilité du repli
    Étant donné le déclenchement de l'affichage d'une ressource ou l'absence de support de l'extension
    Quand le cadre est en cours de rendu
    Alors un indicateur de chargement s'affiche jusqu'à l'état de succès
    Et en cas de client sans support, un message de dégradation gracieuse accompagne le retour de l'adresse locale
    Et chaque activation de la bannière de repli ou de la remise d'adresse de secours est journalisée
    Et aucun appel réseau sortant n'est émis depuis le cadre à aucun moment
```