#!/usr/bin/env python
"""
Cost tracking example.

Demonstrates how to track LLM costs across different providers and models.

Requirements: pip install socratic-workflow
"""

from socratic_workflow import Task, Workflow, WorkflowEngine
from socratic_workflow.cost import CostTracker


class LLMTask(Task):
    """Task that simulates LLM API calls."""

    def execute(self, context):
        """Execute and track cost."""
        model = self.config.get("model", "claude-opus-4")
        input_tokens = self.config.get("input_tokens", 1000)
        output_tokens = self.config.get("output_tokens", 500)

        # Simulate LLM work
        return {
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "result": f"Processed with {model}",
        }


def example_1_basic_cost_tracking():
    """Example 1: Basic cost tracking."""
    print("=" * 70)
    print("EXAMPLE 1: Basic Cost Tracking")
    print("=" * 70)
    print()

    tracker = CostTracker()

    # Track various LLM calls
    print("Tracking API calls...")
    cost1 = tracker.track_call("claude-opus-4", 1000, 500)
    print(f"  Claude Opus-4: ${cost1:.4f}")

    cost2 = tracker.track_call("gpt-4", 1000, 500)
    print(f"  GPT-4: ${cost2:.4f}")

    cost3 = tracker.track_call("claude-haiku-4.5", 5000, 2000)
    print(f"  Claude Haiku: ${cost3:.4f}")

    print()
    print("Summary:")
    print(f"  Total cost: ${tracker.get_total_cost():.4f}")
    print(f"  Total calls: {tracker.get_call_count()}")
    print()


def example_2_cost_breakdown():
    """Example 2: Cost breakdown by provider."""
    print("=" * 70)
    print("EXAMPLE 2: Cost Breakdown by Provider")
    print("=" * 70)
    print()

    tracker = CostTracker()

    # Simulate multi-provider workflow
    models = [
        ("claude-opus-4", 2000, 1000),
        ("claude-opus-4", 1500, 800),
        ("gpt-4", 2000, 1000),
        ("gpt-4", 1000, 500),
        ("claude-haiku-4.5", 5000, 2000),
        ("gemini-1.5-pro", 1000, 500),
    ]

    print("Tracking calls across providers...")
    for model, input_tokens, output_tokens in models:
        cost = tracker.track_call(model, input_tokens, output_tokens)
        print(f"  {model:20s} -> ${cost:.4f}")

    print()
    print("Cost Summary:")
    summary = tracker.get_summary()

    print(f"  Total Cost:        ${summary['total_cost_usd']:.4f}")
    print(f"  Total Calls:       {summary['total_calls']}")
    print(f"  Avg Cost/Call:     ${summary['average_cost_per_call']:.4f}")
    print(f"  Total Tokens:      {summary['total_tokens']['total']:,}")
    print()

    print("Cost by Provider:")
    for provider, cost in summary["cost_by_provider"].items():
        percentage = cost / summary["total_cost_usd"] * 100
        print(f"  {provider:15s} ${cost:7.4f} ({percentage:5.1f}%)")

    print()
    print("Cost by Model:")
    for model, cost in sorted(summary["cost_by_model"].items(), key=lambda x: x[1], reverse=True):
        print(f"  {model:20s} ${cost:7.4f}")

    print()


def example_3_cost_recommendations():
    """Example 3: Cost optimization recommendations."""
    print("=" * 70)
    print("EXAMPLE 3: Cost Optimization Recommendations")
    print("=" * 70)
    print()

    tracker = CostTracker()

    # Simulate expensive usage pattern
    print("Simulating expensive usage pattern...")
    print("  Multiple GPT-4 calls with large contexts...")
    for _ in range(5):
        tracker.track_call("gpt-4", 5000, 2000)

    print()
    print("Recommendations:")
    recommendations = tracker.get_recommendations()
    for i, rec in enumerate(recommendations, 1):
        print(f"  {i}. {rec}")

    print()


def example_4_supported_models():
    """Example 4: Supported models."""
    print("=" * 70)
    print("EXAMPLE 4: Supported Models and Providers")
    print("=" * 70)
    print()

    models = CostTracker.get_supported_models()

    for provider, provider_models in sorted(models.items()):
        print(f"\n{provider.upper()}:")
        for model in provider_models:
            pricing = CostTracker.PRICING[model]
            print(
                f"  {model:25s} "
                f"(in: ${pricing['input']:.4f}/1k, "
                f"out: ${pricing['output']:.4f}/1k)"
            )


def example_5_workflow_cost_tracking():
    """Example 5: Cost tracking in a workflow."""
    print("=" * 70)
    print("EXAMPLE 5: Cost Tracking in Workflow")
    print("=" * 70)
    print()

    # Create workflow
    workflow = Workflow("Cost-Tracked Pipeline")
    workflow.add_task(
        "claude_task",
        LLMTask(model="claude-opus-4", input_tokens=2000, output_tokens=1000),
    )
    workflow.add_task(
        "gpt_task",
        LLMTask(model="gpt-4", input_tokens=1000, output_tokens=500),
        depends_on=["claude_task"],
    )
    workflow.add_task(
        "haiku_task",
        LLMTask(model="claude-haiku-4.5", input_tokens=5000, output_tokens=2000),
        depends_on=["gpt_task"],
    )

    # Execute with cost tracking
    tracker = CostTracker()

    engine = WorkflowEngine()
    print("Executing workflow...")
    result = engine.execute(workflow)

    # Manual cost tracking (in real use, would be integrated with engine)
    print()
    print("Simulating cost tracking for executed tasks...")
    for task_id in ["claude_task", "gpt_task", "haiku_task"]:
        if task_id == "claude_task":
            tracker.track_call("claude-opus-4", 2000, 1000)
        elif task_id == "gpt_task":
            tracker.track_call("gpt-4", 1000, 500)
        else:
            tracker.track_call("claude-haiku-4.5", 5000, 2000)

    print()
    print("Workflow Execution Results:")
    print(f"  Success: {result.success}")
    print(f"  Duration: {result.duration:.2f}s")
    print(f"  Tasks: {len(result.task_results)}")

    print()
    print("Cost Analysis:")
    summary = tracker.get_summary()
    print(f"  Total Cost: ${summary['total_cost_usd']:.4f}")
    print(f"  Calls: {summary['total_calls']}")
    print(f"  Tokens: {summary['total_tokens']['total']:,}")

    print()


def main():
    """Run all examples."""
    print()
    print("*" * 70)
    print("COST TRACKING EXAMPLES")
    print("*" * 70)
    print()

    example_1_basic_cost_tracking()
    print()

    example_2_cost_breakdown()
    print()

    example_3_cost_recommendations()
    print()

    example_4_supported_models()
    print()

    example_5_workflow_cost_tracking()

    print()
    print("*" * 70)
    print("Examples Complete!")
    print("*" * 70)
    print()


if __name__ == "__main__":
    main()
