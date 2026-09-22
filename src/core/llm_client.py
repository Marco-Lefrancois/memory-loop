"""
AsyncLLMClient : Client asynchrone unifié et optimisé pour Memory Loop (mLoop).
- Support HTTP/2 persistant via httpx / AsyncOpenAI
- Limitation de concurrence et rate-limiting via asyncio.Semaphore
- Intégration transparente avec SemanticCache (0 token / 0ms sur hits)
- Optimisation pour le Prompt Prefix Caching (invariants en tête de message)
- Traçabilité automatique des coûts via TokenLedger
"""

import asyncio
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

try:
    import httpx
except ImportError:
    httpx = None

try:
    from openai import AsyncOpenAI
except ImportError:
    AsyncOpenAI = None

from src.core.semantic_cache import SemanticCache
from src.utils.token_ledger import TokenLedger
from src.utils.logger import get_logger

logger = get_logger("llm_client")


class AsyncLLMClient:
    """
    Client LLM asynchrone haute performance avec cache déterministe et gestion de flux.
    Supporte l'injection de dépendances et le protocole contextuel async with (ADR-0369).
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        max_concurrency: int = 20,
        enable_cache: bool = True,
        cache_db_path: Optional[Path] = None,
        cache: Optional[SemanticCache] = None,
        openai_client: Optional[Any] = None,
    ):
        self.base_url = (
            base_url
            or os.environ.get("LITELLM_BASE_URL", "https://api-ia.nmedia.ca").rstrip("/") + "/v1"
        )
        self.api_key = api_key or self._resolve_api_key()
        self.semaphore = asyncio.Semaphore(max_concurrency)
        self.enable_cache = enable_cache
        self.cache = cache or (SemanticCache(cache_db_path) if enable_cache else None)

        self._http_client: Optional[Any] = None
        self._openai_client: Optional[Any] = openai_client
        if self._openai_client is None and AsyncOpenAI is not None:
            # Initialisation AsyncOpenAI avec HTTP/2 si disponible
            if httpx is not None:
                try:
                    self._http_client = httpx.AsyncClient(
                        http2=True,
                        limits=httpx.Limits(max_keepalive_connections=50, max_connections=100),
                        timeout=60.0,
                    )
                except Exception as e:
                    logger.warning(
                        "Initialisation HTTP/2 échouée, repli sur client HTTP/1.1",
                        exc_info=True,
                        extra={
                            "component": "core.llm_client",
                            "operation": "__init__",
                            "error": str(e),
                        },
                    )
                    self._http_client = httpx.AsyncClient(timeout=60.0)

            self._openai_client = AsyncOpenAI(
                api_key=self.api_key or "sk-dummy",
                base_url=self.base_url,
                http_client=self._http_client,
            )

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.aclose()

    async def aclose(self):
        """Ferme proprement les sessions HTTP et clients asynchrones (ADR-0369)."""
        if self._openai_client and hasattr(self._openai_client, "close"):
            try:
                await self._openai_client.close()
            except Exception as e:
                logger.debug("Échec non bloquant fermeture client openai", exc_info=True)
        if (
            self._http_client
            and hasattr(self._http_client, "aclose")
            and not getattr(self._http_client, "is_closed", False)
        ):
            try:
                await self._http_client.aclose()
            except Exception as e:
                logger.debug("Échec non bloquant fermeture http_client", exc_info=True)

    def _resolve_api_key(self) -> str:
        """Résout la clé API active depuis les variables d'environnement ou les secrets."""
        try:
            from dotenv import load_dotenv

            env_file = Path(__file__).resolve().parents[2] / ".env"
            if env_file.exists():
                load_dotenv(dotenv_path=env_file, override=True)
            else:
                load_dotenv(override=True)
        except Exception as e:
            logger.debug(
                "Chargement du fichier .env échoué, lecture des variables d'environnement système",
                exc_info=True,
                extra={
                    "component": "core.llm_client",
                    "operation": "_resolve_api_key",
                    "error": str(e),
                },
            )

        active_val = os.environ.get("LITELLM_API_KEY")
        if active_val:
            active_val = active_val.strip()
            alias_map = {
                "LITELLM_API_KEY_BOIRE": "LITELLM_API_KEY_BOIRE",
                "${LITELLM_API_KEY_BOIRE}": "LITELLM_API_KEY_BOIRE",
                "boire": "LITELLM_API_KEY_BOIRE",
                "BOIRE": "LITELLM_API_KEY_BOIRE",
                "LITELLM_API_KEY_METRO": "LITELLM_API_KEY_METRO",
                "${LITELLM_API_KEY_METRO}": "LITELLM_API_KEY_METRO",
                "metro": "LITELLM_API_KEY_METRO",
                "METRO": "LITELLM_API_KEY_METRO",
                "LITELLM_API_KEY_PERSO": "LITELLM_API_KEY_PERSO",
                "${LITELLM_API_KEY_PERSO}": "LITELLM_API_KEY_PERSO",
                "perso": "LITELLM_API_KEY_PERSO",
                "PERSO": "LITELLM_API_KEY_PERSO",
            }
            if active_val in alias_map:
                target = os.environ.get(alias_map[active_val])
                if target:
                    return target.strip()
            elif not active_val.startswith("sk-"):
                clean_ref = active_val.strip("${}").strip()
                if clean_ref in os.environ:
                    return os.environ[clean_ref].strip()
            return active_val

        for env_var in [
            "LITELLM_API_KEY_BOIRE",
            "LITELLM_API_KEY_METRO",
            "LITELLM_API_KEY_PERSO",
            "OPENAI_API_KEY",
        ]:
            val = os.environ.get(env_var)
            if val:
                return val.strip()

        for secret_name in ["litellm-key", "nmedia-key", "openai-key"]:
            secret_path = Path.home() / ".secrets" / secret_name
            if secret_path.exists():
                try:
                    return secret_path.read_text(encoding="utf-8").strip()
                except Exception as e:
                    logger.warning(
                        "Lecture du fichier secret de clé API échouée",
                        exc_info=True,
                        extra={
                            "component": "core.llm_client",
                            "operation": "_resolve_api_key",
                            "secret_path": str(secret_path),
                            "error": str(e),
                        },
                    )
        return "sk-placeholder"

    @staticmethod
    def _format_messages_for_prefix_cache(
        system_prompt: str,
        user_prompt: str,
        history: Optional[List[Dict[str, str]]] = None,
    ) -> List[Dict[str, str]]:
        """
        Structure les messages pour maximiser le hit-rate du Prompt Prefix Caching.
        Le bloc système invariant et volumineux est placé en tête absolue.
        """
        messages = [{"role": "system", "content": system_prompt.strip()}]
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": user_prompt.strip()})
        return messages

    async def complete(
        self,
        model: str,
        system_prompt: str,
        user_prompt: str,
        response_schema: Optional[Dict[str, Any]] = None,
        temperature: float = 0.0,
        project_name: str = "mLoop",
        action_name: str = "llm_completion",
        target_name: Optional[str] = None,
        force_refresh: bool = False,
    ) -> Dict[str, Any]:
        """
        Exécute une complétion asynchrone avec cache déterministe et enregistrement de ledger.
        """
        cache_key = SemanticCache.compute_key(
            model=model,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response_schema=response_schema,
            temperature=temperature,
        )

        # 1. Vérification du Cache Déterministe
        if self.enable_cache and self.cache and not force_refresh:
            cached_result = self.cache.get(cache_key)
            if cached_result:
                return {
                    "text": cached_result["response_text"],
                    "json": cached_result["response_json"],
                    "cached": True,
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "model": model,
                }

        # 2. Exécution asynchrone avec contrôle de flux (Semaphore)
        messages = self._format_messages_for_prefix_cache(system_prompt, user_prompt)

        async with self.semaphore:
            if self._openai_client is None:
                raise RuntimeError("AsyncOpenAI n'est pas installé ou initialisé.")

            kwargs: Dict[str, Any] = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
            }

            if response_schema:
                kwargs["response_format"] = {"type": "json_object"}

            response = await self._openai_client.chat.completions.create(**kwargs)
            res_text = response.choices[0].message.content or ""

            usage = getattr(response, "usage", None)
            p_tok = (
                getattr(usage, "prompt_tokens", len(system_prompt + user_prompt) // 4)
                if usage
                else len(system_prompt + user_prompt) // 4
            )
            c_tok = (
                getattr(usage, "completion_tokens", len(res_text) // 4)
                if usage
                else len(res_text) // 4
            )

        # 3. Extraction / Parsing JSON optionnel
        parsed_json = None
        if response_schema or (res_text.strip().startswith("{") and res_text.strip().endswith("}")):
            try:
                # Nettoyage d'éventuels backticks markdown
                clean_json = re.sub(r"^```json\s*", "", res_text.strip(), flags=re.MULTILINE)
                clean_json = re.sub(r"\s*```$", "", clean_json, flags=re.MULTILINE).strip()
                parsed_json = json.loads(clean_json)
            except Exception as e:
                logger.warning(
                    "Parsing JSON de la réponse LLM échoué (réponse retournée en texte brut)",
                    exc_info=True,
                    extra={
                        "component": "core.llm_client",
                        "operation": "complete",
                        "model": model,
                        "error": str(e),
                    },
                )

        # 4. Enregistrement dans le SemanticCache
        if self.enable_cache and self.cache:
            self.cache.set(
                cache_key=cache_key,
                model=model,
                response_text=res_text,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                response_json=parsed_json,
                prompt_tokens=p_tok,
                completion_tokens=c_tok,
            )

        # 5. Enregistrement dans le TokenLedger
        try:
            TokenLedger.record_interaction(
                project_name=project_name,
                action=action_name,
                model=model,
                prompt_tokens=p_tok,
                completion_tokens=c_tok,
                target=target_name or "N/A",
            )
        except Exception as e:
            logger.debug(
                "Échec non bloquant de l'enregistrement dans TokenLedger",
                exc_info=True,
                extra={
                    "project": project_name,
                    "action": action_name,
                    "model": model,
                    "target": target_name or "N/A",
                },
            )

        return {
            "text": res_text,
            "json": parsed_json,
            "cached": False,
            "prompt_tokens": p_tok,
            "completion_tokens": c_tok,
            "model": model,
        }

    async def batch_complete(
        self,
        requests: List[Dict[str, Any]],
        project_name: str = "mLoop",
        overall_timeout: Optional[float] = None,
        per_request_timeout: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """
        Exécute une collection de requêtes en concurrence structurée via asyncio.TaskGroup (ADR-0367).
        Garantit l'éradication des tâches orphelines et supporte des budgets temporels hiérarchiques.
        """
        if not requests:
            return []

        results: List[Optional[Dict[str, Any]]] = [None] * len(requests)

        async def _run_indexed(idx: int, req: Dict[str, Any]):
            kwargs = {
                "model": req.get("model", "nmedia_cloud/claude-sonnet-4.6"),
                "system_prompt": req.get("system_prompt", ""),
                "user_prompt": req.get("user_prompt", ""),
                "response_schema": req.get("response_schema"),
                "temperature": req.get("temperature", 0.0),
                "project_name": project_name,
                "action_name": req.get("action_name", "batch_complete"),
                "target_name": req.get("target_name"),
            }
            if per_request_timeout:
                async with asyncio.timeout(per_request_timeout):
                    res = await self.complete(**kwargs)
            else:
                res = await self.complete(**kwargs)
            results[idx] = res

        async def _run_all():
            async with asyncio.TaskGroup() as tg:
                for idx, req in enumerate(requests):
                    tg.create_task(_run_indexed(idx, req))

        if overall_timeout:
            async with asyncio.timeout(overall_timeout):
                await _run_all()
        else:
            await _run_all()

        return [r for r in results if r is not None]
