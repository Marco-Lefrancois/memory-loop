---
id: MLOOP-352-BE
jira_key: ''
epic_key: EPIC-35-REFIGBENCH-ARTIFACT-HARNESS-V2
type: Feature
title: Linter Matriciel d'Inversion Causale par Comparaison d'Adjacence (A_spec vs A_diag)
tags:
- core
- linter
- causality
- matrix
- archify
- backend
status: DONE_TESTED
grill_me: DONE
invest_score: 6/6
layer: backend
blocked_by:
- MLOOP-350-BE
- MLOOP-351-BE
created_at: '2026-09-25'
validated_by: Marco
validated_at: '2026-09-25T21:29:40Z'
dossier_ref: memory/evidence/MLOOP-352-BE_fact_dossier.md
ttl_cycles: 3
---

# Linter Matriciel d'Inversion Causale par Comparaison d'Adjacence (A_spec vs A_diag)

---

## Description
**En tant qu'** Architecte Système ou Auditeur de Cohérence causale mLoop (Phase 2 & Phase 4),  
**je veux** disposer d'un vérificateur matriciel déterministe qui confronte la matrice d'adjacence des dépendances théoriques du code/spécifications ($\mathbf{A}_{\text{spec}}$) à la matrice d'adjacence des connecteurs du schéma graphique ($\mathbf{A}_{\text{diag}}$),  
**afin d'** interdire mécaniquement toute inversion de sens de flux ou de flèche relationnelle dans les schémas d'architecture livrés aux développeurs, résolvant la défaillance critique mise en évidence dans ReFigBench (*arXiv:2609.18844*, Figure 6).

---

## Contexte & Périmètre

### Contexte Métier
L'étude ReFigBench a mis en lumière l'un des angles morts les plus dangereux de l'IA générative : un agent peut produire un diagramme d'une éditabilité et d'une esthétique parfaites tout en **inversant silencieusement toutes les flèches du pipeline** (la sortie devenant l'entrée et vice-versa). Dans le contexte de l'architecture logicielle de mLoop, présenter une flèche inversée entre un composant émetteur et récepteur (ex: inverser la dépendance entre un service métier et sa couche d'accès aux données) conduit les ingénieurs ou agents de codage avals à implémenter le contraire absolu de l'architecture voulue.

### In-Scope
- Implémentation du module `src/pipelines/causal_flow_linter.py` (strictement $\le 300$L, `RULE-AST-01`).
- Moteur d'extraction et de comparaison matricielle `verify_causal_adjacency_matrices(spec_dependencies: list[tuple], diagram_edges: list[dict]) -> CausalLinterResult`.
- Construction de la matrice d'adjacence dirigée théorique $\mathbf{A}_{\text{spec}}[u, v] \in \{0, 1\}$.
- Construction de la matrice d'adjacence dirigée observée sur le schéma $\mathbf{A}_{\text{diag}}[u, v] \in \{0, 1\}$.
- Détection des anomalies causales :
  - **Inversion Causale Stricte** : $\mathbf{A}_{\text{spec}}[u, v] = 1$ et $\mathbf{A}_{\text{diag}}[v, u] = 1$ alors que l'arête n'est pas bidirectionnelle.
  - **Arête Contradictoire Fantôme** : existence d'un flux inverse contredisant une règle d'encapsulation (ex. couche basse dépendant d'une couche haute).
- Sanction éliminatoire immédiate : levée de l'erreur bloquante `CAUSAL_FLOW_INVERSION_DETECTED` forçant le sous-score sémantique $S$ à 0.
- Identification précise des identifiants de nœuds sources et cibles en conflit pour auto-remédiation immédiate par WikiFix.

### Out-of-Scope
- Correction graphique automatique des coordonnées de la flèche (déléguée à l'outil Archify).
- Détection de cycles d'héritage objet complexes non modélisés.

---

## Critères d'acceptation

### Opérations Métier & Logique Backend *(backend)*
#### 1. Audit Matriciel de Conformité Causale
* **Entrée Métier** : Liste des couples de dépendances attendues $(u \to v)$ issues de l'AST ou de la story INVEST, liste des arêtes observées sur le schéma.
* **Règles d'admissibilité & Validation** : Les deux listes doivent partager le même référentiel d'identifiants de nœuds.
* **Traitement & Algorithme Métier** :
  1. Indexation des nœuds et projection dans deux matrices creuses booléennes $\mathbf{A}_{\text{spec}}$ et $\mathbf{A}_{\text{diag}}$.
  2. Produit de Hadamard de détection d'inversion : repérage des couples où $\mathbf{A}_{\text{spec}} \odot \mathbf{A}_{\text{diag}}^T \neq \mathbf{0}$ pour les arêtes asymétriques.
  3. Si au moins une inversion est détectée, le statut bascule à invalide avec extraction des paires de nœuds incriminées.
* **Résultat Métier & Mutations** : Objet `CausalLinterResult(is_valid: bool, inverted_flows: list[dict], missing_flows: list[dict], anomaly_code: str)`.
* **Cas de Rejet Métier** : Rejet catégorique avec code `CAUSAL_FLOW_INVERSION_DETECTED`.

---

## Parcours Interactif & API

### Contrats d'Échange API (Backend / Services)
- `src.pipelines.causal_flow_linter:verify_causal_adjacency_matrices(...) -> CausalLinterResult`

| Méthode | Route / Point d'Entrée | Finalité | Contrat |
| :--- | :--- | :--- | :--- |
| `verify_causal_adjacency_matrices` | `src.pipelines.causal_flow_linter:verify_causal_adjacency_matrices` | Vérification matricielle anti-inversion | `(spec_deps: list, diagram_edges: list) -> CausalLinterResult` |

---

## Règles d'affaires

- **Tolérance Zéro Inversion Causale** : Une seule flèche orientée à l'envers d'une dépendance logicielle critique entraîne le rejet immédiat du schéma ($S=0$, Gate fermée).
- **Gestion des Flux Bidirectionnels** : Une liaison explicitement déclarée `bidirectional` ou `symmetric` dans la spécification n'est pas traitée comme une inversion.

---

## Références

### 1. Preuves Amont & Traçabilité Factuelle
- 📂 **Dossier de Preuves Factuelles** : [`memory/evidence/MLOOP-352-BE_fact_dossier.md`](../../memory/evidence/MLOOP-352-BE_fact_dossier.md)
- 📄 **Publication de Référence** : ReFigBench (*arXiv:2609.18844*, Section 5 : *Editability Can Mask Semantic Failure*, Figure 6, Section I Case Study).

### 2. Spécifications & Modèles de Données SSOT
- 🏛️ **Graphe de Dépendances** : [`standards/protocols/CLI_PIPELINE_GUIDE.md`](../../standards/protocols/CLI_PIPELINE_GUIDE.md)
- 📜 **ADR Associé** : [ADR-0396](../../standards/adr-system/0396-audit-artefacts-5-axes-et-anti-inversion-causale-refigbench.md)

---

## Scénarios de test

```gherkin
# language: fr
Fonctionnalité: Linter Matriciel d'Inversion Causale par Comparaison d'Adjacence

  # CHEMIN NOMINAL (Happy Path & Persistance)
  Scénario: Validation d'un schéma d'architecture dont toutes les flèches respectent la spécification
    Étant donné une dépendance déclarée "Module_Auth -> Token_Verifier" dans la spécification
    Et que le diagramme Archify contient une arête orientée de "Module_Auth" vers "Token_Verifier"
    Quand le linter matriciel compare les matrices d'adjacence
    Alors le statut est "is_valid = Vrai"
    Et la liste des flux inversés est vide

  # EXCEPTIONS & REJETS MÉTIER (Règles d'affaires)
  Scénario: Détection et rejet éliminatoire d'une flèche de dépendance inversée
    Étant donné une spécification prescrivant "Service_Paiement -> Passerelle_Bancaire"
    Mais que le schéma graphique relie la flèche de "Passerelle_Bancaire" vers "Service_Paiement"
    Quand le linter matriciel inspecte l'artefact
    Alors l'anomalie "CAUSAL_FLOW_INVERSION_DETECTED" est levée
    Et le résultat identifie précisément la paire inversée
    Et le sous-score de structure sémantique S est forcé à zéro

  # RÉSILIENCE TECHNIQUE & MODE DÉGRADÉ (Timeouts, Idempotence, Concurrence)
  Scénario: Prise en compte légitime d'une relation déclarée explicitement bidirectionnelle
    Étant donné une liaison déclarée "bidirectional" entre deux microservices partenaires
    Quand le diagramme connecte les deux nœuds
    Alors aucune fausse inversion n'est signalée
    Et le linter valide la symétrie sans pénalité

  # UX, OBSERVABILITÉ & EMPTY STATE (Spinners, Retours Écran, Logs)
  Scénario: Rapport textuel précis des nœuds concernés par l'inversion
    Étant donné un rejet pour inversion de flux
    Quand le message d'erreur est restitué
    Alors le log affiche clairement : "Inversion détectée : la flèche pointe de B vers A alors que la dépendance exige A vers B"
```

---

## Definition of Ready (DoR) Checklist

- [x] **1. Description & Périmètre** : Clairs, contextualisés par ReFigBench et formulés autour de la comparaison d'adjacence matricielle ($\mathbf{A}_{\text{spec}} \text{ vs } \mathbf{A}_{\text{diag}}$).
- [x] **2. Critères d'Acceptation** : Spécifications mathématiques déterministes, seuils d'admissibilité et gestion des flux bidirectionnels.
- [x] **3. Contrats d'Échange API & Données** : Signature `verify_causal_adjacency_matrices` et classe immuable `CausalLinterResult` définies.
- [x] **4. Dépendances & Impacts** : Dépend de `MLOOP-350-BE` et `MLOOP-351-BE` (opérationnels).
- [x] **5. Dossier de Preuves Sourcé** : Preuves factuelles établies dans `memory/evidence/MLOOP-352-BE_fact_dossier.md`.
- [x] **6. Validation Micro-Grill PO** : 3 arbitrages techniques (slugified normalization, missing vs inverted flow, support flag bidirectional) intégrés.
