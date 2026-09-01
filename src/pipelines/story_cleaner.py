import re
from pathlib import Path
from src.cli import ZeroFluffConsole

def clean_story_markdown(content: str) -> tuple[str, bool]:
    """
    Nettoie le contenu d'une User Story Markdown en supprimant toutes les sections
    de traçabilité, notes d'audit IA et blocs résiduels (ADR-0319 / ADR-0326 / ADR-0333).
    
    Retourne (nouveau_contenu, modifié).
    """
    original = content

    # 1. Supprimer toute variante de bloc de traçabilité / notes IA (H2) jusqu'à la fin
    # Couvre : '## 📑 Notes de Traçabilité...', '## Notes de Traçabilité...', dédoublonnements corrompus
    content = re.sub(
        r"(?ms)(?:\r?\n+---\s*)?\r?\n+##\s+(?:📑\s*)?Notes?\s+de\s+Traçabilité.*$",
        "",
        content
    )

    # 2. Supprimer tout bloc citation "Suite Mémoire & Audit (IA)"
    content = re.sub(
        r"(?ms)(?:\r?\n+---\s*)?\r?\n+>\s*🛡️\s*\*\*Suite\s+Mémoire\s+&\s+Audit\s+\(IA\)\*\*.*$",
        "",
        content
    )

    # 3. Supprimer tout séparateur '---' orphelin en fin de fichier
    content = re.sub(r"(?ms)(?:\r?\n+---\s*)+\Z", "", content)

    # 4. Normaliser la fin de fichier (single trailing newline)
    cleaned = content.rstrip() + "\n"
    return cleaned, cleaned != original

def run_story_clean(project_path: Path, verbose: bool = False):
    """
    Supprime toutes les sections de traçabilité et blocs IA historiquement
    injectés en dur dans les récits Markdown (dette pré-ADR-0326/0333).
    
    Sanctuarise le gabarit story_template.md qui s'arrête STRICTEMENT à '## Scénarios de test'.
    Toute la traçabilité réside exclusivement dans memory/evidence/<STORY_ID>_evidence.json.
    """
    stories_dir = project_path / "backlog" / "stories"
    if not stories_dir.exists():
        if verbose:
            ZeroFluffConsole.info(f"Aucun dossier backlog/stories/ trouvé sous : {project_path}")
        return

    cleaned_count = 0
    inspected_count = 0

    for fpath in sorted(stories_dir.rglob("*.md")):
        inspected_count += 1
        content = fpath.read_text(encoding="utf-8")
        new_content, changed = clean_story_markdown(content)
        if changed:
            fpath.write_text(new_content, encoding="utf-8")
            cleaned_count += 1
            ZeroFluffConsole.success(f"Nettoyé : {fpath.name}")
        elif verbose:
            ZeroFluffConsole.info(f"Déjà conforme : {fpath.name}")

    if verbose or cleaned_count > 0:
        ZeroFluffConsole.info(f"[story-clean] {inspected_count} fichier(s) inspecté(s), {cleaned_count} fichier(s) nettoyé(s).")

