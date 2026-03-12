#!/usr/bin/env python
"""
Basic workflow example.

Demonstrates how to create and execute a simple workflow with tasks.

Requirements: pip install socratic-workflow
"""

from socratic_workflow import SimpleTask, Task, Workflow, WorkflowEngine


class ProcessDataTask(Task):
    """Custom task that processes data."""

    def execute(self, context):
        """Execute the task."""
        data = self.config.get("data", "default")
        return {"processed": f"Processed: {data}"}


class AnalyzeDataTask(Task):
    """Custom task that analyzes processed data."""

    def execute(self, context):
        """Execute the task."""
        processed = context.get("process", {}).get("processed", "")
        return {"analysis": f"Analysis of: {processed}"}


def main():
    """Run the basic workflow example."""
    print("=" * 60)
    print("BASIC WORKFLOW EXAMPLE")
    print("=" * 60)
    print()

    # Create workflow
    workflow = Workflow("Data Processing Pipeline", description="Process and analyze data")

    # Add tasks with dependencies
    workflow.add_task("input", SimpleTask(result={"data": "raw input"}))

    workflow.add_task("process", ProcessDataTask(data="input data"), depends_on=["input"])

    workflow.add_task("analyze", AnalyzeDataTask(), depends_on=["process"])

    print(f"Workflow: {workflow.name}")
    print(f"Tasks: {workflow.list_tasks()}")
    print()

    # Execute workflow
    print("Executing workflow...")
    engine = WorkflowEngine()
    result = engine.execute(workflow)

    print()
    print("=" * 60)
    print("EXECUTION RESULTS")
    print("=" * 60)
    print(f"Success: {result.success}")
    print(f"Duration: {result.duration:.2f}s")
    print(f"Tasks executed: {len(result.task_results)}")
    print()

    print("Task Results:")
    for task_id, task_result in result.task_results.items():
        print(f"  {task_id}: {task_result}")

    if result.errors:
        print()
        print("Errors:")
        for task_id, error in result.errors.items():
            print(f"  {task_id}: {error}")

    print()
    print("=" * 60)


if __name__ == "__main__":
    main()
