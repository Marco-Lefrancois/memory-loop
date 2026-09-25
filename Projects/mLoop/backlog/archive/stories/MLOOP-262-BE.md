---
id: MLOOP-262-BE
jira_key: ""
epic_key: EPIC-26-CLINE-ECOSYSTEM-HARNESS
type: Feature
title: Intégration du Mode Plan/Act de Cline (--plan) avec les Gates de Cycle de Vie mLoop
tags: [workflow, cline, lifecycle, backend]
status: DONE_TESTED
layer: backend
invest_score: 6/6
grill_me: DONE
created_at: "2026-09-24T14:15:00"
updated_at: "2026-09-24T14:42:00"
validated_by: Marco
validated_at: "2026-09-25T12:08:50.485909+00:00"

---

# 📖 MLOOP-262-BE : Intégration du Mode Plan/Act de Cline (--plan) avec les Gates de Cycle de Vie mLoop

---

## Description
**En tant qu'** Orchestrateur de Récits et Gardien de la Qualité mLoop,  
**je veux** que Cline soit automatiquement confiné en Mode Plan (`cline --plan`) tant que le récit est en statut de cadrage (`DRAFT`, `IN_ANALYZE`), et autorisé en Mode Act (`cline`) uniquement lorsque le récit est certifié `READY_FOR_DEV`,  
**afin d'** interdire mécaniquement tout saut de phase intempestif et empêcher toute modification de code avant la validation du rituel Grill-Me (Phase 2 ADR-0375).

---

## Contexte & Périmètre

### Contexte Métier
Le principe suprême de gouvernance mLoop ([ADR-0339](file:///C:/Memory%20Loop/standards/adr-system/0339-project-lifecycle-stages-governance-gates.md) et [ADR-0375](file:///C:/Memory%20Loop/standards/adr-system/0375-project-lifecycle-5-phases-and-analysis-types.md)) interdit formellement de coder avant que l'analyse contradictoire Grill-Me 1:1 n'ait purgé les zones d'ombre. Or, les agents d'IDE comme Cline peuvent avoir tendance à écrire immédiatement des fichiers s'ils ne sont pas physiquement bridés.  
Ce récit couple les gates de la machine à états mLoop avec le commutateur natif `--plan` de Cline pour rendre l'écriture de code matériellement impossible en Phase 2.

### In-Scope
- **Verrouillage Déterministe Plan/Act (Arbitrage Grill-Me Q1 - Option A)** :
  - Détection dynamique du statut du récit dans son frontmatter ou son EvidencePack.
  - Injection obligatoire du drapeau `--plan` si le statut est `DRAFT`, `PLANNED`, `OPEN` ou `IN_ANALYZE`.
  - Déverrouillage du mode normal (`Act`) exclusivement conditionné à la présence simultanée de `status: READY_FOR_DEV` et `grill_me: DONE` (DoR 6/6).
- **Fail-Closed Pédagogique (Arbitrage Grill-Me Q2 - Option A)** :
  - En cas de tentative d'écriture ou d'exécution destructive en Phase 2, émission d'un refus explicite orientant l'agent vers la résolution des questions ouvertes et la finalisation du Grill-Me.
- **Protection Multi-Interfaces** : Prise en charge du confinement aussi bien lors des lancements programmatiques via Herdr que dans les consignes injectées sous `.clinerules/mloop.md`.

### Out-of-Scope
- Remplacement du moteur d'exécution de Cline.
- Modification des permissions de l'environnement VS Code hôte.

---

## Critères d'acceptation

### Opérations Métier & Logique Backend

#### 1. Opération `evaluate_lifecycle_mode(story_id: str, project_name: str) -> str`
* **Entrée Métier** : Identifiant de la story (`story_id`) et nom du projet (`project_name`).
* **Règles d'admissibilité & Validation** : La story doit exister sous `Projects/<project_name>/backlog/stories/` ou dans le `sprint_backlog.md`.
* **Traitement & Algorithme Métier** :
  1. Lecture du frontmatter YAML de la story.
  2. Extraction de `status` et `grill_me`.
  3. Si `status == "READY_FOR_DEV"` et `grill_me == "DONE"`, retourner `"act"`.
  4. Dans tous les autres cas (statuts `DRAFT`, `IN_ANALYZE`, etc.), retourner impérativement `"plan"`.
* **Résultat Métier & Mutations** : Chaîne normalisée `"plan"` ou `"act"`.
* **Cas de Rejet Métier** : Story introuvable (retourne `"plan"` par sécurité fail-closed).

#### 2. Opération `enforce_cline_flags(flags: List[str], target_mode: str) -> List[str]`
* **Entrée Métier** : Liste actuelle des arguments CLI et mode cible évalué (`"plan"` ou `"act"`).
* **Règles d'admissibilité & Validation** : Aucun drapeau contradictoire ne doit subsister dans la ligne de commande.
* **Traitement & Algorithme Métier** :
  1. Si `target_mode == "plan"`, vérifier la présence de `"--plan"` ou `"-p"` ; l'ajouter si absent.
  2. Si `target_mode == "act"`, purger d'éventuels résidus `"--plan"` ou `"-p"`.
* **Résultat Métier & Mutations** : Liste d'arguments CLI prête pour `start_agent`.
* **Cas de Rejet Métier** : Format d'arguments non valide.

---

### Contrats d'échange API (Interface Python)

#### Matrice des Contrats API
- **OQ-262 (Exemption Zéro Fausse Route)** : Exemption complète de la Matrice des Contrats API réseau — opération purement interne d'évaluation de machine à états et de construction d'arguments de ligne de commande, sans interface HTTP réseau ni route REST distante `[API de soumission à définir]` ; toute future exposition d'API distante pour le cycle de vie est à confirmer dans un récit dédié avec sa propre matrice (ADR-0319).

```python
from typing import List, Dict, Any

class PlanActGuard:
    """Garde-fou déterministe d'application du mode Plan/Act pour Cline."""

    @staticmethod
    def evaluate_mode(story_path: str) -> str:
        """Retourne 'plan' ou 'act' selon le statut de maturité du récit."""
        ...

    @staticmethod
    def enforce_flags(flags: List[str], mode: str) -> List[str]:
        """Injecte ou retire --plan selon le mode requis."""
        ...
```

---

### Contraintes Techniques & Performance
- **Plafond Modulaire (ADR-0202)** : L'extension sous `src/core/herdr_worker_core.py` ou le garde-fou associé doit respecter le plafond modulaire.
- **Temps de Réponse** : Évaluation du mode en moins de 5 millisecondes sans appel réseau.
- **Principe Fail-Closed** : En cas de doute ou d'anomalie de lecture de la story, le mode `"plan"` est systématiquement appliqué par défaut.

---

## Scénarios de test (4 Piliers Gherkin)

### Pilier 1 : Nominal (Happy Path — Confinement Plan en Phase 2)
```gherkin
SCÉNARIO: Injection obligatoire de --plan pour un récit en ébauche
ÉTANT DONNÉ une story 'MLOOP-263-BE' au statut 'DRAFT' avec grill_me 'PENDING'
QUAND Herdr prépare le lancement d'un worker Cline via spawn_story_worker_impl()
ALORS l'opération évalue le mode de cycle de vie à 'plan'
ET le drapeau '--plan' est obligatoirement injecté dans les arguments d'exécution
ET le worker démarre en lecture seule sans capacité d'écriture.
```

### Pilier 2 : Exceptions & Rejets Métier (Tentative de Saut de Phase Rejetée)
```gherkin
SCÉNARIO: Refus d'exécution du mode Act pour une story non certifiée
ÉTANT DONNÉ une story au statut 'IN_ANALYZE' sans validation DoR 6/6
QUAND un utilisateur tente de forcer le lancement en mode normal
ALORS le garde-fou intercepte la requête et impose le mode 'plan'
ET un message de journalisation explicite signale l'obligation de compléter le rituel Grill-Me.
```

### Pilier 3 : Résilience & Idempotence (Préservation Mtime & Anti-Rebond)
```gherkin
SCÉNARIO: Déverrouillage nominal du mode Act lors de la certification DoR
ÉTANT DONNÉ une story certifiée au statut 'READY_FOR_DEV' avec grill_me 'DONE'
QUAND Herdr lance le worker d'implémentation physique
ALORS le mode évalué est 'act'
ET le drapeau '--plan' est omis des arguments de démarrage
ET le worker dispose des capacités complètes de modification et de test.

SCÉNARIO: Résilience face à un fichier de story corrompu ou manquant
ÉTANT DONNÉ un identifiant de story introuvable sur le disque
QUAND l'évaluation du cycle de vie est exécutée
ALORS le garde-fou bascule par défaut sur le mode sécurisé 'plan'
ET aucune exception non capturée n'interrompt le processus de dispatch.
```

### Pilier 4 : UX / Observabilité & Restitution Déterministe
```gherkin
SCÉNARIO: Traçabilité du mode dans les journaux d'exécution
ÉTANT DONNÉ l'instanciation d'un worker Cline sous surveillance Herdr
QUAND le processus est initialisé
ALORS le journal structuré consigne explicitement le mode assigné ('plan' ou 'act')
ET l'EvidencePack de la story enregistre le jalon de cycle de vie franchi.
```

---

## Validation DoR 6/6 (Checklist INVEST)

- [x] **Independent** : Le guard Plan/Act est autonome et s'appuie sur la machine à états standard mLoop.
- [x] **Negotiable** : Arbitrages validés en session Grill-Me 1:1 (validation stricte DoR 6/6, fail-closed pédagogique).
- [x] **Valuable** : Élimine définitivement le risque de saut de phase et protège l'intégrité du code source.
- [x] **Estimable** : Taille M (2 jours), intégration ciblée dans `herdr_worker_core.py`.
- [x] **Small** : Logique concise sans dépendance externe lourde.
- [x] **Testable** : 4 Piliers Gherkin automatisés et testés dans `tests/test_herdr_circuit_breaker.py`.
