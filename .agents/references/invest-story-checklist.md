# Checklist Qualité des Récits Utilisateurs (INVEST, 4 Piliers & Story 2.0)

Cette checklist normative régit la validation de toute User Story rédigée par Memory Loop (`backlog/stories/<ID>.md`).
Elle doit être validée par le skill [`plan`](../skills/plan/SKILL.md) et auditée par [`sentinel`](../skills/sentinel/SKILL.md) avant tout handoff technique (ADR-0366).

---

## 1. Critères INVEST Fondamentaux

- [ ] **I - Independent (Indépendant)** : La story peut être développée et livrée sans dépendance bloquante envers une autre story du même sprint. Si une dépendance existe, elle est documentée sous `## Dépendances` avec l'ID précis.
- [ ] **N - Negotiable (Négociable)** : La story spécifie le *Quoi* et les règles d'affaires, sans imposer l'implémentation physique interne au développeur (respect absolu de la frontière No-Code de l'ADR-0319).
- [ ] **V - Valuable (Valeur Métier)** : La valeur apportée à l'utilisateur final ou au système est explicite dans la formulation standard :  
  *En tant que... Je veux... Afin de...*
- [ ] **E - Estimable (Estimable)** : La complexité et le périmètre sont suffisamment clairs pour que l'équipe technique puisse estimer l'effort sans ambiguïté.
- [ ] **S - Small (Suffisamment Petit)** : La story représente une tranche verticale mince (1 à 3 jours de dev). Si la story touche plus de 5 fichiers physiques ou requiert plus de 2 sous-tâches majeures, elle doit être découpée.
- [ ] **T - Testable (Testable)** : Chaque critère d'acceptation est univoque et vérifiable par un test automatisé ou manuel.

---

## 2. Les 4 Piliers Gherkin (Non Négociables)

Chaque User Story DOIT comporter au minimum 4 scénarios Gherkin distincts, un par pilier :

- [ ] **Pilier 1 : Nominal & Happy Path**
  - Cas d'usage principal où tout se déroule normalement.
  - Préconditions claires (`Étant donné que`), actions précises (`Quand`), résultats observables (`Alors`).
- [ ] **Pilier 2 : Erreurs de Validation & Limites Métier**
  - Données invalides, champs obligatoires manquants, dépassement de limites (ex: seuil max, format de date erroné).
  - Messages d'erreur explicites et positionnement dans l'interface spécifiés.
- [ ] **Pilier 3 : Résilience, Concurrence & Défaillances Système**
  - Timeout d'API, coupure réseau, collision d'accès concurrent, indisponibilité de service tiers.
  - Comportement dégradé (*graceful degradation*), idempotence et stratégie de reprise documentés.
- [ ] **Pilier 4 : Expérience Utilisateur, États Vides (Empty State) & Rétroaction**
  - Cas limite de collection vide (*empty state*) impérativement documenté : retour d'une liste vide `[]` avec code `200 OK` (et non `404 Not Found`).
  - Feedback visuel immédiat (spinners, toasts, états de focus) pour le frontend.

---

## 3. Matrice Complète des Call-to-Actions (CTA) *(Frontend / Fullstack)*

Pour tout composant interactif spécifié dans la story :

- [ ] **État Initial / Default** : Libellé, couleur, positionnement conformes aux maquettes SSOT.
- [ ] **État Hover / Focus** : Contraste d'accessibilité (WCAG 2.1 AA) et rétroaction visuelle.
- [ ] **État Active / Pressed** : Rétroaction tactile ou visuelle d'enfoncement.
- [ ] **État Disabled / Inactif** : Règle métier explicite désactivant l'élément + infobulle/tooltip explicative.
- [ ] **État Loading / Traitement** : Désactivation anti-double-clic + indicateur de chargement asynchrone.

---

## 4. Contrats Déclaratifs d'APIs & Garde-fous Épistémiques *(Backend)*

- [ ] **Méthode & Route Canonique** : Verbe HTTP (`GET`, `POST`, `PUT`, `DELETE`, `PATCH`) et URI normalisée.
- [ ] **Format de Date Strict ISO 8601** : Dates d'échange typées explicitement en `YYYY-MM-DD` (ou ISO UTC complet avec millisecondes).
- [ ] **Clause Anti-Leak sur la Pagination** : Les totaux, minima, maxima et critères de priorité biologique ou économique DOIVENT impérativement être calculés côté serveur sur la population totale éligible avant pagination.
- [ ] **Payload Requête & Réponse** : Structure JSON typée avec exemples valides et types primitifs explicites.
- [ ] **Codes d'État HTTP Spécifiés** : `200` (Succès/Liste vide), `400` (Validation), `401/403` (Sécurité), `404` (Ressource spécifique absente), `500` (Erreur interne).
- [ ] **Idempotence Documentée** : Spécifiée pour toute mutation critique.

---

## 5. Intégrité Référentielle & Constellation Documentaire (ADR-0366)

- [ ] **Structure Canonique à 3 Sous-Blocs dans `## Références`** :
  1. `### 1. Preuves Amont & Traçabilité Factuelle` (lien vers `*_fact_dossier.md` et revue Sentinel).
  2. `### 2. Spécifications & Modèles de Données SSOT` (liens vers `Structure-de-données.md`, cas d'usage, ADRs).
  3. `### 3. Handoff Technique Aval & Référentiel Dev` (lien vers `tasks.md`, paquet tripartite et DoD).
- [ ] **Pattern Dual-Link Systématique** : Tout document critique dispose d'un lien Web distant (Azure DevOps / GitHub) **ET** d'un lien workspace local (`file:///...`).
- [ ] **Zéro Route Fantôme & Zéro Snippet de Code** : Aucune URL, colonne DB ou snippet de code inventé ; 100% déclaratif et adossé au socle factuel.
