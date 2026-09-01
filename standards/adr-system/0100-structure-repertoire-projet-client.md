# ADR-0100 : Structure de Répertoire Projet Client (Loi des 3 Piliers)
## Statut : Accepté (Série 01xx - Structure Projet Client)

---

## 1. Contexte

Les anciennes spécifications (ADR-0002 originale et ADR-0019) imposaient la présence de répertoires `src/` et `openspec/` dans tous les projets sous `Projects/`. En mode `ProjectMode.CLIENT` (analyse et spécification d'affaires pour une application client), le code applicatif physique réside dans le dépôt propre du client (hors de mLoop).

---

## 2. Décision

Nous formalisons la **Structure Canonique de Projet Client (Loi des 3 Piliers)** pour tout projet sous `Projects/<nom_projet>/` :

```
Projects/<nom_projet>/
├── reference/       <-- Intrants bruts déposés par l'humain (PDF, Excel, Word, SVG)
├── docs/            <-- Source de Vérité Architecturale SSOT (5 dossiers canoniques)
├── backlog/         <-- Stories & sprint_backlog.md
├── memory/          <-- Mémoire Persistante & Observabilité (6 sous-dossiers canoniques)
│   ├── sessions/    (Handoffs inter-sessions)
│   ├── debates/     (Transcriptions débats Sentinel/Rubber Duck)
│   ├── sync/        (Historique & rapports Jira)
│   ├── reports/     (Rapports sémantiques WikiFix)
│   ├── cache/       (Base SQLite FTS5, Graphify & execution_traces.json)
│   └── tmp/         (Espace temporaire machine DAG fanout/ & checkpoints/)
└── graphify-out/    <-- Graphe de connaissances NetworkX (Persistance interne)
```

**Règles Inviolables :**
1. **Exemption `src/` et `openspec/`** : Les projets clients en mode `CLIENT` ne contiennent ni dossier `src/` ni dossier `openspec/`.
2. **Loi des 3 Piliers Métier** : Les agents et l'humain interagissent exclusivement via `reference/` (matière première), `docs/` (SSOT) et `backlog/` (exécution).

---

## 3. Conséquences

- **Alignement Terrain 100%** : Reflète exactement la structure validée des projets en production.
- **Clarté pour les Agents** : Élimine la confusion liée à la recherche de répertoires de code fictifs.
