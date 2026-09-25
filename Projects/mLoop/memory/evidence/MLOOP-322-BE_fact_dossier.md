# 📂 Dossier de Preuves Documentaires — `MLOOP-322-BE` : Garde Mécanique FSM & Verrou Anti-Promotion Directe

---

### 1. 📜 Sources Physiques Normatives & Extraits Verbatim

#### Source 1 : [`src/pipelines/state_machine.py`](file:///C:/Memory%20Loop/src/pipelines/state_machine.py#L47-L54)
> **Extrait 1 — Brèche FSM Directe DRAFT ➔ READY_FOR_DEV (Lignes 47-54) :**  
> ```python
> ALLOWED_TRANSITIONS = {
>     StoryStatus.DRAFT: [
>         StoryStatus.OPEN,
>         StoryStatus.IN_ANALYZE,
>         StoryStatus.READY_FOR_GROOMING,
>         StoryStatus.READY_FOR_DEV,  # <--- BRÈCHE IDENTIFIÉE
>         StoryStatus.ON_HOLD,
>         StoryStatus.ERROR,
>     ],
> ```  
> ➔ **Fait établi** : La table FSM permettait historiquement de sauter directement de `DRAFT` à `READY_FOR_DEV` sans passer par `IN_ANALYZE` ni `READY_FOR_GROOMING`, violant la machine à états canonique en 5 phases (ADR-0391).

---

#### Source 2 : [`src/pipelines/grill/_engine.py`](file:///C:/Memory%20Loop/src/pipelines/grill/_engine.py#L160-L206)
> **Extrait 2 — Promotion dans `mark_story_grilled` (Lignes 196-198) :**  
> ```python
> current_status = StoryStatus.from_raw(data.get("status", "OPEN"))
> engine.validate_transition(current_status, StoryStatus.READY_FOR_GROOMING)
> data["status"] = StoryStatus.READY_FOR_GROOMING.value
> ```  
> ➔ **Fait établi** : Le moteur promeut bien à `READY_FOR_GROOMING`, mais ne dispose pas d'assertion fail-closed interdisant explicitement `READY_FOR_DEV`, ni d'exception dédiée `LifecycleAuthorityError`.

---

#### Source 3 : [`src/pipelines/grill/_cli_handler.py`](file:///C:/Memory%20Loop/src/pipelines/grill/_cli_handler.py#L51-L54)
> **Extrait 3 — Détermination du Mode Macro vs Micro :**  
> ```python
> ge = GrillEngine(project_path)
> story_id = getattr(args, "story", None)
> is_macro = story_id is None
> ```  
> ➔ **Fait établi** : Lorsque `is_macro = True` (`grill-project` ou absence de `--story`), aucune barrière logicielle n'interdisait formellement l'accès en écriture au dossier `backlog/stories/`.

---

#### Source 4 : [`Projects/mLoop/docs/01-architecture/ADR-017_epic-32_decouplage_modalite_grill_et_anti_cascade.md`](file:///C:/Memory%20Loop/Projects/mLoop/docs/01-architecture/ADR-017_epic-32_decouplage_modalite_grill_et_anti_cascade.md#L20-L24)
> **Extrait 4 — Décision d'Architecture 1 (Fail-Closed Strict) :**  
> *« 1. Fail-Closed Strict sur la Mutation de Récits (MLOOP-322-BE) :  
> - Interdiction programmatique absolue pour une commande transverse (grill-project ou scope EPIC) de muter les fichiers de backlog/stories/.  
> - Levée immédiate d'une exception LifecycleAuthorityError en cas d'infraction.  
> - Bridage mécanique de GrillEngine.mark_story_grilled() à READY_FOR_GROOMING (zéro auto-promotion en READY_FOR_DEV). »*  
> ➔ **Fait établi** : `MLOOP-322-BE` est le garant physique de cette sécurité d'exécution.

---

### 2. 🎯 Contrat Déclaratif Cible (Garde Mécanique)
1. **`src/pipelines/state_machine.py`** :
   - Suppression de `StoryStatus.READY_FOR_DEV` depuis `StoryStatus.DRAFT` et `StoryStatus.OPEN` dans `ALLOWED_TRANSITIONS`. Seul `StoryStatus.READY_FOR_GROOMING` peut transiter vers `StoryStatus.READY_FOR_DEV`.
   - Création de la classe d'exception `LifecycleAuthorityError(StateTransitionError)`.
2. **`src/pipelines/grill/_engine.py`** :
   - Vérification stricte dans `mark_story_grilled` : si le statut cible requis ou inféré est `READY_FOR_DEV`, levée immédiate de `LifecycleAuthorityError`.
   - Ajout d'une méthode de protection `assert_no_story_mutation(scope: str)` pour bloquer toute écriture dans `backlog/stories/` en mode transverse.
3. **`src/pipelines/grill/_cli_handler.py`** :
   - Blocage à l'entrée de toute option non autorisée tentant d'imposer un statut `READY_FOR_DEV`.

---

### 3. 🔍 Frontière Active & Questions d'Arbitrage pour `MLOOP-322-BE`
- **Question 1** : Comportement de sanction de `LifecycleAuthorityError` (Fail-Closed bloquant avec journalisation de sécurité vs fallback silencieux).
- **Question 2** : Éligibilité de transition : vérification de présence obligatoire des champs `validated_by` et `validated_at` dès la transition vers `READY_FOR_DEV`.
