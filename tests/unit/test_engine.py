"""Tests for WorkflowEngine."""


import pytest

from socratic_workflow import SimpleTask, Task, Workflow, WorkflowEngine


class DummyTask(Task):
    """Simple task for testing."""

    def execute(self, context):
        """Execute dummy task."""
        return {"result": "done"}


class FailingTask(Task):
    """Task that fails."""

    def execute(self, context):
        """Raise an error."""
        raise ValueError("Task failed intentionally")


class ContextTask(Task):
    """Task that uses context."""

    def execute(self, context):
        """Return context info."""
        return {"context_keys": list(context.keys())}


class TestWorkflowEngine:
    """Test WorkflowEngine."""

    def test_engine_creation(self):
        """Test engine can be created."""
        engine = WorkflowEngine()
        assert engine is not None
        assert engine.llm_client is None

    def test_engine_with_llm_client(self):
        """Test engine can accept LLM client."""
        mock_client = object()
        engine = WorkflowEngine(llm_client=mock_client)
        assert engine.llm_client is mock_client

    def test_simple_workflow_execution(self):
        """Test execution of simple workflow."""
        workflow = Workflow("Test")
        workflow.add_task("task1", DummyTask())

        engine = WorkflowEngine()
        result = engine.execute(workflow)

        assert result.success is True
        assert result.duration > 0
        assert "task1" in result.task_results
        assert result.task_results["task1"]["result"] == "done"
        assert len(result.errors) == 0

    def test_workflow_with_multiple_tasks(self):
        """Test execution of workflow with multiple tasks."""
        workflow = Workflow("Multi-Task")
        workflow.add_task("task1", DummyTask())
        workflow.add_task("task2", DummyTask())
        workflow.add_task("task3", DummyTask())

        engine = WorkflowEngine()
        result = engine.execute(workflow)

        assert result.success is True
        assert len(result.task_results) == 3
        assert "task1" in result.task_results
        assert "task2" in result.task_results
        assert "task3" in result.task_results

    def test_workflow_with_dependencies(self):
        """Test workflow respects task dependencies."""
        workflow = Workflow("Dependencies")
        workflow.add_task("task1", DummyTask())
        workflow.add_task("task2", ContextTask(), depends_on=["task1"])
        workflow.add_task("task3", ContextTask(), depends_on=["task2"])

        engine = WorkflowEngine()
        result = engine.execute(workflow)

        assert result.success is True
        # task2 should have task1 in context
        assert "task1" in result.task_results["task2"]["context_keys"]
        # task3 should have task1 and task2 in context
        assert "task1" in result.task_results["task3"]["context_keys"]
        assert "task2" in result.task_results["task3"]["context_keys"]

    def test_task_failure_handling(self):
        """Test engine handles task failures."""
        workflow = Workflow("Failure")
        workflow.add_task("task1", FailingTask())

        engine = WorkflowEngine()
        result = engine.execute(workflow)

        assert result.success is False
        assert "task1" in result.errors
        assert "Task failed intentionally" in result.errors["task1"]

    def test_partial_failure(self):
        """Test workflow continues after partial failures."""
        workflow = Workflow("Partial")
        workflow.add_task("task1", DummyTask())
        workflow.add_task("task2", FailingTask())
        workflow.add_task("task3", DummyTask())

        engine = WorkflowEngine()
        result = engine.execute(workflow)

        assert result.success is False
        assert "task1" in result.task_results
        assert "task3" in result.task_results
        assert "task2" in result.errors

    def test_simple_task(self):
        """Test SimpleTask convenience class."""
        task = SimpleTask(result={"value": 42})
        result = task.execute({})
        assert result == {"value": 42}

    def test_execution_duration_tracking(self):
        """Test execution duration is tracked."""
        workflow = Workflow("Duration")
        workflow.add_task("task1", DummyTask())

        engine = WorkflowEngine()
        result = engine.execute(workflow)

        assert result.duration >= 0
        assert isinstance(result.duration, float)

    def test_result_to_dict(self):
        """Test result can be converted to dict."""
        workflow = Workflow("Dict")
        workflow.add_task("task1", SimpleTask(result={"x": 1}))

        engine = WorkflowEngine()
        result = engine.execute(workflow)

        result_dict = result.to_dict()
        assert result_dict["success"] is True
        assert "duration" in result_dict
        assert "task_results" in result_dict
        assert "errors" in result_dict


class TestWorkflowEngineAsync:
    """Test async execution."""

    @pytest.mark.asyncio
    async def test_async_simple_execution(self):
        """Test async execution."""
        workflow = Workflow("Async")
        workflow.add_task("task1", DummyTask())

        engine = WorkflowEngine()
        result = await engine.execute_async(workflow)

        assert result.success is True
        assert "task1" in result.task_results

    @pytest.mark.asyncio
    async def test_async_multiple_tasks(self):
        """Test async execution with multiple tasks."""
        workflow = Workflow("AsyncMulti")
        workflow.add_task("task1", DummyTask())
        workflow.add_task("task2", DummyTask())
        workflow.add_task("task3", DummyTask())

        engine = WorkflowEngine()
        result = await engine.execute_async(workflow)

        assert result.success is True
        assert len(result.task_results) == 3

    @pytest.mark.asyncio
    async def test_async_with_dependencies(self):
        """Test async execution respects dependencies."""
        workflow = Workflow("AsyncDeps")
        workflow.add_task("task1", DummyTask())
        workflow.add_task("task2", ContextTask(), depends_on=["task1"])

        engine = WorkflowEngine()
        result = await engine.execute_async(workflow)

        assert result.success is True
        assert "task1" in result.task_results["task2"]["context_keys"]

    @pytest.mark.asyncio
    async def test_async_failure_handling(self):
        """Test async handles failures."""
        workflow = Workflow("AsyncFail")
        workflow.add_task("task1", FailingTask())

        engine = WorkflowEngine()
        result = await engine.execute_async(workflow)

        assert result.success is False
        assert "task1" in result.errors
