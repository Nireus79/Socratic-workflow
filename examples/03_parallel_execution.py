#!/usr/bin/env python
"""
Parallel task execution example.

Demonstrates how to run independent tasks in parallel using the ParallelExecutor.
Shows how dependencies are respected and how independent tasks run concurrently.

Requirements: pip install socratic-workflow
"""

import asyncio

from socratic_workflow import SimpleTask, Task, Workflow
from socratic_workflow.execution.executor import ParallelExecutor


class DataProcessingTask(Task):
    """Task that processes data."""

    def execute(self, context):
        """Process data and return result."""
        item_id = self.config.get("item_id", "unknown")
        result = {"item_id": item_id, "processed": True, "value": item_id * 10}
        return result


class AggregationTask(Task):
    """Task that aggregates results from other tasks."""

    def execute(self, context):
        """Aggregate results from previous tasks."""
        # All previous task results are in context
        values = [
            result.get("value", 0)
            for result in context.values()
            if isinstance(result, dict) and "value" in result
        ]
        return {
            "sum": sum(values),
            "count": len(values),
            "average": sum(values) / len(values) if values else 0,
        }


def example_1_independent_parallel():
    """Example 1: Run independent tasks in parallel."""
    print("=" * 70)
    print("EXAMPLE 1: Independent Parallel Tasks")
    print("=" * 70)
    print()

    # Create workflow with independent tasks
    workflow = Workflow("Parallel Data Processing")
    workflow.add_task("process_item_1", DataProcessingTask(item_id=5))
    workflow.add_task("process_item_2", DataProcessingTask(item_id=10))
    workflow.add_task("process_item_3", DataProcessingTask(item_id=15))

    print("Tasks to execute (all independent, can run in parallel):")
    print("  - process_item_1: Process item 5")
    print("  - process_item_2: Process item 10")
    print("  - process_item_3: Process item 15")
    print()

    print("Executing in parallel...")
    executor = ParallelExecutor(max_workers=3)
    result = asyncio.run(executor.execute_parallel(workflow))

    print()
    print("Results:")
    for task_id, task_result in result["task_results"].items():
        print(f"  {task_id}: item_id={task_result['item_id']}, value={task_result['value']}")

    metrics = executor.get_execution_metrics()
    print()
    print("Execution metrics:")
    print(f"  Total tasks: {metrics['total_tasks']}")
    print(f"  Successful: {metrics['successful_tasks']}")
    print(f"  Success rate: {metrics['success_rate']:.1%}")
    print()


def example_2_branching_parallelization():
    """Example 2: Branching workflow with parallelization."""
    print("=" * 70)
    print("EXAMPLE 2: Branching Workflow with Parallelization")
    print("=" * 70)
    print()

    # Create workflow with branching
    workflow = Workflow("Branch and Process")

    # Initial task
    workflow.add_task("load_data", SimpleTask(result={"data": "loaded"}))

    # Three parallel processing branches
    workflow.add_task("process_a", DataProcessingTask(item_id=1), depends_on=["load_data"])
    workflow.add_task("process_b", DataProcessingTask(item_id=2), depends_on=["load_data"])
    workflow.add_task("process_c", DataProcessingTask(item_id=3), depends_on=["load_data"])

    # Aggregation (joins all branches)
    workflow.add_task(
        "aggregate",
        AggregationTask(),
        depends_on=["process_a", "process_b", "process_c"],
    )

    print("Workflow structure:")
    print("  1. load_data")
    print("     |")
    print("     +---> process_a")
    print("     |     |")
    print("     +---> process_b  --> aggregate")
    print("     |     |")
    print("     +---> process_c")
    print()

    print("Executing workflow...")
    executor = ParallelExecutor(max_workers=3)
    result = asyncio.run(executor.execute_parallel(workflow))

    print()
    print("Results:")
    print(f"  load_data: {result['task_results']['load_data']}")
    print(f"  process_a: {result['task_results']['process_a']['value']}")
    print(f"  process_b: {result['task_results']['process_b']['value']}")
    print(f"  process_c: {result['task_results']['process_c']['value']}")

    agg = result["task_results"]["aggregate"]
    print("  aggregate:")
    print(f"    - sum: {agg['sum']}")
    print(f"    - count: {agg['count']}")
    print(f"    - average: {agg['average']:.1f}")
    print()


def example_3_complex_dag():
    """Example 3: Complex dependency DAG."""
    print("=" * 70)
    print("EXAMPLE 3: Complex DAG with Multiple Parallelization Levels")
    print("=" * 70)
    print()

    # Create workflow with multiple parallelization levels
    workflow = Workflow("Complex DAG")

    # Level 0: Initial task
    workflow.add_task("start", SimpleTask(result={"phase": 0}))

    # Level 1: Three parallel branches
    workflow.add_task("fetch_data_a", DataProcessingTask(item_id=1), depends_on=["start"])
    workflow.add_task("fetch_data_b", DataProcessingTask(item_id=2), depends_on=["start"])
    workflow.add_task("fetch_data_c", DataProcessingTask(item_id=3), depends_on=["start"])

    # Level 2: Processing (some dependent on previous level)
    workflow.add_task(
        "process_ab", DataProcessingTask(item_id=10), depends_on=["fetch_data_a", "fetch_data_b"]
    )
    workflow.add_task("process_c", DataProcessingTask(item_id=20), depends_on=["fetch_data_c"])

    # Level 3: Final aggregation
    workflow.add_task(
        "finalize",
        AggregationTask(),
        depends_on=["process_ab", "process_c"],
    )

    print("Workflow structure (showing parallelization levels):")
    print("  Level 0: start")
    print("           |")
    print("  Level 1: fetch_data_a  fetch_data_b  fetch_data_c")
    print("           |               |             |")
    print("  Level 2: process_ab ----/             process_c")
    print("           |                             |")
    print("  Level 3: finalize <-------------------/")
    print()

    print("Executing complex DAG...")
    executor = ParallelExecutor(max_workers=3)
    result = asyncio.run(executor.execute_parallel(workflow))

    print()
    print("Results:")
    for task_id in [
        "start",
        "fetch_data_a",
        "fetch_data_b",
        "fetch_data_c",
        "process_ab",
        "process_c",
        "finalize",
    ]:
        if task_id in result["task_results"]:
            res = result["task_results"][task_id]
            print(f"  {task_id}: {res}")

    print()


def example_4_max_workers_limiting():
    """Example 4: Limiting concurrent workers."""
    print("=" * 70)
    print("EXAMPLE 4: Limiting Concurrent Workers")
    print("=" * 70)
    print()

    # Create workflow with many independent tasks
    workflow = Workflow("Many Tasks")
    for i in range(10):
        workflow.add_task(f"task_{i:02d}", DataProcessingTask(item_id=i + 1))

    print("Created workflow with 10 independent tasks")
    print()

    print("Scenario A: max_workers=1 (sequential)")
    executor = ParallelExecutor(max_workers=1)
    asyncio.run(executor.execute_parallel(workflow))
    metrics = executor.get_execution_metrics()
    print(f"  Executed: {metrics['successful_tasks']} tasks")
    print()

    print("Scenario B: max_workers=3 (limited parallelism)")
    executor = ParallelExecutor(max_workers=3)
    asyncio.run(executor.execute_parallel(workflow))
    metrics = executor.get_execution_metrics()
    print(f"  Executed: {metrics['successful_tasks']} tasks")
    print("  This allows at most 3 tasks to run concurrently")
    print()

    print("Scenario C: max_workers=10 (full parallelism)")
    executor = ParallelExecutor(max_workers=10)
    asyncio.run(executor.execute_parallel(workflow))
    metrics = executor.get_execution_metrics()
    print(f"  Executed: {metrics['successful_tasks']} tasks")
    print("  All 10 tasks can run concurrently")
    print()


def main():
    """Run all examples."""
    print()
    print("*" * 70)
    print("PARALLEL EXECUTION EXAMPLES")
    print("*" * 70)
    print()

    example_1_independent_parallel()
    print()

    example_2_branching_parallelization()
    print()

    example_3_complex_dag()
    print()

    example_4_max_workers_limiting()

    print()
    print("*" * 70)
    print("Examples Complete!")
    print("*" * 70)
    print()


if __name__ == "__main__":
    main()
