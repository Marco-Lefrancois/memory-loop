# 📦 Gabarit Normatif : Paquet de Handoff Développeur Tripartite (Inspiration OpenSpec)

- **Autorité** : [ADR-0319](../../standards/adr-system/0319-dual-agent-handoff-openspec-ready.md), [ADR-0366](../../standards/adr-system/0366-standard-story-2.0-handoff-tripartite-et-maillage-referentiel.md)
- **Emplacement SSOT mLoop** : `Projects/<PROJET>/backlog/handoff/<STORY_ID>/`
- **Projection Build Applicatif** : `openspec/changes/<STORY_ID>/` (dans le dépôt de code du développeur)
- **Principe Fondateur** : 100% Markdown déclaratif, zéro snippet de code d'implémentation dans la story, zéro binaire npm/CLI imposé.

---

## Structure du Paquet Tripartite

```
backlog/handoff/<STORY_ID>/
├── proposal.md       <-- Le Pourquoi (Rationale technique, architecture, sécurité)
├── specs/
│   └── api.md        <-- Le Quoi (Contrats d'échange JSON/OpenAPI, codes HTTP)
└── tasks.md          <-- Le Comment (Micro-tâches TDD atomiques < 5 fichiers)
```

---

## 1. Modèle `proposal.md`

```markdown
# Technique Proposal : [Titre Technique de la Modification / Endpoint]

- **Story ID** : <STORY_ID> (Jira: <JIRA_KEY>)
- **Auteur / Émetteur** : Équipe mLoop Swarm & Co-Architecte
- **Date** : YYYY-MM-DD
- **Statut** : DRAFT | READY_FOR_DEV | IMPLEMENTED

## 1. Contexte & Rationale Technique
[Expliquer pourquoi ce changement technique ou cet endpoint est conçu de cette manière.
Préciser les arbitrages techniques, le découpage avec les autres modules et l'alignement avec les principes directeurs.]

## 2. Impact Architectural & Modèle de Données
- **Tables sollicitées (Lecture)** : [Liste des tables SSOT, ex: `Lot`, `Troupeau`, `TypeOeuf`]
- **Tables modifiées (Écriture/Mise à jour)** : [Liste ou "Aucune (Endpoint Read-Only)"]
- **Découplage** : [Expliquer comment l'opération isole ses responsabilités sans effets de bord]

## 3. Sécurité, Performance & Résilience
- **Authentification & Rôles** : [Politique RBAC ou Bearer token requis]
- **Indexation & Requêtes DB** : [Champs indexés indispensables pour les filtres et le tri]
- **Anti-Leak Pagination** : [Confirmation que les calculs de minima et de totaux s'exécutent côté base avant découpage en pages]
- **Gestion de la Concurrence** : [Idempotence, verrous optimistes ou absence d'impact si lecture]
```

---

## 2. Modèle `specs/api.md` (ou `specs/<domaine>.md`)

```markdown
# Spécification Technique d'Échange : [Nom de l'API / Service]

- **Protocole** : HTTP REST / JSON
- **Sécurité** : Bearer JWT (Role: <ROLE_REQUIS>)
- **Idempotence** : Oui (GET sans effet de bord / En-tête Idempotency-Key si POST/PUT)

## 1. Route & Signature
`GET /api/v1/...` (ou `POST /api/v1/...`)

### Paramètres de Requête (Query Params)
| Paramètre | Type | Requis | Description & Validation |
| :--- | :--- | :--- | :--- |
| `date_debut` | `string (YYYY-MM-DD)` | Non | Date ISO 8601 de début de filtrage |
| `page` | `integer` | Non | Numéro de page (défaut: 1) |
| `page_size` | `integer` | Non | Nombre d'éléments par page (défaut: 50, max: 200) |

## 2. Contrats de Schéma (OpenAPI / JSON Schema)

### Réponse Nominale `200 OK`
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "required": ["metadata", "donnees"],
  "properties": {
    "metadata": {
      "type": "object",
      "required": ["total_elements", "page", "page_size"],
      "properties": {
        "total_elements": { "type": "integer" },
        "page": { "type": "integer" },
        "page_size": { "type": "integer" }
      }
    },
    "donnees": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["id", "statut"],
        "properties": {
          "id": { "type": "string" },
          "statut": { "type": "string" }
        }
      }
    }
  }
}
```

### Réponses d'Erreur
- **`400 Bad Request`** : `{ "code": "INVALID_DATE_FORMAT", "message": "Le format attendu est YYYY-MM-DD" }`
- **`500 Internal Error`** : `{ "code": "DATABASE_UNAVAILABLE", "message": "Erreur interne" }`
```

---

## 3. Modèle `tasks.md` (Ingénierie TDD & Beyoncé Rule)

```markdown
# Tasks Breakdown : [Titre Story] (<STORY_ID>)

- **Méthodologie** : Test-Driven Development (Red-Green-Refactor)
- **Règle Fondatrice** : Règle de Beyoncé (*"If you liked it, you should have put a test on it"*)
- **Contrainte d'Atomicité** : Strictement < 5 fichiers modifiés par micro-tâche

## Séquence d'Exécution Ordonnée

### [ ] 1. Harnais de Tests Unitaires & DTOs
- **Fichiers** : `tests/Unit/DTOs/EligibleLotDtoTest.cs`, `src/Domain/DTOs/EligibleLotDto.cs` (< 5 fichiers)
- **Phase Red** : Définir les tests de sérialisation et validation du schéma JSON.
- **Phase Green** : Implémenter le DTO typé et ses validateurs.
- **Phase Refactor** : Simplifier les règles de transformation.

### [ ] 2. Spécification des Règles d'Éligibilité en TDD
- **Fichiers** : `tests/Unit/Services/EligibilityFilterTest.cs`, `src/Domain/Services/EligibilityFilter.cs`
- **Phase Red** : Tests pour chaque critère d'exclusion et de conformité.
- **Phase Green** : Implémenter les prédicats métier purs.
- **Phase Refactor** : Factoriser les conditions avec le domaine métier.

### [ ] 3. Calcul Déterministe des Indicateurs Globaux (Anti-Leak)
- **Fichiers** : `tests/Unit/Services/PriorityCalculatorTest.cs`, `src/Domain/Services/PriorityCalculator.cs`
- **Phase Red** : Test validant que l'ancienneté maximale est calculée sur le stock global avant pagination.
- **Phase Green** : Implémenter la logique d'agrégation globale.
- **Phase Refactor** : Optimiser l'algorithme de tri.

### [ ] 4. Implémentation du Controller / Endpoint API
- **Fichiers** : `tests/Integration/Controllers/InventoryEndpointTest.cs`, `src/Api/Controllers/InventoryController.cs`
- **Phase Red** : Tests d'intégration mockant la base (200 avec données, 200 vide [], 400 format invalide).
- **Phase Green** : Implémenter la route et le câblage de médiation.
- **Phase Refactor** : Assurer l'étanchéité des exceptions.

### [ ] 5. Revue Finale Definition of Done (DoD)
- [ ] Tous les tests automatisés passent à 100%.
- [ ] Couverture de code supérieure au seuil cible.
- [ ] Zéro violation de sécurité OWASP.
- [ ] Synchronisation du statut dans le backlog mLoop.

---

## 4. Section Phase 4 Certification (MLOOP-122-BE)

> Cette section est injectée automatiquement lors du handoff si le projet a franchi la Gate 4.

### Statut de Certification

| Champ | Valeur |
| :--- | :--- |
| **Statut** | `{{ STATUT_CERTIFICATION }}` (`CERTIFIÉ` ou `REJETÉ`) |
| **Date d'approbation** | `{{ DATE_APPROBATION }}` |
| **Approbateur** | `{{ APPROBATEUR }}` |
| **Hash SHA-256 du rapport QA** | `{{ QA_CERTIFICATION_HASH }}` |
| **Lien vers le rapport** | `{{ QA_REPORT_LINK }}` (`memory/evidence/qa_certification_report.json`) |

### Mode Dégradé

> ⚠️ **Avertissement** : Le fichier `qa_certification_report.json` est absent ou inaccessible.
> La certification QA n'est pas traçable dans ce paquet de handoff.
> Le hash SHA-256 ne peut être calculé. La Gate 4 a été approuvée sans preuve de certification persistante.
```
