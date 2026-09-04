---
name: grill
description: Interrogatoire interactif Grill-with-Docs & Frontier Design Tree, arbitrage Faits vs Décisions, création d'ADRs, modélisation de domaine inline (CONTEXT.md), support multi-domaines et gouvernance de stories.
---

# 🛠️ Skill : Session Interactive Grill-with-Docs & Frontier Design Tree (`/grill`)

Ce skill régit la discipline d'interrogatoire sans concession (*Relentless Interview*) et de modélisation de domaine en continu (*Domain Modeling*) entre l'agent mLoop et l'utilisateur pour aligner le langage et la vision d'architecture **AVANT** toute phase de build (ADR-0320).

---

## 🎯 1. Principes Fondamentaux de Grilling (AI Hero / Matt Pocock Pattern)

### A. Le Design Tree & La Frontière Active (Frontier Rounds)
- **Arbre de Conception (*Design Tree*)** : Chaque projet ou fonctionnalité se modélise comme un arbre de décisions interdépendantes.
- **La Frontière (*Frontier*)** : L'ensemble des décisions dont les prérequis sont déjà résolus. Ce sont les questions que l'agent peut poser *immédiatement* sans extrapoler de réponses non fournies.
- **Rounds Structurés** : L'agent pose l'ensemble des questions de la frontière active (ou en mode atomique 1 question par tour). Chaque question respecte scrupuleusement la nomenclature :

```markdown
❓ **Q1** - **<Titre de la Question>** : <Corps, contexte, alternatives A/B/C et compromis>

➡️ **Recommandation mLoop** : <Option recommandée motivée techniquement>
```

- **Dynamique de Frontière** : Chaque réponse de l'utilisateur résout un nœud, étend la frontière et débloque les sous-questions descendantes. L'agent recalcule la frontière pour le round suivant.
- **Condition de Fin** : La session se termine lorsque la frontière est vide (arbre entièrement exploré, aucune hypothèse implicite résiduelle) et validée par l'utilisateur.

### B. Étape 0 : Déconstruction Critique Pré-Grill & Roast à Froid (First-Principles Truth Alignment)
- **Interdiction de Polissage Docile** : L'agent ne doit **jamais** accepter passivement un brouillon de story existant ni se contenter de formater du texte préexistant.
- **Roast à Froid Obligatoire** : Avant de poser la première question du Grill, l'agent délivre une **opinion franche, non complaisante et déconstruite** comprenant :
  1. *Les faiblesses & hallucinations identifiées* (ex: faux endpoints API, en-têtes HTTP synthétiques, sur-ingénieries inutiles, dérives du gabarit).
  2. *La confrontation aux faits vérifiés* (ce que disent réellement les SDKs, le code source physique et les documents officiels).
  3. *La véritable responsabilité fonctionnelle épurée* (définition de la valeur métier sans fioritures).
- **Anti-Complaisance (*Anti-Sycophancy*)** : L'agent est mandaté pour agir comme un auditeur impitoyable de la vérité technique et métier, et non comme un générateur approbateur.

### C. Étape 0-bis : Fact-Search Préalable Obligatoire & Dossier de Preuves Documentaires (ADR-0326)
- **Faits (Look it up)** : Trouver les faits est la responsabilité exclusive de l'agent (inspection filesystem, base FTS5 SQLite, `docs/00-ingested/`, subagents). L'agent a l'interdiction formelle d'interroger l'humain sur des faits qu'il peut découvrir lui-même.
- **Affichage des Preuves à l'Écran** : Lors de chaque recherche préalable, l'agent affiche sur la console :
  ```text
  (i) [FACT-SEARCH] 🔍 Requête FTS5 : '<sujet>' ➔ <N> fait(s) vérifié(s) dans <fichier>
  ```
- **Mode Dual-Pane Herdr (Split Fact-Search SSOT — ADR-0345 & ADR-0346)** :
  - **Dans l'environnement Herdr** : L'agent consigne le Dossier de Preuves complet dans `memory/evidence/<STORY_ID>_fact_dossier.md` (nom canonique unique — cf. `DOSSIER_DE_PREUVES_PROTOCOL.md` §4) ou ouvre le volet split latéral droit (`herdr plugin pane open --plugin org.mloop.orchestrator --entrypoint evidence`). Dans le terminal principal de conversation (`p1`), l'agent n'affiche que la synthèse concise des faits et l'unique question d'arbitrage ciblée.
  - **Hors de Herdr (Dégradation Gracieuse / Mode Inline Classique)** : Si l'agent tourne dans un terminal standard (PowerShell, terminal VS Code, Cursor, CI/CD sans multiplexeur), il bascule automatiquement en mode **Inline complet** : l'intégralité du Dossier de Preuves Documentaires (Maquette, Extraits verbatim sourcés, Structure DBML) et la Question d'arbitrage sont affichées directement dans le corps de la réponse textuelle, garantissant zéro perte d'information.

- **Standard Visuel du Dossier de Preuves Documentaires (Passage-Level Grounding)** :

  Avant de poser une question d'arbitrage au PO, l'agent a l'obligation formelle de structurer son intervention selon le **Gabarit Standard du Dossier de Preuves** :

```markdown
# 🐣 Session *Grill with Docs* — `<STORY_ID>` (<Titre Fonctionnel Pur>)

---

### 📂 Dossier de Preuves Documentaires (Sources Physiques & Extraits)

#### 1. 🖼️ Maquettes & Notes d'Atelier (SSOT Visuelle)
* **Maquette Principale** : [`docs/05-assets/.../<fichier>.svg`](file:///chemin/vers/fichier.svg)
* **Note d'ajustement UI (Grooming / Cadrage)** : [`reference/.../<image>.jpg`](file:///chemin/vers/image.jpg)
  > 📌 **Ajustement validé** : <Description précise de l'ajustement validé>.

---

#### 2. 🎙️ Extraits de la Transcription d'Atelier / Spécifications
Source : [`docs/00-ingested/.../<doc>.md`](file:///chemin/vers/doc.md)

> **Extrait 1 — <Titre de la Règle> (Lignes X–Y) :**  
> *« <Citation mot-à-mot du texte source> »*  
> ➔ **Fait établi** : <Traduction fonctionnelle concise de la règle métier>.

> **Extrait 2 — <Titre de la Règle> (Lignes X–Y) :**  
> *« <Citation mot-à-mot du texte source> »*  
> ➔ **Fait établi** : <Traduction fonctionnelle concise de la règle métier>.

---

#### 3. 🗄️ Structure de Données (Wiki Azure DevOps & DBML)
* **Sources** : [`docs/00-ingested/.../<spec>.md`](file:///chemin/vers/spec.md)
* **Entités & Champs Clés** :
  ```json
  {
    "id": "UUID",
    "champMetier": "Type (Description)"
  }
  ```

---

### 🎯 Contrat Déclaratif Cible (Profil B / Matrice CTA)
* **Route / Action** : `METHOD /api/...` ou `Composant UI ➔ Action`
* **Comportement attendu** : <Résumé du contrat fonctionnel>.

---

### ❓ Question d'Arbitrage #N pour `<STORY_ID>` (Règle d'Or de l'Interview)

<Contexte précis de l'arbitrage adossé aux faits vérifiés ci-dessus>.

* **Option A (Recommandée — <Motivation Technique>)** : <Description claire de l'option recommandée>.
* **Option B** : <Description de l'alternative>.
* **Option C** : <Description de l'alternative>.

👉 **<Question fermée d'arbitrage / validation> ?**
```

- **Décisions (Ask the PO)** : Les arbitrages métier, de priorités (`RM-XXX`) et de compromis appartiennent au PO. Chaque question posée au PO est obligatoirement adossée à ce dossier de preuves documentaires.
- **Journalisation Persistante** : Toute requête Fact-Search est consignée dans `memory/fact_search_log.jsonl`.


### D. Modélisation de Domaine Inline (`CONTEXT.md`)
- **Langage Ubiquitaire (*Ubiquitous Language*)** : Élimine le jargon flou ou surchargé. Dès qu'un terme canonique se stabilise, il est consigné immédiatement dans `CONTEXT.md` (ou le glossaire SSOT du projet).
- **Zéro détail d'implémentation** : `CONTEXT.md` contient uniquement le vocabulaire métier pur, pas de code ni de spécifications d'implémentation.

### D. Création d'ADRs avec Parsimonie & Réversibilité (ADR-0320 & ADR-0336)
Un ADR n'est proposé et rédigé que si la décision remplit **les 3 filtres réunis** et relève du **Type 1** (`thinking-reversibility`) :
1. **Type 1 / Difficile à inverser** (*Hard to reverse / One-way door*) — Le coût d'un changement futur est majeur (schéma DB, contrat d'API public, frontière de sécurité). Les décisions de *Type 2* (réversibles rapidement) sont actées localement sans bureaucratie d'ADR.
2. **Surprenante sans contexte** (*Surprising without context*) — Un futur développeur se demanderait *"pourquoi cela a-t-il été fait ainsi ?"*.
3. **Résultat d'un vrai arbitrage** (*Real trade-off*) — Il existait de véritables alternatives et un choix explicite a été fait.

---

## 🔍 2. Double-Focus Grilling & Audit Visuel par Zone UX (Stories Logicielles)

Lors de l'analyse d'un composant ou d'une User Story logicielle, l'agent audite impérativement les dimensions suivantes :
- **Focus 1 (Fonctionnel & Vertical)** : Traduction 1:1 de chaque vue/composant UI vers les endpoints API Backend et les modèles de données.
- **Focus 2 (5 Vecteurs de Résilience Technique)** :
  1. *Mode dégradé / Offline* (Comportement en cas de perte réseau).
  2. *Accès concurrents* (Conflits d'écriture et idempotence).
  3. *Données partielles / Nulls* (Affichage en l'absence de données).
  4. *Sécurité & Auth* (Permissions, sessions expirées, tokens).
  5. *Rate Limits & Volumétrie* (Pagination, throttling, montées en charge).
- **Focus 3 (Audit Visuel par Zone UX)** :
  1. *Header / Contexte* (Statuts, badges, métadonnées).
  2. *Body / Read Model* (Résumés, visualisations, listes).
  3. *Footer / Write Model* (Actions, triggers, modales de confirmation).
  4. *Matrice des 4 États* (Empty, Loading, Error, Success).

---

## 🌐 3. Grilling Multi-Domaines & Fallback Questionnaires

Le Grilling s'applique à tous les domaines d'ingénierie et de réflexion :
- **Archétype 1 : Cadrage Produit & Spécifications** (User Stories, architecture logicielle, refactoring).
- **Archétype 2 : Pédagogie & Formation** (Conception de cours, dépendances pédagogiques, interrogation contradictoire d'essais).
- **Archétype 3 : Gestion Stratégique & R&D** (Analyse de faisabilité, projets d'envergure, arbitrages budgétaires et techniques).
- **Archétype 4 : Fallback `to-questionnaire` (Dépendances Externes)** :
  - Si une question de la frontière dépend d'une partie prenante tierce (client, sécurité, infrastructure, partenaire), l'agent génère un artefact de **Questionnaire de Découverte Asynchrone** (`to-questionnaire-<sujet>.md`) ciblé sur l'écart d'information.

---

## 🔄 4. Protocole mLoop 1:1 par Story

1. **Grill Atomique Récit par Récit (Frontier Exhaustion Rule — ADR-0320 §F)** :
   - Interdiction du batching non maîtrisé. Le grilling traite un récit ou un module à la fois.
   - Dès que la frontière d'un récit est vide (plus de question de fact-search ou d'arbitrage PO en attente pour ce récit précis), l'agent **arrête immédiatement d'interroger** sur ce récit et **finalise sa rédaction** sans délai.
   - L'agent **avance automatiquement** au récit suivant de la liste dès la finalisation actée — sans attendre d'avoir traité l'ensemble du lot pour clôturer individuellement chaque récit.
   - La validation mécanique finale (`rubber-duck`, EvidencePack, statut `READY_FOR_DEV`) peut être différée/batchée via Worker Herdr, ou traitée ponctuellement à la demande explicite du PO (sortie ciblée du Mode Plan), suivie d'un retour automatique au Grill du récit suivant.
   - **Signal de Confiance Non-Fiable (ADR-0320 §G)** : Le champ `confidence_score` des EvidencePacks ne doit jamais servir de critère d'arrêt tant qu'il reste basé sur un simple contrôle d'existence de fichier (`verification_method: file_existence_only`). Seul le jugement de l'agent (fact-search réel, en priorisant le code source physique quand il est disponible) et la confirmation explicite du PO ferment la frontière d'un récit.
2. **Questions Ouvertes (`OQ-XXX`)** : Toute décision suspendue génère une question ouverte dans `docs/04-transverse/00-questions-ouvertes.md`.
3. **Règle ADR-Sync** : Si le grilling modifie une structure de répertoire ou une règle ADR (série 01xx), l'agent met à jour `standards/adr-contracts.json` et valide via `python src/swarm.py calibrate`.
4. **Blindage 4 Piliers Gherkin** : À la fin du grilling d'une story, l'agent garantit les 4 scénarios Gherkin (Nominal, Exceptions RM-XXX, Résilience offline, UX/Observabilité).
5. **Porte de Confirmation** : Récapituler la compréhension partagée et obtenir l'accord formel de l'utilisateur.

---

## 🛠️ 5. Commandes CLI à Invoquer

```powershell
# Enregistrer un ADR issu de la session Grill
python src/swarm.py grill --project <nom_projet> --title "Titre de l'ADR" --context "Contexte & Problématique" --decision "Décision retenue" --positives "Positifs" --negatives "Risques"

# Enregistrer un ADR ET marquer une story comme grilled (READY_FOR_GROOMING)
python src/swarm.py grill --project <nom_projet> --title "Validations" --story "US-001"

# Synchroniser la base de connaissances et le graphe de dépendances
python src/swarm.py sync --project <nom_projet>
```
