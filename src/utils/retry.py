"""
Retry Module - Robust API Retry with Exponential Backoff & Jitter for mLoop.

Implements production-grade resilience against network glitches, HTTP 429 Rate Limits,
and 503 Service Unavailable errors when calling LLM APIs or external tools.
"""

import time
import random
import functools
import logging
from typing import Callable, Any, Optional, Tuple, Type

logger = logging.getLogger("retry")


def robust_api_call(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 10.0,
    backoff_factor: float = 2.0,
    jitter: bool = True,
    retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,)
) -> Callable:
    """
    Decorator for robust API execution using Exponential Backoff with Jitter.

    :param max_retries: Maximum number of retry attempts.
    :param initial_delay: Base delay in seconds.
    :param max_delay: Upper cap for backoff delay.
    :param backoff_factor: Multiplier for exponential backoff.
    :param jitter: Adds random variation to prevent thundering herd.
    :param retryable_exceptions: Tuple of exception classes to trigger retries.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            delay = initial_delay
            last_exception: Optional[Exception] = None

            for attempt in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except retryable_exceptions as exc:
                    last_exception = exc
                    if attempt == max_retries:
                        logger.error(
                            f"[RobustRetry] Attempt {attempt}/{max_retries} failed for '{func.__name__}'. "
                            f"Max retries reached. Error: {exc}"
                        )
                        raise exc

                    # Calculate exponential backoff
                    sleep_time = min(delay, max_delay)
                    if jitter:
                        # Full Jitter strategy: uniform random float between 0 and calculated sleep_time
                        sleep_time = random.uniform(0.5 * sleep_time, sleep_time)

                    logger.warning(
                        f"[RobustRetry] Attempt {attempt}/{max_retries} failed for '{func.__name__}': {exc}. "
                        f"Retrying in {sleep_time:.2f}s..."
                    )
                    time.sleep(sleep_time)
                    delay *= backoff_factor

            if last_exception:
                raise last_exception

        return wrapper
    return decorator
