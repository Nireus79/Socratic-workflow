"""Workflow definition using builder pattern."""

from typing import Any, Dict, List, Optional

from .task import Task


class Workflow:
    """
    Workflow definition with builder pattern.

    Define tasks and their dependencies, then execute through WorkflowEngine.

    Example:
        workflow = Workflow("AI Pipeline")
            .add_task("generate", GenerateTask())
            .add_task("validate", ValidateTask(), depends_on=["generate"])
            .add_task("analyze", AnalyzeTask(), depends_on=["validate"])
    """

    def __init__(self, name: str, description: str = ""):
        """
        Initialize a workflow.

        Args:
            name: Workflow name
            description: Optional workflow description
        """
        self.name = name
        self.description = description
        self.tasks: Dict[str, Task] = {}
        self.dependencies: Dict[str, List[str]] = {}

    def add_task(
        self, task_id: str, task: Task, depends_on: Optional[List[str]] = None
    ) -> "Workflow":
        """
        Add a task to the workflow.

        Args:
            task_id: Unique task identifier
            task: Task instance to add
            depends_on: List of task IDs this task depends on

        Returns:
            Self for method chaining
        """
        if task_id in self.tasks:
            raise ValueError(f"Task '{task_id}' already exists in workflow")

        self.tasks[task_id] = task
        self.dependencies[task_id] = depends_on or []

        return self

    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID."""
        return self.tasks.get(task_id)

    def list_tasks(self) -> List[str]:
        """List all task IDs in order."""
        return list(self.tasks.keys())

    def get_dependencies(self, task_id: str) -> List[str]:
        """Get dependencies for a task."""
        return self.dependencies.get(task_id, [])

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize workflow to dictionary.

        Can be saved to JSON for persistence.
        """
        return {
            "name": self.name,
            "description": self.description,
            "tasks": {
                task_id: {
                    "type": task.__class__.__name__,
                    "config": task.config,
                    "depends_on": self.dependencies.get(task_id, []),
                }
                for task_id, task in self.tasks.items()
            },
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Workflow":
        """
        Deserialize workflow from dictionary.

        Note: This creates workflow structure but not Task instances.
        """
        workflow = cls(data["name"], data.get("description", ""))

        # Note: Task instances need to be created separately
        # This is a limitation of serialization - tasks are Python objects
        return workflow

    def __repr__(self) -> str:
        """String representation."""
        task_count = len(self.tasks)
        return f"Workflow(name='{self.name}', tasks={task_count})"
