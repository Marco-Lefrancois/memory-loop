# ADR-0365 : Harmonisation Symbiotique des Compétences, Standard Agent-Skills et Checklists Partagées

- **Statut** : Approuvé (Constitutionnel)
- **Date** : 2026-09-13
- **Auteurs** : Équipe mLoop Swarm & Co-Architecte Agentique
- **Périmètre** : Catalogue de compétences (`.agents/skills/`), Checklists normatives (`.agents/references/`), Archives (`memory/archive-skills/`), Métrologie (`src/pipelines/skill_doctor.py`), Ingestion Web (`src/pipelines/crawler.py`), Étalonnage (`src/pipelines/calibrate.py`)

---

## 1. Contexte & Problématique

L'audit d'hygiène contextuelle et de métrologie des compétences (ADR-0362, `python src/swarm.py doctor --skills`) a révélé des vulnérabilités architecturales majeures au sein du catalogue `.agents/skills/` de Memory Loop :
1. **Saturation de l'Empreinte de Démarrage & Context Rot** : Le catalogue cumulait 35 compétences totalisant ~39 464 jetons, générant un risque critique de saturation de la fenêtre d'attention et d'amnésie précoce du modèle.
2. **Compétences Obèses et Manque de Déport** : 6 compétences clés excédaient 2 000 jetons chacune (`plan`: 4280 tok, `grill`: 3672 tok, `sentinel`: 2604 tok, `herdr-orchestration`: 2557 tok, `teach`: 2224 tok, `impeccable`: 2018 tok) en raison de l'imbrication de gabarits volumineux dans les fichiers `SKILL.md`.
3. **Sur-Spécification Théorique & Doublons Fonctionnels** : La présence de 6 compétences de réflexion abstraite (`thinking-*`) et de compétences d'assistance floues (`teach`, `office`, `research`, `analyze`, `sop`) diluait le routage des agents sans valeur probante sur le cycle de livraison.
4. **Carence d'Excellence Aval d'Ingénierie Logicielle** : Alors que mLoop excelle dans la gouvernance amont (Phases 1 à 3 : Ingestion, Analyse, Spécification INVEST, Grounding), il manquait d'un cadre d'ingénierie logicielle rigoureux (TDD avec Beyoncé Rule, vérification du doute in-flight, contraintes de performance, garde-fous de sécurité OWASP, tests runtime avec DevTools) pour guider le handoff d'implémentation.

L'étude comparative approfondie du standard *Agent Skills* d'Addy Osmani a mis en lumière la complémentarité symbiotique parfaite entre l'Amont souverain mLoop et l'Aval d'ingénierie d'Agent Skills.

---

## 2. Décisions d'Architecture

```
                                  ┌────────────────────────────────────────────────────────┐
                                  │          ADR-0365 : HARMONISATION SYMBIOTIQUE          │
                                  └───────────────────────────┬────────────────────────────┘
                                                              │
                    ┌─────────────────────────────────────────┼─────────────────────────────────────────┐
                    │                                         │                                         │
                    ▼                                         ▼                                         ▼
    ┌───────────────────────────────┐         ┌───────────────────────────────┐         ┌───────────────────────────────┐
    │  1. ANATOMIE DE COMPÉTENCE 2.0│         │  2. RATIONALISATION & ARCHIVE │         │  3. SOUTIEN PIPELINE & CACHE  │
    │ • Frontmatter 'Use when...'   │         │ • 14 compétences archivées    │         │ • Revalidation HTTP 304       │
    │ • Table Anti-Rationalisation  │         │   (memory/archive-skills/)    │         │ • Linter collision cosinus    │
    │ • Red Flags & Preuves Sortie  │         │ • 15 skills d'ingénierie Addy │         │ • Contrôle trigger syntaxe    │
    │ • 4 Core mLoop condensés      │         │ • 12 checklists partagées     │         │ • Seuil boot < 15k jetons     │
    └───────────────────────────────┘         └───────────────────────────────┘         └───────────────────────────────┘
```

### 2.1 Standard Normatif « Skill Anatomy 2.0 »
Toute compétence active dans `.agents/skills/` doit obligatoirement respecter l'anatomie septuple suivante :
1. **Frontmatter YAML Normalisé** : Propriété `name` univoque, `description` concise (< 1024 caractères) contenant impérativement une clause explicite de déclenchement formulée selon la syntaxe :  
   `"Use when <circonstance précise>, when <déclencheur alternatif>, or when <besoin>."`
2. **Aperçu & Rôle Souverain** : Mission fonctionnelle définie en 2 phrases sans fioritures.
3. **Déclencheurs & Exclusions Explicites** : Section binaire *Quand l'utiliser* / *Quand NE PAS l'utiliser*.
4. **Déroulé Opérationnel Structuré** : Étapes numérotées, algorithmes de décision ou diagrammes compacts.
5. **Table Anti-Rationalisation (Inviolable)** : Tableau à 2 colonnes confrontant les excuses de paresse du LLM aux règles strictes et rebuttals factuels.
6. **Signaux d'Alerte (Red Flags)** : Liste des comportements interdits trahissant une dérive ou un raccourci.
7. **Vérification de Sortie avec Preuves** : Checklist finale obligatoire conditionnant le statut Done.

### 2.2 Rationalisation du Catalogue et Archivage dans `memory/archive-skills/`
- **14 Compétences Archivées** : Les compétences `tdd`, `thinking-cynefin`, `thinking-kepner-tregoe`, `thinking-reversibility`, `thinking-theory-of-constraints`, `thinking-triz`, `thinking-via-negativa`, `teach`, `office`, `analyze`, `research`, `research-and-develop`, `validate` et `sop` sont retirées du catalogue actif et sanctuarisées sous [`memory/archive-skills/`](../../memory/archive-skills/) avec leur table de correspondance.
- **Adoption des 15 Compétences d'Ingénierie d'Addy Osmani** :  
  `test-driven-development`, `source-driven-development`, `doubt-driven-development`, `spec-driven-development`, `constraint-driven-development`, `planning-and-task-breakdown`, `incremental-implementation`, `context-engineering`, `code-simplification`, `security-and-hardening`, `performance-optimization`, `shipping-and-launch`, `api-and-interface-design`, `browser-testing-with-devtools`, `debugging-and-error-recovery`.
- **Condensation Chirurgicale des Compétences Maîtresses mLoop** :
  - `grill` condensé de 3 672 à ~600 tokens (externalisation des gabarits vers `standards/blueprints/dossier_de_preuves_template.md` et intégration de la mécanique *interview-me* : hypothèse, confidence %, question 1:1 avec guess).
  - `plan` condensé de 4 280 à ~700 tokens (recentrage sur le slicing INVEST vertical et délégation du graphe de tâches à `planning-and-task-breakdown`).
  - `sentinel` condensé de 2 604 à ~650 tokens (cycle de doute en 5 étapes et 4 axes d'attaque non-négociables).
  - `herdr-orchestration` condensé de 2 557 à ~550 tokens (matrice des 4 critères de fork, gouvernance et teardown gate anti-zombies).

### 2.3 Bibliothèque de Checklists Partagées (`.agents/references/`)
Création du sous-système partagé [`.agents/references/`](../../.agents/references/) accessible par référence relative (`../../references/`) par l'ensemble des compétences et contenant 12 checklists exhaustives :
- **7 Checklists d'Ingénierie Addy** : `definition-of-done.md`, `security-checklist.md`, `performance-checklist.md`, `accessibility-checklist.md`, `observability-checklist.md`, `orchestration-patterns.md`, `testing-patterns.md`.
- **5 Checklists Souveraines mLoop** :
  1. `invest-story-checklist.md` : Validation des 4 Piliers Gherkin, matrice CTA et contrats API Profil B.
  2. `fact-search-grounding-checklist.md` : Ancrage Passage-Level Grounding, requêtes FTS5, OCR Chromium et journalisation de vol.
  3. `adr-decision-checklist.md` : Filtrage strict des décisions de Type 1 (portes à sens unique).
  4. `herdr-worker-checklist.md` : Matrice de fork, prompt par fichier scratch et politique anti-zombies.
  5. `sync-and-release-checklist.md` : Synchronisation tripartite Git / Jira / FTS5 et seuils de rollback.

### 2.4 Améliorations du Pipeline Python `src/`
1. **Revalidation Conditionnelle HTTP 304 dans `src/pipelines/crawler.py`** :  
   Pour satisfaire au protocole `source-driven-development` sans gaspiller de bande passante ni de quota réseau, le crawler mLoop mémorise les en-têtes `ETag` et `Last-Modified` dans le cache Markdown (`memory/crawler/cache/`), et injecte `If-None-Match` et `If-Modified-Since` lors des requêtes ultérieures. En cas de réponse HTTP 304, le fichier de cache existant est réutilisé instantanément sans re-téléchargement.
2. **Métrologie SkillDoctor & Détection de Collisions (`src/pipelines/skill_doctor.py`)** :  
   - Vérification de la présence de la clause syntaxique `"Use when..."` dans chaque frontmatter.
   - Calcul de similarité cosinus lexicale (TF-IDF simplifié) entre les descriptions de compétences : toute paire de compétences affichant une similarité > 75% est signalée comme collision potentielle de routage.
   - Distinction formelle entre l'empreinte de démarrage (descriptions boot < 15 000 jetons) et le volume à la demande.
3. **Contrôle d'Étalonnage (`src/pipelines/calibrate.py`)** :  
   L'étape [3/8] valide l'exhaustivité de l'index du routeur et vérifie la conformité syntaxique des descriptions.

---

## 3. Conséquences & Bénéfices

### 3.1 Gains Mesurés
- **Réduction Drastique du Context Rot** : Le poids des descriptions de démarrage est stabilisé à ~2 300 jetons, soit seulement **15.3% du plafond constitutionnel des 15 000 jetons**.
- **Éradication des Doublons** : 14 compétences obsolètes ou redondantes écartées de la fenêtre d'attention.
- **Excellence d'Ingénierie Immédiate** : Capacité d'exécuter des cycles TDD stricts, des revues contradictoires, des audits OWASP et des tests navigateur avec outillage DevTools.
- **Compatibilité Universelle Handoff** : Découpage de tâches compatible avec OpenSpec sans imposer aucune dépendance Node.js physique dans mLoop.

### 3.2 Engagements Opérationnels
- Aucune compétence ne peut être fusionnée dans `.agents/skills/` sans clause `"Use when..."` valide et table anti-rationalisation.
- Toute décision de Type 1 doit être validée via `adr-decision-checklist.md` et consignée dans `standards/adr-system/`.
