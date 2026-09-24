# ADR-0390 : Indexation Fact-Search Multi-Niveaux (`docs/<domaine>/<couche>/`) & Contrat `doc_path` Racine Projet

* **Statut** : ACCEPTÉ *(implémenté le 24 septembre 2026 — PLAN-ADR-0390 approuvé puis exécuté : 34 tests verts, migration Metro_SANTE effectuée, convergence sync prouvée)*
* **Date** : 24 septembre 2026
* **Décideurs** : Équipe Architecture mLoop, Agent Orchestrateur, Product Owner
* **Dépendances / Références** : [ADR-0102](0102-structure-ssot-dossier-docs.md) (Structure SSOT `docs/`), [ADR-0369](0369-standard-robustesse-python-senior.md) (Standards Python Senior), [ADR-0370](0370-cli-pipeline-ssot-generator-and-anti-drift-governance.md) (Anti-Drift CLI), [ADR-0376](0376-standard-rigueur-zero-blindspot-ecosysteme-mloop.md) (Audit 360° 7 Couches), [ADR-0385](0385-protocole-falsification-frontieres-architecture-immunite-cognitive.md) (Échelle de Preuve)

---

## 🚀 1. Contexte & Problématique

Constat établi le **24 septembre 2026** lors de la session d'alignement SANTÉ sur FOOD (rapport `Projects/Metro_SANTE/docs/OneTrust/04-transverse/AUDIT_ALIGNEMENT_SANTE_SUR_FOOD_2026-09-24.md` §9.3), validé par appel d'épreuve (Niveau 2 — lecture de l'AST source + état réel de la base) :

1. **Découverte bornée à un niveau (D1)** :
   L'indexeur canonique `FactSearchIndexer.index_project_docs` (`src/engine/fact_search/indexer.py`) construit ses chemins d'exploration comme `docs_dir / folder_name` pour 7 couches fixes (`00-ingested`, `01-architecture`, `02-business-rules`, `03-models`, `04-transverse`, `05-assets`, `06-knowledge`) — c'est-à-dire **uniquement les enfants directs** de `docs/`. Or Metro SANTE (et potentiellement tout projet multi-domaine) organise ses couches sous un niveau intermédiaire : `docs/OneTrust/00-ingested/…`.
   *Conséquence matérielle* : l'intégralité de l'arbre `docs/OneTrust/**` (410 fichiers, dont le livrable d'alignement) était **invisible pour `fact-search`** — seuls `docs/index.md` (gob racine) et `reference/**` (parcours dédié) étaient indexés pour le projet.

2. **Convention de `doc_path` non contractuelle (D2)** :
   Le `rel_path` inséré est calculé via `md_file.relative_to(docs_dir.parent)`. Cette formule n'est correcte **que si `docs_dir` est canoniquement `Projects/<projet>/docs`**. L'indexation manuelle de contournement (stopgap) exécutée avec `docs_dir = docs/OneTrust` a produit des `doc_path` de forme `OneTrust/00-ingested/…` **dépourvus du préfixe `docs/`**. Or le handler CLI `src/commands/handlers/fact_search.py` (L74-95) résout chaque `doc_path` contre `Projects/<projet>/` pour générer les liens `file:///…#Lx-Ly` : les 3 tentatives de résolution échouent et la source s'affiche **sans lien cliquable** (dégradation silencieuse, pas d'erreur).

3. **Le stopgap est un pis-aller, pas une solution** :
   L'indexation isolée (cache dédié `memory/.fact_search_hashes_Metro_SANTE.json`) a rendu le livrable searchable (preuves FTS : `MATCH 'ApplicationInsights'` → 4 hits), mais elle n'est **pas rejouable par `sync`** (l'indexeur canonique ne voit toujours pas l'arbre niché), laisse des `doc_path` hors contrat, et repose sur un second cache divergent.

---

## 💡 2. Décisions d'Architecture

### A. Découverte à Deux Foyers, Profondeur Bornée (Flat + Niché)

* Conserver le parcours plat existant : `docs_dir/<couche>/**` (récursif, inchangeur des projets conformes ADR-0102 à couches directes).
* **Ajouter un second foyer** : `docs_dir/<domaine>/<couche>` pour les 7 couches, où `<domaine>` parcourt **uniquement les enfants directs de `docs_dir`** — i.e. `docs_dir.glob(f"*/{couche}")`.
* **Borne stricte** : profondeur maximale de découverte = **2 niveaux sous `docs/`** (domaine + couche). Aucun `rglob` depuis la racine, aucune récursion non bornée — conformité à l'esprit ADR-0369 (pas d'exploration non bornée) et coût prévisible : 7 cibles × N domaines directs.
* **Non-chevauchement garanti** : le foyer plat couvre `docs/<couche>/**`, le foyer niché ne matche que `docs/<domaine>/<couche>` (profondeur exacte 2) — un même fichier n'est jamais atteint deux fois.

### B. Contrat `doc_path` = Chemin Relatif Racine Projet (`Projects/<projet>/`)

* **Invariante contractuelle** : tout `doc_path` inséré est relatif à la racine du projet → commence par `docs/`, `reference/` ou `standards/`. C'est la seule forme que le handler CLI sait résoudre en lien `file:///`.
* **Mécanisme** : le paramètre `docs_dir` reste **canoniquement `Projects/<projet>/docs`** pour tous les appelsants (`sync`, `index_project_docs_to_fts5`, wrappers) ; la découverte nichée est **interne** à `index_project_docs` (elle ne doit jamais être pilotée en passant un `docs_dir` niche — c'est exactement la faute du stopgap).
* **Contrat testé** : un test paramétré exige que chaque `doc_path` issu d'un walk synthétique résolve physiquement sous la racine projet (Failure Contract ADR-0369 §5).

### C. Migration Obligatoire du Stopgap vers la Convention

* **Purge/normalisation** des chunks orphelins `OneTrust/%` (410 fichiers / 5 283 chunks) vers la forme canonique `docs/OneTrust/%` — soit par `UPDATE docs_chunks SET doc_path = 'docs/' || doc_path WHERE project_name=? AND doc_path LIKE 'OneTrust/%'` (recommandé : chirurgical, préserve chunking et `docs_chunks_fts` via le trigger/`INSERT OR REPLACE` ré-aligné), soit par réindexation forcée complète (alternative plus lourde).
* **Suppression du cache divergent** `memory/.fact_search_hashes_Metro_SANTE.json` après migration : le cache partagé `Projects/<projet>/memory/.fact_search_hashes.json` redevient l'unique source d'incrémentation.
* La méthode définitive et son test de non-régression sont arbitrés dans le plan d'implémentation (OQ-01).

### D. Garde-Fous de Mise en Œuvre (ADR-0376 / ADR-0369 / ADR-0370)

* **Aucune écriture dans `src/` sans approbation humaine bloquante** du Plan Zéro Blindspot détaillant chaque fichier `[NEW] / [MODIFY] / [DELETE]`.
* Écoute des standards Python Senior ADR-0369 (context managers, `timeout` explicite, logs structurés — l'indexeur est déjà conforme, le patch doit le rester).
* **Aucune entrée ajoutée à `src/commands/_registry.py`** → pas de `guide --sync` requis (parité CLI préservée).
* Après modification code : `graphify update .` (règle graphify) + suites de tests 100 % vertes (couche 7 : les 8 fichiers `tests/test_fact_*` et `test_nli_polarity.py` référençant `index_project_docs`).

---

## 📈 3. Conséquences & Bénéfices

* **Findabilité SSOT totale** : les projets à structure nichée (`docs/<domaine>/<couche>/`) deviennent intégralement interrogeables par `fact-search` — condition de la règle « Fact-Search & Traçabilité des Preuves » de la constitution agentique.
* **Contrat de liens restauré** : tous les résultats CLI retrouvent leur lien `file:///` cliquable vers la ligne source (fin de la dégradation silencieuse observée sur le stopgap).
* **Un seul mécanisme, un seul cache** : suppression de la dérive à deux caches ; `sync` redevient suffisant (fin du rituel d'indexation manuelle).
* **Régression verrouillée** : le foyer plat plat existant reste couvert par les tests actuels ; les nouveaux tests bornent la découverte nichée et le contrat `doc_path`.
* **Coûts & frontières assumés** : un niveau de domaine supplémentaire seulement (au-delà de `docs/<d1>/<d2>/<couche>/`, non découvert — documenté comme limite volontaire) ; migration manuelle unique des chunks stopgap ; l'ADR ne s'applique qu'à l'indexation documentaire, pas au graphe Graphify ni au LOD (déjà multi-niveaux).
