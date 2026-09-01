# 🎨 Galerie de Démonstration Archify — Memory Loop

Ce répertoire regroupe les diagrammes d'architecture interactifs vectoriels générés avec **Archify** pour le framework **mLoop** et les projets clients.

Ces artefacts HTML sont **100% autonomes** (zéro dépendance externe, CSS/JS et SVG vectoriel natif embarqués), validés au standard de qualité **Showcase** (9/9 contrôles stricts) et conçus pour la présentation d'équipe et la documentation technique vivante.

---

## 📂 Index des Démonstrations Disponibles

### 1. 🧠 Architecture du Framework Memory Loop (mLoop)
*Architecture du cerveau agentique, du double moteur d'analyse et de la matrice de synchronisations.*
- 🌐 **Rendu HTML Interactif** : [`mloop-framework.architecture.html`](mloop-framework.architecture.html)
- 📄 **Spécification JSON IR** : [`mloop-framework.architecture.json`](mloop-framework.architecture.json)
- **Vues incluses** :
  1. *Boot Sequence & Orchestration Agentique* (IDE CLI $\rightarrow$ Swarm Core $\rightarrow$ Workers Herdr $\rightarrow$ Git Distant).
  2. *Double Moteur Sémantique & Base SSOT* (reference/ $\rightarrow$ Ingestion MarkItDown $\rightarrow$ Graphify SQLite $\rightarrow$ Jira Cloud).
  3. *Analyse Code & Universal Handoff* (Code Client $\rightarrow$ CodeGraph AST $\rightarrow$ Usine à Récits $\rightarrow$ Dev Agents).

---

### 2. 📱 Metro Food — Architecture Multi-Bannières & API Gateway
*Solution mobile .NET C# alimentant les 3 bannières alimentaires de Metro.*
- 🌐 **Rendu HTML Interactif** : [`metro-food.architecture.html`](metro-food.architecture.html)
- 📄 **Spécification JSON IR** : [`metro-food.architecture.json`](metro-food.architecture.json)
- **Vues incluses** :
  1. *Applications Multi-Bannières* (Metro App, Super C App, Food Basics App $\rightarrow$ Noyau Commun $\rightarrow$ ApiGateway).
  2. *API Gateway & Domaines Métiers* (Coupons/Moi, Catalogue/Circulaires, Panier/Commandes, Auth/OneTrust).
  3. *Services Externes & Infrastructure* (Notifications push, Postes Canada Geo, Azure Blob DAL).

---

### 3. 🏗️ Metro Food — Cartographie Détaillée des 5 Couches Logicielles (.NET)
*Modélisation granulaire par couches avec frontières (boundaries) pour la solution `Food.sln`.*
- 🌐 **Rendu HTML Interactif** : [`metro-food-layers.architecture.html`](metro-food-layers.architecture.html)
- 📄 **Spécification JSON IR** : [`metro-food-layers.architecture.json`](metro-food-layers.architecture.json)
- **Les 5 Couches Modélisées** :
  - **Couche 1 : Présentation & UI Mobile** (`Food.Grocery_Store_1/2/3`, `MasterPage`, `Views`, `XAML`)
  - **Couche 2 : Application & Orchestration** (`Food.Application`, `DeepLinkService`, `UserCache` singleton)
  - **Couche 3 : Domaine & Services Métiers** (`Food.Definitions`, `Food.Services`, `Food.Flyer`)
  - **Couche 4 : Passerelle API & Client Réseau** (`Food.Gateway.APIClient`, `ApiGateway` Flurl)
  - **Couche 5 : Persistance, Sécurité & Cloud** (`NEssentials` Crypto EC, `Azure Blob DAL`, `OneTrust`)

---

### 4. ⚡ Metro Food — Diagramme de Séquence de Traversée des Couches (Runtime)
*Traversée de bout en bout d'un clic utilisateur jusqu'au réseau et au cache de session.*
- 🌐 **Rendu HTML Interactif** : [`metro-food-sequence.sequence.html`](metro-food-sequence.sequence.html)
- 📄 **Spécification JSON IR** : [`metro-food-sequence.sequence.json`](metro-food-sequence.sequence.json)
- **Scénario Métier** : *Chargement des Coupons "Mes Offres" & Points Moi* (UI $\rightarrow$ App $\rightarrow$ Cache $\rightarrow$ Passerelle Flurl $\rightarrow$ Cloud REST $\rightarrow$ Mise à jour réactive).

---

### 5. 🥚 Boire & Frères — Noyau Couvoir (Segment 2 Dataverse-First)
*Système de gestion de couvoir industriel avec règles d'isolation des référentiels.*
- 🌐 **Rendu HTML Interactif** : [`boirefrere-couvoir.architecture.html`](boirefrere-couvoir.architecture.html)
- 📄 **Spécification JSON IR** : [`boirefrere-couvoir.architecture.json`](boirefrere-couvoir.architecture.json)
- **Vues incluses** :
  1. *Flux de Réception au Quai* (Canvas App $\rightarrow$ Azure Functions $\rightarrow$ Dataverse / Azure SQL).
  2. *Exécution Couvoir & Événements* (Mirage, transfert, vaccination, publication Azure Service Bus).
  3. *Intégrations & Référentiels* (CRM Dynamics 365 amont, passerelle unique `boire_ref_*`).

---

## 🎬 Fonctionnalités Interactives à Montrer en Démo

1. **Onglets de Vues (Chapters / Views)** : Cliquez sur les boutons de scénarios en haut pour voir la caméra zoomer et mettre en évidence le parcours ciblé.
2. **Animation des Flux (`Trace`)** : Visualisez les particules lumineuses circulant en temps réel le long des liaisons orthogonales.
3. **Exploration Pan & Zoom** : Naviguez librement à la molette sans perte de qualité grâce au rendu SVG vectoriel natif.
4. **Fiches de Synthèse Métier (Cards)** : Consultez les règles d'architecture associées aux pastilles de couleur en bas de page.
5. **Export Multi-Formats** : Exportez le diagramme instantanément en PNG haute définition, SVG vectoriel ou vidéo animée WebM via le menu d'export.

---

## 🚀 Commande Rapide d'Ouverture Locale

Pour ouvrir n'importe quel diagramme dans votre navigateur :
```powershell
Start-Process "tools/archify/showcase/metro-food-layers.architecture.html"
```
