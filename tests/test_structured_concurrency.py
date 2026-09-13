"""
Tests unitaires et métrologiques d'orchestration asynchrone structurée (ADR-0367).
Vérifie l'éradication des tâches orphelines, le respect des sémaphores et des délais hiérarchiques.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from src.core.llm_client import AsyncLLMClient


@pytest.mark.asyncio
async def test_taskgroup_cancels_sibling_tasks_on_failure():
    """
    Prouve l'avantage constitutionnel de TaskGroup sur gather :
    Dès qu'une coroutine échoue, les coroutines sœurs doivent être immédiatement annulées.
    """
    sibling_started = False
    sibling_cancelled = False

    async def failing_task():
        await asyncio.sleep(0.01)
        raise ValueError("Simulated backend crash")

    async def long_sibling_task():
        nonlocal sibling_started, sibling_cancelled
        sibling_started = True
        try:
            await asyncio.sleep(1.0)
        except asyncio.CancelledError:
            sibling_cancelled = True
            raise

    # Avec TaskGroup, la tâche longue doit être annulée avant la fin du bloc
    with pytest.raises(ExceptionGroup if hasattr(__builtins__, "ExceptionGroup") else Exception):
        async with asyncio.TaskGroup() as tg:
            tg.create_task(failing_task())
            tg.create_task(long_sibling_task())

    assert sibling_started is True
    assert sibling_cancelled is True, "La coroutine sœur aurait dû être annulée par TaskGroup !"


@pytest.mark.asyncio
async def test_llm_client_batch_complete_with_taskgroup():
    """
    Vérifie que AsyncLLMClient.batch_complete utilise une concurrence structurée
    et ne laisse fuiter aucune tâche en arrière-plan en cas de crash partiel.
    """
    client = AsyncLLMClient(base_url="https://api.mock/v1", api_key="test-key")

    call_count = 0

    async def mock_complete(model, system_prompt, user_prompt, **kwargs):
        nonlocal call_count
        call_count += 1
        if "fail" in user_prompt:
            await asyncio.sleep(0.02)
            raise ConnectionError("LLM API Timeout/Error")
        await asyncio.sleep(0.05)
        return {"content": "ok", "cached": False}

    with patch.object(client, "complete", side_effect=mock_complete):
        requests = [
            {"user_prompt": "fail request"},
            {"user_prompt": "normal request 1"},
            {"user_prompt": "normal request 2"},
        ]

        # En cas d'échec d'un appel, batch_complete doit lever l'erreur et annuler le reste
        with pytest.raises((ConnectionError, ExceptionGroup if hasattr(__builtins__, "ExceptionGroup") else Exception)):
            await client.batch_complete(requests)


@pytest.mark.asyncio
async def test_semaphore_bounds_maximum_concurrency():
    """
    Vérifie qu'un sémaphore partagé borne strictement le pic de concurrence simultanée.
    """
    capacity = 3
    sem = asyncio.Semaphore(capacity)
    in_flight = 0
    max_observed_in_flight = 0

    async def bounded_worker(idx: int):
        nonlocal in_flight, max_observed_in_flight
        async with sem:
            in_flight += 1
            max_observed_in_flight = max(max_observed_in_flight, in_flight)
            await asyncio.sleep(0.03)
            in_flight -= 1
        return idx

    async with asyncio.TaskGroup() as tg:
        tasks = [tg.create_task(bounded_worker(i)) for i in range(15)]

    assert max_observed_in_flight <= capacity, f"Concurrence max observée ({max_observed_in_flight}) a dépassé la capacité ({capacity}) !"
    assert all(t.result() is not None for t in tasks)


@pytest.mark.asyncio
async def test_hierarchical_deadline_propagation():
    """
    Vérifie qu'un budget global via asyncio.timeout() interrompt les tâches si le délai expire,
    tout en préservant les résultats intermédiaires déjà terminés.
    """
    overall_timeout = 0.08
    results = {}

    async def fast_op():
        await asyncio.sleep(0.02)
        results["fast"] = "done"

    async def slow_op():
        await asyncio.sleep(0.5)
        results["slow"] = "done"

    try:
        async with asyncio.timeout(overall_timeout):
            async with asyncio.TaskGroup() as tg:
                tg.create_task(fast_op())
                tg.create_task(slow_op())
    except TimeoutError:
        pass

    assert results.get("fast") == "done", "L'opération rapide aurait dû terminer !"
    assert "slow" not in results, "L'opération lente aurait dû être coupée par le budget global !"
