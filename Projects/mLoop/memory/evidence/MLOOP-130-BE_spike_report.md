# MLOOP-130-BE — Rapport d'Arbitrage : Benchmark Empirique Croisé Graft vs CodeGraph

---

**Spike ID**: MLOOP-130-BE  
**Date d'exécution**: 2026-09-21  
**Auteur**: Agent mLoop (OpenCode)  
**Statut**: Terminé  

---

## 1. Protocole de Benchmark

### 1.1 Corpus
| Paramètre | Valeur |
|:---|:---|
| Dépôt tiers | `pallets/click` (bibliothèque Python CLI) |
| Commit | `6aabf099bfdd4c1e75fe8d0e0d4241372b988ab1` |
| Fichiers Python | 90 |
| Graine aléatoire | 42 |

### 1.2 Moteurs évalués
| Moteur | Version | Commandes utilisées |
|:---|:---|:---|
| **CodeGraph** (mLoop) | 1.5.0 | `explore` (NL query), `callers` (symbol) |
| **Graft** (Nanonets/Trail) | 0.18.0 | `ask --json` (NL query), `callers --json` (symbol) |

### 1.3 Métriques
- **Justesse** : Precision, Recall, F1 contre la vérité terrain (fichiers réellement touchés par le correctif humain)
- **Latence** : Temps d'exécution par appel (secondes)
- **Fiabilité** : Taux de succès des appels (exit code 0)
- **Coût** : Nombre approximatif de jetons par sortie (estimation ~4 chars/token)

### 1.4 Vérité Terrain (10 bugs historiques)
| Bug ID | Description | Fichiers GT |
|:---|:---|:---|
| BUG-01 | Race condition KeyboardInterrupt | `core.py`, `test_abort_interrupt.py` |
| BUG-02 | copy/deepcopy/pickle Sentinel | `_utils.py`, `test_sentinel.py` |
| BUG-03 | package_name resolution | `decorators.py`, `test_basic.py` |
| BUG-04 | get_parameter_source() eager | `core.py`, `test_defaults.py`, `test_options.py` |
| BUG-05 | write_usage spurious chars | `formatting.py`, `test_formatting.py` |
| BUG-06 | Dual-option defaults | `core.py`, `test_options.py` |
| BUG-07 | Sentinel typing parser | `_utils.py`, `core.py`, `parser.py` |
| BUG-08 | Fish completion multiline | `shell_completion.py`, `test_shell_completion.py` |
| BUG-09 | flag_value callable | `core.py`, `test_defaults.py`, `test_options.py` |
| BUG-10 | Sentinel pickling (variant) | `_utils.py`, `test_sentinel.py` |

---

## 2. Tableau Croisé des Résultats

### 2.1 Agrégats par Moteur × Méthode

| Moteur × Méthode | Precision | Recall | F1 | Latence (s) | Fiabilité |
|:---|:---:|:---:|:---:|:---:|:---:|
| **CodeGraph explore** (NL) | 0.279 | **0.733** | 0.389 | 1.694 | 100% |
| **CodeGraph callers** (sym) | 0.477 | 0.400 | 0.400 | 1.482 | 100% |
| **Graft ask** (NL) | 0.000 | 0.000 | 0.000 | 1.000 | 100% |
| **Graft callers** (sym) | **0.583** | 0.467 | **0.457** | **0.932** | 80% |

### 2.2 Détail par Bug

| Bug | CG explore R | CG callers R | Graft ask R | Graft callers R |
|:---|:---:|:---:|:---:|:---:|
| BUG-01 | 0.5 | 0.5 | 0.0 | 0.5 |
| BUG-02 | **1.0** | 0.5 | 0.0 | 0.5 |
| BUG-03 | 0.0 | 0.0 | 0.0 | 0.0 |
| BUG-04 | **1.0** | **1.0** | 0.0 | 0.333 |
| BUG-05 | **1.0** | 0.5 | 0.0 | 0.5 |
| BUG-06 | 0.5 | 0.5 | 0.0 | **1.0** |
| BUG-07 | **1.0** | 0.0 | 0.0 | 0.333 |
| BUG-08 | **1.0** | 0.5 | 0.0 | **1.0** |
| BUG-09 | 0.333 | 0.0 | 0.0 | 0.0 |
| BUG-10 | **1.0** | 0.5 | 0.0 | 0.5 |

### 2.3 Analyse des Échecs

**Graft `ask` (0% recall sur les 10 bugs)** :
- Graft `ask` utilise un mode **lexical** par défaut (pas sémantique/LLM)
- Les questions en langage naturel ne matchent pas les tokens indexés
- Les symboles recherchés (ex: "KeyboardInterrupt", "Sentinel") sont trop spécifiques pour la recherche lexicale
- **Constat** : Graft `ask` n'est pas conçu pour du QA navigation en NL — il faut d'abord `graft build --deep` pour l'index sémantique

**CodeGraph `explore` (recall 73% mais precision 28%)** :
- Retourne le **code source complet** + blast radius — beaucoup de faux positifs
- Mais identifie correctement les fichiers pertinents dans 7/10 cas

**Graft `callers` (F1=0.457, meilleur score)** :
- Meilleure precision (0.583) et meilleur F1 (0.457)
- Mais 80% de fiabilité (échoue sur `package_name` et `flag_value`)
- Plus rapide (0.932s vs 1.4-1.7s)

---

## 3. Verdict Argumenté

### 3.1 Constats Principaux

1. **CodeGraph `explore` domine en recall** (0.733) — c'est le meilleur mode pour identifier *tous* les fichiers pertinents, au prix de faux positifs
2. **Graft `callers` domine en precision et F1** — plus ciblé, plus rapide, mais moins fiable (20% d'échecs)
3. **Graft `ask` est inopérant en mode lexical** — nécessite `--deep` build pour le QA sémantique, ce qui n'a pas été testé ici (hors périmètre du spike)
4. **Les deux moteurs sont rapides** (< 2s par appel) — la latence n'est pas un facteur discriminant
5. **CodeGraph a 100% de fiabilité** — Graft perd 20% sur des symboles ambigus

### 3.2 Recommandation

**Architecture recommandée : Mode hybride séquentiel**

```
┌─────────────────────────────────────────────────────┐
│  Phase 1 : Exploration à haut recall                │
│  → CodeGraph explore (NL query)                     │
│  → Résultat : ensemble large de fichiers candidats  │
├─────────────────────────────────────────────────────┤
│  Phase 2 : Filtrage à haute precision               │
│  → Graft callers (symbol-based)                     │
│  → Résultat : sous-ensemble affiné                  │
├─────────────────────────────────────────────────────┤
│  Phase 3 : Validation croisée                       │
│  → Intersection des résultats                       │
│  → Fichiers dans les deux = haute confiance         │
└─────────────────────────────────────────────────────┘
```

**Justification** :
- CodeGraph `explore` pour le *rappel* (ne manquer aucun fichier pertinent)
- Graft `callers` pour la *précision* (éliminer les faux positifs)
- L'intersection produit un ensemble à la fois complet et ciblé

### 3.3 Limites du Spike

- **Graft `ask` non testé en mode `--deep`** : le build sémantique LLM n'a pas été activé, donc les résultats NL de Graft sont sous-estimés
- **Corpus unique** (90 fichiers Python) : à valider sur des dépôts plus larges
- **Vérité terrain partielle** : les fichiers GT sont ceux du correctif humain, pas nécessairement tous les fichiers impactés
- **Pas de mesure de tokens réelle** : estimation approximative (~4 chars/token)

---

## 4. Recommandations pour les Récits 131-135

| Récit | Recommandation |
|:---|:---|
| **MLOOP-131** | Implémenter le pipeline séquentiel (CodeGraph explore → Graft callers → intersection) |
| **MLOOP-132** | Tester Graft `--deep` build sur le même corpus pour valider le mode sémantique |
| **MLOOP-133** | Ajouter un mécanisme de fallback : si Graft callers échoue (exit 1), promouvoir les résultats CodeGraph |
| **MLOOP-134** | Mesurer les tokens réels via les APIs LiteLLM (pas l'estimation) |
| **MLOOP-135** | Étendre le benchmark à 3+ dépôts de tailles variées (S/M/L) |

---

## 5. Artefacts

| Artefact | Chemin |
|:---|:---|
| Dataset de benchmark | `scratch/mloop-130-benchmark/benchmark_dataset.py` |
| Script d'exécution | `scratch/mloop-130-benchmark/run_benchmark.py` |
| Résultats JSON | `scratch/mloop-130-benchmark/results/benchmark_results.json` |
| Corpus cloné | `scratch/mloop-130-benchmark/corpus/` (git-ignored) |
| Index CodeGraph | `scratch/mloop-130-benchmark/corpus/.codegraph/` |
| Index Graft | `scratch/mloop-130-benchmark/corpus/graft/` |

---

*Rapport généré le 2026-09-21 — Seed 42 — Corpus pallets/click@6aabf099*
