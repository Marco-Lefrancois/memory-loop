---
id: 0319
validation_rules: []
---

# ADR-0319 : Universal Dev Handoff, Contrats Déclaratifs & Règle No-Code (Amont mLoop ➔ Aval Dev & Agents IA)
## Statut : Accepté (Série 03xx - Gouvernance & Handoff Universel Agnostique)
## Autorité : [ADR-0000](0000-agentic-coworker-framework.md), [ADR-0100](0100-structure-repertoire-projet-client.md), [ADR-0301](0301-standard-gherkin-outlines-4-piliers.md)

---

## 1. Contexte & Problématique (Principe d'Agnosticisme d'Outillage)

Memory Loop (mLoop) opère en amont comme **Machine à états cognitive, d'analyse fonctionnelle et d'architecture d'affaires**. 

En aval, la phase de réalisation physique du code peut être prise en charge par une variété infinie d'acteurs et d'environnements :
- Des **agents IA de développement** pilotés par des frameworks variés (ex: OpenSpec, Cursor Agents, Claude Code, GitHub Copilot Workspace, Devin, Cline, Aider).
- Des **développeurs humains** (Tech Leads, Développeurs Senior/Junior).
- Des pipelines CI/CD ou des générateurs de tests d'acceptation.

**Problématique identifiée :**
Lorsque des récits mLoop injectent du pseudo-code syntaxique prématuré (ex: `SDK_Loaded == true`, `TMPSDK.sharedInstance.setupUI(...)`), du code d'implémentation présumé ou tentent d'imposer une syntaxe de bas niveau :
1. **Pollution de Contexte Universelle** : Tout agent IA de dev ou développeur humain en aval subit une surcharge cognitive et un risque élevé d'hallucination ou de conflit avec l'architecture réelle du codebase.
2. **Couplage Toxique à l'Outillage** : mLoop ne doit **JAMAIS** dépendre d'un outil aval particulier ni supposer comment le développeur ou son agent organise son découpage technique interne.
3. **Spec-Drift** : Le mélange entre exigences métier et propositions de code fragilise la maintenabilité du backlog.

---

## 2. Décision

Nous officialisons les **4 Lois du Handoff Universel et de la Rédaction Déclarative (Dev-Ready & Agent-Ready)** :

### 1. Protocole Universal Dev Handoff (Agnosticisme Total de l'Aval)
- **Rôle Exclusif de mLoop (Amont)** : Fournisseur universel de la **Source de Vérité Fonctionnelle (SSOT)**. Produire des récits autonomes, universellement compréhensibles par tout humain ou agent IA, sans couplage à un outil tiers.
- **Souveraineté de l'Aval (Dev / Agent)** : Le choix des patterns d'implémentation (MVVM, Clean Architecture, DI), des outils de découpage de tâches (ex: OpenSpec, Jira Subtasks, Markdown checklists) et de la génération du code physique appartient exclusivement à l'équipe de dev aval.

### 2. Règle "No-Code" & Zéro Pseudo-Code Syntaxique
- **Interdiction Formelle de Snippets de Code** : Aucun bloc de code source d'implémentation (C#, Swift, Kotlin, TypeScript, etc.) ni pseudo-code syntaxique (ex: `(SDK_Loaded == true)`) ne doit figurer dans les récits (`backlog/stories/`).
- **Description en Français Naturel** : Les préconditions, parcours d'usage, états système et règles de gestion doivent être rédigés en français technique pur, rigoureux et naturel.

### 3. Principe "Doc-First" pour SDKs & Composants Tiers
- **Priorité Documentation Officielle** : Pour toute intégration de SDK (ex: OneTrust, Firebase, Stripe) ou librairie tierce, l'agent a l'interdiction de suggérer du code d'intégration.
- **Référencement Documentaire** : L'agent doit obligatoirement pointer vers la documentation technique officielle ingérée (`docs/00-ingested/...`) ou les références officielles.

### 4. Contrats Déclaratifs (Interfaces, Services & Endpoints)
- Dans les sections techniques des récits (`## Contrats UI & API Backend`), l'agent liste de façon **purement déclarative** les concepts cibles : noms de méthodes, services, interfaces ou schémas JSON d'API (ex: méthode `ShowPreferenceCenterUI()`, service de gestion du consentement), sans prescrire la syntaxe d'instanciation.

---

## 3. Conséquences

- **Interopérabilité Maximale (Agent-Ready & Human-Ready)** : Les récits deviennent la matière première idéale pour n'importe quel développeur ou agent IA du marché (OpenSpec, Cursor, Copilot, etc.) sans modification requise.
- **Zéro Dépendance Outil** : mLoop conserve une architecture universelle, pérenne et indépendante des modes ou évolutions des outils de dev aval.
- **Respect Strict de la Séparation des Responsabilités (SoC)** : Frontière limpide entre le *Quoi* (l'intention métier, mLoop) et le *Comment* (l'implémentation logicielle, l'équipe de dev).
- **Validation Déterministe Continue** : Les linters `RubberDuckEngine` et `WikiFix` contrôlent automatiquement l'absence de code parasite et la pureté déclarative du backlog.
