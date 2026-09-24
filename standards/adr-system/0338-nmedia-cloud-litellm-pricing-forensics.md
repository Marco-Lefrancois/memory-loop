# ADR-0338 : Gouvernance Modèles LiteLLM & Pricing Forensics

## Statut
**Accepté (SSOT Normatif)** — 25 août 2026

## Contexte & Problématique
Une analyse superficielle des coûts d'API basée uniquement sur les tarifs de catalogue public hors-cache engendre des décisions contre-productives (ex: sélectionner des modèles légers sous prétexte d'un coût nominal plus bas, alors que leur taux de cache hit est faible et leur qualité de raisonnement inférieure).

Un audit direct du serveur **LiteLLM NMedia Cloud (`https://api-ia.nmedia.ca`)** a été mené le 25 août 2026 sur les 81 modèles déployés, la table des coûts (`/public/litellm_model_cost_map`), les configurations de marge (`cost_margin_config = 0%`), et les journaux de télémétrie de production (`/team/daily/activity`).

---

## 1. Données Certifiées du Serveur NMedia Cloud

### A. Constat Télémétrique sur la Clé de Production (`Boire et Frère`)
- **Requêtes réelles auditées** : 286 requêtes API.
- **Volume total traité** : **31 495 021 tokens** (~31.5 M tokens).
- **Prompt Caching Read** : **27 530 089 tokens (87.84% de cache hits)**.
- **Facture réelle enregistrée par le serveur** : **0.0192 $ USD** (au lieu de ~94.00 $ au tarif plein).

---

## 2. Grille Officielle des Coûts NMedia Cloud ($/1M Tokens)

| Modèle Déployé | Famille | Input Standard | Output | **Cache Read (-90%)** | Contexte Max | Usage Recommandé |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **`claude-sonnet-5`** | Anthropic | **2.000 $** | 10.000 $ | **0.200 $** | **1 000 000** | 👑 **Daily Driver / Orchestration / Stories / Code** |
| **`claude-sonnet-4-6`** | Anthropic | **3.000 $** | 15.000 $ | **0.300 $** | **1 000 000** | 🤖 Daily Driver alternatif |
| **`claude-opus-4-8`** | Anthropic | **5.000 $** | 25.000 $ | **0.500 $** | **1 000 000** | 🧠 Arbitrages critiques & ADRs Type 1 |
| **`gpt-5.6-luna`** | OpenAI | **0.200 $** | 1.200 $ | **0.020 $** | **1 050 000** | ⚡ **Small Model / Tâches de masse & Linters** |
| **`gpt-5.6-terra`** | OpenAI | **2.000 $** | 12.000 $ | **0.200 $** | **1 050 000** | 🤖 Raisonnement généraliste |
| **`gpt-5.6-terra-thinking`** | OpenAI | **2.000 $** | 12.000 $ | **0.200 $** | **1 050 000** | 🔍 **Agent Sentinel (Revue Rubber-Duck)** |
| **`gemini-3.5-flash-lite`** | Google | **0.300 $** | 2.500 $ | **0.030 $** | **1 048 576** | ⚡ Ingestion documentaire brute |
| **`gemini-3.1-flash-lite`** | Google | **0.250 $** | 1.500 $ | **0.025 $** | **1 048 576** | ⚡ Ingestion rapide |

---

## 3. Décision : Le "Trio d'Or" pour la Configuration `opencode.json`

Pour maximiser la qualité sans compromis tout en conservant un coût journalier dérisoire (< 2.50 $ / jour) :

```json
{
  "model": "nmedia_cloud/claude-sonnet-5",
  "small_model": "nmedia_cloud/gpt-5.6-luna",
  "agent": {
    "orchestrator": {
      "model": "nmedia_cloud/claude-sonnet-5"
    },
    "plan": {
      "model": "nmedia_cloud/claude-sonnet-5"
    },
    "build": {
      "model": "nmedia_cloud/claude-sonnet-5"
    },
    "sentinel": {
      "model": "nmedia_cloud/gpt-5.6-terra-thinking"
    },
    "worker": {
      "model": "nmedia_cloud/claude-sonnet-5"
    }
  }
}
```

### Rationale du Trio :
1. **`claude-sonnet-5` (Moteur Principal)** : Configuré à seulement **2.00 $ / 1M** (moins cher que Sonnet 4.6), il apporte 1M de contexte et une conformité Gherkin/INVEST absolue. Grâce au Prompt Caching (0.20 $/M), une session de 20 tours coûte **0.52 $**.
2. **`gpt-5.6-luna` (Modèle Léger `small_model`)** : À **0.20 $ / 1M input** et **0.02 $ / 1M cache**, il offre 1 050 000 tokens de contexte pour un coût 10x inférieur aux modèles standards.
3. **`gpt-5.6-terra-thinking` (Agent Sentinel & Audit)** : À **2.00 $ / 1M**, il apporte la chaîne de pensée (*thinking*) pour traquer impitoyablement les failles fonctionnelles lors des revues Rubber-Duck.

---

## 4. Conséquences & Règles d'Hygiène Opérationnelle

1. **Stabilité du Préfixe de Prompt** : Les fichiers `AGENTS.md`, `GEMINI.md` et les blueprints doivent impérativement être injectés en tête de contexte pour garantir un taux de cache hit > 85%.
2. **Sessions Continues** : Le cache Anthropic a une durée de rétention de 5 minutes renouvelée à chaque tour. Privilégier les blocs de travail continus.
3. **Zero-Model-Jumping** : Ne pas changer de modèle arbitrairement au milieu d'une session de cadrage afin de ne pas invalider le cache GPU distant.

---

## 5. Amendement — ADR-0388 (24 septembre 2026)

Le Trio d'Or ci-dessus reste la SSOT normative pour les agents primaires **orchestrator / plan / sentinel** et pour les `task-type` de gouvernance qualité (`deepening`, `validation`, `deepsearch`, `compaction`) de `TASK_MODEL_MAP`.

La mission `build` (développement mLoop et `worker-spawn` sans `--task-type`) a été déportée vers le **free tier natif OpenCode** (`opencode/mimo-v2.6-flash-free`, hors proxy LiteLLM) afin de réduire le coût de développement quotidien, en cohérence avec le précédent `DEFAULT_CLINE_MODEL` déjà en vigueur pour le runtime Cline. Voir [ADR-0388](0388-worker-build-default-free-model.md) pour le détail complet de la décision, du périmètre et des invariants préservés.
