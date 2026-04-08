"""Workflow state management for persistence and resumption."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


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
        """
        Save state to JSON file.

        Args:
            path: File path to save state to

        Raises:
            IOError: If write fails
        """
        file_path = Path(path).resolve()

        # Create parent directory if needed
        file_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(file_path, "w") as f:
                json.dump(self.to_dict(), f, indent=2)
            logger.debug(f"Workflow state saved to {file_path}")
        except IOError as e:
            logger.error(f"Failed to save workflow state to {file_path}: {e}")
            raise

    @classmethod
    def load_from_file(cls, path: str) -> "WorkflowState":
        """
        Load state from JSON file with validation.

        Args:
            path: File path to load state from

        Returns:
            WorkflowState object loaded from file

        Raises:
            ValueError: If JSON schema is invalid
            IOError: If read fails
        """
        file_path = Path(path).resolve()

        try:
            with open(file_path, "r") as f:
                data = json.load(f)
        except IOError as e:
            logger.error(f"Failed to load workflow state from {file_path}: {e}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in state file {file_path}: {e}")
            raise ValueError(f"Invalid JSON format in state file: {e}")

        # Validate required fields
        required_fields = {"workflow_name", "started_at", "task_results", "task_status"}
        if not isinstance(data, dict):
            raise ValueError("State file must contain a JSON object")

        missing_fields = required_fields - set(data.keys())
        if missing_fields:
            logger.error(f"Missing required fields in state file: {missing_fields}")
            raise ValueError(f"State file missing required fields: {missing_fields}")

        try:
            state = cls.from_dict(data)
            logger.debug(f"Workflow state loaded from {file_path}")
            return state
        except (KeyError, TypeError) as e:
            logger.error(f"Error deserializing state file {file_path}: {e}")
            raise ValueError(f"Invalid state file format: {e}")
