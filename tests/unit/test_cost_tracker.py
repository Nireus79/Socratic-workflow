"""Tests for CostTracker."""

import pytest

from socratic_workflow.cost import CostTracker


class TestCostTracker:
    """Test CostTracker class."""

    def test_tracker_creation(self):
        """Test tracker can be created."""
        tracker = CostTracker()
        assert tracker.total_cost == 0.0
        assert len(tracker.calls) == 0

    def test_track_single_call(self):
        """Test tracking a single API call."""
        tracker = CostTracker()
        cost = tracker.track_call("claude-opus-4", 1000, 500)

        assert cost > 0
        assert tracker.get_total_cost() == cost
        assert tracker.get_call_count() == 1

    def test_track_multiple_calls(self):
        """Test tracking multiple calls."""
        tracker = CostTracker()

        cost1 = tracker.track_call("claude-opus-4", 1000, 500)
        cost2 = tracker.track_call("gpt-4", 1000, 500)
        cost3 = tracker.track_call("claude-haiku-4.5", 1000, 500)

        total = cost1 + cost2 + cost3
        assert abs(tracker.get_total_cost() - total) < 0.001
        assert tracker.get_call_count() == 3

    def test_cost_calculation(self):
        """Test cost calculation accuracy."""
        tracker = CostTracker()

        # Claude Opus-4: $0.015 per 1k input, $0.075 per 1k output
        # 1000 input tokens: 1 * 0.015 = $0.015
        # 500 output tokens: 0.5 * 0.075 = $0.0375
        # Total: $0.0525
        cost = tracker.track_call("claude-opus-4", 1000, 500)
        assert abs(cost - 0.0525) < 0.001

    def test_unsupported_model_error(self):
        """Test error on unsupported model."""
        tracker = CostTracker()

        with pytest.raises(ValueError, match="Unknown model"):
            tracker.track_call("unknown-model", 1000, 500)

    def test_cost_by_provider(self):
        """Test cost breakdown by provider."""
        tracker = CostTracker()

        tracker.track_call("claude-opus-4", 1000, 500)
        tracker.track_call("claude-haiku-4.5", 1000, 500)
        tracker.track_call("gpt-4", 1000, 500)

        costs = tracker.get_cost_by_provider()

        assert "anthropic" in costs
        assert "openai" in costs
        assert costs["anthropic"] > 0
        assert costs["openai"] > 0

    def test_cost_by_model(self):
        """Test cost breakdown by model."""
        tracker = CostTracker()

        tracker.track_call("claude-opus-4", 1000, 500)
        tracker.track_call("claude-opus-4", 1000, 500)
        tracker.track_call("gpt-4", 1000, 500)

        costs = tracker.get_cost_by_model()

        assert "claude-opus-4" in costs
        assert "gpt-4" in costs
        # Should have double the cost for claude-opus-4
        assert costs["claude-opus-4"] > costs["gpt-4"]

    def test_total_tokens(self):
        """Test token counting."""
        tracker = CostTracker()

        tracker.track_call("claude-opus-4", 1000, 500)
        tracker.track_call("gpt-4", 2000, 1000)

        tokens = tracker.get_total_tokens()

        assert tokens["input"] == 3000
        assert tokens["output"] == 1500
        assert tokens["total"] == 4500

    def test_summary(self):
        """Test summary generation."""
        tracker = CostTracker()

        tracker.track_call("claude-opus-4", 1000, 500)
        tracker.track_call("gpt-4", 1000, 500)

        summary = tracker.get_summary()

        assert "total_cost_usd" in summary
        assert "total_calls" in summary
        assert "total_tokens" in summary
        assert "average_cost_per_call" in summary
        assert "cost_by_provider" in summary
        assert summary["total_calls"] == 2

    def test_recommendations(self):
        """Test cost recommendations."""
        tracker = CostTracker()

        # Track some calls
        tracker.track_call("gpt-4", 1000, 500)
        tracker.track_call("gpt-4", 1000, 500)

        recommendations = tracker.get_recommendations()

        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        assert isinstance(recommendations[0], str)

    def test_no_calls_recommendations(self):
        """Test recommendations with no calls."""
        tracker = CostTracker()
        recommendations = tracker.get_recommendations()

        assert len(recommendations) > 0
        assert "No calls" in recommendations[0]

    def test_reset(self):
        """Test resetting tracker."""
        tracker = CostTracker()

        tracker.track_call("claude-opus-4", 1000, 500)
        assert tracker.get_total_cost() > 0

        tracker.reset()

        assert tracker.get_total_cost() == 0.0
        assert tracker.get_call_count() == 0

    def test_supported_models(self):
        """Test getting supported models."""
        models = CostTracker.get_supported_models()

        assert "anthropic" in models
        assert "openai" in models
        assert "google" in models
        assert "claude-opus-4" in models["anthropic"]
        assert "gpt-4" in models["openai"]

    def test_provider_detection(self):
        """Test provider auto-detection."""
        tracker = CostTracker()

        # Should auto-detect provider
        cost = tracker.track_call("claude-opus-4", 1000, 500)
        assert cost > 0

        call = tracker.calls[0]
        assert call["provider"] == "anthropic"

    def test_provider_specification(self):
        """Test explicit provider specification."""
        tracker = CostTracker()

        cost = tracker.track_call("claude-opus-4", 1000, 500, provider="custom")
        assert cost > 0

        call = tracker.calls[0]
        assert call["provider"] == "custom"

    def test_call_records(self):
        """Test call records contain all info."""
        tracker = CostTracker()

        tracker.track_call("claude-opus-4", 1000, 500)

        call = tracker.calls[0]

        assert "timestamp" in call
        assert "model" in call
        assert "provider" in call
        assert "input_tokens" in call
        assert "output_tokens" in call
        assert "cost" in call
        assert call["model"] == "claude-opus-4"
        assert call["input_tokens"] == 1000
        assert call["output_tokens"] == 500

    def test_cheap_model_usage(self):
        """Test tracking cheap models."""
        tracker = CostTracker()

        # Haiku is much cheaper
        cost = tracker.track_call("claude-haiku-4.5", 10000, 5000)

        # Should be very cheap for 15k tokens
        assert cost < 0.10

    def test_expensive_model_usage(self):
        """Test tracking expensive models."""
        tracker = CostTracker()

        cost = tracker.track_call("gpt-4", 1000, 500)

        # GPT-4 is expensive
        assert cost > 0.03
