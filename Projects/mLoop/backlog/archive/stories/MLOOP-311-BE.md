---
id: MLOOP-311-BE
jira_key: MLOOP-311-BE
epic_key: EPIC-31-FSM-ANTI-HARDCODING-AND-LIFECYCLE-HARMONIZATION
type: Technical_Debt
title: "Assainissement Anti-Hardcoding de state_machine.py (Verticaux, TTL & Arborescence)"
tags: [core, fsm, anti-hardcoding, refactoring, backend]
status: DONE_TESTED
layer: backend
invest_score: 6/6
grill_me: DONE
origin: DIRECT_REQUIREMENT
source_ref: "ADR-0391-§2"
macro_size: M
blocked_by: [MLOOP-310-BE]
created_at: "2026-09-25T04:35:00Z"
updated_at: "2026-09-25T05:07:00Z"
---

# Assainissement Anti-Hardcoding de state_machine.py (Verticaux, TTL & Arborescence)

---

## Description
**En tant qu'** architecte du framework mLoop,  
**je veux** purger tous les résidus hardcodés dans `src/pipelines/state_machine.py` (verticaux clients `FOOD/COMMERCE/SANTE`, constantes TTL dupliquées et divergentes, chemins en dur, chaînes magiques),  
**afin de** garantir que le moteur de Machine à États soit rigoureusement générique, souverain et conforme aux standards de gouvernance SSOT (`ProjectLayout`).

---

## Contexte & Périmètre

### Contexte Métier
Le moteur de machine à états `src/pipelines/state_machine.py` est le garant de l'intégrité du cycle de vie des récits dans mLoop. L'audit contradictoire du 25/09/2026 a mis en évidence des fuites métiers critiques :
1. Une liste codée en dur de verticaux d'un ancien client (`["FOOD", "COMMERCE", "SANTE"]`) à la ligne 263 pour localiser les revues Sentinel.
2. Une double déclaration contradictoire de `DEFAULT_TTL_CYCLES` (3 en ligne 22 vs 5 en ligne 174).
3. L'usage de chaînes de caractères littérales pour vérifier les statuts dans les gardes C9, Sentinel et Anti-Tampering, au lieu des énumérateurs de `StoryStatus`.
Lors du Macro-Grill du 25/09/2026, le PO a validé la résolution dynamique relative à `self.stories_path` et la centralisation SSOT du TTL adossée aux variables d'environnement.

### In-Scope
- Éradication intégrale des chaînes `"FOOD"`, `"COMMERCE"`, `"SANTE"` dans `validate_sentinel_approval` au profit d'une résolution relative dynamique : sous-dossier miroir sous `reviews/`, repli à la racine de `reviews/`, puis recherche récursive `rglob`.
- Élimination de la duplication de `DEFAULT_TTL_CYCLES` : suppression de la ligne 22 et centralisation unique en ligne 174 via `int(os.getenv("MLOOP_DEFAULT_TTL_CYCLES", "5"))`.
- Remplacement des chemins codés en dur par les constantes canoniques de `ProjectLayout`.
- Remplacement des tuples de chaînes littérales de statuts dans `validate_fact_dossier_gate`, `validate_content_integrity` et `validate_single_in_analyze` par des comparaisons typées s'appuyant sur `StoryStatus`.

### Out-of-Scope
- Modification de la matrice des transitions autorisées (couverte par `MLOOP-312-BE`).
- Modification des parsers de synchronisation Markdown (couverte par `MLOOP-313-BE`).

---

## Critères d'acceptation

> **Critères mesurables (INVEST 6/6)** :
> - [x] **CA-1** — Zéro occurrence de `"FOOD"`, `"COMMERCE"` ou `"SANTE"` dans `src/pipelines/state_machine.py`.
> - [x] **CA-2** — La méthode `validate_sentinel_approval` localise avec succès les revues Rubber Duck qu'elles soient à la racine ou dans un sous-dossier modulaire (ex: `backlog/stories/CORE/`).
> - [x] **CA-3** — Une seule définition de `DEFAULT_TTL_CYCLES` subsiste dans le fichier, configurable via la variable d'environnement `MLOOP_DEFAULT_TTL_CYCLES` (valeur par défaut : 5).
> - [x] **CA-4** — Les gardes `validate_fact_dossier_gate` et `validate_content_integrity` vérifient les statuts via les énumérateurs `StoryStatus`.
> - [x] **CA-5** — `validate_single_in_analyze` utilise `StoryStatus.IN_ANALYZE.value` au lieu d'une chaîne magique en dur.
> - [x] **CA-6** — Aucun test existant sous `tests/test_state_machine_c9_gate.py` et `tests/test_story_guard.py` n'est régressé.

### Opérations Métier & Logique Backend

#### 1. Résolution Dynamique de Revue — `_resolve_review_file(story_file: Path) -> Optional[Path]`
* **Entrée Métier** : Chemin `Path` du fichier de récit cible.
* **Règles d'admissibilité & Validation** : Le fichier de récit doit exister sous `self.stories_path`.
* **Traitement & Algorithme Métier** :
  1. Extraire le nom de tige du récit (`story_stem`).
  2. Calculer le chemin relatif du parent par rapport à `self.stories_path`.
  3. Vérifier l'existence du fichier miroir `self.reviews_path / rel_parent / f"rubber_duck_{story_stem}.md"`.
  4. Si absent, vérifier l'existence à la racine `self.reviews_path / f"rubber_duck_{story_stem}.md"`.
  5. Si absent, exécuter une recherche récursive de secours via `self.reviews_path.rglob()`.
* **Résultat Métier & Mutations** : Chemin `Path` du rapport de revue trouvé, ou `None`.
* **Cas de Rejet Métier** : Si aucun rapport n'est trouvé, `validate_sentinel_approval` lève `StateTransitionError`.

---

## Parcours Interactif & API

### Contrats d'Échange API (Backend / Services)

#### Matrice des Contrats API
- **OQ-311 (Exemption Zéro Fausse Route)** : Exemption complète de la Matrice des Contrats API réseau — refactorisation interne du moteur Python de machine à états (`src/pipelines/state_machine.py`), sans interface HTTP ni route REST distante `[API de soumission à définir]` ; exposition interne via la classe `StateMachineEngine` (ADR-0319).

---

## Règles d'affaires

- **Souveraineté Générique du Framework** : Le cœur mLoop ne doit héberger aucune chaîne magique, marqueur ou nom de client spécifique. Toute catégorisation doit être déduite de la topologie réelle des dossiers.
- **SSOT des Paramètres de Dépréciation** : Le cycle de vie des récits obéit à un TTL unique dont la valeur par défaut est 5 cycles, surchargeable par variable d'environnement pour les tests de charge.

---

## Références

### 1. Preuves Amont & Traçabilité Factuelle
- 📂 **Dossier de Preuves Factuelles** : [`memory/evidence/MLOOP-311-BE_fact_dossier.md`](../../memory/evidence/MLOOP-311-BE_fact_dossier.md)
- ⚖️ **Épopée Cadre** : [`backlog/epics/epic_fsm_anti_hardcoding_and_lifecycle_refactor.md`](../epics/epic_fsm_anti_hardcoding_and_lifecycle_refactor.md)

### 2. Spécifications & Modèles de Données SSOT
- 🏛️ **Moteur de Machine à États** : [`src/pipelines/state_machine.py`](../../../src/pipelines/state_machine.py)
- 📜 **Topologie Projet** : [`src/core/layout.py`](../../../src/core/layout.py)
- 📜 **Décision d'Architecture** : [ADR-0391 — Harmonisation Cycle de Vie 5 Phases](../../standards/adr-system/0391-harmonisation-cycle-de-vie-recits-5-phases-fsm.md)

---

## Scénarios de test

```gherkin
# language: fr
Fonctionnalité: Assainissement Anti-Hardcoding de state_machine.py

  # CHEMIN NOMINAL (Happy Path & Résolution Miroir)
  Scénario: Résolution nominale d'un rapport de revue dans un sous-dossier modulaire
    Étant donné un récit situé dans un sous-dossier "backlog/stories/CORE/story.md"
    Et un rapport de revue présent sous "backlog/reviews/CORE/rubber_duck_story.md"
    Quand validate_sentinel_approval est invoqué
    Alors le fichier de revue est correctement résolu sans erreur
    Et aucune mention de client en dur n'intervient dans la résolution

  # EXCEPTIONS & REJETS (Absence de rapport)
  Scénario: Rejet avec message d'erreur clair si aucun rapport de revue n'existe
    Étant donné un récit valide ne disposant d'aucun rapport Rubber Duck
    Quand validate_sentinel_approval est exécuté
    Alors une exception StateTransitionError est levée
    Et le message d'erreur indique précisément la commande à exécuter

  # RÉSILIENCE TECHNIQUE (Fallback récursif et délai d'attente)
  Scénario: Résolution par recherche récursive de secours sous contrainte de performance
    Étant donné un rapport de revue déplacé dans une sous-arborescence profonde
    Quand validate_sentinel_approval cherche le fichier
    Alors la recherche récursive rglob localise le rapport sans délai d'attente excessif ni timeout
    Et la transition est validée

  # UX & OBSERVABILITÉ (TTL unifié et variables d'environnement)
  Scénario: Configuration du TTL via variable d'environnement sans valeur null
    Étant donné la variable d'environnement MLOOP_DEFAULT_TTL_CYCLES définie à "7"
    Quand le module state_machine est chargé
    Alors DEFAULT_TTL_CYCLES prend la valeur entière 7 sans valeur null ni champ vide
    Et le système trace l'initialisation conforme dans les journaux sans token expiré
```
