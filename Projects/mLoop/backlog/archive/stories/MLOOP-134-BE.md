---
id: MLOOP-134-BE
jira_key: ''
epic_key: EPIC-13-CODE-GRAPH-INTELLIGENCE
type: Feature
title: Mesure de Tokens Réelle via APIs LiteLLM
tags:
- core
- code-intelligence
- tokens
origin: SPEC_SLICING
source_ref: MLOOP-130-BE_spike_report
macro_size: S
status: SHIPPED
grill_me: DONE
invest_score: 6/6
layer: backend
blocked_by:
- MLOOP-130-BE
created_at: '2026-09-21'
ttl_cycles: 4
---

# Mesure de Tokens Réelle via APIs LiteLLM

---

## Description
**En tant qu'**Architecte du framework mLoop,
**je veux** mesurer le nombre réel de tokens consommés par appel à CodeGraph et Graft via les APIs LiteLLM,
**afin de** disposer de métriques de coût fiables pour l'arbitrage architectural.

---

## Contexte & Périmètre

### Contexte Métier
Le spike MLOOP-130-BE a mesuré les jetons de manière indirecte. Il faut une mesure réelle via les APIs LiteLLM pour obtenir des métriques de coût fiables.

### In-Scope
- Instrumentation des appels CodeGraph et Graft
- Collecte des tokens input/output via LiteLLM
- Agrégation par moteur et par question

### Out-of-Scope
- Optimisation des coûts
- Alertes de budget

---

## Critères d'acceptation

### Opérations Métier & Logique Backend

#### 1. Instrumentation
- Chaque appel à CodeGraph est instrumenté
- Chaque appel à Graft est instrumenté
- Les tokens input/output sont collectés

#### 2. Agrégation
- Les tokens sont agrégés par moteur
- Les tokens sont agrégés par question
- Les totaux sont consignés dans le rapport

---

## Règles Métier
- **RM-134-01** : La mesure ne doit pas impacter la latence (> 5ms supplémentaires)
- **RM-134-02** : Les tokens sont consignés en mode structuré (JSON)
- **RM-134-03** : Les données sont anonymisées (pas de contenu de code)

---

## Contrats UI & API Backend → Profil B

### Matrice des Contrats API

> **Contexte** : Ce récit mesure les tokens réels via APIs LiteLLM. Aucune API HTTP n'est exposée par le récit lui-même (consommation API LiteLLM existante). Conformément à ADR-0319, l'absence de routes HTTP exposées est consignée via la question ouverte **OQ-134-01**.

| Méthode | Route | Finalité |
|:---|:---|:---|
| `token_counter.track_llm_call()` | `src.pipelines.token_counter:track_llm_call` | Context manager async instrumentant appels LLM |
| `token_counter.record_from_response()` | `src.pipelines.token_counter:record_from_response` | Extrait tokens depuis `response.usage` |
| `token_counter.get_report()` | `src.pipelines.token_counter:get_report` | Génère rapport agrégé par moteur/question |

**Question Ouverte (Exemption ADR-0319)** :
- **OQ-134-01** : Ce récit instrumente des appels vers l'API LiteLLM (proxy existant). Le récit lui-même n'expose pas d'API HTTP. Les interfaces sont des appels de fonction Python internes. **[API de soumission à définir]**

---

## Scénarios de test

### Pilier 1 — Chemin Nominal
```gherkin
Scénario : Mesure des tokens
  Étant donné un appel à CodeGraph
  Quand l'appel est exécuté
  Alors les tokens input sont mesurés
  Et les tokens output sont mesurés
  Et les résultats sont consignés
```

### Pilier 2 — Exceptions & Rejets
```gherkin
Scénario : API indisponible
  Étant donné une API LiteLLM indisponible
  Quand un appel est exécuté
  Alors les tokens sont estimés
  Et l'estimation est marquée comme approximative
```

### Pilier 3 — Résilience & Mode Dégradé
```gherkin
Scénario : Timeout de mesure
  Étant donné un appel lent
  Quand la mesure dépasse le timeout
  Alors la mesure est interrompue
  Et les résultats partiels sont conservés
```

### Pilier 4 — UX & Observabilité
```gherkin
Scénario : Rapport de tokens
  Étant donné une session de benchmark terminée
  Quand l'opérateur consulte le rapport
  Alors il voit les tokens par moteur
  Et les tokens par question
  Et le coût estimé
```
