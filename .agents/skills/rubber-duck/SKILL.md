---
name: rubber-duck
description: "Revue contradictoire Read-Only (Agent Sentinel) pour auditer les critères d'acceptation et les 4 piliers Gherkin. Use when requesting a read-only sanity check on user stories, specs, or acceptance criteria."
---

# Skill Rubber-Duck : Critique Contradictoire Read-Only (Agent Sentinel)


Utilisez cette skill pour demander à l'agent **Sentinel** d'exécuter une révision contradictoire **100% Read-Only** sur un récit (`ST-*.md`), une spécification ou un plan d'architecture.

---

## 🎯 Quand utiliser cette skill ?
- **Après la planification** : Avant de finaliser une story ou de déclencher le handoff vers le développement.
- **Après la rédaction des critères et scénarios Gherkin** : Pour s'assurer que les 4 Piliers Gherkin, le découpage UI/API Backend et les Critères d'Acceptation (AC) sont complets.
- **Audit de propreté déclarative (ADR-0319)** : Pour s'assurer de l'absence totale de snippets de code / pseudo-code et de la présence des références vers la documentation SDK officielle.
- **En cas de doute sur la résilience** : Pour auditer les 5 vecteurs techniques (*Offline, Concurrency, Partial Data, Security, Rate Limits*).

---

## 🛠️ Instructions pour l'Agent

1. **Exécution Read-Only Strict** :
   - Exécutez la sous-commande CLI :
     ```bash
     python src/swarm.py rubber-duck --project <nom_du_projet> --file Projects/<nom_du_projet>/backlog/stories/<ST-XXX.md>
     ```
   - **NOUVEAU STANDARD DE TRAÇABILITÉ (ADR-0333)** : Avant de juger des "hallucinations" métier, Sentinel DOIT obligatoirement lire l'EvidencePack du récit :
     ```bash
     cat Projects/<nom_du_projet>/memory/evidence/<ST-XXX>_evidence.json
     ```
     L'agent doit baser sa validation Fact-Search sur ce fichier JSON, et non plus sur la section "Notes de Traçabilité" du Markdown (qui a été purgée pour des raisons de Zero-Bruit).
2. **Analyse du Rapport Généré** :
   - Lisez le rapport produit sous `Projects/<nom_du_projet>/backlog/reviews/rubber_duck_<ST-XXX>.md`.
   - Si le rapport contient des **🔴 Problèmes de Blocage (Blocking Issues)**, l'agent doit se corriger immédiatement avant de solliciter l'utilisateur.
   - Présentez la synthèse du tri des severités à l'utilisateur.

3. **Contrôle Conditionnel Contrats API (ADR-0319)** :
   - **Si `layer: backend` ou `layer: fullstack`** : Vérifier que la section `## Contrats UI & API Backend → Profil B` contient une Matrice des Contrats API (`| Méthode | Route | Finalité |`) avec au minimum une route documentée ou une mention `[API de soumission à définir]` accompagnée d'une `OQ-XXX`. L'absence de cette matrice est un défaut `BLOCKING`.
   - **Si `layer: frontend`** : Vérifier que chaque action réseau dans la Matrice CTA (colonne `Action (Navigation/API)`) référence une méthode et une route HTTP connue, ou une mention `[API à définir]` avec `OQ-XXX`. Un FE qui appelle un endpoint non documenté constitue une asymétrie `BLOCKING`.
   - **Clause OQ Exemptante** : Si une question ouverte `OQ-XXX` accompagne explicitement le contrat manquant (ou si `[API de soumission à définir]` est présent), déclasser la sévérité en `NON_BLOCKING`.
   - **Anti-Invention** : Signaler comme `BLOCKING` toute route fictive ou placeholder sans confirmation documentaire (ex : `/api/dummy`, `/api/test`, `/api/submit-todo`).

4. **Contrôle Anti-Slop & Macrostructures UI (ADR-0340)** :
   - **Si `layer: frontend` ou `layer: fullstack`** : Vérifier que le récit déclare une macrostructure valide parmi les 21 formes répertoriées ([`standards/blueprints/ui_macrostructures.md`](file:///c:/Memory%20Loop/standards/blueprints/ui_macrostructures.md)) et explicite le comportement sur les 8 états d'interaction pour les composants interactifs.
   - **Traque AI-Slop** : Signaler comme anomalie majeure toute présence de stéréotypes d'IA (titres en italique, gradients violets/bleus sans ancre OKLCH, 3 cartes répétitives, métriques non prouvées dans `docs/`).
