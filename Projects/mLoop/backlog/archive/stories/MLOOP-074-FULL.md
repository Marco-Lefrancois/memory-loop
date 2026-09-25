---
id: MLOOP-074-FULL
jira_key: '-'
epic_key: EPIC-7-AGENTIC-OBSERVABILITY
status: SHIPPED
type: Feature
title: Runway de Handoffs Multi-Agents et Trajectory Diff Viewer
layer: fullstack
invest_score: 6/6
macrostructure: "workbench"
---
# [EPIC-7-AGENTIC-OBSERVABILITY] Runway de Handoffs Multi-Agents et Trajectory Diff Viewer (MLOOP-074-FULL)

## Description
**En tant qu'** Architecte et Opérateur d'Essaims mLoop,  
**je veux** suivre la chaîne séquentielle des handoffs entre sous-agents dans l'onglet Swarm et comparer les trajectoires contrefactuelles dans le laboratoire Dream RSI,  
**afin de** vérifier visuellement l'absence de boucle infinie et comprendre instantanément pourquoi le harnais optimisé surpasse la trajectoire réelle.

---

## Contexte
L'observabilité des systèmes multi-agents exige de rendre visible la causalité des passages de témoin (*Handoffs*) ainsi que l'explication des échecs évités.
Ce récit combine l'enrichissement de l'onglet Swarm (affichage du runway chronologique de handoff avec statut du PingPongGuard) et de l'onglet Dream RSI (affichage d'un comparateur à double colonne entre la trajectoire réelle $\pi_0$ et la politique simulée $\pi^*$).

---

## Spécifications de l'Interface & UX

### Macrostructure & États de surface
- **Panneau Runway (Onglet Swarm)** : Ligne chronologique horizontale montrant les transferts récents sous forme de bulles reliées : `Orchestrator ➔ Plan ➔ Sentinel [Handoff 2/4]`.
- **Badge Ping-Pong Guard** : Statut holographique vert `🛡️ PING-PONG GUARD : CONFORME (0 boucle / Seuil: 3)`.
- **Comparateur Diff (Onglet Dream RSI)** : Double colonne visuelle comparant étape par étape l'exécution réelle $\pi_0$ et l'exécution simulée $\pi^*$.

### Feedback Utilisateur
- Mise en évidence visuelle de la dernière étape active avec pulsation subtile.

---

## Opérations Métier & Logique Backend

### Matrice des Opérations Backend
| Opération Métier | Contrat / Trigger | Validation & Préconditions | Succès Observable | Gestion Erreurs |
| :--- | :--- | :--- | :--- | :--- |
| **[Flux des Handoffs]** | `GET /api/swarm/handoffs` | Projet valide spécifié en paramètre | Liste ordonnée des transferts récents et statut du PingPongGuard | Retour liste vide si aucun handoff |
| **[Calcul Diff Trajectoires]** | `GET /api/dream-rsi/diff` | Épisodes disponibles dans le projet | Objet comparatif structuré $\pi_0$ vs $\pi^*$ avec étapes et gains | Calcul heuristique sécurisé |

---

## Règles d'affaires
* **[Transparence Causale Complète]** : Tout passage de témoin entre sous-agents doit être représenté avec son agent source, son agent cible et son horodatage local.
* **[Explication Explicite du Gain]** : Le comparateur de trajectoires doit expliciter concrètement la règle ou le goulot éliminé (ex. "Règle INVEST injectée en amont, économisant 11k tokens").

---

## Scénarios de test

```gherkin
# language: fr
Fonctionnalité: Runway de Handoffs Multi-Agents et Trajectory Diff Viewer

  # 1. CHEMIN NOMINAL (Happy Path & Runway Actif)
  Scénario: Affichage du runway des handoffs récents dans l'onglet Swarm
    Étant donné une séquence de 3 délégations entre agents d'un même projet
    Quand l'utilisateur consulte l'onglet Swarm du Cockpit
    Alors la chaîne de handoff affiche graphiquement les 3 étapes reliées
    Et le badge Ping-Pong Guard confirme l'absence de boucle

  # 2. EXCEPTIONS & REJETS MÉTIER (Visualisation d'une Alerte de Boucle)
  Scénario: Alerte visuelle immédiate en cas de disjonction du Ping-Pong Guard
    Étant donné un cycle de récursion détecté par le disjoncteur
    Quand le tableau de bord interroge le statut de l'essaim
    Alors le badge Ping-Pong Guard passe à l'état écarlate "ALERTE BOUCLE DÉTECTÉE"
    Et la dernière liaison du runway est surlignée en rouge

  # 3. RÉSILIENCE TECHNIQUE & MODE DÉGRADÉ (Absence d'Épisodes pour le Diff)
  Scénario: Affichage gracieux du laboratoire Dream RSI en l'absence de replay
    Étant donné un projet nouvellement initialisé sans épisode archivé
    Quand l'onglet Dream RSI charge le comparateur de trajectoires
    Alors l'interface affiche un état vide explicite invitant à générer un premier cycle
    Et aucun plantage JavaScript n'est déclenché

  # 4. UX & OBSERVABILITÉ (Comparateur Contrefactuel à Double Colonne)
  Scénario: Rendu comparatif côte-à-côte des trajectoires réelle et optimisée
    Étant donné un épisode analysé avec succès par le moteur Dream RSI
    Quand le comparateur s'affiche
    Alors la colonne réelle liste les échecs et le coût en tokens
    Et la colonne optimisée montre le chemin épuré et le gain calculé
```
