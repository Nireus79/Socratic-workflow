"""LLM cost tracking across providers."""

from datetime import datetime
from typing import Dict, List, Optional


class CostTracker:
    """
    Track LLM costs across providers.

    Maintains up-to-date pricing for Claude, GPT-4, Gemini, Llama, and other models.
    Tracks token usage and calculates costs in real-time.
    """

    # Pricing data: {model: {input_cost_per_1k, output_cost_per_1k}}
    PRICING = {
        # Anthropic - Claude models
        "claude-opus-4": {"input": 0.015, "output": 0.075},
        "claude-sonnet-3.5": {"input": 0.003, "output": 0.015},
        "claude-haiku-4.5": {"input": 0.0008, "output": 0.004},
        "claude-opus": {"input": 0.015, "output": 0.075},
        "claude-sonnet": {"input": 0.003, "output": 0.015},
        "claude-haiku": {"input": 0.0008, "output": 0.004},
        # OpenAI - GPT models
        "gpt-4-turbo": {"input": 0.01, "output": 0.03},
        "gpt-4": {"input": 0.03, "output": 0.06},
        "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
        "gpt-4o": {"input": 0.005, "output": 0.015},
        # Google - Gemini models
        "gemini-1.5-pro": {"input": 0.00125, "output": 0.005},
        "gemini-1.5-flash": {"input": 0.000075, "output": 0.0003},
        "gemini-pro": {"input": 0.0005, "output": 0.0015},
        # Meta - Llama models (via API)
        "llama-2-70b": {"input": 0.001, "output": 0.001},
        "llama-3-70b": {"input": 0.001, "output": 0.001},
        # Open-source (local/self-hosted)
        "mistral-7b": {"input": 0, "output": 0},
        "mistral-medium": {"input": 0.00027, "output": 0.00081},
    }

    # Provider categories for cost breakdown
    PROVIDERS = {
        "anthropic": ["claude-opus-4", "claude-sonnet-3.5", "claude-haiku-4.5"],
        "openai": ["gpt-4-turbo", "gpt-4", "gpt-3.5-turbo", "gpt-4o"],
        "google": ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-pro"],
        "meta": ["llama-2-70b", "llama-3-70b"],
        "local": ["mistral-7b"],
    }

    def __init__(self):
        """Initialize cost tracker."""
        self.calls: List[Dict] = []
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cost = 0.0
        self.started_at = datetime.now().isoformat()

    def track_call(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        provider: Optional[str] = None,
    ) -> float:
        """
        Track a single LLM API call with input validation.

        Args:
            model: Model name (e.g., "claude-opus-4", "gpt-4")
            input_tokens: Number of input tokens (must be non-negative)
            output_tokens: Number of output tokens (must be non-negative)
            provider: Optional provider name (auto-detected if not provided)

        Returns:
            Cost of this call in USD

        Raises:
            ValueError: If model is unknown or token counts are invalid
            TypeError: If token counts are not integers
        """
        # Validate model
        if model not in self.PRICING:
            raise ValueError(f"Unknown model: {model}. Use get_supported_models() for list.")

        # Validate token counts are integers
        if not isinstance(input_tokens, int):
            raise TypeError(f"input_tokens must be an integer, got {type(input_tokens).__name__}")
        if not isinstance(output_tokens, int):
            raise TypeError(f"output_tokens must be an integer, got {type(output_tokens).__name__}")

        # Validate token counts are non-negative
        if input_tokens < 0:
            raise ValueError(f"input_tokens must be non-negative, got {input_tokens}")
        if output_tokens < 0:
            raise ValueError(f"output_tokens must be non-negative, got {output_tokens}")

        pricing = self.PRICING[model]  # type: ignore
        cost = (input_tokens / 1000 * pricing["input"]) + (  # type: ignore
            output_tokens / 1000 * pricing["output"]  # type: ignore
        )

        # Auto-detect provider if not provided
        if provider is None:
            provider = self._detect_provider(model)

        call_record = {
            "timestamp": datetime.now().isoformat(),
            "model": model,
            "provider": provider,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost": cost,
        }

        self.calls.append(call_record)
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.total_cost += cost

        return cost

    def get_total_cost(self) -> float:
        """Get total cost across all calls."""
        return self.total_cost

    def get_total_tokens(self) -> Dict[str, int]:
        """Get total tokens used."""
        return {
            "input": self.total_input_tokens,
            "output": self.total_output_tokens,
            "total": self.total_input_tokens + self.total_output_tokens,
        }

    def get_cost_by_provider(self) -> Dict[str, float]:
        """Get costs broken down by provider."""
        costs = {}
        for call in self.calls:
            provider = call["provider"]
            if provider not in costs:
                costs[provider] = 0.0
            costs[provider] += call["cost"]
        return costs

    def get_cost_by_model(self) -> Dict[str, float]:
        """Get costs broken down by model."""
        costs = {}
        for call in self.calls:
            model = call["model"]
            if model not in costs:
                costs[model] = 0.0
            costs[model] += call["cost"]
        return costs

    def get_call_count(self) -> int:
        """Get number of tracked calls."""
        return len(self.calls)

    def get_summary(self) -> Dict:
        """
        Get comprehensive cost summary.

        Returns:
            Dict with total cost, token counts, breakdown by provider/model
        """
        return {
            "total_cost_usd": round(self.total_cost, 4),
            "total_calls": len(self.calls),
            "total_tokens": self.get_total_tokens(),
            "average_cost_per_call": round(
                self.total_cost / len(self.calls) if self.calls else 0, 4
            ),
            "cost_by_provider": {k: round(v, 4) for k, v in self.get_cost_by_provider().items()},
            "cost_by_model": {k: round(v, 4) for k, v in self.get_cost_by_model().items()},
        }

    def get_recommendations(self) -> List[str]:
        """
        Get recommendations to reduce costs.

        Returns:
            List of cost optimization recommendations
        """
        recommendations = []

        if not self.calls:
            return ["No calls tracked yet"]

        # Analyze cost distribution
        costs_by_provider = self.get_cost_by_provider()
        total = self.total_cost

        # Find most expensive provider
        if costs_by_provider:
            expensive = max(costs_by_provider.items(), key=lambda x: x[1])
            percentage = (expensive[1] / total) * 100
            if percentage > 50:
                recommendations.append(
                    f"{expensive[0].title()} accounts for {percentage:.1f}% of costs. "
                    "Consider using cheaper alternatives or fewer calls."
                )

        # Check if using expensive models
        costs_by_model = self.get_cost_by_model()
        expensive_models = [m for m in costs_by_model if "gpt-4" in m or "opus-4" in m]
        if expensive_models:
            recommendations.append(
                f"Using expensive models: {', '.join(expensive_models)}. "
                "Consider using cheaper alternatives like Claude Haiku or GPT-3.5 Turbo."
            )

        # Check token efficiency
        avg_tokens_per_call = (self.total_input_tokens + self.total_output_tokens) / len(self.calls)
        if avg_tokens_per_call > 2000:
            recommendations.append(
                f"Average {avg_tokens_per_call:.0f} tokens per call. "
                "Consider optimizing prompts or reducing context size."
            )

        if not recommendations:
            recommendations.append("✓ Cost-effective usage detected. Well optimized!")

        return recommendations

    def reset(self) -> None:
        """Reset all tracked data."""
        self.calls = []
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cost = 0.0
        self.started_at = datetime.now().isoformat()

    @staticmethod
    def get_supported_models() -> Dict[str, List[str]]:
        """Get all supported models by provider."""
        return CostTracker.PROVIDERS.copy()

    @staticmethod
    def _detect_provider(model: str) -> str:
        """Detect provider from model name."""
        for provider, models in CostTracker.PROVIDERS.items():
            if model in models:
                return provider
        return "unknown"
