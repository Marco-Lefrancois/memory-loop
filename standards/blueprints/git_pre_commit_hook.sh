#!/bin/sh
# mLoop Git Pre-Commit Hook — Garde-Fou Déterministe (MLOOP-105-BE)
# Audite les fichiers indexés via code-check (AST ADR-0202/0369) et struct-check (récits C1-C9).
# Bypass souverain d'urgence : définir MLOOP_SKIP_HOOKS à 1/true/yes (toute casse, zéro dépendance externe).

case "$MLOOP_SKIP_HOOKS" in
    1|[Tt][Rr][Uu][Ee]|[Yy][Ee][Ss])
        echo "⚠️  [mLoop Pre-Commit] Bypass souverain activé (MLOOP_SKIP_HOOKS=$MLOOP_SKIP_HOOKS)."
        exit 0
        ;;
esac

cd "{{ROOT_DIR}}" || exit 1

STAGED=$(git diff --cached --name-only --diff-filter=ACM)
if [ -z "$STAGED" ]; then
    exit 0
fi

PY_FILES=""
STORY_FILES=""
for file in $STAGED; do
    case "$file" in
        *.py)
            case "$file" in
                src/*) PY_FILES="$PY_FILES $file" ;;
            esac
            ;;
        backlog/stories/*.md|Projects/*/backlog/stories/*.md)
            STORY_FILES="$STORY_FILES $file"
            ;;
    esac
done

if [ -z "$PY_FILES" ] && [ -z "$STORY_FILES" ]; then
    echo "✅ [mLoop Pre-Commit] Aucun fichier régi (code/récit) indexé — validation instantanée."
    exit 0
fi

FAILED=0

for file in $PY_FILES; do
    python "{{SWARM_PY}}" code-check --file "$file"
    if [ $? -ne 0 ]; then
        FAILED=1
    fi
done

for file in $STORY_FILES; do
    python "{{SWARM_PY}}" struct-check --project {{PROJECT_NAME}} --file "$file"
    if [ $? -ne 0 ]; then
        FAILED=1
    fi
done

if [ $FAILED -ne 0 ]; then
    echo "❌ [mLoop Pre-Commit] Commit bloqué : violations détectées (code-check / struct-check)."
    echo "   Corrigez les violations ci-dessus, ou forcez avec MLOOP_SKIP_HOOKS=1 (urgence souveraine)."
    exit 1
fi

echo "✅ [mLoop Pre-Commit] Tous les fichiers indexés sont conformes — commit autorisé."
exit 0
