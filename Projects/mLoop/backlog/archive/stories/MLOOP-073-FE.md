---
id: MLOOP-073-FE
jira_key: '-'
epic_key: EPIC-7-AGENTIC-OBSERVABILITY
status: SHIPPED
type: Feature
title: Jauge Contextuelle Dynamique 3 Zones par Session
layer: frontend
invest_score: 6/6
macrostructure: "workbench"
---
# [EPIC-7-AGENTIC-OBSERVABILITY] Jauge Contextuelle Dynamique 3 Zones par Session (MLOOP-073-FE)

## Description
**En tant qu'** Analyste ou Pilote du Cockpit mLoop,  
**je veux** visualiser en temps réel la charge de saturation contextuelle de ma session active selon les 3 zones cognitives (Smart, Caution, Dumb Zone),  
**afin d'** anticiper les dérives d'amnésie et déclencher un compactage ou une isolation de sous-agent avant toute hallucination.

---

## Contexte
L'ADR-0324 définit rigoureusement trois paliers d'attention des LLMs : la zone optimale (🟢 0-40%), la zone de vigilance (🟡 40-60%), et la zone de décrochage cognitif (🔴 >60% dite Dumb Zone).
Ce récit implémente dans l'en-tête de navigation du Cockpit 2.0 (`src/dashboard/static/index.html`) le widget dynamique `#header-context-gauge` qui s'actualise à chaque cycle de télémétrie (5s) ou lors d'un changement de projet.

---

## Spécifications de l'Interface & UX

### Macrostructure & États de surface
- **État Initial / Nominal (Smart Zone < 40%)** : Badge discret vert émeraude `[ 🟢 SMART ZONE : 24% ]` avec ratio de tokens (ex. 31k / 128k).
- **État de Vigilance (Caution Zone 40-60%)** : Badge ambre `[ 🟡 CAUTION : 48% ]` avec infobulle invitant au compactage de session.
- **État Critique (Dumb Zone > 60%)** : Badge écarlate clignotant `[ 🔴 DUMB ZONE : 72% ]` avec signal d'alerte visuelle recommandant l'isolation Clean-Slate.
- **État Chargement** : Affichage temporaire `[ 🕒 CONTEXT : ... ]` pendant la première interrogation API.

### États d'Interaction
- **Survol (Hover)** : Affichage d'une infobulle technique détaillant : tokens estimés, fenêtre totale allouée, recommandation de l'ADR-0324.
- **Clic** : Déclenche l'affichage d'un panneau d'hygiène contextuelle avec raccourci vers la commande de compactage ou de flush.

### Feedback Utilisateur
- Transition de couleur CSS fluide (animée en 300ms) entre les zones d'alerte.

---

## Règles d'affaires
* **[Plafond Critique de Dumb Zone]** : Dès que l'occupation contextuelle de la session dépasse 60%, le badge doit obligatoirement basculer en mode alerte visuelle rouge.
* **[Calibrage Dynamique par Session]** : Le pourcentage calculé doit refléter la charge réelle de la session en cours et non un chiffre théorique statique.
* **[Non-Régression F5]** : L'état d'affichage de la jauge s'actualise immédiatement lors d'un rafraîchissement F5 sans masquer les autres indicateurs d'en-tête.

---

## Scénarios de test

```gherkin
# language: fr
Fonctionnalité: Jauge Contextuelle Dynamique 3 Zones par Session

  # 1. CHEMIN NOMINAL (Happy Path & Affichage Smart Zone)
  Scénario: Affichage nominal de la jauge en zone d'attention optimale
    Étant donné une session active consommant 25 000 tokens sur une fenêtre de 128 000
    Quand le tableau de bord interroge les métriques de contexte
    Alors le badge d'en-tête affiche "🟢 SMART ZONE : 20%"
    Et la bordure et le texte adoptent la nuance vert émeraude

  # 2. EXCEPTIONS & REJETS MÉTIER (Transition en Caution Zone)
  Scénario: Alerte visuelle modérée lors du franchissement du seuil de 40%
    Étant donné une session ayant accumulé 55 000 tokens sur 128 000
    Quand la jauge s'actualise
    Alors le badge bascule au format "🟡 CAUTION ZONE : 43%"
    Et le texte d'infobulle recommande un compactage préventif

  # 3. RÉSILIENCE TECHNIQUE & MODE DÉGRADÉ (Alerte Critique Dumb Zone)
  Scénario: Alerte critique clignotante lors du franchissement de la Dumb Zone
    Étant donné une charge contextuelle atteignant 85 000 tokens soit plus de 60%
    Quand l'indicateur évalue la charge
    Alors le badge passe au rouge écarlate avec animation clignotante "🔴 DUMB ZONE : 66%"
    Et le message d'avertissement conseille une scission vers un worker clean-slate

  # 4. UX & OBSERVABILITÉ (Persistance et Actualisation sans Décalage)
  Scénario: Actualisation automatique de la jauge lors du changement de projet
    Étant donné un utilisateur changeant de projet actif dans le sélecteur d'en-tête
    Quand le nouveau projet est sélectionné
    Alors la jauge recalcule instantanément la saturation contextuelle du projet cible
    Et l'horloge locale et les autres balises d'en-tête restent stables
```
