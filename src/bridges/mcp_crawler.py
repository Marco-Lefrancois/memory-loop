import os
import sys
import subprocess
from pathlib import Path


def resolve_crawler_cli_path() -> Path:
    """Résout dynamiquement le chemin d'accès au binaire mloop-crawler."""
    env_path = os.environ.get("MLOOP_CRAWLER_PATH")
    if env_path:
        p = Path(env_path)
        if p.exists():
            return p

    candidates = [
        Path("c:/mloop-crawler/packages/cli/dist/index.js"),
        Path.home() / "mloop-crawler" / "packages" / "cli" / "dist" / "index.js",
        Path(__file__).resolve().parent.parent.parent
        / "mloop-crawler"
        / "packages"
        / "cli"
        / "dist"
        / "index.js",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def main():
    cli_path = resolve_crawler_cli_path()

    if not cli_path.exists():
        sys.stderr.write(
            f"[MCP CRAWLER] ERREUR FATALE: L'outil mloop-crawler n'est pas compilé ou introuvable à {cli_path}\n"
        )
        sys.stderr.write(
            "[MCP CRAWLER] Exécutez 'npm install && npm run build' dans le dossier mloop-crawler ou définissez MLOOP_CRAWLER_PATH\n"
        )
        sys.stderr.flush()
        sys.exit(1)

    cmd = ["node", str(cli_path), "mcp"]

    sys.stderr.write(f"[MCP CRAWLER] Délégation du protocole MCP vers {cli_path}...\n")
    sys.stderr.flush()

    process = subprocess.Popen(  # noqa: RULE-AST-03 (processus MCP stdio — durée de vie = session client)
        cmd, stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr
    )

    process.wait(timeout=86400)  # borné à 24h max (session MCP stdio)
    sys.exit(process.returncode)


if __name__ == "__main__":
    main()
