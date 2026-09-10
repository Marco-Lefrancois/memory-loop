# 🏛️ Spécification d'Architecture : Système de Preuves & Passage-Level Grounding

> **Référence** : ADR-0326 / Universal Dev Handoff ADR-0319  
> **Domaine** : Assurance Qualité Sémantique, Traçabilité Documentaire & Anti-Hallucination

---

## 1. Contexte & Problématique

Dans les cycles de spécification assistés par IA, deux modes de défaillance majeurs sont régulièrement observés :
1. **Hallucination Non Groundée** : L'IA formule des questions ou des récits fondés sur des extrapolations logiques mais contraires aux sources documentaires réelles du client.
2. **Pollution Textuelle du Récit** : Pour prouver sa rigueur, l'IA injecte des extraits de compte-rendu de réunions, des noms d'intervenants ou des traces d'ateliers directement dans la User Story, créant du bruit pour les développeurs.

---

## 2. Architecture en 4 Couches Découplées

Le système sépare strictement la découverte, la présentation, l'archivage et le livrable final :

```mermaid
flowchart TD
    subgraph C1["Couche 1 : Découverte & Restitution"]
        C1A["Couche 1a : Fact-Search Engine (FTS5 SQLite)<br/>Indexation plein-texte et extraction à granularité de passage"]
        C1B["Couche 1b : Dossier de Preuves Documentaires<br/>Restitution visuelle structurée lors de l'interview active"]
    end

    subgraph C2["Couche 2 : Sidecar EvidencePack JSON"]
        C2A["memory/evidence/<STORY_ID>_evidence.json<br/>- fact_search_proofs (Citations verbatim, Lignes X-Y)<br/>- Empreintes SHA-256 des fichiers sources<br/>- Audit épistémique (Périmètre prouvé vs non-prouvé)"]
    end

    subgraph C3["Couche 3 : Journalisation Persistante"]
        C3A["memory/fact_search_log.jsonl<br/>Journal append-only immuable de chaque requête de recherche"]
    end

    subgraph C4["Couche 4 : Livrable Fonctionnel Pur"]
        C4A["backlog/stories/<JIRA_KEY>.md<br/>Récit 100% no-code, Gherkin 4 piliers, zéro citation de réunion"]
    end

    C1A --> C1B
    C1B --> C2A
    C1B --> C3A
    C2A --> C4A
```

---

## 3. Contrats d'Intégrité (Invariants de Production)

1. **Search-Before-Ask** : Aucune question ne doit être posée à l'humain si la réponse est présente dans la base documentaire.
2. **Visual Grounding** : Chaque question d'arbitrage doit être accompagnée de son dossier de preuves sourcé.
3. **Zero-Noise Markdown** : Le récit Markdown final s'arrête strictement après la section `## Scénarios de test`. Zéro injection de trace d'atelier dans le `.md`.
4. **Deterministic EvidencePack** : L'EvidencePack JSON sidecar est validé contre `schemas/evidence_pack.schema.json`.
