"""
mLoop Framework Safe-Execution Wrapper
Gestionnaire d'exécution sécurisée pour intercepter les exceptions d'encodage (UTF-8 Windows),
encapsuler les erreurs d'état et empêcher les crashs brutaux de subprocess sous OpenCode.
"""

import sys
import io
import traceback
from src.utils.logger import get_logger

logger = get_logger("core.safe_exec")


def setup_utf8_environment():
    """
    Forcer les flux d'entrée/sortie de la console Python à utiliser l'encodage UTF-8
    avec repli propre en cas de caractères non pris en charge par le terminal Windows.
    """
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    except Exception as e:
        logger.warning(
            "Rewrap UTF-8 des flux console impossible, encodage système conservé",
            exc_info=True,
            extra={
                "component": "core.safe_exec",
                "operation": "setup_utf8_environment",
                "error": str(e),
            },
        )


def safe_run_entrypoint(main_func):
    """
    Décorateur / Enrobeur autour de main() pour intercepter toutes les exceptions non-gérées,
    empêcher les plantages non-zéro et produire un message structuré.
    """
    setup_utf8_environment()
    try:
        main_func()
    except KeyboardInterrupt:
        print("\n[mLoop CLI] Opération interrompue par l'utilisateur.")
        sys.exit(130)
    except Exception as e:
        err_name = type(e).__name__
        err_msg = str(e)

        # En-tête explicite d'avertissement
        print(f"\n⚠️  [mLoop EXECUTION GUARD] Une exception a été interceptée ({err_name}) :")
        print(f"   {err_msg}\n")

        # S'il s'agit d'une erreur d'état connue (StateTransitionError), fournir le conseil de remédiation
        if "StateTransitionError" in err_name or "VIOLATION" in err_msg or "VERROU" in err_msg:
            print("💡  Action recommandée :")
            print("   1. Vérifiez le statut des stories via 'python src/swarm.py cycle-status'.")
            print(
                "   2. Ajustez l'attention du récit actif avec 'python src/swarm.py focus --project <projet> --story <chemin>'."
            )

        # ADR-0369 Zero-Fail Carryover : TOUTE exception non gérée doit sortir en non-zéro.
        # L'ancien sys.exit(0) créait un fail-open silencieux (hook pre-commit MLOOP-105-BE
        # qui validait des commits dont struct-check avait crashé au démarrage).
        sys.exit(1)
