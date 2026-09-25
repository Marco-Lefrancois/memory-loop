# Dossier de Preuves Documentaires — MLOOP-151-FE
> Grill-with-Docs (ADR-0320 / ADR-0326 / ADR-0361) — Cadrage DRAFT, séance Grill-Me 1:1 à venir.

## 1. Sources & Maquettes SSOT
- file:///C:/Memory%20Loop/src/dashboard/static/index.html (L154-177 : nav onglets ; L2480-2482 : iframe dynamique graphe)
- file:///C:/Memory%20Loop/src/dashboard/routers/database.py (L60-84 : restitution graph.html)
- file:///C:/Memory%20Loop/Projects/mLoop/backlog/stories/MLOOP-150-BE.md (contrats API prérequis)

## 2. Extraits Verbatim Sourcés
**Extrait 1 — Pattern onglets (index.html L154-177)** : « <button onclick="switchTab('overview')" id="tab-btn-overview" ...> 🎯 COCKPIT & GOUVERNANCE </button> ... <button onclick="switchTab('graph')" id="tab-btn-graph" ...> 🕸️ GRAPH & DATABASE </button> » ➔ Fait établi : 7 onglets existent via un mécanisme `switchTab` uniforme ; l'onglet Archify s'ajoute au même pattern sans refonte.

**Extrait 2 — Iframe dynamique existante (index.html L2480-2482)** : « if (iframe && iframe.getAttribute('src') !== targetSrc) { iframe.src = targetSrc; } » ➔ Fait établi : le mécanisme d'iframe rechargée dynamiquement (onglet Graph) est le pattern exact à répliquer pour les diagrammes Archify.

**Extrait 3 — Absence d'onglet Archify** : recherche "archify" dans `index.html` : 0 hit ➔ Fait établi : aucune vue Archify n'existe côté UI ; l'écart est confirmé.

## 3. Contrats Déclaratifs Cibles (UI)
| Composant | Comportement |
|:---|:---|
| Bouton nav `tab-btn-archify` | `switchTab('archify')` — style `font-tech` / `glass-cyber` cohérent |
| Section `#tab-archify` | Liste depuis `GET /api/archify/list` + iframe sur `GET /api/archify/html?file=...` |
| État vide | Message explicite avec commande CLI de compilation Archify |

## 4. Frontière Active & Admission of Limits
- Dépendance stricte aux endpoints de MLOOP-150-BE (`blocked_by: MLOOP-150-BE`) et au verrou SCC MLOOP-145-BE.
- `index.html` n'est pas dans le SCC de MLOOP-145-BE (backend-only) mais la cohérence de sprint impose le blocage cycle.
- Maquette vectorielle : aucune maquette `docs/05-assets/` ne couvre l'UI dashboard (les maquettes concernent les projets clients) — l'onglet suit les conventions internes du Cockpit, pas un contrat visuel client.
- Open questions OQ-151-01 → OQ-151-04 : voir story §5.