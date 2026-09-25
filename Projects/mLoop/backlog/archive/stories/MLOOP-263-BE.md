---
id: MLOOP-263-BE
jira_key: ""
epic_key: EPIC-26-CLINE-ECOSYSTEM-HARNESS
type: Enabler
title: "Adaptateur Worker Cline Agent Teams (--team-name) pour Swarm Multitâches"
tags: [swarm, cline, agent-teams, worker, backend]
status: DONE_TESTED
layer: backend
invest_score: 6/6
grill_me: DONE
blocked_by: [MLOOP-261-BE, MLOOP-262-BE]
created_at: "2026-09-24T14:15:00"
updated_at: "2026-09-24T14:44:00"
validated_by: Marco
validated_at: "2026-09-25T12:08:50.485909+00:00"

---

# 📖 MLOOP-263-BE : Adaptateur Worker Cline Agent Teams (--team-name) pour Swarm Multitâches

---

## Description
**En tant qu'** Architecte Swarm Core mLoop,  
**je veux** un adaptateur de worker supportant le mode Agent Teams de Cline (`cline --team-name <nom>`),  
**afin de** pouvoir déléguer des tâches complexes ou des épopées entières à une escouade coordonnée de sous-agents spécialistes Cline s'appuyant sur un tableau de tâches partagé et une boîte aux lettres inter-agents, avec un repli déterministe immédiat sur OpenCode en cas d'incident.

---

## Contexte & Périmètre

### Contexte Métier
L'exécution de tâches complexes d'ingénierie logicielle (ADR-0375 Phase 3 Build) nécessite souvent la collaboration d'agents spécialisés (explorateur, testeur, implémenteur). Cline propose une architecture native d'équipes autonomes (`Agent Teams`) via le paramètre `--team-name`, où les agents collaborent via un tableau de bord et une boîte aux lettres partagée dans `~/.cline/data/teams/`.  
Ce récit intègre cette capacité d'orchestration dans le Swarm mLoop via un adaptateur dédié, tout en appliquant deux garde-fous fondamentaux validés lors du Grill-Me 1:1 :
1. **Borne stricte de sous-agents** : un plafond maximal de 3 sous-agents par équipe pour interdire toute récursion ou dérive budgétaire.
2. **Circuit-Breaker Inviolable** : basculement immédiat et transparent vers `opencode --yolo` au moindre incident (binaire absent, erreur Win32, quota épuisé ou crash).

### In-Scope
- Lancement de processus d'équipe Cline via `cline --team-name <story_id> "<prompt>"`.
- Injection et gouvernance du plafond strict de **3 sous-agents au maximum** pour l'équipe (Option A validée en Grill-Me) afin de prévenir tout emballement de tokens.
- Surveillance de l'état d'équipe sous `~/.cline/data/teams/[story_id]/` (tableau de tâches partagé et boîte aux lettres).
- Moissonnage automatique des journaux d'équipe consolidés dans l'EvidencePack de la story (`Projects/<Projet>/memory/evidence/`) dès l'achèvement de la mission, suivi de la purge déterministe du dossier temporaire Cline (Option A validée en Grill-Me).
- **Circuit-Breaker Inviolable vers OpenCode** : basculement immédiat et automatique vers `opencode --yolo` en cas d'absence du binaire Cline, d'erreur de lancement Windows (`%1 Win32`), de dépassement de quota ou de timeout.

### Out-of-Scope
- Orchestration d'équipes d'agents réparties sur plusieurs machines physiques distantes.
- Modification du protocole binaire interne d'échange de messages de Cline.

---

## Critères d'acceptation

### Opérations Métier & Logique Backend

#### 1. Opération `spawn_cline_team_worker(story_id: str, prompt: str, max_subagents: int = 3) -> Dict[str, Any]`
* **Entrée Métier** : Identifiant unique de la story, consigne de mission consolidée et quota de sous-agents.
* **Règles d'admissibilité & Validation** : L'identifiant de story doit être valide ; si un champ vide ou des données partielles sont fournis, la requête est rejetée avec une erreur 400 explicite. Si `cline` n'est pas opérationnel, déclenchement immédiat du Circuit-Breaker.
* **Traitement & Algorithme Métier** :
  1. Construire les arguments : `["cline", "--team-name", story_id, prompt]`.
  2. Démarrer le processus surveillé sous le Watchdog Herdr avec protection anti-rebond et file d'attente atomique.
  3. En cas d'erreur de création de processus ou de timeout d'initialisation, basculer sur OpenCode : `["opencode", "--yolo", prompt]`.
* **Résultat Métier & Mutations** : Dictionnaire d'état du worker (`pid`, `runtime_used`, `team_name`, `status`).
* **Cas de Rejet Métier** : Échec simultané de Cline et du runtime de repli OpenCode.

#### 2. Opération `harvest_team_evidence_and_cleanup(story_id: str, evidence_dir: Path) -> None`
* **Entrée Métier** : Identifiant de la story et chemin cible du dossier de preuves.
* **Règles d'admissibilité & Validation** : Le dossier d'équipe source `~/.cline/data/teams/[story_id]/` doit être accessible.
* **Traitement & Algorithme Métier** :
  1. Lire le journal de mission et les livrables d'équipe.
  2. Écrire le compte-rendu consolidé sous `Projects/<Projet>/memory/evidence/<story_id>_team_log.md`.
  3. Purger intégralement le dossier temporaire `~/.cline/data/teams/[story_id]/` pour garantir l'hygiène disque.
* **Résultat Métier & Mutations** : Artefact de preuves pérenne créé et dossier temporaire supprimé.

---

### Contrats d'échange API (Interface Python)

#### Matrice des Contrats API
- **OQ-263 (Exemption Zéro Fausse Route)** : Exemption complète de la Matrice des Contrats API réseau — composant d'orchestration interne et adaptateur de worker CLI sans aucun endpoint HTTP REST distant exposé `[API de soumission à définir]` ; tout service de télémesure distribuée éventuel fera l'objet d'un récit dédié avec contrat réseau explicite (ADR-0319).

```python
from pathlib import Path
from typing import Dict, Any, Optional

class ClineTeamWorkerAdapter:
    """Adaptateur de worker Swarm gérant les escouades Cline Agent Teams avec repli OpenCode."""

    def __init__(self, workspace_root: Path, max_subagents: int = 3):
        self.workspace_root = workspace_root
        self.max_subagents = max_subagents

    def spawn_team(self, story_id: str, prompt: str) -> Dict[str, Any]:
        """Lance l'équipe Cline ou déclenche le Circuit-Breaker vers OpenCode."""
        ...

    def harvest_and_cleanup(self, story_id: str) -> Path:
        """Moissonne les artefacts de l'équipe vers l'EvidencePack et purge le dossier temporaire."""
        ...
```

---

### Contraintes Techniques & Performance
- **Plafond Modulaire (ADR-0202)** : Tout nouveau fichier ou modification sous `src/core/` reste strictement $\le 300$ lignes de code effectives.
- **Réactivité du Circuit-Breaker** : Bascule vers OpenCode en moins de 500 millisecondes sans interruption bloquante de l'ordonnanceur.
- **Hygiène Disque** : Aucun dossier orphelin ne subsiste dans `~/.cline/data/teams/` à l'issue de l'exécution d'une tâche.

---

## Scénarios de test (4 Piliers Gherkin)

### Pilier 1 : Nominal (Happy Path — Déploiement d'une Équipe)
```gherkin
SCÉNARIO: Lancement et coordination d'une équipe Cline avec moissonnage
ÉTANT DONNÉ une story complexe 'MLOOP-264-FULL' avec le runtime configuré sur 'cline_team'
QUAND Herdr exécute spawn_team() pour initialiser la mission
ALORS le processus Cline démarre avec les arguments '--team-name' et 'MLOOP-264-FULL'
ET le plafond de sous-agents est borné à 3 au maximum
ET à l'issue de la mission les artefacts sont archivés dans l'EvidencePack et le dossier temporaire est purgé.
```

### Pilier 2 : Exceptions & Rejets Métier (Validation des Saisies & Plafond)
```gherkin
SCÉNARIO: Interception d'une tentative de spawn au-delà du plafond autorisé
ÉTANT DONNÉ une équipe Cline active ayant déjà 3 sous-agents enregistrés
QUAND un coordinateur tente d'instancier un 4ème sous-agent
ALORS le superviseur Herdr intercepte la demande et la refuse
ET une alerte de dépassement de quota est consignée dans le journal d'événements.

SCÉNARIO: Rejet de saisie incomplète ou champ vide
ÉTANT DONNÉ une requête d'instanciation avec prompt vide ou champ vide
QUAND la fonction spawn_team() est invoquée
ALORS la validation échoue immédiatement avec un code d'erreur explicite
ET aucun processus orphelin n'est créé.
```

### Pilier 3 : Résilience & Mode Dégradé (Circuit-Breaker vers OpenCode & Anti-Rebond)
```gherkin
SCÉNARIO: Repli déterministe immédiat sur OpenCode lors d'un échec de Cline
ÉTANT DONNÉ une tentative de lancement d'équipe Cline déclenchant une coupure réseau, timeout ou code 503
QUAND le processus Cline lève une exception d'exécution
ALORS le Circuit-Breaker intercepte immédiatement l'incident en moins de 500ms
ET un worker de secours 'opencode --yolo' est instancié sans interruption
ET un avertissement explicite est consigné dans les métriques de fiabilité.

SCÉNARIO: Protection anti-rebond sur double-clic ou soumission concurrente
ÉTANT DONNÉ une demande d'exécution d'équipe en cours de démarrage
QUAND une seconde invocation identique survient simultanément (double-clic ou double soumission)
ALORS le mécanisme anti-rebond ignore la requête redondante
ET une seule instance d'équipe est conservée active.
```

### Pilier 4 : Sécurité & Performance (Confinement & Expiration)
```gherkin
SCÉNARIO: Nettoyage étanche des répertoires temporaires post-mission
ÉTANT DONNÉ une mission d'équipe Cline terminée
QUAND le moissonnage des preuves est validé par harvest_and_cleanup()
ALORS le répertoire temporaire ~/.cline/data/teams/[story_id]/ est complètement supprimé
ET aucun secret d'authentification ou jeton n'est persisté en clair.

SCÉNARIO: Gestion d'un token expiré ou session expirée
ÉTANT DONNÉ une session expirée ou un token expiré lors de la communication inter-agents
QUAND un sous-agent tente d'envoyer un message
ALORS l'adaptateur consigne une erreur 401 et interrompt la communication en mode sécurisé.
```

---

## 5. Definition of Ready (DoR 6/6)
- [x] **Clarté du besoin & non-ambiguïté** : Périmètre délimité à l'adaptation de worker Cline Agent Teams avec repli OpenCode.
- [x] **Architecture & Contrats clarifiés** : Exemption d'API réseau OQ-263 formalisée et interface Python documentée.
- [x] **Critères d'acceptation 4 Piliers Gherkin** : Piliers nominal, exceptions, résilience (Circuit-Breaker) et sécurité rédigés.
- [x] **Dépendances identifiées & levées** : MLOOP-261-BE et MLOOP-262-BE validés au Palier 2.
- [x] **Estimations et découpage validés** : Enveloppe macro L, sous plafond modulaire ADR-0202 ($\le 300$L).
- [x] **Session Grill-Me complétée** : 2 décisions actées et consignées ci-dessous.

---

## 6. Traçabilité & Historique Grill-Me (Session du 24/09/2026)

| Réf Question | Question Grill-Me | Option Retenue | Justification & Ancrage SSOT |
| :--- | :--- | :--- | :--- |
| **Q1** | Comment borner la prolifération de sous-agents au sein de l'équipe Cline ? | **Option A : Plafond strict à 3 sous-agents** | Évite toute dérive récursive de coût ou de jetons, gouverné par `.clinerules/mloop.md` et surveillé par Herdr. |
| **Q2** | Quel cycle de vie et politique de rétention appliquer aux dossiers d'état d'équipes ? | **Option A : Moissonnage EvidencePack puis purge propre** | Centralisation pérenne des traces d'audit dans `memory/evidence/` et hygiène disque irréprochable sans accumulation résiduelle. |
