---
story_id: MLOOP-175-BE
dossier_status: VALIDATED
created_at: 2026-09-23T15:08:56Z
updated_at: 2026-09-23T15:08:56Z
sources_hashes:
  source_1: epic17_prioritization_matrix
  source_2: modular_extraction_protocol
---

# Dossier de Preuves Documentaires & Cadrage — `MLOOP-175-BE` (Extraction Modulaire de src/commands/_registry.py — Registre Déclaratif CLI (BR=3, 2028L))

> **Titre Fonctionnel Pur** : Extraction Modulaire de src/commands/_registry.py — Registre Déclaratif CLI (BR=3, 2028L)  
> **Epic Jira** : `EPIC-17-MODULAR-REFACTORING` (Extraction Modulaire RULE-AST-01)  
> **Couche** : `backend`  
> **Récit Précédent / Dépendances** : [`MLOOP-172-BE.md`](file:///C:/Memory%20Loop/Projects/mLoop/backlog/stories/MLOOP-172-BE.md)

---

### 1. Sources Physiques & Maquettes SSOT (Liens Directs Cliquables)

| Source SSOT | Nature du Document | Lien Repo Local |
| :--- | :--- | :--- |
| **Maquette Principale** | — | *N/A - Composant Headless* |
| **Cible d'extraction** | Code source monolithique | [`src/commands/_registry.py`](file:///C:/Memory%20Loop/src/commands/_registry.py) |
| **Protocole SSOT** | Règle d'extraction modulaire | [MODULAR_EXTRACTION_PROTOCOL.md](file:///C:/Memory%20Loop/standards/protocols/MODULAR_EXTRACTION_PROTOCOL.md) |
| **Matrice priorisation** | Blast radius & ordre Lot | [epic17_prioritization_matrix.md](file:///C:/Memory%20Loop/Projects/mLoop/memory/evidence/epic17_prioritization_matrix.md) |
| **Gabarit dossier** | Template officiel | [dossier_de_preuves_template.md](file:///C:/Memory%20Loop/standards/blueprints/dossier_de_preuves_template.md) |

> *Note Headless* : Récit de refactoring modulaire 100% headless — aucune interface visuelle, le code source physique `src/commands/_registry.py` est la source principale.

---

### 1.1 Matrice de Résolution des Conflits de Sources

| Conflit Identifié | Source A | Source B | Décision Retenue |
| :--- | :--- | :--- | :--- |
| *N/A — zéro conflit de sources détecté* | — | — | — |

---

### 2. Extraits Verbatim Sourcés (Passage-Level Grounding)

> NOTE
**Extrait 1 — Registre monolithique 2028 lignes**  
**Source** : [`src/commands/_registry.py`](file:///C:/Memory%20Loop/src/commands/_registry.py)  
*« Le fichier src/commands/_registry.py pèse 2028 lignes (73.1 Ko) — soit 6,7× le plafond RULE-AST-01 de 300 lignes — avec le dict COMMANDS s'étendant des lignes 32 à 2028 et déclarant 122 clés uniques de commandes CLI réparties sur 22 sections thématiques. »*  
➔ **Fait établi** : 2028L, 73.1 Ko, COMMANDS L32-2028, 122 clés uniques, BR=3 callers..

> NOTE
**Extrait 2 — Doublons de clés dernier gagne**  
**Source** : [`src/commands/_registry.py`](file:///C:/Memory%20Loop/src/commands/_registry.py)  
*« Trois doublons de clés détectés dans le dict COMMANDS : dream, story-clean (L414 vs L562) et drawdb ×2 — en Python, lorsqu'une clé est réassignée dans un dict literal, la dernière définition écrase les précédentes (comportement dernier gagne à préserver). »*  
➔ **Fait établi** : 3 doublons (dream, story-clean, drawdb) — comportement dict dernier gagne préservé..

> NOTE
**Extrait 3 — ADR-0370 anti-drift guide CLI**  
**Source** : [`standards/adr-system/0370`](file:///C:/Memory%20Loop/standards/adr-system/0370)  
*« L'ADR-0370 impose que toute modification du registre _registry.py soit immédiatement suivie de l'exécution de python src/swarm.py guide --sync pour maintenir le guide CLI_PIPELINE_GUIDE.md en parité stricte — contrôle vérifié par le 15e contrôle Vibe-Check. »*  
➔ **Fait établi** : guide --sync exécuté une fois en fin de story, parité 100% guide CLI (Vibe-Check 15)..

---

### 3. Schéma de Données & Tables Clés

Pas d'entité transactionnelle : récit purement structurel (refactoring modulaire), zéro schéma DB modifié.

---

### 4. Contrats Déclaratifs Cibles

* **Backend** : `N/A - Exemption ADR-0319` — aucune route HTTP n'est consommée ni exposée. Exemption déclarée avec `OQ-175` + `[API de soumission à definir]`.
* **Contrat d'import (shim)** : `from src.commands._registry import *` résout tous les symboles publics historiques sans `ImportError`.
* **Plafond** : chaque sous-module ≤ 300 L / 15 Ko (RULE-AST-01 PASS via `code-check --file`).

---

### 5. Evaluation de la Frontiere Active

#### CAS A — Arbitrages tranches en Grill-Me 1:1 : Decisions Consignees

| Question Grill | Decision Arbitree |
| :--- | :--- |
| Q1 — Granularité des domaines | Option B (7 domaines agrégés) — hypothèse 5 phases réfutée F3, 22 sections réelles |
| Q2 — Dispatcher actuel | pré-résolu F5 — COMMANDS conservé, zéro rename |
| Q3 — Import circulaire latent | pré-résolu F4 — zéro, seul import lazy worker_runtimes |

> **Frontiere close** — toutes les questions d'arbitrage ont ete tranchees en session Grill-Me 1:1 contradictoire (frontiere epuisee), puis approuvees par l'humain (batch APPROVE 2026-09-23). Zero question ouverte residuelle.
