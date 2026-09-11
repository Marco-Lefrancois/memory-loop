# ADR-0364 : Protocole de Hooks de Pré-Compaction, Checkpoint Boundaries et Récupération Déterministe

- **Statut** : Approuvé (Constitutionnel)
- **Date** : 2026-09-11
- **Auteurs** : Équipe mLoop Swarm & Co-Architecte Agentique
- **Périmètre** : Framework Swarm (`src/engine/hooks/`, `src/commands/handlers/hook.py`), Harnais IDE (`.agents/hooks.json`, `.opencode/plugins/mloop-compaction.js`, `.claude/settings.json`), Hygiène Contextuelle (`src/utils/context_guard.py`), Standards mLoop (`standards/adr-system/README.md`)

---

## 1. Contexte & Problématique

Dans les flux de travail agentiques à long cours (sessions dépassant 30 à 50 tours d'inférence), la saturation de la fenêtre de contexte de l'agent est inéluctable. Deux pathologies critiques ont été identifiées lors des cycles de compaction standard (`/compact`) opérées par les IDEs (ChatGPT, Claude Code, OpenCode) :

1. **La faillite de la compaction probabiliste standard (*Lossy Squish*)** :
   En l'absence de contraintes de harnais, le grand modèle de langage décide de manière discrétionnaire de ce qu'il résume ou omet. Il traite un identifiant de ticket formel (`COUVBOIRE-990`), des fichiers en cours d'édition ou des échecs récents de tests unitaires avec le même niveau de compression qu'une formule de politesse conversationnelle.
2. **L'amnésie opérationnelle et la dérive d'édition (*Post-Compaction Drift*)** :
   Au réveil post-compaction, l'agent opère dans un contexte artificiellement allégé mais dénué d'invariants factuels. Il tente des explorations sauvages du disque (`ls -R`, `find`), ré-édite des fichiers déjà validés, ou abandonne les cas limites de résilience et d'exceptions lors des implémentations TDD.
3. **Le gaspillage invisible de tokens sur les chemins physiques** :
   La répétition continue de chemins absolus Windows ou POSIX (ex: `file:///c:/Memory%20Loop/Projects/.../docs/05-assets/maquettes/<fichier>.svg` consommant 28 tokens par occurrence) brûle jusqu'à 40 % du budget de contexte réservé aux reprises d'état.

---

## 2. Décisions d'Architecture

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│              ARCHITECTURE ADR-0364 : CHECKPOINT BOUNDARY & PRE-COMPACTION HOOKS                  │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                  │
│   1. INTERCEPTION SYSTÈME 1 (PRE-COMPACT HOOK)                                                   │
│      ├── Déclenchement : Commande /compact ou Seuil Handoff (15 tours)                           │
│      ├── Extraction Déterministe : Git Status -s + EvidencePack + Story Cible                    │
│      └── Sérialisation Atomique : memory/compaction/latest_checkpoint.json                       │
│                                                                                                  │
│   2. PROTOCOLE D'INJECTION LOD-0 (≤ 400 TOKENS)                                                 │
│      ├── Ancrage Racine Unique : @root: Projects/<nom_projet>/                                   │
│      ├── Micro-URIs Canoniques : assets://, evidence://, story://, model:// (-75% tokens)       │
│      └── Directives d'Orientation : Point d'étape + Prochaine action unique non négociable      │
│                                                                                                  │
│   3. TRIPLE FILET DE RÉCUPÉRATION (FAIL-SAFE RECOVERY)                                          │
│      ├── Niveau 1 : latest_checkpoint.json vérifié par empreinte SHA-256                        │
│      ├── Niveau 2 : Rotation d'archives memory/compaction/history/checkpoint_<timestamp>.json    │
│      ├── Niveau 3 : Reconstruction SSOT depuis memory/SESSION_MEMORY_HEALTH.md                   │
│      └── Drift Guard : Interception des crawls sauvages avec réinjection forcée de l'invariant  │
│                                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 2.1 Principe du Checkpoint Boundary Déterministe

La compaction cesse d'être une compression destructive pour devenir une **frontière de point de contrôle déterministe (*Checkpoint Boundary*)**. 
Avant toute réduction de contexte par le LLM, le runtime Python mLoop intercepte le cycle de vie via `PreCompactionHandler` pour figer l'état physique du projet sur disque.

### 2.2 Matrice d'Autorité de Vérité par Phase (0 Blindspot)

L'Artefact #1 d'autorité n'est pas statique ; il est déterminé dynamiquement selon la phase active du cycle mLoop :

| Phase du Cycle | Artefact #1 d'Autorité | Données Invariant LOD-0 Réinjectées (Prompt) |
| :--- | :--- | :--- |
| **1. SPEC (Cadrage / Ingestion)** | `docs/00-ingested/` + Maquettes SSOT | Sources autoritaires, faits verbatim extraits, modèle DBML initial, questions ouvertes (`OQs`). |
| **2. PLAN (Découpage & Archi)** | `memory/evidence/<ID>_fact_dossier.md` | Pointeur direct cliquable, 3 faits majeurs non négociables, entités BD cibles, frontières ADR. |
| **3. BUILD (Dév & Tests TDD)** | Diptyque `_fact_dossier.md` + Story physique + Contrat Visuel (si UI) | Contexte story, 4 Piliers Gherkin, fichiers modifiés récents (`file_reservations`), tests `PASS/FAIL`. |
| **4. VALIDATE (Audit Sentinel)** | Story `<JIRA_KEY>.md` + `_evidence.json` | Score INVEST, anomalies Sentinel à corriger, résultats des portes d'acceptation. |

### 2.3 Système d'Ancrage et Micro-URIs Canoniques (Gain : -75 % Tokens)

Pour immuniser le contexte contre la répétition stérile de chemins absolus, mLoop déploie le résolveur `PathAliasResolver` (`src/engine/hooks/path_resolver.py`) :
- `@root: Projects/<nom_projet>/`
- `assets://<nom>.svg` ➔ `docs/05-assets/maquettes/<nom>.svg`
- `evidence://<id>.facts.md` ➔ `memory/evidence/<id>_fact_dossier.md`
- `story://<key>` ➔ `backlog/stories/<key>.md`
- `model://<nom>.dbml` ➔ `docs/03-models/<nom>.dbml`
- `source://<nom>.md` ➔ `docs/00-ingested/<nom>.md`

La résolution en chemins physiques Windows/POSIX pour les outils (`view_file`, `replace_file_content`) s'effectue en **0 ms sans appel disque**.

### 2.4 Le Schéma Pydantic `CompactionCheckpoint`

Le fichier [memory/compaction/latest_checkpoint.json](file:///c:/Memory%20Loop/memory/compaction/latest_checkpoint.json) est gouverné par le modèle Pydantic strict `CompactionCheckpoint` :
- `project_name` : Identifiant canonique du projet actif.
- `focused_story_id` : Identifiant de la story en cours (`None` si phase SPEC).
- `stage` : Phase mLoop (`SPEC`, `PLAN`, `BUILD`, `VALIDATE`, `SHIP`).
- `timestamp` : Horodatage ISO-8601.
- `story_context` : Chapeau fonctionnel condensé (*« En tant que... je veux... afin de... »*) et règles `RM-xxx`.
- `active_acceptance_criteria` : Les 4 Piliers Gherkin contractuels (Nominal, Exceptions, Résilience, UX).
- `file_reservations` : Chemins relatifs et statuts (`M`, `A`, `D`) des fichiers modifiés extraits de `git status -s`.
- `tool_outcomes` : Tableau structuré des derniers résultats d'outils (`{tool, status: PASS|FAIL, proof_hash}`).
- `primary_artifact_uri` : Micro-URI de l'Artefact #1 selon la phase.
- `visual_contract_uri` : Micro-URI de la maquette validée (si frontend/fullstack).
- `resume_instructions` : Bloc Markdown condensé injecté au réveil (≤ 400 tokens).
- `checkpoint_hash` : Empreinte SHA-256 garantissant l'intégrité à la relecture.

### 2.5 Triple Filet de Récupération Fail-Safe

1. **Niveau 1 (Lecture Atomique)** : Chargement de `latest_checkpoint.json` validé par `checkpoint_hash`.
2. **Niveau 2 (Fallback Historique)** : En cas d'incohérence ou de fichier tronqué, lecture du dernier fichier sain sous `memory/compaction/history/checkpoint_<timestamp>.json`.
3. **Niveau 3 (Reconstruction SSOT)** : Reconstruction de secours depuis `memory/SESSION_MEMORY_HEALTH.md` et `backlog/sprint_backlog.md`.
4. **Post-Compact Drift Guard** : Interception au vol des commandes exploratoires (`ls -R`, `find`) au tour N+1 post-compaction avec injection forcée de l'invariant d'orientation.

### 2.6 Intégration Multi-Harnais Symbiotique

- **Python Core mLoop** : Commande CLI officielle `python src/swarm.py hook --event pre_compact [--project <nom>]`.
- **Antigravity IDE** : Déploiement de `.agents/hooks.json` exploitant `PostToolUse` (mise à jour continue des réservations et tests), `PreInvocation` (détection de reprise) et `Stop` (teardown gate).
- **OpenCode** : Extension `.opencode/plugins/mloop-compaction.js` interceptant `experimental.session.compacting` pour injecter l'invariant via `output.context.push(...)`.
- **Claude Code** : Enregistrement dans `.claude/settings.json` du hook `PreCompact` (matcher `manual|auto`) appelant la CLI mLoop.

---

## 3. Tableau Comparatif Avant / Après ADR-0364

| Dimension | Avant ADR-0364 | Après ADR-0364 |
| :--- | :--- | :--- |
| **Nature de la Compaction** | Oubli probabiliste non maîtrisé (*lossy squish*) | Frontière de point de contrôle déterministe (*Checkpoint Boundary*) |
| **Fichiers sous contrat (Dirty State)** | Fréquemment oubliés ou réécrits par-dessus | Verrouillés déterministement via `git status -s` et Micro-URIs |
| **Cas limites de test (Gherkin)** | Oubliés au profit du cas nominal seul | Préservés intacts (Exceptions, Résilience 5s, UX) |
| **Consommation de tokens chemins** | ~28 tokens par chemin physique complet | ~5 tokens par Micro-URI (**Gain : -75 %**) |
| **Budget de réinjection au réveil** | Aléatoire (souvent > 3 000 tokens ou 0) | Strictement plafonné en **LOD-0 ≤ 400 tokens** |
| **Résilience en cas de crash session** | Amnésie totale, obligation de ré-ingérer | Triple filet de récupération automatique Fail-Safe |

---

## 4. Conséquences

### Positives :
- **Continuité Cognitive Ininterrompue** : L'agent reprend son travail à la seconde exacte où il a été interrompu sans hésitation ni re-scan de disque.
- **Conformité Constitutionnelle** : Respect rigoureux du Contrat Visuel (Maquettes SSOT), du Dossier de Preuves Documentaires et des 4 Piliers Gherkin.
- **Portabilité Totale** : Le même invariant fonctionne de manière transparente sur Antigravity, OpenCode, Claude Code et les sous-sessions isolées Herdr.

### Négatives / Contraintes :
- **Discipline de synchronicité** : Le hook de pré-compaction doit s'exécuter localement en **moins de 150 ms** pour ne créer aucune latence perceptible pour l'utilisateur.
- **Écriture atomique obligatoire** : Exige l'écriture via fichier temporaire `.tmp` puis `replace()` pour supporter les verrous de fichiers sous Windows.
