"""Core workflow execution engine."""

import logging
import time
from typing import Any, Dict, Optional

from .definition import Workflow
from .state import WorkflowState


class WorkflowResult:
    """Result of workflow execution."""

    def __init__(self):
        """Initialize workflow result."""
        self.success: bool = False
        self.duration: float = 0.0
        self.task_results: Dict[str, Any] = {}
        self.errors: Dict[str, str] = {}
        self.metrics: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "success": self.success,
            "duration": self.duration,
            "task_results": self.task_results,
            "errors": self.errors,
            "metrics": self.metrics,
        }


class WorkflowEngine:
    """
    Core workflow execution engine.

    Orchestrates task execution, manages state, handles errors.
    """

    def __init__(self, llm_client: Optional[Any] = None):
        """
        Initialize workflow engine.

        Args:
            llm_client: Optional LLMClient from Socrates Nexus
        """
        self.llm_client = llm_client
        self.logger = logging.getLogger(__name__)
        self.state: Optional[WorkflowState] = None

    def execute(self, workflow: Workflow) -> WorkflowResult:
        """
        Execute workflow synchronously.

        Args:
            workflow: Workflow to execute

        Returns:
            WorkflowResult with execution details
        """
        self.state = WorkflowState(workflow.name)
        result = WorkflowResult()

        start_time = time.perf_counter()

        try:
            # Initialize all tasks as pending
            for task_id in workflow.list_tasks():
                self.state.mark_task_pending(task_id)

            # Execute tasks sequentially
            for task_id in workflow.list_tasks():
                task = workflow.get_task(task_id)
                if task is None:
                    continue

                try:
                    self.state.mark_task_started(task_id)
                    context = self.state.get_context()

                    task.result = task.execute(context)
                    task.success = True

                    self.state.mark_task_completed(task_id, task.result)
                    self.logger.info(f"Task '{task_id}' completed successfully")

                except Exception as e:
                    error_msg = str(e)
                    task.error = error_msg
                    task.success = False
                    self.state.mark_task_failed(task_id, error_msg)
                    self.logger.error(f"Task '{task_id}' failed: {error_msg}")

            self.state.mark_completed()
            result.success = not self.state.has_errors()
            result.task_results = self.state.task_results.copy()
            result.errors = self.state.execution_errors.copy()

        except Exception as e:
            self.logger.error(f"Workflow execution failed: {e}")
            result.success = False
            result.errors["_workflow"] = str(e)

        finally:
            end_time = time.perf_counter()
            result.duration = end_time - start_time

        return result

    async def execute_async(self, workflow: Workflow) -> WorkflowResult:
        """
        Execute workflow asynchronously.

        Currently executes sequentially using async/await.
        Parallel execution support coming in Phase 3.

        Args:
            workflow: Workflow to execute

        Returns:
            WorkflowResult with execution details
        """
        self.state = WorkflowState(workflow.name)
        result = WorkflowResult()

        start_time = time.perf_counter()

        try:
            # Initialize all tasks as pending
            for task_id in workflow.list_tasks():
                self.state.mark_task_pending(task_id)

            # Execute tasks asynchronously
            for task_id in workflow.list_tasks():
                task = workflow.get_task(task_id)
                if task is None:
                    continue

                try:
                    self.state.mark_task_started(task_id)
                    context = self.state.get_context()

                    task.result = await task.execute_async(context)
                    task.success = True

                    self.state.mark_task_completed(task_id, task.result)
                    self.logger.info(f"Task '{task_id}' completed successfully")

                except Exception as e:
                    error_msg = str(e)
                    task.error = error_msg
                    task.success = False
                    self.state.mark_task_failed(task_id, error_msg)
                    self.logger.error(f"Task '{task_id}' failed: {error_msg}")

            self.state.mark_completed()
            result.success = not self.state.has_errors()
            result.task_results = self.state.task_results.copy()
            result.errors = self.state.execution_errors.copy()

        except Exception as e:
            self.logger.error(f"Workflow execution failed: {e}")
            result.success = False
            result.errors["_workflow"] = str(e)

        finally:
            end_time = time.perf_counter()
            result.duration = end_time - start_time

        return result

    def save_state(self, path: str) -> None:
        """Save workflow state to file for resumption."""
        if self.state is None:
            raise RuntimeError("No active workflow state to save")
        self.state.save_to_file(path)
        self.logger.info(f"Workflow state saved to {path}")

    def load_state(self, path: str) -> None:
        """Load workflow state from file."""
        self.state = WorkflowState.load_from_file(path)
        self.logger.info(f"Workflow state loaded from {path}")
