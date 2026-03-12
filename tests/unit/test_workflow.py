"""Tests for Workflow definition."""

import pytest

from socratic_workflow import SimpleTask, Workflow


class TestWorkflow:
    """Test Workflow class."""

    def test_workflow_creation(self):
        """Test workflow can be created."""
        workflow = Workflow("Test")
        assert workflow.name == "Test"
        assert workflow.description == ""

    def test_workflow_with_description(self):
        """Test workflow with description."""
        workflow = Workflow("Test", description="Test description")
        assert workflow.name == "Test"
        assert workflow.description == "Test description"

    def test_add_task(self):
        """Test adding task to workflow."""
        workflow = Workflow("Test")
        task = SimpleTask()

        workflow.add_task("task1", task)

        assert "task1" in workflow.tasks
        assert workflow.get_task("task1") is task

    def test_add_multiple_tasks(self):
        """Test adding multiple tasks."""
        workflow = Workflow("Test")

        workflow.add_task("task1", SimpleTask())
        workflow.add_task("task2", SimpleTask())
        workflow.add_task("task3", SimpleTask())

        assert len(workflow.tasks) == 3
        assert workflow.list_tasks() == ["task1", "task2", "task3"]

    def test_duplicate_task_error(self):
        """Test error on duplicate task ID."""
        workflow = Workflow("Test")
        workflow.add_task("task1", SimpleTask())

        with pytest.raises(ValueError, match="already exists"):
            workflow.add_task("task1", SimpleTask())

    def test_task_dependencies(self):
        """Test task dependencies."""
        workflow = Workflow("Test")
        workflow.add_task("task1", SimpleTask())
        workflow.add_task("task2", SimpleTask(), depends_on=["task1"])
        workflow.add_task("task3", SimpleTask(), depends_on=["task1", "task2"])

        assert workflow.get_dependencies("task1") == []
        assert workflow.get_dependencies("task2") == ["task1"]
        assert workflow.get_dependencies("task3") == ["task1", "task2"]

    def test_builder_pattern(self):
        """Test builder pattern chaining."""
        workflow = (
            Workflow("Test")
            .add_task("task1", SimpleTask())
            .add_task("task2", SimpleTask(), depends_on=["task1"])
            .add_task("task3", SimpleTask(), depends_on=["task2"])
        )

        assert len(workflow.tasks) == 3

    def test_workflow_to_dict(self):
        """Test workflow serialization."""
        workflow = Workflow("Test", description="Test workflow")
        workflow.add_task("task1", SimpleTask())
        workflow.add_task("task2", SimpleTask(), depends_on=["task1"])

        data = workflow.to_dict()

        assert data["name"] == "Test"
        assert data["description"] == "Test workflow"
        assert "task1" in data["tasks"]
        assert "task2" in data["tasks"]
        assert data["tasks"]["task1"]["depends_on"] == []
        assert data["tasks"]["task2"]["depends_on"] == ["task1"]

    def test_workflow_get_nonexistent_task(self):
        """Test getting nonexistent task returns None."""
        workflow = Workflow("Test")
        assert workflow.get_task("nonexistent") is None

    def test_workflow_repr(self):
        """Test workflow string representation."""
        workflow = Workflow("Test")
        workflow.add_task("task1", SimpleTask())
        workflow.add_task("task2", SimpleTask())

        repr_str = repr(workflow)
        assert "Test" in repr_str
        assert "tasks=2" in repr_str
