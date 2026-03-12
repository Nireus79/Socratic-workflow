"""Tests for WorkflowState."""

import json
import tempfile
from pathlib import Path

from socratic_workflow.workflow.state import WorkflowState


class TestWorkflowState:
    """Test WorkflowState class."""

    def test_state_creation(self):
        """Test state can be created."""
        state = WorkflowState("TestWorkflow")
        assert state.workflow_name == "TestWorkflow"
        assert state.started_at is not None
        assert state.completed_at is None
        assert len(state.task_results) == 0

    def test_mark_task_pending(self):
        """Test marking task as pending."""
        state = WorkflowState("Test")
        state.mark_task_pending("task1")
        assert state.get_task_status("task1") == "pending"

    def test_mark_task_started(self):
        """Test marking task as started."""
        state = WorkflowState("Test")
        state.mark_task_started("task1")
        assert state.get_task_status("task1") == "running"

    def test_mark_task_completed(self):
        """Test marking task as completed."""
        state = WorkflowState("Test")
        result = {"value": 42}
        state.mark_task_completed("task1", result)

        assert state.get_task_status("task1") == "completed"
        assert state.get_task_result("task1") == result

    def test_mark_task_failed(self):
        """Test marking task as failed."""
        state = WorkflowState("Test")
        state.mark_task_failed("task1", "Error message")

        assert state.get_task_status("task1") == "failed"
        assert state.execution_errors["task1"] == "Error message"
        assert state.has_errors() is True

    def test_get_context(self):
        """Test getting execution context."""
        state = WorkflowState("Test")
        state.mark_task_completed("task1", {"value": 1})
        state.mark_task_started("task2")
        state.mark_task_failed("task3", "failed")

        context = state.get_context()

        # Should only include completed tasks
        assert "task1" in context
        assert "task2" not in context
        assert "task3" not in context
        assert context["task1"]["value"] == 1

    def test_mark_completed(self):
        """Test marking workflow as completed."""
        state = WorkflowState("Test")
        assert state.is_completed() is False

        state.mark_completed()
        assert state.is_completed() is True
        assert state.completed_at is not None

    def test_no_errors_initially(self):
        """Test no errors initially."""
        state = WorkflowState("Test")
        assert state.has_errors() is False

    def test_state_to_dict(self):
        """Test state serialization."""
        state = WorkflowState("Test")
        state.mark_task_completed("task1", {"value": 1})
        state.mark_task_failed("task2", "error")

        data = state.to_dict()

        assert data["workflow_name"] == "Test"
        assert "task1" in data["task_results"]
        assert data["task_results"]["task1"]["value"] == 1
        assert "task2" in data["execution_errors"]

    def test_state_from_dict(self):
        """Test state deserialization."""
        original = WorkflowState("Test")
        original.mark_task_completed("task1", {"value": 1})
        original.mark_task_failed("task2", "error")

        data = original.to_dict()
        restored = WorkflowState.from_dict(data)

        assert restored.workflow_name == original.workflow_name
        assert restored.get_task_result("task1") == original.get_task_result("task1")
        assert restored.execution_errors == original.execution_errors

    def test_state_save_and_load_file(self):
        """Test saving and loading state from file."""
        state = WorkflowState("Test")
        state.mark_task_completed("task1", {"value": 42})
        state.mark_task_failed("task2", "failed")

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "state.json"

            # Save
            state.save_to_file(str(path))
            assert path.exists()

            # Verify JSON format
            with open(path) as f:
                data = json.load(f)
            assert data["workflow_name"] == "Test"

            # Load
            loaded = WorkflowState.load_from_file(str(path))
            assert loaded.workflow_name == state.workflow_name
            assert loaded.get_task_result("task1") == state.get_task_result("task1")

    def test_state_get_nonexistent_result(self):
        """Test getting nonexistent task result."""
        state = WorkflowState("Test")
        assert state.get_task_result("nonexistent") is None

    def test_state_get_nonexistent_status(self):
        """Test getting nonexistent task status."""
        state = WorkflowState("Test")
        assert state.get_task_status("nonexistent") == "pending"

    def test_multiple_task_tracking(self):
        """Test tracking multiple tasks."""
        state = WorkflowState("Test")

        # Add various tasks
        state.mark_task_pending("task1")
        state.mark_task_completed("task2", {"result": "ok"})
        state.mark_task_failed("task3", "error")
        state.mark_task_started("task4")

        # Verify all tracked
        context = state.get_context()
        assert len(context) == 1
        assert "task2" in context
        assert state.has_errors() is True
