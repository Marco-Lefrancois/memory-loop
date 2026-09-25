---
id: MLOOP-132-BE
jira_key: ''
epic_key: EPIC-13-CODE-GRAPH-INTELLIGENCE
type: Feature
title: Test Graft Deep Build pour QA Sémantique
tags:
- core
- code-intelligence
- graft
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

# Test Graft Deep Build pour QA Sémantique

---

## Description
**En tant qu'**Architecte du framework mLoop,
**je veux** tester le mode `graft build --deep` sur le même corpus que le spike MLOOP-130-BE,
**afin d'évaluer** si le mode profond améliore le recall de Graft (actuellement 0.467) pour le QA sémantique.

---

## Contexte & Périmètre

### Contexte Métier
Le spike MLOOP-130-BE a révélé que Graft `ask` est inopérant en mode lexical (0% recall). Le mode `--deep` build pourrait améliorer les performances en construisant un index sémantique profond.

### In-Scope
- Exécution de `graft build --deep` sur le corpus du spike
- Test de Graft `ask` après construction profonde
- Comparaison des résultats avec le spike initial

### Out-of-Scope
- Modification du corpus
- Integration dans le pipeline principal

---

## Critères d'acceptation

### Opérations Métier & Logique Backend

#### 1. Construction Profonde
- `graft build --deep` est exécuté sur le corpus
- La construction réussit sans erreur
- L'index est persisté localement

#### 2. Test QA Sémantique
- Graft `ask` est exécuté sur les mêmes questions que le spike
- Les résultats sont comparés au mode lexical
- Le recall est mesuré contre la vérité terrain

---

## Règles Métier
- **RM-132-01** : Le build deep doit être exécuté avant tout test ask
- **RM-132-02** : Les résultats sont consignés dans le rapport d'arbitrage
- **RM-132-03** : Le timeout du build deep est de 300 secondes

---

## Contrats UI & API Backend → Profil B

### Matrice des Contrats API

> **Contexte** : Ce récit teste le mode `graft build --deep` pour QA sémantique. Aucune API HTTP n'est exposée. Conformément à ADR-0319, l'absence de routes HTTP est consignée via la question ouverte **OQ-132-01**.

| Méthode | Route | Finalité |
|:---|:---|:---|
| `graft_deep_test.run_deep_test_suite()` | `src.pipelines.graft_deep_test:run_deep_test_suite` | Exécute `graft build --deep` + test `graft ask` |
| `graft_deep_test.format_report()` | `src.pipelines.graft_deep_test:format_report` | Génère rapport markdown comparatif lexical vs deep |

**Question Ouverte (Exemption ADR-0319)** :
- **OQ-132-01** : Ce récit teste un mode CLI Graft (`build --deep` + `ask`) en local. Aucune API HTTP n'est exposée. Les interfaces sont des appels de fonction Python internes. **[API de soumission à définir]**

---

## Scénarios de test

### Pilier 1 — Chemin Nominal
```gherkin
Scénario : Build deep et test ask
  Étant donné le corpus du spike MLOOP-130-BE
  Quand graft build --deep est exécuté
  Alors l'index est créé
  Et quand graft ask est exécuté
  Alors les résultats sont non-vides
  Et le recall est mesuré
```

### Pilier 2 — Exceptions & Rejets
```gherkin
Scénario : Build deep échoue
  Étant donné un corpus corrompu
  Quand graft build --deep est exécuté
  Alors l'erreur est consignée
  Et le test ask est ignoré
```

### Pilier 3 — Résilience & Mode Dégradé
```gherkin
Scénario : Timeout du build deep
  Étant donné un corpus volumineux
  Quand graft build --deep dépasse 300s
  Alors le processus est interrompu
  Et le résultat est "timeout"
```

### Pilier 4 — UX & Observabilité
```gherkin
Scénario : Observabilité du build
  Étant donné un build deep en cours
  Quand l'opérateur consulte les logs
  Alors il voit la progression
  Et la durée totale
```
