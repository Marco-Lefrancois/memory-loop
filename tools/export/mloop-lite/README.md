# 🚀 mLoop Lite : Le Cycle en 4 Phases Distillées

> **INCEPTION ➔ SPEC / INGEST ➔ PLAN ➔ VALIDATE**  
> **Framework Méthodologique Autonome pour Tous les Quarts de Métier (Nmédia)**

---

## 🧭 Le Pipeline Canonique des 4 Phases

```text
┌────────────────────────┐     ┌────────────────────────┐     ┌────────────────────────┐     ┌────────────────────────┐
│  PHASE 0 : INCEPTION   │ ──> │ PHASE 1 : SPEC/INGEST  │ ──> │   PHASE 2 : PLAN/GRILL │ ──> │  PHASE 3 : VALIDATE    │
│  mloop init --role ... │     │ mloop ingest           │     │ mloop plan --query ... │     │ mloop validate         │
│  reference/ (Brut)     │     │ docs/ (FTS5 SQLite)    │     │ deliverables/          │     │ memory/evidence/ (QA)  │
└────────────────────────┘     └────────────────────────┘     └────────────────────────┘     └────────────────────────┘
```

---

## ⚡ Les 4 Commandes Essentielles au Quotidien

### 1️⃣ Phase 0 : Inception (Amorçage & Dépôt)
Initialise votre espace de travail avec vos gabarits métiers et vos dossiers :
```bash
python mloop.py init --role ba --name "ProjetClient"
# (Rôles disponibles : ba, dev, qa, design, pm, sales)
```
*Action : Déposez vos notes d'entretiens, briefs, PDFs ou liens web dans `reference/`.*

### 2️⃣ Phase 1 : Spec / Ingest (Normalisation & Indexation FTS5)
Distille vos documents bruts et crée l'index SQLite FTS5 instantané :
```bash
python mloop.py ingest
```
*Résultat : Tous vos documents sont indexés par paragraphe avec numéros de lignes pour l'IA.*

### 3️⃣ Phase 2 : Plan & Arbitrage (Fact-Search & Cadrage Grill)
Recherche les faits établis et prépare le dossier de preuves pour l'interview :
```bash
python mloop.py plan --query "rabais VIP et plancher"
```
*Action : Dans votre chat IA (Open WebUI / Cursor / Claude), l'IA applique le Grill with Docs et rédige le livrable dans `deliverables/`.*

### 4️⃣ Phase 3 : Validate / QA (Gatekeeper & Preuves)
Audite la conformité du livrable et valide les EvidencePacks sidecars :
```bash
python mloop.py validate
```
*Résultat : Vérifie que le gabarit est 100% respecté et que les preuves SHA-256 sont intactes.*

---

## 📊 Suivi d'Avancement en Temps Réel
Pour afficher le tableau de bord des 4 phases à tout moment :
```bash
python mloop.py status
```
