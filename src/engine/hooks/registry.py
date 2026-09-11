"""
mLoop Lifecycle Hooks Engine.
Inspiré du système d'événements et de hooks d'OpenAI Codex.

Fournit un bus d'interception standardisé pour :
- session_start : Initialisation et amorçage Boot Sequence
- session_end : Nettoyage et Teardown Gate
- user_prompt_submit : Détection d'URL (crawling) et enrichissement Fact-Search
- pre_tool_use : Validation de sécurité Guardian
- post_tool_use : Capture de preuves Fact-Search et EvidencePacks
"""

from typing import Callable, Dict, List, Any, Optional
import time
from dataclasses import dataclass


@dataclass
class HookEvent:
    name: str
    payload: Dict[str, Any]
    timestamp: float = time.time()


HookHandler = Callable[[HookEvent], Optional[Dict[str, Any]]]


class LifecycleHookRegistry:
    """
    Registre central des hooks du cycle de vie mLoop.
    """

    def __init__(self):
        self._handlers: Dict[str, List[HookHandler]] = {
            "session_start": [],
            "session_end": [],
            "user_prompt_submit": [],
            "pre_tool_use": [],
            "post_tool_use": [],
            "interrupt": [],
            "pre_compact": [],
            "post_compact": [],
            "checkpoint_resume": [],
        }

    def register(self, event_name: str, handler: HookHandler) -> None:
        if event_name not in self._handlers:
            self._handlers[event_name] = []
        self._handlers[event_name].append(handler)

    def trigger(self, event_name: str, payload: Dict[str, Any]) -> List[Any]:
        """
        Déclenche séquentiellement tous les handlers enregistrés pour un événement donné.
        """
        event = HookEvent(name=event_name, payload=payload)
        results = []
        for handler in self._handlers.get(event_name, []):
            try:
                res = handler(event)
                if res is not None:
                    results.append(res)
            except Exception as ex:
                print(f"⚠️ [HOOK ENGINE] Erreur lors de l'exécution du hook '{event_name}' : {ex}")
        return results


# Instance singleton globale
global_hook_registry = LifecycleHookRegistry()
