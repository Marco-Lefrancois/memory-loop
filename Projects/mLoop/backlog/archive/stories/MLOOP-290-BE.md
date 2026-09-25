---
id: MLOOP-290-BE
jira_key: ''
epic_key: EPIC-29-GRILL-V2-FRONTIER-SKILLS
type: Feature
title: Câblage CLI Swarm (Options --mode round/atomic & Alertes Health)
tags:
- grill
- cli
- context-health
- dumb-zone
- frontier-rounds
status: SHIPPED
validated_by: "Marco (PO - Feu Vert 2026-09-24)"
validated_at: "2026-09-24"
grill_me: DONE
layer: backend
invest_score: 6/6
macro_size: M
created_at: '2026-09-24'
ttl_cycles: 4
---

# 📖 MLOOP-290-BE : Câblage CLI Swarm (Options --mode round/atomic & Alertes Health)

---

## Description
**En tant qu'** Utilisateur ou Agent exécutant un cadrage via `python src/swarm.py grill-project` ou `grill-me`,  
**je veux** disposer des options de ligne de commande `--mode round|atomic` avec valeurs par défaut adaptées et d'une surveillance active de santé du contexte (`check_context_health`),  
**afin de** piloter la vitesse d'interrogation (rounds groupés en macro vs 1:1 en micro) et d'être alerté dès que la session approche du seuil de fatigue cognitive ("Dumb Zone" > 120k tokens) sans purge intempestive de contexte.

---

## Contexte & Périmètre

### Contexte Métier
L'arbitrage de l'ADR-013 (issu de l'ADR-0389 et de la validation macro du 24/09/2026) a scellé l'asymétrie des modes d'interrogation :
- `grill-project` adopte `--mode round` par défaut (lots de 2 à 4 questions orthogonales indépendantes).
- `grill-me --story <ID>` conserve `--mode atomic` par défaut (1:1 strict pour les dépendances fines).
- La surveillance de la fenêtre de contexte doit émettre un avertissement clair (`WARNING`) entre 80k et 120k tokens (exigeant la pose d'un checkpoint) et bloquer l'expansion de nouvelles branches au-delà de 120k tokens (`DUMB_ZONE`).

### In-Scope
- Ajout du paramètre `--mode` dans les parsers CLI d'architecture (`src/commands/handlers/architecture.py` et `src/swarm.py`) acceptant `round` et `atomic`.
- Câblage de `format_frontier_round` dans le flux d'exécution macro quand `--mode round` est actif.
- Gestion des validations granulaires : capacité de parser des réponses composites (ex: "Q1: A, Q2: amendé avec...") et de mettre à jour la frontière active.
- Intégration de l'utilitaire `check_context_health` :
  - `OK` : < 80k tokens.
  - `WARNING_ZONE` : 80k - 120k tokens (invitation explicite à checkpoint).
  - `DUMB_ZONE` : > 120k tokens (blocage d'expansion, recommandation de transition immédiate vers la rédaction sans vider le contexte).
- Ajout du sous-drapeau d'inspection ciblée `python src/swarm.py grill --health` pour inspection instantanée du budget.

### Out-of-Scope
- Réécriture de la FSM centrale de Swarm.
- Purge ou remise à zéro du contexte de session (formellement proscrite par ADR-0389).

---

## Critères d'acceptation (Gherkin 4 Piliers)

### 1. Pilier Nominal (Happy Path - Mode Round & Mode Atomic)
```gherkin
Scénario: Exécution par défaut de grill-project en mode round
  Étant donné un projet mLoop contenant plusieurs questions orthogonales ouvertes
  Quand l'utilisateur lance "python src/swarm.py grill-project --project MonProjet"
  Alors le moteur utilise le mode "round" par défaut
  Et affiche un lot groupé de 2 à 4 questions orthogonales numérotées
  Et l'utilisateur peut valider l'ensemble du round en une seule réponse "VALIDÉ"
```

```gherkin
Scénario: Exécution par défaut de grill-me en mode atomic
  Étant donné une story spécifique identifiée par son ID
  Quand l'utilisateur lance "python src/swarm.py grill-me --project MonProjet --story STORY-01"
  Alors le moteur utilise le mode "atomic" par défaut
  Et présente une unique question avec options d'arbitrage 1:1
```

### 2. Pilier Exception & Résolution Granulaire
```gherkin
Scénario: Validation granulaire d'un round avec amendement partiel
  Étant donné un round actif présentant les questions Q1, Q2 et Q3
  Quand l'utilisateur répond "Q1 validée, Q2 amendée avec option B, Q3 à revoir"
  Alors le moteur acte la décision pour Q1 et Q2
  Et réinjecte la question Q3 amendée dans la frontière active du tour suivant
  Et aucune décision contradictoire n'est enregistrée
```

### 3. Pilier Résilience & Détection de la Dumb Zone
```gherkin
Scénario: Détection du seuil critique Dumb Zone (> 120k tokens)
  Étant donné une session de cadrage dont l'estimation dépasse 120k tokens
  Quand le moteur évalue l'état de santé via check_context_health
  Alors le statut retourné est "DUMB_ZONE"
  Et un message d'alerte explicite ZeroFluffConsole.warning est affiché
  Et le moteur bloque l'ajout de nouvelles branches exploratoires
  Et suggère la concrétisation immédiate des décisions acquises
```

### 4. Pilier Performance & Inspection Sub-seconde
```gherkin
Scénario: Inspection instantanée de la santé du contexte via CLI
  Étant donné une session de projet active
  Quand l'utilisateur exécute "python src/swarm.py grill --health --project MonProjet"
  Alors l'estimation du nombre de tokens et le statut de santé sont affichés en moins de 500 ms
  Et aucun appel réseau externe bloquant n'est émis
```

---

### Contrats d'Échange API (Interface Python & In-Process)

#### Matrice des Contrats API
- **OQ-290 (Exemption Zéro Fausse Route)** : Exemption complète de la Matrice des Contrats API réseau — commande CLI locale et in-process Python (`src/commands/handlers/architecture.py`, `src/swarm.py`), sans point de terminaison HTTP ni route REST distante `[API de soumission à définir]` (ADR-0319).

**Contrats Python Internes :**
- `handle_grill_project(project_name: str, mode: str = "round", auto_commit: bool = False) -> int`
- `handle_grill_story(project_name: str, story_id: str, mode: str = "atomic") -> int`
- `check_context_health(token_count: Optional[int] = None, transcript_path: Optional[Path] = None) -> Dict[str, Any]`

---

## Logique Métier & Algorithme Backend

### `check_context_health`
1. Si `token_count` est fourni, l'utiliser directement.
2. Sinon, si `transcript_path` existe, lire la taille en octets ou le nombre de caractères et estimer : $\text{tokens} = \text{len}(\text{chars}) // 4$.
3. Seuil d'évaluation :
   - $\text{tokens} < 80\,000$ : `status = "OK"`, niveau `INFO`.
   - $80\,000 \le \text{tokens} \le 120\,000$ : `status = "WARNING_ZONE"`, niveau `WARNING`, message : *"Approche du seuil de fatigue cognitive. Envisager un checkpoint."*
   - $\text{tokens} > 120\,000$ : `status = "DUMB_ZONE"`, niveau `CRITICAL`, message : *"Dumb Zone atteinte (>120k tokens). Interdiction de purge de contexte : basculer immédiatement en rédaction."*
4. Retourner `{"status": status, "tokens": tokens, "threshold": 120000, "alert": bool}`.

### `handle_grill_project` avec `--mode`
1. Parser l'argument `--mode` (valeur par défaut : `"round"`).
2. Si mode `"round"`, charger l'instance `GrillFrontier` et appeler `format_frontier_round(max_questions=4)`.
3. Évaluer la santé du contexte via `check_context_health()`.
4. Si alerte présente, afficher le bandeau de mise en garde en tête de console.

---

## Références
- 🏛️ **ADR Associés** : [ADR-013](../../../docs/01-architecture/ADR-013_epic-29_grill_v2_frontier_rounds_ungrillable_context.md) · [ADR-0389](../../../../standards/adr-system/0389-grill-v2-frontier-rounds-ungrillable-handoff-context-budget.md) · [ADR-0320](../../../../standards/adr-system/0320-grill-me-frontier-design-tree-alignment.md)
- 📂 **Spécification Source** : `docs/00-ingested/grill-me/12_things_people_get_wrong_with_grill_me_and_grill_with_docs.md`
- 📦 **Épopée Parente** : [`EPIC-29-GRILL-V2-FRONTIER-SKILLS`](../epics/epic_grill_v2_frontier_rounds_ungrillable_context.md)