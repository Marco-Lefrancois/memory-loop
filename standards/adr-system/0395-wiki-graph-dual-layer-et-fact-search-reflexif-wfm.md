# ADR-0395 : Wiki Graph Dual-Layer, Fact-Search Réflexif Biaisé & Mode Reject Souverain (Intégration Cognitive WFM)

* **Statut** : ACCEPTÉ *(validé par Macro-Grill PO le 25 septembre 2026 — épopée EPIC-34)*
* **Date** : 25 septembre 2026
* **Décideurs** : Product Owner (Marco), Lead Architect mLoop, Agent Orchestrateur
* **Dépendances / Références** : [ADR-0202](0202-modularite-interne-agents.md) (Modularité ≤ 300L), [ADR-0375](0375-standard-preuve-epistemique-et-tracabilite-radicale.md) (Traçabilité Radicale), [ADR-0376](0376-standard-rigueur-zero-blindspot-ecosysteme-mloop.md) (Rigueur 360° Zéro Blindspot), [ADR-0389](0389-grill-v2-frontier-rounds-ungrillable-handoff-context-budget.md) (Frontier Rounds & Ungrillable Context), [ADR-0390](0390-fact-search-indexation-arbres-niches-docs-domaine-couche.md) (Fact-Search Niche Trees), [ADR-0393](0393-decouplage-modalite-grill-scope-anti-cascade.md) (Découplage Format vs Scope & Arrêt Formel Post-Grill), [ADR-0394](0394-tracabilite-bidirectionnelle-code-exigences-preuves-programmation-ast.md) (EvidencePack 2.0).
* **Référence Scientifique** : *WFM: Wiki Foundation Model for Complex Agentic Reasoning* (arXiv:2609.18182, Septembre 2026).

---

## 🚀 1. Contexte & Problématique

Dans son rôle de Cerveau et Backend d'État Déterministe du cycle de vie logiciel, **Memory Loop (mLoop)** assure la persistance contextuelle anti-amnésique à travers ses 5 phases canoniques.

L'étude scientifique de pointe **WFM** (*arXiv:2609.18182*) démontre que les deux approches conventionnelles de récupération documentaire souffrent d'angles morts critiques pour les systèmes multi-agents :
1. **Le RAG classique vectoriel par chunks** : Aveugle aux connexions relationnelles, il fragmente la connaissance et détruit le contexte macroscopique.
2. **Le GraphRAG par triplets discrets** : Trop épars, il sacrifie la substance textuelle continue et élimine la nuance contextuelle, rendant les chemins de déduction ambigus.
3. **L'Aplatissement Uniforme d'Attention (*Uniform Attention Collapse*)** : Sur des graphes denses, les algorithmes de reranking ont tendance à tasser leurs scores vers une moyenne indécise ($1/|N|$), causant un verrou d'attention où tout semble moyennement pertinent.

Pour surmonter ces faiblesses, WFM formalise la représentation **LLM-Wiki dual-layer** $\mathcal{W} = (\mathcal{E}_w, \mathcal{R}_w, \mathcal{D})$ unissant la topologie d'entités discrètes aux passages textuels denses par des hyper-arêtes transversales, couplée à une boucle de recherche réflexive avec arrêt adaptatif et mode Reject sans hallucination.

---

## 💡 2. Décisions d'Architecture

### A. Persistance Native Unifiée SQLite du Wiki Graph Dual-Layer
* **Module** : `src/state/wiki_graph_db.py`.
* **Choix d'Architecture (Arbitrage PO Q1)** : Intégration directe et native dans `memory/loop_mem.db` aux côtés de l'index FTS5 existant (zéro dépendance externe, atomicité SQLite WAL locale).
* **Schéma Relationnel** :
  * `wiki_entities` : entités canoniques de premier ordre (`ADR`, `RULE`, `STORY`, `AST_SYMBOL`, `CONCEPT`), identifiants normalisés, SHA-256.
  * `wiki_relations` : relations structurelles typées entre entités (`implements`, `verifies`, `governs`, `depends_on`, `calls`).
  * `wiki_passages` : unités documentaires sémantiques continues découpées selon la structure Markdown (titres `#`, `##`, `###`).
  * `wiki_cross_links` : hyper-arêtes transversales liant chaque entité à ses contextes textuels (`defines`, `mentions`, `justifies`).

### B. Indexation Hiérarchique Markdown sans Perte de Contexte
* **Module** : `src/pipelines/llm_wiki_indexer.py`.
* **Découpage Sémantique** : Remplacement du chunking naïf par un sectioning respectant strictement l'arbre des titres Markdown sous `docs/00-ingested/` et `docs/`.
* **Hyper-Arêtes Automatiques** : Découverte lexicale et résolution AST reliant automatiquement les symboles et règles métier à leurs sections d'origine.

### C. Recherche Réflexive Bornée à Arrêt Anticipé Adaptatif
* **Module** : `src/pipelines/reflective_search.py`.
* **Doctrine Budgétaire (Arbitrage PO Q2)** : Budget d'exploration borné à **$B = 3$ passes maximum**.
* **Arrêt Adaptatif Immédiat** : À chaque itération $t$, l'agent évalue la complétude du panier de preuves cumulées $\mathcal{C}^{(t)}$. Dès que chaque exigence dispose d'un ancrage textuel probant, l'agent émet le drapeau $f^{(t)} = \text{Final}$ et s'arrête (gain empirique mesuré de ~37% d'appels).

### D. Mode Reject Souverain & Barrière de Variance Anti-Collapse
* **Module** : `src/pipelines/fact_reject_auditor.py`.
* **Abstention Bloquante (Arbitrage PO Q2)** : En Phase 2 (Plan & Analyse) et Phase 4 (QA), le mode **Reject** est formellement bloquant. L'agent a l'interdiction d'extrapoler sur sa mémoire paramétrique. En l'absence de citation textuelle probante, la validation DoR/Gate 2 est refusée avec le code `REJECT_INSUFFICIENT_EVIDENCE`.
* **Régularisation de Variance** : La variance de dispersion des scores de contexte sélectionnés doit respecter le plancher $\text{Var}(w) \ge \epsilon = 0.05$. En deçà, un ré-étalement non linéaire de contraste est appliqué pour prévenir l'effondrement d'attention.

### E. Sonde Vibe-Check Check 30 & Commande CLI `wiki-search`
* **Commande CLI** : `python src/swarm.py wiki-search --query "<q>" [--project <p>] [--reject-mode]`.
* **Garde-Fou Pré-Vol** : Le **Check 30 (Intégrité du Wiki Graph & Fact-Search Réflexif)** est intégré à la suite de vol `vibe-check` pour bloquer toute promotion si la table `wiki_cross_links` est corrompue ou si le ratio d'entités orphelines dépasse 10%.

---

## 🛡️ 3. Impact sur les Récits de l'Épopée EPIC-34

| Récit ID | Composant | Décision Clé Associée |
| :--- | :--- | :--- |
| **`MLOOP-340-BE`** | `Core/Memory` | Schéma relationnel `wiki_entities`, `wiki_passages`, `wiki_cross_links` dans `loop_mem.db`. |
| **`MLOOP-341-BE`** | `Pipelines/Ingest` | Sectioning Markdown hiérarchique et création des hyper-arêtes transversales. |
| **`MLOOP-342-BE`** | `Search/Reflection` | Boucle de recherche itérative $B \le 3$ avec arrêt adaptatif $f^{(t)} = \text{Final}$. |
| **`MLOOP-343-BE`** | `QA/Grounding` | Mode Reject bloquant anti-hallucination et plancher de variance $\epsilon = 0.05$. |
| **`MLOOP-344-FULL`**| `CLI/VibeCheck` | Commande CLI `mloop wiki-search`, intégration Grill-Me et Check 30 Vibe-Check. |

---

## ⚖️ 4. Conséquences

### Positives
* **Mémoire Anti-Amnésique Robuste** : Unification du lexique, des ADRs, du code AST et des documents denses dans une structure unique interrogeable.
* **Économie Cognitive & Frugalité** : Réduction de plus d'un tiers des requêtes documentaires grâce à l'arrêt adaptatif dès preuve acquise.
* **Zéro Hallucination en Cadrage** : Refus mécanique d'inventer des règles métier grâce au mode Reject strict.
* **Traçabilité 360°** : Chaque exigence est formellement reliée à son paragraphe source.

### Négatives / Contraintes
* **Exigence de Rigueur lors de l'Ingestion** : Les documents sources doivent adopter une structure de titres Markdown claire pour un découpage optimal.
* **Plafond Modulaire** : Chaque nouveau module (`wiki_graph_db.py`, `reflective_search.py`, etc.) doit respecter la limite stricte de 300 lignes (`RULE-AST-01`).
