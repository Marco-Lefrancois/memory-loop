# ADR-0344 : Architecture Zero-Blindspot pour Moteurs d'Analyse IA (Pattern AI Resume Analyzer)

- **Statut** : Accepté
- **Date** : 2026-08-30
- **Auteurs** : Équipe mLoop Swarm & AI Architecture
- **Périmètre** : Ingestion Multimodale, Abstraction de Fournisseurs (Puter/LiteLLM), Validation Zod & Déterminisme ATS

---

## 1. Contexte

L'analyse approfondie du dépôt `adrianhajdin/ai-resume-analyzer` a révélé un potentiel applicatif majeur (architecture Zero-Backend sur navigateur, intégration de Puter.js, rendu PDF.js via Web Worker), mais a également mis en lumière **6 angles morts critiques** :
1. Dépendance exclusive (SPOF) à un écosystème fermé (Puter.js).
2. Perte d'information sur les documents multipages (conversion limitée à la page 1).
3. Fragilité des sorties JSON non typées face aux dérives LLM.
4. Absence de déterminisme et risque d'hallucination sur le scoring ATS.
5. Absence de protection de la vie privée (fuite de PII non masquées).
6. Conflits d'hydratation SSR (React Router v7 / objet global `window.puter`).

---

## 2. Décisions d'Architecture (Les 6 Piliers 0-Blindspot)

### 2.1 Pilote Multi-Provider Abstraction (`IAuthProvider`, `IStorageProvider`, `IAIProvider`)
- Découplage strict de la couche d'infrastructure via des adaptateurs interchangeables.
- Support natif de :
  - **PuterProvider** (Serverless client-side par défaut).
  - **LiteLLMProvider / DirectProxy** (OpenAI, Gemini, Anthropic avec sécurité de clé).
  - **LocalProvider** (Ollama / WebLLM + IndexedDB pour fonctionnement 100% souverain/hors-ligne).

### 2.2 Pipeline d'Ingestion Hybride Texte & Multi-Pages Canvas
- Extraction simultanée du **texte brut découpé** via `pdfjs-dist` et des **vignettes vectorielles canvas** de chaque page.
- Assemblage vertical optimisé pour la vision multimodale avec compression adaptative WebP/JPEG.

### 2.3 Contrats de Données Zod & Moteur de Réparation JSON
- Typage strict du schéma de retour de l'IA (`analysisSchema.ts`).
- Filet de résilience à 3 niveaux : Structured Outputs $\rightarrow$ Parseur `jsonRepair` $\rightarrow$ Ré-inférence ciblée.

### 2.4 Grounding Evidence & Scoring Déterministe
- Interdiction pour le LLM d'émettre une pénalité de score sans **citer textuellement le passage du CV incriminé**.
- Score ATS hybride : base déterministe (mots-clés / heuristique) + audit qualitatif des 4 axes (Structure, Clarté, Compétences, Impact).

### 2.5 Module de Confidentialité Client-Side (PII Redaction)
- Masquage automatique des identifiants directs (Email, Téléphone, Adresse, Nom) avant toute émission réseau vers des modèles tiers.

### 2.6 Isolation SSR Déterministe
- Composant barrière `<ClientOnly>` neutralisant les accès non sécurisés à `window.puter` lors du pré-rendu serveur React Router v7.

---

## 3. Conséquences

### Positives :
- **Résilience 100% garantie** face aux pannes ou évolutions de tiers.
- **Zéro hallucination** et traçabilité intégrale des recommandations pour les candidats.
- **Conformité RGPD / Privacy** par conception grâce au masquage PII.
- **Compatibilité multi-plateformes** (navigateur, desktop PWA, environnement d'entreprise).

### Statut d'Alignement :
- Consigné sous `standards/adr-system/0344-ai-resume-analyzer-zero-blindspot-architecture.md` et documenté sous `Projects/Ai_Resume_Analyzer/docs/01-architecture/`.
