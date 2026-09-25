---
id: MLOOP-070-BE
jira_key: '-'
epic_key: EPIC-7-AGENTIC-OBSERVABILITY
status: SHIPPED
type: Feature
title: Disjoncteur Anti-Boucle Ping-Pong Guard
layer: backend
invest_score: 6/6
macrostructure: "workbench"
---
# [EPIC-7-AGENTIC-OBSERVABILITY] Disjoncteur Anti-Boucle Ping-Pong Guard (MLOOP-070-BE)

## Description
**En tant qu'** Orchestrateur du framework mLoop,  
**je veux** détecter et interrompre toute délégation circulaire ou répétitive entre agents dépassant 3 transferts consécutifs sans production de livrable,  
**afin de** prévenir l'épuisement silencieux du budget de tokens et garantir l'intervention humaine (HITL) avant tout gaspillage financier.

---

## Contexte
Dans les architectures d'essaims multi-agents (Swarm), la délégation non bornée est l'un des modes de défaillance les plus fréquents et coûteux (*Goal Drift & Infinite Handoffs*).
Deux agents peuvent entrer en résonance stérile (ex. l'Orchestrateur délègue au Planificateur, qui renvoie au Sentinelle, qui réinterroge le Planificateur).
Ce récit met en place le composant déterministe `PingPongGuard` dans le kernel de sécurité (`src/agents/circuit_breaker.py`) pour couper net tout cycle dès le 3e handoff consécutif non productif.

---

## Opérations API & Logique Backend

### Matrice des Opérations Backend
| Opération Métier | Contrat / Trigger | Validation & Préconditions | Succès Observable | Gestion Erreurs |
| :--- | :--- | :--- | :--- | :--- |
| **[Enregistrement Handoff]** | `record_handoff(from_agent, to_agent, produced_artifact=False)` | Rôles d'agents valides issus du registre de topologie | Pile d'appels mise à jour, compteur incrémenté | Levée `ValueError` si rôle inconnu |
| **[Vérification de Cycle]** | `check_recursion()` | Appelé avant tout dispatch de sous-agent | Autorisation d'exécution si pile saine | Levée de `PingPongRecursionError` et drapeau HITL levé si cycle $\ge 3$ |
| **[Réinitialisation sur Livrable]** | `record_artifact_production(file_path)` | Fichier persisté physiquement sur disque | Compteur de handoffs remis à zéro | Fail-safe non-bloquant |

---

## Règles d'affaires
* **[Seuil de Récursion Infranchissable]** : Tout cycle alterné entre deux agents ($A \rightarrow B \rightarrow A \rightarrow B$) ou toute chaîne de délégation atteignant 3 handoffs consécutifs sans modification de fichier sur disque doit immédiatement stopper l'exécution.
* **[Interruption HITL Non Négociable]** : Le disjoncteur consigne l'incident dans le journal d'état (`circuit_breaker:ping_pong_detected`) et lève l'exception `PingPongRecursionError` pour forcer l'arbitrage humain.
* **[Tolérance sur Production Réelle]** : L'écriture d'un fichier valide (code, test, documentation) réinitialise la profondeur de la chaîne de handoffs.

---

## Scénarios de test

```gherkin
# language: fr
Fonctionnalité: Disjoncteur Anti-Boucle Ping-Pong Guard

  # 1. CHEMIN NOMINAL (Happy Path & Délégations Linéaires)
  Scénario: Délégation linéaire d'orchestration sous le seuil maximal
    Étant donné un essaim initialisé avec les agents "Orchestrator", "Plan" et "Worker"
    Quand "Orchestrator" délègue la tâche à "Plan"
    Et que "Plan" délègue l'exécution à "Worker"
    Alors le compteur de handoffs consécutifs s'établit à 2
    Et l'exécution se poursuit sans interruption du disjoncteur

  # 2. EXCEPTIONS & REJETS MÉTIER (Détection de Cycle Répétitif)
  Scénario: Interception d'une boucle circulaire alternée entre deux agents
    Étant donné une interaction entre "Worker" et "Sentinel"
    Quand "Worker" passe la main à "Sentinel"
    Et que "Sentinel" renvoie la main à "Worker"
    Et que "Worker" renvoie à nouveau la main à "Sentinel" sans produire de fichier
    Alors le PingPongGuard détecte le 3e handoff circulaire
    Et le système lève immédiatement l'exception PingPongRecursionError
    Et le drapeau HITL_REQUIRED est activé

  # 3. RÉSILIENCE TECHNIQUE & MODE DÉGRADÉ (Réinitialisation sur Production)
  Scénario: Réinitialisation légitime du compteur lors de l'écriture d'un artefact
    Étant donné une chaîne de handoff ayant cumulé 2 transferts consécutifs
    Quand l'agent actif génère et persiste avec succès un fichier sur disque
    Alors la profondeur de handoff est automatiquement réinitialisée à zéro
    Et le compteur permet de nouveaux échanges sans faux positif

  # 4. UX & OBSERVABILITÉ (Traçabilité Événementielle & Journal d'État)
  Scénario: Consignation de la disjonction dans le journal d'état et le flux d'événements
    Étant donné un arrêt provoqué par le PingPongGuard
    Quand le disjoncteur interrompt la session
    Alors une entrée "circuit_breaker:ping_pong_detected" est inscrite dans le journal d'état
    Et un événement structuré de type "circuit_breaker_tripped" est émis dans memory/events.jsonl
    Et la trace d'incident est visible sur le tableau de bord Cockpit
```
