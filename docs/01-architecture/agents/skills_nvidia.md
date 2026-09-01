# Intégration du catalogue NVIDIA Skills

## Contexte
Le système d'agents mLoop est nativement compatible avec la spécification **Agent Skills** (`agentskills.io`).
Le catalogue officiel NVIDIA (`github.com/NVIDIA/skills`) offre plus de 140 compétences vérifiées pour l'optimisation (cuOpt), l'IA physique (Omniverse), le RAG Blueprint, etc.

## Directive d'écosystème (mLoop & Opencode)
Au lieu de forcer l'agent à déduire ou réinventer des implémentations de frameworks d'IA ou d'optimisation complexes, vous êtes autorisés à installer des compétences (Skills) spécialisées :

1. Explorer les compétences : `npx skills add nvidia/skills --list`
2. Installer une compétence requise (ex. cuOpt) : `npx skills add nvidia/skills --skill cuopt-numerical-optimization-api-python`

Ces compétences doivent être ajoutées localement au besoin ou dans la configuration globale des agents pour permettre à Opencode ou à l'agent mLoop de générer un code expert instantanément sans épuiser le *Thinking Budget*.

## Compétences locales (Custom Skills)
En plus du catalogue NVIDIA, mLoop supporte des compétences locales pour la productivité métier :

- **office** : Intégration OfficeCLI pour la lecture et l'écriture de fichiers .docx, .xlsx et .pptx. 
  - Usage : `office_read`, `office_write`, `office_render`.
  - Emplacement : `.agents/skills/office/SKILL.md`.

> Note: Ceci n'est pas un ADR logiciel (qui concerne l'architecture du projet client), mais une directive d'enrichissement de l'écosystème d'Agents (Agentic Ecosystem Capability).
