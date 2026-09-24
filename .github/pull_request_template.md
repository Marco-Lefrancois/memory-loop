# 🚀 Demande de Fusion / Pull Request mLoop

## 📋 Informations Générales
- **Titre** : `<type>(<scope>): <résumé court et impératif>`
- **User Story / Ticket lié** : `MLOOP-XXX` (ou lien vers le ticket Jira / Azure DevOps)
- **Phase du Cycle** : `Phase 5 — SHIP & SYNC` ([ADR-0375](standards/adr-system/0375-project-lifecycle-5-phases-and-analysis-types.md))
- **Autorité Constitutionnelle** : [ADR-0386](standards/adr-system/0386-gouvernance-github-rulesets-pull-requests-et-garde-fous-phase-5-ship.md)

---

## 🔍 Description des Modifications
*Décrivez succinctement les changements apportés, la motivation technique et les arbitrages retenus.*

- [x] Découpage modulaire conforme au plafond ADR-0202 (modules ≤ 300 lignes / 15 Ko).
- [x] Documentation et schémas mis à jour le cas échéant.

---

## 🛡️ Preuves Déterministes Pré-Vol (Porte 5)

Renseignez les résultats d'exécution locale des contrôles obligatoires :

| Contrôle Déterministe | Commande d'Exécution | Résultat Observé | Statut |
| :--- | :--- | :--- | :---: |
| **Vibe-Check Déterministe** | `uv run python src/swarm.py vibe-check --project <P>` | `22 PASS / 1 WARNING / 0 FAIL` | ✅ |
| **Harnais Pytest E2E** | `uv run pytest` | `1386 passed` | ✅ |
| **Linter AST Déterministe** | `uv run python src/swarm.py code-check --all` | `0 violation(s)` | ✅ |

---

## 🔒 Checklist Zéro-Fuite & Sécurité
- [ ] Aucun secret, clé d'API brute ou token n'est présent dans le diff.
- [ ] Les fichiers `.env` et `opencode.json` sont strictement exclus par `.gitignore`.
- [ ] Les templates `.env.example` et `opencode.example.json` ne contiennent que des placeholders anonymisés (`your_litellm_api_key_here`, `litellm_proxy`).
- [ ] Aucun domaine interne, URL de proxy privé ou PII client n'est exposé.

---

## 🔄 Actions Post-Merge Immédiates (Phase 5 Ship & Sync)
Après acceptation et fusion de cette PR :
1. Basculer sur `main` et exécuter `git pull origin main`.
2. Mettre à jour le frontmatter du récit : `status: DONE_SHIPPED`.
3. Lancer la synchronisation du graphe : `uv run python src/swarm.py sync --project <P>`.
