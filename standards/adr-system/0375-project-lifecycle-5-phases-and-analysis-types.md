# ADR-0375 : Réalignement du Cycle de Vie en 5 Phases, Typologie d'Analyses & Règle des 2 Gabarits

* **Statut** : ACCEPTÉ (Amende formellement ADR-0339)
* **Date** : 18 septembre 2026
* **Décideurs** : Architecte en Chef, Équipe Core mLoop, Product Owner
* **Domaine** : Cycle de vie universel, typologie des analyses, dualité Grill-Me, consolidation des gabarits de récits

---

## 🚀 1. Contexte & Problématique

L'ADR-0339 avait introduit un cycle en 6 étapes en formalisant `Phase 0 : T-SHIRT-SIZE` et `Phase 1 : SOW` comme étapes séquentielles bloquantes. L'usage en production a mis en évidence trois défauts conceptuels majeurs :

1. **Dépendance Circulaire et Illogisme d'Amorçage** :
   Un chiffrage macro T-Shirt Size ou un SOW ne peuvent pas exister dans le vide. Ils requièrent obligatoirement l'initialisation du projet (`init`) et l'ingestion structurée de la matière première (`ingest`). Or, dans ADR-0339, ces actions vivaient artificiellement dans la Phase 0.
2. **Confusion entre Phase de Cycle de Vie et Type d'Analyse / Livrable** :
   Un T-Shirt Size et un SOW ne sont pas des phases universelles de développement logiciel, mais des **livrables d'analyse d'avant-projet**. Pour un projet démarrant avec un SOW déjà signé et des spécifications arrêtées, forcer le passage par ces deux étapes créait une friction artificielle et des blocages inutiles (*phase-skip false positives*).
3. **Prolifération des Gabarits et Absence de Distinction de Maturité** :
   L'absence de formalisation de la maturation d'une story a entraîné la coexistence chaotique de plusieurs templates (`story_template.md`, `story_template_PRO_ANALYSIS.md`, `project_tracer_bullet_story_template.md`), sans distinguer une **ébauche de cadrage** issue d'un découpage macro d'un **récit haute fidélité** issu d'un Grill-Me 1:1.

---

## 💡 2. Décisions d'Architecture

### A. Cycle de Vie Unifié en 5 Phases d'Ingénierie Universelles
Le cycle officiel de tout projet mLoop est désormais structuré en 5 phases universelles :
1. **`1. INGEST & EXPLORE`** : Socle technique universel (`init` + `ingest`). Ingestion de l'ensemble des sources brutes.
2. **`2. PLAN & ANALYSE`** : Dualité inséparable de la planification macro et de la micro-analyse fine.
3. **`3. BUILD & DEV`** : Développement physique, tests unitaires et exécution des workers Herdr.
4. **`4. VALIDATE & QA`** : Assurance qualité sémantique, Fact-Check NLI, Sentinel et Evals.
5. **`5. SHIP & SYNC`** : Synchronisation Jira Cloud Fail-Closed, release Git et clôture.

### B. Reclassification de T-Shirt Size & SOW comme Types d'Analyses Optionnels
- Le dimensionnement macro (T-Shirt Size) et le contrat (SOW) deviennent des **modes d'analyse** et des **livrables optionnels** de la Phase 2 (sous-étape Planification Macro).
- **Parcours Fast-Track** : Tout projet disposant déjà de son SOW et de ses spécifications peut débuter directement l'analyse fine des récits en Phase 2 sans avertissement.

### C. Trinité Documentaire Étanche
- `docs/01-architecture/TSHIRT_SIZE_<PROJET>.md` : Analyse macro et grille budgétaire Kevin Chamberland (1 000 $/j), exclusions explicites.
- `docs/01-architecture/SOW_<PROJET>.md` : Engagement contractuel, RACI, jalons et conformité Loi 25.
- `backlog/sprint_backlog.md` : Tableau de bord agile vivant dédié exclusivement au suivi opérationnel des sprints (zéro colonne macro d'avant-projet).

### D. Dualité du Protocole Grill-Me (Macro vs Micro)
- **Grill-Me Macro (`python src/swarm.py grill-project`)** : Cadrage global transverse post-ingestion pour éliminer les zones d'ombre d'architecture (SSO, Loi 25, exclusions nettes) et alimenter `TSHIRT_SIZE.md` et `SOW.md`.
- **Grill-Me Micro (`python src/swarm.py grill-me --story <ID>`)** : Entrevue contradictoire 1:1 chirurgicale sur un récit spécifique pour résoudre ses ambiguïtés d'interface, contrats d'API et edge cases.

### E. Règle des 2 Seuls Gabarits de Récits & Cycle de Maturation
L'écosystème élimine tous les gabarits redondants et ne conserve que **2 templates officiels** :
1. **Palier 1 : `standards/blueprints/story_draft_template.md`** : Ébauche de cadrage issue de l'avant-projet (`status: DRAFT`, `grill_me: PENDING`, `invest_score: 0/6`).
2. **Palier 2 : `standards/blueprints/story_template.md`** : Spécification haute-fidélité issue du Grill-Me 1:1 (`status: READY_FOR_DEV`, `grill_me: DONE`, DoR 6/6, 4 Piliers Gherkin).

---

## ⚖️ 3. Conséquences

### Positives
* **Clarté conceptuelle absolue** : Ingestion préalable obligatoire, élimination des dépendances circulaires.
* **Flexibilité opérationnelle** : Support natif des projets d'avant-projet comme des mandats déjà contractualisés (Fast-Track).
* **Zéro pollution du Backlog** : `sprint_backlog.md` redevient un tableau agile propre et focalisé sur l'exécution.
* **Réduction de la charge cognitive** : 2 gabarits de stories au lieu de 4, fin des questions répétitives grâce au Grill-Me Macro.

### Négatives & Mitigations
* **Mise à niveau requise de la machine à états** : `src/core/lifecycle.py` et `vibe_check.py` doivent être mis à jour, avec migration transparente des anciens états.
