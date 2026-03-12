"""Retry logic and error recovery utilities."""

import asyncio
import random
import time
from typing import Any, Callable, Coroutine, Optional, TypeVar

T = TypeVar("T")


class RetryConfig:
    """Configuration for retry behavior."""

    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        retryable_exceptions: Optional[list] = None,
    ):
        """
        Initialize retry configuration.

        Args:
            max_attempts: Maximum number of attempts
            initial_delay: Initial delay between retries (seconds)
            max_delay: Maximum delay between retries (seconds)
            exponential_base: Base for exponential backoff
            jitter: Add randomness to delay to prevent thundering herd
            retryable_exceptions: List of exception types to retry on
        """
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.retryable_exceptions = retryable_exceptions or [Exception]

    def calculate_delay(self, attempt: int) -> float:
        """
        Calculate delay for given attempt number.

        Args:
            attempt: Attempt number (0-indexed)

        Returns:
            Delay in seconds
        """
        # Exponential backoff: initial_delay * (exponential_base ^ attempt)
        delay = self.initial_delay * (self.exponential_base**attempt)

        # Cap at max_delay
        delay = min(delay, self.max_delay)

        # Add jitter if enabled
        if self.jitter:
            # Add ±25% random variation
            jitter_amount = delay * 0.25
            delay += random.uniform(-jitter_amount, jitter_amount)

        return max(0, delay)  # Ensure non-negative

    def should_retry(self, exception: Exception, attempt: int) -> bool:
        """
        Determine if exception should be retried.

        Args:
            exception: Exception that was raised
            attempt: Attempt number (0-indexed)

        Returns:
            True if should retry, False otherwise
        """
        # Check if max attempts reached
        if attempt >= self.max_attempts - 1:
            return False

        # Check if exception type is retryable
        for exc_type in self.retryable_exceptions:
            if isinstance(exception, exc_type):
                return True

        return False


class RetryableFunction:
    """Wrapper for a function with retry logic."""

    def __init__(self, func: Callable[..., T], config: Optional[RetryConfig] = None):
        """
        Initialize retryable function.

        Args:
            func: Function to wrap
            config: Retry configuration (uses defaults if None)
        """
        self.func = func
        self.config = config or RetryConfig()
        self.attempt_count = 0
        self.last_exception: Optional[Exception] = None

    def __call__(self, *args: Any, **kwargs: Any) -> T:  # type: ignore[type-var]
        """
        Call function with retry logic.

        Returns:
            Function result

        Raises:
            Last exception if all retries exhausted
        """
        self.attempt_count = 0
        last_exception = None

        for attempt in range(self.config.max_attempts):
            self.attempt_count = attempt + 1

            try:
                return self.func(*args, **kwargs)  # type: ignore[return-value]
            except Exception as e:
                last_exception = e
                self.last_exception = e

                if not self.config.should_retry(e, attempt):
                    raise

                # Calculate and apply delay
                delay = self.config.calculate_delay(attempt)
                if delay > 0:
                    time.sleep(delay)

        # All retries exhausted
        if last_exception:
            raise last_exception
        raise RuntimeError("Retry exhausted without exception")


def retry(config: Optional[RetryConfig] = None) -> Callable:
    """
    Decorator for retrying a function.

    Args:
        config: Retry configuration

    Returns:
        Decorator function

    Example:
        @retry(RetryConfig(max_attempts=3))
        def risky_operation():
            ...
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        retryable = RetryableFunction(func, config or RetryConfig())

        def wrapper(*args: Any, **kwargs: Any) -> T:
            return retryable(*args, **kwargs)

        wrapper.retryable = retryable  # type: ignore
        return wrapper

    return decorator


async def retry_async(
    func: Callable[[], Coroutine[Any, Any, T]], config: Optional[RetryConfig] = None
) -> T:
    """
    Async version of retry.

    Args:
        func: Async function to retry
        config: Retry configuration

    Returns:
        Function result
    """
    cfg = config or RetryConfig()
    last_exception = None

    for attempt in range(cfg.max_attempts):
        try:
            return await func()
        except Exception as e:
            last_exception = e

            if not cfg.should_retry(e, attempt):
                raise

            # Calculate and apply delay
            delay = cfg.calculate_delay(attempt)
            if delay > 0:
                await asyncio.sleep(delay)

    # All retries exhausted
    if last_exception:
        raise last_exception
    raise RuntimeError("Async retry exhausted without exception")
