# ADR-0311 : Optimisation et Gouvernance Avancée d'OpenCode (`opencode.json`)

## Statut
**Accepté** (Alignement avec la Spécification Officielle OpenCode 2026 `opencode.ai/docs/fr/`)

---

## 1. Contexte & Problématique

L'audit approfondi de la documentation officielle **OpenCode** (`https://opencode.ai/docs/fr/`) à travers ses 4 rubriques majeures (*Introduction*, *Utilisation*, *Configuration*, *Développement*) met en évidence des capacités natives de contrôle d'accès, d'élagage du watcher et de duologie de modèles.

Sans ces optimisations natifs :
1. Chaque sous-commande CLI mLoop (`python src/swarm.py *`) déclenchait des interruptions manuelles ou requérait une approbation aveugle.
2. La surveillance en arrière-plan de gros répertoires de cache (Crawler Web, Sessions) ralentissait la réactivité de l'interface TUI.
3. Les sous-agents n'étaient pas filtrés par permission de tâche (`permission.task`).

---

## 2. Décisions d'Architecture

### 2.1. Auto-Approbation Sécurisée par Pattern (`permission.bash`)
Nous activons le filtrage par pattern glob pour le moteur Bash. Toutes les sous-commandes de la CLI backbone mLoop (`python src/swarm.py *`) ainsi que les commandes de contrôle Git de routine (`git status`, `git diff`) sont automatiquement autorisées sans interruption de flux :
```json
"permission": {
  "edit": "allow",
  "read": "allow",
  "bash": {
    "*": "ask",
    "python src/swarm.py *": "allow",
    "git status *": "allow",
    "git diff *": "allow"
  },
  "webfetch": "allow",
  "websearch": "allow"
}
```

### 2.2. Contrôle de Délégation de Sous-Agents (`permission.task`)
Nous encadrons le droit d'appel des sous-agents par les agents primaires. L'`orchestrator` et `plan` peuvent appeler `sentinel` (revue contradictoire Read-Only) et `explore` (navigation rapide), tout en bloquant l'invocation d'agents non autorisés :
```json
"permission": {
  "task": {
    "*": "deny",
    "sentinel": "allow",
    "explore": "allow",
    "scout": "allow"
  }
}
```

### 2.3. Exclusion Étendue dans le Watcher (`watcher.ignore`)
Nous excluons les répertoires de cache temporaire pour éliminer toute latence du TUI/IDE lors des moissonnages web ou de la synchronisation :
```json
"watcher": {
  "ignore": [
    "node_modules/**",
    "dist/**",
    ".git/**",
    "tmp/**",
    "graphify-out/**",
    "memory/crawler/cache/**",
    "memory/sessions/**",
    "**/*.svg"
  ]
}
```

### 2.4. Duologie de Modèles (`model` & `small_model`)
Nous combinons le modèle principal de raisonnement (`gemini-3-flash-preview-thinking`) avec un modèle secondaire ultra-rapide (`gemini-3.1-flash-lite`) pour les tâches auxiliaires.

---

## 3. Conséquences

- **Performance TUI/IDE** : Suppression de la latence de saisie grâce à l'exclusion du cache du crawler web.
- **Fluidité CLI mLoop** : Exécution fluide et continue des routines `swarm.py` sans fenêtres modales répétitives d'approbation.
- **Gouvernance & Sécurité** : Encadrement des sous-agents via `permission.task`.
