# Fiche d'Architecture : ADR-0381 — Harnais Déterministe de Phase 3

## 1. Synthèse Exécutive
* **Identifiant ADR** : [`standards/adr-system/0381-standard-harnais-phase-3-linter-ast-tournoi-tdd-red-green.md`](../../standards/adr-system/0381-standard-harnais-phase-3-linter-ast-tournoi-tdd-red-green.md)
* **Titre** : Standard du Harnais Déterministe de Phase 3 : Linter Statique AST, Tournoi TDD Multi-Candidats & Traçabilité Red-Green
* **Autorité** : mLoop Senior Architecture Board
* **Statut** : Accepté (SSOT Normatif)
* **Date de Ratification** : 19 Septembre 2026

---

## 2. Piliers d'Architecture

### Pilier 1 : Linter Statique AST Local Déterministe (`code-check`)
Un analyseur statique s'appuyant exclusivement sur la bibliothèque standard Python (`ast`) pour auditer le code produit en moins de 50 ms sans dépendance externe lourde :
- **Plafond Modulaire ADR-0202** : Maximum 300 lignes physiques et 15 Ko par fichier de code.
- **Ressources Confinées (ADR-0369 Standard 2)** : Interdiction d'instancier des connexions SQLite, descripteurs de fichiers ou clients HTTP en dehors d'un gestionnaire de contexte (`with` / `async with`).
- **Timeouts Systématiques (ADR-0369 Standard 3)** : Obligation d'un paramètre `timeout=` explicite sur tout appel `subprocess` ou client réseau.
- **Zéro Exception Engloutie (ADR-0369 Standard 4)** : Rejet de tout bloc `except: pass` sans journalisation d'audit contextuelle.
- **Désignation de l'Appelant (ADR-0369 Standard 7)** : Présence obligatoire de `stacklevel=2` sur les avertissements de dépréciation `warnings.warn`.

### Pilier 2 : Moteur de Tournoi Multi-Draft & Matrice Pareto ($S_{\text{pareto}}$)
Face aux tâches critiques du Système 1 (Core Engine), le moteur génère physiquement 2 à 3 candidats sous `memory/drafts/code/<STORY>/` et les soumet à une double épreuve :
1. **Hard Gates (Tolérance 0)** : 100% de tests unitaires passés et 0 violation au linter AST.
2. **Matrice Pareto** :
   $$S_{\text{pareto}} = 0.40 \cdot R + 0.35 \cdot S + 0.25 \cdot P$$
   Le candidat ayant le meilleur score est promu en **Golden Master** dans `src/`. Les autres sont scellés dans le registre de trajectoires contrefactuelles pour le simulateur Dream RSI (ADR-0372).

### Pilier 3 : Enforceur TDD Red-Green & Sceau Gate 3
Empêche tout contournement du cycle TDD en scellant deux empreintes immuables dans l'EvidencePack de chaque récit :
1. `RedSnapshot` : Preuve formelle d'échec du banc de test unitaire avant implémentation (`pytest_exit_code != 0`, hash SHA-256 du fichier de test).
2. `GreenSnapshot` : Preuve formelle de réussite intégrale après implémentation (`pytest_exit_code == 0`, hash SHA-256 du code et des tests, durée en ms).
L'approbation de Gate 3 et le statut `DONE_TESTED` sont physiquement bloqués si ce couple de preuves est incomplet.

---

## 3. Cartographie des Composants & Découpage

| Composant | Fichier Source | Récit Associé | Rôle & Invariant |
| :--- | :--- | :--- | :--- |
| **AST Linter** | `src/core/ast_checker.py` | `MLOOP-080-BE` | Audit statique des 5 règles de modularité et de robustesse. |
| **Code Tournament** | `src/pipelines/code_tournament.py` | `MLOOP-081-BE` | Génération, exécution unitaire et arbitrage Pareto multi-drafts. |
| **TDD Enforcer** | `src/core/tdd_enforcer.py` | `MLOOP-082-BE` | Captation Red/Green, scellement SHA-256 et verrou Gate 3. |

---
*Document scellé et synchronisé avec le référentiel des 96 ADRs de Memory Loop.*
