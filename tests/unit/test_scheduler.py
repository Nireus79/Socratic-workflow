"""Tests for TaskScheduler."""

import pytest

from socratic_workflow.execution.scheduler import TaskScheduler


class TestTaskScheduler:
    """Test TaskScheduler."""

    def test_scheduler_creation(self):
        """Test scheduler can be created."""
        scheduler = TaskScheduler()
        assert scheduler is not None
        assert scheduler.tasks == {}

    def test_add_single_task(self):
        """Test adding a single task."""
        scheduler = TaskScheduler()
        scheduler.add_task("task1", [])

        assert "task1" in scheduler.tasks
        assert scheduler.tasks["task1"] == set()

    def test_add_task_with_dependencies(self):
        """Test adding task with dependencies."""
        scheduler = TaskScheduler()
        scheduler.add_task("task1", [])
        scheduler.add_task("task2", ["task1"])

        assert scheduler.tasks["task2"] == {"task1"}

    def test_add_multiple_dependencies(self):
        """Test adding task with multiple dependencies."""
        scheduler = TaskScheduler()
        scheduler.add_task("task1", [])
        scheduler.add_task("task2", [])
        scheduler.add_task("task3", ["task1", "task2"])

        assert scheduler.tasks["task3"] == {"task1", "task2"}

    def test_validate_no_dependencies(self):
        """Test validation with no dependencies."""
        scheduler = TaskScheduler()
        scheduler.add_task("task1", [])
        scheduler.add_task("task2", [])

        # Should not raise
        scheduler.validate_dependencies()

    def test_validate_valid_dependencies(self):
        """Test validation with valid dependencies."""
        scheduler = TaskScheduler()
        scheduler.add_task("task1", [])
        scheduler.add_task("task2", ["task1"])
        scheduler.add_task("task3", ["task2"])

        # Should not raise
        scheduler.validate_dependencies()

    def test_validate_detects_circular_dependency(self):
        """Test validation detects circular dependencies."""
        scheduler = TaskScheduler()
        scheduler.add_task("task1", ["task2"])
        scheduler.add_task("task2", ["task1"])

        with pytest.raises(ValueError, match="Circular dependency"):
            scheduler.validate_dependencies()

    def test_validate_detects_self_dependency(self):
        """Test validation detects self dependencies."""
        scheduler = TaskScheduler()
        scheduler.add_task("task1", ["task1"])

        with pytest.raises(ValueError, match="Circular dependency"):
            scheduler.validate_dependencies()

    def test_validate_detects_indirect_circular_dependency(self):
        """Test validation detects indirect circular dependencies."""
        scheduler = TaskScheduler()
        scheduler.add_task("task1", ["task2"])
        scheduler.add_task("task2", ["task3"])
        scheduler.add_task("task3", ["task1"])

        with pytest.raises(ValueError, match="Circular dependency"):
            scheduler.validate_dependencies()

    def test_build_execution_plan_single_task(self):
        """Test execution plan for single task."""
        scheduler = TaskScheduler()
        scheduler.add_task("task1", [])

        plan = scheduler.build_execution_plan()

        assert len(plan) == 1
        assert "task1" in plan[0]

    def test_build_execution_plan_independent_tasks(self):
        """Test execution plan for independent tasks."""
        scheduler = TaskScheduler()
        scheduler.add_task("task1", [])
        scheduler.add_task("task2", [])
        scheduler.add_task("task3", [])

        plan = scheduler.build_execution_plan()

        # All tasks should be in level 0
        assert len(plan) == 1
        assert len(plan[0]) == 3
        assert set(plan[0]) == {"task1", "task2", "task3"}

    def test_build_execution_plan_linear_dependencies(self):
        """Test execution plan with linear dependencies."""
        scheduler = TaskScheduler()
        scheduler.add_task("task1", [])
        scheduler.add_task("task2", ["task1"])
        scheduler.add_task("task3", ["task2"])

        plan = scheduler.build_execution_plan()

        # Should have 3 levels
        assert len(plan) == 3
        assert plan[0] == ["task1"]
        assert plan[1] == ["task2"]
        assert plan[2] == ["task3"]

    def test_build_execution_plan_branching(self):
        """Test execution plan with branching dependencies."""
        scheduler = TaskScheduler()
        scheduler.add_task("task1", [])
        scheduler.add_task("task2", ["task1"])
        scheduler.add_task("task3", ["task1"])

        plan = scheduler.build_execution_plan()

        # task1 at level 0, task2 and task3 at level 1
        assert len(plan) == 2
        assert plan[0] == ["task1"]
        assert set(plan[1]) == {"task2", "task3"}

    def test_build_execution_plan_complex(self):
        """Test execution plan with complex dependencies."""
        scheduler = TaskScheduler()
        scheduler.add_task("task1", [])
        scheduler.add_task("task2", [])
        scheduler.add_task("task3", ["task1", "task2"])
        scheduler.add_task("task4", ["task3"])
        scheduler.add_task("task5", ["task2"])

        plan = scheduler.build_execution_plan()

        # Verify structure
        assert len(plan) >= 2
        # task1 and task2 should be at level 0
        assert set(plan[0]) == {"task1", "task2"}

    def test_get_independent_tasks_empty_completed(self):
        """Test get independent tasks with no completed tasks."""
        scheduler = TaskScheduler()
        scheduler.add_task("task1", [])
        scheduler.add_task("task2", ["task1"])

        ready = scheduler.get_independent_tasks(set())

        assert set(ready) == {"task1"}

    def test_get_independent_tasks_with_completed(self):
        """Test get independent tasks with some completed."""
        scheduler = TaskScheduler()
        scheduler.add_task("task1", [])
        scheduler.add_task("task2", ["task1"])
        scheduler.add_task("task3", ["task2"])

        ready = scheduler.get_independent_tasks({"task1"})

        assert set(ready) == {"task2"}

    def test_get_independent_tasks_multiple_ready(self):
        """Test get independent tasks when multiple are ready."""
        scheduler = TaskScheduler()
        scheduler.add_task("task1", [])
        scheduler.add_task("task2", ["task1"])
        scheduler.add_task("task3", ["task1"])

        ready = scheduler.get_independent_tasks({"task1"})

        assert set(ready) == {"task2", "task3"}

    def test_get_all_dependencies_no_deps(self):
        """Test get all dependencies for task with no deps."""
        scheduler = TaskScheduler()
        scheduler.add_task("task1", [])

        deps = scheduler.get_all_dependencies("task1")

        assert deps == set()

    def test_get_all_dependencies_direct(self):
        """Test get all dependencies with direct deps."""
        scheduler = TaskScheduler()
        scheduler.add_task("task1", [])
        scheduler.add_task("task2", ["task1"])

        deps = scheduler.get_all_dependencies("task2")

        assert deps == {"task1"}

    def test_get_all_dependencies_transitive(self):
        """Test get all dependencies with transitive closure."""
        scheduler = TaskScheduler()
        scheduler.add_task("task1", [])
        scheduler.add_task("task2", ["task1"])
        scheduler.add_task("task3", ["task2"])

        deps = scheduler.get_all_dependencies("task3")

        assert deps == {"task1", "task2"}

    def test_get_all_dependencies_multiple(self):
        """Test get all dependencies with multiple paths."""
        scheduler = TaskScheduler()
        scheduler.add_task("task1", [])
        scheduler.add_task("task2", [])
        scheduler.add_task("task3", ["task1", "task2"])
        scheduler.add_task("task4", ["task3"])

        deps = scheduler.get_all_dependencies("task4")

        assert deps == {"task1", "task2", "task3"}

    def test_get_dependent_tasks_no_dependents(self):
        """Test get dependent tasks when none exist."""
        scheduler = TaskScheduler()
        scheduler.add_task("task1", [])

        dependents = scheduler.get_dependent_tasks("task1")

        assert dependents == set()

    def test_get_dependent_tasks_single(self):
        """Test get dependent tasks with single dependent."""
        scheduler = TaskScheduler()
        scheduler.add_task("task1", [])
        scheduler.add_task("task2", ["task1"])

        dependents = scheduler.get_dependent_tasks("task1")

        assert dependents == {"task2"}

    def test_get_dependent_tasks_multiple(self):
        """Test get dependent tasks with multiple dependents."""
        scheduler = TaskScheduler()
        scheduler.add_task("task1", [])
        scheduler.add_task("task2", ["task1"])
        scheduler.add_task("task3", ["task1"])

        dependents = scheduler.get_dependent_tasks("task1")

        assert dependents == {"task2", "task3"}

    def test_get_execution_order_single(self):
        """Test execution order for single task."""
        scheduler = TaskScheduler()
        scheduler.add_task("task1", [])

        order = scheduler.get_execution_order()

        assert order == ["task1"]

    def test_get_execution_order_linear(self):
        """Test execution order for linear dependencies."""
        scheduler = TaskScheduler()
        scheduler.add_task("task1", [])
        scheduler.add_task("task2", ["task1"])
        scheduler.add_task("task3", ["task2"])

        order = scheduler.get_execution_order()

        # Should be in dependency order
        assert order.index("task1") < order.index("task2")
        assert order.index("task2") < order.index("task3")

    def test_get_execution_order_valid(self):
        """Test execution order is valid."""
        scheduler = TaskScheduler()
        scheduler.add_task("task1", [])
        scheduler.add_task("task2", ["task1"])
        scheduler.add_task("task3", ["task2"])
        scheduler.add_task("task4", ["task1"])

        order = scheduler.get_execution_order()

        # Verify all tasks present
        assert len(order) == 4
        assert set(order) == {"task1", "task2", "task3", "task4"}

        # Verify order respects dependencies
        assert order.index("task1") < order.index("task2")
        assert order.index("task1") < order.index("task4")
        assert order.index("task2") < order.index("task3")

    def test_get_parallelizable_count_empty(self):
        """Test parallelizable count for empty scheduler."""
        scheduler = TaskScheduler()

        metrics = scheduler.get_parallelizable_count()

        assert metrics["total_tasks"] == 0
        assert metrics["max_parallel"] == 0
        assert metrics["critical_path_length"] == 0

    def test_get_parallelizable_count_single(self):
        """Test parallelizable count for single task."""
        scheduler = TaskScheduler()
        scheduler.add_task("task1", [])

        metrics = scheduler.get_parallelizable_count()

        assert metrics["total_tasks"] == 1
        assert metrics["max_parallel"] == 1
        assert metrics["critical_path_length"] == 1

    def test_get_parallelizable_count_independent(self):
        """Test parallelizable count for independent tasks."""
        scheduler = TaskScheduler()
        scheduler.add_task("task1", [])
        scheduler.add_task("task2", [])
        scheduler.add_task("task3", [])

        metrics = scheduler.get_parallelizable_count()

        assert metrics["total_tasks"] == 3
        assert metrics["max_parallel"] == 3
        assert metrics["critical_path_length"] == 1
        assert abs(metrics["parallelization_factor"] - 1.0) < 0.01

    def test_get_parallelizable_count_linear(self):
        """Test parallelizable count for linear dependencies."""
        scheduler = TaskScheduler()
        scheduler.add_task("task1", [])
        scheduler.add_task("task2", ["task1"])
        scheduler.add_task("task3", ["task2"])

        metrics = scheduler.get_parallelizable_count()

        assert metrics["total_tasks"] == 3
        assert metrics["max_parallel"] == 1
        assert metrics["critical_path_length"] == 3
        assert abs(metrics["parallelization_factor"] - (1.0 / 3.0)) < 0.01

    def test_get_parallelizable_count_complex(self):
        """Test parallelizable count for complex dependencies."""
        scheduler = TaskScheduler()
        scheduler.add_task("task1", [])
        scheduler.add_task("task2", [])
        scheduler.add_task("task3", ["task1", "task2"])
        scheduler.add_task("task4", ["task3"])
        scheduler.add_task("task5", ["task3"])

        metrics = scheduler.get_parallelizable_count()

        assert metrics["total_tasks"] == 5
        assert metrics["max_parallel"] == 2  # task1, task2 in parallel
        assert metrics["critical_path_length"] == 3
