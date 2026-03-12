"""Parallel task execution with dependency management."""

import asyncio
from typing import Any, Dict, Optional

from ..workflow import Workflow
from .retry import RetryConfig
from .scheduler import TaskScheduler


class ParallelExecutor:
    """
    Execute workflow tasks in parallel respecting dependencies.

    Uses asyncio to run independent tasks concurrently.
    """

    def __init__(self, retry_config: Optional[RetryConfig] = None, max_workers: int = 5):
        """
        Initialize parallel executor.

        Args:
            retry_config: Retry configuration for task failures
            max_workers: Maximum concurrent tasks
        """
        self.retry_config = retry_config or RetryConfig()
        self.max_workers = max_workers
        self.task_results: Dict[str, Any] = {}
        self.task_errors: Dict[str, str] = {}

    async def execute_parallel(self, workflow: Workflow) -> Dict[str, Any]:
        """
        Execute workflow with parallel task execution.

        Tasks are executed in parallel when dependencies allow.

        Args:
            workflow: Workflow to execute

        Returns:
            Dict with task_results and errors
        """
        # Build execution schedule
        scheduler = TaskScheduler()
        for task_id in workflow.list_tasks():
            depends_on = workflow.get_dependencies(task_id)
            scheduler.add_task(task_id, depends_on)

        scheduler.validate_dependencies()
        execution_plan = scheduler.build_execution_plan()

        # Execute by levels (parallel at each level)
        for level in execution_plan:
            if not level:
                continue

            # Execute all tasks in this level in parallel
            await self._execute_level(workflow, level)

        return {
            "task_results": self.task_results.copy(),
            "task_errors": self.task_errors.copy(),
        }

    async def _execute_level(self, workflow: Workflow, task_ids: list) -> None:
        """
        Execute a level of tasks in parallel.

        Args:
            workflow: Workflow instance
            task_ids: Task IDs to execute at this level
        """
        # Create coroutines for all tasks
        coroutines = [self._execute_single_task(workflow, task_id) for task_id in task_ids]

        # Run in parallel with semaphore to limit concurrency
        semaphore = asyncio.Semaphore(self.max_workers)

        async def execute_with_semaphore(coro):  # type: ignore
            async with semaphore:
                return await coro

        await asyncio.gather(*[execute_with_semaphore(coro) for coro in coroutines])

    async def _execute_single_task(self, workflow: Workflow, task_id: str) -> None:
        """
        Execute a single task asynchronously.

        Args:
            workflow: Workflow instance
            task_id: Task ID to execute
        """
        task = workflow.get_task(task_id)
        if task is None:
            return

        try:
            # Get context from completed tasks
            context = {
                tid: self.task_results[tid]
                for tid in workflow.list_tasks()
                if tid in self.task_results
            }

            # Execute task
            result = await task.execute_async(context)
            self.task_results[task_id] = result
            task.success = True

        except Exception as e:
            self.task_errors[task_id] = str(e)
            task.error = str(e)
            task.success = False

    def get_execution_metrics(self) -> Dict[str, Any]:
        """
        Get metrics about parallel execution.

        Returns:
            Dict with execution metrics
        """
        total_tasks = len(self.task_results) + len(self.task_errors)
        success_count = len(self.task_results)
        failure_count = len(self.task_errors)

        return {
            "total_tasks": total_tasks,
            "successful_tasks": success_count,
            "failed_tasks": failure_count,
            "success_rate": success_count / total_tasks if total_tasks > 0 else 0,
        }
