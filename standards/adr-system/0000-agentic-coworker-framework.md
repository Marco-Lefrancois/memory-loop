# ADR-0000 : Agentic Coworker Framework (Fondation Constitutionnelle)
## Statut : Accepté (Gouvernance Racine - Loi Fondamentale)

---

## 1. Contexte et Problématique

Le développement logiciel assisté par l'IA au sein du framework **Memory Loop Autonomous Engine (mLoop)** dépasse le simple prompt interactif pour instaurer une collaboration industrielle de niveau **Agentic Coworker** (Collaborateur Cognitif).

Afin d'éradiquer les dérives algorithmiques (*Agent Drift*) et de garantir un niveau de qualité de classe entreprise, mLoop réaffirme son rôle de **Backend d'État et de Validation (State & Validation)** opérant de manière étanche et découpée hors du code applicatif physique du client.

---

## 2. Décisions d'Architecture

Le Cœur Constitutionnel repose sur le modèle hybride à double couche :

### 🧠 Couche 1 : L'Ontologie (L'Être)
Constitution interne et autonomie sémantique de l'agent :
1. **Memory** : Capacité à relier les faits de domaine via SQLite FTS5 et le graphe Graphify.
2. **Skills** : Arsenal d'outils modulaires sous `.agents/skills/`.
3. **Soul** : Persona, style Zero-Fluff et règles d'engagement.
4. **Session Recall (Handoff)** : Persistance contextuelle typée inter-agents (`HandoffContext`).
5. **Self-Healing** : Capacité d'auto-correction déterministe (`wikifix`, `calibrate`).

### ⚙️ Couche 2 : Le Protocole (Le Faire)
Mécanique d'interaction avec le monde extérieur (Humain et Backlog) :
1. **Délégation Asymétrique** : Séparation entre la raison profonde (Système 2 - Cloud) et l'exécution rapide (Système 1 - Infanterie).
2. **Backend d'État Strict** : mLoop gouverne l'analyse, la spécification et la validation du backlog (`backlog/` et `docs/`). Le codage applicatif physique client est hors périmètre direct de l'agent.
3. **Graph Loop Architecture** : Exploration sémantique par graphe de connaissances (`graphify path/query`).
4. **Cycle P-A-V** : Plan $\rightarrow$ Analyze $\rightarrow$ Validate.
5. **Story Constraint Contract (HITL Strict)** : Frontière hermétique d'Analyse scellée par des contraintes métier inviolables.

---

## 3. Conséquences de cette Décision

- **Loi Fondamentale** : L'ADR-0000 est la Constitution Supérieure. Toutes les ADRs des séries `01xx`, `02xx` et `03xx` déclinent cette loi.
- **Transparence Absolue** : L'agent est prévisible, factuel, et soumis à la confirmation humaine.
