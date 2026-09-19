"""
Système 2 : Contrôles Déterministes & Rétrospective Hybride (PR #1083 / ADR-0365).
Substitue les consignes de prompt textuelles fragiles par des vérifications AST et regex inviolables.
"""
import ast
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


MECHANICAL_KEYWORDS = {
    'placeholder', 'todo', 'fixme', 'ellipsis', 'stub',
    'focus', 'active story', 'no active story', 'lock',
    'import', 'deep module', 'boundary', 'barrel',
    'naming', 'convention', 'formatting', 'syntax',
    'compact', 'string', 'comment', 'verbeux', 'raccourcir'
}


def classify_anomaly(keyword_or_msg: str) -> Tuple[str, Optional[str]]:
    """
    Classifie une anomalie détectée lors d'une session ou d'une rétro.
    Retourne ('MECHANICAL', check_type) ou ('JUDGEMENT', None).
    """
    text = keyword_or_msg.lower()
    
    if any(k in text for k in ['placeholder', 'todo', 'fixme', 'ellipsis', 'stub']):
        return 'MECHANICAL', 'no_placeholders'
    if any(k in text for k in ['focus', 'active story', 'no active story', 'lock']):
        return 'MECHANICAL', 'focus_lock'
    if any(k in text for k in ['import', 'deep module', 'boundary', 'barrel']):
        return 'MECHANICAL', 'deep_module_boundaries'
    if any(k in text for k in ['naming', 'convention', 'syntax', 'format']):
        return 'MECHANICAL', 'syntax_and_convention'
    if any(k in text for k in ['compact', 'string multi-ligne', 'commentaire verbeux', 'raccourcir', 'commentaires verbeux']):
        return 'MECHANICAL', 'compact_strings_and_comments'
        
    return 'JUDGEMENT', None


def check_no_placeholders(code_or_file: str, is_file: bool = False) -> List[Dict[str, Any]]:
    """
    Détecte les ellipses, placeholders et TODO interdits dans le code source (RHO-002 déterministe).
    """
    if is_file:
        p = Path(code_or_file)
        if not p.exists():
            return []
        lines = p.read_text(encoding='utf-8', errors='ignore').splitlines()
    else:
        lines = code_or_file.splitlines()

    violations = []
    placeholder_patterns = [
        re.compile(r'//\s*TODO', re.IGNORECASE),
        re.compile(r'/\*\s*TODO', re.IGNORECASE),
        re.compile(r'#\s*TODO', re.IGNORECASE),
        re.compile(r'#\s*FIXME', re.IGNORECASE),
        re.compile(r'<INSERT\s+CODE', re.IGNORECASE),
        re.compile(r'pass\s*#\s*stub', re.IGNORECASE),
        re.compile(r'\.\.\.\s*#\s*placeholder', re.IGNORECASE),
    ]

    for idx, line in enumerate(lines, 1):
        for pat in placeholder_patterns:
            if pat.search(line):
                violations.append({
                    'line': idx,
                    'snippet': line.strip(),
                    'rule': 'BANNED_PLACEHOLDER',
                    'message': f'Ligne {idx}: placeholder ou TODO interdit détecté.',
                })
                break

    return violations


def check_focus_lock(active_story_id: Optional[str], project_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Vérifie la présence et la validité d'une User Story active (RHO-001 déterministe).
    """
    if not active_story_id or not active_story_id.strip():
        return {
            'valid': False,
            'rule': 'FOCUS_LOCK_REQUIRED',
            'message': 'Aucun récit actif verrouillé dans le contexte. Exécutez focus --story <ID>.',
        }

    clean_id = active_story_id.strip().upper()
    if not re.match(r'^(US|SPIKE|FEAT|BUG)-[A-Z0-9_-]+$', clean_id, re.IGNORECASE):
        return {
            'valid': False,
            'rule': 'INVALID_STORY_FORMAT',
            'message': f'Identifiant de story invalide : {active_story_id}. Format attendu : US-XXX.',
        }

    return {
        'valid': True,
        'story_id': clean_id,
        'message': f'Focus lock actif et conforme sur {clean_id}.',
    }


def check_python_deep_module_boundaries(file_path: Path, base_dir: Optional[Path] = None) -> List[Dict[str, Any]]:
    """
    Vérifie l'encapsulation Deep Module (interdiction des imports internes profonds).
    """
    if not file_path.exists() or file_path.suffix != '.py':
        return []

    try:
        source = file_path.read_text(encoding='utf-8', errors='ignore')
        tree = ast.parse(source)
    except Exception:
        return []

    violations = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            parts = node.module.split('.')
            if len(parts) >= 4 and parts[0] in ['src', 'packages'] and parts[-1].startswith('_'):
                violations.append({
                    'line': node.lineno,
                    'module': node.module,
                    'rule': 'DEEP_MODULE_VIOLATION',
                    'message': f'Ligne {node.lineno}: import interne privé interdit ({node.module}). Passez par l API publique du package.',
                })

    return violations


def check_compact_strings_and_comments(
    code_or_file: str,
    is_file: bool = False,
    max_comment_lines: int = 5,
) -> List[Dict[str, Any]]:
    """
    Analyse statique des blocs de commentaires verbeux et docstrings multi-lignes excessives.
    Détecte les opportunités d'optimisation contextuelle (ADR-0202 & ADR-0365).
    """
    if is_file:
        p = Path(code_or_file)
        if not p.exists():
            return []
        lines = p.read_text(encoding='utf-8', errors='ignore').splitlines()
    else:
        lines = code_or_file.splitlines()

    violations = []
    consecutive_comments = 0
    start_line = 0

    for idx, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith('#') and not stripped.startswith('#!'):
            if consecutive_comments == 0:
                start_line = idx
            consecutive_comments += 1
        else:
            if consecutive_comments > max_comment_lines:
                violations.append({
                    'line': start_line,
                    'count': consecutive_comments,
                    'rule': 'EXCESSIVE_COMMENT_BLOCK',
                    'message': (
                        f"Bloc de commentaires verbeux détecté (lignes {start_line}-{start_line + consecutive_comments - 1}, "
                        f"{consecutive_comments} lignes). Raccourcir ou extraire en documentation externe."
                    ),
                })
            consecutive_comments = 0

    if consecutive_comments > max_comment_lines:
        violations.append({
            'line': start_line,
            'count': consecutive_comments,
            'rule': 'EXCESSIVE_COMMENT_BLOCK',
            'message': (
                f"Bloc de commentaires verbeux détecté (lignes {start_line}-{start_line + consecutive_comments - 1}, "
                f"{consecutive_comments} lignes). Raccourcir ou extraire en documentation externe."
            ),
        })

    return violations

