# ADR-0005 : Gouvernance Backlog & Nomenclature OKF

**Statut** : ACCEPTED  
**Date** : 2026-07-30  
**Décideurs** : PO mLoop, Antigravity Agentic Coworker  
**Domaine** : Framework mLoop, Standards d'Architecture, Métadonnées OKF v0.1 & Backlog

---

## 📋 Contexte & Enjeux

Dans l'évolution du framework mLoop (v2.2.0), l'intégration du standard **Open Knowledge Format (OKF v0.1)** et de la mémoire sémantique **LLM Wiki v2** ont introduit de nouvelles métadonnées (Score de confiance $C$, Registre d'entités typées, graphes sémantiques, règles de supersession).

L'analyse de l'utilisation réelle par les équipes de développement et les PO a révélé 3 risques majeurs :
1. **Pollution du Backlog** : L'injection de tables de registres d'entités OKF et de métadonnées sémantiques dans les User Stories créait du bruit ("Fluff") pour les développeurs.
2. **Sur-Spécification d'Outillage** : L'utilisation de noms d'outils tiers spécifiques (ex: gVisor, Charles Proxy, Tink, Proxyman) créait des contraintes artificielles et non-standard.
3. **Absence de Standard de Nomenclature** : L'absence de convention universelle sur le nommage des fichiers risquait d'entraîner la création de documents ad-hoc jetables.

---

## 🎯 Décision d'Architecture

Il est décidé d'adopter les 4 principes d'architecture fondamentaux suivants :

### 1. Le Manifeste d'Excellence (L'Âme de mLoop : `soul.json`)
L'écosystème mLoop consigne dans `c:\Memory Loop\.agents\soul.json` et `AGENTS.md` le principe d'immutabilité :
- **Zéro Raccourci** : Analyse complète et rigoureuse obligatoire avant toute modification.
- **Interdiction des Documents Ad-Hoc Jetables** : Tout document doit s'insérer proprement dans la structure officielle (`docs/` ou `backlog/`).
- **Solutions Optimales, Paramétrées & Génériques** : Toujours offrir la solution la plus réutilisable, configurée via `opencode.json`.

### 2. Séparation Stricte des Artefacts (Separation of Concerns)
- **Les User Stories (`backlog/stories/<CODEBASE>/US-<ID>.md`)** sont 100% dédiées au PO et à l'équipe dev. Elles contiennent exclusivement les sections du template officiel.
- **Les Registres d'Entités Typées OKF** et métadonnées de graphes sont isolés dans le dossier d'architecture du projet (`docs/01-architecture/OKF_REGISTRE_ENTITES.md`).

### 3. Convention Universelle de Nomenclature des Fichiers

| Catégorie | Emplacement & Pattern | Exemple Concret |
| :--- | :--- | :--- |
| **Récits Pré-triage (Draft)** | `backlog/stories/<CODEBASE>/REC-<ID>.md` | `backlog/stories/COMMERCE/REC-001.md` |
| **User Stories Validées** | `backlog/stories/<CODEBASE>/US-<ID>.md` | `backlog/stories/COMMERCE/US-00.md` |
| **ADR Framework / Projet** | `docs/01-architecture/ADR-<XXX>_<nom_snake_case>.md` | `docs/01-architecture/ADR-005_gouvernance.md` |
| **Registres Entités OKF** | `docs/01-architecture/OKF_REGISTRE_ENTITES.md` | `docs/01-architecture/OKF_REGISTRE_ENTITES.md` |
| **Backlog SSOT** | `backlog/sprint_backlog.md` | `backlog/sprint_backlog.md` |
| **Questions Client / PO** | `docs/04-transverse/00-questions-ouvertes-client.md` | `Q-001`, `Q-002` |
| **Questions Dev Team** | `docs/04-transverse/00-questions-ouvertes-devteam.md` | `QD-001`, `QD-002` |

> **Note sur les préfixes REC vs US :** Le préfixe `REC-XXX` est utilisé pour les récits en cours d'analyse et de triage par l'agent Plan. Une fois le récit découpé, grillé, validé (score INVEST > 80) et prêt pour le sprint, il est promu sous le préfixe définitif `US-XXX`.

### 4. Sequence Immuable des Sections de Story
Ordre strict et immuable des sections dans chaque récit :
`Description` | `Contexte` | `Critères d'acceptation` | `Règles d'affaires` | `Maquettes` | `Contrats UI & API Backend` | `Scénarios de test (Gherkin)` | `Notes de Traçabilité & Références (IA Only)`

### 5. Numérotation Indépendante des Questions Ouvertes (`Q-` vs `QD-`)
Afin d'éviter tout conflit ou ambiguïté d'attribution entre les arbitrages d'affaires/légaux et les verrous techniques internes :
- **Préfixe `Q-XXX`** : Réservé exclusivement aux questions ouvertes Client, PO, Légal et Métier (`00-questions-ouvertes-client.md`).
- **Préfixe `QD-XXX`** : Réservé exclusivement aux questions ouvertes Équipe Dev, Architecture et Technique (`00-questions-ouvertes-devteam.md`).
- Chaque sous-domaine possède sa propre séquence autonome et indépendante démarrant à `001`.

### 6. Cycle de Vie et Statuts des ADRs
Le statut d'une Décision d'Architecture (ADR) doit obligatoirement être l'un des suivants :
- **DRAFT** : En cours de rédaction ou de discussion.
- **PROPOSED** : Soumis à la validation (en attente).
- **ACCEPTED** : Décision actée et en vigueur.
- **DEPRECATED** : Décision obsolète (remplacée ou abandonnée).
- **SPECULATIVE / TARGET_INFRASTRUCTURE** : Décision décrivant une cible architecturale idéale ou future, non encore applicable formellement mais servant de cap (ex: ADR-004 sur gVisor).


---

## ⚡ Conséquences & Bénéfices

- **Bénéfice Développeur** : Backlog 100% propre, sans bruit agentique ni sur-spécification d'outils tiers.
- **Bénéfice Architecte** : Centralisation propre de la connaissance sémantique OKF sous `docs/01-architecture/`.
- **Bénéfice Agentic Engine** : Contrôle déterministe via le linter `WikiFix` et le moteur RHO (`standards/rho_rules.yaml`).
