"""LangChain tool integration for Socratic Workflow.

Provides a LangChain tool to run Socratic Workflow workflows from LangChain agents.
"""

import asyncio
import json
from typing import Any, Dict, Optional

from socratic_workflow import Workflow, WorkflowEngine
from socratic_workflow.analytics import MetricsCollector
from socratic_workflow.cost import CostTracker
from socratic_workflow.execution.executor import ParallelExecutor
from socratic_workflow.execution.retry import RetryConfig


class SocraticWorkflowTool:
    """
    LangChain tool for executing Socratic Workflows.

    Allows LangChain agents to orchestrate complex multi-step workflows with
    task dependencies, parallel execution, cost tracking, and error recovery.

    This tool integrates Socratic Workflow capabilities into LangChain agents.

    Example:
        from langchain.agents import Tool
        from socratic_workflow.integrations.langchain import SocraticWorkflowTool

        workflow_tool = SocraticWorkflowTool()
        tool = Tool(
            name="execute_workflow",
            func=workflow_tool.execute_sync,
            description="Execute a Socratic Workflow with multiple tasks"
        )
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
        Initialize LangChain tool.

        Args:
            use_parallel_executor: Use ParallelExecutor for async execution
            max_workers: Maximum concurrent tasks
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

    def execute_sync(self, workflow_spec_json: str) -> str:
        """
        Synchronous execution for LangChain compatibility.

        Args:
            workflow_spec_json: JSON string containing workflow specification

        Returns:
            JSON string with execution results
        """
        try:
            workflow_spec = json.loads(workflow_spec_json)
            result = asyncio.run(self.execute_workflow(workflow_spec))
            return json.dumps(result)
        except json.JSONDecodeError as e:
            return json.dumps(
                {
                    "success": False,
                    "error": f"Invalid JSON: {str(e)}",
                    "task_results": {},
                    "errors": {},
                }
            )
        except Exception as e:
            return json.dumps(
                {
                    "success": False,
                    "error": str(e),
                    "task_results": {},
                    "errors": {"execution": str(e)},
                }
            )

    async def execute_workflow(self, workflow_spec: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a workflow defined in a spec dictionary.

        Args:
            workflow_spec: Workflow specification with tasks and dependencies

        Returns:
            Dict with execution results
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

    def get_tool_description(self) -> str:
        """Get description for LangChain tool registration."""
        features = []
        if self.use_parallel_executor:
            features.append("parallel execution")
        if self.track_costs:
            features.append("cost tracking")
        if self.track_metrics:
            features.append("performance metrics")
        if self.retry_config:
            features.append("automatic error recovery")

        features_str = ", ".join(features) if features else "basic execution"

        return (
            "Execute Socratic Workflows with task orchestration, "
            f"dependencies, and {features_str}. "
            "Accepts JSON workflow specifications."
        )

    def get_json_schema(self) -> Dict[str, Any]:
        """Get JSON schema for tool input validation."""
        return {
            "type": "object",
            "properties": {
                "workflow_spec_json": {
                    "type": "string",
                    "description": "JSON string containing workflow specification with tasks and dependencies",
                }
            },
            "required": ["workflow_spec_json"],
        }
