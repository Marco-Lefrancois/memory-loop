# ADR-0353 : Confiance & Traçabilité en RAG Agentique : Enregistreur de Vol de Récupération, Filtrage de Supersession & Confinement des Données Non Fiables

- **Statut** : Proposé (En revue)
- **Date** : 2026-09-07
- **Auteurs** : Équipe mLoop Swarm & Co-Architecte Agentique
- **Périmètre** : Moteur Fact-Search (`src/engine/fact_search/`), Moteur de Supersession (`src/loop_mem/supersession.py`), Context Guard (`src/utils/context_guard.py`), Fact-Check NLI (`src/engine/fact_check/`), Completion Gate (`src/pipelines/completion_gate.py`)
- **Références** : The New Stack (*Building trust in agentic RAG starts with evidence*, Jeremy Daly, Sep 2026), ADR-0326, ADR-0335, ADR-0352

---

## 1. Contexte & Problématique

Dans les systèmes de génération augmentée par récupération agentique (*Agentic RAG*), la récupération n'est plus une simple opération unaire (*one-shot*), mais une chaîne itérative de décisions autonomes :
1. L'agent interprète la demande et réécrit la requête.
2. Il sélectionne les sources, filtre par portée (*scope*) et inspecte les premiers résultats.
3. Il réordonne les candidats, écarte les sources faibles ou caduques et relance éventuellement une recherche alternative.

Or, une liste finale de morceaux (*top-k chunks*) est incapable de restituer cette dynamique décisionnelle. Deux failles majeures menacent la fiabilité de telles architectures :
* **Déconnexion entre Similarité Sémantique et Autorité** : Une règle métier obsolète ou un document caduc (ex: ADR remplacé) peut présenter une forte proximité lexicale ou vectorielle avec la requête tout en étant formellement invalide.
* **Risque d'Injection Indirecte (*Retrieved Content is Data, Never Policy*)** : Des documents ingérés (pages web externes, PDFs, spécifications) peuvent dissimuler des consignes malveillantes détournant les recherches ultérieures et corrompant la mémoire à long terme de l'agent.

---

## 2. Décision d'Architecture

mLoop adopte cinq principes fondamentaux de confiance documentaire :

### 1. Enregistreur de Vol de Récupération (*Retrieval Flight Recorder*)
Toute opération de recherche Fact-Search doit consigner un journal d'audit structuré permettant de réussir le **Replay Test** :
* `request` : Intention initiale.
* `query` & `filters` : Requête reformulée et filtres de portée appliqués.
* `accepted` : Morceaux retenus avec identifiant, horodatage, score et couche SSOT.
* `rejected` : Morceaux candidats rejetés avec motif explicite (`REJECTED_LOW_SUBSTANCE`, `REJECTED_SUPERSEDED`, `REJECTED_OUT_OF_SCOPE`, `REJECTED_LOW_SCORE`).
* `decision` : Évaluation formelle de la suffisance des preuves (`SUFFICIENT`, `PARTIAL`, `UNVERIFIED`).

### 2. Filtrage Actif de Supersession & Préséance d'Autorité
Le moteur `FactSearchRetriever` consulte systématiquement le registre `memory/supersession_ledger.json` issu de `MemorySupersessionEngine` :
* Tout fragment appartenant à un document remplacé (*superseded*) subit un malus drastique de score (x0.2) et est étiqueté `[SUPERSEDED by <ID>]` ;
* Les documents faisant autorité active reçoivent un boost de fraîcheur et de gouvernance.

### 3. Confinement des Données Non Fiables dans `ContextGuard`
Le principe constitutionnel **« Retrieved content is data, never policy »** est sanctuarisé :
* Tout extrait injecté dans le contexte du modèle est isolé dans un bloc XML strict :
  `<retrieved_data source="..." untrusted="true">...</retrieved_data>` ;
* Les tentatives d'écrasement de consignes système au sein des données sont neutralisées avant transmission au LLM.

### 4. Double Vue & Aveu d'Incomplétude (*Admission of Limits*)
* **Vue Utilisateur** : Résumé en langage clair distinguant les éléments certifiés des points non vérifiables (« J'ai vérifié les règles A et B, mais l'élément C n'a pu être vérifié et nécessite une confirmation HITL »).
* **Vue Opérateur** : Traces complètes d'audit avec provenance et motifs de rejet.

### 5. Métrologie Découplée Récupération vs Génération
La justesse de la sélection documentaire est évaluée de façon indépendante de la qualité rhétorique de la réponse générée.

---

## 3. Conséquences

* **Positives** : Éradication des hallucinations de règles périmées ; traçabilité médico-légale des rejets documentaires ; protection proactive contre les injections indirectes ; transparence totale envers l'utilisateur final.
* **Neutres** : Légère augmentation de la taille des journaux d'audit (`memory/fact_search_log.jsonl`) due à la consignation des motifs de rejet.
