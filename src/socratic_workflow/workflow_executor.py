"""
Workflow Execution Engine - Executes complex workflows with task dependencies.

Provides:
- Sequential workflow execution
- Dependency management between tasks
- Error handling and retry logic
- State tracking and persistence
- Event emission for monitoring
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class WorkflowExecutor:
    """
    Executes workflows (sequences of tasks with dependencies).

    Features:
    - Execute steps sequentially or with dependency management
    - Persist workflow state
    - Event emission for monitoring
    - Error handling and recovery
    - Variable substitution across steps
    """

    def __init__(
        self,
        orchestrator: Optional[Any] = None,
        event_bus: Optional[Any] = None,
    ):
        """
        Initialize workflow executor.

        Args:
            orchestrator: Optional agent orchestrator for agent calls
            event_bus: Optional event bus for emitting events
        """
        self.orchestrator = orchestrator
        self.event_bus = event_bus
        self.logger = logging.getLogger(f"{__name__}.WorkflowExecutor")

        # Active workflows: id -> workflow state
        self._workflows: Dict[str, Dict[str, Any]] = {}

        self.logger.info("WorkflowExecutor initialized")

    def execute_workflow(
        self,
        workflow: Dict[str, Any],
        stop_on_error: bool = True,
    ) -> Dict[str, Any]:
        """
        Execute a workflow.

        Workflow format:
        {
            "id": "workflow_id",
            "name": "Workflow Name",
            "steps": [
                {
                    "id": "step_1",
                    "agent": "agent_name",  # or "action" for action steps
                    "request": {...},
                    "depends_on": ["step_0"],  # optional dependencies
                    "retry": 3  # optional retry count
                }
            ]
        }

        Args:
            workflow: Workflow definition dict
            stop_on_error: Stop execution on first error

        Returns:
            Workflow execution result
        """
        workflow_id = workflow.get("id", "unknown")
        workflow_name = workflow.get("name", "Unnamed Workflow")

        self.logger.info(f"Starting workflow execution: {workflow_name} ({workflow_id})")

        # Initialize workflow state
        workflow_state = {
            "id": workflow_id,
            "name": workflow_name,
            "status": "running",
            "started_at": datetime.utcnow().isoformat(),
            "steps": {},
            "variables": {},
        }

        self._workflows[workflow_id] = workflow_state

        steps = workflow.get("steps", [])
        completed_steps = set()
        failed_steps = set()
        variables = {}

        try:
            # Execute steps
            for step in steps:
                step_id = step.get("id", f"step_{len(completed_steps)}")
                self.logger.info(f"Executing step: {step_id}")

                # Check dependencies
                dependencies = step.get("depends_on", [])
                if not self._check_dependencies(dependencies, completed_steps, failed_steps):
                    self.logger.error(f"Step {step_id} dependency not met")
                    step_result = {
                        "status": "skipped",
                        "reason": "dependency not met",
                    }
                    workflow_state["steps"][step_id] = step_result
                    if stop_on_error:
                        break
                    continue

                # Execute step
                step_result = self._execute_step(step, variables)
                workflow_state["steps"][step_id] = step_result

                # Update state
                if step_result.get("status") == "success":
                    completed_steps.add(step_id)

                    # Save output for dependent steps
                    save_as = step.get("save_as")
                    if save_as:
                        variables[save_as] = step_result.get("result")
                else:
                    failed_steps.add(step_id)
                    if stop_on_error:
                        self.logger.error(f"Step {step_id} failed, stopping workflow")
                        break

            # Determine final status
            workflow_state["status"] = (
                "completed" if not failed_steps else "failed" if stop_on_error else "partial"
            )

            self.logger.info(
                f"Workflow {workflow_name} completed: "
                f"{len(completed_steps)} succeeded, {len(failed_steps)} failed"
            )

            # Emit completion event
            self._emit_event(
                "workflow_completed",
                {"workflow_id": workflow_id, "status": workflow_state["status"]},
            )

            return {
                "workflow_id": workflow_id,
                "status": workflow_state["status"],
                "steps_completed": len(completed_steps),
                "steps_failed": len(failed_steps),
                "results": workflow_state["steps"],
            }

        except Exception as e:
            self.logger.error(f"Workflow execution error: {str(e)}")
            workflow_state["status"] = "error"

            self._emit_event("workflow_error", {"workflow_id": workflow_id, "error": str(e)})

            return {
                "workflow_id": workflow_id,
                "status": "error",
                "message": str(e),
                "results": workflow_state["steps"],
            }

    def _execute_step(self, step: Dict[str, Any], variables: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a single step.

        Args:
            step: Step definition
            variables: Current variables dict

        Returns:
            Step execution result
        """
        step_id = step.get("id", "unknown")
        agent_name = step.get("agent")
        action = step.get("action")
        request = step.get("request", {})
        retry_count = step.get("retry", 0)

        try:
            # Substitute variables in request
            request = self._substitute_variables(request, variables)

            # Execute as agent call
            if agent_name and self.orchestrator:
                result = self.orchestrator.call_agent(agent_name, request)

                return {
                    "status": "success" if result.get("status") != "error" else "error",
                    "step_id": step_id,
                    "agent": agent_name,
                    "result": result,
                }

            # Execute as action
            elif action:
                return self._execute_action(action, request, variables)

            else:
                return {
                    "status": "error",
                    "step_id": step_id,
                    "message": "Step must have 'agent' or 'action'",
                }

        except Exception as e:
            self.logger.error(f"Error executing step {step_id}: {str(e)}")

            # Retry logic
            if retry_count > 0:
                self.logger.info(f"Retrying step {step_id} ({retry_count} retries left)")
                retry_step = step.copy()
                retry_step["retry"] = retry_count - 1
                return self._execute_step(retry_step, variables)

            return {
                "status": "error",
                "step_id": step_id,
                "message": str(e),
            }

    def _execute_action(
        self, action: str, request: Dict[str, Any], variables: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a built-in action (not an agent call).

        Args:
            action: Action name
            request: Action request dict
            variables: Current variables

        Returns:
            Action result
        """
        if action == "wait":
            # Wait action - pause execution
            import time

            delay = request.get("delay", 1)
            time.sleep(delay)
            return {"status": "success", "action": action, "waited_seconds": delay}

        elif action == "branch":
            # Branch action - conditional execution
            condition = request.get("condition", "")
            true_branch = request.get("true", {})
            false_branch = request.get("false", {})

            # Evaluate condition (simple variable check)
            condition_result = variables.get(condition, False)

            result = (
                self._execute_step(true_branch, variables)
                if condition_result
                else self._execute_step(false_branch, variables)
            )
            return result

        elif action == "merge":
            # Merge action - combine results from multiple steps
            results = {}
            for key in request.get("inputs", []):
                results[key] = variables.get(key)
            return {"status": "success", "action": action, "result": results}

        else:
            return {
                "status": "error",
                "action": action,
                "message": f"Unknown action: {action}",
            }

    def _check_dependencies(self, dependencies: List[str], completed: set, failed: set) -> bool:
        """Check if all dependencies are met."""
        for dep in dependencies:
            if dep in failed:
                return False
            if dep not in completed:
                return False
        return True

    def _substitute_variables(self, obj: Any, variables: Dict[str, Any]) -> Any:
        """Recursively substitute ${var} references."""
        if isinstance(obj, dict):
            return {k: self._substitute_variables(v, variables) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._substitute_variables(item, variables) for item in obj]
        elif isinstance(obj, str):
            # Replace ${var} with variable value
            for var_name, var_value in variables.items():
                obj = obj.replace(f"${{{var_name}}}", str(var_value))
            return obj
        return obj

    def _emit_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Emit an event."""
        if self.event_bus:
            self.event_bus.emit(event_type, data)
        else:
            self.logger.debug(f"Event (no bus): {event_type}")

    def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a workflow."""
        return self._workflows.get(workflow_id)

    def list_active_workflows(self) -> List[Dict[str, Any]]:
        """List all active workflows."""
        return list(self._workflows.values())
