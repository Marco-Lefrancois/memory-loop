# ADR-0301 : Standard Gherkin Outlines & Règle des 4 Piliers Obligatoires
## Statut : Accepté (Série 03xx - BDD Quality)

---

## 1. Contexte & Amendement de Durcissement

L'ADR-0017 (mai 2026) autorisait de différer la résilience technique pour privilégier le "100% Happy Path". Cette tolérance a causé des régressions lors des recettes fonctionnelles.

---

## 2. Décision (Amendement 2026-06)

Nous imposons la **Règle Formelle et Non-Négociable des 4 Piliers Gherkin** pour tout récit rédigé sous mLoop :

Tout bloc Gherkin doit comporter au moins **4 scénarios distincts** couvrant :
1. **Chemin Nominal (Happy Path)** : Succès fonctionnel et persistance.
2. **Exceptions & Rejets Métier** : Respect des règles `RM-XXX`, erreurs HTTP 400/409.
3. **Résilience Technique & Mode Dégradé** : Timeouts, idempotence, coupure réseau, rejets d'API.
4. **UX & Observabilité** : Spinners, toasts, boutons grisés, redirections et logs d'audit.

### Amendement de Propreté & Anti-Pollution (Gouvernance mLoop RHO) :
- **Nettoyage des Commentaires d'Échafaudage** : Les lignes de commentaires (`# PILIER 1 : CHEMIN NOMINAL`, `# PILIER 2...`) sont des guides d'analyse temporaires (scaffolding). **Interdiction formelle** de les inclure dans le bloc `gherkin` rédigé final. Les 4 piliers doivent être déclinés uniquement par des scénarios distincts purs (`Scénario: ...`).
- **Pureté du Titre de la Fonctionnalité** : La ligne `Fonctionnalité:` contient **exclusivement le nom métier pur**. Interdiction absolue d'y insérer des clés d'identifiants entre parenthèses ou préfixes (ex: Ne JAMAIS écrire `Fonctionnalité: Nom (REC-007 / COUVBOIRE-736)`).
- **Standardisation des Préfixes de Règles Métier (Rule #7 - Amendement 2026-09)** : Afin d'assurer une traçabilité déterministe et binaire entre les exigences métier et le Pilier 2 Gherkin, chaque règle d'affaires dans la section `## Règles d'affaires` doit porter un identifiant formel préfixé en gras selon le standard canonique : `* **RM-XXX [Nom de la Règle]** : [Formulation explicite de la contrainte, du calcul ou du comportement attendu]` (ex: `RM-101`, `RM-102`). Les scénarios du Pilier 2 (*Exceptions & Rejets Métier*) doivent explicitement tester le rejet lié à ces identifiants (ex: `Scénario: Rejet pour non-respect de la règle RM-101`). Sont formellement proscrits les identifiants temporaires ad-hoc non normés (ex: `RM-TEMP`, `RM-TODO`, `WIP`).

**Validation Déterministe :**
La commande `python src/swarm.py wikifix` contrôle la conformité de la DoR et l'absence de fuites. L'absence d'un pilier ou le non-respect des règles rejette la validation avec un Exit Code non nul.

---

## 3. Conséquences

- **Zéro Malentendu** : Couverture d'acceptation complète avant le dev.
- **Auto-Audit** : Validation mécanique de la DoR.
