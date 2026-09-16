# 🛡️ Guide Agentique & Spécifications Développeur — {{PROJECT_NAME}}

Ce document constitue la **Source de Vérité Agentique et Fonctionnelle (SSOT)** pour le projet **{{PROJECT_NAME}}**.

Il est conçu pour être consommé directement par l'équipe de développement et par tout assistant de codage IA (Cursor, GitHub Copilot, VS Code, OpenCode, Claude Code, OpenAI Codex), dans le respect strict du protocole **Universal Dev Handoff** ([ADR-0319](../../standards/adr-system/0319-dual-agent-handoff-openspec-ready.md)).

---

## 1. Organisation du Dépôt & Source de Vérité (La Loi des 3 Piliers)

Le dépôt est structuré de façon modulaire et étanche :

```
├── 📂 docs/                          # Source de Vérité Fonctionnelle & Architecturale (SSOT)
│   ├── 📂 00-ingested/               # Analyse normalisée des documents sources & maquettes
│   ├── 📂 01-architecture/           # Énoncé des Travaux (SOW), schémas et décisions d'architecture (ADRs)
│   ├── 📂 02-business-rules/         # Règles d'affaires métier (RM-XXX)
│   ├── 📂 04-transverse/             # Registres de questions ouvertes et arbitrages
│   └── 📂 05-assets/                 # Actifs graphiques versionnés (maquettes, diagrammes - ADR-0332)
│
├── 📂 backlog/                       # Terrain d'Exécution & Spécifications Prêtes pour Dev
│   ├── 📄 sprint_backlog.md          # Matrice d'avancement & statut des récits
│   └── 📂 stories/                   # User Stories au Gold Standard (4 Piliers Gherkin)
│
└── 📂 memory/                        # Traçabilité & Preuves de Spécifications
    └── 📂 evidence/                  # EvidencePacks JSON associés à chaque récit
```

---

## 2. Contrats de Spécification & Règle des 4 Piliers Gherkin ([ADR-0301](../../standards/adr-system/0301-standard-gherkin-outlines-4-piliers.md))

Chaque User Story présente sous `backlog/stories/` constitue un **contrat fonctionnel déclaratif complet** structuré autour des **4 Piliers Gherkin** que le code applicatif doit obligatoirement satisfaire :

1. **Chemin Nominal (*Happy Path*)** : Le parcours utilisateur standard complété avec succès.
2. **Rejets Métier & Erreurs de Validation** : Données invalides, règles métier non respectées, formulaires incomplets.
3. **Résilience Technique & Cas Limites (*Edge Cases*)** : Comportement hors-ligne, expiration de session (timeout réseau), saturation des requêtes (anti-rebond).
4. **UX, Sécurité & Accessibilité** : Retours visuels clairs, accessibilité (WCAG AA), masquage des données sensibles et états de chargement.

---

## 3. Directives de Développement & Pureté Fonctionnelle ([ADR-0319](../../standards/adr-system/0319-dual-agent-handoff-openspec-ready.md))

- **Pureté Fonctionnelle & Zéro Code Physique** : Les spécifications décrivent le comportement métier et les flux d'écrans sans couplage rigide à une implémentation physique. Zéro snippet de code physique dans les récits.
- **Doc-First Obligatoire** : Se référer en priorité aux documents d'analyse sous `docs/00-ingested/` pour le détail de chaque parcours.
- **Souveraineté de l'Aval** : L'équipe de développement et ses agents d'implémentation choisissent librement leurs patrons d'architecture (MVVM, Clean Architecture, DI) et leurs frameworks de test pour satisfaire les critères Gherkin.
