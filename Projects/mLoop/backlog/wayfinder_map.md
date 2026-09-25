# 🧭 Wayfinder Map : Evolution Framework

> [!NOTE]
> Cette carte recense l'ensemble des **tickets de décision** (arbitrages, questions ouvertes OQ, choix d'architecture) nécessaires pour lever le brouillard avant le développement.

## Status de l'Initiative
- **Initiative** : Evolution Framework
- **Projet** : mLoop
- **Statut** : IN_PROGRESS

## 🚦 Frontière des Décisions (Tranchées lors du Grill-Me & Arbitrages d'Architecture)
- [x] **DEC-001** : **Sensibilité du Ping-Pong Guard** — Arbitrage : Limite stricte à 3 handoffs consécutifs ($A \leftrightarrow B$) sans fichier produit sur disque avant levée du drapeau `[HITL REQUIRED]`.
- [x] **DEC-002** : **Référence du Context Gauge** — Arbitrage : Calcul dynamique par session active sur la fenêtre contextuelle du modèle, avec franchissement à 60% pour la Dumb Zone.
- [x] **DEC-003** : **Ménage des Projets de Test** — Arbitrage : Archivage des 4 dossiers `TestProject`, `TestSpecial`, `TestProjet`, `TestShopifyProject` sous `Projects/_archive/tests_and_scaffolds/archive_20260919/`.
- [x] **DEC-004** : **Explorateur Graph & Database** — Arbitrage : Création de l'Onglet 9 dans le Cockpit 2.0 pour visualiser le graphe Graphify du projet mLoop et requêter les bases SQLite locales en lecture seule.
- [x] **DEC-005** : **Isolation du Harnais Déterministe de Phase 3 dans EPIC-8** — Arbitrage : Découplage des travaux d'outillage (Linter statique AST, Moteur de Tournoi Multi-Draft Pareto, Verrouillage TDD Red-Green) dans une épopée dédiée `EPIC-8-BUILD-HARNESS-GOVERNANCE` et mise en pause temporaire de `EPIC-7-AGENTIC-OBSERVABILITY` (dont MLOOP-070 et 071 sont scellés `DONE_TESTED`).
- [x] **DEC-006** : **Création du Backlog d'Excellence Souveraine EPIC-10** — Arbitrage : Ratification du backlog d'excellence souveraine (découpage modulaire du code hérité ADR-0202/0369, embeddings denses 100% locaux sans cloud, streaming MCP SSE réactif, cockpit force-directed graph et hook pre-commit déterministe) composé des 6 récits `MLOOP-100-BE` à `MLOOP-105-BE`.

## 📋 Registre des Tickets de Décision
*Initiative EPIC-10-SOVEREIGN-EXCELLENCE cadrée, formalisée et active dans le backlog produit.*

---
*Généré automatiquement par mLoop Wayfinder Engine.*
