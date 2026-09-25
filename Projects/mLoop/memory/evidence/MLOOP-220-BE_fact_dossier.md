# 📁 Dossier de Preuves Documentaires — `MLOOP-220-BE`

- **Récit** : `MLOOP-220-BE` — Bridge d'Exécution & Commande CLI OpenCode (Intégration Declarative opencode.json) (EPIC-22-TOOLING-ECOSYSTEM-HARNESS)
- **Établi le** : 2026-09-24 — Cadrage Macro-Grill VALIDÉ
- **dossier_status**: VALIDATED
- **Décisions scellées** : Grill Macro EPIC-22 (Q1-A Isolation Projet & Proxy Local LiteLLM port 4000) → `ADR-014_epic-22_integration_operationnelle_ecosysteme_tooling.md`

---

## 1. Sources & Notes d'Atelier

- Épopée : `Projects/mLoop/backlog/epics/epic_tooling_ecosystem_harness.md`
- Fiche de Savoir SSOT : `docs/06-knowledge/06-tooling-ecosystem/KN-050_opencode_cli_runtime.md`
- ADR de référence : `standards/adr-system/0202-modularite-interne-agents.md` (≤ 300L), `standards/adr-system/0370-standard-cli-transverse-parite-ssot-et-decoupage-modulaire.md`
- ADR de cadrage local : `Projects/mLoop/docs/01-architecture/ADR-014_epic-22_integration_operationnelle_ecosysteme_tooling.md`
- Ingestion technique : `docs/00-ingested/opencode/`
- Code source ciblé : `src/commands/handlers/opencode.py` (≤ 300L) et `src/swarm.py`

---

## 2. Matrice de Résolution des Conflits

| Conflit | Résolution |
| :--- | :--- |
| Configuration globale vs Configuration par projet | **Isolation Projet (Q1-A)** : Configuration stockée sous `Projects/<project>/.opencode/opencode.json` sans écriture globale polluante. |
| Routage direct API externe vs Proxy LiteLLM | **Proxy Local LiteLLM** : Routage exclusif sur `http://localhost:4000` garantissant gouvernance, logs et maîtrise des clés. |
| Ingestion des directives mLoop | **Injection automatique** : Les règles fondamentales de `AGENTS.md` sont injectées dans la configuration générée. |

---

## 3. Extraits Verbatim Sourcés

**Extrait 1 — `docs/06-knowledge/06-tooling-ecosystem/KN-050_opencode_cli_runtime.md` :**
```text
"OpenCode CLI supporte nativement un fichier declarative .opencode/opencode.json définissant les providers et endpoints. Le proxy LiteLLM local (port 4000) permet d'unifier l'authentification et les quotas."
```
➔ **Fait établi (F-01)** : La commande `mloop opencode init` doit provisionner `opencode.json` pointant vers LiteLLM local sans exposer de secret API en clair.

**Extrait 2 — `standards/adr-system/0202-modularite-interne-agents.md` :**
```text
"Plafond strict de 300 lignes de code et 15 Ko par fichier Python source sous src/."
```
➔ **Fait établi (F-02)** : Le nouveau handler `src/commands/handlers/opencode.py` doit respecter impérativement `RULE-AST-01` (≤ 300L).
