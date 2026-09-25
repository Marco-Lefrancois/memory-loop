---
id: MLOOP-133-BE
jira_key: ''
epic_key: EPIC-13-CODE-GRAPH-INTELLIGENCE
type: Feature
title: Fallback Automatique si Graft Callers Échoue
tags:
- core
- code-intelligence
- resilience
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

# Fallback Automatique si Graft Callers Échoue

---

## Description
**En tant qu'**Architecte du framework mLoop,
**je veux** un fallback automatique vers CodeGraph lorsque Graft callers échoue (20% d'échec sur symboles ambigus),
**afin de** garantir la continuité de service sans intervention manuelle.

---

## Contexte & Périmètre

### Contexte Métier
Le spike MLOOP-130-BE a montré que Graft callers a 20% d'échec sur les symboles ambigus. Le fallback automatique doit être déclenché sans intervention humaine.

### In-Scope
- Détection automatique de l'échec Graft callers
- Fallback vers CodeGraph explore
- Journalisation de l'échec et du fallback

### Out-of-Scope
- Correction des symboles ambigus
- Notification externe

---

## Critères d'acceptation

### Opérations Métier & Logique Backend

#### 1. Détection d'Échec
- L'échec de Graft callers est détecté (code de retour ≠ 0 ou exception)
- Le type d'erreur est consigné

#### 2. Fallback Automatique
- CodeGraph explore est exécuté en remplacement
- Les résultats sont fusionnés avec les résultats partiels de Graft
- Le mode fallback est signalé dans les logs

---

## Règles Métier
- **RM-133-01** : Le fallback est déclenché après 1 échec (pas de retry)
- **RM-133-02** : Les résultats partiels de Graft sont conservés
- **RM-133-03** : Le fallback est journalisé en WARNING

---

## Contrats UI & API Backend → Profil B

### Matrice des Contrats API

> **Contexte** : Ce récit implémente un fallback automatique Graft → CodeGraph. Aucune API HTTP n'est exposée. Conformément à ADR-0319, l'absence de routes HTTP est consignée via la question ouverte **OQ-133-01**.

| Méthode | Route | Finalité |
|:---|:---|:---|
| `hybrid_context_search()` | `src.pipelines.hybrid_context_engine:hybrid_context_search` | Pipeline avec fallback Graft → CodeGraph |
| `_execute_codegraph_fallback()` | `src.pipelines.hybrid_context_engine:_execute_codegraph_fallback` | Exécute CodeGraph explore en fallback |
| `_extract_graft_exit_code()` | `src.pipelines.hybrid_context_engine:_extract_graft_exit_code` | Détecte échec Graft (exit_code ≠ 0) |

**Question Ouverte (Exemption ADR-0319)** :
- **OQ-133-01** : Ce récit implémente un fallback interne entre deux moteurs de contexte de code. Aucune API HTTP n'est exposée. Les interfaces sont des appels de fonction Python internes. **[API de soumission à définir]**

---

## Scénarios de test

### Pilier 1 — Chemin Nominal
```gherkin
Scénario : Fallback après échec Graft
  Étant donné un symbole ambigu
  Quand Graft callers échoue
  Alors CodeGraph explore est exécuté
  Et les résultats sont fusionnés
  Et le fallback est journalisé
```

### Pilier 2 — Exceptions & Rejets
```gherkin
Scénario : Les deux moteurs échouent
  Étant donné un corpus inaccessible
  Quand Graft et CodeGraph échouent
  Alors une erreur est levée
  Et aucun résultat n'est retourné
```

### Pilier 3 — Résilience & Mode Dégradé
```gherkin
Scénario : Timeout Graft
  Étant donné un symbole complexe
  Quand Graft callers dépasse le timeout
  Alors le fallback est déclenché
```

### Pilier 4 — UX & Observabilité
```gherkin
Scénario : Logs du fallback
  Étant donné un fallback déclenché
  Quand l'opérateur consulte les logs
  Alors il voit "WARNING: Graft callers failed, fallback to CodeGraph"
```
