---
id: 0326
validation_rules: []
---

# ADR-0326 : Fact-Search Obligatoire, Preuves Visibles en 4 Couches & Revue Sémantique de Contenu

- **Statut** : ACCEPTÉ / SSOT NORMATIF
- **Date** : 21 août 2026
- **Décideurs** : Équipe mLoop, Architecture & Gouvernance Agentique
- **Domaine** : Rigueur Épistémique, Grounding, Anti-Hallucination, Sentinel Substantive Review, Traçabilité Machine

---

## Contexte & Problème

Dans le développement assisté par IA, les architectures classiques reposent souvent sur des linters de forme superficiels (comptage de mots-clés, vérification de regex) ou sur du RAG passif non-vérifiable. Ces approches présentent deux faiblesses critiques :
1. **Hallucinations de citations** : Des agents prétendent citer des sources qui n'existent pas sur le disque ou inventent des paramètres d'APIs.
2. **Revues mécaniques sans valeur ajoutée** : Des revues de récits réduites à de simples scores ("INVEST 95/100") sans challenger la véritable substance métier des scénarios Gherkin.

Il est impératif d'institutionnaliser un protocole de **Fact-Search déterministe avec preuves visibles** et de transformer la revue de récits en une **revue sémantique de contenu qualitative**.

---

## Décision Retenue

1. **Fact-Search Obligatoire & Règle « Search-Before-Ask »** :
   - Interdiction formelle de poser une question au PO ou de rédiger un récit sans avoir préalablement interrogé la base documentaire (`docs/00-ingested/`, `docs/02-business-rules/`, `loop_mem_search`).
   - Toute question posée au PO doit être sourcée et justifiée par l'absence avérée d'information dans les documents clients.

2. **Système de Preuves Fact-Search Découplé (4 Couches SSOT)** :
   - *Couche 1a (Console CLI)* : Feedback temps réel `[FACT-SEARCH]` à l'écran lors des recherches FTS5.
   - *Couche 1b (Restitution Visuelle Interactive Grill-with-Docs)* : Production systématique du **Dossier de Preuves Documentaires** lors des sessions d'interrogatoire unitaire (Passage-Level Grounding) :
     1. Maquettes SSOT & Notes d'atelier avec liens cliquables `file:///...`.
     2. Extraits verbatim sourcés avec numéros de ligne précis et faits établis déduits (`Extrait N — Titre (Lignes X-Y) : « Citation » ➔ Fait établi : ...`).
     3. Modèle de données et DBML des entités manipulées.
   - *Couche 2 (EvidencePack JSON Sidecar)* : Fichier `memory/evidence/<STORY_ID>_evidence.json` avec bloc `fact_search_proofs`, empreintes SHA-256 et diptyque épistémique.
   - *Couche 3 (Journal d'Audit Persistant)* : Fichier append-only `memory/fact_search_log.jsonl`.
   - *Règle Zero-Bruit User Story* : Aucune injection de notes IA dans le Markdown ; le récit se termine strictement après `## Scénarios de test`.

3. **Revue Sémantique de Contenu Métier (*Substantive Review*)** :
   - Séparation stricte entre le linter de forme (géré silencieusement par WikiFix) et la revue de fond (gérée par Sentinel / `rubber-duck`).
   - La revue délivre un rapport qualitatif d'analyse critique en 4 axes :
     1. *Cohérence Métier & Clarté Fonctionnelle*
     2. *Analyse Critique des Scénarios Gherkin (4 Piliers)*
     3. *Confrontation Fact-Search aux Sources Réelles*
     4. *Recommandations Constructives d'Amélioration*

4. **Linter Déterministe WikiFix (`[GUARDRAIL FACT-SEARCH]`)** :
   - Contrôle logiciel physique vérifiant sur disque (`Path.exists()`) que 100% des fichiers et règles cités dans les récits ou l'EvidencePack existent réellement.

---

## Conséquences

### Positives
* **Zéro Question Triviale au PO** : Réduction drastique des interruptions et professionnalisme accru.
* **Zéro Contestation Client** : Traçabilité irréfutable de chaque exigence à sa source contractuelle.
* **Éradication des Citations Fantômes** : Contrôle physique déterministe sur disque.
* **Haute Valeur Ajoutée de la Revue** : Les développeurs et POs reçoivent des retours intelligents sur les cas limites et l'UX plutôt que des scores de regex.

### Négatives / Contraintes
* **Discipline d'Ingestion** : Les documents de référence doivent obligatoirement être ingérés sous `docs/00-ingested/` pour être indexés.
