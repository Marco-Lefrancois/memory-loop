---
id: MLOOP-342-BE
jira_key: ''
epic_key: EPIC-34-WFM-COGNITIVE-WIKI-GRAPH
type: Feature
title: Boucle de Fact-Search Réflexif à Budget Borné (B <= 4) & Arrêt Anticipé Adaptatif
tags:
- core
- search
- reflection
- fact-search
- backend
status: DRAFT
grill_me: PENDING
invest_score: 6/6
layer: backend
blocked_by:
- MLOOP-340-BE
- MLOOP-341-BE
created_at: '2026-09-25'
ttl_cycles: 3
---

# Boucle de Fact-Search Réflexif à Budget Borné (B <= 4) & Arrêt Anticipé Adaptatif

---

## Description
**En tant qu'** Agent Orchestrateur ou Moteur de Fact-Search mLoop (Phase 2 : Plan & Analyse),  
**je veux** disposer d'une boucle de recherche itérative bornée à un budget maximal $B \le 4$ passes qui évalue dynamiquement la complétude du panier de preuves accumulé et s'interrompt dès l'émission d'un drapeau d'arrêt adaptatif $f^{(t)} = \text{Final}$,  
**afin de** garantir une couverture complète des preuves documentaires requises pour les 4 piliers Gherkin tout en économisant ~37% d'appels d'inférence inutiles, conformément aux découvertes empiriques de WFM (*arXiv:2609.18182*).

---

## Contexte & Périmètre

### Contexte Métier
Dans le pipeline actuel, la recherche documentaire amont (Fact-Search) procède par une interrogation statique unique (`top-k`). Si les preuves nécessaires à l'élaboration d'un scénario d'exception ou d'un critère d'acceptation complexe sont disséminées dans plusieurs documents, l'agent échoue ou comble le vide par hallucination paramétrique. L'approche WFM introduit une boucle d'auto-réflexion bornée : à chaque tour, l'agent inspecte ce qu'il a trouvé, identifie ce qui manque, formule une sous-requête ciblée $q^{(t+1)}$, et s'arrête dès que la preuve est suffisante ($f^{(t)} = \text{Final}$).

### In-Scope
- Implémentation du module `src/pipelines/reflective_search.py` (strictement $\le 300$L, `RULE-AST-01`).
- Moteur d'itération réflexive `execute_reflective_search(query: str, budget: int = 4) -> ReflectiveSearchResult`.
- Accumulation cumulative des preuves sans perte : $\mathcal{C}^{(t)} = \mathcal{C}^{(t-1)} \cup \mathcal{D}^{(t)}$.
- Détecteur de complétude documentaire : vérifie si les termes clés et relations de la requête sont couverts par des citations exactes.
- Émission du drapeau d'état : `Continue` (si des preuves restent à trouver) ou `Final` (si le dossier de preuve est complet).
- Barrière budgétaire stricte : arrêt forcé au tour $t = B$ si aucun arrêt anticipé n'est déclenché.
- Métriques d'observabilité : nombre de passes réelles exécutées, gain de tokens, taux d'arrêt anticipé.

### Out-of-Scope
- Récriture humaine des requêtes.
- Modification des données stockées dans SQLite.

---

## Critères d'acceptation

### Opérations Métier & Logique Backend *(backend)*
#### 1. Exécution de la Recherche Réflexive Bornée (`execute_reflective_search`)
* **Entrée Métier** : Requête initiale $q^{(1)}$, budget maximal $B$ ($1 \le B \le 6$, défaut 4), seuil de complétude.
* **Règles d'admissibilité & Validation** : La requête ne doit pas être vide ; le budget doit être un entier positif borné.
* **Traitement & Algorithme Métier** :
  1. Tour $t=1$ : recherche initiale sur le Wiki Graph combinant FTS5 lexical et nœuds transversaux.
  2. Accumulation des passages retournés dans le panier de preuves $\mathcal{C}^{(1)}$.
  3. Évaluation de complétude : analyse si les entités cibles disposent d'un ancrage textuel suffisant.
  4. Si complet : émission de $f^{(1)} = \text{Final}$ et retour immédiat du résultat (arrêt en 1 passe).
  5. Sinon, génération de la requête dérivée $q^{(2)}$ ciblant les entités non couvertes et boucle jusqu'à $t=B$.
* **Résultat Métier & Mutations** : Objet `ReflectiveSearchResult(query: str, total_rounds: int, final_evidence: list[dict], stopped_early: bool, coverage_score: float)`.
* **Cas de Rejet Métier** : Échec propre si aucune correspondance trouvée dès la première passe avec statut `NO_EVIDENCE_FOUND`.

---

## Parcours Interactif & API

### Contrats d'Échange API (Backend / Services)
- `src.pipelines.reflective_search:execute_reflective_search(query: str, budget: int = 4) -> ReflectiveSearchResult`

#### Matrice des Contrats API
| Méthode | Route / Point d'Entrée | Finalité | Contrat |
| :--- | :--- | :--- | :--- |
| `execute_reflective_search` | `src.pipelines.reflective_search:execute_reflective_search` | Exécution de la recherche réflexive adaptative | `(query: str, budget: int = 4) -> ReflectiveSearchResult` |

- **Admission of Limits & Résilience Système** :
  - **Plafond Budgétaire Garanti** : Le nombre d'itérations ne peut sous aucun prétexte excéder $B$.
  - **Détection de Boucle Infinie** : Si $q^{(t+1)}$ est identique ou quasi-identique à une requête antérieure, la boucle s'interrompt immédiatement avec arrêt forcé.

---

## Règles d'affaires

- **Budget Inviolable** : La boucle s'arrête au plus tard à $t = B$ ; aucune relance non bornée n'est autorisée.
- **Principe d'Accumulation Monotone** : Aucune preuve découverte au tour $t$ ne peut être retirée ou perdue aux tours ultérieurs ($\mathcal{C}^{(t-1)} \subseteq \mathcal{C}^{(t)}$).
- **Arrêt Adaptatif Prioritaire** : Dès qu'une preuve textuelle directe est attestée pour chaque entité de la requête, l'arrêt est immédiat sans consommer les tours restants.

---

## Références

### 1. Preuves Amont & Traçabilité Factuelle
- 📂 **Dossier de Preuves** : [`memory/evidence/EPIC-34_wfm_fact_dossier.md`](../../memory/evidence/EPIC-34_wfm_fact_dossier.md)
- 📄 **Publication de Référence** : WFM (*arXiv:2609.18182*, Section 3.3 : *Iterative Retrieval with Self-Reflection*, Figure 3b).

### 2. Spécifications & Modèles de Données SSOT
- 🏛️ **Protocole de Recherche** : [`standards/protocols/DECISION_BRIEF_GUIDE.md`](../../standards/protocols/DECISION_BRIEF_GUIDE.md)
- 📜 **ADR Associé** : [ADR-0395](../../standards/adr-system/0395-wiki-graph-dual-layer-et-fact-search-reflexif-wfm.md)

---

## Scénarios de test

```gherkin
# language: fr
Fonctionnalité: Boucle de Fact-Search Réflexif à Budget Borné

  # CHEMIN NOMINAL (Happy Path & Persistance)
  Scénario: Arrêt adaptatif précoce dès que les preuves sont complètes
    Étant donné une requête ciblée sur une entité "ADR-0392"
    Et que le premier tour de recherche retourne le passage exact contenant la décision
    Quand la boucle de recherche réflexive évalue le panier de preuves
    Alors le drapeau "Final" est émis dès le tour 1
    Et le résultat indique "stopped_early = Vrai" avec "total_rounds = 1"
    Et les tours 2, 3 et 4 ne sont jamais exécutés

  # EXCEPTIONS & REJETS MÉTIER (Règles d'affaires)
  Scénario: Épuisement du budget maximal sur une recherche complexe à plusieurs sauts
    Étant donné une requête multi-hop nécessitant de relier 4 concepts dispersés
    Et que chaque tour ne découvre qu'un concept partiel
    Quand la boucle atteint le budget maximal B = 4
    Alors le traitement s'interrompt mécaniquement au tour 4
    Et le résultat consolide l'ensemble des preuves cumulées sans dépasser la limite

  # RÉSILIENCE TECHNIQUE & MODE DÉGRADÉ (Timeouts, Idempotence, Concurrence)
  Scénario: Interruption préventive en cas de requête dérivée redondante
    Étant donné un tour où la requête dérivée q(2) est identique à q(1)
    Quand le détecteur de stagnation analyse la progression
    Alors la boucle s'arrête immédiatement pour éviter une dépense stérile
    Et les preuves du tour 1 sont retournées

  # UX, OBSERVABILITÉ & EMPTY STATE (Spinners, Retours Écran, Logs)
  Scénario: Rapport d'efficience et journalisation des gains de passes
    Étant donné une recherche résolue en 2 tours au lieu de 4
    Quand le bilan de recherche est consigné
    Alors le log indique un gain d'efficience de 50% sur le budget théorique
```
