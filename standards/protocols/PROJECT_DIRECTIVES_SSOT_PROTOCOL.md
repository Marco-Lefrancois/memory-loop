# 📜 Protocole de Hiérarchie SSOT & Chargement des Directives Projet

**Statut** : Norme Fondatrice Inviolable (ADR-0384)
**Date d'effet** : Septembre 2026
**Autorité** : Architecte en Chef & Équipe Core mLoop
**Champ d'Application** : Tout cadrage, audit, analyse ou délégation opérée par un agent mLoop sur un projet, en Phase ≥ 2 (PLAN & ANALYSE).

---

## 1. Raison d'Être

Un agent qui agit sans avoir localisé la source de vérité canonique d'un projet audite sur des documents non autoritaires et produit des diagnostics erronés (ex. faux « conflit de modèle de données »). Le principe « les directives d'un projet sont ses lois fondamentales » était documenté mais jamais opposable. Ce protocole le rend déterministe et citable.

---

## 2. Hiérarchie Documentaire à Trois Niveaux (Inviolable)

| Niveau | Source | Autorité |
| :---: | :--- | :--- |
| **1 — Canonique** | La source de vérité déclarée par le projet dans ses directives (ex. modèle de données consolidé sous `docs/03-models/`). | **Fait foi absolue.** |
| **2 — Amont** | Sources d'ingestion amont (ex. `docs/00-ingested/`). | **Non autoritaire** en cas de divergence avec le niveau 1. |
| **3 — Staging** | Matière première brute locale (`reference/`). | **Jamais lue directement, jamais autoritaire.** |

> **Règle d'or** : en cas de divergence entre deux niveaux, le niveau supérieur prime toujours. Toute divergence est consignée comme incohérence sourcée, sans inventer de structure de remplacement.

---

## 3. Obligation de Localisation Avant Délégation

Avant de déléguer une tâche d'audit ou d'analyse à un sous-agent (`task`, `worker-spawn`), l'orchestrateur DOIT :

1. Lire `directives/tech.md` et `directives/business.md` du projet actif s'ils existent.
2. Identifier la source de vérité canonique déclarée.
3. **Citer** cette source dans le brief transmis au sous-agent.

**Interdiction de brief non sourcé** : aucun brief ne doit référencer un chemin de modèle de données qui n'a pas été préalablement confirmé comme source de vérité canonique.

---

## 4. Deux Mécanismes de Gouvernance (Une Seule Exigence : la Considération Obligatoire)

- **Mécanisme A — Contrôle mécanique générique** : pour les principes universels codables en dur, valables pour TOUS les projets. Exemple : le **Contrat Visuel Premier** (un récit d'interface sans ancrage maquette est un signal d'alerte).
- **Mécanisme B — Chargement forcé + lecture obligatoire** : pour les directives propres à un projet, quel que soit leur contenu présent ou futur. Le framework n'a pas besoin de « connaître » ces directives ; il garantit que l'agent les a **lues avant d'agir**.

---

## 5. Catalogue de Directives Projet Impératives (Cas Réels)

Ces directives ne sont **pas** des exemples négligeables : ce sont des impératifs à considération obligatoire, couverts par le Mécanisme B.

- **Périmètre Déprécié** : des identifiants de récits formellement dépréciés et archivés ne doivent pas être réutilisés silencieusement (risque de collision d'identifiants).
- **Règles de Saisie Transverses** : conventions d'interface imposées à l'échelle du projet (ex. saisie en delta uniquement, raccourci de sélection maximale, verrouillage de validation conditionnel).

> Toute directive projet, présente ou future, est couverte par le chargement obligatoire sans nécessiter de codage spécifique dans le cœur du framework.
