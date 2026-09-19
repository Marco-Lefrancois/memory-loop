# 👕 Dimensionnement Budgétaire & Macro-Estimation (T-Shirt Size) - [NOM_DU_PROJET]

> [!NOTE]
> **Norme Méthodologique** : ADR-0375 (Cycle de Vie en 5 Phases & Typologie d'Analyses).  
> Ce document formalise l'estimation macroscopique préalable d'avant-projet pour décision d'affaires et cadrage d'enveloppe budgétaire.  
> **Ratio de Conversion Standard** : **1 000 $ CAD / jour de développement senior**.

---

## 1. Métadonnées de Cadrage
- **Projet** : `[NOM_DU_PROJET]`
- **Date d'Émission** : `[DATE_ISO]`
- **Responsable de l'Évaluation** : IA mLoop / Lead Architecte
- **Documents Sources Ingérés** : `docs/00-ingested/`
- **Statut de l'Analyse** : `DRAFT` | `EN_REVUE` | `APPROUVÉ`
- **Statut Contractuel Associé** : Avant-Projet (Préalable optionnel au SOW)

---

## 2. Grille de Référence Kevin Chamberland (Tailles T-Shirt)

| Taille | Fourchette Jours (Effort) | Coût Estimé (Ratio 1 000 $/j) | Profil Type de Travail |
| :---: | :---: | :---: | :--- |
| **XS** | 1 à 2 jours | 1 000 $ - 2 000 $ | Configuration simple, script unitaire, écran statique, ajustement d'API existante. |
| **S** | 3 à 5 jours | 3 000 $ - 5 000 $ | Composant CRUD standard, écran métier interactif, connecteur webhook léger. |
| **M** | 6 à 10 jours | 6 000 $ - 10 000 $ | Module métier complet, flux transactionnel, intégration d'un SDK tiers avec résilience. |
| **L** | 11 à 15 jours | 11 000 $ - 15 000 $ | Sous-système structurant, moteur de calcul asynchrone, refonte d'architecture transversale. |
| **XL** | 16 à 25 jours | 16 000 $ - 25 000 $ | Initiative majeure multi-modules, pipeline ETL de données critiques, migration d'infrastructure. |

---

## 3. Backlog Sommaire de Dimensionnement (Macro-Briques)

> *Chaque ligne ci-dessous sera découpée ultérieurement en User Stories de Palier 1 (`story_draft_template.md`) lors de la transition vers la planification active.*

| Réf. | Macro-Brique Fonctionnelle / Technique | Composant | Taille | Fourchette Jours | Coût Estimé ($ CAD) | Risque & Hypothèses Clés |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| `TS-01` | **[Nom de la brique 1]** | Backend | **S** | 3 - 5 j | 3 000 $ - 5 000 $ | Dépendance SDK disponible et documentée. |
| `TS-02` | **[Nom de la brique 2]** | Frontend | **M** | 6 - 8 j | 6 000 $ - 8 000 $ | Maquettes UI stabilisées dans Figma. |
| `TS-03` | **[Nom de la brique 3]** | Data / Sync | **S** | 4 - 5 j | 4 000 $ - 5 000 $ | Accès aux bases sources accordé. |
| `TS-04` | **Gouvernance, CI/CD & Tests d'Intégration** | DevOps | **XS** | 2 - 2 j | 2 000 $ - 2 000 $ | Environnements de staging opérationnels. |

---

## 4. Tableau des Exclusions Explicites de Périmètre (Out-of-Scope)

> [!CAUTION]
> Les éléments ci-dessous sont **formellement exclus** de la présente enveloppe d'avant-projet pour éliminer tout risque de glissement de périmètre (*Scope Creep*).

| Réf. Excl. | Domaine / Fonctionnalité Exclue | Rationale / Justification | Impact Budgétaire |
| :--- | :--- | :--- | :---: |
| `EX-01` | **[Exclusion 1 : ex: Application mobile native]** | Hors mandat initial (focalisation Web/Desktop). | `-` (0 j / 0 $) |
| `EX-02` | **[Exclusion 2 : ex: Migration des données historiques > 5 ans]** | Données froides traitées dans un lot séparé. | `-` (0 j / 0 $) |
| `EX-03` | **[Exclusion 3 : ex: Support multilingue espagnol]** | Seuls le français et l'anglais sont retenus pour la V1. | `-` (0 j / 0 $) |

---

## 5. Synthèse Financière Consolidée

| Indicateur | Valeur Basse (Optimiste) | Valeur Haute (Conservatrice) |
| :--- | :---: | :---: |
| **Effort Total Estimé** | **[MIN_JOURS] jours** | **[MAX_JOURS] jours** |
| **Enveloppe Financière Globale** | **[MIN_BUDGET] $ CAD** | **[MAX_BUDGET] $ CAD** |
| **Provision pour Aléas / Incertitude (+15%)** | [ALEAS_MIN] $ CAD | [ALEAS_MAX] $ CAD |
| **Enveloppe Cible Recommandée** | \- | **[ENVELOPPE_CIBLE] $ CAD** |

---

## 6. Décision & Prochaines Étapes
- [ ] **Option A : Accord sur l'Enveloppe** ➔ Déclenchement de la rédaction du **SOW Contractuel** (`python src/swarm.py to-sow`).
- [ ] **Option B : Démarrage Agile Direct** ➔ Découpage direct en récits de cadrage `DRAFT` (`python src/swarm.py to-tickets`).
- [ ] **Option C : Révision du Périmètre** ➔ Session contradictoire Grill-Me Macro (`python src/swarm.py grill-project`).
