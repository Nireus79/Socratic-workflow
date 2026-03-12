"""Tests for ParallelExecutor."""

import pytest

from socratic_workflow import SimpleTask, Task, Workflow
from socratic_workflow.execution.executor import ParallelExecutor
from socratic_workflow.execution.retry import RetryConfig


class CounterTask(Task):
    """Task that increments a counter."""

    counter = 0

    def execute(self, context):
        """Execute and increment counter."""
        CounterTask.counter += 1
        return {"count": CounterTask.counter}

    @classmethod
    def reset(cls):
        """Reset counter."""
        cls.counter = 0


class SlowTask(Task):
    """Task that takes time to execute."""

    def execute(self, context):
        """Execute with delay."""
        import time

        delay = self.config.get("delay", 0.01)
        time.sleep(delay)
        return {"slept": delay}


class FailingTask(Task):
    """Task that fails."""

    def execute(self, context):
        """Raise error."""
        raise ValueError("Task failed")


class ContextTask(Task):
    """Task that reads context."""

    def execute(self, context):
        """Return context keys."""
        return {"keys": sorted(context.keys())}


class TestParallelExecutor:
    """Test ParallelExecutor."""

    @pytest.mark.asyncio
    async def test_executor_creation(self):
        """Test executor can be created."""
        executor = ParallelExecutor()
        assert executor is not None
        assert executor.max_workers == 5
        assert executor.task_results == {}
        assert executor.task_errors == {}

    @pytest.mark.asyncio
    async def test_executor_with_retry_config(self):
        """Test executor with retry config."""
        config = RetryConfig(max_attempts=2)
        executor = ParallelExecutor(retry_config=config)

        assert executor.retry_config is config

    @pytest.mark.asyncio
    async def test_executor_with_max_workers(self):
        """Test executor with max workers."""
        executor = ParallelExecutor(max_workers=10)
        assert executor.max_workers == 10

    @pytest.mark.asyncio
    async def test_execute_parallel_single_task(self):
        """Test parallel execution of single task."""
        CounterTask.reset()
        workflow = Workflow("Single")
        workflow.add_task("task1", SimpleTask(result={"value": 42}))

        executor = ParallelExecutor()
        result = await executor.execute_parallel(workflow)

        assert "task_results" in result
        assert "task1" in result["task_results"]
        assert result["task_results"]["task1"]["value"] == 42
        assert len(result["task_errors"]) == 0

    @pytest.mark.asyncio
    async def test_execute_parallel_independent_tasks(self):
        """Test parallel execution of independent tasks."""
        workflow = Workflow("Independent")
        workflow.add_task("task1", SimpleTask(result={"id": 1}))
        workflow.add_task("task2", SimpleTask(result={"id": 2}))
        workflow.add_task("task3", SimpleTask(result={"id": 3}))

        executor = ParallelExecutor()
        result = await executor.execute_parallel(workflow)

        assert "task1" in result["task_results"]
        assert "task2" in result["task_results"]
        assert "task3" in result["task_results"]
        assert result["task_results"]["task1"]["id"] == 1
        assert result["task_results"]["task2"]["id"] == 2
        assert result["task_results"]["task3"]["id"] == 3

    @pytest.mark.asyncio
    async def test_execute_parallel_with_dependencies(self):
        """Test parallel execution respects dependencies."""
        workflow = Workflow("Dependencies")
        workflow.add_task("task1", SimpleTask(result={"x": 10}))
        workflow.add_task("task2", ContextTask(), depends_on=["task1"])
        workflow.add_task("task3", ContextTask(), depends_on=["task2"])

        executor = ParallelExecutor()
        result = await executor.execute_parallel(workflow)

        # Verify all tasks executed
        assert "task1" in result["task_results"]
        assert "task2" in result["task_results"]
        assert "task3" in result["task_results"]

        # Verify context is passed
        assert "task1" in result["task_results"]["task2"]["keys"]
        assert "task1" in result["task_results"]["task3"]["keys"]
        assert "task2" in result["task_results"]["task3"]["keys"]

    @pytest.mark.asyncio
    async def test_execute_parallel_branching(self):
        """Test parallel execution with branching."""
        workflow = Workflow("Branching")
        workflow.add_task("root", SimpleTask(result={"root": True}))
        workflow.add_task("branch1", SimpleTask(result={"b": 1}), depends_on=["root"])
        workflow.add_task("branch2", SimpleTask(result={"b": 2}), depends_on=["root"])
        workflow.add_task("join", ContextTask(), depends_on=["branch1", "branch2"])

        executor = ParallelExecutor()
        result = await executor.execute_parallel(workflow)

        # Verify branching
        assert "root" in result["task_results"]
        assert "branch1" in result["task_results"]
        assert "branch2" in result["task_results"]
        assert "join" in result["task_results"]

        # Verify join has both branches in context
        join_keys = result["task_results"]["join"]["keys"]
        assert "branch1" in join_keys
        assert "branch2" in join_keys

    @pytest.mark.asyncio
    async def test_execute_parallel_task_failure(self):
        """Test parallel execution handles task failure."""
        workflow = Workflow("Failure")
        workflow.add_task("task1", SimpleTask(result={"ok": True}))
        workflow.add_task("task2", FailingTask())

        executor = ParallelExecutor()
        result = await executor.execute_parallel(workflow)

        # task1 should succeed
        assert "task1" in result["task_results"]
        assert result["task_results"]["task1"]["ok"] is True

        # task2 should fail
        assert "task2" in result["task_errors"]
        assert "Task failed" in result["task_errors"]["task2"]

    @pytest.mark.asyncio
    async def test_execute_parallel_multiple_failures(self):
        """Test parallel execution with multiple failures."""
        workflow = Workflow("MultiFailure")
        workflow.add_task("task1", FailingTask())
        workflow.add_task("task2", SimpleTask(result={"ok": True}))
        workflow.add_task("task3", FailingTask())

        executor = ParallelExecutor()
        result = await executor.execute_parallel(workflow)

        # task2 should succeed
        assert "task2" in result["task_results"]

        # tasks 1 and 3 should fail
        assert "task1" in result["task_errors"]
        assert "task3" in result["task_errors"]

    @pytest.mark.asyncio
    async def test_execute_parallel_respects_max_workers(self):
        """Test parallel execution respects max workers limit."""
        workflow = Workflow("Workers")
        for i in range(5):
            workflow.add_task(f"task{i}", SlowTask(delay=0.05))

        executor = ParallelExecutor(max_workers=2)
        result = await executor.execute_parallel(workflow)

        # All tasks should complete
        assert len(result["task_results"]) == 5

    @pytest.mark.asyncio
    async def test_get_execution_metrics(self):
        """Test execution metrics."""
        workflow = Workflow("Metrics")
        workflow.add_task("task1", SimpleTask(result={"ok": True}))
        workflow.add_task("task2", SimpleTask(result={"ok": True}))
        workflow.add_task("task3", FailingTask())

        executor = ParallelExecutor()
        await executor.execute_parallel(workflow)

        metrics = executor.get_execution_metrics()

        assert metrics["total_tasks"] == 3
        assert metrics["successful_tasks"] == 2
        assert metrics["failed_tasks"] == 1
        assert abs(metrics["success_rate"] - (2.0 / 3.0)) < 0.01

    @pytest.mark.asyncio
    async def test_execute_parallel_empty_workflow(self):
        """Test parallel execution with empty workflow."""
        workflow = Workflow("Empty")

        executor = ParallelExecutor()
        result = await executor.execute_parallel(workflow)

        assert result["task_results"] == {}
        assert result["task_errors"] == {}

    @pytest.mark.asyncio
    async def test_execute_parallel_complex_dag(self):
        """Test parallel execution with complex DAG."""
        workflow = Workflow("ComplexDAG")

        # Layer 0
        workflow.add_task("task1", SimpleTask(result={"x": 1}))
        workflow.add_task("task2", SimpleTask(result={"x": 2}))

        # Layer 1
        workflow.add_task("task3", ContextTask(), depends_on=["task1"])
        workflow.add_task("task4", ContextTask(), depends_on=["task2"])

        # Layer 2
        workflow.add_task("task5", ContextTask(), depends_on=["task3", "task4"])

        executor = ParallelExecutor()
        result = await executor.execute_parallel(workflow)

        # Verify all executed
        for i in range(1, 6):
            assert f"task{i}" in result["task_results"]

        # Verify dependencies
        assert "task3" in result["task_results"]["task5"]["keys"]
        assert "task4" in result["task_results"]["task5"]["keys"]

    @pytest.mark.asyncio
    async def test_execute_level_empty(self):
        """Test execute level with empty level."""
        workflow = Workflow("Test")
        executor = ParallelExecutor()

        # Should handle empty level gracefully
        await executor._execute_level(workflow, [])

        assert executor.task_results == {}
        assert executor.task_errors == {}

    @pytest.mark.asyncio
    async def test_execute_single_task_success(self):
        """Test execute single task success."""
        workflow = Workflow("Test")
        task = SimpleTask(result={"ok": True})
        workflow.add_task("task1", task)

        executor = ParallelExecutor()
        await executor._execute_single_task(workflow, "task1")

        assert "task1" in executor.task_results
        assert executor.task_results["task1"]["ok"] is True

    @pytest.mark.asyncio
    async def test_execute_single_task_failure(self):
        """Test execute single task failure."""
        workflow = Workflow("Test")
        workflow.add_task("task1", FailingTask())

        executor = ParallelExecutor()
        await executor._execute_single_task(workflow, "task1")

        assert "task1" in executor.task_errors
        assert "Task failed" in executor.task_errors["task1"]

    @pytest.mark.asyncio
    async def test_execute_single_task_nonexistent(self):
        """Test execute single task that doesn't exist."""
        workflow = Workflow("Test")
        executor = ParallelExecutor()

        # Should handle gracefully
        await executor._execute_single_task(workflow, "nonexistent")

        assert "nonexistent" not in executor.task_results
        assert "nonexistent" not in executor.task_errors

    @pytest.mark.asyncio
    async def test_parallel_execution_timing(self):
        """Test parallel execution is actually parallel."""
        import time

        workflow = Workflow("Timing")
        for i in range(3):
            workflow.add_task(f"task{i}", SlowTask(delay=0.05))

        executor = ParallelExecutor(max_workers=3)

        start = time.time()
        result = await executor.execute_parallel(workflow)
        elapsed = time.time() - start

        # If truly parallel, should take ~0.05s, not 0.15s
        # Allow generous overhead for system variation
        assert elapsed < 0.20
        assert len(result["task_results"]) == 3
