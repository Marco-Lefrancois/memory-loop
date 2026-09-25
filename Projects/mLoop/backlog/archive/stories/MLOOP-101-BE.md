---
id: MLOOP-101-BE
jira_key: '-'
epic_key: EPIC-10-SOVEREIGN-EXCELLENCE
type: Feature
title: Rénovation Modulaire du Résolveur Lexical et Grand Livre de Jetons
tags:
- token-ledger
- lexicon
- refactoring
- adr-0202
- adr-0369
status: SHIPPED
grill_me: DONE
plan_ref: memory/plan/implementation_plan_MLOOP-101-BE.md
layer: backend
invest_score: 6/6
macrostructure: workbench
ttl_cycles: 3
---
# [EPIC-10-SOVEREIGN-EXCELLENCE] Rénovation Modulaire du Résolveur Lexical et Grand Livre de Jetons (MLOOP-101-BE)

---

## Description
**En tant qu'** Ingénieur Plateforme / Maintainer mLoop,  
**je veux** scinder les utilitaires monolithiques `lexicon_resolver.py` et `token_ledger.py` en modules restreints sous le plafond des 300 lignes et purger l'ensemble des clauses d'exception silencieuses du répertoire utilitaire,  
**afin de** garantir que 100% de la couche d'outillage support obéit aux normes de robustesse de code senior ADR-0202 et ADR-0369.

---

## Contexte & Périmètre

### Contexte Métier
Le répertoire `src/utils/` regroupe des mécanismes vitaux : l'attribution des projets par préfixe lexical (`lexicon_resolver.py`, 411 lignes), la comptabilité financière des jetons LLM (`token_ledger.py`, 350 lignes) et la pose de verrous concurrents (`file_lock.py`). Certains de ces fichiers excèdent la limite des 300 lignes et intègrent encore d'anciens blocs `except: pass` qui masquent les pannes de disque ou de concurrence. Ce récit élimine définitivement ces vulnérabilités.

### In-Scope
> **Amendé le 2026-09-20 (Grill-Me 1:1 — Arbitrages #2/#3/#4 — dossier : `memory/evidence/MLOOP-101-BE_fact_dossier.md`)**

- Découpage de `src/utils/lexicon_resolver.py` (411L) en :
  - `src/utils/lexicon/entity_matcher.py` : Algorithmes de matching flou et détection des préfixes de tickets.
  - `src/utils/lexicon/project_resolver.py` : Résolution contextuelle et tie-break managérial.
  - Façade publique `SemanticLexiconResolver` intangible (16 sites d'import).
- Découpage de `src/utils/token_ledger.py` (350L) en package :
  - `src/utils/token_ledger/reporting.py` : report budgétaire (`generate_report`, ~100L).
  - `src/utils/token_ledger/key_info.py` : sélection de clé LiteLLM (`resolve_active_key_info`, ~70L).
  - Façade `TokenLedger` allégée < 300L (`calculate_cost`, `record_interaction`, `load_entries`), intangible (7 sites d'import).
- Audit et remplacement exhaustif de tous les `except: pass` dans `src/utils/file_lock.py`, `src/utils/context_guard.py` et `src/utils/opencode_meter.py`.
- Extension (Arbitrage #2) : audit et remplacement des `except: pass` dans `src/utils/context_monitor.py`, `src/utils/lexical_guard.py` et `src/utils/antigravity_meter.py`.
- Extension (Arbitrage #2) : correction RULE-AST-02 de `src/utils/opencode_meter.py` (`sqlite3.connect` nu, L143 → context manager).
- Non-régression totale sur `tests/test_token_ledger.py`, `tests/test_lexicon_project_resolver.py`, `tests/test_lexicon_resolver_tiebreak.py` et `tests/test_lexicon_resolve_story_prefix.py`.
- Harnais de performance (Arbitrage #4) : `tests/performance/test_utils_latency.py` (moyenne < 5 ms + plafonds 300L/15 Ko).

### Out-of-Scope
- Altération du format de stockage du grand livre de jetons JSONL.
- Modification des seuils financiers et plafonds d'alerte configurés.

---

## Critères d'acceptation

### Opérations Métier & Logique Backend

#### 1. Découpage Modulaire et Sécurisation des Utilitaires Système
* **Entrée Métier** : Chaîne textuelle à classifier pour le résolveur lexical, ou consommation brute de tokens (prompt, complétion) pour le ledger.
* **Règles d'admissibilité & Validation** : Tout fichier sous `src/utils/` doit respecter une taille maximale de 300 lignes physiques et zéro bloc d'interception aveugle sans journalisation contextuelle.
* **Traitement & Algorithme Métier** : Exécution modulaire de la détection lexicale, enregistrement atomique et thread-safe des transactions de jetons avec verrouillage explicite et gestion de ressources via gestionnaires de contexte `with`.
* **Résultat Métier & Mutations** : Métriques de consommation persistées et identification univoque du projet cible, sans compromettre la performance ni masquer d'anomalies E/S.
* **Cas de Rejet Métier** : Signalement immédiat par exception typée ou journalisation explicite en cas de verrou corrompu ou d'incapacité d'écriture fichier.

#### Matrice des Contrats API
N/A — Récit de refactoring framework 100% headless : aucune route REST/CTA n'est exposée, consommée ou modifiée (les 16 sites d'import recensés sont des imports Python internes, cf. dossier de preuves §3.2).
- **OQ-101 (Exemption Zéro Fausse Route)** : Exemption complète de la Matrice des Contrats API — composant backend sans interface HTTP `[API de soumission à définir]` ; toute future exposition d'API est reportée et à confirmer dans un récit dédié avec sa propre matrice.
- **Admission of Limits** : Les 3 avertissements génériques rubber-duck (timeout réseau, expiration de session, validation de saisie extrême) sont hors domaine pour ce composant headless (ni UI, ni API distante) ; la résilience E/S locale est couverte par le Pilier 2 (verrous corrompus, échecs d'écriture disque).

---

## Scénarios de test

```gherkin
# language: fr
Fonctionnalité: Rénovation Modulaire du Résolveur Lexical et Grand Livre de Jetons

  # CHEMIN NOMINAL
  Scénario: Résolution lexicale et comptabilisation de tokens intègres
    Étant donné une requête référençant un identifiant de ticket mLoop
    Quand le résolveur lexical détermine le projet et que le grand livre enregistre les tokens
    Alors le projet cible est correctement identifié
    Et la transaction de jetons est persistée sans anomalie

  # EXCEPTIONS & REJETS MÉTIER
  Scénario: Détection et journalisation explicite lors d'un verrou concurrent bloqué
    Étant donné un conflit de concurrence sur le fichier de verrou
    Quand une écriture concurrente est tentée sur le grand livre
    Alors le conflit est tracé dans les journaux d'audit avec son niveau d'exception
    Et aucune interruption silencieuse par clause vide n'est tolérée

  # RÉSILIENCE TECHNIQUE & MODE DÉGRADÉ
  Scénario: Maintien de la performance sous forte charge de requêtes
    Étant donné un afflux massif de résolutions de préfixes
    Quand le module découpé effectue les calculs de correspondance
    Alors le temps de réponse unitaire moyen demeure sous le seuil des 5 millisecondes
    Et la mémoire vive consommée reste stable

  # UX, OBSERVABILITÉ & EMPTY STATE
  Scénario: Vérification de conformité globale du répertoire utils
    Étant donné l'achèvement de la rénovation modulaire
    Quand l'analyseur déterministe code-check inspecte l'ensemble du dossier utils
    Alors chaque module audité obtient la mention PASS
    Et le compte total des violations AST pour cette couche est strictement égal à zéro
```
