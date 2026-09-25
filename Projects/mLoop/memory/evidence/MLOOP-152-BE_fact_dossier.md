# Dossier de Preuves Documentaires — MLOOP-152-BE
> Grill-with-Docs (ADR-0320 / ADR-0326 / ADR-0361) — Cadrage DRAFT, séance Grill-Me 1:1 à venir.

## 1. Sources & Maquettes SSOT
- file:///C:/Memory%20Loop/tools/drawdb/runner.py (L16-43 : page fallback iframe externe)
- file:///C:/Memory%20Loop/src/bridges/drawdb_bridge.py (L13-70 : parse_dbml opérationnel)
- file:///C:/Memory%20Loop/src/commands/handlers/tooling.py (L169-181 : handle_drawdb / serve_drawdb)
- file:///C:/Memory%20Loop/src/dashboard/static/index.html (L174-176 : onglet Graph & Database)
- AGENTS.md § « Confinement Local des Diagrammes (Zéro Exfiltration) »

## 2. Extraits Verbatim Sourcés
**Extrait 1 — Non-conformité actuelle (runner.py L40)** : « <iframe src="https://www.drawdb.app/editor" title="drawDB Local Editor"></iframe> » ➔ Fait établi : le runner drawdb exfiltre la consultation vers un serveur externe en dépit du confinement local exigé (AGENTS.md : « Interdiction formelle d'exfiltrer du code ou des données vers des serveurs distants »).

**Extrait 2 — Parseur DBML existant (drawdb_bridge.py L13-70)** : « def parse_dbml(content: str) -> List[Dict[str, Any]] ... tables.append(current_table) » ➔ Fait établi : un parseur DBML → tables/champs/PK/FK est déjà opérationnel dans `src/bridges/` ; le visualiseur local peut s'appuyer dessus sans réécriture.

**Extrait 3 — Serveur drawdb souverain (runner.py L45-60)** : « def serve_drawdb(port: int = DEFAULT_PORT, auto_open: bool = True) ... with socketserver.ThreadingTCPServer(("", port), handler) as httpd » ➔ Fait établi : l'infrastructure de service HTTP local existe déjà (défaut port 8080 — conflit avec le dashboard, d'où la proposition 8081).

**Extrait 4 — Onglet Graph & Database (index.html L174-176)** : « <button onclick="switchTab('graph')" id="tab-btn-graph" ...> 🕸️ GRAPH & DATABASE </button> » ➔ Fait établi : point d'ancrage UI naturel pour le lien « Ouvrir DrawDB ».

## 3. Contrats Déclaratifs Cibles (REST/CTA)
| Méthode | Route / CTA | Finalité |
|:---|:---|:---|
| `GET` | `http://localhost:<port>/` (runner drawdb) | Page visualiseur 100% locale, zéro CDN |
| `POST` (interne) | conversion DBML → JSON via `drawdb_bridge.parse_dbml` | Alimentation du rendu ERD local |
| CTA | Bouton « 🗄️ Ouvrir DrawDB » (onglet Graph & Database) | Ouverture du visualiseur sur le port configuré |

## 4. Frontière Active & Admission of Limits
- Aucun build drawDB vendored n'existe dans le dépôt (`tools/drawdb/static/` ne contient que le `index.html` généré) ➔ l'arbitrage « build npm vendored vs visualiseur maison » est l'OQ-152-01 bloquante du Grill.
- Le pipeline CLI drawdb (export/import/sync, `src/pipelines/drawdb_pipeline.py`) est hors périmètre : cette story couvre uniquement le visualiseur local et le lien Cockpit.
- Conflit de port documenté : dashboard 8080 vs drawdb 8080 (défauts actuels identiques) ➔ convention 8081 à valider en Grill.
- Open questions OQ-152-01 → OQ-152-05 : voir story §5.