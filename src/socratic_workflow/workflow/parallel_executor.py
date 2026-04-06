"""Parallel workflow execution engine supporting dependency-aware task scheduling."""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Set

from .definition import Workflow
from .engine import WorkflowResult
from .state import WorkflowState

logger = logging.getLogger(__name__)


class ParallelWorkflowExecutor:
    """
    Executes workflow tasks in parallel while respecting dependencies.

    Features:
    - Analyzes task dependency graph
    - Executes independent tasks concurrently
    - Respects task dependencies
    - Configurable concurrency limits
    - Error handling with graceful degradation
    """

    def __init__(self, max_concurrent: int = 5):
        """
        Initialize parallel executor.

        Args:
            max_concurrent: Maximum tasks to execute in parallel (default: 5)
        """
        if max_concurrent <= 0:
            raise ValueError("max_concurrent must be positive")
        self.max_concurrent = max_concurrent
        self.logger = logging.getLogger(__name__)

    def _get_ready_tasks(
        self,
        workflow: Workflow,
        completed: Set[str],
        pending: Set[str],
    ) -> List[str]:
        """
        Get tasks that are ready to execute.

        A task is ready if all its dependencies are completed.

        Args:
            workflow: Workflow definition
            completed: Set of completed task IDs
            pending: Set of pending task IDs

        Returns:
            List of task IDs ready to execute
        """
        ready = []

        for task_id in pending:
            dependencies = workflow.get_dependencies(task_id)

            # Check if all dependencies are completed
            if all(dep_id in completed for dep_id in dependencies):
                ready.append(task_id)

        return ready

    async def execute_parallel(self, workflow: Workflow, state: WorkflowState) -> WorkflowResult:
        """
        Execute workflow with parallel task execution.

        Respects task dependencies while maximizing parallelism.

        Args:
            workflow: Workflow to execute
            state: Workflow state tracker

        Returns:
            WorkflowResult with execution details

        Notes:
            - Tasks without dependencies execute immediately
            - Tasks wait for all dependencies before starting
            - Concurrency limited by max_concurrent parameter
            - Errors in one task don't block other independent tasks
        """
        result = WorkflowResult()
        completed: Set[str] = set()
        failed: Set[str] = set()
        pending: Set[str] = set(workflow.list_tasks())

        # Track running tasks
        running_tasks: Dict[str, asyncio.Task] = {}

        try:
            while pending or running_tasks:
                # Get tasks ready to execute
                ready_tasks = self._get_ready_tasks(workflow, completed, pending)

                # Launch new tasks up to concurrency limit
                while ready_tasks and len(running_tasks) < self.max_concurrent:
                    task_id = ready_tasks.pop(0)
                    pending.remove(task_id)

                    task = workflow.get_task(task_id)
                    if task is None:
                        self.logger.warning(f"Task '{task_id}' not found in workflow")
                        continue

                    state.mark_task_started(task_id)
                    context = state.get_context()

                    # Create async task
                    async_task = asyncio.create_task(
                        self._execute_task_async(task_id, task, context, state)
                    )
                    running_tasks[task_id] = async_task

                    self.logger.debug(f"Started task '{task_id}'")

                if not running_tasks:
                    break

                # Wait for first task to complete
                done, _ = await asyncio.wait(
                    running_tasks.values(),
                    return_when=asyncio.FIRST_COMPLETED,
                )

                # Process completed tasks
                for async_task in done:
                    # Find which task completed
                    task_id = None
                    for tid, atask in running_tasks.items():
                        if atask is async_task:
                            task_id = tid
                            break

                    if task_id:
                        del running_tasks[task_id]

                        if async_task.exception():
                            failed.add(task_id)
                            error_msg = str(async_task.exception())
                            state.mark_task_failed(task_id, error_msg)
                            self.logger.error(f"Task '{task_id}' failed: {error_msg}")
                        else:
                            completed.add(task_id)
                            result_data = async_task.result()
                            state.mark_task_completed(task_id, result_data)
                            self.logger.info(f"Task '{task_id}' completed successfully")

            state.mark_completed()
            result.success = len(failed) == 0
            result.task_results = state.task_results.copy()
            result.errors = state.execution_errors.copy()

        except Exception as e:
            self.logger.error(f"Parallel workflow execution failed: {e}", exc_info=True)
            result.success = False
            result.errors["_workflow"] = str(e)

            # Cancel any running tasks
            for async_task in running_tasks.values():
                async_task.cancel()

        return result

    async def _execute_task_async(
        self,
        task_id: str,
        task: Any,
        context: Dict[str, Any],
        state: WorkflowState,
    ) -> Any:
        """
        Execute a single task asynchronously.

        Args:
            task_id: Task identifier
            task: Task object
            context: Workflow context
            state: Workflow state tracker

        Returns:
            Task result

        Raises:
            Exception: If task execution fails
        """
        try:
            # Check if task has async method
            if hasattr(task, 'execute_async') and callable(task.execute_async):
                result = await task.execute_async(context)
            else:
                # Fall back to sync execution in thread pool
                result = await asyncio.to_thread(task.execute, context)

            task.success = True
            return result

        except asyncio.CancelledError:
            self.logger.warning(f"Task '{task_id}' was cancelled")
            raise
        except Exception as e:
            self.logger.error(f"Task '{task_id}' execution error: {e}", exc_info=True)
            task.success = False
            task.error = str(e)
            raise


class PriorityWorkflowExecutor(ParallelWorkflowExecutor):
    """
    Executes tasks with priority support.

    Allows tasks to have priority levels that affect scheduling order.
    """

    def _get_ready_tasks(
        self,
        workflow: Workflow,
        completed: Set[str],
        pending: Set[str],
    ) -> List[str]:
        """
        Get ready tasks sorted by priority.

        Args:
            workflow: Workflow definition
            completed: Set of completed task IDs
            pending: Set of pending task IDs

        Returns:
            List of task IDs ready to execute, sorted by priority
        """
        # Get base ready tasks
        ready = super()._get_ready_tasks(workflow, completed, pending)

        # Sort by task priority if available
        def get_priority(task_id: str) -> float:
            task = workflow.get_task(task_id)
            if task and hasattr(task, 'priority'):
                return -task.priority  # Negate for sort (higher priority first)
            return 0

        ready.sort(key=get_priority)
        return ready
