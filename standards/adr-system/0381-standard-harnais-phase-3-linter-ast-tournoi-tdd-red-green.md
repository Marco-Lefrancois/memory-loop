---
id: "ADR-0381"
title: "Standard du Harnais Déterministe de Phase 3 : Linter Statique AST, Tournoi TDD Multi-Candidats & Traçabilité Red-Green"
status: "Accepté"
date: "2026-09-19"
type: "Type 1 — Architecture & Gouvernance Système"
authority: "mLoop Senior Architecture Board"
validation_rules:
  - check_id: "ast_checker_compliance"
    severity: "BLOCKING"
    description: "Conformité statique stricte aux règles de modularité ADR-0202 (<=300 lignes, <=15 Ko) et standards senior ADR-0369 vérifiée par ast_checker."
    params:
      max_lines: 300
      max_bytes: 15360
      forbidden_patterns: ["bare_resource_call", "missing_timeout", "silent_except_pass", "missing_stacklevel_2"]
  - check_id: "tdd_red_green_enforcement"
    severity: "BLOCKING"
    description: "Interdiction de transition vers DONE_TESTED ou approbation Gate 3 sans preuves cryptographiques RedSnapshot et GreenSnapshot dans l'EvidencePack."
    params:
      require_red_failure: true
      require_green_success: true
      sha256_binding: true
  - check_id: "tournament_multi_draft_pareto"
    severity: "BLOCKING"
    description: "Évaluation multi-candidats obligatoire pour tout composant Système 1 critique par matrice de décision Pareto pondérée."
    params:
      min_candidates: 2
      weights:
        robustness: 0.40
        simplicity: 0.35
        performance: 0.25
---

# ADR-0381 : Standard du Harnais Déterministe de Phase 3 : Linter Statique AST, Tournoi TDD Multi-Candidats & Traçabilité Red-Green

## Statut
**Accepté (SSOT Normatif)** — 19 Septembre 2026

---

## 1. Contexte & Problématique

Dans l'ingénierie logicielle agentique moderne (2025/2026), l'implémentation brute est devenue quasi instantanée (« *implementation has become cheap, but verification is the new bottleneck* » — Martin Fowler, Databricks, SWE-bench).
Cependant, l'autonomie agentique en Phase 3 (Build) souffre de trois vulnérabilités systémiques majeures :
1. **Le Piège du Tir Unique (*Single-Shot & First-Token Bias*)** :
   Un agent générant du code en une seule passe s'ancre sur ses premiers choix syntaxiques, accumulant de la dette technique ou de l'over-engineering sans confronter des alternatives d'architecture viables.
2. **L'Illusion du Test Vert sans Preuve d'Échec Préalable (TDD Inversé ou Biais du Survivant)** :
   Un test unitaire rédigé après ou conjointement au code peut être tautologique ou permissif. Sans la preuve formelle et immuable que le test échouait (`RED`) avant que le composant ne soit développé (`GREEN`), l'intégrité de la barrière de régression est nulle.
3. **Le Glissement Hors-Standard Silencieux (ADR-0202 & ADR-0369)** :
   Même avec des directives en prompt, des fichiers de code dépassent insensiblement les 300 lignes / 15 Ko, omettent des `timeout=` sur les sous-processus ou requêtes réseau, oublient la fermeture des ressources dans des blocs `with`, ou avalent des exceptions via `except: pass`.

Cette ADR ratifie l'établissement d'un **Harnais Déterministe Physique** pour la Phase 3 de mLoop, composé d'un linter AST statique local, d'un moteur de tournoi de code multi-draft et d'un protocole cryptographique d'enforcement TDD.

---

## 2. Décisions Fondatrices d'Architecture

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ HARNAIS DÉTERMINISTE DE PHASE 3 (BUILD) — ARCHITECTURE GLOBALE (ADR-0381)              │
├────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                        │
│   [ÉTAPE A : SPÉCIFICATION & TDD RED ENFORCEMENT]                                      │
│   Récit INVEST 4 Piliers Gherkin ──> Écriture du Banc de Test (tests/test_*.py)        │
│   └──> Exécution tdd-enforce --phase red                                               │
│   └──> Capture formelle : RedSnapshot(test_sha256, failed_tests, error_sig, UTC)       │
│                                                                                        │
│   [ÉTAPE B : MULTI-DRAFT CODE TOURNAMENT]                                              │
│   Génération de 2 à 3 Candidats Physiques :                                            │
│   • Candidat A : Minimaliste (Standard Library pure, 0 dépendance externe)             │
│   • Candidat B : Robuste & Modulaire (Typage étendu, invariants défensifs)             │
│   └──> Hard Gates (Tolérance 0) : 100% Pytest vert + 0 violation code-check            │
│   └──> Fitness Pareto : S_pareto = 0.40*Robustesse + 0.35*Simplicité + 0.25*Vitesse   │
│   └──> Promotion du Vainqueur en Golden Master (src/) & Archivage Dream RSI            │
│                                                                                        │
│   [ÉTAPE C : LINTER STATIQUE AST DÉTERMINISTE (code-check)]                            │
│   Analyseur AST Python standard (0 dépendance externe, exécution < 50ms) :             │
│   • RULE-AST-01 : <= 300 lignes physiques et <= 15 Ko (ADR-0202)                      │
│   • RULE-AST-02 : Ressources nues interdites (with/async with obligatoire)             │
│   • RULE-AST-03 : Timeout obligatoire sur subprocess/network                           │
│   • RULE-AST-04 : Interdiction du 'except: pass' silencieux                            │
│   • RULE-AST-05 : stacklevel=2 obligatoire sur warnings.warn                           │
│                                                                                        │
│   [ÉTAPE D : SCELLEMENT TDD GREEN & VERROU GATE 3]                                     │
│   Exécution tdd-enforce --phase green ──> GreenSnapshot(code_sha, test_sha, dur, UTC)   │
│   └──> Scellement dans memory/evidence/<STORY>_evidence.json                           │
│   └──> Verrou Gate 3 : Interdiction physique de clore en DONE_TESTED sans le couple   │
│                                                                                        │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Spécification Mathématique de la Matrice de Pareto

La sélection du candidat optimal repose sur une fonction scalaire multicritère normalisée $S_{\text{pareto}} \in [0, 100]$ :

$$S_{\text{pareto}} = (w_R \cdot R) + (w_S \cdot S) + (w_P \cdot P)$$

Avec les pondérations constitutionnelles suivantes :
* **$w_R = 0.40$ (Robustesse & Typage)** :
  $$R = 100 \times \left(1 - \frac{\min(CC_{\text{max}}, 15)}{15}\right) \times \text{TypeAnnotationRatio}$$
* **$w_S = 0.35$ (Simplicité & Sobriété ADR-0202)** :
  $$S = 100 \times \left(1 - \frac{N_{\text{lines}}}{300}\right)$$
* **$w_P = 0.25$ (Performance Relative)** :
  $$P = 100 \times \left(\frac{\min_k T_k}{T_{\text{candidat}}}\right)$$

---

## 4. Conséquences & Invariants Système

1. **Zéro Régression Silencieuse** : Tout code de production est certifié par un cycle Red-Green inviolable.
2. **Conformité Constitutionnelle Automatisée** : Les 7 standards de robustesse Senior Python (ADR-0369) et les plafonds ADR-0202 sont vérifiés par l'AST avant toute intégration dans la branche principale.
3. **Pérennité du Mode Dogfooding** : mLoop s'applique à lui-même les exigences d'outillage les plus exigeantes de l'industrie logicielle agentique.
