#!/usr/bin/env python
"""
Error recovery and retry example.

Demonstrates how to use retry logic with exponential backoff and jitter
to recover from transient failures.

Requirements: pip install socratic-workflow
"""

import random

from socratic_workflow.execution.retry import (
    RetryableFunction,
    RetryConfig,
    retry,
)

from socratic_workflow import Task


class FlakeyTask(Task):
    """Task that fails intermittently."""

    def execute(self, context):
        """Execute and fail randomly."""
        failure_rate = self.config.get("failure_rate", 0.5)

        # Fail based on probability
        if random.random() < failure_rate:
            attempt_num = self.config.get("attempt", 0)
            raise ValueError(
                f"Transient failure on attempt {attempt_num + 1} "
                f"(failure_rate={failure_rate:.0%})"
            )

        return {"status": "success", "value": 42}


class APICallTask(Task):
    """Task that simulates API calls that might fail."""

    def execute(self, context):
        """Execute API call that might fail."""
        endpoint = self.config.get("endpoint", "/api/data")
        max_retries = self.config.get("max_retries", 3)

        # Simulate retry attempts
        for attempt in range(max_retries):
            if random.random() < 0.7:  # 70% chance of failure
                if attempt < max_retries - 1:
                    continue
                raise RuntimeError(f"API call to {endpoint} failed after {max_retries} attempts")

        return {"endpoint": endpoint, "data": {"id": 1, "value": "success"}}


def example_1_retry_config_basics():
    """Example 1: Basic retry configuration."""
    print("=" * 70)
    print("EXAMPLE 1: Retry Configuration Basics")
    print("=" * 70)
    print()

    print("RetryConfig provides configurable retry behavior:")
    print()

    # Default configuration
    print("1. Default configuration (3 attempts, 1s initial delay, 60s max):")
    config = RetryConfig()
    print(f"   max_attempts: {config.max_attempts}")
    print(f"   initial_delay: {config.initial_delay}s")
    print(f"   max_delay: {config.max_delay}s")
    print(f"   exponential_base: {config.exponential_base}")
    print(f"   jitter: {config.jitter}")
    print()

    # Custom configuration for aggressive retries
    print("2. Aggressive retry (5 attempts, quick retries):")
    config = RetryConfig(max_attempts=5, initial_delay=0.1, exponential_base=1.5)
    print(f"   max_attempts: {config.max_attempts}")
    print(f"   initial_delay: {config.initial_delay}s")
    print(f"   exponential_base: {config.exponential_base}")
    print()

    # Custom configuration for conservative retries
    print("3. Conservative retry (2 attempts, longer delays):")
    config = RetryConfig(max_attempts=2, initial_delay=2.0, exponential_base=3.0)
    print(f"   max_attempts: {config.max_attempts}")
    print(f"   initial_delay: {config.initial_delay}s")
    print(f"   exponential_base: {config.exponential_base}")
    print()


def example_2_exponential_backoff():
    """Example 2: Exponential backoff with jitter."""
    print("=" * 70)
    print("EXAMPLE 2: Exponential Backoff with Jitter")
    print("=" * 70)
    print()

    config = RetryConfig(
        max_attempts=5,
        initial_delay=1.0,
        exponential_base=2.0,
        max_delay=30.0,
        jitter=False,
    )

    print("Delay progression (without jitter):")
    print("Attempt | Base Delay | Max Delay | Final Delay")
    print("-" * 50)
    for attempt in range(5):
        delay = config.calculate_delay(attempt)
        base = config.initial_delay * (config.exponential_base**attempt)
        print(f"   {attempt}    | {base:8.2f}s  | {config.max_delay:7.1f}s | {delay:10.2f}s")

    print()
    print("With jitter enabled, delays vary randomly (±25%):")
    config_jitter = RetryConfig(
        max_attempts=3, initial_delay=1.0, exponential_base=2.0, jitter=True
    )

    print("Attempt | Jittered Delays (multiple runs)")
    print("-" * 50)
    for attempt in range(3):
        delays = [config_jitter.calculate_delay(attempt) for _ in range(5)]
        delay_str = ", ".join(f"{d:.2f}s" for d in delays)
        print(f"   {attempt}    | {delay_str}")
    print()


def example_3_retry_decorator():
    """Example 3: Using the @retry decorator."""
    print("=" * 70)
    print("EXAMPLE 3: @retry Decorator Pattern")
    print("=" * 70)
    print()

    attempt_count = [0]

    @retry(RetryConfig(max_attempts=3, initial_delay=0.01, jitter=False))
    def fetch_data():
        """Simulated function that might fail."""
        attempt_count[0] += 1
        if attempt_count[0] < 3:
            raise ConnectionError(f"Connection failed on attempt {attempt_count[0]}")
        return {"status": "connected", "data": [1, 2, 3]}

    print("Decorated function: fetch_data()")
    print("Configured with: max_attempts=3, initial_delay=0.01s")
    print()

    print("Calling fetch_data()...")
    result = fetch_data()

    print(f"Result after {attempt_count[0]} attempts: {result}")
    print(f"Retryable function info: {fetch_data.retryable.attempt_count} attempts made")
    print()


def example_4_selective_retry():
    """Example 4: Selective retry by exception type."""
    print("=" * 70)
    print("EXAMPLE 4: Selective Retry by Exception Type")
    print("=" * 70)
    print()

    # Only retry on ConnectionError and TimeoutError
    config = RetryConfig(
        max_attempts=3,
        initial_delay=0.05,
        retryable_exceptions=[ConnectionError, TimeoutError],
    )

    print("Configuration: Retry only on ConnectionError and TimeoutError")
    print()

    # Test 1: Retryable exception
    print("1. Retryable exception (ConnectionError):")
    print(f"   should_retry(ConnectionError): {config.should_retry(ConnectionError('test'), 0)}")

    # Test 2: Non-retryable exception
    print("2. Non-retryable exception (ValueError):")
    print(f"   should_retry(ValueError): {config.should_retry(ValueError('test'), 0)}")

    # Test 3: After exhausting attempts
    print("3. After exhausting attempts:")
    print(
        f"   should_retry(ConnectionError, attempt=2): {config.should_retry(ConnectionError('test'), 2)}"
    )
    print()


def example_5_retry_statistics():
    """Example 5: Retry statistics and tracking."""
    print("=" * 70)
    print("EXAMPLE 5: Retry Statistics and Tracking")
    print("=" * 70)
    print()

    def unstable_api_call():
        """Simulated API call with tracking."""
        import random

        if random.random() < 0.6:  # 60% failure rate
            raise ConnectionError("API temporarily unavailable")
        return {"result": "success"}

    config = RetryConfig(max_attempts=3, initial_delay=0.01, jitter=False)
    retryable = RetryableFunction(unstable_api_call, config)

    print("Running unstable API call with retry...")
    print()

    try:
        result = retryable()
        print(f"Success after {retryable.attempt_count} attempt(s)")
        print(f"Result: {result}")
    except Exception:
        print(f"Failed after {retryable.attempt_count} attempt(s)")
        print(f"Last error: {retryable.last_exception}")
    print()


def example_6_comparison_retry_strategies():
    """Example 6: Comparing different retry strategies."""
    print("=" * 70)
    print("EXAMPLE 6: Comparing Retry Strategies")
    print("=" * 70)
    print()

    strategies = {
        "Conservative": RetryConfig(max_attempts=2, initial_delay=2.0, exponential_base=2.0),
        "Moderate": RetryConfig(max_attempts=4, initial_delay=1.0, exponential_base=2.0),
        "Aggressive": RetryConfig(max_attempts=6, initial_delay=0.1, exponential_base=1.5),
    }

    print("Total delay needed for each strategy (no jitter):")
    print()

    for strategy_name, config in strategies.items():
        delays = [config.calculate_delay(i) for i in range(config.max_attempts - 1)]
        total_delay = sum(delays)

        print(f"{strategy_name}:")
        print(f"  Max attempts: {config.max_attempts}")
        print(f"  Delays between attempts: {', '.join(f'{d:.2f}s' for d in delays)}")
        print(f"  Total delay time: {total_delay:.2f}s")
        print()


def main():
    """Run all examples."""
    print()
    print("*" * 70)
    print("ERROR RECOVERY AND RETRY EXAMPLES")
    print("*" * 70)
    print()

    example_1_retry_config_basics()
    print()

    example_2_exponential_backoff()
    print()

    example_3_retry_decorator()

    example_4_selective_retry()
    print()

    example_5_retry_statistics()

    example_6_comparison_retry_strategies()

    print()
    print("*" * 70)
    print("Examples Complete!")
    print("*" * 70)
    print()


if __name__ == "__main__":
    main()
