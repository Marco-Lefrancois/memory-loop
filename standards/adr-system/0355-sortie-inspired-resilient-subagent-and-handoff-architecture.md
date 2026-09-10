# ADR-0355 : Architecture de Résilience des Sous-Agents, Signalisation Sidecar & Handoff Evidence Policy

- **Statut** : Accepté
- **Date** : 2026-09-07
- **Auteurs** : Équipe mLoop Swarm & Co-Architecte Agentique
- **Périmètre** : Protocole de Signalisation (`src/core/worker_signal.py`), Adaptateur Herdr & Stall Watchdog (`src/core/herdr_adapter.py`), Pipeline de Workers (`src/pipelines/worker_pipeline.py`), Portes d'Achèvement & Non-Dégénérescence (`src/pipelines/completion_gate.py`), Commandes CLI (`src/commands/handlers/worker.py`, `src/commands/_registry.py`)
- **Références** : Sortie Architecture (sortie-ai/sortie), ADR-0029 (Herdr CLI Multiplexer), ADR-0205 (Autonomous Execution Loops), ADR-0306 (Teardown Gate Zero Zombie), ADR-0341 (Runnable Acceptance Gates), ADR-0352 (HarnessDev Non-Degeneracy Gate)

---

## 1. Contexte & Problématique

Dans les orchestrations de sous-agents autonomes au sein de mLoop (exécutés dans des volets terminaux PTY isolés gérés par Herdr), plusieurs fragilités opérationnelles récurrentes ont été identifiées :

1. **La Fausse Déclaration de Complétion (*Passive Drift & Degeneracy*)** :
   Un sous-agent peut proclamer dans sa sortie console ou son chat avoir achevé son travail avec succès, alors qu'aucune ligne de code, aucun fichier de test ou aucun artefact mémoire n'a été créé ou modifié (problématique documentée dans HarnessDev, ADR-0352).
2. **L'Absence de Canal pour les Non-Modifications Légitimes** :
   Lorsqu'un sous-agent mandaté pour un diagnostic ou une correction conclut après analyse approfondie qu'aucun changement de code n'est requis (`NO_CHANGE_NEEDED`), mLoop risquait d'assimiler cette absence de diff à une dégénérescence passive et d'interrompre le flux.
3. **Les Blocages Silencieux et Sessions Fantômes (*Stalls & Zombie Panes*)** :
   Des agents exécutant des processus interactifs bloquants, attendant des saisies non fournies ou crashant silencieusement laissaient des volets terminaux orphelins ouverts indéfiniment, consommant mémoire vive et descripteurs de processus sans progression.
4. **La Fragilité du Parsing PTY Brut** :
   Déduire l'état d'un agent uniquement à partir de regex heuristiques sur des flux ANSI bruts de 150 lignes est sujet au bruit, aux animations de loaders CLI et aux troncatures de buffers.

L'étude de l'architecture de **Sortie** (*sortie-ai/sortie*) a mis en lumière des mécanismes de résilience particulièrement vertueux : un protocole sidecar de statut par fichier plat, un watchdog de blocage (*stall detection*), et une politique stricte de validation des preuves d'effort (*handoff evidence policy*).

---

## 2. Décision d'Architecture

mLoop adopte formellement une intégration **purement souveraine en Python** des principes de Sortie au sein de son moteur et de son adaptateur Herdr, sans ajout de daemon Go externe ni de base SQLite concurrente.

### 1. Protocole de Signalisation Sidecar (`WorkerSignal`)
- Un fichier d'état sidecar normalisé est inspecté à la racine du projet (`.mloop/status`) ou dans la mémoire du worker (`Projects/<proj>/memory/worker_<story_id>.status`).
- Ce fichier supporte indifféremment une sérialisation **JSON structurée** ou une syntaxe **Clé-Valeur légère** (`STATUS=...`, `REASON=...`).
- Quatre états sémantiques formels sont reconnus :
  - `COMPLETED` : Tâche menée à terme avec succès, preuve physique attendue.
  - `NO_CHANGE_NEEDED` : Tâche analysée et clôturée avec dispense motivée d'écriture physique.
  - `BLOCKED` : Blocage explicite signalé par l'agent (dépendance manquante, contradiction, etc.).
  - `NEEDS_REVIEW` : Travail préliminaire complété nécessitant arbitrage ou validation HITL.
- L'invite transmise aux workers Herdr lors du spawn inclut automatiquement les consignes d'écriture de ce fichier sidecar.

### 2. Stall Detection & Watchdog de Purge (`detect_stalled_agents` & `reap_zombie_workers`)
- `HerdrAdapter` intègre une analyse d'inactivité basée sur les métadonnées de statut des volets.
- Tout worker identifié dans un état terminal ou inactif (`idle`, `stopped`, `completed`, `done`, `failed`, `blocked`, ou sans état actif) est catégorisé comme bloqué/stalled.
- La méthode `reap_zombie_workers` (exposée via la commande CLI `mloop worker-reap --timeout 300 --force`) procède à la clôture propre et méthodique des volets concernés, garantissant le respect strict de la politique *Zéro Session Zombie* (ADR-0306).

### 3. Politique de Preuve d'Effort Handoff (`HandoffEvidencePolicy`)
- Avant d'accepter l'achèvement d'une story et d'autoriser le passage à l'étape suivante, `CompletionGate.validate_workspace_evidence` est invoqué avec l'une des trois politiques :
  - **`OBSERVED` (Défaut)** : Valide la présence d'au moins un fichier modifié ou généré post-spawn. Si aucun changement n'est constaté sans signal explicite `NO_CHANGE_NEEDED`, la story est classée `DEGENERATE_CANDIDATE` et requiert une validation HITL.
  - **`STRICT`** : Refuse le passage si aucune modification tangible n'est détectée.
  - **`OFF`** : Désactive le contrôle physique (usage restreint aux environnements de test unitaire purs).
- Le signal `BLOCKED` déclenche immédiatement le statut `FAIL` et marque la story en attente d'arbitrage.

### 4. Commande CLI `worker-reap`
- La commande CLI standardisée `mloop worker-reap` est enregistrée dans le routeur central (`src/commands/_registry.py`) avec les drapeaux `--timeout` et `--force`, consolidant l'ancienne commande d'audit en une interface unifiée.

---

## 3. Conséquences & Bénéfices

* **Positives** :
  - **Souveraineté et Zéro Dépendance Binaire** : Implémenté à 100% en Python standard dans le socle existant de mLoop.
  - **Élimination des Faux Positifs** : Impossibilité pour un agent de clore une story sans preuve physique ou sans justification explicite dans le sidecar.
  - **Hygiène Parfaite du Runtime Herdr** : Clôture automatisée des processus résiduels et libération immédiate des ressources PTY.
  - **Transparence Asynchrone** : Le sidecar offre un point d'observation décorrélé du bruit de la sortie terminal.

* **Neutres / Légères Contraintes** :
  - Les agents doivent écrire dans `.mloop/status` pour notifier un état particulier, consigne ajoutée dans l'instruction de cadrage initiale du worker.
  - Les tests de pipeline simulant une moisson doivent simuler la création/modification d'un fichier pour passer la gate `OBSERVED`.
