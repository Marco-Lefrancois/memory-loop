---
id: MLOOP-264-FULL
jira_key: ""
epic_key: EPIC-26-CLINE-ECOSYSTEM-HARNESS
type: Feature
title: "Commandes CLI mLoop cline-sync & Harnais de Validation Pré-Vol Vibe-Check"
tags: [cli, vibe-check, cline, sync, backend]
status: DONE_TESTED
layer: backend
invest_score: 6/6
grill_me: DONE
blocked_by: [MLOOP-260-BE, MLOOP-261-BE]
created_at: "2026-09-24T14:15:00"
updated_at: "2026-09-24T14:46:00"
validated_by: Marco
validated_at: "2026-09-25T12:08:50.485909+00:00"

---

# 📖 MLOOP-264-FULL : Commandes CLI mLoop cline-sync & Harnais de Validation Pré-Vol Vibe-Check

---

## Description
**En tant que** Développeur et Utilisateur de Cline dans un projet mLoop,  
**je veux** disposer d'une commande CLI `mloop cline-sync` et d'un contrôle pré-vol automatique dans `vibe-check`,  
**afin de** synchroniser la Memory Bank, projeter les configurations de serveurs MCP, vérifier la parité des règles `.clinerules` et m'assurer que Cline opère en conformité totale avec les standards de qualité mLoop.

---

## Contexte & Périmètre

### Contexte Métier
Pour garantir une expérience de développement fluide sans divergence de contexte entre l'environnement mLoop (CLI, swarm, ADRs) et l'extension Cline sous VS Code, les ponts de parité doivent pouvoir être actualisés et vérifiés à tout moment.  
Ce récit livre le harnais de commande utilisateur et les vérifications pré-vol :
1. **Auto-guérison déterministe (Grill-Me Q1 - Option A)** : `vibe-check` et `cline-sync` régénèrent automatiquement les fichiers miroirs `.clinerules` et la Memory Bank manquants ou désynchronisés.
2. **Projection MCP Complète (Grill-Me Q2 - Option A)** : Synchronisation automatique des serveurs MCP déclarés dans mLoop vers `cline_mcp_settings.json`.

### In-Scope
- Commande CLI Click `mloop cline-sync [--project <nom>]` :
  - Projette les 6 fichiers de la Memory Bank (`memory-bank/`).
  - Génère et met à jour `.clinerules/mloop.md`.
  - Projette les serveurs MCP enregistrés vers `cline_mcp_settings.json`.
- Commande CLI Click `mloop cline-status [--project <nom>]` :
  - Restitution déterministe de la présence du binaire `cline`, de la version active, du statut de la Memory Bank et des serveurs MCP configurés.
- Contrôle dans `vibe-check` (`src/pipelines/vibe_check/_vc_agents.py`) :
  - Vérification de la parité `.clinerules/mloop.md` avec auto-guérison.
- Documentation SSOT : Intégration dans le Guide CLI (ADR-0370).

### Out-of-Scope
- Forcer le redémarrage de VS Code côté utilisateur.
- Modification des clés d'API personnelles des fournisseurs tiers dans les paramètres de Cline.

---

## Critères d'acceptation

### Opérations Métier & Logique Backend

#### 1. Opération `run_cline_sync(project_dir: Path, auto_fix: bool = True) -> Dict[str, Any]`
* **Entrée Métier** : Chemin racine du projet et indicateur d'auto-remédiation.
* **Règles d'admissibilité & Validation** : Le répertoire projet doit être valide ; si un champ vide ou des données partielles sont fournis, la requête est rejetée avec un code d'erreur explicite.
* **Traitement & Algorithme Métier** :
  1. Instancier `MemoryBankBridge` et invoquer `sync_from_mloop()`.
  2. Instancier `ClineRulesMirror` et invoquer `generate_mirror_rules()`.
  3. Exporter la configuration MCP vers `cline_mcp_settings.json`.
* **Résultat Métier & Mutations** : Rapport d'exécution structuré indiquant les fichiers créés ou modifiés.
* **Cas de Rejet Métier** : Répertoire non accessible en écriture.

#### 2. Opération `get_cline_status(project_dir: Path) -> Dict[str, Any]`
* **Entrée Métier** : Chemin du projet.
* **Règles d'admissibilité & Validation** : Aucune mutation disque.
* **Traitement & Algorithme Métier** :
  1. Sonde de détection du binaire `cline` via `shutil.which()`.
  2. Contrôle de l'existence des 6 fichiers de la Memory Bank.
  3. Contrôle de l'existence de `.clinerules/mloop.md`.
* **Résultat Métier & Mutations** : Dictionnaire d'état opérationnel complet.

---

### Contrats d'échange API (Interface Python)

#### Matrice des Contrats API
- **OQ-264 (Exemption Zéro Fausse Route)** : Exemption complète de la Matrice des Contrats API réseau — commande CLI Click locale et harnais d'inspection de fichiers sans endpoint REST exposé `[API de soumission à définir]` ; tout service de télémétrie distant éventuel sera spécifié dans un récit distinct (ADR-0319).

```python
from pathlib import Path
from typing import Dict, Any

class ClineCliHarness:
    """Harnais d'orchestration CLI pour l'écosystème Cline."""

    @staticmethod
    def sync_ecosystem(project_path: Path) -> Dict[str, Any]:
        """Synchronise Memory Bank, règles et serveurs MCP."""
        ...

    @staticmethod
    def inspect_status(project_path: Path) -> Dict[str, Any]:
        """Inspecte la présence et la cohérence de la suite Cline."""
        ...
```

---

### Contraintes Techniques & Performance
- **Plafond Modulaire (ADR-0202)** : Tout nouveau fichier sous `src/cli/commands/` reste sous la barre des 300 lignes de code.
- **Vitesse d'Exécution** : Synchronisation complète réalisée en moins de 300 millisecondes sur disque local.
- **Idempotence** : Plusieurs exécutions successives de `cline-sync` ne génèrent aucune modification si l'état source n'a pas changé.

---

## Scénarios de test (4 Piliers Gherkin)

### Pilier 1 : Nominal (Happy Path — Synchronisation Complète Réussie)
```gherkin
SCÉNARIO: Synchronisation nominale de l'environnement Cline
ÉTANT DONNÉ un projet mLoop valide avec un backlog actif
QUAND l'utilisateur exécute la commande 'mloop cline-sync'
ALORS les 6 fichiers de la Memory Bank sous Projects/<Projet>/memory/memory-bank/ sont mis à jour
ET le fichier .clinerules/mloop.md est généré en conformité avec CONSTRAINTS.md
ET les serveurs MCP configurés sont exportés vers cline_mcp_settings.json.
```

### Pilier 2 : Exceptions & Rejets Métier (Validation des Paramètres & Saisies)
```gherkin
SCÉNARIO: Rejet de commande avec argument invalide ou champ vide
ÉTANT DONNÉ une invocation de 'mloop cline-sync' avec un projet inexistant ou champ vide
QUAND le parseur CLI évalue les options
ALORS la commande s'interrompt avec une erreur explicite sans modifier le système de fichiers.
```

### Pilier 3 : Résilience & Mode Dégradé (Auto-Guérison Vibe-Check & Anti-Rebond)
```gherkin
SCÉNARIO: Auto-guérison transparente lors du contrôle vibe-check
ÉTANT DONNÉ un projet où le fichier .clinerules/mloop.md a été accidentellement supprimé
QUAND la commande 'mloop vibe-check' est exécutée
ALORS le contrôle détecte l'absence du fichier miroir
ET régénère immédiatement le fichier manquant en mode auto-guérison
ET le contrôle retourne l'état PASS avec un avertissement de remédiation consigné.

SCÉNARIO: Protection anti-rebond sur invocations concurrentes
ÉTANT DONNÉ deux exécutions concurrentes de cline-sync déclenchées rapidement (double-clic ou double soumission)
QUAND le système traite les requêtes
ALORS un verrou atomique garantit une écriture séquentielle sans corruption de fichier.
```

### Pilier 4 : Sécurité & Performance (Confinement & Confidentialité)
```gherkin
SCÉNARIO: Préservation stricte des secrets et clés d'API
ÉTANT DONNÉ l'exportation des configurations vers cline_mcp_settings.json
QUAND la synchronisation s'achève
ALORS aucune clé secrète en clair n'est copiée en dehors de son conteneur sécurisé
ET les droits d'accès aux fichiers générés respectent les permissions utilisateur de la session.

SCÉNARIO: Traitement d'un token expiré ou session expirée
ÉTANT DONNÉ une session expirée ou un token expiré lors d'une tentative de synchronisation MCP distante
QUAND l'adaptateur tente de requérir les métadonnées
ALORS une notification 401 explicite est renvoyée sans planter la boucle principale.
```

---

## 5. Definition of Ready (DoR 6/6)
- [x] **Clarté du besoin & non-ambiguïté** : Commande CLI `cline-sync`, statut `cline-status` et garde-fou `vibe-check`.
- [x] **Architecture & Contrats clarifiés** : Exemption d'API réseau OQ-264 formalisée et interface Python documentée.
- [x] **Critères d'acceptation 4 Piliers Gherkin** : Piliers nominal, validation, résilience (auto-guérison) et sécurité rédigés.
- [x] **Dépendances identifiées & levées** : MLOOP-260-BE et MLOOP-261-BE validés au Palier 2.
- [x] **Estimations et découpage validés** : Enveloppe macro M, sous plafond modulaire ADR-0202 ($\le 300$L).
- [x] **Session Grill-Me complétée** : 2 décisions actées et consignées ci-dessous.

---

## 6. Traçabilité & Historique Grill-Me (Session du 24/09/2026)

| Réf Question | Question Grill-Me | Option Retenue | Justification & Ancrage SSOT |
| :--- | :--- | :--- | :--- |
| **Q1** | Quelle politique d'auto-remédiation appliquer dans vibe-check et cline-sync ? | **Option A : Auto-guérison transparente** | Restaure automatiquement les miroirs de règles et la Memory Bank pour éliminer toute friction utilisateur. |
| **Q2** | Faut-il synchroniser automatiquement les serveurs MCP mLoop avec cline_mcp_settings.json ? | **Option A : Support parité MCP complète** | Permet à Cline d'utiliser immédiatement les outils d'ingénierie et d'exploration de mLoop sans configuration manuelle. |
