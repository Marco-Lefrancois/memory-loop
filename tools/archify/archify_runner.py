"""
Archify Runner — Outil de génération et validation de diagrammes d'architecture interactifs (mLoop Tool).

Intègre Archify CLI (tt-a1i/archify) pour transformer des spécifications JSON IR
en diagrammes d'architecture interactifs vectoriels (HTML standalone, zoomable, filtres de vues, animations trace).
"""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

def find_archify_bin() -> Path:
    """Localise le binaire archify.mjs installé."""
    home = Path.home()
    candidates = [
        home / ".agents" / "skills" / "archify" / "bin" / "archify.mjs",
        Path("C:/Users/mlefrancois/.agents/skills/archify/bin/archify.mjs"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate

    raise FileNotFoundError(
        "Archify CLI n'est pas trouvé sous ~/.agents/skills/archify/bin/archify.mjs. "
        "Installez-le avec : npx -y skills add tt-a1i/archify -g"
    )

def run_archify_command(cmd: str, diagram_type: str, input_path: str, output_path: str = None, quality: str = "showcase") -> int:
    """Exécute une commande Archify CLI via Node.js."""
    archify_bin = find_archify_bin()
    args = ["node", str(archify_bin), cmd, diagram_type, input_path]

    if output_path and cmd in ["render", "deliver"]:
        args.append(output_path)

    if quality:
        args.extend(["--quality", quality])

    args.append("--json")

    res = subprocess.run(args, capture_output=True, text=True, encoding="utf-8")
    if res.stdout:
        try:
            parsed = json.loads(res.stdout)
            print(json.dumps(parsed, indent=2, ensure_ascii=False))
        except Exception:
            print(res.stdout)
    if res.stderr:
        print(res.stderr, file=sys.stderr)

    return res.returncode

def main():
    parser = argparse.ArgumentParser(description="Archify CLI Runner pour Memory Loop")
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    # validate
    p_val = subparsers.add_parser("validate", help="Valider un diagramme JSON IR (9 contrôles géométriques)")
    p_val.add_argument("input", type=str, help="Chemin du fichier JSON de spécification")
    p_val.add_argument("--type", type=str, default="architecture", choices=["architecture", "flow", "sequence", "mindmap"], help="Type de diagramme")
    p_val.add_argument("--quality", type=str, default="showcase", choices=["draft", "standard", "showcase"], help="Profil de qualité")

    # deliver
    p_del = subparsers.add_parser("deliver", help="Compiler un diagramme JSON IR en HTML standalone")
    p_del.add_argument("input", type=str, help="Chemin du fichier JSON de spécification")
    p_del.add_argument("output", type=str, help="Chemin du fichier HTML de sortie")
    p_del.add_argument("--type", type=str, default="architecture", choices=["architecture", "flow", "sequence", "mindmap"], help="Type de diagramme")
    p_del.add_argument("--quality", type=str, default="showcase", choices=["draft", "standard", "showcase"], help="Profil de qualité")
    p_del.add_argument("--open", action="store_true", help="Ouvrir directement dans le navigateur par défaut après génération")

    args = parser.parse_args()

    if args.subcommand == "validate":
        code = run_archify_command("validate", args.type, args.input, quality=args.quality)
        sys.exit(code)
    elif args.subcommand == "deliver":
        code = run_archify_command("deliver", args.type, args.input, output_path=args.output, quality=args.quality)
        if code == 0 and args.output:
            out_file = Path(args.output)
            if out_file.exists():
                html_txt = out_file.read_text(encoding="utf-8")
                target_script = "theme = window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark';"
                if target_script in html_txt:
                    html_txt = html_txt.replace(target_script, "theme = 'dark';")
                    out_file.write_text(html_txt, encoding="utf-8")
            if args.open and sys.platform == "win32":
                os.startfile(out_file.resolve())
        sys.exit(code)

if __name__ == "__main__":
    main()
