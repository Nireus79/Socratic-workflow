"""Task scheduling with dependency resolution."""

from typing import Any, Dict, List, Set


class TaskScheduler:
    """
    Schedule tasks based on dependencies.

    Builds a DAG (Directed Acyclic Graph), detects cycles,
    and enables parallel execution by identifying independent tasks.
    """

    def __init__(self):
        """Initialize task scheduler."""
        self.tasks: Dict[str, Set[str]] = {}  # task_id -> dependencies

    def add_task(self, task_id: str, depends_on: List[str]) -> None:
        """
        Add task with its dependencies.

        Args:
            task_id: Unique task identifier
            depends_on: List of task IDs this task depends on
        """
        self.tasks[task_id] = set(depends_on)

    def validate_dependencies(self) -> None:
        """
        Validate that there are no circular dependencies.

        Raises:
            ValueError: If circular dependency detected
        """
        visited: Set[str] = set()
        rec_stack: Set[str] = set()

        def has_cycle(task_id: str) -> bool:
            """Check if task has circular dependency."""
            visited.add(task_id)
            rec_stack.add(task_id)

            dependencies = self.tasks.get(task_id, set())
            for dep in dependencies:
                if dep not in visited:
                    if has_cycle(dep):
                        return True
                elif dep in rec_stack:
                    return True

            rec_stack.remove(task_id)
            return False

        for task_id in self.tasks:
            if task_id not in visited:
                if has_cycle(task_id):
                    raise ValueError(f"Circular dependency detected involving {task_id}")

    def build_execution_plan(self) -> List[List[str]]:
        """
        Build execution plan grouped by dependency level.

        Tasks at the same level can execute in parallel.

        Returns:
            List of task groups that can run in parallel.
            Example: [["task1", "task2"], ["task3"], ["task4", "task5"]]

        Raises:
            ValueError: If circular dependency detected
        """
        self.validate_dependencies()

        # Calculate depth for each task (longest path from a root)
        depths: Dict[str, int] = {}

        def calculate_depth(task_id: str) -> int:
            """Calculate depth of a task in the DAG."""
            if task_id in depths:
                return depths[task_id]

            dependencies = self.tasks.get(task_id, set())
            if not dependencies:
                depths[task_id] = 0
                return 0

            max_dep_depth = max(calculate_depth(dep) for dep in dependencies)
            depths[task_id] = max_dep_depth + 1
            return depths[task_id]

        # Calculate depths for all tasks
        for task_id in self.tasks:
            calculate_depth(task_id)

        # Group tasks by depth
        levels: Dict[int, List[str]] = {}
        for task_id, depth in depths.items():
            if depth not in levels:
                levels[depth] = []
            levels[depth].append(task_id)

        # Return as list of lists, sorted by depth
        max_depth = max(depths.values()) if depths else -1
        result = [levels.get(i, []) for i in range(max_depth + 1)]

        return result

    def get_independent_tasks(self, completed: Set[str]) -> List[str]:
        """
        Get tasks that can run now (all dependencies completed).

        Args:
            completed: Set of completed task IDs

        Returns:
            List of task IDs ready to execute
        """
        ready = []

        for task_id, dependencies in self.tasks.items():
            if task_id not in completed:
                # Check if all dependencies are completed
                if dependencies.issubset(completed):
                    ready.append(task_id)

        return ready

    def get_all_dependencies(self, task_id: str) -> Set[str]:
        """
        Get all dependencies for a task (transitive closure).

        Args:
            task_id: Task to get dependencies for

        Returns:
            Set of all task IDs this task depends on
        """
        all_deps: Set[str] = set()

        def collect_deps(tid: str) -> None:
            """Recursively collect all dependencies."""
            direct_deps = self.tasks.get(tid, set())
            for dep in direct_deps:
                if dep not in all_deps:
                    all_deps.add(dep)
                    collect_deps(dep)

        collect_deps(task_id)
        return all_deps

    def get_dependent_tasks(self, task_id: str) -> Set[str]:
        """
        Get all tasks that depend on this task.

        Args:
            task_id: Task to find dependents for

        Returns:
            Set of task IDs that depend on this task
        """
        dependents: Set[str] = set()

        for tid, dependencies in self.tasks.items():
            if task_id in dependencies:
                dependents.add(tid)

        return dependents

    def get_execution_order(self) -> List[str]:
        """
        Get topological sort of tasks (valid execution order).

        Returns:
            List of task IDs in valid execution order
        """
        self.validate_dependencies()

        visited: Set[str] = set()
        order: List[str] = []

        def visit(task_id: str) -> None:
            """Visit task and its dependencies."""
            if task_id in visited:
                return

            visited.add(task_id)

            # Visit dependencies first
            for dep in self.tasks.get(task_id, set()):
                visit(dep)

            order.append(task_id)

        for task_id in self.tasks:
            visit(task_id)

        return order

    def get_parallelizable_count(self) -> Dict[str, Any]:
        """
        Get metrics about parallelization potential.

        Returns:
            Dict with:
            - total_tasks: Total number of tasks
            - max_parallel: Max tasks that can run in parallel
            - critical_path_length: Longest dependency chain
        """
        if not self.tasks:
            return {"total_tasks": 0, "max_parallel": 0, "critical_path_length": 0}

        execution_plan = self.build_execution_plan()
        max_parallel = max(len(level) for level in execution_plan) if execution_plan else 0

        return {
            "total_tasks": len(self.tasks),
            "max_parallel": max_parallel,
            "critical_path_length": len(execution_plan),
            "parallelization_factor": max_parallel / len(self.tasks) if self.tasks else 0,
        }
