# -*- coding: utf-8 -*-
"""
tools_bridge.py - Bridge d'Outils Natifs TypeScript pour OpenCode (MLOOP-251-BE).

Génère et déploie les outils TypeScript sous .opencode/tools/ (fact_search.ts, vibe_check.ts)
pour exposer le Système 1 mLoop directement au raisonnement du modèle en lecture seule.
Conforme ADR-0202 (<=300L), ADR-0369 et ADR-0377.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger("mloop.bridges.opencode.tools_bridge")


class OpenCodeToolsBridge:
    """Générateur et gestionnaire de déploiement des outils .opencode/tools/."""

    def __init__(
        self,
        workspace_root: Optional[Path] = None,
        target_dir: Optional[Path] = None,
    ) -> None:
        self.root = Path(workspace_root) if workspace_root else Path.cwd()
        self.target_dir = Path(target_dir) if target_dir else self.root / ".opencode" / "tools"

    def ensure_target_dir(self) -> Path:
        """Assure la présence du dossier .opencode/tools/."""
        self.target_dir.mkdir(parents=True, exist_ok=True)
        return self.target_dir

    def generate_fact_search_ts(self) -> str:
        """Génère le code TypeScript de l'outil fact_search.ts (FTS5 Read-Only)."""
        return """import { spawn } from "child_process";
import { tool } from "@opencode/tool";

export interface FactSearchParams {
  query: string;
  limit?: number;
}

export default tool({
  name: "fact_search",
  description: "Recherche lexicale déterministe FTS5 dans la mémoire et les invariants mLoop (Lecture Seule).",
  parameters: {
    type: "object",
    properties: {
      query: { type: "string", description: "Terme ou expression à rechercher dans l'index FTS5" },
      limit: { type: "number", description: "Nombre maximum de correspondances (défaut: 5)" }
    },
    required: ["query"]
  },
  async execute({ query, limit = 5 }: FactSearchParams): Promise<string> {
    return new Promise((resolve) => {
      const proc = spawn("python", ["src/swarm.py", "fact-search", query, "--limit", String(limit), "--json"], {
        timeout: 5000,
        shell: true
      });
      let stdout = "";
      let stderr = "";

      proc.stdout.on("data", (data) => { stdout += data.toString(); });
      proc.stderr.on("data", (data) => { stderr += data.toString(); });

      proc.on("close", (code) => {
        if (code === 0 && stdout.trim()) {
          resolve(stdout.trim());
        } else {
          resolve(JSON.stringify({ error: stderr.trim() || `Code de sortie non nul: ${code}`, query }));
        }
      });

      proc.on("error", (err) => {
        resolve(JSON.stringify({ error: `Erreur d'exécution: ${err.message}` }));
      });
    });
  }
});
"""

    def generate_vibe_check_ts(self) -> str:
        """Génère le code TypeScript de l'outil vibe_check.ts (Pré-vol Read-Only)."""
        return """import { spawn } from "child_process";
import { tool } from "@opencode/tool";

export interface VibeCheckParams {
  fast?: boolean;
}

export default tool({
  name: "vibe_check",
  description: "Exécute le contrôle pré-vol Vibe-Check mLoop pour valider les règles et frontières du projet.",
  parameters: {
    type: "object",
    properties: {
      fast: { type: "boolean", description: "Mode rapide court-circuitant les calculs lourds (défaut: true)" }
    }
  },
  async execute({ fast = true }: VibeCheckParams = {}): Promise<string> {
    return new Promise((resolve) => {
      const args = ["src/swarm.py", "vibe-check", "--project", "mLoop"];
      if (fast) args.push("--fast");

      const proc = spawn("python", args, { timeout: 10000, shell: true });
      let stdout = "";
      let stderr = "";

      proc.stdout.on("data", (data) => { stdout += data.toString(); });
      proc.stderr.on("data", (data) => { stderr += data.toString(); });

      proc.on("close", (code) => {
        resolve(JSON.stringify({
          exit_code: code,
          status: code === 0 ? "PASS" : "FAIL_OR_WARNING",
          output: stdout.trim() || stderr.trim()
        }));
      });

      proc.on("error", (err) => {
        resolve(JSON.stringify({ error: `Échec Vibe-Check: ${err.message}`, exit_code: -1 }));
      });
    });
  }
});
"""

    def deploy_tools(self) -> Dict[str, int]:
        """Déploie tous les outils TypeScript sous .opencode/tools/ de façon idempotente."""
        self.ensure_target_dir()
        stats = {"deployed": 0, "skipped": 0}

        tools_to_write = {
            "fact_search.ts": self.generate_fact_search_ts(),
            "vibe_check.ts": self.generate_vibe_check_ts(),
        }

        for filename, content in tools_to_write.items():
            target_file = self.target_dir / filename
            if target_file.exists():
                existing = target_file.read_text(encoding="utf-8")
                if existing == content:
                    stats["skipped"] += 1
                    continue

            target_file.write_text(content, encoding="utf-8")
            stats["deployed"] += 1
            logger.info(f"[OpenCodeTools] Outil déployé : {filename}")

        return stats

    def check_tools_installed(self) -> bool:
        """Vérifie si les outils natifs indispensables sont installés."""
        fact_search_file = self.target_dir / "fact_search.ts"
        vibe_check_file = self.target_dir / "vibe_check.ts"
        return fact_search_file.exists() and vibe_check_file.exists()
