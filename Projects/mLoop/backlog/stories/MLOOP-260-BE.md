---
id: MLOOP-260-BE
jira_key: ''
epic_key: EPIC-26-CLINE-ECOSYSTEM-HARNESS
type: Feature
title: Bridge de Mémoire Bidirectionnel mLoop <-> Cline Memory Bank
tags:
- bridges
- cline
- memory
- backend
status: DONE_TESTED
layer: backend
invest_score: 6/6
grill_me: DONE
created_at: '2026-09-24T14:15:00'
updated_at: '2026-09-24T14:31:00'
ttl_cycles: 4
validated_by: Marco
validated_at: "2026-09-25T12:08:50.485909+00:00"

---

# 📖 MLOOP-260-BE : Bridge de Mémoire Bidirectionnel mLoop <-> Cline Memory Bank

---

## Description
**En tant que** Développeur utilisant l'extension ou le CLI Cline sur un projet mLoop,  
**je veux** que le contexte actif de sprint et les EvidencePacks soient automatiquement traduits dans le standard `memory-bank/` sous `Projects/<Projet>/memory/memory-bank/`, avec réconciliation inverse des découvertes,  
**afin que** Cline dispose immédiatement d'une mémoire de projet persistante sans amnésie et que ses trouvailles de session enrichissent durablement les EvidencePacks mLoop.

---

## Contexte & Périmètre

### Contexte Métier
Les agents autonomes de code (comme Cline) perdent leur état entre deux fenêtres de discussion. Cline s'appuie sur une discipline documentaire standardisée appelée **Memory Bank** (6 fichiers structurés) pour conserver la mémoire architecturale et opérationnelle.  
Plutôt que d'obliger l'ingénieur à rédiger manuellement cette Memory Bank ou de tolérer une divergence avec le backlog mLoop, ce récit implémente une passerelle bidirectionnelle souveraine : mLoop projette son état épistémique vers Cline à l'amorçage, et moissonne les découvertes de Cline lors de la synchronisation.

### In-Scope
- **Emplacement Intra-Projet Dédié** : Génération des 6 fichiers standardisés exclusivement sous `Projects/<project_name>/memory/memory-bank/` (zéro pollution de la racine du dépôt).
- **Les 6 Fichiers Standardisés** :
  1. `projectbrief.md` : Vision du projet, mission et exigences fondamentales.
  2. `productContext.md` : Problèmes résolus et parcours utilisateurs clés.
  3. `activeContext.md` : Focus chirurgical du sprint actif (stories `READY_FOR_DEV`, `IN_PROGRESS`, `BLOCKED`, et 3 dernières `DONE`).
  4. `systemPatterns.md` : Architecture mLoop, ADRs clés (ADR-0202, ADR-0346, ADR-0375, ADR-0376, ADR-0377).
  5. `techContext.md` : Stack Python 3.11+, pytest, Herdr, commandes CLI souveraines.
  6. `progress.md` : Métriques consolidées du backlog (total, terminés, en cours).
- **Idempotence Stricte** : Aucune réécriture physique de fichier si le contenu généré est identique (préservation des horodatages `mtime`).
- **Moissonnage Bidirectionnel (*Harvesting*)** : Détection des sections annotées par l'agent ou le développeur sous le titre `## Notes de Session` dans `activeContext.md`, et réinjection dans l'attribut `session_notes` de l'EvidencePack de la story active.
- **Routage Documentaire** : Consigne dans `.clinerules/mloop.md` indiquant à Cline l'emplacement exact de sa Memory Bank.

### Out-of-Scope
- Altération du code binaire ou du moteur interne de Cline.
- Remplacement du format natif des EvidencePacks mLoop (la Memory Bank est une projection sidecar).
- Synchronisation réseau distante (le mécanisme opère 100% hors-ligne en local).

---

## Critères d'acceptation

### Opérations Métier & Logique Backend

#### 1. Opération `sync_memory_bank(project_path: Path) -> Dict[str, Path]`
* **Entrée Métier** : Chemin absolu ou relatif vers le dossier du projet cible sous `Projects/<project_name>`.
* **Règles d'admissibilité & Validation** : Le dossier du projet doit exister et comporter un répertoire `backlog/` ou `memory/`.
* **Traitement & Algorithme Métier** :
  1. Résolution de l'emplacement cible : `project_path / "memory" / "memory-bank"`.
  2. Extraction chirurgicale des métadonnées du sprint actif depuis `sprint_backlog.md` (filtrage anti-bloat des stories actives).
  3. Construction en mémoire des 6 documents markdown formatés selon le standard Cline.
  4. Comparaison byte-à-byte avec les fichiers existants pour éviter toute écriture inutile.
* **Résultat Métier & Mutations** : Création ou mise à jour atomique des 6 fichiers sous `memory-bank/`.
* **Cas de Rejet Métier** : Chemin de projet inexistant ou cible non inscriptible (permission refusée).

#### 2. Opération `harvest_cline_notes(project_path: Path, story_id: str) -> bool`
* **Entrée Métier** : Identifiant de la story active (`story_id`) et chemin du projet.
* **Règles d'admissibilité & Validation** : Le fichier `activeContext.md` doit exister et l'EvidencePack cible `memory/evidence/<story_id>_evidence.json` doit être disponible.
* **Traitement & Algorithme Métier** :
  1. Lecture et analyse syntaxique de `activeContext.md`.
  2. Extraction de la section `### Notes de Session & Découvertes`.
  3. Si de nouvelles notes sont présentes et absentes de l'EvidencePack, fusion et mise à jour de l'EvidencePack.
* **Résultat Métier & Mutations** : Enrichissement persistant de `memory/evidence/<story_id>_evidence.json`.
* **Cas de Rejet Métier** : Aucune note nouvelle détectée ou syntaxe non conforme.

---

### Contrats d'échange API (Interface Python)

#### Matrice des Contrats API
- **OQ-260 (Exemption Zéro Fausse Route)** : Exemption complète de la Matrice des Contrats API réseau — opération purement locale sur fichiers markdown (`memory-bank/*.md`) et EvidencePacks JSON, sans interface HTTP réseau ni route REST distante `[API de soumission à définir]` ; toute future exposition d'API distante pour la Memory Bank est à confirmer dans un récit dédié avec sa propre matrice (ADR-0319).

```python
from pathlib import Path
from typing import Dict, List, Optional

class MemoryBankBridge:
    """Passerelle de projection et de moissonnage Memory Bank pour Cline."""

    def __init__(self, workspace_root: Optional[Path] = None, project_name: str = "mLoop") -> None: ...

    def sync_all(self) -> Dict[str, Path]:
        """Génère de façon idempotente les 6 fichiers sous Projects/<project>/memory/memory-bank/."""
        ...

    def harvest_session_notes(self) -> List[str]:
        """Extrait les notes libres rédigées par Cline dans activeContext.md."""
        ...

    def update_evidence_pack(self, story_id: str, notes: List[str]) -> bool:
        """Injecte les notes récoltées dans le sidecar JSON de la story."""
        ...
```

---

### Contraintes Techniques & Performance
- **Plafond Modulaire (ADR-0202)** : Le module `src/bridges/cline/memory_bank_bridge.py` ne doit pas excéder 300 lignes.
- **Performance** : La génération complète des 6 fichiers doit s'exécuter en moins de 150 millisecondes.
- **Zéro Régression Git** : Idempotence garantie, pas de modification d'horodatage si le contenu est stable.

---

## Scénarios de test (4 Piliers Gherkin)

### Pilier 1 : Nominal (Happy Path — Focus Chirurgical)
```gherkin
SCÉNARIO: Projection initiale réussie de la Memory Bank
ÉTANT DONNÉ un projet mLoop avec des récits actifs dans son sprint_backlog.md
QUAND l'opération sync_all() du MemoryBankBridge est déclenchée
ALORS un répertoire 'Projects/mLoop/memory/memory-bank/' est créé
ET les 6 fichiers canoniques sont générés avec un contenu non vide
ET le fichier 'activeContext.md' ne contient que les récits actifs du sprint en cours
ET le fichier 'progress.md' affiche les compteurs agrégés sans saturer la mémoire.
```

### Pilier 2 : Exceptions & Rejets Métier (Chemin Invalide)
```gherkin
SCÉNARIO: Rejet lors d'un chemin de projet introuvable
ÉTANT DONNÉ un chemin de projet inexistant 'Projects/Projet_Inconnu'
QUAND l'opération sync_all() est invoquée
ALORS une exception de validation explicite est levée
ET aucun fichier orphelin n'est créé à la racine du dépôt.
```

### Pilier 3 : Résilience & Idempotence (Préservation Mtime & Anti-Rebond)
```gherkin
SCÉNARIO: Préservation déterministe des fichiers en l'absence de modification
ÉTANT DONNÉ une Memory Bank déjà générée et synchronisée
QUAND la commande de synchronisation est exécutée une seconde fois immédiatement
ALORS l'horodatage mtime des 6 fichiers reste strictement inchangé
ET le statut de synchronisation indique 'inchangé (idempotent)'.

SCÉNARIO: Résilience face aux accès concurrents et anti-rebond
ÉTANT DONNÉ deux invocations quasi-simultanées de sync_all() sur le même projet
QUAND le premier appel est en cours d'écriture
ALORS le second appel temporise de façon non bloquante ou réutilise le contenu atomique sans corruption
ET les 6 fichiers de la Memory Bank conservent une intégrité parfaite.
```

### Pilier 4 : UX / Moissonnage & Observabilité (Harvesting Bidirectionnel)
```gherkin
SCÉNARIO: Réconciliation automatique des notes de Cline vers l'EvidencePack
ÉTANT DONNÉ qu'un agent Cline a ajouté une note technique dans 'activeContext.md' sous '### Notes de Session'
QUAND le pipeline 'mloop sync' est exécuté
ALORS les notes sont extraites par le moissonneur
ET elles sont annexées dans 'Projects/mLoop/memory/evidence/MLOOP-260-BE_evidence.json'
ET un message de journalisation confirme l'enrichissement de l'EvidencePack.
```

---

## Validation DoR 6/6 (Checklist INVEST)

- [x] **Independent** : Le bridge est autonome et découplé du runtime d'exécution Herdr.
- [x] **Negotiable** : Arbitrages validés en session Grill-Me 1:1 (emplacement intra-projet, bidirectionnel, focus chirurgical).
- [x] **Valuable** : Élimine l'amnésie de contexte de Cline et enrichit la base de connaissances mLoop.
- [x] **Estimable** : Taille M (2 jours), architecture délimitée sous `src/bridges/cline/`.
- [x] **Small** : Fichier unique $\le$ 300 lignes avec responsabilité unique de sérialisation documentaire.
- [x] **Testable** : 4 Piliers Gherkin vérifiables par tests unitaires automatisés sous `tests/test_cline_bridge.py`.
