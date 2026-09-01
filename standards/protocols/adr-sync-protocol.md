# Protocole ADR-Sync — Gouvernance Code ↔ ADR (Anti-Drift)

## Statut : Actif — Non Négociable

---

## 1. Contexte

Les ADRs de la série 01xx (`0100`, `0102`, `0103`) définissent la structure canonique des projets
mLoop. Ces décisions se répercutent dans le code via `src/state.py::ProjectLayout` et dans un
registre machine-readable `standards/adr-contracts.json`.

**Sans ce protocole**, toute modification d'ADR crée un drift silencieux entre la loi documentée
et le code exécuté — la catégorie d'erreur que ce protocole élimine.

---

## 2. Règle ADR-Sync (Agent Mandatory)

> **⚙️ Tout agent qui modifie ou crée un ADR de la série 01xx DOIT :**
>
> 1. **Mettre à jour `standards/adr-contracts.json`** pour refléter fidèlement la nouvelle décision.
> 2. **Relancer `python src/swarm.py calibrate --project <nom>`** pour valider la cohérence
>    code ↔ ADR (Step 9/9 : ADR Contract Sync).
> 3. **Ne jamais clore la session** si le Step 9 retourne FAIL — corriger avant de handoff.
>
> Une ADR modifiée **sans mise à jour du contrat** est considérée comme **non-appliquée**.

---

## 3. Périmètre des ADRs Couvertes

| ADR | Clé JSON dans `adr-contracts.json` | Constantes `ProjectLayout` |
|-----|------------------------------------|---------------------------|
| ADR-0100 | `ADR-0100.client_layout` | `CLIENT_LAYOUT`, `REFERENCE`, `DOCS`, `BACKLOG`, `MEMORY`, `GRAPHIFY_OUT` |
| ADR-0102 | `ADR-0102.docs_subdirs`, `ssot_files` | `DOCS_SUBDIRS`, `DOCS_INGESTED`, `DOCS_ARCHITECTURE`, `SPRINT_BACKLOG_FILE`, ... |
| ADR-0103 | `ADR-0103.mloop_layout`, `mloop_only_dirs` | `MLOOP_LAYOUT`, `DIRECTIVES`, `SRC`, `OPENSPEC` |

---

## 4. Flux de Maintenance

```
1. Modifier l'ADR source (standards/adr-system/01xx-*.md)
       ↓
2. Mettre à jour standards/adr-contracts.json
       ↓
3. python src/swarm.py calibrate --project <nom>
       ↓
4. Step 9/9 → PASS  ✅ (session peut se clore)
   Step 9/9 → FAIL  ❌ (corriger l'écart avant toute autre action)
```

---

## 5. Mécanisme de Détection Automatique

Le calibrateur (`src/pipelines/calibrate.py::_audit_adr_contracts()`) vérifie automatiquement :
- `ADR-0100.client_layout` == `ProjectLayout.CLIENT_LAYOUT`
- `ADR-0102.docs_subdirs` == `ProjectLayout.DOCS_SUBDIRS`
- `ADR-0103.mloop_layout` == `ProjectLayout.MLOOP_LAYOUT`

Tout écart génère un `FAIL` bloquant la validation globale de l'écosystème.
