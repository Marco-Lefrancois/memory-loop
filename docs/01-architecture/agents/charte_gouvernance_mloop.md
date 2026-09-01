# 📜 Charte de Gouvernance & Directives Générale mLoop

**Statut** : Directive Générale Immuable  
**Système** : Framework Backend mLoop (v2.2.0)  
**Source de Vérité Structurée** : [`C:\Memory Loop\.agents\soul.json`](file:///c:/Memory%20Loop/.agents/soul.json)  
**Portée** : Tous les agents, rôles (Orchestrator, Plan, Build, Sentinel/Validate) et pipelines mLoop.

---

## 💎 1. Le Manifeste d'Excellence Architecturale (The Soul of mLoop)

1. **Zéro Raccourci (Ne jamais tourner les coins ronds)** : L'agent doit toujours effectuer une analyse complète, minutieuse et rigoureuse. Interdiction formelle de proposer des correctifs superficiels ou de sauter des étapes d'analyse.
2. **Interdiction des Documents Ad-Hoc Jetables** : Ne jamais créer de fichiers jetables ou de scripts ad-hoc à la volée. Tout document produit doit s'inscrire dans l'architecture officielle (`docs/` ou `backlog/`).
3. **Compréhension Globale de l'Écosystème** : Prendre systématiquement le temps d'analyser la codebase, le graphe de connaissances (Graphify) et la structure mLoop avant toute décision.
4. **Solutions Optimales, Paramétrées et Génériques** : Toujours privilégier des solutions réutilisables, paramétrables par projet via `opencode.json` et découplées des cas particuliers.

---

## 📁 2. Convention Universelle de Nomenclature des Fichiers

| Type d'Artefact | Chemin & Convention de Nomenclature | Exemple Concret |
| :--- | :--- | :--- |
| **User Stories Backlog** | `backlog/stories/<CODEBASE>/US-<ID>.md` | `backlog/stories/COMMERCE/US-00.md` |
| **Documents d'Architecture** | `docs/01-architecture/ADR-<XXX>_<nom_snake_case>.md` | `docs/01-architecture/ADR-005_gouvernance_backlog.md` |
| **Registres d'Entités OKF** | `docs/01-architecture/OKF_REGISTRE_ENTITES.md` | `docs/01-architecture/OKF_REGISTRE_ENTITES.md` |
| **Backlog Dynamique SSOT** | `backlog/sprint_backlog.md` | `backlog/sprint_backlog.md` |
| **Cartographie Wayfinder** | `backlog/wayfinder_map.md` | `backlog/wayfinder_map.md` |

---

## 🏛️ 3. Séquence Immuable du Gabarit Unique Universel (`story_template.md`)

Toute User Story générée ou révisée dans le backlog (`backlog/stories/`) doit utiliser le **Gabarit Unique et Universel [`standards/blueprints/story_template.md`](file:///c:/Memory%20Loop/standards/blueprints/story_template.md)** et respecter **strictement et sans déviation** l'ordre des 8 sections suivant :

```markdown
1. ## Description
2. ## Contexte
3. ## Critères d'acceptation
4. ## Règles d'affaires
5. ## Maquettes (Liens Figma officiels ou Captures d'écran visuelles UI)
6. ## Contrats UI & API Backend
7. ## Notes Techniques pour l'implémentation
8. ## Scénarios de test
```

> 📌 **Note Maquettes & Diagrammes** : La section `## Maquettes` contiendra **exclusivement des liens Figma officiels** (ex: `🔗 Lien Figma`) ou des captures d'écran visuelles UI. Les diagrammes d'architecture Mermaid habitent exclusivement dans le dossier `docs/01-architecture/`.

---

## 🛡️ 4. Les Règles d'Or de Rédaction (Zero-Fluff & Standards)

### Rule #1 : Additivité Stricte lors des Refactorings (Immutabilité du Contexte)
Lors de tout enrichissement ou alignement de format (ex: OKF v0.1), l'agent a **l'interdiction absolue de supprimer, remplacer ou altérer la section `## Contexte`** d'origine. Tout enrichissement s'effectue de façon 100% cumulative.

### Rule #2 : Alignment à la Stack Technologique du Projet
Les récits s'appuient **exclusivement** sur la stack technologique officielle définie dans le projet (ex: .NET 10.0 MAUI, C#, iOS, Android, NuGet, XAML).

### Rule #3 : Neutralité & Généricité des Outillages de Test
Pour les outillages de test, d'inspection et d'audit, les agents doivent **impérativement employer des termes génériques et neutres** (*Proxy d'analyse réseau*, *Scan de symboles binaire*, *Harnais de test d'intégration*). Interdiction formelle de sur-spécifier des noms d'outils tiers spécifiques non-standard (ex: gVisor, Charles Proxy, Tink, Proxyman).

### Rule #4 : Pureté du Persona Métier ("En tant que")
La clause *"En tant que"* doit désigner **exclusivement le rôle métier ou organisationnel** (ex: *PO du vertical SANTÉ*, *développeur mobile*). Interdiction absolue d'y insérer du jargon ou de la stack technologique (ex: pas de `(.NET 10)` dans l'intitulé du rôle persona).

### Rule #5 : Séparation des Artefacts OKF (Separation of Concerns)
Les *Registres d'Entités Typées OKF* et les métadonnées de graphes sémantiques **ne doivent JAMAIS figurer dans le corps des User Stories** (`backlog/stories/`). Ils appartiennent exclusivement au dossier d'architecture du projet (`docs/01-architecture/`, ex: `OKF_REGISTRE_ENTITES.md`).

### Rule #6 : Zero Meta-Commentaires Agentiques
Interdiction formelle d'inclure des notes système agentiques ou des commentaires méta (ex: `> **Note mLoop Stricte**...`) dans le corps des récits rédigés. Le récit doit rester 100% propre pour l'équipe dev et le PO.

### Rule #7 : Rédaction Directe des Règles d'Affaires (Interdiction des Identifiants Éphémères)
Interdiction absolue d'utiliser des préfixes d'identifiants éphémères internes (ex: `RM-TECH-04`, `REC-007`) dans la section `## Règles d'affaires`. Les règles d'affaires doivent être intitulées et rédigées en **français clair, fluide et professionnel** (ex: `* **Isolation d'Environnement (Pure-Privacy)** : La conformité pour SANTÉ...`).

---

## 🟢 5. Intégration dans le Moteur RHO & Linter WikiFix

Ces règles d'or sont encodées de façon déterministe dans :
- `c:\Memory Loop\.agents\soul.json` (Définition de l'Âme mLoop).
- `standards/rho_rules.yaml` (`section_preservation`, `technology_alignment`, `persona_purity`, `zero_meta_comments`, `okf_separation`, `no_shortcuts_excellence`).
- `src/pipelines/wikifix.py` (Validation INVEST et nomenclature automatique).
- `AGENTS.md` et `GEMINI.md` à la racine de mLoop.
