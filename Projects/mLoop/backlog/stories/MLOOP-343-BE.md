---
id: MLOOP-343-BE
jira_key: ''
epic_key: EPIC-34-WFM-COGNITIVE-WIKI-GRAPH
type: Enabler
title: Mode Reject Souverain Anti-Hallucination & Régularisation de Variance de Scoring
tags:
- core
- qa
- reject-mode
- variance
- grounding
- backend
status: DRAFT
grill_me: PENDING
invest_score: 6/6
layer: backend
blocked_by:
- MLOOP-342-BE
created_at: '2026-09-25'
ttl_cycles: 3
---

# Mode Reject Souverain Anti-Hallucination & Régularisation de Variance de Scoring

---

## Description
**En tant qu'** Auditeur de Preuves Factuelles mLoop (Phase 2 & Phase 4),  
**je veux** disposer d'un mode de validation strict *Reject* qui force l'abstention formelle dès qu'une exigence ou un critère Gherkin manque de fondement documentaire probant, couplé à un contrôle de dispersion de variance des scores de pertinence ($\text{Var} \ge \epsilon$),  
**afin d'** interdire toute hallucination paramétrique dans les spécifications fonctionnelles et éliminer l'effondrement uniforme de pertinence lors du reranking de contexte, conformément aux principes fondateurs de WFM (*arXiv:2609.18182*).

---

## Contexte & Périmètre

### Contexte Métier
Dans l'évaluation de WFM, le mode **Reject** distingue les systèmes qui inventent des réponses plausibles de ceux qui s'ancrent rigoureusement sur la vérité documentaire : WFM y surpasse tous les systèmes concurrents de +4 à +5 points. Parallèlement, l'étude démontre que sur des graphes denses, les mécanismes de scoring s'effondrent vers une distribution quasi-uniforme (*Uniform Attention Collapse*), où tous les documents finissent par recevoir le même poids médiocre. Ce récit transpose ces deux innovations mathématiques dans le moteur d'évaluation cognitive de mLoop.

### In-Scope
- Implémentation du module `src/pipelines/fact_reject_auditor.py` (strictement $\le 300$L, `RULE-AST-01`).
- Moteur d'évaluation en mode Reject `audit_grounding_reject_mode(evidence_pack: dict, claims: list[dict]) -> RejectAuditResult`.
- Rejet strict (*Abstain*) avec statut `REJECT_INSUFFICIENT_EVIDENCE` si une assertion métier ou un critère d'acceptation ne dispose d'aucune citation verbatim avec lien d'hyper-arête vérifié.
- Contrôle de variance d'attention sur les poids de pertinence des passages :
  - Calcul de la variance empirique : $\text{Var}(w) = \frac{1}{N} \sum_{i=1}^N (w_i - \bar{w})^2$.
  - Si $\text{Var}(w) < \epsilon$ (seuil calibré $\epsilon = 0.05$), application d'une pénalité de contraste ou ré-étalement non linéaire (Softmax à température basse $\tau = 0.5$) pour éviter l'aplatissement indécis.
- Émission d'alertes préventives en cas de risque de tassement des scores de contexte.

### Out-of-Scope
- Rédaction manuelle de nouvelles assertions.
- Remplacement du moteur SQLite FTS5.

---

## Critères d'acceptation

### Opérations Métier & Logique Backend *(backend)*
#### 1. Audit en Mode Reject des Assertions Métier (`audit_grounding_reject_mode`)
* **Entrée Métier** : Liste des exigences / critères à certifier, ensemble des passages documentaires accumulés.
* **Règles d'admissibilité & Validation** : Chaque assertion doit posséder un identifiant et un énoncé fonctionnel clair.
* **Traitement & Algorithme Métier** :
  1. Pour chaque assertion, vérification de l'existence d'une correspondance textuelle exacte ou d'une hyper-arête `defines` / `justifies`.
  2. Si aucune preuve formelle n'est trouvée dans le panier documentaire, l'assertion est marquée `UNGROUNDED`.
  3. En mode Reject, la présence d'au moins une assertion `UNGROUNDED` entraîne le rejet global du lot de critères avec code `REJECT_INSUFFICIENT_EVIDENCE`.
* **Résultat Métier & Mutations** : Objet `RejectAuditResult(is_accepted: bool, grounded_count: int, rejected_claims: list[str], variance_score: float)`.
* **Cas de Rejet Métier** : Blocage DoR immédiat avant entrée en Phase 3 si une exigence est non prouvée.

---

## Parcours Interactif & API

### Contrats d'Échange API (Backend / Services)
- `src.pipelines.fact_reject_auditor:audit_grounding_reject_mode(claims: list, passages: list) -> RejectAuditResult`
- `src.pipelines.fact_reject_auditor:calculate_variance_dispersion(scores: list[float]) -> float`

#### Matrice des Contrats API
| Méthode | Route / Point d'Entrée | Finalité | Contrat |
| :--- | :--- | :--- | :--- |
| `audit_grounding_reject_mode` | `src.pipelines.fact_reject_auditor:audit_grounding_reject_mode` | Certification stricte sans hallucination | `(claims: list, passages: list) -> RejectAuditResult` |
| `calculate_variance_dispersion` | `src.pipelines.fact_reject_auditor:calculate_variance_dispersion` | Calcul de dispersion anti-effondrement | `(scores: list[float]) -> float` |

---

## Règles d'affaires

- **Interdiction Formelle d'Extrapolation Paramétrique** : Si une information n'apparaît pas dans les documents sources, l'agent a l'obligation stricte d'admettre son ignorance et de refuser la validation.
- **Seuil Plancher de Variance** : La variance de scoring des passages sélectionnés ne doit pas descendre sous $\epsilon = 0.05$ ; une distribution plate est considérée comme un échec de sélectivité.

---

## Références

### 1. Preuves Amont & Traçabilité Factuelle
- 📂 **Dossier de Preuves** : [`memory/evidence/EPIC-34_wfm_fact_dossier.md`](../../memory/evidence/EPIC-34_wfm_fact_dossier.md)
- 📄 **Publication de Référence** : WFM (*arXiv:2609.18182*, Section 3.4 : *Attention Variance Regularization Loss*, Équation 11, Section 4.5).

### 2. Spécifications & Modèles de Données SSOT
- 🏛️ **Protocole Zéro Blindspot** : [`standards/protocols/ECOSYSTEM_RIGOR_PROTOCOL.md`](../../standards/protocols/ECOSYSTEM_RIGOR_PROTOCOL.md)
- 📜 **ADR Associé** : [ADR-0395](../../standards/adr-system/0395-wiki-graph-dual-layer-et-fact-search-reflexif-wfm.md)

---

## Scénarios de test

```gherkin
# language: fr
Fonctionnalité: Mode Reject Souverain Anti-Hallucination & Régularisation de Variance

  # CHEMIN NOMINAL (Happy Path & Persistance)
  Scénario: Approbation nominale lorsque toutes les exigences sont étayées par des preuves
    Étant donné un ensemble de 4 critères d'acceptation Gherkin
    Et que chaque critère est relié à une citation verbatim dans les passages du Wiki Graph
    Quand l'auditeur exécute le contrôle en mode Reject
    Alors le statut retourné est "is_accepted = Vrai"
    Et la note de dispersion de variance dépasse le seuil minimal de 0.05

  # EXCEPTIONS & REJETS MÉTIER (Règles d'affaires)
  Scénario: Rejet strict pour manque de fondement documentaire sur une règle critique
    Étant donné un scénario d'exception affirmant une règle de quota non documentée
    Mais qu'aucun passage ingéré ne mentionne cette valeur
    Quand le mode Reject est appliqué
    Alors la certification est immédiatement refusée avec le code "REJECT_INSUFFICIENT_EVIDENCE"
    Et le critère non ancré est explicitement listé dans les rejets

  # RÉSILIENCE TECHNIQUE & MODE DÉGRADÉ (Timeouts, Idempotence, Concurrence)
  Scénario: Ré-étalement dynamique en cas de variance de scoring effondrée
    Étant donné une liste de 10 passages ayant tous un score de pertinence identique de 0.50
    Quand le régularisateur de variance détecte une variance nulle inférieure à 0.05
    Alors une transformation de contraste à température basse est appliquée
    Et la variance résultante est restaurée au-dessus du seuil plancher

  # UX, OBSERVABILITÉ & EMPTY STATE (Spinners, Retours Écran, Logs)
  Scénario: Alerte visuelle en cas d'abstention forcée
    Étant donné une exigence rejetée en mode Reject
    Quand le rapport d'audit est généré
    Alors un avertissement clair indique à l'utilisateur de mener une session Grill-Me pour clarifier le point manquant
```
