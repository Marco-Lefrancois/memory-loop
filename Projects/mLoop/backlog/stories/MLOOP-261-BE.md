---
id: MLOOP-261-BE
jira_key: ''
epic_key: EPIC-26-CLINE-ECOSYSTEM-HARNESS
type: Feature
title: Génération Automatique de la Parité .clinerules depuis CONSTRAINTS.md & AGENTS.md
tags:
- rules
- cline
- governance
- backend
status: DONE_TESTED
layer: backend
invest_score: 6/6
grill_me: DONE
created_at: '2026-09-24T14:15:00'
updated_at: '2026-09-24T14:39:00'
ttl_cycles: 4
validated_by: Marco
validated_at: "2026-09-25T12:08:50.485909+00:00"

---

# 📖 MLOOP-261-BE : Génération Automatique de la Parité .clinerules depuis CONSTRAINTS.md & AGENTS.md

---

## Description
**En tant qu'** Administrateur Qualité et Développeur mLoop,  
**je veux** que les règles et garde-fous constitutionnels (`CONSTRAINTS.md`, `AGENTS.md`) soient projetés automatiquement dans `.clinerules/mloop.md` et audités au pré-vol,  
**afin que** les sessions d'agents Cline appliquent rigoureusement les mêmes 23 contrôles et interdictions strictes que l'écosystème global sans dérive comportementale.

---

## Contexte & Périmètre

### Contexte Métier
Dans un environnement de développement multi-agents où coexistent Antigravity, OpenCode et Cline, il est impératif d'éviter le *Rule Drift* (dérive des règles). Si Cline n'a pas accès aux règles constitutionnelles mLoop (interdiction de suppression silencieuse de code, plafond de 300 lignes ADR-0202, interdiction de saut de phase ADR-0375), il risque d'altérer l'intégrité de la base de code.  
Ce récit standardise la projection modulaire de nos invariants dans `.clinerules/mloop.md` et intègre son contrôle déterministe dans le pipeline pré-vol `vibe-check`.

### In-Scope
- **Format Modulaire Dédié (Arbitrage Grill-Me Q1 - Option A)** : Génération du fichier de règles sous `.clinerules/mloop.md` pour préserver les éventuels fichiers de règles personnalisées du développeur (zéro écrasement intempestif).
- **Invariants Constitutionnels Projetés** :
  1. Interdiction formelle du saut de phase (obligation du mode `--plan` en Phase 2).
  2. Plafond modulaire strict $\le$ 300 lignes par fichier Python (ADR-0202).
  3. Préservation intangible du code existant et des tests unitaires (zéro suppression sauvage).
  4. Règle d'audit en 7 couches Zéro Blindspot (ADR-0376).
  5. Commandes de validation pré-vol (`pytest`, `vibe-check`).
- **Contrôle Déterministe dans le Vibe-Check (Arbitrage Grill-Me Q2 - Option A)** : Ajout d'une assertion formelle dans le pré-vol vérifiant la présence et la non-vacuité de `.clinerules/mloop.md`.
- **Auto-Healing à la Synchronisation** : Régénération ou réparation automatique lors de l'exécution de `python src/swarm.py sync`.

### Out-of-Scope
- Altération des fichiers de configuration internes de Cline sous `~/.cline/data/`.
- Modification des règles personnelles situées hors de `mloop.md` (ex: `.clinerules/custom.md`).

---

## Critères d'acceptation

### Opérations Métier & Logique Backend

#### 1. Opération `sync_cline_rules(workspace_root: Path) -> Path`
* **Entrée Métier** : Chemin racine de l'espace de travail.
* **Règles d'admissibilité & Validation** : Le dossier `.clinerules/` doit être créé si absent ; l'écriture doit être atomique.
* **Traitement & Algorithme Métier** :
  1. Extraction des règles constitutionnelles standardisées mLoop.
  2. Formatage au standard markdown avec en-tête d'avertissement d'auto-génération.
  3. Vérification de hash pour garantir une écriture 100% idempotente.
* **Résultat Métier & Mutations** : Création ou mise à jour de `.clinerules/mloop.md`.
* **Cas de Rejet Métier** : Dossier parent non accessible en écriture.

#### 2. Opération `audit_clinerules_parity(workspace_root: Path) -> Dict[str, Any]`
* **Entrée Métier** : Chemin racine vérifié par `vibe-check`.
* **Règles d'admissibilité & Validation** : Le fichier `.clinerules/mloop.md` doit exister et faire plus de 100 octets.
* **Traitement & Algorithme Métier** :
  1. Vérification d'existence de `.clinerules/mloop.md`.
  2. Validation de la présence des marqueurs clés (`ADR-0376`, `ADR-0202`, `ADR-0375`, `--plan`).
  3. Émission du statut `PASS` si conforme, sinon `WARNING` avec recommandation de sync.
* **Résultat Métier & Mutations** : Résultat de contrôle inclus dans le rapport final du `vibe-check`.
* **Cas de Rejet Métier** : Fichier manquant ou corrompu.

---

### Contrats d'échange API (Interface Python)

#### Matrice des Contrats API
- **OQ-261 (Exemption Zéro Fausse Route)** : Exemption complète de la Matrice des Contrats API réseau — opération purement locale sur fichiers markdown de règles (`.clinerules/mloop.md`) et contrôle statique de pré-vol, sans interface HTTP réseau ni route REST distante `[API de soumission à définir]` ; toute future exposition d'API distante pour les règles est à confirmer dans un récit dédié avec sa propre matrice (ADR-0319).

```python
from pathlib import Path
from typing import Dict, Any

class ClineRulesMirror:
    """Générateur et vérificateur de parité des règles mLoop pour Cline."""

    def __init__(self, workspace_root: Path | None = None) -> None: ...

    def sync(self) -> Path:
        """Génère de façon idempotente .clinerules/mloop.md."""
        ...

    def verify_parity(self) -> Dict[str, Any]:
        """Contrôle la conformité et la fraîcheur des règles projetées."""
        ...
```

---

### Contraintes Techniques & Performance
- **Plafond Modulaire (ADR-0202)** : Le module `src/bridges/cline/rules_mirror.py` ne doit pas excéder 200 lignes.
- **Vitesse d'Exécution** : Le contrôle pré-vol dans `vibe-check` doit s'exécuter en moins de 10 millisecondes.
- **Idempotence** : Zéro écriture sur disque si le contenu est déjà synchronisé.

---

## Scénarios de test (4 Piliers Gherkin)

### Pilier 1 : Nominal (Happy Path — Génération Modulaire)
```gherkin
SCÉNARIO: Génération nominale de .clinerules/mloop.md
ÉTANT DONNÉ un espace de travail mLoop sans dossier .clinerules
QUAND l'opération sync() de ClineRulesMirror est exécutée
ALORS le répertoire '.clinerules/' est créé
ET le fichier '.clinerules/mloop.md' est généré avec les 5 sections d'invariants
ET les éventuels fichiers de règles additionnels ne sont pas altérés.
```

### Pilier 2 : Exceptions & Rejets Métier (Fichier Manquant au Pré-Vol)
```gherkin
SCÉNARIO: Détection d'un fichier de règles absent lors du Vibe-Check
ÉTANT DONNÉ que le fichier '.clinerules/mloop.md' a été accidentellement supprimé
QUAND le contrôle pré-vol 'vibe-check' est exécuté
ALORS le contrôle 'Règles .clinerules (Parité Miroir)' signale un statut WARNING
ET le message explicite invite à exécuter 'python src/swarm.py sync --project mLoop'.
```

### Pilier 3 : Résilience & Idempotence (Préservation Mtime & Anti-Rebond)
```gherkin
SCÉNARIO: Préservation déterministe lors d'exécutions successives
ÉTANT DONNÉ un fichier '.clinerules/mloop.md' déjà généré et synchronisé
QUAND l'opération sync() est invoquée une seconde fois immédiatement
ALORS l'horodatage mtime du fichier reste strictement identique
ET aucune écriture disque superflue n'est effectuée.

SCÉNARIO: Auto-guérison en cas de corruption de contenu
ÉTANT DONNÉ un fichier '.clinerules/mloop.md' dont le contenu a été altéré
QUAND 'mloop sync' est exécuté
ALORS le miroir détecte la dérive et restaure immédiatement la version canonique.
```

### Pilier 4 : UX / Observabilité & Vibe-Check
```gherkin
SCÉNARIO: Restitution déterministe du statut dans le rapport Vibe-Check
ÉTANT DONNÉ un fichier '.clinerules/mloop.md' conforme et à jour
QUAND 'python src/swarm.py vibe-check --project mLoop' est exécuté
ALORS la ligne 'Règles .clinerules (Parité Miroir) : PASS' apparaît dans la console
ET le compteur total de contrôles reflète l'intégration du nouveau garde-fou.
```

---

## Validation DoR 6/6 (Checklist INVEST)

- [x] **Independent** : Découplé des autres composants, opère uniquement sur les fichiers de directives.
- [x] **Negotiable** : Arbitrages validés en session Grill-Me 1:1 (format modulaire, contrôle actif Vibe-Check).
- [x] **Valuable** : Empêche toute dérive comportementale de Cline lors des sessions de dev.
- [x] **Estimable** : Taille S (1 jour), périmètre circonscrit sous `src/bridges/cline/rules_mirror.py`.
- [x] **Small** : Composant de moins de 150 lignes avec tests unitaires directs.
- [x] **Testable** : 4 Piliers Gherkin automatisés et vérifiables sous `tests/test_cline_bridge.py`.
