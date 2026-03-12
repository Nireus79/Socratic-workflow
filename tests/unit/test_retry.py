"""Tests for retry logic and error recovery."""

import pytest

from socratic_workflow.execution.retry import RetryableFunction, RetryConfig, retry, retry_async


class TestRetryConfig:
    """Test RetryConfig."""

    def test_config_creation(self):
        """Test RetryConfig can be created."""
        config = RetryConfig()
        assert config.max_attempts == 3
        assert config.initial_delay == 1.0
        assert config.max_delay == 60.0
        assert config.exponential_base == 2.0
        assert config.jitter is True

    def test_config_custom_values(self):
        """Test RetryConfig with custom values."""
        config = RetryConfig(
            max_attempts=5,
            initial_delay=0.5,
            max_delay=30.0,
            exponential_base=1.5,
            jitter=False,
        )

        assert config.max_attempts == 5
        assert config.initial_delay == 0.5
        assert config.max_delay == 30.0
        assert config.exponential_base == 1.5
        assert config.jitter is False

    def test_calculate_delay_first_attempt(self):
        """Test delay calculation for first attempt."""
        config = RetryConfig(
            initial_delay=1.0,
            exponential_base=2.0,
            jitter=False,
        )

        delay = config.calculate_delay(0)

        assert delay == 1.0

    def test_calculate_delay_second_attempt(self):
        """Test delay calculation for second attempt."""
        config = RetryConfig(
            initial_delay=1.0,
            exponential_base=2.0,
            jitter=False,
        )

        delay = config.calculate_delay(1)

        assert delay == 2.0

    def test_calculate_delay_exponential(self):
        """Test exponential backoff."""
        config = RetryConfig(
            initial_delay=1.0,
            exponential_base=2.0,
            jitter=False,
        )

        delays = [config.calculate_delay(i) for i in range(5)]

        assert delays == [1.0, 2.0, 4.0, 8.0, 16.0]

    def test_calculate_delay_caps_at_max(self):
        """Test delay is capped at max_delay."""
        config = RetryConfig(
            initial_delay=1.0,
            exponential_base=2.0,
            max_delay=10.0,
            jitter=False,
        )

        delay = config.calculate_delay(5)

        assert delay == 10.0

    def test_calculate_delay_with_jitter(self):
        """Test delay includes jitter."""
        config = RetryConfig(
            initial_delay=1.0,
            exponential_base=2.0,
            max_delay=60.0,
            jitter=True,
        )

        delays = [config.calculate_delay(0) for _ in range(10)]

        # All delays should be around 1.0 (±25%)
        assert all(0.75 <= delay <= 1.25 for delay in delays)
        # Not all should be exactly 1.0
        assert len(set(delays)) > 1

    def test_calculate_delay_non_negative(self):
        """Test delay is always non-negative."""
        config = RetryConfig(
            initial_delay=0.1,
            exponential_base=2.0,
            jitter=True,
        )

        for i in range(10):
            delay = config.calculate_delay(i)
            assert delay >= 0

    def test_should_retry_within_attempts(self):
        """Test should_retry returns True within attempts."""
        config = RetryConfig(max_attempts=3)

        assert config.should_retry(Exception("test"), 0) is True
        assert config.should_retry(Exception("test"), 1) is True

    def test_should_retry_exhausted_attempts(self):
        """Test should_retry returns False when attempts exhausted."""
        config = RetryConfig(max_attempts=3)

        assert config.should_retry(Exception("test"), 2) is False

    def test_should_retry_non_retryable_exception(self):
        """Test should_retry checks exception type."""
        config = RetryConfig(max_attempts=3, retryable_exceptions=[ValueError])

        assert config.should_retry(ValueError("test"), 0) is True
        assert config.should_retry(RuntimeError("test"), 0) is False

    def test_should_retry_multiple_exception_types(self):
        """Test should_retry with multiple exception types."""
        config = RetryConfig(max_attempts=3, retryable_exceptions=[ValueError, RuntimeError])

        assert config.should_retry(ValueError("test"), 0) is True
        assert config.should_retry(RuntimeError("test"), 0) is True
        assert config.should_retry(TypeError("test"), 0) is False


class TestRetryableFunction:
    """Test RetryableFunction."""

    def test_successful_call(self):
        """Test successful function call."""

        def func():
            return "success"

        retryable = RetryableFunction(func)
        result = retryable()

        assert result == "success"
        assert retryable.attempt_count == 1

    def test_call_with_args(self):
        """Test function call with arguments."""

        def func(a, b):
            return a + b

        retryable = RetryableFunction(func)
        result = retryable(2, 3)

        assert result == 5

    def test_call_with_kwargs(self):
        """Test function call with keyword arguments."""

        def func(a, b=10):
            return a + b

        retryable = RetryableFunction(func)
        result = retryable(5, b=15)

        assert result == 20

    def test_retry_on_failure(self):
        """Test function retries on failure."""
        call_count = [0]

        def func():
            call_count[0] += 1
            if call_count[0] < 3:
                raise ValueError("Not yet")
            return "success"

        config = RetryConfig(max_attempts=3, initial_delay=0.01, jitter=False)
        retryable = RetryableFunction(func, config)

        result = retryable()

        assert result == "success"
        assert retryable.attempt_count == 3
        assert call_count[0] == 3

    def test_exhaust_retries(self):
        """Test function raises after exhausting retries."""

        def func():
            raise ValueError("Always fails")

        config = RetryConfig(max_attempts=2, initial_delay=0.01)
        retryable = RetryableFunction(func, config)

        with pytest.raises(ValueError, match="Always fails"):
            retryable()

        assert retryable.attempt_count == 2

    def test_non_retryable_exception_no_retry(self):
        """Test non-retryable exceptions are not retried."""
        call_count = [0]

        def func():
            call_count[0] += 1
            raise TypeError("Not retryable")

        config = RetryConfig(max_attempts=3, retryable_exceptions=[ValueError])
        retryable = RetryableFunction(func, config)

        with pytest.raises(TypeError, match="Not retryable"):
            retryable()

        assert retryable.attempt_count == 1
        assert call_count[0] == 1

    def test_last_exception_stored(self):
        """Test last exception is stored."""

        def func():
            raise ValueError("Final error")

        config = RetryConfig(max_attempts=2, initial_delay=0.01)
        retryable = RetryableFunction(func, config)

        try:
            retryable()
        except ValueError:
            pass

        assert retryable.last_exception is not None
        assert str(retryable.last_exception) == "Final error"


class TestRetryDecorator:
    """Test retry decorator."""

    def test_decorator_successful(self):
        """Test retry decorator with successful function."""

        @retry()
        def func():
            return "success"

        result = func()

        assert result == "success"

    def test_decorator_with_retries(self):
        """Test retry decorator retries on failure."""
        call_count = [0]

        @retry(RetryConfig(max_attempts=3, initial_delay=0.01))
        def func():
            call_count[0] += 1
            if call_count[0] < 3:
                raise ValueError("Not yet")
            return "success"

        result = func()

        assert result == "success"
        assert call_count[0] == 3

    def test_decorator_has_retryable_attribute(self):
        """Test decorator adds retryable attribute."""

        @retry()
        def func():
            return "success"

        assert hasattr(func, "retryable")
        assert isinstance(func.retryable, RetryableFunction)

    def test_decorator_with_args_and_kwargs(self):
        """Test decorator works with args and kwargs."""
        call_count = [0]

        @retry(RetryConfig(max_attempts=3, initial_delay=0.01))
        def func(a, b, c=10):
            call_count[0] += 1
            if call_count[0] < 2:
                raise ValueError("Not yet")
            return a + b + c

        result = func(1, 2, c=3)

        assert result == 6
        assert call_count[0] == 2


class TestAsyncRetry:
    """Test async retry."""

    @pytest.mark.asyncio
    async def test_async_retry_successful(self):
        """Test successful async retry."""

        async def func():
            return "success"

        result = await retry_async(func)

        assert result == "success"

    @pytest.mark.asyncio
    async def test_async_retry_with_retries(self):
        """Test async retry retries on failure."""
        call_count = [0]

        async def func():
            call_count[0] += 1
            if call_count[0] < 3:
                raise ValueError("Not yet")
            return "success"

        config = RetryConfig(max_attempts=3, initial_delay=0.01, jitter=False)
        result = await retry_async(func, config)

        assert result == "success"
        assert call_count[0] == 3

    @pytest.mark.asyncio
    async def test_async_retry_exhausted(self):
        """Test async retry exhausts attempts."""

        async def func():
            raise ValueError("Always fails")

        config = RetryConfig(max_attempts=2, initial_delay=0.01)

        with pytest.raises(ValueError, match="Always fails"):
            await retry_async(func, config)

    @pytest.mark.asyncio
    async def test_async_retry_respects_delays(self):
        """Test async retry respects configured delays."""
        call_count = [0]
        import time

        start = time.time()

        async def func():
            call_count[0] += 1
            if call_count[0] < 2:
                raise ValueError("Not yet")
            return "success"

        config = RetryConfig(max_attempts=2, initial_delay=0.05, jitter=False)
        result = await retry_async(func, config)

        elapsed = time.time() - start

        assert result == "success"
        assert elapsed >= 0.05  # At least initial delay

    @pytest.mark.asyncio
    async def test_async_retry_non_retryable(self):
        """Test async retry with non-retryable exception."""
        call_count = [0]

        async def func():
            call_count[0] += 1
            raise TypeError("Not retryable")

        config = RetryConfig(max_attempts=3, retryable_exceptions=[ValueError])

        with pytest.raises(TypeError, match="Not retryable"):
            await retry_async(func, config)

        assert call_count[0] == 1
