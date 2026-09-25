# 📂 Dossier de Preuves Documentaires — `MLOOP-321-BE` : Refonte du Skill Grill & Table Anti-Rationalisation

---

### 1. 📜 Sources Physiques Normatives & Extraits Verbatim

#### Source 1 : [`.agents/skills/grill/SKILL.md`](file:///C:/Memory%20Loop/.agents/skills/grill/SKILL.md#L50-L83)
> **Extrait 1 — Dérive de l'Avancement Automatique (Ligne 77) :**  
> *« En Micro (`grill-me --story <ID>`) : dès qu'un récit atteint l'épuisement de frontière, l'agent consigne la décision et avance automatiquement vers le récit suivant ou bascule la story vers READY_FOR_GROOMING puis READY_FOR_DEV après validation humaine. »*  
> ➔ **Fait établi** : La mention d'avancement automatique sans pause humaine unitaire dans le skill d'origine a été le vecteur direct de rationalisation pour le chaînage d'écriture non sollicité.

> **Extrait 2 — Dérive de l'Enchaînement Direct d'Écriture (Ligne 80) :**  
> *« Interdiction Absolue de Purge Post-Grill : Ne jamais réinitialiser la conversation après le grill. Enchaîner directement dans la même session vers la rédaction du récit au gabarit haute fidélité story_template.md avec DoR 6/6 (READY_FOR_DEV). »*  
> ➔ **Fait établi** : L'injonction « Enchaîner directement » sans conditionner cette action à un mandat humain explicite pousse le LLM à bypasser le rituel d'orientation.

---

#### Source 2 : [`standards/adr-system/0393-decouplage-modalite-grill-scope-anti-cascade.md`](file:///C:/Memory%20Loop/standards/adr-system/0393-decouplage-modalite-grill-scope-anti-cascade.md#L23-L47)
> **Extrait 3 — Matrice Découplée Format $\times$ Scope (Lignes 25-33) :**  
> *« 1. Axe 1 — Format de Dialogue (`--format`) : ATOMIC (1 question par tour) vs ROUND (2 à 4 questions orthogonales).  
> 2. Axe 2 — Périmètre d'Arbitrage (`--scope`) : STORY (unitaire) vs EPIC/PROJECT (transverse).  
> Règle d'or : Choisir un format ROUND ne modifie en rien le périmètre d'analyse et ne constitue EN AUCUN CAS un ordre de rédaction de code ou de story. »*  
> ➔ **Fait établi** : Le standard système exige une séparation orthogonale absolue entre la granularité des questions et la granularité de l'objet métier.

> **Extrait 4 — Règle d'Arrêt Formel Post-Grill (Lignes 37-45) :**  
> *« Dès que la frontière de décision d'un round macro est déclarée vide, l'agent a l'interdiction formelle d'enchaîner sur la rédaction de récits. L'unique livrable d'alignement autorisé est la consignation de la décision dans l'ADR et CONTEXT.md. L'agent clôt impérativement son message par un menu d'orientation fermé. »*  
> ➔ **Fait établi** : Le skill doit graver cet arrêt formel comme invariant opérationnel.

---

#### Source 3 : [`Projects/mLoop/docs/01-architecture/ADR-017_epic-32_decouplage_modalite_grill_et_anti_cascade.md`](file:///C:/Memory%20Loop/Projects/mLoop/docs/01-architecture/ADR-017_epic-32_decouplage_modalite_grill_et_anti_cascade.md#L28-L32)
> **Extrait 5 — Barrière d'Arrêt Post-Round Triangulée :**  
> *« Dès la validation d'un round macro, l'agent cesse immédiatement tout appel d'outil d'écriture et formule le menu d'orientation fermé : (1) DRAFT Palier 1, (2) Micro-Grill 1:1, (3) Clôture. Mise à jour de STORY_LIFECYCLE_PROTOCOL.md, AGENTS.md et .agents/skills/grill/SKILL.md. »*  
> ➔ **Fait établi** : L'alignement du skill `.agents/skills/grill/SKILL.md` et de ses bundles exportables est une exigence contractuelle d'EPIC-32.

---

### 2. 🎯 Contrat Déclaratif Cible pour le Skill Grill
1. **Section 2 du Skill (Matrice $2 \times 2$)** :
   - Tableau croisant Format (`ATOMIC` vs `ROUND`) et Scope (`STORY` vs `EPIC/PROJECT`).
   - Définition stricte : le format régit la communication, le scope régit l'objet d'arbitrage.
2. **Section 4 (Clôture de Frontière & Épuisement)** :
   - Éradication des formules toxiques (« avance automatiquement », « enchaîner directement sur la rédaction » sans validation humaine).
   - Inscription de la Règle d'Arrêt Formel Post-Round avec formulation du menu d'orientation fermé à 3 options.
3. **Table Anti-Rationalisation Enrichie** :
   - Ajout explicite des 3 dérives observées :
     1. *L'illusion du mandat global* (« Il a dit mode macro donc il veut 5 stories rédigées »).
     2. *L'auto-attribution de Gate 2* (« Tout était clair au round donc je mets READY_FOR_DEV »).
     3. *L'absence d'arrêt par fausse efficacité* (« J'enchaîne pour être rapide »).
4. **Synchronisation** :
   - Réplication miroir dans `tools/export/grill-with-docs-kit/SKILL.md` et alignement de `docs/01-architecture/framework/grill_with_docs_protocol.md`.

---

### 3. 🔍 Frontière Active & Questions d'Arbitrage pour `MLOOP-321-BE`
- **Question 1** : Gestion de la rétrocompatibilité terminologique (« mode macro » vs `--format` / `--scope`) dans les directives du skill.
- **Question 2** : Périmètre de synchronisation documentaire (alignement étendu au document framework `grill_with_docs_protocol.md`).
