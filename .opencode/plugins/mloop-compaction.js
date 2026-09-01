export const MLoopCompactionPlugin = async ({ project }) => {
  return {
    "experimental.session.compacting": async (input, output) => {
      output.context.push(`
## Contexte Mémoire mLoop (Anti-Amnésie)
- Projet actif : ${project?.name || "mLoop"}
- Respecter strictly la séquence d'amorçage mLoop et les règles SSOT définies dans AGENTS.md.
- Conserver les critères INVEST, les statuts des Stories et l'intégrité des EvidencePacks.
`);
    }
  };
};
