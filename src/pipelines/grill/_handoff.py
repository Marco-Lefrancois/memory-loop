"""
Handoff Pattern & Prototype Staging - mLoop Grill Package (ADR-0389 / MLOOP-291-FE).
Génération zéro-build de prototypes jetables HTML5/Tailwind et SVG sous scratch/prototypes/.
"""
from __future__ import annotations

import shutil
from pathlib import Path
from typing import Optional

from src.cli import ZeroFluffConsole
from src.utils.logger import get_logger

logger = get_logger("grill.handoff")

_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Prototype {story_id} : {subject}</title>
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-50 text-slate-900 min-h-screen p-6">
  <div class="max-w-4xl mx-auto bg-white rounded-xl shadow-md border border-slate-200 overflow-hidden">
    <header class="bg-slate-900 text-white px-6 py-4 flex justify-between items-center">
      <div>
        <span class="text-xs uppercase tracking-wider text-indigo-400 font-semibold">mLoop Handoff Prototype</span>
        <h1 class="text-lg font-bold">{story_id} — {subject}</h1>
      </div>
      <span class="text-xs bg-amber-500/20 text-amber-300 border border-amber-500/40 px-3 py-1 rounded-full font-mono">
        Zéro-Build Sandbox
      </span>
    </header>
    <main class="p-6">
      {content}
    </main>
    <footer class="bg-slate-100 border-t border-slate-200 px-6 py-3 text-xs text-slate-500 flex justify-between">
      <span>Généré automatiquement par mLoop Grill Engine (ADR-0389)</span>
      <span>Ouvrable directement via protocole local file:///</span>
    </footer>
  </div>
</body>
</html>
"""

_SVG_TEMPLATE = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 500" width="100%" height="100%">
  <defs>
    <style>
      .bg {{ fill: #f8fafc; }}
      .card {{ fill: #ffffff; stroke: #cbd5e1; stroke-width: 1.5; rx: 8; }}
      .header {{ fill: #0f172a; font-family: sans-serif; font-size: 18px; font-weight: bold; }}
      .sub {{ fill: #64748b; font-family: sans-serif; font-size: 12px; }}
      .badge {{ fill: #fef3c7; stroke: #f59e0b; stroke-width: 1; rx: 4; }}
      .badge-text {{ fill: #92400e; font-family: monospace; font-size: 11px; }}
    </style>
  </defs>
  <rect width="100%" height="100%" class="bg" />
  <rect x="40" y="30" width="720" height="440" class="card" />
  <text x="60" y="70" class="header">{story_id} — {subject}</text>
  <text x="60" y="95" class="sub">mLoop Handoff SVG Vector Mockup (ADR-0389)</text>
  <rect x="620" y="50" width="120" height="24" class="badge" />
  <text x="630" y="66" class="badge-text">Zéro-Build SVG</text>
  <g transform="translate(60, 120)">
    {content}
  </g>
</svg>
"""


def stage_prototype(
    project_path: Path,
    story_id: str,
    subject: str,
    content: str = "",
    kind: str = "html",
) -> Path:
    """
    Crée un prototype autonome sous scratch/prototypes/ et affiche l'URL locale file:///.
    """
    clean_subj = subject.strip().replace(" ", "_").replace("/", "_").lower()
    proto_dir = project_path / "scratch" / "prototypes"
    proto_dir.mkdir(parents=True, exist_ok=True)

    ext = "svg" if kind.lower() == "svg" else "html"
    proto_path = proto_dir / f"proto_{story_id}_{clean_subj}.{ext}"

    if ext == "svg":
        inner_content = content or '<text x="20" y="50" font-family="sans-serif" font-size="14" fill="#334155">Composant vectoriel en cours d arbitrage...</text>'
        rendered = _SVG_TEMPLATE.format(story_id=story_id, subject=subject, content=inner_content)
    else:
        inner_content = content or '<div class="p-8 text-center text-slate-500 border-2 border-dashed border-slate-300 rounded-lg"><p class="text-sm font-medium">Composant IHM en cours d arbitrage...</p></div>'
        rendered = _HTML_TEMPLATE.format(story_id=story_id, subject=subject, content=inner_content)

    proto_path.write_text(rendered, encoding="utf-8")
    uri = f"file:///{proto_path.resolve().as_posix()}"
    ZeroFluffConsole.info(f"🎨 Prototype Handoff généré avec succès ({ext.upper()}) :")
    ZeroFluffConsole.info(f"   👉 {uri}")
    logger.info("Prototype Handoff créé : %s", proto_path)
    return proto_path


def promote_prototype(
    prototype_path: Path,
    target_dir: Optional[Path] = None,
    final_name: Optional[str] = None,
) -> Path:
    """
    Promeut un prototype validé depuis scratch/ vers docs/05-assets/mockups/.
    """
    if not prototype_path.exists():
        raise FileNotFoundError(f"Prototype source introuvable : {prototype_path}")

    if target_dir is None:
        # Heuristique : remonter vers la racine du projet
        # scratch/prototypes/file.html -> target: docs/05-assets/mockups/
        proj_root = prototype_path.parents[2]
        dest_dir = proj_root / "docs" / "05-assets" / "mockups"
    else:
        dest_dir = target_dir

    dest_dir.mkdir(parents=True, exist_ok=True)
    out_name = final_name or prototype_path.name
    dest_path = dest_dir / out_name

    shutil.copyfile(prototype_path, dest_path)
    ZeroFluffConsole.success(f"🏆 Prototype promu en actif permanent : {dest_path}")
    logger.info("Prototype promu vers %s", dest_path)
    return dest_path
