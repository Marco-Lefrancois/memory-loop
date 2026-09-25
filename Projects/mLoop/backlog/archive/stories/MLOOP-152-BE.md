---
id: MLOOP-152-BE
jira_key: ''
epic_key: EPIC-16-DASHBOARD-TOOLING
type: Feature
title: DrawDB Souverain Local & Lien Cockpit (Zéro Exfiltration)
origin: DIRECT_REQUIREMENT
source_ref: Demande utilisateur 2026-09-22 + tools/drawdb/runner.py L16-43 + src/bridges/drawdb_bridge.py
  L13-70
macro_size: S
status: SHIPPED
grill_me: DONE
invest_score: 6/6
layer: backend
blocked_by:
- MLOOP-145-BE
created_at: '2026-09-22'
content_hash: 2922034834f7c6c0
---

# 🗄️ DrawDB Souverain Local & Lien Cockpit (Zéro Exfiltration)

> [!NOTE]
> **Fichier restauré le 2026-09-22** à partir du dossier de preuves intact `memory/evidence/MLOOP-152-BE_fact_dossier.md` et de l'EvidencePack `MLOOP-152-BE_evidence.json`, après suppression physique externe du fichier original (agents parallèles WORKING détectés — voir `worker-status`). **Palier 2 atteint** : `status: READY_FOR_DEV`, `grill_me: DONE`, séance Grill-Me 1:1 tenue le 2026-09-22, DoR 6/6 validé.

## 1. Intention Métier (User Story)
**En tant qu'** utilisateur du Cockpit Agentique modélisant des schémas de bases de données,
**je veux** un serveur DrawDB 100% local (zéro dépendance externe) accessible depuis l'onglet Graph & Database du dashboard,
**afin de** modéliser et visualiser les ERD sans exfiltration de code ou de données vers des serveurs distants, en conformité avec la règle « Confinement Local des Diagrammes » (AGENTS.md).


---

## 2. Origine & Cadrage Avant-Projet
- **Constat de non-conformité** : `tools/drawdb/runner.py` (L40) sert une page fallback contenant `<iframe src="https://www.drawdb.app/editor">` — dépendance web externe en tension avec l'interdiction d'exfiltration.
- **Atout existant** : un parseur DBML opérationnel `parse_dbml` (`src/bridges/drawdb_bridge.py`, L13-70) produit tables/champs/PK/FK — réutilisable sans réécriture.
- **Infrastructure existante** : serveur HTTP local `socketserver.ThreadingTCPServer` (runner L45-60), défaut port 8080 — en conflit avec le dashboard (8080), d'où la convention proposée 8081.
- **Enveloppe Macro Estimée** : S (0.5-1 jo
---

## 3. Périmètre Sommaire
### In-Scope (Macro)
- Suppression de l'iframe externe `https://www.drawdb.app` du runner (`tools/drawdb/runner.py`) au profit d'un visualiseur 100% local (zéro CDN, zéro appel sortant)
- Réutilisation de `parse_dbml` (`src/bridges/drawdb_bridge.py`) pour alimenter le rendu ERD local
- Bouton « 🗄️ Ouvrir DrawDB » dans l'onglet GRAPH & DATABASE du dashboard (`index.html` L174-176)
- Convention de ports : drawdb sur 8081 (dashboard reste sur 8080)

### Out-of-Scope (Macro)
- Le pipeline CLI drawdb (export/import/sync, `src/pipelines/drawdb_pipeline.py`) — hors périmètre
- Onglet Archify (MLOOP-151-FE) et API Archify (MLOOP-150-BE)
- Build npm vendored : arbitrage à trancher (OQ-152-01 
---

## 4. Critères de Succès Préliminaires
- [ ] Zéro requête réseau sortante depuis la page DrawDB servie (audit : aucun host externe dans le HTML/JS servi)
- [ ] Le visualiseur restitue les schémas DBML via `parse_dbml` (tables, champs, PK/FK)
- [ ] Le bouton Cockpit ouvre le visualiseur sur le port conventionné sans conflit avec le dashboard
- [ ] Non-régression : commande `python src/swarm.py drawdb` opérationnelle, suites `tests/test_dashboa
---

## 5. Arbitrages Grill-Me Micro 1:1 (Séance du 2026-09-22)
> ✅ Session Grill-with-Docs tenue (1 question par tour, arbitrages verbatim du PO).

| OQ | Décision Arbitrée |
|:---|:---|
| OQ-152-01 | **Visualiseur ERD maison** s'appuyant sur `parse_dbml` (`src/bridges/drawdb_bridge.py`) — zéro dépendance npm, 100% souverain, portée affichage tables/champs/PK/FK (arbitrage englobant : la suppression de l'iframe `drawdb.app` devient implicite, la page servie étant intégralement le visualiseur maison) |
| OQ-152-02 | **Convention de ports croisée** : drawdb **8081** par défaut / dashboard **8080**, les deux configurables via `--port`, avec documentation croisée des défauts |
| OQ-152-03 | **Auto-détection récursive** des `*.dbml` sous `Projects/<projet actif>/`, avec sélecteur si plusieurs fichiers |
| OQ-152-04 | **Widget avec health-check** dans l'onglet GRAPH & DATABASE : sonde d'état (🟢 démarré sur :8081 / 🔴 arrêté), ouverture au clic |
| OQ-152-05 | **Démarrage automatique zéro friction** : le widget lance le serveur via `subprocess` (timeout explicite ADR-0369) puis act
---

## Critères d'acceptation

### 1. Visualiseur Souverain (Confinement Local)
- [ ] La page servie par le runner drawdb est 100% locale : zéro référence `drawdb.app`, zéro CDN, zéro host externe (audit du HTML/JS servi)
- [ ] Le rendu ERD s'appuie sur `parse_dbml` : tables, champs, PK/FK restitués fidèlement

### 2. Découverte DBML
- [ ] Auto-détection récursive des `*.dbml` sous `Projects/<projet actif>/` ; sélecteur de schéma si plusieurs fichiers détectés

### 3. Widget Cockpit & Cycle de Vie du Serveur
- [ ] Widget dans l'onglet GRAPH & DATABASE : sonde d'état 🟢/🔴, ouverture au clic
- [ ] Serveur arrêté ➔ spawn `subprocess` avec timeout explicite, puis re-sonde avant ouverture
- [ ] Échec de spawn (port occupé, binaire absent) ➔ état d'erreur explicite avec la cause

### 4. Ports & Non-Régression
- [ ] Défauts croisés 8080/8081 documentés, configurables `--port`
- [ ] `python src/swarm.py drawdb` opérationnel ; suites `tests/test_dashboard_*.py` passent ; Vibe-Check 20/20

### Scénarios de test (Gherkin 4 Piliers)

#### Pilier 1 — Chemin Nominal
```gherkin
Scénario : Visualisation d'un schéma DBML en local
  Étant donné un projet actif contenant des fichiers "*.dbml" sous "Projects/<projet>/"
  Et le serveur drawdb démarré sur le port 8081
  Quand "GET http://localhost:8081/" est appelé
  Alors la page restitue les tables, champs et relations PK/FK issus de "parse_dbml"
  Et aucun host externe n'est référencé dans le HTML servi
```

#### Pilier 2 — Exceptions & Rejets
```gherkin
Scénario : Fichier DBML invalide
  Étant donné un fichier "*.dbml" malformé détecté sous "Projects/<projet>/"
  Quand le visualiseur tente son rendu
  Alors le sélecteur expose le fichier en état d'erreur explicite
  Et les autres fichiers DBML restent consultables

Scénario : Aucun schéma DBML détecté
  Étant donné un projet actif sans aucun fichier "*.dbml"
  Quand la page du visualiseur est chargée
  Alors un état vide explicite s'affiche avec la convention de localisation attendue
```

#### Pilier 3 — Résilience & Mode Dégradé
```gherkin
Scénario : Anti-rebond du démarrage automatique
  Étant donné un subprocess de démarrage drawdb déjà en cours
  Quand l'utilisateur multiplie les interactions rapides avec le widget
  Alors un seul processus de démarrage est lancé (verrou en cours ou attente du résultat existant)
  Et le widget affiche un indicateur de chargement pendant l'opération

Scénario : Démarrage automatique du serveur drawdb
  Étant donné le serveur drawdb arrêté (sonde 🔴)
  Quand l'utilisateur interagit avec le widget de l'onglet GRAPH & DATABASE
  Alors un subprocess est lancé avec un "timeout" explicite
  Et la sonde est re-vérifiée avant ouverture du visualiseur
  Et en cas d'échec (port occupé, binaire absent) le widget affiche la cause sans bloquer le dashboard

Scénario : Dashboard seul en fonction
  Étant donné le serveur drawdb indisponible
  Quand l'utilisateur consulte les autres onglets du Cockpit
  Alors aucune régression ni blocage n'est constaté sur ces onglets
```

#### Pilier 4 — UX & Observabilité
```gherkin
Scénario : Widget de santé du serveur DrawDB
  Étant donné l'onglet "GRAPH & DATABASE" ouvert
  Quand le widget interroge l'état du serveur drawdb
  Alors il affiche "🟢 démarré sur :8081" si la sonde répond
  Et il affiche "🔴 arrêté" sinon, avec le déclencheur de démarrage aut
---

## Contrats UI & API Backend → Profil B (hybride backend/widget)

### Matrice des Contrats REST / CTA

| Méthode | Route / CTA | Finalité |
|:---|:---|:---|
| `GET` | `http://localhost:<port>/` (runner drawdb) | Page visualiseur ERD 100% locale (zéro CDN, zéro host externe) |
| `GET` | `/api/drawdb/list?project=<nom>` | Inventaire des `*.dbml` sous `Projects/<projet>/` (découverte récursive) |
| `GET` | `/api/drawdb/health` | Sonde d'état du serveur drawdb (widget 🟢/🔴) |
| `POST` | `/api/drawdb/start` | Démarrage subprocess du serveur (timeout explicite, re-sonde) |
| Conversion interne | `drawdb_bridge.parse_dbml` | DBML → tables/champs/PK/FK pour le rendu ERD |
| CTA | Widget « 🗄️ DrawDB » (onglet GRAPH & DATABASE) | Sonde + ouverture visualiseur + démarrage auto si arrêté |