# Plan d'Implémentation : Intégration des Innovations Awesome Agents dans mLoop

Ce plan formalise l'intégration de 3 piliers d'opportunités identifiés lors du benchmark d'**Awesome Agents** (Août 2026) :
1. **Auto-Génération d'Evals depuis les Rejets Sentinel (Pattern Latitude)** : Transformer automatiquement chaque rejet de récit ou anomalie d'architecture en cas de test de non-régression dans la suite d'évaluation AOEP (`tests/evals/`).
2. **Moniteur de Contexte & Observabilité Dumb-Zone (Pattern ctop / ClawMetry)** : Alerte visuelle CLI et blocage préventif lorsque la fenêtre de contexte franchit le seuil critique de 60% (*Dumb Zone*).
3. **Moteur de Supersession de Mémoire (Pattern Statewave)** : Remplacement automatique et archivage des connaissances et règles d'affaires obsolètes lors de la publication de nouveaux ADRs ou récits.

---

## 🎯 Objectifs & Bénéfices

* **Immunité contre les régressions** : Toute anomalie détectée par Sentinel/Rubber Duck devient instantanément un cas de test pérenne.
* **Prévention du décrochage cognitif** : Empêcher les hallucinations causées par la saturation de contexte en alertant l'orchestrateur.
* **Hygiène de la base de connaissances** : Éliminer les règles contradictoires en marquant automatiquement les anciennes assertions comme `SUPERSEDED`.

---

## ⚠️ User Review Required

> [!IMPORTANT]
> - L'implémentation touche uniquement le cœur de framework mLoop (`src/`, `tests/`) et la documentation d'architecture (`docs/01-architecture/`).
> - Zéro impact sur les projets clients isolés (`Projects/Metro_*`, `Projects/BoireFrere_*`).

---

## 📂 Modifications Proposées

### 1. Générateur Automatique d'Evals (`AutoEvalHarvester`)

#### [NEW] [`src/pipelines/eval_harvester.py`](file:///C:/Memory%20Loop/src/pipelines/eval_harvester.py)
* Intercepte les `blocking_issues` renvoyées par `RubberDuckEngine` et `WikiFix`.
* Génère automatiquement un fichier de test d'évaluation structuré dans `memory/evals/` ou `tests/evals/`.
* Permet de rejouer les évaluations via la CLI : `python src/swarm.py eval-replay --project mLoop`.

---

### 2. Moniteur de Contexte & Alerte Dumb-Zone (`ContextMonitor`)

#### [NEW] [`src/utils/context_monitor.py`](file:///C:/Memory%20Loop/src/utils/context_monitor.py)
* Estime l'occupation contextuelle de la session en cours et de chaque prompt.
* Avertit dès que le seuil de 60% de la fenêtre de contexte maximale du modèle est dépassé (*Zone de Dérive Cognitive*).
* Fournit une jauge visuelle synthétique dans la CLI : `python src/swarm.py context-watch`.

---

### 3. Moteur de Supersession de Connaissances (`MemorySupersessionEngine`)

#### [NEW] [`src/loop_mem/supersession.py`](file:///C:/Memory%20Loop/src/loop_mem/supersession.py)
* Analyse les nouveaux ADRs et récits pour identifier les assertions antérieures rendues caduques.
* Marque les faits obsolètes avec `status: SUPERSEDED` et lien vers le fait remplaçant (`superseded_by: ADR-XXXX`).

---

### 4. Intégration CLI Swarm & Registre

#### [MODIFY] [`src/commands/_registry.py`](file:///C:/Memory%20Loop/src/commands/_registry.py)
* Ajout des commandes :
  - `eval-harvest` : Récolte et conversion des anomalies en tests d'évaluation.
  - `context-watch` : Diagnostic de l'occupation mémoire et santé contextuelle.

#### [MODIFY] [`src/commands/handlers/analysis.py`](file:///C:/Memory%20Loop/src/commands/handlers/analysis.py)
* Implémentation des handlers CLI associés.

---

### 5. Formalisation SSOT & ADR

#### [NEW] [`docs/01-architecture/ADR-0326_auto_eval_harvesting_context_guard_and_memory_supersession.md`](file:///C:/Memory%20Loop/docs/01-architecture/ADR-0326_auto_eval_harvesting_context_guard_and_memory_supersession.md)
* Consignation formelle des protocoles de moisson d'évals et de gestion de supersession.

---

## 🧪 Plan de Validation & Vérification

### Tests Automatisés
- **Tests unitaires des 3 moteurs** :
  ```bash
  python -m unittest tests/test_eval_harvester.py
  python -m unittest tests/test_context_monitor.py
  python -m unittest tests/test_memory_supersession.py
  ```
- **Validation Globale de la Suite de Tests** :
  ```bash
  python -m unittest discover -s tests -p "test_*.py"
  ```

### Vérification CLI & Auto-Étalonnage
- Exécution de `context-watch` et `eval-harvest` :
  ```bash
  python src/swarm.py context-watch --project mLoop
  python src/swarm.py calibrate --project mLoop
  ```
