"""Base Task class for workflow tasks."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class Task(ABC):
    """
    Abstract base class for workflow tasks.

    All tasks must inherit from this class and implement the execute method.
    """

    def __init__(self, name: Optional[str] = None, **kwargs: Any) -> None:
        """
        Initialize a task.

        Args:
            name: Optional task name (defaults to class name)
            **kwargs: Additional configuration parameters
        """
        self.name = name or self.__class__.__name__
        self.config = kwargs
        self.result: Optional[Dict[str, Any]] = None
        self.error: Optional[str] = None
        self.duration: float = 0.0
        self.success: bool = False

    @abstractmethod
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the task.

        Args:
            context: Results from previous tasks in workflow

        Returns:
            Dictionary with task results
        """
        pass

    async def execute_async(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the task asynchronously.

        Default implementation calls sync execute. Override for true async.

        Args:
            context: Results from previous tasks in workflow

        Returns:
            Dictionary with task results
        """
        return self.execute(context)

    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary for serialization."""
        return {
            "name": self.name,
            "type": self.__class__.__name__,
            "config": self.config,
        }


class SimpleTask(Task):
    """Simple task that returns a static result."""

    def __init__(self, name: Optional[str] = None, result: Optional[Dict] = None, **kwargs):
        """
        Initialize a simple task.

        Args:
            name: Task name
            result: Result to return when executed
            **kwargs: Additional config
        """
        super().__init__(name=name, **kwargs)
        self._result = result or {}

    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Return the predefined result."""
        return self._result
