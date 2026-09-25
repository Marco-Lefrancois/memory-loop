---
id: MLOOP-024-BE
jira_key: '-'
epic_key: EPIC-3-SAFETY-GOVERNANCE
type: Feature
title: Pont de Speculative Drafting et Confidence Gate
tags: [safety, confidence-gate, speculative-drafting, validation, lint]
status: SHIPPED
layer: backend
invest_score: 6/6
macrostructure: "workbench"
---
# [EPIC-3-SAFETY-GOVERNANCE] Pont de Speculative Drafting et Confidence Gate (MLOOP-024-BE)

---

## Description
**En tant qu'** Orchestrateur Asymétrique,  
**je veux** introduire une porte de confiance (Confidence Gate) utilisant un linter déterministe et des contrôles légers,  
**afin d'** évaluer la conformité syntaxique et structurelle d'un brouillon de spécification avant de solliciter l'agent de raisonnement profond.

---

## Contexte & Périmètre

### Contexte Métier
Basé sur la vérification planifiée par confiance de l'architecture DeepSpec/DSpark, cette fonctionnalité évite de gaspiller du budget API lourd pour valider des documents qui échoueraient sur des règles syntaxiques primaires (YAML corrompu, balises Gherkin absentes). Le brouillon est évalué localement et rejeté s'il ne franchit pas le seuil minimal de conformité.

### In-Scope
- Module `src/bridges/confidence_gate.py`.
- Calcul du score de confiance structurel sur les brouillons.
- Rejet immédiat avec motifs en cas d'anomalies bloquantes.
- Suite de tests unitaire dédiée.

### Out-of-Scope
- Remplacement du censeur sémantique approfondi (Sentinel).

---

## Critères d'acceptation

### Opérations Métier & Logique Backend

#### 1. Évaluation du Score de Confiance du Draft
* **Entrée Métier** : Chemin ou contenu textuel du document Markdown candidat.
* **Règles d'admissibilité & Validation** : Présence impérative du frontmatter YAML, des 4 sections obligatoires et des balises Gherkin.
* **Traitement & Algorithme Métier** : Analyse statique locale sans appel LLM externe et scoring sur 100 points.
* **Résultat Métier & Mutations** : Décision PASS si score supérieur ou égal au seuil de 80 points, ou REJECT.
* **Cas de Rejet Métier** : Rejet direct avec rapport d'erreurs pour correction immédiate sans mobilisation des modèles de raisonnement.

---

## Scénarios de test

```gherkin
# language: fr
Fonctionnalité: Pont de Speculative Drafting et Confidence Gate

  # CHEMIN NOMINAL
  Scénario: Validation avec score de confiance élevé
    Étant donné un brouillon de story complet respectant la structure officielle
    Quand le Confidence Gate évalue le document
    Alors le statut retourné est PASS
    Et le document est transmis pour approbation formelle

  # EXCEPTIONS & REJETS MÉTIER
  Scénario: Rejet immédiat sur frontmatter YAML invalide
    Étant donné un brouillon avec une syntaxe YAML corrompue
    Quand le Confidence Gate inspecte le document
    Alors le statut retourné est REJECT
    Et la liste des erreurs syntaxiques est explicitement fournie

  # RÉSILIENCE TECHNIQUE & MODE DÉGRADÉ
  Scénario: Évaluation locale rapide sous contrainte de temps
    Étant donné un document volumineux soumis au filtre
    Quand le Confidence Gate exécute les vérifications statiques
    Alors le temps d'exécution total demeure inférieur à 2 secondes
    Et aucune requête réseau externe n'est émise

  # UX, OBSERVABILITÉ & EMPTY STATE
  Scénario: Rapport détaillé des points d'amélioration
    Étant donné un brouillon recevant un score sous le seuil d'admissibilité
    Quand le rapport de conformité est émis
    Alors chaque critère défaillant est documenté avec sa ligne d'occurrence
    Et un conseil d'auto-correction est suggéré au rédacteur
```
