---
id: MLOOP-003-BE
jira_key: '-'
epic_key: EPIC-1-CORE-LOOP
type: Feature
title: Circuit Breaker Financier Tokens et TTL de Session
tags: [core, circuit-breaker, tokens, ttl, safety]
status: SHIPPED
layer: backend
invest_score: 6/6
macrostructure: "workbench"
---
# [EPIC-1-CORE-LOOP] Circuit Breaker Financier Tokens et TTL de Session (MLOOP-003-BE)

---

## Description
**En tant que** Kernel mLoop,  
**je veux** surveiller la consommation de tokens et la durée de session,  
**afin d'** interrompre automatiquement toute session coûteuse ou bloquée avant de déclencher une dépense incontrôlée sur le cloud NMedia.

---

## Contexte & Périmètre

### Contexte Métier
Les agents de Système 2 (LLM cloud) consomment des jetons à chaque invocation. Sans garde-fou, une boucle non convergente ou une session zombie peut épuiser le budget alloué. Ce récit ajoute un Circuit Breaker à deux dimensions — financière (tokens) et temporelle (TTL) — qui s'intercale avant chaque délégation vers le Système 2.

### In-Scope
- Classe `FinancialCircuitBreaker` dans `src/agents/circuit_breaker.py`.
- Validation O(1) locale du budget de jetons et du TTL de session.
- Comptabilisation stricte basée sur `response.usage.total_tokens` ou ratio 1:4.
- Suite de tests unitaire de blocage financier.

### Out-of-Scope
- Intégration de facturation multi-devises.

---

## Critères d'acceptation

### Opérations Métier & Logique Backend

#### 1. Interception Pré-Vol Financière
* **Entrée Métier** : État de session, budget de tokens cumulés et horodatage de début de session.
* **Règles d'admissibilité & Validation** : Dépassement de `MAX_TOKENS` (50 000 par défaut) ou expiration du `TTL` (7 200 secondes par défaut).
* **Traitement & Algorithme Métier** : Évaluation locale O(1) avant délégation vers le LLM Système 2.
* **Résultat Métier & Mutations** : Autorisation de passage si le budget est sain, ou basculement forcé en phase ERROR.
* **Cas de Rejet Métier** : Levée de `BudgetExceededError` ou `SessionExpiredError` interceptée par l'orchestrateur.

---

## Scénarios de test

```gherkin
# language: fr
Fonctionnalité: Circuit Breaker Financier Tokens et TTL de Session

  # CHEMIN NOMINAL
  Scénario: Autorisation nominale sous les seuils de budget et TTL
    Étant donné un état de session avec 10 000 tokens consommés sur 50 000 autorisés
    Et une session active depuis 15 minutes sur un TTL de 2 heures
    Quand le Circuit Breaker est vérifié avant un appel Système 2
    Alors l'appel est autorisé sans exception
    Et la session se poursuit normalement

  # EXCEPTIONS & REJETS MÉTIER
  Scénario: Blocage immédiat sur dépassement du quota de tokens
    Étant donné un état de session avec 50 001 tokens consommés pour un plafond de 50 000
    Quand le Circuit Breaker est vérifié
    Alors une exception BudgetExceededError est levée
    Et l'orchestrateur bascule l'état de boucle en ERROR

  # RÉSILIENCE TECHNIQUE & MODE DÉGRADÉ
  Scénario: Rejet pour expiration de TTL de session
    Étant donné une session initiée depuis plus de 7 200 secondes
    Quand le Circuit Breaker évalue la durée écoulée
    Alors une exception SessionExpiredError est levée
    Et aucun appel réseau payant n'est émis

  # UX, OBSERVABILITÉ & EMPTY STATE
  Scénario: Alerte préventive à 80% du budget
    Étant donné une consommation atteignant 40 000 tokens sur 50 000
    Quand l'orchestrateur traite l'étape
    Alors un avertissement de vigilance budgétaire est consigné dans la console
    Et le traitement continue sans interruption bloquante
```
