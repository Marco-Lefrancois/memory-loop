# ADR-0317 : Integration des Patterns PDF-Brain (Enrichissement IA Post-Ingest & Taxonomie SKOS)

* **Statut** : Proposé
* **Décideurs** : Équipe Architecture mLoop, Agent Orchestrateur
* **Date** : 13 août 2026

---

## 🚀 Contexte & Problématique

L'analyse R&D du projet **pdf-brain** (`joelhooks/pdf-brain`) a mis en évidence trois innovations majeures pour la gestion des bases de connaissances locales (PDF & Markdown) :
1. **Passe d'Enrichissement IA Structuré (`--enrich`)** : Extraction automatique des métadonnées (titre propre, résumé en 2-3 phrases, type de document, tags, concepts) combinée à un fallback déterministe par heuristique de chemin/nom de fichier.
2. **Taxonomie Hiérarchique SKOS (Simple Knowledge Organization System)** : Arborescence de concepts (`broader`/`narrower`) avec suggestions de nouveaux concepts par l'IA et gouvernance de validation (`accept`/`reject`).
3. **Contrat d'Output Agent-First (`nextActions`)** : Enveloppes JSON standardisées avec suggestion des actions suivantes recommandées pour l'agent LLM.

Dans mLoop, les documents ingérés sous `docs/00-ingested/` sont convertis bruts via MarkItDown mais manquent de métadonnées sémantiques normalisées pour le RAG et le graphe de dépendances Graphify.

---

## 💡 Décisions d'Architecture

1. **Module d'Enrichissement Post-Ingest dans `src/pipelines/ingest.py`** :
   - Après la conversion Markdown/Office via MarkItDown, injection automatique d'un en-tête Frontmatter YAML structuré dans les documents `docs/00-ingested/*.md` :
     ```yaml
     ---
     title: "Titre Métier Propre"
     summary: "Résumé en 2-3 phrases synthétisant le document."
     document_type: "api_reference | architecture_doc | spec | guide"
     tags: ["onetrust", "maui", "consent"]
     concepts: ["cmp/onetrust/webview", "analytics/firebase"]
     ---
     ```
   - Fallback par heuristique en cas d'absence/échec du modèle LLM d'enrichissement.

2. **Taxonomie Métier mLoop (`docs/05-knowledge/taxonomy.json`)** :
   - Mise en place d'un registre SKOS standardisé pour classifier les domaines applicatifs (`FOOD`, `COMMERCE`, `SANTÉ`) et les composants techniques (`CMP`, `Analytics`, `Push`, `SSO`).

3. **Inclusion de `nextActions` dans les EvidencePacks JSON** :
   - Enrichissement du moteur `EvidencePackEngine` (`src/pipelines/evidence_pack.py`) avec un champ `next_actions: ["python src/swarm.py grill...", "python src/swarm.py sync..."]` pour guider le pilote de pipeline mLoop.

---

## 📈 Conséquences & 6 Piliers d'Impact

* **Qualité RAG & Graphify** : Indexation sémantique nettement plus précise grâce au Frontmatter enrichi.
* **Statut Stateless & Local-First** : Zéro dépendance cloud externe obligatoire, compatible Ollama / Heuristique locale.
* **Gouvernance mLoop** : Alignement strict avec la Loi des 3 Piliers et la taxonomie unifiée.
