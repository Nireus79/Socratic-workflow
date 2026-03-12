"""Tests for Openclaw skill integration."""

import pytest

from socratic_workflow.integrations.openclaw import SocraticWorkflowSkill


class TestSocraticWorkflowSkill:
    """Test Openclaw skill integration."""

    def test_skill_creation(self):
        """Test skill can be created."""
        skill = SocraticWorkflowSkill()
        assert skill is not None
        assert skill.use_parallel_executor is False
        assert skill.max_workers == 5

    def test_skill_with_parallel_executor(self):
        """Test skill with parallel executor enabled."""
        skill = SocraticWorkflowSkill(use_parallel_executor=True, max_workers=10)
        assert skill.use_parallel_executor is True
        assert skill.max_workers == 10

    def test_skill_with_cost_tracking(self):
        """Test skill with cost tracking."""
        skill = SocraticWorkflowSkill(track_costs=True)
        assert skill.track_costs is True
        assert skill.cost_tracker is not None

    def test_skill_with_metrics(self):
        """Test skill with metrics collection."""
        skill = SocraticWorkflowSkill(track_metrics=True)
        assert skill.track_metrics is True
        assert skill.metrics_collector is not None

    @pytest.mark.asyncio
    async def test_execute_simple_workflow(self):
        """Test executing a simple workflow."""
        skill = SocraticWorkflowSkill()

        workflow_spec = {
            "name": "Test Workflow",
            "tasks": [{"id": "task1", "type": "SimpleTask", "result": {"value": 42}}],
        }

        result = await skill.execute_workflow(workflow_spec)

        assert result["success"] is True
        assert "task1" in result["task_results"]
        assert result["task_results"]["task1"]["value"] == 42

    @pytest.mark.asyncio
    async def test_execute_workflow_with_dependencies(self):
        """Test workflow with task dependencies."""
        skill = SocraticWorkflowSkill()

        workflow_spec = {
            "name": "Dependent Tasks",
            "tasks": [
                {"id": "task1", "type": "SimpleTask", "result": {"value": 10}},
                {
                    "id": "task2",
                    "type": "SimpleTask",
                    "result": {"value": 20},
                    "depends_on": ["task1"],
                },
            ],
        }

        result = await skill.execute_workflow(workflow_spec)

        assert result["success"] is True
        assert "task1" in result["task_results"]
        assert "task2" in result["task_results"]

    @pytest.mark.asyncio
    async def test_execute_workflow_with_invalid_spec(self):
        """Test workflow with invalid specification."""
        skill = SocraticWorkflowSkill()

        workflow_spec = {
            "name": "Invalid",
            "tasks": None,  # Invalid
        }

        result = await skill.execute_workflow(workflow_spec)

        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_execute_workflow_parallel(self):
        """Test parallel execution of independent tasks."""
        skill = SocraticWorkflowSkill(use_parallel_executor=True, max_workers=3)

        workflow_spec = {
            "name": "Parallel Tasks",
            "tasks": [
                {"id": "task1", "type": "SimpleTask", "result": {"value": 1}},
                {"id": "task2", "type": "SimpleTask", "result": {"value": 2}},
                {"id": "task3", "type": "SimpleTask", "result": {"value": 3}},
            ],
        }

        result = await skill.execute_workflow(workflow_spec)

        assert result["success"] is True
        assert len(result["task_results"]) == 3

    @pytest.mark.asyncio
    async def test_execute_workflow_with_cost_tracking(self):
        """Test workflow execution with cost tracking."""
        skill = SocraticWorkflowSkill(track_costs=True)

        workflow_spec = {
            "name": "Cost Tracking",
            "tasks": [{"id": "task1", "type": "SimpleTask", "result": {"value": 1}}],
        }

        result = await skill.execute_workflow(workflow_spec)

        assert result["success"] is True
        assert "cost_summary" in result

    def test_get_capabilities(self):
        """Test getting skill capabilities."""
        skill = SocraticWorkflowSkill(
            use_parallel_executor=True, track_costs=True, track_metrics=True
        )

        capabilities = skill.get_capabilities()

        assert capabilities["name"] == "SocraticWorkflow"
        assert "task_orchestration" in capabilities["capabilities"]
        assert capabilities["features"]["parallel_execution"] is True
        assert capabilities["features"]["cost_tracking"] is True
        assert capabilities["features"]["performance_metrics"] is True

    def test_build_workflow_simple(self):
        """Test building workflow from spec."""
        skill = SocraticWorkflowSkill()

        workflow_spec = {
            "name": "Test",
            "tasks": [
                {"id": "task1", "type": "SimpleTask", "result": {"x": 1}},
                {"id": "task2", "type": "SimpleTask", "depends_on": ["task1"]},
            ],
        }

        workflow = skill._build_workflow(workflow_spec)

        assert workflow.name == "Test"
        assert len(workflow.list_tasks()) == 2

    @pytest.mark.asyncio
    async def test_workflow_with_multiple_dependencies(self):
        """Test workflow with tasks having multiple dependencies."""
        skill = SocraticWorkflowSkill()

        workflow_spec = {
            "name": "Multi-Dep",
            "tasks": [
                {"id": "task1", "type": "SimpleTask", "result": {"x": 1}},
                {"id": "task2", "type": "SimpleTask", "result": {"x": 2}},
                {
                    "id": "task3",
                    "type": "SimpleTask",
                    "result": {"x": 3},
                    "depends_on": ["task1", "task2"],
                },
            ],
        }

        result = await skill.execute_workflow(workflow_spec)

        assert result["success"] is True
        assert len(result["task_results"]) == 3

    @pytest.mark.asyncio
    async def test_empty_workflow(self):
        """Test workflow with no tasks."""
        skill = SocraticWorkflowSkill()

        workflow_spec = {"name": "Empty", "tasks": []}

        result = await skill.execute_workflow(workflow_spec)

        assert result["success"] is True
        assert len(result["task_results"]) == 0
