# Product Context — Memory Loop (mLoop)

## 1. Why this project exists
Les agents de code autonomes souffrent fréquemment d'amnésie de contexte, de sauts de phase intempestifs (commencer à coder avant le cadrage) et de destructions silencieuses de code existant. mLoop élimine ces dérives par des garde-fous déterministes.

## 2. User Workflows
1. Cadrage & Ingestion : Ingestion des documents et code source sans modification.
2. Analyse & Grill-Me : Entrevue contradictoire 1:1 pour éliminer les zones d'ombre.
3. Build Délégué : Délégation de l'implémentation physique à des workers isolés (Herdr).
4. Certification QA : Fact-Check NLI, Vibe-Check pré-vol et suites de tests pytest.
5. Livraison Fail-Closed : Publication Git et Jira uniquement si tous les invariants sont respectés.
