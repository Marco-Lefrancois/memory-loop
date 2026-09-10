---
name: herdr-orchestration
description: Directives et protocole de contrôle d'infrastructure natif via Herdr v0.8.0 PTY multiplexer (Mode Unattended / Autonomie Totale).
---

# 🤖 HERDR OPERATING PROTOCOL v0.8.2+ (System Capabilities & Rules - ADR-0345)

Tu es l'**Agent Orchestrateur Principal**. Tu disposes de la pleine possession de l'environnement d'exécution via le daemon **Herdr v0.8.2+** et le plugin officiel **`mloop-herdr-plugin`**.

> [!IMPORTANT]
> **Règle d'Or de Non-Blocage :**
> Ne réalise jamais les tâches d'implémentation de bas niveau toi-même sur le terminal principal `p1` si tu peux les déléguer. Scinde le terminal en volets *workers*, démarre l'agent approprié, envoie la tâche avec attente et récupère le résultat.

---

## 🚀 Commandes CLI mLoop Haut-Niveau (Herdr Automation - ADR-0324, ADR-0325 & ADR-0345)

L'orchestrateur mLoop dispose de commandes CLI unifiées pour automatiser le cycle de vie des workers sans manipulation manuelle de volets terminaux, avec sélection dynamique du meilleur modèle LiteLLM selon la mission :

```bash
# 1. Instancier un worker dédié avec sélection dynamique du meilleur modèle
# Missions supportées : deepening | validation | deepsearch | build | compaction
python src/swarm.py worker-spawn --project <nom_projet> --story <STORY_ID> --task-type validation

# Ou avec spécification explicite du modèle LiteLLM :
python src/swarm.py worker-spawn --project <nom_projet> --story <STORY_ID> --kind opencode --model nmedia_cloud/claude-opus-4.8

# 2. Interroger la santé et l'état d'avancement de tous les workers
python src/swarm.py worker-status --project <nom_projet>

# 3. Moissonner la sortie PTY déballée, élaguer le bruit (anti-bloat) et enrichir l'EvidencePack
python src/swarm.py worker-harvest --project <nom_projet> --story <STORY_ID>

# 4. Clôturer le volet worker une fois la tâche validée
python src/swarm.py worker-close --project <nom_projet> --story <STORY_ID>

# 5. Purger tous les volets orphelins (Zero Zombie Policy)
herdr plugin action invoke reap_zombies --plugin org.mloop.orchestrator
```

> [!IMPORTANT]
> **Expérience Native dans Herdr (Link Handlers & Panes) :**
> - **Split Backlog** : `herdr plugin pane open --plugin org.mloop.orchestrator --entrypoint backlog`
> - **EvidencePack Overlay** : `herdr plugin pane open --plugin org.mloop.orchestrator --entrypoint evidence`
> - **Navigation par Clic (Link Handlers)** : Faire `Ctrl+Click` sur un chemin de story (`backlog/stories/US-XXX.md`) ou un fichier d'evidence (`*_evidence.json`) dans n'importe quel terminal Herdr ouvre instantanément le volet d'inspection mLoop dédié.

> [!IMPORTANT]
> **Règle du Prompt Auto-Suffisant (Clean Slate Protocol) :**
> Un worker spawné démarre dans une **session vierge sans contexte projet**. Le prompt transmis via `worker-spawn` DOIT être **auto-suffisant** et contenir dans cet ordre :
> 1. La commande de restauration : `python src/swarm.py resume --project <projet>`
> 2. Le chemin exact du fichier à traiter
> 3. La séquence d'actions précise à exécuter (pas de pointeurs vagues)
> 4. La commande de finalisation : `python src/swarm.py sync --project <projet>`
>
> Un prompt de type *"Consulte le fichier X et fais Y"* sans boot sequence est **insuffisant** — le worker ne pourra pas résoudre le contexte projet seul.

> [!IMPORTANT]
> **Règle de Cadrage des Outils LiteLLM (ADR-0325) :**
> - N'utilisez que les agents configurés sur la passerelle d'entreprise LiteLLM (`opencode`, `pi`, `omp`, `agy`).
> - Ne JAMAIS invoquer de binaire externe direct (ex: Claude Code standalone `claude`) qui échouerait à l'authentification.
> - Types de missions et modèles recommandés :
>   - **`deepening`** (Approfondissement/Architecture) ➔ `nmedia_cloud/claude-opus-4.8`
>   - **`validation`** (Validation & QA de haute fidélité) ➔ `nmedia_cloud/gpt-5.6-terra-thinking`
>   - **`deepsearch`** (Exploration/R&D) ➔ `nmedia_cloud/claude-sonnet-5`
>   - **`build`** (Développement physique) ➔ `nmedia_cloud/claude-sonnet-4.6`
>   - **`compaction`** (Micro-tâches & Linters) ➔ `nmedia_cloud/gemini-3.5-flash-lite`

---


## 🛠️ Primitives de Contrôle Herdr v0.8.0 (Bas Niveau)

### 1. Créer et Scinder les Volets Terminals (Layout Primitive)

> [!WARNING]
> **Windows — Résolution `opencode.exe` vs `opencode.cmd` (O3) :**
> `Start-Process -FilePath opencode` résout `opencode.cmd` (wrapper CMD npm) avant `opencode.exe`.
> Cela déclenche l'erreur `%1 n'est pas une application Win32 valide`.
> **`herdr_adapter.py` corrige cela automatiquement** en résolvant le chemin absolu
> `%APPDATA%\npm\opencode.exe` dans le fallback `pane_run`.
> Ne jamais appeler `Start-Process -FilePath opencode` directement — toujours passer
> par `python src/swarm.py worker-spawn` ou `herdr agent start`.

```bash
# 1. Scinder le terminal courant sans basculer le focus UI
created=$(herdr pane split $PANE_ID --direction right --no-focus)
worker_pane=$(echo "$created" | jq -r '.result.pane.pane_id')
```

### 2. Démarrer et Prompt un Agent Worker (Agent Primitive)

> [!WARNING]
> **Délai `interactive_ready` obligatoire (O2 — Windows) :**
> OpenCode a besoin de ~3 secondes pour atteindre l'état `interactive_ready` après
> `agent start`. Un prompt envoyé avant cet état est **perdu silencieusement** —
> l'agent reste IDLE sans traiter la tâche (`revision` reste à 2 sans progresser).
> **Toujours passer par `worker-spawn`** qui gère ce délai automatiquement (3s fixe + wait_agent).
> En cas d'appel bas-niveau direct, attendre `idle` avant `agent prompt`.

```bash
# Recommandé : worker-spawn gère le délai automatiquement
python src/swarm.py worker-spawn --project <P> --story <ID> --task-type <type>

# Bas-niveau : attendre idle AVANT d'envoyer le prompt
herdr agent start worker_1 --kind opencode --pane "$worker_pane" -- --yolo
herdr agent wait worker_1 --until idle --timeout 10000          # ← OBLIGATOIRE avant prompt
herdr agent prompt worker_1 "Build US-XXX component following SCC rules" --wait --timeout 300000
```

### 3. Surveillance du Cycle de Vie (State Monitoring)
```bash
# 4. Attendre que l'agent atteigne un état stable (working, blocked, idle, done, unknown)
herdr agent wait worker_1 --until idle --until done --until blocked --timeout 300000
```

> [!WARNING]
> **Interception du Mode Bloqué (`blocked`) :**
> Si `herdr agent wait` retourne l'état `blocked`, Herdr a détecté une question utilisateur ou une confirmation requise. L'orchestrateur doit déclencher le protocole **Stop & Ask (HITL)** ou soumettre l'entrée nécessaire via `herdr agent send-keys`.

### 4. Lecture d'Historique PTY Alternate-Screen

> [!WARNING]
> **Source conditionnée par l'état de l'agent (O5) :**
> La source `recent-unwrapped` est **bloquée** quand l'agent est `WORKING` — erreur
> `agent_not_idle: cannot read while working`. Adapter la source selon l'état :

```bash
# Agent IDLE ou done → historique complet déroulé (recommandé après complétion)
herdr agent read worker_1 --source recent-unwrapped --lines 120

# Agent WORKING → capture de la vue visible uniquement (surveillance en temps réel)
herdr agent read worker_1 --source visible --lines 60
```

> **Bonne pratique** : Toujours appeler `agent wait` avant `agent read --source recent-unwrapped`
> pour garantir que l'agent est dans un état stable (idle / done / blocked).

### 5. Nettoyage & Libération des Ressources (Teardown Obligatoire)

> [!IMPORTANT]
> **Zéro Session Zombie (O4) :**
> Un `worker-spawn` non suivi d'un `worker-close` laisse un process OpenCode actif en mémoire.
> Lors du test de délégation de cette session, **3 zombies** ont été produits par omission
> du teardown après chaque test. La séquence complète est non négociable :

```bash
# Séquence complète OBLIGATOIRE — ne jamais s'arrêter après worker-spawn seul
python src/swarm.py worker-harvest --project <P> --story <ID>   # 1. Moisson des livrables
python src/swarm.py worker-close   --project <P> --story <ID>   # 2. Fermeture du volet

# Contrôle final avant fin de session : doit afficher 1 seul worker (session principale)
python src/swarm.py worker-status --project <P>
```

> **Règle de fin de tour** : Si `worker-status` affiche des workers en état `IDLE`,
> ce sont des zombies — les fermer immédiatement via `worker-close` ou `herdr pane close <id>`.

---

## 📐 Alignement avec le Cycle Spec-Driven mLoop v2.0.0 & AI Coding Loop

1. **Phase 1 SPEC** : Ingestion documentaire sous `docs/00-ingested/`.
2. **Phase 2 PLAN** :
   - Étape 2A : Découpage sommaire Outcome-Driven & ToT/DFS dans `STORY_MAPPING.md`.
   - Étape 2B : *Grill with Docs* par récit + qualification INVEST 4 Piliers Gherkin + Artefact `memory/evidence/<STORY_ID>_evidence.json`.
3. **Phase 3 BUILD (Herdr Clean Slate)** : Lancement du worker dédié via `python src/swarm.py worker-spawn --project <proj> --story <ID>`. L'agent s'exécute dans une fenêtre de contexte vierge (Smart Zone maximale). Le linter `story_guard.py` bloque physiquement toute écriture hors-périmètre du SCC.
4. **Phase 4 VALIDATE (mLoop Gatekeeping & Harvest)** : Moisson automatique des logs et filtrage anti-bloat via `python src/swarm.py worker-harvest --project <proj> --story <ID>`, audit Sentinel (`rubber-duck` + `wikifix`), validation des 4 Piliers Gherkin.
5. **Phase 5 SHIP / MEMORY** : Auto-synchronisation Graphify (`sync`), Jira Cloud (`jira_sync` Story-Only), Auto-Repair (`calibrate` 8/8 PASS) et libération des ressources via `python src/swarm.py worker-close --project <proj> --story <ID>`.

