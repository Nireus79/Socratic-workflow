"""Workflow state management for persistence and resumption."""

import json
from datetime import datetime
from typing import Any, Dict, Optional


class WorkflowState:
    """
    Manages workflow state for persistence and recovery.

    Saves task results and execution status to enable resuming interrupted workflows.
    """

    def __init__(self, workflow_name: str):
        """
        Initialize workflow state.

        Args:
            workflow_name: Name of the workflow
        """
        self.workflow_name = workflow_name
        self.started_at = datetime.now().isoformat()
        self.completed_at: Optional[str] = None
        self.task_results: Dict[str, Dict[str, Any]] = {}
        self.task_status: Dict[str, str] = {}  # pending, running, completed, failed
        self.execution_errors: Dict[str, str] = {}

    def mark_task_started(self, task_id: str) -> None:
        """Mark a task as started."""
        self.task_status[task_id] = "running"

    def mark_task_completed(self, task_id: str, result: Dict[str, Any]) -> None:
        """Mark a task as completed with its result."""
        self.task_status[task_id] = "completed"
        self.task_results[task_id] = result

    def mark_task_failed(self, task_id: str, error: str) -> None:
        """Mark a task as failed with error message."""
        self.task_status[task_id] = "failed"
        self.execution_errors[task_id] = error

    def mark_task_pending(self, task_id: str) -> None:
        """Mark a task as pending (not yet executed)."""
        self.task_status[task_id] = "pending"

    def get_task_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get result of a completed task."""
        return self.task_results.get(task_id)

    def get_task_status(self, task_id: str) -> str:
        """Get execution status of a task."""
        return self.task_status.get(task_id, "pending")

    def get_context(self) -> Dict[str, Any]:
        """
        Get execution context with all completed task results.

        This is passed to tasks so they can access results from dependencies.
        """
        return {
            task_id: result
            for task_id, result in self.task_results.items()
            if self.task_status.get(task_id) == "completed"
        }

    def mark_completed(self) -> None:
        """Mark workflow as completed."""
        self.completed_at = datetime.now().isoformat()

    def is_completed(self) -> bool:
        """Check if workflow execution completed."""
        return self.completed_at is not None

    def has_errors(self) -> bool:
        """Check if any tasks failed."""
        return len(self.execution_errors) > 0

    def to_dict(self) -> Dict[str, Any]:
        """Serialize state to dictionary for JSON storage."""
        return {
            "workflow_name": self.workflow_name,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "task_results": self.task_results,
            "task_status": self.task_status,
            "execution_errors": self.execution_errors,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkflowState":
        """Deserialize state from dictionary (JSON)."""
        state = cls(data["workflow_name"])
        state.started_at = data["started_at"]
        state.completed_at = data.get("completed_at")
        state.task_results = data.get("task_results", {})
        state.task_status = data.get("task_status", {})
        state.execution_errors = data.get("execution_errors", {})
        return state

    def save_to_file(self, path: str) -> None:
        """Save state to JSON file."""
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load_from_file(cls, path: str) -> "WorkflowState":
        """Load state from JSON file."""
        with open(path, "r") as f:
            data = json.load(f)
        return cls.from_dict(data)
