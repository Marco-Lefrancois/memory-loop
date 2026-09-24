#!/bin/sh
# mLoop Git Pre-Commit Hook — Garde-Fou Deterministe (MLOOP-105-BE / MLOOP-171-BE)
# Audite les fichiers indexes via RULE-AST-01-DELTA (anti-aggravation) et struct-check (recits C1-C9).
# Bypass souverain d'urgence : MLOOP_SKIP_HOOKS=1/true/yes (toute casse).
# Audit de chaque bypass : append horodate dans mloop_skip_hooks_audit.log (OQ-171-02).

case "$MLOOP_SKIP_HOOKS" in
    1|[Tt][Rr][Uu][Ee]|[Yy][Ee][Ss])
        echo "[mLoop Pre-Commit] Bypass souverain active (MLOOP_SKIP_HOOKS=$MLOOP_SKIP_HOOKS)."
        # Audit du bypass : printf horodate sans appel externe Python (zero dependance)
        # Ancre dynamique : fonctionne depuis la racine framework OU un sous-repo projet
        _TOP=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
        AUDIT_LOG="$_TOP/memory/evidence/mloop_skip_hooks_audit.log"
        AUDIT_DIR=$(dirname "$AUDIT_LOG")
        if [ ! -d "$AUDIT_DIR" ]; then
            mkdir -p "$AUDIT_DIR" 2>/dev/null
        fi
        _TS=$(date -u +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || echo "unknown-ts")
        _USER="${USER:-${USERNAME:-unknown}}"
        _REASON="${MLOOP_SKIP_HOOKS_REASON:-(aucune raison fournie)}"
        printf "%s | %s | MLOOP_SKIP_HOOKS=1 | reason=%s\n" \
            "$_TS" "$_USER" "$_REASON" >> "$AUDIT_LOG" 2>/dev/null || true
        exit 0
        ;;
esac

# FIX 2026-09-24 : ne plus cd un chemin relatif fixe (cassait depuis un sous-repo projet)
TOP=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
cd "$TOP" || exit 1

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
    echo "[mLoop Pre-Commit] Aucun fichier regi (code/recit) indexe — validation instantanee."
    exit 0
fi

FAILED=0

# Resolution binaire Python : venv local ($TOP), sinon venv framework ({{ROOT_DIR}}), sinon PATH
PYTHON_BIN="python"
if [ -f "$TOP/.venv/Scripts/python.exe" ]; then
    PYTHON_BIN="$TOP/.venv/Scripts/python.exe"
elif [ -f "$TOP/.venv/bin/python" ]; then
    PYTHON_BIN="$TOP/.venv/bin/python"
elif [ -f "{{ROOT_DIR}}/.venv/Scripts/python.exe" ]; then
    PYTHON_BIN="{{ROOT_DIR}}/.venv/Scripts/python.exe"
elif [ -f "{{ROOT_DIR}}/.venv/bin/python" ]; then
    PYTHON_BIN="{{ROOT_DIR}}/.venv/bin/python"
fi

for file in $PY_FILES; do
    "$PYTHON_BIN" -m src.pipelines.ast_delta_checker "$file"
    if [ $? -ne 0 ]; then
        FAILED=1
    fi
done

for file in $STORY_FILES; do
    "$PYTHON_BIN" "{{SWARM_PY}}" struct-check --project {{PROJECT_NAME}} --file "$file"
    if [ $? -ne 0 ]; then
        FAILED=1
    fi
done

if [ $FAILED -ne 0 ]; then
    echo "[mLoop Pre-Commit] Commit bloque : violations detectees (RULE-AST-01-DELTA / struct-check)."
    echo "   Corrigez les violations ci-dessus, ou forcez avec MLOOP_SKIP_HOOKS=1 (urgence souveraine)."
    exit 1
fi

echo "[mLoop Pre-Commit] Tous les fichiers indexes sont conformes — commit autorise."
exit 0
