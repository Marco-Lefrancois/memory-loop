#!/usr/bin/env python3
"""
Script utilitaire mLoop : Résolution Canonique d'URLs Wiki Azure DevOps (ADR-0327).

Usage:
  python resolve_wiki_url.py --file "reference/SIGPA.wiki/Architecture/doc.md" --org "Projet-SIGPA" --project "SIGPA"
  python resolve_wiki_url.py --path "/Architecture/01 - Modele.md" --org "Projet-SIGPA" --project "SIGPA" --wiki "SIGPA.wiki"
"""

import argparse
import os
import re
import sys
import urllib.parse
from pathlib import Path


def clean_page_path_segment(segment: str) -> str:
    """
    Nettoie et normalise un segment de chemin Wiki Azure DevOps conformément à ADR-0327.
    Gère notamment le piège du %2D (tiret littéral Git vs écrasement en ---).
    """
    # Si le segment se termine par .md, le retirer
    if segment.lower().endswith(".md"):
        segment = segment[:-3]

    # Remplacer les séquences de tirets encadrant %2D par ' - '
    # Dans Git Azure DevOps, "Titre - Sous-titre" est stocké "Titre-%2D-Sous-titre"
    segment = segment.replace("-%2D-", " - ")
    segment = segment.replace("---", " - ")

    # Les tirets cadratins '—'
    segment = segment.replace("—-", "—")

    # Décoder d'éventuels encodages partiels existants
    decoded = urllib.parse.unquote(segment)

    # Ré-encoder selon RFC 3986 en préservant les caractères sûrs
    # Encodage spécifique pour respecter ADR-0327
    encoded = urllib.parse.quote(decoded, safe="/()_-")

    return encoded


def build_canonical_wiki_url(
    org: str,
    project: str,
    wiki_name: str,
    page_path: str,
    page_id: int | None = None,
) -> str:
    """
    Construit l'URL canonique Azure DevOps Wiki.
    Priorité 1 : Permalink avec pageId
    Priorité 2 : pagePath strict sans friendlyName
    """
    base_url = f"https://dev.azure.com/{urllib.parse.quote(org)}/{urllib.parse.quote(project)}/_wiki/wikis/{urllib.parse.quote(wiki_name)}"

    if page_id is not None and page_id > 0:
        # Format 1 : Permalink officiel
        slug = re.sub(r"[^\w\-]", "-", page_path.split("/")[-1].replace(".md", ""))
        slug = re.sub(r"-+", "-", slug).strip("-")
        return f"{base_url}/{page_id}/{slug}"

    # Format 2 : pagePath strict
    normalized_path = page_path.replace("\\", "/").strip()
    if not normalized_path.startswith("/"):
        normalized_path = "/" + normalized_path

    parts = normalized_path.split("/")
    cleaned_parts = [clean_page_path_segment(p) for p in parts]
    encoded_path = "/".join(cleaned_parts)

    return f"{base_url}?pagePath={encoded_path}"


def parse_local_file_path(file_path: str) -> tuple[str, str, str, str]:
    """
    Détecte automatiquement org, project, wiki et pagePath à partir d'un chemin local.
    Exemple attendu : reference/<wikiName>/<dossiers>/<fichier>.md
    """
    path_obj = Path(file_path).resolve()

    # Recherche d'un segment .wiki dans le chemin
    parts = list(path_obj.parts)
    wiki_index = -1
    for idx, part in enumerate(parts):
        if part.endswith(".wiki"):
            wiki_index = idx
            break

    if wiki_index != -1:
        wiki_name = parts[wiki_index]
        sub_parts = parts[wiki_index + 1 :]
        page_path = "/" + "/".join(sub_parts)
        # Déduire le projet du nom de wiki (ex: SIGPA.wiki -> SIGPA)
        project_guess = wiki_name.replace(".wiki", "")
        return "", project_guess, wiki_name, page_path

    # Fallback si pas de .wiki explicite
    return "", "", "Default.wiki", "/" + path_obj.stem


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Générateur d'URL canonique Azure DevOps Wiki (mLoop ADR-0327)"
    )
    parser.add_argument("--file", help="Chemin vers le fichier Markdown local dans reference/")
    parser.add_argument("--path", help="pagePath explicite dans le Wiki")
    parser.add_argument("--org", default=os.getenv("AZURE_DEVOPS_ORG", "Projet-SIGPA"), help="Organisation Azure DevOps")
    parser.add_argument("--project", default=os.getenv("AZURE_DEVOPS_PROJECT", "SIGPA"), help="Nom du projet")
    parser.add_argument("--wiki", default=os.getenv("AZURE_DEVOPS_WIKI", "SIGPA.wiki"), help="Nom du wiki (ex: SIGPA.wiki)")
    parser.add_argument("--page-id", type=int, default=None, help="Identifiant numérique pageId (si connu)")

    args = parser.parse_args()

    org = args.org
    project = args.project
    wiki = args.wiki
    page_path = args.path

    if args.file:
        file_path = Path(args.file)
        if not file_path.exists():
            print(f"[AVERTISSEMENT] Le fichier local '{file_path}' n'a pas été trouvé sur le disque.", file=sys.stderr)
        _, detected_proj, detected_wiki, detected_path = parse_local_file_path(args.file)
        if not page_path:
            page_path = detected_path
        if detected_proj and project == "SIGPA":
            project = detected_proj
        if detected_wiki and wiki == "SIGPA.wiki":
            wiki = detected_wiki

    if not page_path:
        print("Erreur : Spécifiez --file ou --path.", file=sys.stderr)
        return 1

    url = build_canonical_wiki_url(
        org=org,
        project=project,
        wiki_name=wiki,
        page_path=page_path,
        page_id=args.page_id,
    )

    print("\n✅ URL Canonique Azure DevOps Wiki (ADR-0327) :")
    print(url)
    print("\nFormat Markdown à insérer dans la Story :")
    title = page_path.split("/")[-1].replace(".md", "").replace("-%2D-", " - ").replace("-", " ")
    print(f"- [{title}]({url})")

    return 0


if __name__ == "__main__":
    sys.exit(main())
