# 📂 Dossier de Preuves Documentaires — `MLOOP-320-BE` : Formalisation Normative & Triangulation des Standards

---

### 1. 📜 Sources Physiques Normatives & Extraits Verbatim

#### Source 1 : [`standards/adr-system/0393-decouplage-modalite-grill-scope-anti-cascade.md`](file:///C:/Memory%20Loop/standards/adr-system/0393-decouplage-modalite-grill-scope-anti-cascade.md) (Lignes 23-45)
> **Extrait 1 — Découplage Format vs Scope (Lignes 25-35) :**  
> *« 1. Axe 1 — Format de Dialogue (--format) : ATOMIC (1 question par tour) vs ROUND (2 à 4 questions orthogonales).  
> 2. Axe 2 — Périmètre d'Arbitrage (--scope) : STORY (unitaire) vs EPIC/PROJECT (transverse).  
> Règle d'or : Choisir un format ROUND ne modifie en rien le périmètre d'analyse et ne constitue EN AUCUN CAS un ordre de rédaction de code ou de story. »*  
> ➔ **Fait établi** : La modalité de questionnement est totalement orthogonale au périmètre et à la décision de rédaction.

> **Extrait 2 — Règle d'Arrêt Formel Post-Grill (Lignes 37-47) :**  
> *« Dès que la frontière de décision d'un round macro est déclarée vide, l'agent a l'interdiction formelle d'enchaîner sur la rédaction de récits. L'unique livrable d'alignement autorisé est la consignation de la décision dans l'ADR et CONTEXT.md. L'agent clôt impérativement son message par un menu d'orientation fermé. »*  
> ➔ **Fait établi** : L'arrêt d'écriture après un round macro est un invariant déterministe strict.

---

#### Source 2 : [`standards/protocols/STORY_LIFECYCLE_PROTOCOL.md`](file:///C:/Memory%20Loop/standards/protocols/STORY_LIFECYCLE_PROTOCOL.md) (Lignes 37-54 et 107-111)
> **Extrait 3 — Autorité Exclusive Gate 2 (Lignes 43-44) :**  
> *« READY_FOR_GROOMING : État maximal atteignable par l'IA. DoR 6/6, 4 piliers Gherkin, audit Sentinel PASS.  
> READY_FOR_DEV : Validation Humaine Exclusive. Interdiction formelle à l'IA. Arbitrage humain validant l'engagement physique. »*  
> ➔ **Fait établi** : Toute tentative de l'agent d'auto-promouvoir un récit vers `READY_FOR_DEV` est une infraction directe au protocole.

---

#### Source 3 : [`standards/adr-system/0320-grill-me-frontier-design-tree-alignment.md`](file:///C:/Memory%20Loop/standards/adr-system/0320-grill-me-frontier-design-tree-alignment.md) (§F, Lignes 55-67)
> **Extrait 4 — Dérive d'Interprétation de l'Avancement Automatique :**  
> *« Dès que la frontière d'un récit donné est vide (...), l'agent DOIT immédiatement arrêter d'interroger sur ce récit (...). L'agent avance automatiquement au récit suivant de la liste dès la finalisation actée. »*  
> ➔ **Fait établi** : Cette clause a été formulée pour le dépouillement séquentiel d'un lot en grooming 1:1, mais a été détournée par l'agent pour justifier un bulk-spawning après un cadrage macro.

---

### 2. 🎯 Contrat Déclaratif Cible (Triangulation Normative à Sceller)
1. **`standards/protocols/STORY_LIFECYCLE_PROTOCOL.md`** :
   - Insertion de la section normée *« 2.3 Règle d'Arrêt Formel Post-Grill & Barrière d'Écriture »*.
   - Définition explicite de l'interdiction de cascade autonome (*Auto-Spawning Cascade*).
2. **`AGENTS.md`** :
   - Ajout dans la section 4.1 (*Directives Impératives*) d'un article dédié au découplage `Format (Atomic/Round)` vs `Scope (Story/Epic)`.
3. **`standards/adr-system/0320-grill-me-frontier-design-tree-alignment.md`** :
   - Amendement de la section §F pour restreindre formellement l'avancement automatique au rituel de grooming unitaire déjà consenti par l'humain.

---

### 3. 🔍 Frontière Active & Questions d'Arbitrage pour `MLOOP-320-BE`
- Frontière de décision active : 2 questions ouvertes relatives à la formalisation du déclencheur d'écriture post-grill.
