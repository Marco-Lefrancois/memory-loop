# Checklist de Synchronisation Tripartite & Release

Cette checklist régit la Phase 5 (Sync & Release) du cycle de vie cognitif de Memory Loop.
Elle garantit que la documentation vivante, le gestionnaire de projet Jira, le dépôt Git et la mémoire externe restent en synchronisation atomique permanente.

---

## 1. Synchronisation Tripartite Déterministe

- [ ] **Axe 1 : Dépôt Git & Historique Atomique** :
  - Commits sémantiques conformes à Conventional Commits (`feat:`, `fix:`, `docs:`, `refactor:`).
  - Aucune modification orpheline non commitée ou fichier de test temporaire non exclu dans `.gitignore`.
- [ ] **Axe 2 : Jira Cloud & Statut du Backlog** :
  - Les User Stories livrées passent à l'état `Done` ou `In Review`.
  - La description Jira contient le lien vers la story Markdown dans le dépôt et l'EvidencePack associé.
- [ ] **Axe 3 : Graphe de Connaissances & FTS5 (Graphify & Ingestion)** :
  - Re-génération incrémentale du graphe via `uv run python src/swarm.py graphify` si de nouveaux documents d'architecture ont été ajoutés.
  - Re-indexation FTS5 SQLite pour les nouvelles décisions.

---

## 2. Actualisation de la Documentation Vivante SSOT

- [ ] **Vérification de la Fraîcheur des Sources** :
  - Les nouveaux ADRs et les modifications de spécifications majeures sont consolidés dans la documentation vivante (`docs/`).
  - L'indexation sémantique FTS5 et l'hypergraphe Graphify sont rafraîchis pour éviter tout drift d'ancrage avec les sessions de RAG.

---

## 3. Déploiement Progressif & Stratégie Canary (Pour Handoff Physique)

- [ ] **Paliers de Déploiement Staged** :
  - Étape 1 : Déploiement interne / Alpha / Staging (0% production).
  - Étape 2 : Canary restreint (5% du trafic utilisateur réel pendant au moins 1 heure).
  - Étape 3 : Déploiement étendu (25% ➔ 50% sous surveillance des métriques d'erreurs).
  - Étape 4 : Déploiement général (100% de production).
- [ ] **Seuils d'Alerte & Déclencheurs de Rollback** :
  - Taux d'erreur 5xx supérieur à 0.5% sur une fenêtre de 5 minutes ➔ **Rollback Immédiat**.
  - Dégradation de latence p95 supérieure à 20% par rapport à la baseline ➔ **Investigation Bloquante**.
  - Détection d'anomalie dans le journal des logs applicatifs (panics, exceptions non catchées).

---

## 4. Clôture de Release & Validation Définitive

- [ ] **Vérification `doctor` et `vibe-check`** :
  - `uv run python src/swarm.py doctor` retourne 🟢 OK sur l'ensemble des modules.
  - `uv run python src/swarm.py vibe-check` confirme la conformité des protocoles.
- [ ] **Changelog Mis à Jour** :
  - L'entrée correspondante est rédigée dans [`CHANGELOG.md`](../../CHANGELOG.md) respectant le format Keep a Changelog.
