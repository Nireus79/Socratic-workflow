"""Tests for Task base class."""

import pytest

from socratic_workflow import SimpleTask, Task


class CustomTask(Task):
    """Custom task for testing."""

    def execute(self, context):
        """Execute and return config."""
        return {"value": self.config.get("value", "default")}


class TestTask:
    """Test Task base class."""

    def test_task_creation(self):
        """Test task can be created."""
        task = CustomTask()
        assert task.name == "CustomTask"
        assert task.result is None
        assert task.error is None
        assert task.success is False

    def test_task_with_name(self):
        """Test task with custom name."""
        task = CustomTask(name="MyTask")
        assert task.name == "MyTask"

    def test_task_with_config(self):
        """Test task with configuration."""
        task = CustomTask(value="test_value")
        assert task.config["value"] == "test_value"

    def test_task_execute(self):
        """Test task execution."""
        task = CustomTask(value="test")
        result = task.execute({})
        assert result == {"value": "test"}

    def test_task_to_dict(self):
        """Test task serialization."""
        task = CustomTask(name="MyTask", value="test")
        data = task.to_dict()

        assert data["name"] == "MyTask"
        assert data["type"] == "CustomTask"
        assert data["config"]["value"] == "test"

    def test_simple_task(self):
        """Test SimpleTask convenience class."""
        task = SimpleTask(result={"x": 1, "y": 2})
        result = task.execute({})
        assert result == {"x": 1, "y": 2}

    def test_simple_task_with_name(self):
        """Test SimpleTask with name."""
        task = SimpleTask(name="Data", result={"value": 42})
        assert task.name == "Data"
        result = task.execute({})
        assert result == {"value": 42}

    def test_simple_task_no_result(self):
        """Test SimpleTask with no result."""
        task = SimpleTask()
        result = task.execute({})
        assert result == {}

    @pytest.mark.asyncio
    async def test_async_execute(self):
        """Test async execution."""
        task = CustomTask(value="async_test")
        result = await task.execute_async({})
        assert result == {"value": "async_test"}
