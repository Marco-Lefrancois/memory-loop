# 🌀 Memory Loop — Cognitive Pure State-Graph Multi-Agent Engine (mLoop)

Bienvenue dans l'espace de travail de **Memory Loop (mLoop)**. Cet écosystème implémente une architecture **Kernel-Pipeline** modulaire, orchestrée par un swarm d'agents cognitifs Système 2 et Système 1.

---

## 🧭 Architecture & Piliers Fondateurs

mLoop structure le cycle de vie de développement piloté par les spécifications à travers 6 phases souveraines :

1. **Phase 0 — Inception & SOW** : T-Shirt sizing, estimation d'effort et scoping initial.
2. **Phase 1 — Spec & Ingestion** : Ingestion documentaire MarkItDown, analyse sémantique et extraction de modèles.
3. **Phase 2 — Plan & Architecture** : Découpage vertical de récits (INVEST), arbitrage contradictoire *Grill-with-Docs* et formalisation d'ADRs.
4. **Phase 3 — Build & Stories** : Rédaction des récits verticaux selon le Gold Standard (Gherkin 4 Piliers, profilage API, EvidencePacks autonomes).
5. **Phase 4 — Validate & QA** : Contrôles pré-vol Vibe-Check (9 contrôles déterministes), Sentinel / Rubber-Duck contradictoire, et audit WikiFix.
6. **Phase 5 — Ship & Sync** : Synchronisation tripartite (Dépôt Git, Jira Cloud, Index Graphify/SQLite FTS5).

---

## 🧰 Boîte à Outils & Standards

Les outils et scripts utilitaires transverses mis à disposition des humains et des agents IA sont centralisés et indexés sous :

* 🧰 **[Catalogue de la Boîte à Outils (`tools/README.md`)](tools/README.md)** : Index central de nos utilitaires d'ingénierie (Archify, drawDB, Office, Jira, Git Hooks).
* 💳 **[Suivi du Budget IA LiteLLM (`tools/budget/README.md`)](tools/budget/README.md)** : Diagnostic et solde en temps réel de votre clé de calcul Nmédia Cloud.
* 🏛️ **[Système de Décisions d'Architecture (`standards/adr-system/README.md`)](standards/adr-system/README.md)** : Catalogue des 58 décisions d'architecture souveraines mLoop.
* 📖 **[Guide Exhaustif du Pipeline CLI (`standards/protocols/CLI_PIPELINE_GUIDE.md`)](standards/protocols/CLI_PIPELINE_GUIDE.md)** : Matrice complète des 58 commandes CLI regroupées par phase.

---

## 🚀 Démarrer le Moteur `src/swarm.py`

Le moteur `src/swarm.py` pilote le cycle mLoop via des pipelines modulaires.

```bash
# 1. Boot Sequence Obligatoire (Anti-amnésie, Vibe-Check, Focus)
python src/swarm.py resume --project <nom-du-projet>
python src/swarm.py vibe-check --project <nom-du-projet>
python src/swarm.py focus --project <nom-du-projet> --story <chemin_ou_id>

# 2. Ingestion & construction initiale du graphe (System 1 Graphify)
python src/swarm.py ingest --project <nom-du-projet>

# 3. Entrevue interactive Drill / Grill (Alignement fonctionnel & DDD)
python src/swarm.py drill --project <nom-du-projet>

# 4. Synchronisation globale (WikiFix sémantique + mise à jour du graphe Graphify)
python src/swarm.py sync --project <nom-du-projet>

# 5. Exécuter un audit sémantique WikiFix indépendant
python src/swarm.py wikifix --project <nom-du-projet>

# 6. Synchroniser le backlog de stories vers Jira Cloud
python src/swarm.py jira_sync --project <nom-du-projet>

# 7. Optimisation Rétrospective du Harnais (Génération de règles RHO)
python src/swarm.py optimize --project <nom-du-projet> --keyword "mot-cle" --msg "explication" --scope <project|global>
```
