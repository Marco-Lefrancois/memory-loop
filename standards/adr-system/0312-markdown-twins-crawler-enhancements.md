# ADR-0312 : Ingestion Déterministe via Markdown Twins et Surfaces de Découverte Web

> **Statut :** Accepté  
> **Date :** 2026-08-06  
> **Contexte :** R&D Ingestion Web & Optimisation mLoop Crawler Agent  

---

## 1. Contexte & Problématique

Jusqu'à présent, le crawler de mLoop (`src/pipelines/crawler.py`) téléchargeait les pages HTML brutes puis utilisait `BeautifulSoup` et `markdownify` pour convertir le DOM en Markdown. Bien que fonctionnelle, cette approche présente plusieurs limites :
1. **Bruit & Scraps DOM** : Risque de conserver du texte parasite (navigation, cookies, footers).
2. **Consommation de ressources** : Traitement inutile d'arbres HTML volumineux.
3. **Perte de structure** : La conversion HTML->Markdown altère parfois le formatage original des blocs de code ou des tableaux.

L'étude de plateformes modernes axées sur les agents IA (telles qu'AI Hero) montre l'émergence d'un standard de découverte web :
- **Markdown Twins** : Mise à disposition de la version Markdown brute à la même URL avec l'extension `.md` (ex: `https://domain.com/slug.md`) ou via la négociation de contenu HTTP `Accept: text/markdown`.
- **Surfaces de Découverte** : Utilisation d'index légers comme `/sitemap.md`, `/llms.txt`, et `/api`.

---

## 2. Décisions d'Architecture

1. **Négociation de Contenu HTTP & En-tête `Accept`** :
   Le crawler mLoop enverra systématiquement `Accept: text/markdown, text/x-markdown, text/plain;q=0.9, text/html;q=0.8` lors de chaque requête HTTP.

2. **Résolution Automatique des URLs `.md` Twins** :
   Pour toute URL HTML cible qui ne se termine pas par `.md`, si le premier appel HTTP retourne du HTML (et non du Markdown brut), le crawler effectue automatiquement une vérification de fallback sur `URL.md`. Si cette variante `.md` existe et renvoie du Markdown brut avec un code HTTP 200, le crawler privilégie ce contenu direct.

3. **Prise en Charge des Surfaces de Découverte (`sitemap.md`, `llms.txt`)** :
   Les fichiers de découverte au format Markdown (`sitemap.md`, `llms.txt`) sont désormais reconnus comme des index de référence et conservés sans altération.

---

## 3. Impact sur les 6 Piliers mLoop

- **Pilier 1 (CLI & Swarm)** : Vitesse de crawl décuplée et réduction du bruit dans les fichiers d'ingestion `memory/crawler/cache/`.
- **Pilier 2 (Bridges & MCP)** : Meilleure extraction des spécifications et des documentations d'APIs externes.
- **Pilier 3 (Skills)** : Accès direct aux sources canoniques des skills et des directives agents.
- **Pilier 4 (Directives & Guardrails)** : Moins d'ambiguïté dans le contexte ingéré.
- **Pilier 5 (Dashboard & Web UI)** : Rendu plus propre des documentations ingérées.
- **Pilier 6 (Graphify & RAG)** : Meilleure qualité du graphe de connaissances généré à partir de contenus Markdown purs.

---

## 4. Statut & Suivi

- Implémentation physique dans `src/pipelines/crawler.py`.
- Validation par le pipeline d'auto-calibration (`python src/swarm.py calibrate --project mLoop`).
