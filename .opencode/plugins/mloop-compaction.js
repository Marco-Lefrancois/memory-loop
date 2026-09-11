import fs from "node:fs";
import path from "node:path";
import { execSync } from "node:child_process";

/**
 * Plugin OpenCode officiel mLoop pour l'interception de pré-compaction (ADR-0364).
 * Intercepte l'événement experimental.session.compacting pour injecter les invariants
 * Système 1 et la micro-boussole LOD-0 (<= 400 tokens) sauvegardés sur disque.
 */
export const MLoopCompactionPlugin = async ({ project }) => {
  return {
    "experimental.session.compacting": async (input, output) => {
      const projectName = project?.name || "Memory Loop";
      const possiblePaths = [
        path.join(process.cwd(), "memory", "compaction", "latest_checkpoint.json"),
        path.join(process.cwd(), "Projects", projectName, "memory", "compaction", "latest_checkpoint.json"),
      ];

      let resumeText = null;

      // 1. Déclenchement déterministe du hook pre_compact
      try {
        execSync(`python src/swarm.py hook --event pre_compact --project "${projectName}"`, {
          timeout: 5000,
          stdio: "ignore",
        });
      } catch (e) {
        // Fallback silencieux vers lecture directe si timeout ou erreur CLI
      }

      // 2. Lecture du dernier checkpoint persistant
      for (const p of possiblePaths) {
        if (fs.existsSync(p)) {
          try {
            const raw = fs.readFileSync(p, "utf-8");
            const data = JSON.parse(raw);
            if (data.resume_instructions) {
              resumeText = data.resume_instructions;
              break;
            }
          } catch (err) {
            // continuer
          }
        }
      }

      // 3. Injection dans la mémoire post-compaction
      if (resumeText) {
        output.context.push(resumeText);
      } else {
        output.context.push(`
## 🛡️ Contexte Mémoire mLoop (Anti-Amnésie - Fallback)
- Projet actif : ${projectName}
- Respecter strictly la séquence d'amorçage mLoop et les règles SSOT définies dans AGENTS.md.
- Conserver les critères INVEST, les 4 Piliers Gherkin et l'intégrité des EvidencePacks.
`);
      }
    },
  };
};
