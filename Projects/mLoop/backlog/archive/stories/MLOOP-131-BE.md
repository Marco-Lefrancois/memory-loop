---
id: MLOOP-131-BE
jira_key: ''
epic_key: EPIC-13-CODE-GRAPH-INTELLIGENCE
type: Feature
title: Pipeline Séquentiel Hybride CodeGraph → Graft → Intersection
tags:
- core
- code-intelligence
- hybrid
origin: SPEC_SLICING
source_ref: MLOOP-130-BE_spike_report
macro_size: M
status: SHIPPED
grill_me: DONE
invest_score: 6/6
layer: backend
blocked_by:
- MLOOP-130-BE
created_at: '2026-09-21'
ttl_cycles: 4
---

# Pipeline Séquentiel Hybride CodeGraph → Graft → Intersection

---

## Description
**En tant qu'**Architecte du framework mLoop,
**je veux** un pipeline séquentiel combinant CodeGraph explore (recall élevé) et Graft callers (précision élevée) via une intersection des résultats,
**afin de** bénéficier du meilleur des deux moteurs tout en minimisant les faux positifs.

---

## Contexte & Périmètre

### Contexte Métier
Le spike MLOOP-130-BE a démontré que CodeGraph explore a un recall de 0.733 mais une précision de 0.279, tandis que Graft callers a une précision de 0.583 mais un recall de 0.467. L'intersection des résultats devrait produire un F1 optimal.

### In-Scope
- Pipeline séquentiel : CodeGraph → Graft → intersection
- Fusion des résultats avec scoring pondéré
- Mode dégradé si l'un des moteurs est indisponible

### Out-of-Scope
- Refonte de CodeGraph ou Graft
- Interface utilisateur

---

## Critères d'acceptation

### Opérations Métier & Logique Backend

#### 1. Pipeline Séquentiel
- CodeGraph explore est exécuté en premier
- Graft callers est exécuté sur les résultats CodeGraph
- L'intersection est calculée comme la liste des fichiers présents dans les deux moteurs

#### 2. Scoring Pondéré
- Chaque fichier reçoit un score basé sur la présence dans chaque moteur
- Poids configurable (défaut : 0.6 CodeGraph, 0.4 Graft)

#### 3. Mode Dégradé
- Si CodeGraph est indisponible : fallback sur Graft seul
- Si Graft est indisponible : fallback sur CodeGraph seul
- Le mode dégradé est signalé dans les logs

---

## Règles Métier
- **RM-131-01** : L'intersection doit être calculée sur le chemin relatif du fichier
- **RM-131-02** : Les poids sont configurables via variables d'environnement
- **RM-131-03** : Le mode dégradé est toujours un fallback, jamais un blocage

---

## Contrats UI & API Backend → Profil B

### Matrice des Contrats API

> **Contexte** : Ce récit implémente un pipeline hybride combinant CodeGraph et Graft. Aucune API HTTP n'est exposée. Conformément à ADR-0319, l'absence de routes HTTP est consignée via la question ouverte **OQ-131-01**.

| Méthode | Route | Finalité |
|:---|:---|:---|
| `hybrid_context_search()` | `src.pipelines.hybrid_context_engine:hybrid_context_search` | Pipeline CodeGraph → Graft → intersection + scoring |
| `CodeGraphEngine.explore()` | `src.bridges.codegraph:CodeGraphEngine.explore` | Recherche langage naturel (recall élevé) |
| `GraftEngine.callers()` | `src.bridges.graft:GraftEngine.callers` | Recherche appelants (précision élevée) |

**Question Ouverte (Exemption ADR-0319)** :
- **OQ-131-01** : Ce récit implémente un pipeline hybride interne combinant deux moteurs de contexte de code. Aucune API HTTP n'est exposée. Les interfaces sont des appels de fonction Python internes. **[API de soumission à définir]**

---

## Scénarios de test

### Pilier 1 — Chemin Nominal
```gherkin
Scénario : Pipeline hybride avec les deux moteurs
  Étant donné un corpus de code analyser
  Quand le pipeline hybride est exécuté
  Alors CodeGraph explore retourne ses résultats
  Et Graft callers est exécuté sur les résultats
  Et l'intersection est calculée
  Et chaque fichier a un score pondéré
```

### Pilier 2 — Exceptions & Rejets
```gherkin
Scénario : Graft indisponible
  Étant donné un corpus de code analyser
  Mais Graft est indisponible
  Quand le pipeline hybride est exécuté
  Alors le fallback utilise CodeGraph seul
  Et un avertissement est émis
```

### Pilier 3 — Résilience & Mode Dégradé
```gherkin
Scénario : CodeGraph indisponible
  Étant donné un corpus de code analyser
  Mais CodeGraph est indisponible
  Quand le pipeline hybride est exécuté
  Alors le fallback utilise Graft seul
  Et un avertissement est émis
```

### Pilier 4 — UX & Observabilité
```gherkin
Scénario : Observabilité du pipeline
  Étant donné un pipeline hybride exécuté
  Quand l'opérateur consulte les logs
  Alors il voit le mode utilisé (hybride, fallback CodeGraph, fallback Graft)
  Et les poids utilisés
  Et le nombre de résultats par moteur
```
