# Socratic Workflow - FAQ by Scenario

## Simple Workflow

How do I create a basic workflow?

```python
from socratic_workflow import Workflow, SimpleTask, WorkflowEngine

workflow = Workflow("My Pipeline")
workflow.add_task("task1", SimpleTask(result={"status": "ok"}))
workflow.add_task("task2", SimpleTask(), depends_on=["task1"])

engine = WorkflowEngine()
result = engine.execute(workflow)
```

## Cost Tracking

How do I track LLM costs?

```python
from socratic_workflow import CostTracker

tracker = CostTracker()
cost = tracker.track_call("claude-opus", 1000, 500)
summary = tracker.get_summary()
```

## Parallel Execution

How do I run tasks in parallel?

```python
workflow = Workflow("Parallel")
workflow.add_task("task1", MyTask())
workflow.add_task("task2", MyTask())  # Runs in parallel
workflow.add_task("task3", MyTask(), depends_on=["task1", "task2"])
```

## Async Execution

How do I use async?

```python
result = await engine.execute_async(workflow)
```

## Error Recovery

Handle errors in tasks:

```python
class RetryableTask(Task):
    def execute(self, context):
        for attempt in range(3):
            try:
                return perform_operation()
            except Exception:
                if attempt == 2:
                    raise
```
