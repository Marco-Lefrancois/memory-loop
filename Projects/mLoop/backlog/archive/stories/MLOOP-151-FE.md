---
id: MLOOP-151-FE
jira_key: ''
epic_key: EPIC-16-DASHBOARD-TOOLING
type: Feature
title: Onglet Archify — Navigation des diagrammes dans le Cockpit
origin: DIRECT_REQUIREMENT
source_ref: Demande utilisateur 2026-09-22 + pattern onglets src/dashboard/static/index.html
  L154-177
macro_size: S
status: SHIPPED
grill_me: DONE
invest_score: 6/6
layer: frontend
blocked_by:
- MLOOP-145-BE
- MLOOP-150-BE
created_at: '2026-09-22'
content_hash: 12f765e42d60b5a5
---

# 📖 MLOOP-151-FE : Onglet Archify — Navigation des diagrammes dans le Cockpit

## 1. Intention Métier (User Story)
**En tant qu'** utilisateur du Cockpit Agentique,  
**je veux** un onglet « 📐 ARCHIFY DIAGRAMS » listant les diagrammes d'architecture disponibles et les affichant en iframe intégrée,  
**afin de** naviguer et projeter les diagrammes interactifs (zoom SVG, vues animées) directement depuis le dashboard, sans ouvrir de fichiers manuellement.

---

## 2. Origine & Cadrage Avant-Projet
- **Document Source** : Demande utilisateur (session dashboard 2026-09-22) — analyse de la navigation existante `src/dashboard/static/index.html`
- **Hypothèse de Chiffrage Retenue** : Extension du pattern d'onglets existant (`switchTab`, 7 onglets actuels) + iframe consommant les endpoints `/api/archify/*` de MLOOP-150-BE
- **Enveloppe Macro Estimée** : S (fourchette de 0.5-1 jour)

---

## 3. Périmètre Sommaire
### In-Scope (Macro)
- Bouton d'onglet dans la nav `index.html` : `<button onclick="switchTab('archify')" id="tab-btn-archify">📐 ARCHIFY DIAGRAMS</button>` (style cohérent `font-tech`, `glass-cyber`)
- Section `#tab-archify` : liste des diagrammes issue de `GET /api/archify/list` (filtre par projet actif du Cockpit) + iframe dynamique pointant vers `GET /api/archify/html?file=...`
- Sélecteur de diagramme (dropdown ou rail latéral) avec rechargement de l'iframe à la sélection
- État vide propre : message explicite « Aucun diagramme compilé — exécutez `python src/swarm.py archify --file <spec.json>` » si la liste est vide

### Out-of-Scope (Macro)
- Endpoints backend (MLOOP-150-BE)
- Édition de diagrammes depuis l'UI (reste outillage CLI Archify)
- DrawDB / ERD (MLOOP-152-BE)

---

## 4. Critères de Succès Préliminaires
- [ ] L'onglet apparaît dans la nav et s'active via `switchTab('archify')` sans régression des 7 onglets existants
- [ ] La liste des diagrammes se charge depuis l'API et l'iframe restitue le diagramme sélectionné
- [ ] Aucun appel réseau externe : les artefacts servis proviennent exclusivement des répertoires locaux allowlistés (Confinement Local des Diagrammes)
- [ ] Non-régression visuelle : onglets et styles existants inchangés

---

## 5. Arbitrages Grill-Me Micro 1:1 (Séance du 2026-09-22)
> ✅ Session Grill-with-Docs tenue (1 question par tour, arbitrages verbatim du PO).

| OQ | Décision Arbitrée |
|:---|:---|
| OQ-151-01 | **Onglet top-level « 📐 ARCHIFY »** dans la barre de navigation (même niveau que OVERVIEW, PIPELINE, GRAPH & DATABASE) |
| OQ-151-02 | **Chargement automatique uniquement si un dernier artefact mémorisé existe** — persistance `localStorage` du dernier artefact consulté (arbitrage couplé consigné) ; sinon état « Sélectionnez un diagramme » sans requête de chargement surprise |
| OQ-151-03 | **Liste latérale des artefacts** (nom + badge type + taille) et **iframe central** — navigation riche type explorateur |
| OQ-151-04 | **Bouton « ⤢ Ouvrir en plein écran »** : nouvel onglet navigateur vers `/api/archify/html?file=...&project=...` (projection native, les deux paramètres transportés dans l'URL) |
| OQ-151-05 | **Réutilisation du sélecteur de projet global du header Cockpit** — l'onglet suit le projet actif, zéro sélecteur local ; le comportement sans projet actif est couvert au Pilier 4 |

---

## Critères d'acceptation

### 1. Navigation
- [ ] Bouton `<button onclick="switchTab('archify')" id="tab-btn-archify">📐 ARCHIFY</button>` actif dans la nav, style cohérent (`font-tech`, `glass-cyber`)
- [ ] Zéro régression des 7 onglets existants (styles et bascules inchangés)

### 2. Exploration
- [ ] Liste latérale alimentée par `GET /api/archify/list?project=<projet global>` : nom + badge `type` + taille
- [ ] Iframe central pointant vers `GET /api/archify/html?file=<artefact>&project=<projet>` à la sélection
- [ ] Auto-chargement du dernier artefact consulté (clé `localStorage` dédiée) à l'ouverture de l'onglet ; sinon état vide explicite

### 3. Projection & Confinement
- [ ] Bouton « ⤢ Ouvrir en plein écran » : `window.open` vers l'URL de restitution avec `file` + `project`
- [ ] Zéro appel réseau externe — artefacts servis exclusivement par le backend local (Confinement Local des Diagrammes)

### 4. Non-Régression
- [ ] Suites `tests/test_dashboard_*.py` existantes passent ; Vibe-Check 20/20

### Scénarios de test (Gherkin 4 Piliers)

#### Pilier 1 — Chemin Nominal
```gherkin
Scénario : Navigation d'un diagramme Archify depuis le Cockpit
  Étant donné un projet actif sélectionné dans le header Cockpit
  Et des artefacts listés par "/api/archify/list?project=<projet>"
  Quand l'utilisateur ouvre l'onglet "📐 ARCHIFY" et clique sur un artefact de la liste latérale
  Alors l'iframe central charge "/api/archify/html?file=<artefact>&project=<projet>"
  Et le dernier artefact consulté est mémorisé dans "localStorage"
```

#### Pilier 2 — Exceptions & Rejets
```gherkin
Scénario : Artefact disparu après affichage de la liste
  Étant donné un artefact supprimé du disque entre le chargement de la liste et la sélection
  Quand l'utilisateur sélectionne cet artefact
  Alors l'iframe restitue le message d'erreur HTTP explicite (404 ou 403)
  Et un bouton de rafraîchissement de l'inventaire est disponible dans la liste latérale
```

#### Pilier 3 — Résilience & Mode Dégradé
```gherkin
Scénario : Anti-rebond des actions utilisateur
  Étant donné un artefact sélectionné dont l'iframe est en cours de chargement
  Quand l'utilisateur multiplie les clics rapides sur les artefacts ou sur "⤢ Ouvrir en plein écran"
  Alors chaque action est inerte pendant le chargement en cours (indicateur visible)
  Et aucune requête dupliquée n'est émise vers l'API

Scénario : Endpoint Archify indisponible
  Étant donné le endpoint "/api/archify/list" en erreur (500 ou timeout)
  Quand l'utilisateur ouvre l'onglet "📐 ARCHIFY"
  Alors un état dégradé explicite s'affiche dans la liste latérale avec la cause
  Et le reste du Cockpit (autres onglets) reste pleinement opérationnel
```

#### Pilier 4 — UX & Observabilité
```gherkin
Scénario : Première visite sans mémorisation
  Étant donné aucune clé "localStorage" existante
  Quand l'utilisateur ouvre l'onglet "📐 ARCHIFY"
  Alors un état vide "Sélectionnez un diagramme" s'affiche sans requête de chargement surprise
  Et si "total_artifacts" vaut 0 le message suggère "python src/swarm.py archify --file <spec.json>"

Scénario : Reprise du dernier diagramme consulté
  Étant donné un artefact mémorisé dans "localStorage"
  Quand l'utilisateur ouvre l'onglet
  Alors l'iframe charge automatiquement ce dernier artefact
  Et le bouton "⤢ Ouvrir en plein écran" transporte "file" et "project" vers un nouvel onglet navigateur
```

---

## Contrats UI & API Backend → Matrice CTA (Profil Frontend)

| Déclencheur Utilisateur | CTA / Endpoint | Effet Attendu |
|:---|:---|:---|
| Ouvrir l'onglet 📐 ARCHIFY | `GET /api/archify/list?project=<projet global>` | Liste latérale (nom + badge type + taille) ; auto-load dernier artefact si mémorisé |
| Cliquer un artefact | Iframe → `GET /api/archify/html?file=<artefact>&project=<projet>` | Affichage du diagramme interactif + mémorisation `localStorage` |
| Cliquer « ⤢ Ouvrir en plein écran » | `window.open('/api/archify/html?file=...&project=...')` | Projection native dans un nouvel onglet navigateur |
| Cliquer « 🔄 Rafraîchir » | `GET /api/archify/list?project=<projet global>` | Re-inventaire après disparition/ajout d'artefacts |

> [!NOTE] Exception d'ancrage visuel (validée PO, 2026-09-22)
> Récit d'outillage framework sans écran métier : l'identité graphique de l'onglet Archify hérite strictement du design system existant du Cockpit (`src/dashboard/static/index.html` — palette, nav top-level, typographie). Aucune maquette dédiée `docs/05-assets/` n'est requise ; le Cockpit lui-même sert de référence visuelle SSOT.