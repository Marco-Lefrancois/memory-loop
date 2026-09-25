---
id: MLOOP-162-BE
jira_key: ''
epic_key: EPIC-15-DIRECTIVES-SSOT-ENFORCEMENT
type: Feature
title: Renforcement de l'Étape Search-Before-Ask du Skill d'Entrevue par la Localisation SSOT
tags:
- skills
- grill
- governance
- ssot
origin: GRILL_PROJECT
source_ref: epic_project_directives_ssot_enforcement.md
macro_size: S
status: DONE_TESTED
grill_me: DONE
layer: backend
invest_score: 6/6
created_at: '2026-09-22'
blocked_by:
- MLOOP-161-BE
---
# Renforcement de l'Étape Search-Before-Ask du Skill d'Entrevue par la Localisation SSOT

---

## Description
**En tant qu'** Agent exécutant une session d'entrevue de cadrage, qu'elle soit macro ou micro,  
**je veux** que l'étape préliminaire de recherche préalable m'oblige explicitement à localiser et citer la source de vérité canonique via les directives du projet avant toute formulation de question ou toute délégation à un sous-agent,  
**afin de** ne plus jamais reproduire l'erreur de source qui a conduit à un audit sur des documents amont non autoritaires.

---

## Contexte & Périmètre

### Contexte Métier
Le skill d'entrevue guide la discipline d'interrogatoire et de cadrage contradictoire. Son étape préliminaire de recherche préalable impose déjà d'interroger l'index de recherche et le contexte du projet pour arbitrer les faits contre les décisions. Cependant, elle ne mentionne pas explicitement l'obligation de localiser la source de vérité canonique via les directives avant d'agir. Cette omission a permis qu'un brief de délégation référence des chemins de modèle de données non confirmés comme autoritaires. Ce récit corrige la lacune au niveau de la compétence portable elle-même.

### In-Scope
- Ajout, dans l'étape préliminaire de recherche préalable du skill d'entrevue, d'une exigence de localisation et de citation de la source de vérité canonique via les directives du projet.
- Formalisation d'un ordre de recherche imposé plaçant les directives en tête.
- Interdiction explicite de transmettre à un sous-agent un brief référençant un chemin de modèle de données non confirmé comme canonique.

### Out-of-Scope
- Le contrôle automatique de pré-vol vérifiant la présence des directives (couvert par le récit du guardrail).
- La rédaction du protocole normatif et de l'ADR (couverts par leurs récits respectifs).

---

## Critères d'acceptation

### Opérations Métier & Logique Backend *(backend)*

#### 1. Enrichissement de l'Étape de Recherche Préalable
* **Entrée Métier** : Le contenu actuel de l'étape préliminaire de recherche préalable du skill d'entrevue et le protocole normatif de hiérarchie SSOT.
* **Règles d'admissibilité & Validation** : L'ajout doit préserver la structure existante du skill et rester cohérent avec le protocole normatif, sans dupliquer son contenu mais en le référençant.
* **Traitement & Algorithme Métier** : Insertion d'une consigne de localisation SSOT, d'un ordre de recherche imposé et d'une interdiction de brief non sourcé.
* **Résultat Métier & Mutations** : Le skill d'entrevue mis à jour reflète fidèlement la nouvelle discipline de localisation préalable.
* **Cas de Rejet Métier** : Une mise à jour qui n'imposerait pas la lecture des directives avant la première question, ou qui autoriserait implicitement un brief non sourcé, est refusée.

---

## Règles d'affaires

- **[Ordre de Recherche Imposé]** : L'étape préliminaire précise un ordre de recherche plaçant en tête les directives d'affaires et techniques du projet, puis la charte d'instructions du projet, puis la documentation d'architecture, avant toute recherche textuelle générale.
- **[Interdiction de Brief Non Sourcé]** : Aucun brief transmis à un sous-agent ne doit référencer un chemin de modèle de données sans que ce chemin ait été préalablement confirmé comme source de vérité canonique.
- **[Citation Obligatoire dans le Dossier de Preuves]** : La hiérarchie SSOT identifiée est citée dans le dossier de preuves de la session d'entrevue.

---

## Contrats UI & API Backend → Profil B

### Matrice des Contrats API

> **Contexte** : Ce récit enrichit une compétence portable Markdown (skill grill). Aucune API HTTP n'est exposée. Conformément à ADR-0319, l'absence de routes HTTP est consignée via la question ouverte **OQ-162-01**.

| Méthode | Route | Finalité |
|:---|:---|:---|
| N/A | N/A | Récit de gouvernance documentaire — aucune interface réseau |

**Question Ouverte (Exemption ADR-0319)** :
- **OQ-162-01** : Ce récit modifie le fichier SKILL.md du skill d'entrevue. Aucune API HTTP n'est exposée ni consommée. **[API de soumission à définir — sans objet pour un artefact documentaire]**

---

## Références

### 1. Preuves Amont & Traçabilité Factuelle
- 📂 **Backlog d'Épopée** : [`backlog/epic_project_directives_ssot_enforcement.md`](../epics/epic_project_directives_ssot_enforcement.md)
- 📂 **Dossier de Preuves Factuelles** : [`memory/evidence/MLOOP-162-BE_fact_dossier.md`](../../memory/evidence/MLOOP-162-BE_fact_dossier.md)
- 📄 **Récits Préalables** : Protocole Normatif de Hiérarchie SSOT et ADR de Boot Enforcement (récits bloquants amont)

### 2. Spécifications & Modèles de Données SSOT
- 📜 **Compétence d'Entrevue** : [`.agents/skills/grill/SKILL.md`](../../../../.agents/skills/grill/SKILL.md)
- 📜 **Protocole Normatif de Hiérarchie SSOT** : à créer sous le répertoire des protocoles standards

---

## Scénarios de test

```gherkin
# language: fr
Fonctionnalité: Renforcement de l'Étape Search-Before-Ask par la Localisation SSOT

  # CHEMIN NOMINAL
  Scénario: Entrevue avec localisation SSOT préalable
    Étant donné une session d'entrevue sur un projet disposant de directives
    Quand l'agent exécute l'étape préliminaire de recherche préalable
    Alors il lit les directives d'affaires et techniques avant toute question
    Et il cite la hiérarchie de source de vérité identifiée dans le dossier de preuves

  # EXCEPTIONS & REJETS MÉTIER
  Scénario: Blocage d'un brief de délégation non sourcé
    Étant donné un agent préparant la délégation d'un audit
    Mais qu'il n'a pas confirmé le chemin du modèle de données comme canonique
    Quand il tente de transmettre le brief au sous-agent
    Alors la discipline du skill interdit la transmission
    Et impose d'abord la confirmation de la source de vérité canonique

  # RÉSILIENCE & COHÉRENCE
  Scénario: Projet dépourvu de directives
    Étant donné une session d'entrevue sur un projet sans répertoire de directives
    Quand l'agent exécute l'étape de recherche préalable
    Alors il applique l'ordre de recherche sur les sources disponibles
    Et il documente l'absence de directives sans inventer de source autoritaire

  # OBSERVABILITÉ & TRAÇABILITÉ
  Scénario: Traçabilité de l'ordre de recherche appliqué
    Étant donné une session d'entrevue terminée
    Quand le dossier de preuves est consulté
    Alors l'ordre de recherche appliqué est visible
    Et la source de vérité canonique retenue est citée explicitement
```