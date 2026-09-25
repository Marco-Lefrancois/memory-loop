---
id: MLOOP-342-BE
jira_key: ''
epic_key: EPIC-34-WFM-COGNITIVE-WIKI-GRAPH
type: Feature
title: Boucle de Fact-Search Réflexif à Budget Borné (B <= 3) & Arrêt Anticipé Adaptatif
tags:
- core
- search
- reflection
- fact-search
- backend
status: DONE_TESTED
grill_me: DONE
invest_score: 6/6
layer: backend
blocked_by:
- MLOOP-340-BE
- MLOOP-341-BE
created_at: '2026-09-25'
validated_by: Marco
validated_at: '2026-09-25T17:16:24Z'
dossier_ref: memory/evidence/MLOOP-342-BE_fact_dossier.md
ttl_cycles: 2
---

# Boucle de Fact-Search Réflexif à Budget Borné (B <= 3) & Arrêt Anticipé Adaptatif

---

## Description
**En tant qu'** Agent Orchestrateur ou Moteur de Fact-Search mLoop (Phase 2 : Plan & Analyse),  
**je veux** disposer d'une boucle de recherche itérative bornée à un budget maximal $B \le 3$ passes qui évalue dynamiquement la complétude du panier de preuves accumulé et s'interrompt dès l'émission d'un drapeau d'arrêt adaptatif $f^{(t)} = \text{Final}$,  
**afin de** garantir une couverture complète des preuves documentaires requises pour les 4 piliers Gherkin tout en économisant ~37% d'appels d'inférence inutiles, conformément aux découvertes empiriques de WFM (*arXiv:2609.18182*).

---

## Contexte & Périmètre

### Contexte Métier
Dans le pipeline actuel, la recherche documentaire amont (Fact-Search) procède par une interrogation statique unique (`top-k`). Si les preuves nécessaires à l'élaboration d'un scénario d'exception ou d'un critère d'acceptation complexe sont disséminées dans plusieurs documents, l'agent échoue ou comble le vide par hallucination paramétrique. L'approche WFM introduit une boucle d'auto-réflexion bornée : à chaque tour, l'agent inspecte ce qu'il a trouvé, identifie ce qui manque, formule une sous-requête ciblée $q^{(t+1)}$, et s'arrête dès que la preuve est suffisante ($f^{(t)} = \text{Final}$).

### In-Scope
- Implémentation du module `src/pipelines/reflective_search.py` (strictement $\le 300$L, `RULE-AST-01`, `ADR-0202`).
- Moteur d'itération réflexive `execute_reflective_search(query: str, budget: int = 3, db_path: Optional[Path] = None) -> ReflectiveSearchResult`.
- Accumulation cumulative des preuves sans perte : $\mathcal{C}^{(t)} = \mathcal{C}^{(t-1)} \cup \mathcal{D}^{(t)}$.
- Détecteur de complétude documentaire : vérifie si toutes les entités cibles disposent d'au moins un passage lié (ou couverture textuelle FTS5 $\ge 85\%$).
- Émission du drapeau d'état : `Continue` (si des preuves restent à trouver) ou `Final` (si le dossier de preuve est complet).
- Barrière budgétaire stricte : arrêt forcé au tour $t = B$ ($B=3$ par défaut, max 6).
- Gestion des impasses : arrêt immédiat à $t=1$ si aucun résultat n'est trouvé (`NO_EVIDENCE_FOUND`).
- Expansion topologique pour générer $q^{(t+1)}$ via les entités voisines non explorées des passages accumulés.
- Détection de stagnation : arrêt si $q^{(t+1)}$ a déjà été interrogée (`STAGNATION_DETECTED`).

### Out-of-Scope
- Récriture humaine des requêtes.
- Modification des données stockées dans SQLite.

---

## Critères d'acceptation

### Opérations Métier & Logique Backend *(backend)*
#### 1. Exécution de la Recherche Réflexive Bornée
* **Entrée Métier** : Requête initiale $q^{(1)}$, budget maximal $B$ ($1 \le B \le 6$, défaut 3), chemin SQLite optionnel.
* **Règles d'admissibilité & Validation** : La requête ne doit pas être vide ; le budget doit être un entier positif borné.
* **Traitement & Algorithme Métier** :
  1. Tour $t=1$ : recherche initiale sur le Wiki Graph combinant FTS5 lexical (`wiki_passages_fts`) et hyper-arêtes (`wiki_cross_links`).
  2. Si aucun passage trouvé à $t=1$ : arrêt immédiat avec `status="NO_EVIDENCE_FOUND"`, `stopped_early=True`, `total_rounds=1`.
  3. Accumulation sans perte des passages retournés dans le panier de preuves $\mathcal{C}^{(1)}$.
  4. Évaluation de complétude : si toutes les entités de la requête initiale ont au moins un passage lié ou si la couverture FTS5 $\ge 85\%$ : émettre $f^{(1)} = \text{Final}$ et renvoyer le résultat (`stopped_early=True`).
  5. Sinon, sélection de l'entité voisine non explorée la plus pertinente pour formuler $q^{(2)}$.
  6. Détection de stagnation : si $q^{(t+1)}$ a déjà été visitée, stopper avec `status="STAGNATION_DETECTED"`.
  7. Répéter jusqu'à $t=B$. Au tour $B$, forcer l'arrêt avec `status="BUDGET_EXHAUSTED"`.
* **Résultat Métier & Mutations** : Objet immuable `ReflectiveSearchResult(query, total_rounds, final_evidence, stopped_early, coverage_score, status, history)`.
* **Cas de Rejet Métier** : Requête vide rejetée avec exception typée `ValueError`.

---

## Parcours Interactif & API

### Contrats d'Échange API (Backend / Services)
- `src.pipelines.reflective_search:execute_reflective_search(query: str, budget: int = 3, db_path: Optional[Path] = None) -> ReflectiveSearchResult`

| Méthode | Route / Point d'Entrée | Finalité | Contrat |
| :--- | :--- | :--- | :--- |
| `execute_reflective_search` | `src.pipelines.reflective_search:execute_reflective_search` | Recherche réflexive adaptative bornée | `(query: str, budget: int = 3, db_path: Optional[Path]) -> ReflectiveSearchResult` |

### Matrice des Contrats API
| Méthode | Route / Point d'Entrée | Finalité | Contrat |
| :--- | :--- | :--- | :--- |
| `execute_reflective_search` | `src.pipelines.reflective_search:execute_reflective_search` | Recherche réflexive adaptative bornée | `(query: str, budget: int = 3, db_path: Optional[Path]) -> ReflectiveSearchResult` |

> OQ-342-1 : Ce récit définit une fonction Python interne (module `src.pipelines.reflective_search`), pas des endpoints HTTP/REST. La "Route / Point d'Entrée" référence le chemin de module Python qualifié (`module:function`), conforme au standard Zéro Fausse Route (ADR-0319) pour les APIs internes. **[API de soumission à définir]** — Aucune route HTTP/REST n'est exposée par ce module.

---

## Règles d'affaires

- **Budget Inviolable (Arbitrage Micro-Grill Q3)** : La boucle s'arrête au plus tard à $t = B$ ($B=3$ par défaut). Aucune boucle infinie n'est permise.
- **Principe d'Accumulation Monotone** : Aucune preuve découverte au tour $t$ ne peut être retirée ou perdue aux tours ultérieurs ($\mathcal{C}^{(t-1)} \subseteq \mathcal{C}^{(t)}$).
- **Arrêt Adaptatif Prioritaire (Arbitrage Micro-Grill Q1)** : Dès que toutes les entités explicites de la requête sont documentées (ou couverture $\ge 85\%$), le drapeau `Final` est levé et la recherche s'interrompt.
- **Expansion Topologique Anti-Stagnation (Arbitrage Micro-Grill Q2)** : La sous-requête suivante cible les entités voisines non explorées ; toute requête déjà visitée coupe immédiatement la boucle.
- **Modularité Étroite (ADR-0202)** : Le fichier source `src/pipelines/reflective_search.py` doit strictement respecter la limite de $\le 300$ lignes.

---

## Références

### 1. Preuves Amont & Traçabilité Factuelle
- 📂 **Dossier de Preuves Factuelles** : [`memory/evidence/MLOOP-342-BE_fact_dossier.md`](../../memory/evidence/MLOOP-342-BE_fact_dossier.md)
- 📄 **Publication de Référence** : WFM (*arXiv:2609.18182*, Section 3.3 : *Iterative Retrieval with Self-Reflection*, Figure 3b).

### 2. Spécifications & Modèles de Données SSOT
- 🏛️ **Persistance Relationnelle** : [`src/state/wiki_graph_db.py`](../../src/state/wiki_graph_db.py)
- 📜 **ADR Associé** : [ADR-0395](../../standards/adr-system/0395-wiki-graph-dual-layer-et-fact-search-reflexif-wfm.md)

---

## Scénarios de test

```gherkin
# language: fr
Fonctionnalité: Boucle de Fact-Search Réflexif à Budget Borné

  # CHEMIN NOMINAL (Happy Path & Persistance)
  Scénario: Arrêt adaptatif précoce dès que les preuves sont complètes
    Étant donné une requête ciblée sur l'entité "ADR-0395"
    Et que le premier tour de recherche retourne le passage exact contenant la décision
    Quand la boucle de recherche réflexive évalue le panier de preuves
    Alors le drapeau "Final" est émis dès le tour 1
    Et le résultat indique "stopped_early = Vrai" avec "total_rounds = 1"
    Et les tours 2 et 3 ne sont jamais exécutés

  # EXCEPTIONS & REJETS MÉTIER (Règles d'affaires)
  Scénario: Épuisement du budget maximal sur une recherche complexe à plusieurs sauts
    Étant donné une requête multi-hop nécessitant d'explorer plusieurs entités
    Et que chaque tour découvre une entité voisine sans atteindre la couverture complète
    Quand la boucle atteint le budget maximal B = 3
    Alors le traitement s'interrompt mécaniquement au tour 3 avec "status = 'BUDGET_EXHAUSTED'"
    Et le résultat consolide l'ensemble des preuves cumulées sans dépasser la limite

  # RÉSILIENCE TECHNIQUE & MODE DÉGRADÉ (Timeouts, Idempotence, Concurrence)
  Scénario: Interruption préventive en cas de requête dérivée redondante
    Étant donné un tour où la requête dérivée q(2) a déjà été interrogée
    Quand le détecteur de stagnation analyse la progression
    Alors la boucle s'arrête immédiatement avec "status = 'STAGNATION_DETECTED'"
    Et les preuves du tour 1 sont retournées intactes

  # UX, OBSERVABILITÉ & BILAN D'EFFICIENCE
  Scénario: Arrêt immédiat sans gaspillage sur requête sans résultat
    Étant donné une requête portant sur un terme inexistant dans la base
    Quand la recherche est lancée
    Alors la boucle s'arrête au tour 1 avec "status = 'NO_EVIDENCE_FOUND'"
    Et le résultat indique "stopped_early = Vrai" avec zéro preuve
```

---

## Definition of Ready (DoR) Checklist

- [x] **1. Description & Périmètre** : Clairs, contextualisés par WFM et centrés sur la boucle d'auto-réflexion à budget borné ($B \le 3$).
- [x] **2. Critères d'Acceptation** : Spécifications fonctionnelles déterministes, détection de complétude et gestion de la stagnation.
- [x] **3. Contrats d'Échange API & Données** : Signature `execute_reflective_search` et dataclass immuable `ReflectiveSearchResult` définies.
- [x] **4. Dépendances & Impacts** : Dépend de `MLOOP-340-BE` et `MLOOP-341-BE` (opérationnels) ; alimente `MLOOP-343-BE`.
- [x] **5. Dossier de Preuves Sourcé** : Preuves factuelles établies dans `memory/evidence/MLOOP-342-BE_fact_dossier.md`.
- [x] **6. Validation Micro-Grill PO** : 3 arbitrages techniques (complétude entités/FTS $\ge 85\%$, expansion topologique, budget par défaut $B=3$) intégrés.
