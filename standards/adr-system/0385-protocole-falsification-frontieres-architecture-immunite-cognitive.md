# 🏛️ ADR-0385 : Protocole de Falsification des Frontières d'Architecture, Étalonnage de Confiance & Immunité Cognitive aux Heuristiques d'Outils

- **Statut** : ACCEPTED
- **Date** : 23 septembre 2026
- **Décideurs** : Marco (Utilisateur) & Antigravity (Agentic Architect)
- **En lien avec** : ADR-0204 (Dual Engine Graph Architecture), ADR-0320 (Grill-Me Frontier Design), ADR-0363 (Hygiène CodeGraph & Graphify), ADR-0375 (Cycle de vie 5 Phases), ADR-0376 (Standard Rigueur 360° Zéro Blindspot), ADR-0379 (StandardsGraph)

---

## 1. Contexte & Défaillances Constatées

Lors de la qualification d'architecture du backlog d'initiatives client Metro FOOD (chantier *Papercuts* en Phase 2 PLAN/ANALYSE), une défaillance critique d'analyse a failli contaminer les livrables d'arbitrage stratégique présentés en comité de direction :

1. **L'initiative composite** : Le besoin client demandait : *« Supprimer le overlay du code postal au click sur panier - Faire en sorte que l'utilisateur sélectionne un magasin lorsqu'il arrive sur le site »*.
2. **Le faux diagnostic** : L'agent a classé l'ensemble sous l'étiquette `L6` en tant que **Quick-Win Natif 🟢** (faisabilité totale sous 2 jours par l'équipe mobile).
3. **La réalité technique du terrain** : L'overlay de code postal au clic panier est rendu à 100 % dans une **WebView externe Tink** (`mon-panier`, `WebViewEnum.Cart`), hébergée sur des serveurs web propriétaires tiers, totalement inaccessible au code C# MAUI de l'application mobile. Le promettre en quick-win natif constituait une faute d'ingénierie majeure discréditant l'équipe en atelier client.

L'autopsie cognitive de l'incident a mis en lumière **trois pathologies systémiques** de l'interaction agentique :

### A. L'hallucination d'impuissance (Prompt-induced Self-Censorship)
L'outil MCP `codegraph_explore` émet en pied de réponse une note ergonomique incitative basée sur le nombre de fichiers indexés :  
> `> **Explore budget: 3 calls for this project (6,216 files indexed).** ... Synthesize once you've used 3.`  

L'agent a sur-interprété cette simple recommandation consultative comme un **quota technique bloquant du serveur MCP**. Arrivé à 3 appels, il a conclu que son budget était « épuisé (3/3) », s'est auto-censuré et s'est interdit d'utiliser l'outil pour le reste de la session sans jamais effectuer d'appel d'épreuve.

### B. Le biais de confirmation lexicale (Grep vs Call-Tree)
S'estimant privé de son outil relationnel (CodeGraph), l'agent s'est rabattu sur la recherche textuelle (`Grep`). Trouvant la méthode C# `SetContextStoreAsync` dans le code mobile, il a opéré un raccourci sémantique par confirmation : *« Le code C# existe, il parle de store et de code postal, donc l'overlay est natif »*. Il a substitué la recherche d'arêtes d'appels réelles (qui déclenche quoi) par une simple présence de chaîne de caractères.

### C. L'asymétrie de certitude & l'alibi de l'outil
L'agent a attribué un statut de confiance maximale (**🟢 Certifié / Quick-Win**) sur la base d'une preuve épistémique dégradée au niveau le plus bas (occurrence lexicale isolée), sans déclarer son incertitude ni mentionner son mode dégradé. Une fois l'erreur relevée par la mémoire humaine, l'agent a rationalisé son raccourci en le justifiant par la perte de son outil structurel plutôt que par son absence de falsification.

---

## 2. Principes Directeurs & Décision Retenue

Pour éliminer définitivement cette classe de faux positifs et immuniser les agents du framework mLoop, quatre piliers constitutionnels sont adoptés.

```
       ┌──────────────────────────────────────────────────────────────┐
       │                PROTOCOLE DE FALSIFICATION                    │
       │                   DES FRONTIÈRES (ADR-0385)                   │
       └──────────────────────────────┬───────────────────────────────┘
                                      │
        ┌─────────────────────────────┼─────────────────────────────┐
        ▼                             ▼                             ▼
┌───────────────┐             ┌───────────────┐             ┌───────────────┐
│  PILIER 1     │             │  PILIER 2     │             │  PILIER 3     │
│ Falsification │             │ Échelle de    │             │ Découplage    │
│  Poppérienne  │             │ Preuve & Conf.│             │ Symptôme /    │
│  Obligatoire  │             │ à 3 Niveaux   │             │ Levier        │
└───────┬───────┘             └───────┬───────┘             └───────┬───────┘
        │                             │                             │
        └─────────────────────────────┼─────────────────────────────┘
                                      ▼
                        ┌───────────────────────────┐
                        │        PILIER 4           │
                        │    Immunité Cognitive     │
                        │    aux Heuristiques       │
                        └───────────────────────────┘
```

---

### 1. Pilier 1 — Inversion de la Charge de la Preuve (Popperian Falsification Gate)

Il est formellement interdit à un agent d'argumenter la faisabilité d'une initiative par **accumulation de preuves positives d'existence**.

* **Règle** : Pour qu'un composant, écran ou comportement soit qualifié de modifiable / autonome / natif (`🟢`), l'agent doit obligatoirement formaliser une **tentative de falsification** :
  1. *Test de rupture de runtime* : Le flux d'exécution traverse-t-il une WebView (`WebViewEnum`, `IWebViewService`), un iframe ou un shell tiers ?
  2. *Test de rupture de données* : Le flux dépend-il d'un endpoint inexistant, d'un contrat en lecture seule ou d'un service back-end non déployé ?
  3. *Test de souveraineté d'équipe* : Le code source visé appartient-il au repository de l'équipe exécutante ou à une dépendance propriétaire externe ?
* **Critère de passage** : Un item n'obtient la pastille `🟢` que s'il a **survécu à l'épreuve de falsification**. S'il échoue à l'un de ces tests, il est obligatoirement classé en `🔴 Externe / Dépendance` ou `🟡 Conditionnel`.

---

### 2. Pilier 2 — Échelle de Preuve à Trois Niveaux & Étalonnage de Confiance

L'attribution d'un statut dans les matrices d'architecture et les récits dépend strictement du **niveau de fidélité de la méthode de vérification** mobilisée :

| Niveau | Méthode de Preuve | Nature de la Preuve | Statut Maximal Autorisé | Seuil de Confiance |
| :---: | :--- | :--- | :---: | :---: |
| **Niveau 1** | **Lexicale** (`Grep`, `find`, regex) | Présence textuelle d'un mot-clé ou identifiant dans un fichier | **🟡 Candidat Présumé** | $\le 40\%$ (Non opposable en Gate 2 / DoR) |
| **Niveau 2** | **Structurelle / AST** (`CodeGraph`, Call-Tree, XAML binding) | Arête relationnelle prouvée reliant le déclencheur UI à la routine métier | **🟢 Qualifié / Robuste** | $\ge 85\%$ (Requis pour Gate 2 / DoR) |
| **Niveau 3** | **Dynamique / Exécutoire** (Test d'intégration, trace runtime) | Validation du comportement en exécution réelle ou mock de contrat | **✅ Certifié / Prouvé** | $100\%$ (Requis pour Gate 4 / DoD) |

> [!IMPORTANT]
> **Interdiction de Sur-Certitude** : Aucun livrable d'architecture ne peut attribuer un statut `🟢 Quick-Win` ou `🟢 Faisabilité Validée` si la méthode de preuve renseignée est de Niveau 1 (Lexicale). Tout rapport enfreignant cette règle est rejeté par Sentinel.

---

### 3. Pilier 3 — Découplage Systémique « Symptôme UI » vs « Levier Technique »

Toute exigence ou irritant formulé sous forme mixte (combinant un désagrément perçu et une solution présumée) doit être **immédiatement décomposé en sous-initiatives atomiques** avant toute qualification :

* **L'Entité Symptôme (`-sym`)** : L'écran ou l'état où l'irritant se manifeste (ex. `L6-cp` : l'overlay de code postal dans le panier).  
  *Audit de frontière* : Où vit cet écran ? ➔ WebView Tink ➔ Verdict : **🔴 Non modifiable**.
* **L'Entité Levier (`-lev`)** : Le mécanisme technique proposé pour agir (ex. `L6-flow` : inviter au choix du magasin dès la 1ʳᵉ visite).  
  *Audit de frontière* : Où vit ce flow ? ➔ `StoreSelectionPage` MAUI natif ➔ Verdict : **🟢 Modifiable**.
* **L'Arête de Contournement** : Formaliser explicitement que le levier ne supprime pas l'overlay web directement, mais en neutralise le déclenchement en amont par pré-conditionnement de session.

---

### 4. Pilier 4 — Immunité Cognitive aux Heuristiques d'Outils (Anti-Self-Censorship)

Pour empêcher l'auto-censure des agents face aux prompts des outils tiers :

1. **Règle d'inviolabilité des outils** : Les messages d'aide, conseils ergonomiques ou compteurs indicatifs retournés par un outil (ex: `Explore budget: X calls`, `Synthesize once used`) sont des suggestions consultatives, **jamais des verrous système**.
2. **Appel d'épreuve obligatoire** : Un agent a l'interdiction formelle de déclarer un outil « épuisé », « verrouillé » ou « indisponible » sans avoir soumis un appel d'épreuve réel retournant un code d'erreur explicite (HTTP 429, Timeout, Crash, Exception bloquante).
3. **Signalement du mode dégradé** : Si un outil primaire devient réellement indisponible, l'agent doit émettre un avertissement explicite à l'utilisateur (`MODE_DÉGRADÉ_DÉCLARÉ`) et abaisser immédiatement la certitude de toutes ses déductions au Niveau 1 (🟡).

---

## 3. Matrice de Traçabilité dans les Backlogs

Les matrices de backlog d'initiatives (ex: `backlog-initiatives-papercuts.md`) doivent intégrer obligatoirement les champs d'opposabilité suivants :

```markdown
| ID | Initiative | Nature | Faisabilité | Méthode de Preuve | Trace Arête / Contrat | Falsification Tentée |
| :--- | :--- | :---: | :---: | :--- | :--- | :--- |
| **L6-cp** | Overlay panier | 🔴 | ❌ | Niveau 2 (CodeGraph) | `Tap Cart -> WebViewService.GetCartWebViewAsync` | Prouvé 100% WebView Tink |
| **L6-flow**| Magasin 1re visite | 🟢 | ✅ | Niveau 2 (CodeGraph) | `StoreSelectionPage -> SetContextStoreAsync` | Aucune dépendance WebView |
```

---

## 4. Conséquences

### Positives
* **Fiabilité Absolue des Arbitrages Client** : Fin des promesses de quick-wins impossibles lors des comités de direction ou ateliers d'arbitrage.
* **Résilience Cognitive des Agents** : Éradication de l'auto-censure induite par les sorties textuelles des serveurs MCP.
* **Transparence Épistémique** : L'humain et Sentinel distinguent immédiatement une affirmation certifiée par un call-tree d'une simple hypothèse lexicale.

### Négatives / Coûts
* Exige des agents une rigueur d'exploration supérieure (obligation de tracer la chaîne d'appel complète avant de clore un statut).
* Nécessite la mise à jour des templates de backlog et du protocole de faits mLoop.

---

## 5. Validation & Références

- **Incident de Référence** : `Projects/Metro_FOOD/docs/PAPERCUTS/01-architecture/constat-technique-webview-natif.md`
- **Implémentation CodeGraph** : `@colbymchenry/codegraph/node_modules/@colbymchenry/codegraph-win32-x64/lib/dist/mcp/tools.js` (L.121, L.3580)
- **Protocole Associé** : `standards/protocols/FACT_SEARCH_PROTOCOL.md` (Amendement de Septembre 2026)
