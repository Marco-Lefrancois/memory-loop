---
name: visual-mermaid
description: Génération de diagrammes Mermaid professionnels pour Obsidian avec thème moderne, directives graphiques et moteur anti-erreurs de parsing (ADR-0337).
disable-model-invocation: true
---

# 📊 Visual Mermaid (Moteur de Visualisation & Anti-Crash)

**Règle d'or :** Transformer les flux, architectures, machines à états et séquences réseau en diagrammes Mermaid d'une lisibilité maximale, tout en appliquant **100% des règles d'échappement anti-crash** pour garantir un rendu parfait dans Obsidian, GitHub et les visionneuses Markdown.

---

## ⚡ Quand l'utiliser (*When to Use*)
- Visualisation de flux métier, architectures de micro-services, arbres de décision et pipelines d'agents.
- Documentation des contrats d'API et interactions réseau sous forme de diagrammes de séquence (`sequenceDiagram`).
- Cycle de vie et transitions de statut sous forme de diagrammes d'états (`stateDiagram-v2`).
- Modélisation de domaines ou décompositions fonctionnelles hiérarchiques sous forme de Mindmap (`mindmap`).

## 🚫 Quand NE PAS l'utiliser (*When NOT to Use*)
- Schémas spatiaux infinis ou libres avec regroupements 2D complexes (utiliser `obsidian-canvas` ou `visual-excalidraw`).
- Simples listes de 2 ou 3 étapes linéaires sans embranchement (un simple format de texte clair suffit).

---

## 🛡️ Règles Critiques Anti-Crash (Zero-Error Mermaid)

1. **Règle Anti-Collision de Liste Ordonnée (Erreur #1)** :
   - ❌ **Interdit** : `[1. Action]`, `[2. Traitement]` (provoque le crash `Parse error: Unsupported markdown: list`).
   - ✅ **Obligatoire** : `[① Action]` (chiffres cerclés), `[1.Action]` (sans espace), ou `[Étape 1 : Action]`.
   - *Référence de chiffres cerclés* : `① ② ③ ④ ⑤ ⑥ ⑦ ⑧ ⑨ ⑩ ⑪ ⑫ ⑬ ⑭ ⑮ ⑯ ⑰ ⑱ ⑲ ⑳`
2. **Règle de Nommage des Sous-Graphes (Subgraphs)** :
   - ❌ **Interdit** : `subgraph Couche API` (espace dans le nom sans ID).
   - ✅ **Obligatoire** : `subgraph api["🌐 Couche API Backend"]` et référencement par ID (`client --> api`).
3. **Règle d'Échappement des Nœuds & Libellés** :
   - Toujours encadrer les labels comportant parenthèses, crochets ou ponctuations par des guillemets : `A["Nom du Service (v2.1)"]`.
   - Toujours référencer les flèches via les IDs de nœuds (`A --> B`) et jamais par le texte d'affichage.

---

## 🎨 Gabarits Standards Prêts à l'Emploi

### 1. Flux de Processus & Architecture Déclarative (graph TD / LR)
```mermaid
%%{init: {'theme': 'base', 'themeVariables': { 'primaryColor': '#1e293b', 'primaryTextColor': '#f8fafc', 'primaryBorderColor': '#38bdf8', 'lineColor': '#94a3b8', 'secondaryColor': '#0f172a', 'tertiaryColor': '#1e1e2e'}}}%%
flowchart TD
    subgraph fe["📱 Frontend (UI / MAUI)"]
        UI_A["Écran d'Accueil"] -->|① Clic Action| UI_B["Validation Locale"]
    end

    subgraph be["🌐 Backend (Services API)"]
        API_A["Endpoint /api/v1/resource"] -->|② Traitement| DB[(Base de Données)]
    end

    UI_B -->|③ Requête HTTPS| API_A
    API_A -->|④ Réponse 200 OK| UI_B
```

### 2. Diagramme de Séquence API & Interception
```mermaid
sequenceDiagram
    autonumber
    actor User as 👤 Utilisateur
    participant UI as 📱 Interface UI
    participant API as 🌐 Passerelle API
    participant Core as ⚙️ Service Métier

    User->>UI: Déclenche l'action
    UI->>API: POST /api/v1/resource (Payload JSON)
    activate API
    API->>Core: Validation & Règle Métier
    Core-->>API: Résultat Validé
    API-->>UI: 200 OK (Données Traitées)
    deactivate API
    UI-->>User: Toast Vert & Rafraîchissement
```

### 3. Diagramme d'États & Cycle de Vie
```mermaid
stateDiagram-v2
    [*] --> OPEN: Création du récit
    OPEN --> IN_ANALYZE: Prise en charge IA
    IN_ANALYZE --> READY_FOR_GROOMING: 4 Piliers Gherkin rédigés
    READY_FOR_GROOMING --> READY_FOR_DEV: Revue PO Validée
    READY_FOR_DEV --> CLOSED: Implémentation livrée
    READY_FOR_DEV --> ON_HOLD: Blocage technique
    ON_HOLD --> READY_FOR_DEV: Arbitrage résolu
```
