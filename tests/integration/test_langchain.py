"""Tests for LangChain tool integration."""

import json

import pytest

from socratic_workflow.integrations.langchain import SocraticWorkflowTool


class TestSocraticWorkflowTool:
    """Test LangChain tool integration."""

    def test_tool_creation(self):
        """Test tool can be created."""
        tool = SocraticWorkflowTool()
        assert tool is not None
        assert tool.use_parallel_executor is False

    def test_tool_with_cost_tracking(self):
        """Test tool with cost tracking."""
        tool = SocraticWorkflowTool(track_costs=True)
        assert tool.track_costs is True
        assert tool.cost_tracker is not None

    def test_tool_with_metrics(self):
        """Test tool with metrics collection."""
        tool = SocraticWorkflowTool(track_metrics=True)
        assert tool.track_metrics is True
        assert tool.metrics_collector is not None

    def test_tool_description(self):
        """Test getting tool description."""
        tool = SocraticWorkflowTool(
            use_parallel_executor=True, track_costs=True, track_metrics=True
        )

        description = tool.get_tool_description()

        assert "Socratic Workflows" in description
        assert "parallel execution" in description
        assert "cost tracking" in description
        assert "performance metrics" in description

    def test_json_schema(self):
        """Test getting JSON schema."""
        tool = SocraticWorkflowTool()

        schema = tool.get_json_schema()

        assert schema["type"] == "object"
        assert "workflow_spec_json" in schema["properties"]
        assert "workflow_spec_json" in schema["required"]

    def test_execute_sync_valid_json(self):
        """Test synchronous execution with valid JSON."""
        tool = SocraticWorkflowTool()

        workflow_spec = {
            "name": "Test",
            "tasks": [{"id": "task1", "type": "SimpleTask", "result": {"value": 42}}],
        }

        result_json = tool.execute_sync(json.dumps(workflow_spec))
        result = json.loads(result_json)

        assert result["success"] is True
        assert "task1" in result["task_results"]

    def test_execute_sync_invalid_json(self):
        """Test synchronous execution with invalid JSON."""
        tool = SocraticWorkflowTool()

        result_json = tool.execute_sync("invalid json {")
        result = json.loads(result_json)

        assert result["success"] is False
        assert "Invalid JSON" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_workflow_simple(self):
        """Test executing simple workflow."""
        tool = SocraticWorkflowTool()

        workflow_spec = {
            "name": "Test",
            "tasks": [{"id": "task1", "type": "SimpleTask", "result": {"x": 1}}],
        }

        result = await tool.execute_workflow(workflow_spec)

        assert result["success"] is True
        assert "task1" in result["task_results"]

    @pytest.mark.asyncio
    async def test_execute_workflow_with_dependencies(self):
        """Test workflow with dependencies."""
        tool = SocraticWorkflowTool()

        workflow_spec = {
            "name": "Dependencies",
            "tasks": [
                {"id": "task1", "type": "SimpleTask", "result": {"x": 1}},
                {
                    "id": "task2",
                    "type": "SimpleTask",
                    "result": {"x": 2},
                    "depends_on": ["task1"],
                },
            ],
        }

        result = await tool.execute_workflow(workflow_spec)

        assert result["success"] is True
        assert "task1" in result["task_results"]
        assert "task2" in result["task_results"]

    @pytest.mark.asyncio
    async def test_execute_workflow_parallel(self):
        """Test parallel execution."""
        tool = SocraticWorkflowTool(use_parallel_executor=True)

        workflow_spec = {
            "name": "Parallel",
            "tasks": [
                {"id": "task1", "type": "SimpleTask", "result": {"x": 1}},
                {"id": "task2", "type": "SimpleTask", "result": {"x": 2}},
                {"id": "task3", "type": "SimpleTask", "result": {"x": 3}},
            ],
        }

        result = await tool.execute_workflow(workflow_spec)

        assert result["success"] is True
        assert len(result["task_results"]) == 3

    def test_execute_sync_wrapper(self):
        """Test synchronous wrapper for async execution."""
        tool = SocraticWorkflowTool()

        workflow_spec = {
            "name": "Test",
            "tasks": [{"id": "task1", "type": "SimpleTask", "result": {"value": 100}}],
        }

        result_json = tool.execute_sync(json.dumps(workflow_spec))
        result = json.loads(result_json)

        assert result["success"] is True
        assert result["task_results"]["task1"]["value"] == 100

    def test_build_workflow(self):
        """Test building workflow from spec."""
        tool = SocraticWorkflowTool()

        workflow_spec = {
            "name": "Built",
            "tasks": [
                {"id": "t1", "type": "SimpleTask"},
                {"id": "t2", "type": "SimpleTask", "depends_on": ["t1"]},
            ],
        }

        workflow = tool._build_workflow(workflow_spec)

        assert workflow.name == "Built"
        assert len(workflow.list_tasks()) == 2

    @pytest.mark.asyncio
    async def test_execute_with_cost_tracking(self):
        """Test execution with cost tracking."""
        tool = SocraticWorkflowTool(track_costs=True)

        workflow_spec = {
            "name": "Cost",
            "tasks": [{"id": "task1", "type": "SimpleTask", "result": {"x": 1}}],
        }

        result = await tool.execute_workflow(workflow_spec)

        assert result["success"] is True
        assert "cost_summary" in result

    @pytest.mark.asyncio
    async def test_execute_with_metrics(self):
        """Test execution with metrics collection."""
        tool = SocraticWorkflowTool(track_metrics=True)

        workflow_spec = {
            "name": "Metrics",
            "tasks": [{"id": "task1", "type": "SimpleTask", "result": {"x": 1}}],
        }

        result = await tool.execute_workflow(workflow_spec)

        assert result["success"] is True
        assert "metrics_summary" in result

    def test_format_result_basic(self):
        """Test result formatting."""
        tool = SocraticWorkflowTool()

        result_input = {"task_results": {"t1": {"x": 1}}, "errors": {}}

        result = tool._format_result(result_input)

        assert result["success"] is True
        assert "task_results" in result
        assert "errors" in result

    @pytest.mark.asyncio
    async def test_complex_workflow_dag(self):
        """Test complex workflow DAG execution."""
        tool = SocraticWorkflowTool()

        workflow_spec = {
            "name": "ComplexDAG",
            "tasks": [
                {"id": "t1", "type": "SimpleTask", "result": {"x": 1}},
                {"id": "t2", "type": "SimpleTask", "result": {"x": 2}},
                {
                    "id": "t3",
                    "type": "SimpleTask",
                    "result": {"x": 3},
                    "depends_on": ["t1", "t2"],
                },
                {"id": "t4", "type": "SimpleTask", "result": {"x": 4}, "depends_on": ["t3"]},
            ],
        }

        result = await tool.execute_workflow(workflow_spec)

        assert result["success"] is True
        assert len(result["task_results"]) == 4

    def test_tool_basic_configuration(self):
        """Test tool basic configuration options."""
        tool = SocraticWorkflowTool(
            use_parallel_executor=True,
            max_workers=8,
            track_costs=True,
            track_metrics=True,
        )

        assert tool.use_parallel_executor is True
        assert tool.max_workers == 8
        assert tool.track_costs is True
        assert tool.track_metrics is True

    def test_sync_execution_round_trip(self):
        """Test complete sync execution round trip."""
        tool = SocraticWorkflowTool()

        workflow_spec = {
            "name": "RoundTrip",
            "tasks": [{"id": "step1", "type": "SimpleTask", "result": {"status": "done"}}],
        }

        # Execute sync (which internally uses async)
        result_json = tool.execute_sync(json.dumps(workflow_spec))

        # Parse result
        result = json.loads(result_json)

        # Verify
        assert result["success"] is True
        assert "step1" in result["task_results"]
        assert result["task_results"]["step1"]["status"] == "done"
