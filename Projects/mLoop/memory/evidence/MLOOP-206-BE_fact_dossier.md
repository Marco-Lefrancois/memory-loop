# 📑 Dossier de Preuves Documentaires — MLOOP-206-BE

```yaml
story_id: MLOOP-206-BE
project: mLoop
created_at: '2026-09-24'
status: ACTIVE
standard: mLoop Epistemic Grounding Protocol 1.0
sources_fingerprints:
  - path: Projects/mLoop/backlog/epic_portfolio_governance_2026q4.md
    observed: '2026-09-24'
  - path: Projects/mLoop/backlog/stories/MLOOP-206-BE.md
    observed: '2026-09-24'
  - path: standards/adr-system/0342-modular-project-architecture-and-subdomain-isolation.md
    observed: '2026-09-24'
  - path: Projects/Metro_FOOD/backlog/stories/RBC_Avion/ST-100-historique-transactions-avion.md
    observed: '2026-09-24'
  - path: Projects/Metro_COMMERCE/backlog/stories/RBC_Avion/ST-101-historique-transactions-avion-commerce.md
    observed: '2026-09-24'
  - path: Projects/Metro_FOOD/AGENTS.md
    observed: '2026-09-24'
  - path: Projects/Metro_COMMERCE/AGENTS.md
    observed: '2026-09-24'
  - path: Projects/Metro_FOOD/backlog/stories/OneTrust_FOOD/
    observed: '2026-09-24'
  - path: Projects/Metro_COMMERCE/backlog/stories/OneTrust_COMMERCE/
    observed: '2026-09-24'
  - path: Projects/Metro_SANTE/backlog/stories/OneTrust_SANTE/
    observed: '2026-09-24'
```

---

## 1. Sources Physiques & Notes d'Atelier

- 📂 Épopée gouvernance : [`file:///C:/Memory%20Loop/Projects/mLoop/backlog/epic_portfolio_governance_2026q4.md`](file:///C:/Memory%20Loop/Projects/mLoop/backlog/epic_portfolio_governance_2026q4.md)
- 📂 Récit cible (haute fidélité) : [`file:///C:/Memory%20Loop/Projects/mLoop/backlog/stories/MLOOP-206-BE.md`](file:///C:/Memory%20Loop/Projects/mLoop/backlog/stories/MLOOP-206-BE.md)
- 📜 ADR modulaire (grille §4) : [`file:///C:/Memory%20Loop/standards/adr-system/0342-modular-project-architecture-and-subdomain-isolation.md`](file:///C:/Memory%20Loop/standards/adr-system/0342-modular-project-architecture-and-subdomain-isolation.md)
- 📄 RBC ST-100 FOOD : [`file:///C:/Memory%20Loop/Projects/Metro_FOOD/backlog/stories/RBC_Avion/ST-100-historique-transactions-avion.md`](file:///C:/Memory%20Loop/Projects/Metro_FOOD/backlog/stories/RBC_Avion/ST-100-historique-transactions-avion.md)
- 📄 RBC ST-101 COMMERCE : [`file:///C:/Memory%20Loop/Projects/Metro_COMMERCE/backlog/stories/RBC_Avion/ST-101-historique-transactions-avion-commerce.md`](file:///C:/Memory%20Loop/Projects/Metro_COMMERCE/backlog/stories/RBC_Avion/ST-101-historique-transactions-avion-commerce.md)
- 📖 AGENTS FOOD : [`file:///C:/Memory%20Loop/Projects/Metro_FOOD/AGENTS.md`](file:///C:/Memory%20Loop/Projects/Metro_FOOD/AGENTS.md)
- 📖 AGENTS COMMERCE : [`file:///C:/Memory%20Loop/Projects/Metro_COMMERCE/AGENTS.md`](file:///C:/Memory%20Loop/Projects/Metro_COMMERCE/AGENTS.md)
- 📂 OneTrust FOOD (20 récits) : [`file:///C:/Memory%20Loop/Projects/Metro_FOOD/backlog/stories/OneTrust_FOOD/`](file:///C:/Memory%20Loop/Projects/Metro_FOOD/backlog/stories/OneTrust_FOOD/)
- 📂 OneTrust COMMERCE (16 récits) : [`file:///C:/Memory%20Loop/Projects/Metro_COMMERCE/backlog/stories/OneTrust_COMMERCE/`](file:///C:/Memory%20Loop/Projects/Metro_COMMERCE/backlog/stories/OneTrust_COMMERCE/)
- 📂 OneTrust SANTÉ (9 récits) : [`file:///C:/Memory%20Loop/Projects/Metro_SANTE/backlog/stories/OneTrust_SANTE/`](file:///C:/Memory%20Loop/Projects/Metro_SANTE/backlog/stories/OneTrust_SANTE/)
- 📜 Protocole dossiers : [`file:///C:/Memory%20Loop/standards/protocols/DOSSIER_DE_PREUVES_PROTOCOL.md`](file:///C:/Memory%20Loop/standards/protocols/DOSSIER_DE_PREUVES_PROTOCOL.md)

---

## 2. Matrice de Résolution des Conflits

| Sujet | Assertion initiale | Résolution | Gagnant |
| :--- | :--- | :--- | :--- |
| Nature des « doublons » OneTrust | 3 récits strictement identiques à purger en 1 canonical | **Variantes légitimes par bounded context** : 3 initiatives × 45 récits (20+16+9), apps et bannières distinctes | **Constat disque** (globs + AGENTS.md) |
| Matrice d'arbitrage ADR-0342 | §3 = matrice de déduplication (fusion/canonical/dépréciation) | **Prémisse rejetée** : ADR-0342 n'a aucune §3 de déduplication ; §3 = baux OWNS:, §4 = Projet Distinct vs Sous-Module | **Lecture intégrale ADR** (92 L) |
| Stratégie d'arbitrage | Q1=A purge canonical (draft) | **C** hybride ciblé : OneTrust parenté sans fusion, RBC audit strict sur grille §4, prémisse corrigée | **Q1 = C** (PO) |
| Traitement RBC | Fusion en 1 récit ou dépréciation | **i** parenté sans fusion : verdict §4 = coexistence ; lien `related:` croisé uniquement | **Q2a = i** (PO) |
| Profondeur matrice OneTrust | Exhaustif 1:1 (45 récits) vs macro | **α** macro 8–10 thèmes de haut niveau, IDs par ligne, `—` si absent | **Q2b = α** (PO) |
| Action Jira / statuts | Won't Fix sur les doublons | **a** aucun Won't Fix, aucun retrait de tableau, zéro mutation de statut | **Q2c = a** (PO) |
| Titre du récit | « Grill-project transverse — arbitrage… §3 » | **I** « Cartographie de parenté des initiatives OneTrust multi-codebase et RBC Avion » | **Q3a = I** (PO) |
| Portée des liens RBC | Recommandés seulement (β) | **α** liens croisés inclus dans le feu vert d'exécution | **Q3b = α** (PO) |
| Taille macro | S (0,5–1 j) | **XS** : travail documentaire + 2 liens frontmatter | **Q3c = XS** (PO) |

---

## 3. Extraits Verbatim Sourcés (Lignes Précises)

**Extrait 1 — epic_portfolio_governance_2026q4.md (L23) : «  dette structurelle  | Naming modulaire inégal, OneTrust ×3, RBC ×2, phase badge-atomique »** ➔ Fait établi : l'épopée qualifie la présence multiple de « ×3 » et « ×2 » de dette, sans préciser s'il s'agit de récits stricts ou d'initiatives par codebase — ambiguïtés que le draft a mal résolue.

**Extrait 2 — MLOOP-206-BE.md draft (L6, L22, L38, L54) : « matrice ADR-0342 §3 (fusion / canonical owner / dépréciation) »** ➔ Fait établi : le draft invoque une section qui n'existe pas — prémisse hallucinée, corrigée dans le récit haute fidélité.

**Extrait 3 — 0342-modular-project-architecture-and-subdomain-isolation.md (L64–L69, §3) : « Isolation des Baux de Concurrence (OWNS:) par Module… OWNS: backlog/stories/02-incubation/** »** ➔ Fait établi : la §3 de l'ADR porte sur les baux de concurrence, pas sur une matrice de déduplication de récits.

**Extrait 4 — 0342-modular (L71–L80, §4) : « Matrice d'Arbitrage : Projet Distinct vs Sous-Module | Documentation & Wiki | Identique / Partagé → Sous-Module | Complètement distinct → Projet Distinct »** ➔ Fait établi : la seule matrice d'arbitrage existante oppose projet unifié (partage docs/schémas) à projet distinct (séparation complète) — appliquée aux apps FOOD vs COMMERCE, elle mène à la coexistence (apps et backlogs séparés, documentation métier partagée au niveau programme).

**Extrait 5 — AGENTS.md FOOD (L24–L25) : « RBC Avion | backlog/stories/RBC_Avion/ | Programme Avion RBC × Loyauté Moi | ST-100+ » et « OneTrust FOOD | backlog/stories/OneTrust_FOOD/ | Conformité CMP / Loi 25 / RGPD — codebase FOOD | MMA-4637+ »** ➔ Fait établi : le guide agentique FOOD déclare explicitement ces initiatives comme propres à la codebase FOOD — intention structurante, pas accident de duplication.

**Extrait 6 — AGENTS.md COMMERCE (L21–L22) : « OneTrust COMMERCE | backlog/stories/OneTrust_COMMERCE/ | Conformité CMP / Loi 25 / RGPD — codebase COMMERCE | MMA-4638+ » et « RBC Avion | backlog/stories/RBC_Avion/ | Programme Avion RBC × Loyauté Moi (côté commerce) | ST-101+ »** ➔ Fait établi : même intention structurante côté COMMERCE, préfixes Jira distincts (MMA-4638+ vs MMA-4637+), clés RBC distinctes (ST-101+ vs ST-100+).

**Extrait 7 — ST-100 (L2–L10) : « id: ST-100 | jira_key: MMA-4630 | epic_key: MMA-4629 | status: BACKLOG | layer: frontend » / « # Food | Affichage des conversions RBC Avion dans l'historique Moi »** ➔ Fait établi : ST-100 est rattachée à l'épique MMA-4629, statut BACKLOG, périmètre MAUI FOOD.

**Extrait 8 — ST-101 (L2–L10) : « id: ST-101 | jira_key: MMA-4631 | epic_key: MMA-4629 | status: OPEN | layer: frontend » / « # Commerce | Affichage des conversions RBC Avion dans l'historique Moi… sur les applications Jean Coutu et Brunet »** ➔ Fait établi : ST-101 partage l'épique MMA-4629 mais cible les apps Pharma (Jean Coutu, Brunet), statut OPEN — variante légitime par codebase, pas doublon strict.

**Extrait 9 — ST-100 (L44) vs ST-101 (L44) : « composants Loyalty_ProgramTransactionCard.xaml et TransactionViewModel.cs » vs « composants MoiTransactionCard.xaml (dans Pharma) et TransactionViewModel.cs (dans Pharma.Application) »** ➔ Fait établi : composants physiques distincts entre FOOD et COMMERCE — fusion impossible sans cross-project coupling, cohérent avec verdict §4 « Projet Distinct ».

**Extrait 10 — Inventaire OneTrust (globs 2026-09-24) : OneTrust_FOOD = 20 fichiers · OneTrust_COMMERCE = 16 fichiers · OneTrust_SANTE = 9 fichiers · total = 45** ➔ Fait établi : « ×3 » du draft = 3 initiatives, pas 3 récits — erreur de lecture factorielle corrigée.

---

## 4. Matrice de Correspondance Macro OneTrust (Q2b = α)

| # | Thème | FOOD (20) | COMMERCE (16) | SANTÉ (9) |
| :-: | :--- | :--- | :--- | :--- |
| 1 | Spike validation .NET 10 / OneTrust | `MMA-4637` | `MMA-4638` | `US-00` |
| 2 | Bannière de consentement / Refonte UX | `MMA-4704` | `MMA-4706`, `MMA-4684`†, `MMA-4686` | `US-03` |
| 3 | Centre de préférences / Refonte UX | `MMA-4705`, `MMA-4658`, `MMA-4659` | `MMA-4708`, `MMA-4685` | `US-04` |
| 4 | Transmission SSO WebView (Base64) | `MMA-4663` | `MMA-4688` | — |
| 5 | Firebase Analytics / Performance C0002 | `MMA-4668` | `MMA-4690` | `US-05` |
| 6 | Firebase Messaging / Push C0001 | `MMA-4672` | `MMA-4691` | — |
| 7 | AppInsights C0001 / purge UserId | `MMA-4676` | `MMA-4694` | — |
| 8 | In-App Review Google Play C0001 | `MMA-4677` | `MMA-4696` | — |
| 9 | Résilience consentement hors-ligne | `MMA-OFFLINE-DRAFT` | — | — |
| 10 | Cycle de vie / infrastructure / persistance | `MMA-4664` (event handlers) | `MMA-4682` (init SDK), `MMA-4687` (persistance), `MMA-4692` (UTM), `MMA-4693` (auto-tracking iOS), `MMA-4695` (GTM) | `US-01`, `US-02`, `US-06`, `US-07`, `US-08` |

† `MMA-4684` = `SUPERSEDED` par `MMA-4706` (refonte UX approuvée) — statut interne COMMERCE, hors purge 206.

**Inventaire total** : FOOD 20 + COMMERCE 16 + SANTÉ 9 = **45 récits**, tous conservés.

---

## 5. Contrats Déclaratifs Cibles & Verdict §4 RBC

### Verdict RBC (grille §4 ADR-0342)

| Critère §4 | ST-100 (FOOD) | ST-101 (COMMERCE) | Colonne retenue |
| :--- | :--- | :--- | :--- |
| Documentation & Wiki | RBC_Avion FOOD | RBC_Avion COMMERCE (docs parallèles, SOW commun PJ737) | Partagé au programme, distinct au dépôt |
| Modèle de données | Loyalty API / GET /transactions | Loyalty API / GET /transactions (même endpoint) | Partagé |
| Flux métier | Conversion Avion → Moi | Conversion Avion → Moi | Partagé |
| Dépôt / Apps | MAUI FOOD (6 apps) | Pharma.App COMMERCE (4 apps) | **Distinct** |
| Gouvernance backlog | sprint_backlog FOOD | sprint_backlog COMMERCE | **Distinct** |

**Verdict** : colonne « Projet mLoop Distinct » pour les axes apps/backlog → **coexistence + parenté**, zéro fusion, zéro dépréciation. Action : `related:` croisé uniquement.

### Contrats déclaratifs
- Aucune route API (récit gouvernance documentaire) — **OQ-206** exemption ADR-0319.
- Écritures cibles : frontmatter `related:` ST-100, ST-101 (après feu vert) + artefacts mLoop.

---

## 6. Frontière Active & Admission of Limits

- **Ce que ce dossier prouve** : prémisse §3 inexistante ; comptage 45 récits ; verdict §4 = coexistence ; décisions de grill C/i/α/a/I/α/XS ; liens de parenté tracés.
- **Ce qu'il ne prouve pas** : que l'alignement exhaustif 1:1 des 45 récits est sans écart (hors périmètre, dette) ; que Jira ne contient pas déjà des liens de parenté (hors périmètre) ; que les apps FOOD/COMMERCE partagent un dépôt Git unique (SOW PJ737 distinct, apps séparées).
- **Frontière active** : zéro mutation de statut OneTrust/RBC ; liens RBC sous feu vert humain ; Jira hors scope.
- **Dettes nominatives** : alignement 1:1 ; normalisation titres SANTE legacy (H1 sans `title:` YAML sur 8/9) ; poussée Jira éventuelle.
