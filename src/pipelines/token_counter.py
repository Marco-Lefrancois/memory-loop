"""
TokenCounter — Mesure réelle de tokens via APIs LiteLLM (MLOOP-134-BE / ADR-0202).

Instrumente les appels CodeGraph et Graphify, agrège par moteur/question,
et génère un rapport JSON structuré. Conforme ADR-0369 (context managers,
timeout, logs structurés). <300 lignes, latence <5ms supplémentaires.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, AsyncIterator, Callable, Dict, List, Optional

from src.utils.logger import get_logger

logger = get_logger("token_counter")

_MAX_ENTRIES = 5000
_COMPLETION_TIMEOUT_S = 120.0


def _hash_token(text: str) -> str:
    """SHA-256 tronqué pour confidentialité des tokens."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


@dataclass(frozen=True, slots=True)
class TokenUsage:
    """Mesure de tokens pour un appel LLM unique."""

    engine: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cached: bool = False
    model: str = ""
    action: str = ""
    target: str = ""
    timestamp: float = field(default_factory=time.time)
    prompt_hash: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "engine": self.engine,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "cached": self.cached,
            "model": self.model,
            "action": self.action,
            "target": self.target,
            "timestamp": self.timestamp,
            "prompt_hash": self.prompt_hash,
        }


@dataclass
class _EngineAgg:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    call_count: int = 0
    cache_hits: int = 0
    models: Dict[str, int] = field(default_factory=dict)


class TokenCounter:
    """
    Compteur de tokens réels avec agrégation par moteur.
    Thread-safe via verrou interne. <300 lignes.
    """

    def __init__(self, project_name: str = "mLoop") -> None:
        self.project_name = project_name
        self._entries: List[TokenUsage] = []
        self._engine_totals: Dict[str, _EngineAgg] = {}
        self._question_index: Dict[str, List[int]] = {}

    @property
    def total_tokens(self) -> int:
        return sum(e.total_tokens for e in self._entries)

    @property
    def total_calls(self) -> int:
        return len(self._entries)

    def record(
        self,
        engine: str,
        prompt_tokens: int,
        completion_tokens: int,
        cached: bool = False,
        model: str = "",
        action: str = "",
        target: str = "",
        prompt_text: str = "",
    ) -> TokenUsage:
        """Enregistre un appel LLM et retourne l'entrée."""
        if len(self._entries) >= _MAX_ENTRIES:
            self._entries = self._entries[_MAX_ENTRIES // 2 :]

        usage = TokenUsage(
            engine=engine,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            cached=cached,
            model=model,
            action=action,
            target=target,
            prompt_hash=_hash_token(prompt_text) if prompt_text else "",
        )
        self._entries.append(usage)

        agg = self._engine_totals.setdefault(engine, _EngineAgg())
        agg.prompt_tokens += prompt_tokens
        agg.completion_tokens += completion_tokens
        agg.call_count += 1
        if cached:
            agg.cache_hits += 1
        if model:
            agg.models[model] = agg.models.get(model, 0) + 1

        if action:
            self._question_index.setdefault(action, []).append(len(self._entries) - 1)

        logger.debug(
            "Token recorded",
            extra={
                "engine": engine,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "cached": cached,
            },
        )
        return usage

    def record_from_response(
        self,
        engine: str,
        response: Any,
        model: str = "",
        action: str = "",
        target: str = "",
        prompt_text: str = "",
    ) -> TokenUsage:
        """Extrait les tokens depuis une réponse API OpenAI/LiteLLM (usage attr)."""
        usage_obj = getattr(response, "usage", None)
        p_tok = getattr(usage_obj, "prompt_tokens", 0) if usage_obj else 0
        c_tok = getattr(usage_obj, "completion_tokens", 0) if usage_obj else 0
        cached = bool(getattr(usage_obj, "prompt_tokens_details", None))
        return self.record(
            engine=engine,
            prompt_tokens=p_tok,
            completion_tokens=c_tok,
            cached=cached,
            model=model,
            action=action,
            target=target,
            prompt_text=prompt_text,
        )

    @asynccontextmanager
    async def track_llm_call(
        self,
        engine: str,
        client_complete: Callable[..., Any],
        *,
        model: str = "",
        action: str = "",
        target: str = "",
        **kwargs: Any,
    ) -> AsyncIterator[Dict[str, Any]]:
        """Context manager async qui instrumente un appel LLM et enregistre les tokens."""
        start = time.monotonic()
        try:
            if asyncio.iscoroutinefunction(client_complete):
                result = await asyncio.wait_for(
                    client_complete(**kwargs),
                    timeout=_COMPLETION_TIMEOUT_S,
                )
            else:
                result = client_complete(**kwargs)
        except asyncio.TimeoutError:
            logger.warning(
                "LLM call timed out",
                extra={"engine": engine, "timeout": _COMPLETION_TIMEOUT_S},
            )
            raise
        except Exception as exc:
            logger.warning(
                "LLM call failed",
                extra={"engine": engine, "error": str(exc)},
            )
            raise

        elapsed_ms = (time.monotonic() - start) * 1000

        self.record_from_response(
            engine=engine,
            response=result,
            model=model or getattr(result, "model", ""),
            action=action,
            target=target,
            prompt_text=kwargs.get("user_prompt", "") or kwargs.get("prompt", ""),
        )

        if elapsed_ms > 5.0:
            logger.debug(
                "LLM call exceeded 5ms overhead budget",
                extra={"engine": engine, "elapsed_ms": round(elapsed_ms, 1)},
            )

        yield {"result": result, "elapsed_ms": round(elapsed_ms, 1)}

    def get_engine_summary(self) -> Dict[str, Dict[str, Any]]:
        """Retourne l'agrégation par moteur."""
        return {
            engine: {
                "prompt_tokens": agg.prompt_tokens,
                "completion_tokens": agg.completion_tokens,
                "total_tokens": agg.prompt_tokens + agg.completion_tokens,
                "call_count": agg.call_count,
                "cache_hits": agg.cache_hits,
                "cache_hit_ratio": (
                    round(agg.cache_hits / agg.call_count, 3) if agg.call_count > 0 else 0.0
                ),
                "models_used": list(agg.models.keys()),
            }
            for engine, agg in self._engine_totals.items()
        }

    def get_question_breakdown(self) -> Dict[str, Dict[str, int]]:
        """Retourne l'agrégation par action/question."""
        breakdown: Dict[str, Dict[str, int]] = {}
        for action, indices in self._question_index.items():
            entries = [self._entries[i] for i in indices]
            breakdown[action] = {
                "total_tokens": sum(e.total_tokens for e in entries),
                "call_count": len(entries),
            }
        return breakdown

    def generate_report(
        self,
        output_path: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """Génère un rapport JSON structuré."""
        report = {
            "project": self.project_name,
            "summary": {
                "total_tokens": self.total_tokens,
                "total_calls": self.total_calls,
                "unique_engines": list(self._engine_totals.keys()),
            },
            "by_engine": self.get_engine_summary(),
            "by_question": self.get_question_breakdown(),
            "entries": [e.to_dict() for e in self._entries[-200:]],
        }

        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            try:
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(report, f, indent=2, ensure_ascii=False)
                logger.info(
                    "Token report written",
                    extra={"path": str(output_path), "total_tokens": self.total_tokens},
                )
            except OSError as exc:
                logger.warning(
                    "Failed to write token report",
                    extra={"path": str(output_path), "error": str(exc)},
                )

        return report

    def reset(self) -> None:
        """Vide le compteur (utile entre sessions)."""
        self._entries.clear()
        self._engine_totals.clear()
        self._question_index.clear()


_global_counter: Optional[TokenCounter] = None


def get_token_counter(project_name: str = "mLoop") -> TokenCounter:
    """Retourne le compteur global (singleton)."""
    global _global_counter
    if _global_counter is None:
        _global_counter = TokenCounter(project_name=project_name)
    return _global_counter


def reset_token_counter() -> TokenCounter:
    """Réinitialise le compteur global et retourne une nouvelle instance."""
    global _global_counter
    _global_counter = TokenCounter()
    return _global_counter
