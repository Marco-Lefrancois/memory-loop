---
id: MLOOP-135-BE
jira_key: ''
epic_key: EPIC-13-CODE-GRAPH-INTELLIGENCE
type: Feature
title: Extension du Benchmark à 3+ Dépôts de Tailles Variées
tags:
- core
- code-intelligence
- benchmark
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

# Extension du Benchmark à 3+ Dépôts de Tailles Variées

---

## Description
**En tant qu'**Architecte du framework mLoop,
**je veux** étendre le benchmark à 3+ dépôts de tailles variées (small, medium, large),
**afin de** valider la scalabilité des résultats du spike MLOOP-130-BE.

---

## Contexte & Périmètre

### Contexte Métier
Le spike MLOOP-130-BE a utilisé un seul dépôt (pallets/click, 90 fichiers). Il faut valider que les résultats se maintiennent sur des dépôts de tailles variées.

### In-Scope
- Sélection de 3 dépôts de tailles variées
- Exécution du benchmark sur chaque dépôt
- Comparaison des résultats inter-dépôts

### Out-of-Scope
- Création de nouveaux benchmarks
- Modification des moteurs

---

## Critères d'acceptation

### Opérations Métier & Logique Backend

#### 1. Sélection des Dépôts
- 3 dépôts de tailles variées sont sélectionnés
- Les dépôts sont documentés (nom, taille, langue)

#### 2. Exécution
- Le benchmark est exécuté sur chaque dépôt
- Les résultats sont comparés
- La scalabilité est évaluée

---

## Règles Métier
- **RM-135-01** : Les dépôts doivent être publics et accessibles
- **RM-135-02** : Chaque dépôt a au moins 10 corrections de bugs
- **RM-135-03** : Les résultats sont consignés séparément par dépôt

---

## Contrats UI & API Backend → Profil B

### Matrice des Contrats API

> **Contexte** : Ce récit étend le benchmark à 3+ dépôts. Aucune API HTTP n'est exposée. Conformément à ADR-0319, l'absence de routes HTTP est consignée via la question ouverte **OQ-135-01**.

| Méthode | Route | Finalité |
|:---|:---|:---|
| `multi_repo_benchmark.run_multi_repo_benchmark()` | `src.pipelines.multi_repo_benchmark:run_multi_repo_benchmark` | Exécute benchmark sur 3 dépôts (S/M/L) |
| `multi_repo_benchmark.format_scalability_report()` | `src.pipelines.multi_repo_benchmark:format_scalability_report` | Génère rapport de scalabilité inter-dépôts |

**Question Ouverte (Exemption ADR-0319)** :
- **OQ-135-01** : Ce récit étend un benchmark local à 3 dépôts tiers. Aucune API HTTP n'est exposée. Les interfaces sont des appels de fonction Python internes. **[API de soumission à définir]**

---

## Scénarios de test

### Pilier 1 — Chemin Nominal
```gherkin
Scénario : Benchmark multi-dépôts
  Étant donné 3 dépôts de tailles variées
  Quand le benchmark est exécuté sur chaque dépôt
  Alors les résultats sont consignés
  Et la comparaison est produite
```

### Pilier 2 — Exceptions & Rejets
```gherkin
Scénario : Dépôt inaccessible
  Étant donné un dépôt inaccessible
  Quand le benchmark est exécuté
  Alors le dépôt est ignoré
  Et le motif est consigné
```

### Pilier 3 — Résilience & Mode Dégradé
```gherkin
Scénario : Timeout sur un dépôt
  Étant donné un dépôt volumineux
  Quand le benchmark dépasse le timeout
  Alors les résultats partiels sont conservés
```

### Pilier 4 — UX & Observabilité
```gherkin
Scénario : Rapport multi-dépôts
  Étant donné un benchmark multi-dépôts terminé
  Quand l'opérateur consulte le rapport
  Alors il voit les résultats par dépôt
  Et la tendance de scalabilité
```
