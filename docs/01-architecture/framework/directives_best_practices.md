# ⚖️ Bonnes Pratiques de Rédaction des Directives & Règles Système

Les directives (`tech.md`, `business.md` et `AGENTS.md`) ne sont pas de simples "README". Elles agissent comme les **Lois Fondamentales** pour les agents cognitifs. Une directive mal rédigée entraînera des hallucinations de l'agent `plan` ou des dérives d'implémentation.

---

## 1. La Règle d'Or : Le Zero-Fluff
Les modèles de raisonnement sont sensibles au bruit contextuel.
* **À ÉVITER** : "Il serait bien d'utiliser React parce que c'est moderne et que l'équipe l'aime bien."
* **À FAIRE** : "Frontend: React 18 avec TypeScript strict. Pas de classes, uniquement Functional Components + Hooks."

## 2. Rédiger `tech.md` (La Loi Technique)
Ce document contraint la phase d'architecture et de validation.
* **Définir la Stack Exacte** : Versions de Python, Node, Pydantic, MAUI, etc.
* **Architecture Obligatoire** : "Architecture Hexagonale. Dossier `src/domain` interdit d'importer `src/infra`."
* **Standard de Tests** : "Pytest / xUnit. Couverture minimum 90%. Respect obligatoire des **4 Piliers Gherkin** (Nominal, Rejet, Mode Dégradé, UX/Observabilité)."

## 3. Rédiger `business.md` (La Loi Métier)
Ce document contraint l'agent `plan`.
* **Le Lexique (Glossaire)** : Définissez les termes pour éviter que Graphify ne crée des doublons (ex: "Utiliser uniquement le terme 'Client', jamais 'Customer' ou 'User'").
* **Les Exclusions (Negative Prompting)** : Bloquez explicitement ce qui sort du périmètre :
  > **EXCLUSIONS :**
  > - NE PAS implémenter de système de paiement dans cette V1.
  > - AUCUN compte administrateur global n'est autorisé.

## 4. `AGENTS.md` (La Loi Opérationnelle Système)
Complète `tech.md` et `business.md` au niveau du harnais mLoop :
* **Boot Sequence Anti-Amnésie** : Exécution mécanique des 5 étapes CLI au 1er tour de parole.
* **Zero-Ask Evidence Enforcement** : Génération synchrone obligatoire de l'EvidencePack (`memory/evidence/`).
* **Gouvernance Jira (Story-Only)** : Synchronisation exclusive en tickets de type Story (`jira_sync`).

## 5. L'Évolution via l'Agent Plan
Le protocole *Grill with Docs* permet à l'agent `plan` d'interroger l'humain et de mettre à jour automatiquement ces fichiers au fur et à mesure des décisions d'architecture.
