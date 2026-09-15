# CHANGELOG — 15 septembre 2026
**Session** : Analyse et intégration symbiotique de l'écosystème Matt Pocock dans Memory Loop (mLoop)  
**Opérateur** : mLoop Swarm + Co-Architecte Agentique  
**Validation** : 12/12 composants valides · 16:46 EST

---

## Contexte de la Session

Suite à l'analyse approfondie de l'écosystème GitHub de **Matt Pocock** via le mLoop Smart Crawler
(dépôt `mattpocock/skills` : 262 768 ⭐, PR #1083 du 15/09/2026 : *Push toward deterministic checks*),
ce changelog documente l'intégration des innovations les plus impactantes dans mLoop.

---

## Nouveaux Fichiers

### `src/pipelines/deterministic_checks.py` ✅ NOUVEAU
**Composant** : Moteur de vérifications déterministes (Rétrospective PR #1083)  
**Fonctions** :
- `classify_anomaly(msg)` → Classifie chaque anomalie en `MECHANICAL` ou `JUDGEMENT`
- `check_no_placeholders(code, is_file)` → Détecte les `# TODO`, `# FIXME`, ellipses interdits
- `check_focus_lock(story_id)` → Valide le verrouillage de story active (RHO-001 déterministe)
- `check_python_deep_module_boundaries(file, base_dir)` → Audit AST des frontières d'encapsulation (Deep Modules)

**Raison d'être** : Remplace les consignes textuelles fragiles de `rho_rules.yaml` par des assertions
mécaniques inviolables, conformément au principe fondateur de Matt Pocock :
> *« Default to building the check over writing the rule. »*

---

### `src/pipelines/task_graph.py` ✅ NOUVEAU
**Composant** : Modélisation DAG et calcul de la Frontier Herdr (inspiré de `implement-spec`)  
**Classes/Fonctions** :
- `TaskGraph(project_path)` → Parse les stories, extrait les clauses `Blocked-By: US-XXX`
- `graph.get_frontier()` → Retourne les stories non bloquées dont tous les prérequis sont `DONE`
- `get_ready_frontier(project_path)` → Fonction utilitaire autonome

**Raison d'être** : Permet à l'orchestrateur Herdr de déployer des workers en parallèle sur les
tâches réellement disponibles plutôt que séquentiellement.

---

### `standards/protocols/DECISION_BRIEF_GUIDE.md` ✅ NOUVEAU
**Composant** : Norme d'interaction Système 2 (Protocole Push-Right, inspiré de `loop-me`)  
**Contenu** : Doctrine Push-Right, anatomie obligatoire d'un Decision Brief en 5 points,
matrice d'évaluation de conformité avec Red Flags explicites.

**Raison d'être** : Ne jamais soumettre d'ébauche brute ou de question floue à l'opérateur humain ;
repousser les checkpoints au maximum et ne présenter que des synthèses actionnables.

---

### `standards/linters/deterministic_rules.json` ✅ NOUVEAU (généré)
**Composant** : Registre JSON des règles d'audit déterministes (alternative mécanique à rho_rules.yaml)  
**Contenu** : Règles de type `no_placeholders`, `focus_lock`, `deep_module_boundaries` avec
horodatage, scope et statut `ACTIVE_DETERMINISTIC`.

---

### `tests/test_crawler_github_tree.py` ✅ NOUVEAU
**2 tests** : Priorisation Tier-1 SKILL.md et protection multi-tenant llms.txt

### `tests/test_rho_deterministic.py` ✅ NOUVEAU
**4 tests** : Classifieur, check_no_placeholders, check_focus_lock, bifurcation optimize_rho

### `tests/test_task_graph_frontier.py` ✅ NOUVEAU
**1 test** : Calcul DAG complet avec 4 stories et dépendances croisées

---

## Fichiers Modifiés

### `src/pipelines/crawler.py` ✅ MODIFIE (+27 lignes)
- **Paramètre `max_github_files`** (défaut : 60, anciennement 30 en dur) : Quota paramétrable
- **Stratégie 2 étages (Tier-1 / Tier-2)** dans `_fetch_github_repo_tree` :
  - Tier-1 (priorité absolue) : `SKILL.md`, `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `package.json`, etc.
  - Tier-2 (quota résiduel) : `docs/**/*.md`, `research/**`, `README.md`
- **Protection multi-tenant renforcée** dans `_fetch_llms_txt` :
  - Ajout de `www.github.com` à la liste d'exclusion
  - Ajout du filtre dynamique `any(domain in netloc)` pour toutes les variantes GitHub/GitLab

### `src/pipelines/rho_optimizer.py` ✅ MODIFIE (+36 lignes)
- **Classifieur d'anomalies ajouté en Step 0** de `optimize_rho()` :
  - Si `MECHANICAL` → Enregistrement dans `standards/linters/deterministic_rules.json`
    (zéro pollution de `rho_rules.yaml`, zéro inflation de contexte LLM)
  - Si `JUDGEMENT` → Comportement classique inchangé (rho_rules.yaml)
- Rétrocompatibilité totale : signature de `optimize_rho()` inchangée

### `src/pipelines/worker_pipeline.py` ✅ MODIFIE (+40 lignes)
- **`run_frontier_autospawn(project_name, max_concurrent, dry_run)`** : Nouvelle fonction
  calculant la Frontier via `TaskGraph` et déployant les workers Herdr sur les stories débloquées
- Supporte le mode `dry_run=True` pour simuler sans spawner

### `src/commands/handlers/pipeline.py` ✅ MODIFIE (+1 ligne)
- Propagation du paramètre `--max-github-files` vers `WebCrawlerAgent(max_github_files=...)`

---

## Résultats de Validation

| Composant | Type | Statut | Preuve |
| :--- | :--- | :---: | :--- |
| `deterministic_checks.py` | NOUVEAU | ✅ | 4 fonctions, 7 assertions, scan AST réel |
| `task_graph.py` | NOUVEAU | ✅ | DAG 4 stories, frontier [US-002, US-004] |
| `DECISION_BRIEF_GUIDE.md` | NOUVEAU | ✅ | Push-Right + 5-points + Blast Radius |
| `deterministic_rules.json` | NOUVEAU | ✅ | Règles MECHANICAL enregistrées sur disque |
| `test_crawler_github_tree.py` | NOUVEAU | ✅ | 2 tests collectés |
| `test_rho_deterministic.py` | NOUVEAU | ✅ | 4 tests collectés |
| `test_task_graph_frontier.py` | NOUVEAU | ✅ | 1 test collecté |
| `crawler.py` | MODIFIE | ✅ | max_github_files=60, tier1/tier2, multi-tenant |
| `rho_optimizer.py` | MODIFIE | ✅ | Bifurcation mécanique vers linters JSON |
| `worker_pipeline.py` | MODIFIE | ✅ | run_frontier_autospawn dry_run OK |
| `pipeline.py` | MODIFIE | ✅ | max_github_files propagé au constructeur |
| **pytest** (18 tests) | SUITE | ✅ | 18 passed · 0 failed |
