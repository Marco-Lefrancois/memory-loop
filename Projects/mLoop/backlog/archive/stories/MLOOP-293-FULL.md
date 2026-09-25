---
id: MLOOP-293-FULL
jira_key: ''
epic_key: EPIC-29-GRILL-V2-FRONTIER-SKILLS
type: Feature
title: Validation E2E sur Cas Réel (Metro FOOD) & Certification Vibe-Check
tags:
- grill
- e2e
- metro-food
- vibe-check
- certification
status: SHIPPED
validated_by: "Marco (PO - Feu Vert 2026-09-24)"
validated_at: "2026-09-24"
grill_me: DONE
layer: fullstack
invest_score: 6/6
macro_size: M
created_at: '2026-09-24'
ttl_cycles: 4
---

# 📖 MLOOP-293-FULL : Validation E2E sur Cas Réel (Metro FOOD) & Certification Vibe-Check

---

## Description
**En tant qu'** Équipe Produit et Architecture mLoop,  
**je veux** dérouler une session de cadrage réelle sur une initiative de `Metro_FOOD` combinant choix d'infrastructure et arbitrage d'interface avec le moteur Grilling v2,  
**afin de** prouver empiriquement la division par deux du nombre d'interactions, l'efficacité du prototype Handoff zéro-build et la conformité intégrale aux portes de qualité avec un `vibe-check` à 0 FAIL.

---

## Contexte & Périmètre

### Contexte Métier
L'ADR-013 fixe comme cible de validation empirique un cas réel issu du portefeuille mLoop (`Metro_FOOD`) plutôt que des tests unitaires synthétiques isolés. Le parcours pilote doit vérifier :
1. L'enchaînement d'un cadrage macro avec `--mode round` réduisant d'au moins 50% le nombre de tours de dialogue pour arbitrer 4 décisions orthogonales.
2. La détection d'une question ungrillable (ex: sélection des substituts alimentaires ou panneau de filtres d'allergènes) déclenchant la génération d'un prototype HTML5 zéro-build dans `scratch/prototypes/`.
3. La continuité cognitive : transition directe sans effacement de mémoire vers la rédaction du récit avec DoR 6/6.
4. L'exécution du contrôle souverain de santé `vibe-check` attestant de l'intégrité de la base de code et de la documentation.

### In-Scope
- Préparation du cas pilote sur une initiative réelle de `Metro_FOOD` (gestion des allergènes / panier de substitution).
- Exécution du Macro-Grill avec rounds de questions orthogonales.
- Génération et test d'un prototype de staging zéro-build.
- Contrôle de la consommation de tokens et absence de reset de contexte.
- Exécution de `python src/swarm.py vibe-check --project mLoop` et validation du résultat.

### Out-of-Scope
- Développement des composants finaux de production dans l'application cliente Metro FOOD.

---

## Critères d'acceptation (Gherkin 4 Piliers)

### 1. Pilier Nominal (Happy Path - Cadrage E2E Pilote Réel)
```gherkin
Scénario: Cadrage E2E complet d'une initiative Metro FOOD en mode round
  Étant donné une initiative Metro FOOD comportant 4 questions orthogonales ouvertes
  Quand l'équipe exécute le macro-grill avec l'option --mode round
  Alors l'ensemble des 4 arbitrages est conclu en 2 tours d'échange maximum
  Et une réduction mesurée de plus de 50% des interactions est constatée par rapport au 1:1 historique
  Et un ADR de synthèse d'architecture est produit automatiquement
```

### 2. Pilier Exception & Déclenchement Handoff lors d'une Ambiguïté Visuelle
```gherkin
Scénario: Déclenchement et validation d'un prototype Handoff sur l'écran d'allergènes
  Étant donné une question de cadrage portant sur l'agencement visuel du filtre d'allergènes Metro FOOD
  Quand l'agent identifie la nature ungrillable de la question
  Alors un prototype HTML5 est généré sous "Projects/Metro_FOOD/scratch/prototypes/proto_allergens.html"
  Et l'ouverture locale confirme la pertinence du layout
  Et la décision est actée en 1 seul tour complémentaire
```

### 3. Pilier Résilience & Continuité Cognitive sans Amnésie
```gherkin
Scénario: Enchaînement direct vers la rédaction de récits DoR 6/6
  Étant donné la conclusion du macro-grill et du prototype Handoff
  Quand l'agent bascule en phase de formalisation des récits utilisateurs
  Alors aucun reset de contexte n'est déclenché
  Et les récits produits héritent exhaustivement des décisions validées
  Et les fact dossiers de preuves C9 sont générés avec statut VALIDATED
```

### 4. Pilier UX, Accessibilité & Certification Vibe-Check Souverain
```gherkin
Scénario: Certification de vol globale du framework et du projet
  Étant donné la fin de l'implémentation et de la documentation d'EPIC-29
  Quand la commande "python src/swarm.py vibe-check --project mLoop" est exécutée
  Alors le rapport retourne 0 FAIL
  Et les portes G6 et G7 sont validées
  Et l'épopée EPIC-29 est éligible à la clôture formelle
```

---

### Contrats d'Échange API (Interface Python & In-Process)

#### Matrice des Contrats API
- **OQ-293 (Exemption Zéro Fausse Route)** : Exemption complète de la Matrice des Contrats API réseau — récit de validation E2E, harnais de test et scénario d'intégration orchestré in-process, sans contrat d'API HTTP distant spécifique `[API de soumission à définir]` (ADR-0319).

**Contrats de Validation E2E :**
- `run_e2e_grill_pilot(project_name: str = "Metro_FOOD") -> Dict[str, Any]`
- `verify_vibe_check_compliance(project_name: str = "mLoop") -> bool`

---

## Métriques Clés d'Évaluation E2E

| Métrique | Valeur de Référence (v1) | Cible Visée (v2) | Tolérance |
| :--- | :---: | :---: | :---: |
| **Nombre de tours de cadrage macro** | 8 à 12 tours (1:1) | 3 à 4 tours (Rounds) | $\le 50\%$ du temps |
| **Délai de résolution question IHM** | 15 à 30 min (débat texte) | $< 3$ min (Handoff prototype) | Immédiat |
| **Taux de perte de contexte post-grill** | Fréquent (purge manuelle) | 0% (continuité stricte) | Zéro perte |
| **Résultat Vibe-Check** | 0 FAIL requis | 0 FAIL garanti | Stricte égalité |

---

## Références
- 🏛️ **ADR Associés** : [ADR-013](../../../docs/01-architecture/ADR-013_epic-29_grill_v2_frontier_rounds_ungrillable_context.md) · [ADR-0389](../../../../standards/adr-system/0389-grill-v2-frontier-rounds-ungrillable-handoff-context-budget.md) · [ADR-0375](../../../../standards/adr-system/0375-standard-preuve-epistemique-et-tracabilite-radicale.md)
- 📂 **Projet Pilote** : `Projects/Metro_FOOD/`
- 📦 **Épopée Parente** : [`EPIC-29-GRILL-V2-FRONTIER-SKILLS`](../epics/epic_grill_v2_frontier_rounds_ungrillable_context.md)