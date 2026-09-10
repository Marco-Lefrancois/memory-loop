# ADR-0320 : Grill-Me, Frontier Design Tree & Alignement Métier

* **Statut** : ACCEPTÉ
* **Date** : 15 août 2026
* **Décideurs** : Équipe Architecture mLoop, Agent Orchestrateur, Product Owner

---

## 🚀 1. Contexte & Problématique

L'interrogatoire contradictoire et l'alignement préalable constituent le cœur de la méthodologie mLoop. L'analyse R&D des travaux de **Matt Pocock (AI Hero)** autour de `/grill-me`, `/grill-with-docs` et du dépôt de référence (200k+ étoiles GitHub) met en lumière des principes fondamentaux d'ingénierie logicielle et de design de systèmes :

1. **The Design Concept (Frederick P. Brooks Jr., *The Design of Design*, 2010)** :
   La conception n'est pas un document statique ou un livrable figé, mais une **compréhension fluide et partagée (*shared mental model*)** entre toutes les parties prenantes du projet. La clarté émerge de la conversation et de l'exploration méthodique de l'espace de décision.
2. **Le Contre-Courant de l'IA (Ralentir pour Réfléchir)** :
   Tandis que la tendance dominante de l'IA pousse à fournir des réponses instantanées et souvent superficielles, le Grilling adopte la posture inverse : **ralentir, interroger sans relâche, débusquer les hypothèses implicites** et structurer la pensée avant d'écrire le moindre code ou la moindre spécification.
3. **Le Schéma "Drill Me / Grill Me" (Satya Nadella)** :
   Structurer l'interrogatoire sous forme d'un **arbre de conception (*Design Tree*)** et en parcourir la **frontière active (*Frontier*)** permet d'éliminer toute ambiguïté sans surcharger l'utilisateur.
4. **Généralisation Multi-Domaines (Beyond Software Development)** :
   Le protocole d'interrogatoire ne se restreint pas aux User Stories techniques, mais s'applique avec un égal succès au cadrage stratégique, à l'ingénierie pédagogique, aux arbitrages de projets complexes et à la structuration de questionnaires de découverte (`to-questionnaire`).

---

## 💡 2. Décisions d'Architecture

### A. Formalisation du Design Tree & des Frontier Rounds
Le processus de grilling dans mLoop est formalisé selon un graphe orienté de décisions :
- **Design Tree** : Chaque décision racine engendre des sous-décisions et des contraintes dépendantes.
- **La Frontière (Frontier)** : Ensemble des questions dont les prérequis sont d'ores et déjà établis. Ce sont les questions que l'agent peut poser *immédiatement* sans deviner de réponses futures.
- **Rounds de Grilling** : L'agent pose les questions de la frontière actuelle par itérations structurées (ou en mode atomique 1 question par tour). Chaque question respecte scrupuleusement la nomenclature :
  ```markdown
  ❓ **Q[N]** - **<Titre de la Question>** : <Corps, contexte et alternatives>
  ➡️ <Recommandation motivée mLoop>
  ```
- **Clôture de la Session** : Une session de grilling est réputée achevée uniquement lorsque la frontière est vide (aucun choix laissé implicite) et que l'utilisateur confirme la compréhension partagée.

### B. Séparation Stricte : Faits (Agent) vs Décisions (PO)
- **Faits (Look it up)** : Trouver les faits relève de la responsabilité exclusive de l'agent (inspection filesystem, bases vectorielles, `docs/00-ingested/`, subagents). L'agent a l'interdiction formelle d'interroger l'humain sur des informations qu'il peut découvrir lui-même.
- **Décisions (Ask the PO)** : Les arbitrages de produit, de priorités et de compromis appartiennent au PO. L'agent propose une recommandation motivée (`➡️`), mais ne décide jamais unilatéralement.

### C. Modélisation de Domaine en Continu (`CONTEXT.md`)
- Dès qu'un terme canonique ou une frontière conceptuelle se stabilise au cours du grilling, l'agent met à jour immédiatement le glossaire du projet (`CONTEXT.md` ou `docs/03-models/`).
- **Zéro détail d'implémentation** : Le glossaire capture exclusivement le vocabulaire métier pur (langage ubiquitaire).

### D. Règle des 3 Filtres pour la Création d'ADR
Un ADR n'est formalisé que si la décision remplit simultanément les **3 critères** :
1. **Difficile à inverser (*Hard to reverse*)** — Coût de changement ultérieur élevé.
2. **Surprenante sans contexte (*Surprising without context*)** — Susceptible d'interroger un développeur futur.
3. **Résultat d'un vrai arbitrage (*Real trade-off*)** — Choix explicite parmi plusieurs alternatives viables.

### E. Extension Multi-Domaines & Passerelle Questionnaires (`to-questionnaire`)
- mLoop étend le scope du Grilling au-delà des US logicielles : cadrage d'initiatives, conception de formations/cours, analyse de faisabilité multi-projets.
- Lorsqu'une question de la frontière dépasse le périmètre de connaissance du PO (dépendance vis-à-vis d'un tiers, d'un client externe ou d'une équipe infrastructure), mLoop déclenche le protocole **`to-questionnaire`** pour générer un artefact de découverte asynchrone ciblé.

### F. Règle d'Épuisement de Frontière par Récit (Per-Story Frontier Exhaustion & Immediate Advance)

Lorsque le Grilling porte sur une **liste de plusieurs récits** (ex: refonte d'un backlog vertical), la frontière se calcule **individuellement pour chaque récit**, en plus de la frontière globale de session (§2.A) :

1. **Critère d'Arrêt Unitaire** : Dès que la frontière d'un récit donné est vide (aucune question de fact-search non résolue, aucun arbitrage PO en attente pour CE récit), l'agent **DOIT immédiatement arrêter d'interroger** sur ce récit — il est formellement interdit de poser des questions supplémentaires "par prudence" ou "pour approfondir" une fois la frontière close.
2. **Finalisation Immédiate, Sans Attendre le Lot** : L'agent finalise sur-le-champ le récit dont la frontière est épuisée (rédaction complète alignée sur les réponses obtenues, mise à jour du frontmatter, citations Jira-Only) — **sans attendre que les autres récits de la liste soient également grillés**. Le traitement séquentiel (US-00 → US-01 → US-02 → ...) n'implique pas un traitement synchrone groupé.
3. **Séparation Grill vs Validation Mécanique** : La clôture de la frontière (fin du dialogue) est distincte de la validation mécanique finale (`rubber-duck`, EvidencePack, transition `READY_FOR_DEV`). Ces dernières peuvent être :
   - **Batchées en fin de vague** via un Worker Herdr dédié (`worker-spawn` type=`validation`), conformément à la règle de délégation obligatoire (AGENTS.md §3) si le volume dépasse les seuils, **OU**
   - **Traitées ponctuellement** en sortant du Mode Plan pour ce récit unique, si le PO le demande explicitement (ex: préparation immédiate d'un copier/coller Jira) — l'agent revient alors automatiquement en Mode Plan pour reprendre le Grill du récit suivant de la liste, sans redemander confirmation de reprise.
4. **Avancement Automatique vers le Récit Suivant** : Une fois un récit finalisé (étape 2 ou 3 ci-dessus complétée), l'agent enchaîne directement sur le premier récit non traité de la liste sans marquer de pause d'attente, sauf si le PO interrompt explicitement la séquence.
5. **Non-Régression sur les Récits Déjà Clos** : Il est interdit de revenir questionner un récit dont la frontière a déjà été déclarée close, sauf si une nouvelle information contredit une décision actée précédemment (cf. skill `wait-what`).
6. **Fiabilité du Signal de Confiance (cf. Section G)** : Le critère d'arrêt de frontière repose sur le jugement de l'agent (fact-search réel + confirmation PO explicite), **jamais** sur le champ `confidence_score` des EvidencePacks JSON tant que celui-ci n'est pas corrigé pour refléter une vérification sémantique ou de code source réelle plutôt qu'un simple contrôle d'existence de fichier.

### G. Fiabilisation du Signal de Confiance des EvidencePacks & Intégration du Code Source Réel (Amendement 2026-08-26)

Suite à un audit de qualité du Fact-Checking mené le 26 août 2026, il est constaté que (a) le champ `confidence_score` généré par `EvidencePackEngine.extract_evidence()` était une constante codée en dur (`1.0`), ne reflétant aucune vérification sémantique, et (b) le Code Source AST — pourtant un niveau obligatoire de la Search Hierarchy (`FACT_SEARCH_PROTOCOL.md` §2, niveau 5) — n'était jamais réellement consulté par le pipeline. La présente section corrige ces deux défauts :

1. **Distinction Existence vs Véracité** : Chaque preuve EvidencePack porte un champ `verification_method` à 3 valeurs possibles : `"file_existence_only"` (fichier Markdown/doc cité, existence vérifiée seulement), `"code_source_verified"` (affirmation confirmée par inspection directe du code source physique — `.cs`, `.csproj`, `.plist`, `.xml` — via grep/AST), ou `"semantic_match"` (correspondance sémantique complète, réservée à une évolution future).
2. **Score Calculé, Non Codé en Dur** : Le score initial est `MEDIUM` (`0.75`) pour toute preuve de type `file_existence_only` ; `HIGH`/`1.0` reste possible mais uniquement pour une preuve `code_source_verified` (le code source physique étant la source de vérité la plus forte pour les faits techniques).
3. **Priorité au Code Source Quand Disponible** : Lorsqu'un récit cite un comportement technique (SDK, service, méthode), le pipeline doit — dans l'ordre — (a) tenter une requête `codegraph_explore` si un index `.codegraph/` existe pour le projet source concerné, (b) à défaut, effectuer une recherche directe (grep) dans les fichiers `reference/**/*.cs|.csproj|.plist|.xml` du projet source si celui-ci est accessible localement, (c) seulement en dernier recours, se limiter à la citation de documents Markdown (`file_existence_only`). Le champ `source_type` (`"code"` vs `"documentation"`) trace laquelle de ces 3 voies a été utilisée.
4. **Journalisation Systématique de la Couche 3** : Toute recherche Fact-Search (manuelle via outils agent, ou via `GrillEngine.perform_fact_search()`) doit être consignée dans `memory/fact_search_log.jsonl`, avec le champ `source_type`. La certitude affichée doit être graduée selon le nombre et le rang des résultats retournés, jamais fixée à `HIGH` par défaut dès qu'un résultat existe.
5. **Rétro-Alimentation des EvidencePacks Caducs** : Un EvidencePack dont le `timestamp` est antérieur à la dernière modification du récit associé doit être marqué `"status": "STALE_PENDING_REGENERATION"` plutôt que de conserver silencieusement `"VALIDATED"`.

### H. Restitution Inconditionnelle du Dossier de Faits Établis (Pre-Grill Fact Disclosure)

Afin d'éradiquer le syndrome de la "boîte noire épistémique" où l'agent fouille en coulisses sans donner de visibilité à l'humain :

1. **Découplage Faits vs Arbitrages** : La restitution des faits découverts (`look it up`) ne doit jamais être conditionnée à la présence de questions d'arbitrage (`ask the PO`).
2. **Restitution Systématique Pré-Rédaction** : Avant d'ouvrir une session de Grilling OU avant de commencer la rédaction d'un récit (si aucun arbitrage n'est requis), l'agent **DOIT impérativement présenter le Dossier de Preuves Documentaires & Faits Établis** complet :
   - Maquettes SSOT & Notes d'ajustement UI (avec liens `file:///...`).
   - Extraits verbatim sourcés avec numéros de lignes précis de transcription/specs et déduction des faits établis.
   - Modèle de données DBML et entités cibles.
3. **Deux Issues Formelles de Cadrage** :
   - *Cas A (Frontière active non vide)* : Le Dossier de Preuves introduit immédiatement l'unique Question d'Arbitrage ciblée (Round 1:1 avec recommandation mLoop).
   - *Cas B (Frontière vide / Faits 100% limpides)* : L'agent présente l'intégralité du Dossier de Preuves, conclut par un constat explicite de frontière vide (*« Tous les faits nécessaires sont vérifiés et documentés sans ambiguïté résiduelle. Aucun arbitrage requis »*), et attend la validation du socle factuel par l'humain avant d'enclencher la rédaction de la story.

---

## 📈 3. Conséquences & 6 Piliers d'Impact mLoop

| Pilier d'Impact | Effet & Gain Mesuré |
| :--- | :--- |
| **1. Clarté & Zéro-Ambigüité** | Élimination des hypothèses fantômes avant toute phase de spécification ou de développement. |
| **2. Alignement Cognitif (Brooks)** | Garantie d'un modèle mental synchronisé entre PO, Architecte mLoop et Développeurs aval. |
| **3. Respect du Budget d'Attention** | Les questions posées en rounds réduisent la fatigue décisionnelle et ciblent uniquement la frontière active. |
| **4. Traçabilité SSOT & ADRs** | Seules les décisions structurantes franchissent le filtre des 3 critères, évitant l'inflation documentaire. |
| **5. Résilience & Anticipation** | Audit systématique des 5 vecteurs de résilience (offline, concurrence, nulls, auth, volumétrie) pendant le grilling. |
| **6. Portabilité Multi-Clients** | Format universellement compatible avec Antigravity IDE, Claude Code, Codex et OpenSpec. |

---

*Décision d'architecture mLoop officialisée le 15 août 2026.*
*Amendement (Sections F & G) officialisé le 26 août 2026, suite à audit de session Grill-with-Docs sur le projet Metro_OneTrust (codebase COMMERCE).*
*Amendement (Section H : Restitution Inconditionnelle du Dossier de Faits) officialisé le 3 septembre 2026.*
