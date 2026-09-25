---
id: MLOOP-172-BE
jira_key: ''
epic_key: EPIC-17-MODULAR-REFACTORING
type: standard
title: Pattern d'Extraction Modulaire Réutilisable (Rétrocompatibilité Imports)
origin: DIRECT_REQUIREMENT
source_ref: EPIC-17/epic_modular_refactoring_ast_debt.md §3
macro_size: S
status: DONE_TESTED
grill_me: DONE
invest_score: 6/6
layer: backend
blocked_by: []
created_at: '2026-09-22'
content_hash: c2b1a295af6bc4e7
ttl_cycles: 4
---

# 📖 Pattern d'Extraction Modulaire Réutilisable

## 1. Intention Métier (User Story)
**En tant que** Ingénieur du framework,
**je veux** un pattern d'extraction documenté dans `standards/protocols/` et validé sur le récit pilote,
**afin d'** appliquer une méthode cohérente et sûre aux 38 fichiers restants en dette (39 - pilote).

---

## 2. Origine & Cadrage Avant-Projet
- **Document Source** : `Projects/mLoop/backlog/epic_modular_refactoring_ast_debt.md` (§3)
- **Faits vérifiés** : le pattern sera extrait de l'expérience réelle du refactoring `vibe_check.py` (MLOOP-170-BE), pas théorique ; l'épopée cible 39 fichiers (audit frais) dont le top : `_registry.py` 2028L, `server.py` 1632L, `svg_to_md.py` 991L
- **Enveloppe Macro Estimée** : S (1-2 jours)

---

## 3. Périmètre Sommaire
### In-Scope (Macro)
- Rédaction de `standards/protocols/MODULAR_EXTRACTION_PROTOCOL.md` (structure, étapes, garanties, checklist non-régression)
- Éventuel gabarit de plan d'extraction (`standards/blueprints/`)
- Validation du pattern sur un second fichier (application pilote indépendante)

### Out-of-Scope (Macro)
- L'exécution des lots de refactoring (récits dédiés à découper ensuite)
- Les dérogations ADR (traitées au cas par cas en Grill)

---

## 4. Critères de Succès Préliminaires
- [ ] Protocole documenté avec pattern issu du pilote
- [ ] Application validée sur un second module (< 300L, zéro import cassé)

---

## 6. Arbitrages Grill-Me Micro 1:1 (Séance du 2026-09-22)
> ✅ Séance tenue (1 question par tour, arbitrages verbatim PO ; frontière close 3/3).

| OQ | Décision Arbitrée |
|:---|:---|
| OQ-172-01 | **Couverture exhaustive dès la v1** — section dédiée par cas spécial (registres déclaratifs, singletons d'état, effets de bord à l'import), chacune avec contre-exemples |
| OQ-172-02 | **Check d'imports résolus (test de fumée)** — léger, exigé à chaque lot, sans comparaison exhaustive de surface AST |
| OQ-172-03 | **Nouveau contrôle Vibe-Check dédié** — conformité au protocole armée en Phase 3 BUILD : plan d'extraction présent + check fumée vert, en complément du RULE-AST-01 existant |

---

## Critères d'acceptation

### Opérations Métier & Logique Backend

#### 1. Protocole v1 Exhaustif (OQ-172-01)
- [ ] `standards/protocols/MODULAR_EXTRACTION_PROTOCOL.md` couvre le cas général (issu du pilote MLOOP-170-BE) **et** les 3 cas spéciaux avec contre-exemples : registres déclaratifs, singletons d'état, effets de bord à l'import
- [ ] Checklist de non-régression intégrée au protocole

#### 2. Garantie d'Extraction Réussie
- [ ] Application validée sur un second module indépendant (< 300L, zéro import cassé)

#### 3. Armement des Contrôles (OQ-172-02 / OQ-172-03)
- [ ] Check de fumée (imports résolus) exécutable et exigé à chaque lot
- [ ] Nouveau contrôle Vibe-Check en Phase 3 BUILD : plan d'extraction présent + fumée verte (en complément du RULE-AST-01)

### Scénarios de test (Gherkin 4 Piliers)

#### Pilier 1 — Chemin Nominal
```gherkin
Scénario : Extraction conforme au protocole
  Étant donné un module en dépassement RULE-AST-01
  Quand un lot d'extraction applique le protocole
  Alors le plan d'extraction existe et le check de fumée est vert
  Et le module extrait respecte le plafond de 300 lignes
```

#### Pilier 2 — Exceptions & Rejets
```gherkin
Scénario : Lot sans plan d'extraction rejeté
  Étant donné un commit de refactoring modulaire sans plan d'extraction associé
  Quand le Vibe-Check Phase 3 s'exécute
  Alors le contrôle de conformité échoue et le lot est rejeté
```

#### Pilier 3 — Résilience & Mode Dégradé
```gherkin
Scénario : Import cassé détecté par la fumée
  Étant donné une extraction ayant supprimé un symbole encore importé par un caller
  Quand le check de fumée s'exécute
  Alors l'import non résolu est signalé avec le fichier caller exact
  Et le lot est marqué en échec avant intégration
```

#### Pilier 4 — UX & Observabilité
```gherkin
Scénario : Protocole actionnable par tout agent
  Étant donné un développeur ou agent aval découvrant le protocole
  Quand il lit MODULAR_EXTRACTION_PROTOCOL.md
  Alors les étapes, garanties et contre-exemples sont directement applicables sans contexte additionnel
```

---

## Contrats UI & API Backend → Profil B

### Matrice des Contrats API
> **Exemption déclarée (ADR-0319)** : artefact de protocole documentaire (`standards/protocols/`) — **aucune route HTTP n'est consommée ni exposée**. Toute route découverte en cours d'implémentation fera l'objet d'une question ouverte `OQ-172` avec la mention `[API de soumission à définir]` — jamais inventée (Zéro Fausse Route, AGENTS.md).

| Contrat | Engagement |
|:---|:---|
| `standards/protocols/MODULAR_EXTRACTION_PROTOCOL.md` | Protocole v1 exhaustif (cas général + 3 cas spéciaux + contre-exemples + checklist) |
| Check de fumée imports | Exécutable à chaque lot, signale l'import non résolu avec le caller exact |
| Vibe-Check Phase 3 | Contrôle conformité protocole : plan présent + fumée verte (en complément RULE-AST-01) |
