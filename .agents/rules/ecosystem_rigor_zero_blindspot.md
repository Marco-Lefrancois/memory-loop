---
trigger: "Toute tâche touchant au code source, gabarits, protocoles ou directives de Memory Loop (C:\\Memory Loop\\)"
authority: "ADR-0376 / ECOSYSTEM_RIGOR_PROTOCOL.md"
---

# Règle Inviolable : Audit 360° en 7 Couches (Zéro Blindspot)

Toute demande d'évolution ou de refactorisation touchant le cœur de l'écosystème Memory Loop (`standards/`, `src/`, `.agents/`, `docs/`) interdit formellement le codage spontané ou partiel.

## Les 7 Couches d'Inspection Obligatoires :
1. **Blueprints (`standards/blueprints/`)** : Vérifier les gabarits créés, modifiés ou rendus caducs. Éliminer les doublons.
2. **Protocoles (`standards/protocols/`)** : Mettre à jour les SSOT normatifs (`PROJECT_LIFECYCLE_STAGES.md`, `STORY_AUTHORING_FRAMEWORK.md`).
3. **Architecture (`standards/adr-system/`)** : Consigner la décision formelle (ADR Type 1) et indexer dans `README.md`.
4. **Directives Agents (`.agents/agents/`, `standards/agents/`)** : Aligner les personas et instructions TOML.
5. **Skills Portables (`.agents/skills/`)** : Mettre à jour les compétences impactées (`grill`, `plan`, `vibe-check`).
6. **Core Python & CLI (`src/core/`, `src/pipelines/`, `src/commands/`)** : Implémenter avec rétrocompatibilité déterministe.
7. **Tests & Parité (`tests/`, `CLI_PIPELINE_GUIDE.md`)** : 100% de tests unitaires verts et parité guide CLI stricte.

## Séquence Bloquante :
- Rédiger un **Plan d'Implémentation Zéro Blindspot** détaillant chaque fichier avec `[NEW]`, `[MODIFY]`, `[DELETE]`.
- Obtenir le feu vert humain explicite avant toute écriture.
- Clôturer par la vérification automatisée de l'ensemble des suites de tests.
