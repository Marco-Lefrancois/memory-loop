# 🎨 Archify — Outil de Diagrammes d'Architecture Interactifs

Bienvenue dans le module **Archify** de la boîte à outils **Memory Loop**.

Archify permet aux agents mLoop et aux développeurs de générer des diagrammes d'architecture interactifs au format HTML standalone à partir de spécifications déclaratives JSON IR.

---

## 🌟 Capacités Principales

- 🗺️ **Vues Multiples & Filtrage Dynamique** : Définition de sous-parcours métier (`views`) avec zoom et focus automatique de la caméra.
- ⚡ **Animation de Particules de Flux (`trace`)** : Visualisation des échanges asynchrones et synchrones via des flux de particules le long des arêtes orthogonales.
- 🛡️ **Validation Showcase (9 Contrôles Géométriques)** : Garantie de zéro chevauchement de texte, zéro croisement ambigu de lignes, tracé orthogonal strict et marges de sécurité.
- 📦 **Artefact Standalone Zéro Dépendance** : Fichier `.html` unique (SVG vectoriel natif, CSS/JS embarqués) ouvrable dans tout navigateur.

---

## 🚀 Commandes d'Utilisation

### 1. Via le script outil Python :
```bash
# Valider une spécification JSON IR
python tools/archify/archify_runner.py validate path/to/diagram.architecture.json --quality showcase

# Compiler et générer l'artefact HTML (avec option d'ouverture automatique)
python tools/archify/archify_runner.py deliver path/to/diagram.architecture.json path/to/output.html --quality showcase --open
```

### 2. Via le CLI mLoop Swarm :
```bash
# Valider
python src/swarm.py archify --file path/to/diagram.json --validate

# Compiler en HTML
python src/swarm.py archify --file path/to/diagram.json --output path/to/diagram.html [--open]
```

### 3. Directement via Archify CLI (Node.js) :
```bash
node "$HOME/.agents/skills/archify/bin/archify.mjs" validate architecture diagram.json --quality showcase --json
node "$HOME/.agents/skills/archify/bin/archify.mjs" deliver architecture diagram.json output.html --quality showcase --json
```

---

## 📐 Structure du Schéma JSON IR (`architecture`)

```json
{
  "schema_version": 1,
  "diagram_type": "architecture",
  "meta": {
    "title": "Nom du Système",
    "output": "output.html",
    "visual_preset": "blueprint",
    "animation": "trace",
    "quality_profile": "showcase",
    "views": [
      {
        "id": "view-1",
        "label": "Parcours Nominal",
        "focus": ["node_a", "node_b"],
        "note": "Description du sous-parcours mis en valeur"
      }
    ]
  },
  "components": [
    { "id": "node_a", "type": "frontend", "label": "Client App", "sublabel": "React / Web", "pos": [38, 200], "size": [140, 60], "tag": "web" },
    { "id": "node_b", "type": "backend", "label": "API Gateway", "sublabel": "Express :443", "pos": [260, 200], "size": [140, 60], "tag": "api" }
  ],
  "boundaries": [
    { "kind": "region", "label": "Infrastructure Cloud", "wraps": ["node_a", "node_b"], "pad": 20 }
  ],
  "connections": [
    { "from": "node_a", "to": "node_b", "label": "HTTPS", "variant": "emphasis", "route": "straight" }
  ],
  "cards": [
    { "dot": "cyan", "title": "Règles Métier", "items": ["Authentification requise", "Chiffrement TLS 1.3"] }
  ]
}
```

---

## 📂 Galerie de Démonstration (Showcase)

Retrouvez tous les diagrammes interactifs prêts pour présentation sous [`tools/archify/showcase/`](showcase/README.md) :
- 🧠 **Framework mLoop** : [`tools/archify/showcase/mloop-framework.architecture.html`](showcase/mloop-framework.architecture.html)
- 🏗️ **Metro Food (5 Couches .NET)** : [`tools/archify/showcase/metro-food-layers.architecture.html`](showcase/metro-food-layers.architecture.html)
- ⚡ **Metro Food (Séquence Runtime)** : [`tools/archify/showcase/metro-food-sequence.sequence.html`](showcase/metro-food-sequence.sequence.html)
- 📱 **Metro Food (Multi-Bannières & API)** : [`tools/archify/showcase/metro-food.architecture.html`](showcase/metro-food.architecture.html)
- 🥚 **Boire & Frères (Noyau Couvoir Dataverse)** : [`tools/archify/showcase/boirefrere-couvoir.architecture.html`](showcase/boirefrere-couvoir.architecture.html)
