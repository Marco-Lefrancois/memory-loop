---
id: MLOOP-165-BE
jira_key: ''
epic_key: EPIC-15-DIRECTIVES-SSOT-ENFORCEMENT
type: Feature
title: Contrôle d'Ancrage Visuel des Récits Frontend selon le Principe du Contrat Visuel Premier
tags:
- core
- vibe-check
- guardrail
- visual-contract
origin: GRILL_PROJECT
source_ref: epic_project_directives_ssot_enforcement.md
macro_size: S
status: DONE_TESTED
grill_me: DONE
layer: backend
invest_score: 6/6
created_at: '2026-09-22'
blocked_by:
- MLOOP-163-BE
---
# Contrôle d'Ancrage Visuel des Récits Frontend selon le Principe du Contrat Visuel Premier

---

## Description
**En tant qu'** Analyste fonctionnel mLoop, pour qui le principe du contrat visuel premier est intrinsèque au métier,  
**je veux** qu'un contrôle de pré-vol vérifie, pour tout récit d'interface en phase active, la présence d'une référence de maquette,  
**afin de** matérialiser mécaniquement le principe universel selon lequel les maquettes constituent la source de vérité première, un écran spécifié sans ancrage visuel étant un signal d'alerte pour l'analyse.

---

## Contexte & Périmètre

### Contexte Métier
Le principe du contrat visuel premier est un fondement de la fonction d'analyste fonctionnel : un écran décrit sans ancrage à une maquette est suspect. Le guardrail de pré-vol comporte déjà un contrôle de lisibilité des maquettes, mais aucun contrôle ne vérifie qu'un récit d'interface est effectivement ancré à une maquette. Contrairement aux directives propres à un projet, ce principe est universel à tous les projets comportant une interface et mérite donc un contrôle mécanique dédié plutôt qu'un simple chargement documentaire.

### In-Scope
- Ajout d'un contrôle de pré-vol vérifiant l'ancrage visuel des récits d'interface en phase active.
- Détection multi-sources d'une référence de maquette valide.
- Exclusion explicite des récits sans dimension d'interface.

### Out-of-Scope
- Le contrôle des directives projet et la sémantique tri-état du verdict (couverts par leur récit, dont ce contrôle réutilise le résultat non bloquant).
- La vérification de la lisibilité par reconnaissance de texte des maquettes, déjà couverte par le contrôle existant.

---

## Critères d'acceptation

### Opérations Métier & Logique Backend *(backend)*

#### 1. Contrôle d'Ancrage Visuel des Récits d'Interface
* **Entrée Métier** : Les récits du projet actif et leur couche déclarée dans leur en-tête.
* **Règles d'admissibilité & Validation** : Le contrôle ne s'applique qu'aux récits déclarant une couche d'interface ou mixte, et uniquement en phase active. Les récits strictement de service sont exclus.
* **Traitement & Algorithme Métier** : Pour chaque récit concerné, recherche d'au moins une référence de maquette parmi plusieurs sources reconnues, en réutilisant la logique de traversée du contrôle de lisibilité existant.
* **Résultat Métier & Mutations** : Un état d'avertissement listant les récits d'interface dépourvus d'ancrage visuel, ou un état de réussite si tous sont ancrés.
* **Cas de Rejet Métier** : Aucun échec bloquant n'est émis. Un récit d'interface sans ancrage produit exclusivement un avertissement.

---

## Règles d'affaires

- **[Cible Interface en Phase Active]** : Le contrôle ne s'applique qu'aux récits dont l'en-tête déclare une couche d'interface ou mixte, et uniquement en phase active. Les récits strictement de service sont explicitement exclus.
- **[Détection Multi-Sources d'Ancrage]** : Une référence de maquette valide est reconnue si le récit contient au moins l'un des éléments suivants : un lien vers le répertoire des actifs visuels, un lien vers l'outil de maquettage, ou une section dédiée aux maquettes de source de vérité. L'absence des trois déclenche l'alerte.
- **[Sévérité Avertissement]** : Toute détection d'un récit d'interface sans ancrage visuel produit un avertissement, jamais un échec, et liste les récits concernés.
- **[Réutilisation de l'Infrastructure Existante]** : L'implémentation étend la logique du contrôle de lisibilité des maquettes existant plutôt que de dupliquer la traversée des récits.

---

## Contrats UI & API Backend → Profil B

### Matrice des Contrats API

> **Contexte** : Ce récit étend un pipeline interne du guardrail de pré-vol. Aucune API HTTP n'est exposée : les interfaces sont des appels de fonction Python internes. Conformément à ADR-0319, l'absence de routes HTTP est consignée via la question ouverte **OQ-165-01**.

| Méthode | Interface interne | Finalité |
|:---|:---|:---|
| Fonction | `src.pipelines.vibe_check:run_vibe_check` | Guardrail de pré-vol ; extension de la logique du contrôle de lisibilité des maquettes |
| Contrôle | Nouveau bloc de contrôle « Ancrage Visuel des Récits Frontend » | Vérification conditionnelle non bloquante des récits d'interface |

**Question Ouverte (Exemption ADR-0319)** :
- **OQ-165-01** : Ce récit étend une fonction Python interne du guardrail. Aucune API HTTP n'est exposée ni consommée. **[API de soumission à définir — sans objet pour un pipeline interne]**

---

## Références

### 1. Preuves Amont & Traçabilité Factuelle
- 📂 **Backlog d'Épopée** : [`backlog/epic_project_directives_ssot_enforcement.md`](../epics/epic_project_directives_ssot_enforcement.md)
- 📂 **Dossier de Preuves Factuelles** : [`memory/evidence/MLOOP-165-BE_fact_dossier.md`](../../memory/evidence/MLOOP-165-BE_fact_dossier.md)
- 📄 **Récit Préalable** : Contrôle de Pré-Vol d'Intégrité des Directives Projet et Sémantique Tri-État (récit bloquant amont pour la sévérité non bloquante)

### 2. Spécifications & Modèles de Données SSOT
- 📜 **Pipeline de Guardrail de Pré-Vol** : [`src/pipelines/vibe_check.py`](../../../../src/pipelines/vibe_check.py)
- 📜 **Principe du Contrat Visuel** : charte d'instructions racine, section des interdictions absolues relatives aux maquettes comme source de vérité

---

## Scénarios de test

```gherkin
# language: fr
Fonctionnalité: Contrôle d'Ancrage Visuel des Récits Frontend

  # CHEMIN NOMINAL
  Scénario: Récit d'interface correctement ancré
    Étant donné un récit d'interface en phase active comportant une section de maquettes de source de vérité
    Quand le contrôle d'ancrage visuel s'exécute
    Alors le récit est reconnu comme ancré
    Et aucun avertissement n'est émis pour ce récit

  # EXCEPTIONS & REJETS MÉTIER
  Scénario: Récit d'interface sans ancrage maquette
    Étant donné un récit d'interface en phase active sans aucun lien de maquette ni section dédiée
    Quand le guardrail de pré-vol est exécuté
    Alors le contrôle d'ancrage visuel émet un avertissement
    Et le message liste l'identifiant du récit non ancré

  # RÉSILIENCE & EXCLUSION
  Scénario: Récit de service non concerné
    Étant donné un récit strictement de service sans référence de maquette
    Quand le contrôle d'ancrage visuel s'exécute
    Alors ce récit est ignoré comme hors périmètre
    Et il ne génère aucun avertissement d'ancrage visuel

  # OBSERVABILITÉ & DÉTECTION MULTI-SOURCES
  Scénario: Reconnaissance des différentes sources d'ancrage
    Étant donné plusieurs récits d'interface ancrés par des sources différentes
    Quand le contrôle inspecte chaque récit
    Alors un lien vers les actifs visuels, un lien de maquettage ou une section dédiée sont tous reconnus comme ancrage valide
    Et seuls les récits dépourvus des trois sources sont signalés
```