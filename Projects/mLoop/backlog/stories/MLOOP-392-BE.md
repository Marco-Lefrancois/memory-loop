---
id: MLOOP-392-BE
jira_key: ''
epic_key: EPIC-36-HERDR-WORKER-PERMISSIONS-AND-RUNTIME-GOVERNANCE
type: Feature
title: Extension Multi-Runtimes Déclarative Herdr (Claude Code, Gemini CLI, Cursor
  CLI, Codex)
tags:
- herdr
- worker-runtimes
- multi-agents
- claude-code
- gemini-cli
- cursor-cli
- delegation
status: READY_FOR_QA
layer: backend
invest_score: 6/6
macrostructure: workbench
validated_by: Marco
validated_at: '2026-09-25T21:29:50.000000+00:00'
ttl_cycles: 2
---
# Extension Multi-Runtimes Déclarative Herdr (Claude Code, Gemini CLI, Cursor CLI, Codex)

---

## Description
**En tant qu'** Architecte de délégation agentique et développeur mLoop,  
**je veux** étendre le registre `WORKER_RUNTIMES` avec des spécifications déclaratives pour les agents CLI leaders (Claude Code, Gemini CLI, Cursor CLI, Codex),  
**afin d'** orchestrer des missions distribuées sur une flotte hétérogène d'outils et de modèles sans modifier le cœur de spawn de Herdr ni compromettre l'autonomie des sessions PTY.

---

## Contexte & Périmètre

### Contexte Métier
L'architecture de délégation dual-track (ADR-0346) et les standards d'intégration de runtimes aval (ADR-0377, ADR-0396) prévoient que mLoop puisse assigner des tâches spécialisées à une multiplicité de harnais d'exécution en fonction de leurs forces respectives (ex. Claude Code pour le refactoring architectural lourd, Gemini CLI pour les contextes massifs, Cursor CLI pour l'alignement IDE, OpenCode/Cline pour le dev autonome standard).  
Actuellement, le registre déclaratif `WORKER_RUNTIMES` de `src/core/worker_runtimes.py` ne couvre pleinement que `opencode` et `cline`. Pour concrétiser la vision multi-runtimes sans introduire de dette technique ni de logique conditionnelle dispersée, ce récit enrichit le registre central avec les spécifications normatives de chaque nouvel agent cible (drapeaux d'auto-approbation, résolution binaire Windows, modèle par défaut).

### In-Scope
- Ajout des spécifications déclaratives `WorkerRuntimeSpec` dans `src/core/worker_runtimes.py` pour :
  - `claude` (Anthropic Claude Code) : drapeaux d'auto-approbation `["--dangerously-skip-permissions"]`, résolution binaire npm/native sous Windows (`_resolve_npm_windows_binary`), modèle par défaut non contraint (`default_model=None`).
  - `gemini` (Google Gemini CLI) : drapeaux d'exécution non-interactive `["--auto-approve"]`, résolution binaire Windows (`_resolve_npm_windows_binary`), modèle par défaut non contraint (`default_model=None`).
  - `cursor` (Cursor Agent CLI / headless mode) : drapeaux de session autonome, résolution binaire Windows (`_resolve_npm_windows_binary`), modèle par défaut non contraint (`default_model=None`).
  - `codex` / `aider` : drapeaux d'auto-commit et de non-confirmation d'édition `["--yes-always"]`, résolution binaire Windows (`_resolve_npm_windows_binary`), modèle par défaut non contraint.
- Standardisation de la résolution des binaires sous Windows 11 : utilisation systématique de `_resolve_npm_windows_binary` pour chaque runtime afin d'éliminer le piège Win32 (« %1 n'est pas une application Win32 valide ») en déclenchant automatiquement le fallback sécurisé `pane run` PowerShell `& "<chemin>"` lorsque le binaire est un shim `.cmd` ou `.ps1`.
- Couverture de tests unitaires exhaustive dans `tests/test_worker_runtimes.py` validant la construction des drapeaux, l'enregistrement des kinds et la détection du fallback pour chaque nouveau runtime.
- Maintien rigoureux du plafond modulaire de 300 lignes sur `src/core/worker_runtimes.py` (ADR-0202).

### Out-of-Scope
- Recompilation ou modification du code binaire de `herdr.exe` (gestion par émulation et flags CLI).
- Implémentation de pipelines de spécialisation de tâches (gérés dans l'épopée EPIC-35 / handoff multi-harnais).
- Migration des fichiers de configuration projet (couvert par `MLOOP-390-BE`).
- Audit continu Vibe-Check (couvert par `MLOOP-391-BE`).

---

## Critères d'acceptation

### Opérations Métier & Logique Backend

#### 1. Déclaration Normalisée des Nouveaux Runtimes
* **Entrée Métier** : Identifiant de kind (`claude`, `gemini`, `cursor`, `codex`).
* **Règles d'admissibilité & Validation** :
  - Chaque runtime doit exposer une instance `WorkerRuntimeSpec` immuable (`frozen=True`).
  - Les drapeaux `one_shot_flags` doivent garantir une exécution 100% autonome sans attente d'interaction humaine.
  - La fonction de résolution sous Windows doit gérer gracieusement la présence ou l'absence du binaire sur la machine hôte sans lever d'exception bloquante lors de la simple lecture du registre.
  - Si aucun modèle explicite n'est passé à `build_flags`, le comportement natif de chaque CLI prévaut (`default_model=None`).
* **Résultat Métier** : La méthode `get_worker_runtime(kind)` retourne la spécification complète et valide la construction de la ligne de commande.
* **Cas de Rejet** : Tout identifiant inconnu lève une `KeyError` explicite listant l'intégralité des runtimes supportés.

#### 2. Robustesse d'Instanciation sous Windows
* **Entrée Métier** : Exécution sur système d'exploitation Windows 11 avec présence de shims npm ou de binaires natifs.
* **Règles d'admissibilité & Validation** :
  - Si un runtime est installé sous forme de script `.cmd` ou `.ps1`, la méthode `needs_pane_run_fallback()` doit renvoyer `True` pour router l'exécution vers le mécanisme de fallback sécurisé de Herdr.
  - Si un binaire exécutable `.exe` direct est localisé, le lancement direct est privilégié.
* **Résultat Métier** : Aucun worker fantôme (*zombie process*) n'est généré suite à une erreur de sous-système Win32.

---

## Parcours Interactif & API

### Contrats d'Échange API (Backend / Services)
* **Accès Registre** : `get_worker_runtime(kind: str) -> WorkerRuntimeSpec`
* **Génération de Commande** : `spec.build_flags(model: Optional[str] = None, extra_args: Optional[List[str]] = None) -> List[str]`
* **Détection Fallback PTY** : `spec.needs_pane_run_fallback() -> bool`

### Matrice des Contrats API
| Méthode | Route / Point d'Entrée | Finalité | Contrat |
| :--- | :--- | :--- | :--- |
| `get_worker_runtime` | `src.core.worker_runtimes:get_worker_runtime` | Accès au registre des runtimes | `(kind: str) -> WorkerRuntimeSpec` |
| `build_flags` | `WorkerRuntimeSpec.build_flags` | Génération de commande CLI | `(model: Optional[str], extra_args: Optional[List[str]]) -> List[str]` |
| `needs_pane_run_fallback` | `WorkerRuntimeSpec.needs_pane_run_fallback` | Détection fallback PTY Windows | `() -> bool` |

> OQ-392-1 : Ce récit définit des fonctions Python internes (module `src.core.worker_runtimes`), pas des endpoints HTTP/REST. La "Route / Point d'Entrée" référence le chemin de module Python qualifié (`module:function`), conforme au standard Zéro Fausse Route (ADR-0319) pour les APIs internes. **[API de soumission à définir]** — Aucune route HTTP/REST n'est exposée par ce module.

## Règles d'affaires

- **Architecture Déclarative Pure** : Aucune logique conditionnelle propre à un outil (`if kind == "claude"`) ne doit être injectée dans `HerdrWorkerMixin` ou dans les gestionnaires de commandes.
- **Principe d'Auto-Suffisance** : Chaque spécification de runtime doit contenir toutes les métadonnées nécessaires à son exécution sécurisée en environnement PTY sans nécessiter de configuration externe préalable.
- **Préservation de la Modularité** : La taille du fichier `worker_runtimes.py` doit demeurer largement inférieure à 300 lignes après l'ajout des nouveaux runtimes.

---

## Scénarios de test (4 Piliers Gherkin)

### Pilier 1 : Scénario Nominal (Instanciation d'un Worker Claude Code Auto-Approuvé)
* **GIVEN** Une demande de délégation vers le runtime `kind="claude"`.
* **WHEN** Le registre `WORKER_RUNTIMES` compile les drapeaux d'exécution.
* **THEN** La commande générée inclut le drapeau `"--dangerously-skip-permissions"`.
* **AND** Aucun modèle forcé n'est injecté si aucun argument `--model` n'a été spécifié.

### Pilier 2 : Scénario d'Exception (Kind Non Enregistré ou Typo)
* **GIVEN** Une tentative d'instanciation avec un identifiant invalide `kind="inconnu"`.
* **WHEN** La fonction `get_worker_runtime` est sollicitée.
* **THEN** Une `KeyError` est levée avec un message listant explicitement tous les runtimes valides (`claude`, `cline`, `codex`, `cursor`, `gemini`, `opencode`, etc.).

### Pilier 3 : Scénario de Résilience (Détection Correcte de Shim npm Windows)
* **GIVEN** Un environnement où le CLI `claude` est installé sous la forme d'un fichier `claude.cmd` dans `$APPDATA/npm`.
* **WHEN** La méthode `needs_pane_run_fallback` est interrogée sur la spécification du runtime.
* **THEN** La méthode retourne `True`, garantissant que le spawn Herdr utilise la syntaxe d'appel PowerShell sécurisée.
* **AND** Aucun plantage `%1 n'est pas une application Win32 valide` ne survient.

### Pilier 4 : Scénario UX & Observabilité (Rapport Exhaustif des Runtimes Disponibles)
* **GIVEN** Un développeur consultant la liste des runtimes enregistrés dans mLoop.
* **WHEN** La commande d'inspection du registre des workers est invoquée.
* **THEN** L'ensemble des 6 runtimes (`opencode`, `cline`, `claude`, `gemini`, `cursor`, `codex`) apparaît avec leurs drapeaux d'auto-approbation associés.

---

## Références

### 1. Décisions d'Architecture SSOT
- 🏛️ **ADR Fondateur** : [`standards/adr-system/0389-worker-permissions-zero-blindspot.md`](../../../../standards/adr-system/0389-worker-permissions-zero-blindspot.md)
- 🏛️ **ADR Runtimes Aval** : [`ADR-0377`](../../../../standards/adr-system/0377-runtimes-agents-aval-et-herdr-operationnels.md)
- 🏛️ **ADR Délégation Spécialisée** : [`ADR-0346`](../../../../standards/adr-system/0346-specialized-agent-delegation-gates.md)
- 🏛️ **ADR Modularité** : [`ADR-0202`](../../../../standards/adr-system/0202-modularite-interne-agents.md)
- 📐 **Dossier de Preuves Factuelles** : [`memory/evidence/MLOOP-392-BE_fact_dossier.md`](../../memory/evidence/MLOOP-392-BE_fact_dossier.md)
