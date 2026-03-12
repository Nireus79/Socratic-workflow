"""Openclaw skill integration for Socratic Workflow.

Provides a skill to run Socratic Workflow workflows from Openclaw agents.
"""

from typing import Any, Dict, Optional

from socratic_workflow import Workflow, WorkflowEngine
from socratic_workflow.analytics import MetricsCollector
from socratic_workflow.cost import CostTracker
from socratic_workflow.execution.executor import ParallelExecutor
from socratic_workflow.execution.retry import RetryConfig


class SocraticWorkflowSkill:
    """
    Openclaw skill for executing Socratic Workflows.

    Allows Openclaw agents to orchestrate complex multi-step workflows with
    task dependencies, parallel execution, cost tracking, and error recovery.

    Example:
        skill = SocraticWorkflowSkill()
        result = await skill.execute_workflow({
            "tasks": [
                {"id": "fetch", "type": "HttpTask", "config": {...}},
                {"id": "process", "type": "ProcessTask", "depends_on": ["fetch"]},
            ]
        })
    """

    def __init__(
        self,
        use_parallel_executor: bool = False,
        max_workers: int = 5,
        retry_config: Optional[RetryConfig] = None,
        track_costs: bool = False,
        track_metrics: bool = False,
    ):
        """
        Initialize Openclaw skill.

        Args:
            use_parallel_executor: Use ParallelExecutor for async execution
            max_workers: Maximum concurrent tasks (if using parallel executor)
            retry_config: Retry configuration for error recovery
            track_costs: Enable LLM cost tracking
            track_metrics: Enable performance metrics collection
        """
        self.use_parallel_executor = use_parallel_executor
        self.max_workers = max_workers
        self.retry_config = retry_config
        self.track_costs = track_costs
        self.track_metrics = track_metrics

        self.cost_tracker: Optional[CostTracker] = None
        self.metrics_collector: Optional[MetricsCollector] = None

        if track_costs:
            self.cost_tracker = CostTracker()
        if track_metrics:
            self.metrics_collector = MetricsCollector()

    async def execute_workflow(self, workflow_spec: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a workflow defined in a spec dictionary.

        Args:
            workflow_spec: Workflow specification with tasks and dependencies

        Returns:
            Dict with:
                - success: Whether workflow succeeded
                - task_results: Results from each task
                - errors: Any errors that occurred
                - cost_summary: Cost tracking (if enabled)
                - metrics_summary: Performance metrics (if enabled)
        """
        try:
            workflow = self._build_workflow(workflow_spec)

            if self.use_parallel_executor:
                result = await self._execute_parallel(workflow)
            else:
                result = await self._execute_sequential(workflow)

            return self._format_result(result)
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "task_results": {},
                "errors": {"workflow": str(e)},
            }

    async def _execute_parallel(self, workflow: Workflow) -> Dict[str, Any]:
        """Execute workflow using parallel executor."""
        executor = ParallelExecutor(retry_config=self.retry_config, max_workers=self.max_workers)
        return await executor.execute_parallel(workflow)

    async def _execute_sequential(self, workflow: Workflow) -> Dict[str, Any]:
        """Execute workflow using standard engine."""
        engine = WorkflowEngine()
        result = await engine.execute_async(workflow)
        return {
            "task_results": result.task_results,
            "errors": result.errors,
            "success": result.success,
        }

    def _build_workflow(self, workflow_spec: Dict[str, Any]) -> Workflow:
        """Build Workflow from spec dictionary."""
        from socratic_workflow import SimpleTask

        name = workflow_spec.get("name", "Workflow")
        workflow = Workflow(name)

        # Get tasks
        tasks = workflow_spec.get("tasks", [])
        for task_spec in tasks:
            task_id = task_spec.get("id")
            task_type = task_spec.get("type", "SimpleTask")
            depends_on = task_spec.get("depends_on", [])

            # Create task based on type
            if task_type == "SimpleTask":
                result = task_spec.get("result", {})
                task = SimpleTask(result=result)
            else:
                # Default to SimpleTask for unknown types
                task = SimpleTask()

            # Add to workflow
            workflow.add_task(task_id, task, depends_on=depends_on)

        return workflow

    def _format_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Format execution result with optional tracking data."""
        formatted = {
            "success": result.get("task_results") is not None,
            "task_results": result.get("task_results", {}),
            "errors": result.get("errors", {}),
        }

        # Add cost tracking if enabled
        if self.track_costs and self.cost_tracker:
            formatted["cost_summary"] = self.cost_tracker.get_summary()

        # Add metrics if enabled
        if self.track_metrics and self.metrics_collector:
            formatted["metrics_summary"] = self.metrics_collector.get_summary()

        return formatted

    def get_capabilities(self) -> Dict[str, Any]:
        """Get skill capabilities for discovery."""
        return {
            "name": "SocraticWorkflow",
            "description": "Execute Socratic Workflow workflows from Openclaw",
            "capabilities": [
                "task_orchestration",
                "parallel_execution",
                "error_recovery",
                "cost_tracking",
                "performance_metrics",
            ],
            "supported_task_types": ["SimpleTask"],
            "features": {
                "parallel_execution": self.use_parallel_executor,
                "cost_tracking": self.track_costs,
                "performance_metrics": self.track_metrics,
                "error_recovery": self.retry_config is not None,
            },
        }
