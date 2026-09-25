---
id: MLOOP-252-BE
jira_key: ''
epic_key: EPIC-25-OPENCODE-ECOSYSTEM-HARNESS
type: Feature
title: "Intégration du Session Forking dans les Rituels Grill-Me & Doubt-Driven"
tags:
- opencode
- session-forking
- grill-me
- doubt-driven
- backend
origin: SPEC_SLICING
source_ref: EPIC-25-§3
macro_size: M
status: SHIPPED
grill_me: DONE
invest_score: 6/6
validated_by: Marco (PO)
validated_at: '2026-09-25'
layer: backend
blocked_by:
- MLOOP-250-BE
created_at: '2026-09-24'
updated_at: '2026-09-25'
---

# 📖 MLOOP-252-BE : Intégration du Session Forking dans les Rituels Grill-Me & Doubt-Driven

## Description
**En tant qu'** Orchestrateur mLoop ou Développeur en session de cadrage,  
**je veux** piloter programmatiquement le Session Forking d'OpenCode (`opencode --fork --session <id>`),  
**afin d'** explorer des variantes d'architecture ou exécuter des revues contradictoires aveugles (Doubt-Driven Development) sur une branche fille isolée sans altérer l'historique principal.

---

## Contexte & Périmètre

### Contexte Métier
Lors des rituels de cadrage (Grill-Me) et des revues contradictoires, explorer des choix d'implémentation alternatifs ou soumettre du code à un relecteur sans son biais d'historique nécessitait auparavant de réinitialiser toute la conversation. OpenCode (v1.18.30+) propose une commande de bifurcation déterministe `--fork`. Ce récit intègre cette capacité directement dans les pipelines mLoop.

**Décisions Grill-Me (2026-09-25) :**
- Gestion du cycle de vie et gouvernance de rétention conforme à l'**ADR-015** (Data Hygiene) : enregistrement des branches forked dans `memory/sessions/forks_registry.json` avec TTL de 7 jours, purgées automatiquement par le module scratch de fin de sprint.
- Socle déterministe CLI `--fork --session <id>` prioritaire, complété par une détection opportuniste de l'API HTTP si le serveur headless (`opencode serve`) est actif.
- Réconciliation contrôlée : possibilité d'extraire les conclusions de la branche fille pour mettre à jour la story parente.

### In-Scope
- Développement du gestionnaire de branches `src/bridges/opencode/session_forker.py` (≤ 300 lignes, ADR-0202).
- Orchestration de la commande `opencode --fork --session <parent_id>` créant une session fille indépendante.
- Maintien du registre de filiation dans `memory/sessions/forks_registry.json` (parent, enfant, horodatage, motif).
- Intégration dans le rituel de revue contradictoire `doubt-driven` : bifurcation pour audit indépendant.
- Procédure de réconciliation et extraction du résumé de branche vers le dossier de preuves de la story.

### Out-of-Scope
- Fusion automatique sans validation humaine de modifications concurrentes sur le même fichier de code.
- Modification de la base SQLite interne d'OpenCode.

---

## Critères d'acceptation

### Opérations Métier & Logique Backend

#### 1. Gestionnaire de Forking — OpenCodeSessionForker
* **Entrée Métier** : ID de session parent, motif de bifurcation (`GRILL_EXPLORATION`, `DOUBT_REVIEW`).
* **Traitement & Algorithme Métier** :
  - Vérification de l'existence de la session parent.
  - Déclenchement de la bifurcation via CLI ou API HTTP.
  - Attribution d'un identifiant de session fille unique.
  - Enregistrement de l'entrée dans `memory/sessions/forks_registry.json` avec TTL de 7 jours.
* **Résultat Métier & Mutations** : Session fille prête à recevoir des prompts d'évaluation contradictoire sans affecter la session parent.

#### 2. Réconciliation & Nettoyage
* **Traitement** : Extraction des conclusions de la branche fille et archivage ou purge des sessions expirées.
* **Cas de Rejet** : Session parent inexistante ou corrompue $\rightarrow$ rejet avec code d'erreur explicite sans planter l'orchestrateur.

---

## Règles d'affaires

- **Isolation Stricte des Branches** : Aucune mutation réalisée dans la session fille ne doit polluer le contexte ou les fichiers de la session parent avant réconciliation explicite.
- **Hygiène & Rétention 7 Jours** : Les sessions de bifurcation orphelines sont automatiquement éligibles à la purge après 7 jours (ADR-015).
- **Plafond Modulaire AST** : `src/bridges/opencode/session_forker.py` $\le 300$ lignes et $\le 15$ Ko (ADR-0202).

---

## Références

### 1. Preuves Amont & Traçabilité Factuelle
- 📂 **Pipeline Grill** : `src/pipelines/grill_engine.py`
- 📂 **Hygiène Mémoire** : `src/commands/handlers/memory_hygiene.py`
- 🏛️ **ADR** : [ADR-0015](../../../standards/adr-system/0015-hygiene-stockage-retention-ebbinghaus.md) · [ADR-0375](../../../standards/adr-system/0375-standard-preuve-epistemique-et-tracabilite-radicale.md) · [ADR-0202](../../../standards/adr-system/0202-modularite-interne-agents.md)
- 📋 **Epic** : [`epics/epic_opencode_ecosystem_harness.md`](../epics/epic_opencode_ecosystem_harness.md)

---

## Scénarios de test

```gherkin
# language: fr
Fonctionnalité: Session Forking OpenCode pour Grill-Me & Doubt-Driven

  Scénario: Pilier 1 - Nominal (Happy path) : Bifurcation réussie d'une session de cadrage
    Étant donné une session OpenCode active avec id="sess-parent-001"
    Quand j'appelle OpenCodeSessionForker.fork_session("sess-parent-001", reason="GRILL_EXPLORATION")
    Alors une nouvelle session fille id="sess-child-002" est créée
    Et forks_registry.json enregistre la filiation avec un TTL de 7 jours
    Et l'historique parent reste inchangé

  Scénario: Pilier 2 - Exceptions (Cas d'erreur) : Session parent introuvable
    Étant donné un identifiant de session inexistant "sess-invalide-999"
    Quand je tente de bifurquer cette session
    Alors une exception SessionNotFoundError est levée
    Et aucun fichier de registre n'est altéré

  Scénario: Pilier 3 - Résilience (Nettoyage & Rétention) : Purge des forks expirés après 7 jours
    Étant donné une session fille créée il y a plus de 7 jours dans forks_registry.json
    Quand le nettoyeur de rétention s'exécute lors du rituel de fin de sprint
    Alors l'entrée de registre est archivée ou purgée
    Et l'espace disque scratch est libéré sans impacter les artefacts certifiés

  Scénario: Pilier 4 - UX (Accessibilité & Traçabilité) : Consultation du graphe des sessions
    Étant donné plusieurs sessions forked rattachées à une story
    Quand un développeur interroge l'arbre des sessions via l'API ou le CLI
    Alors un affichage textuel arborescent clair montre les branches et leurs motifs respectifs
```
