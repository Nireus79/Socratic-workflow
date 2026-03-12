"""Performance metrics collection and analysis."""

import time
from datetime import datetime
from typing import Any, Dict, List, Optional


class MetricsCollector:
    """
    Collect performance metrics during workflow execution.

    Tracks task timing, success rates, and identifies bottlenecks.
    """

    def __init__(self):
        """Initialize metrics collector."""
        self.started_at = datetime.now().isoformat()
        self.task_timings: Dict[str, float] = {}
        self.task_start_times: Dict[str, float] = {}
        self.task_status: Dict[str, str] = {}
        self.task_count = 0
        self.success_count = 0
        self.failure_count = 0

    def track_task_start(self, task_name: str) -> None:
        """
        Mark task start time.

        Args:
            task_name: Name of task starting
        """
        self.task_start_times[task_name] = time.perf_counter()
        self.task_status[task_name] = "running"

    def track_task_end(self, task_name: str, success: bool) -> None:
        """
        Mark task end and record duration.

        Args:
            task_name: Name of task ending
            success: Whether task succeeded
        """
        if task_name not in self.task_start_times:
            return

        duration = time.perf_counter() - self.task_start_times[task_name]
        self.task_timings[task_name] = duration
        self.task_status[task_name] = "success" if success else "failed"
        self.task_count += 1

        if success:
            self.success_count += 1
        else:
            self.failure_count += 1

    def get_task_duration(self, task_name: str) -> Optional[float]:
        """
        Get execution duration of a task.

        Args:
            task_name: Name of task

        Returns:
            Duration in seconds, or None if not found
        """
        return self.task_timings.get(task_name)

    def get_bottlenecks(self, top_n: int = 5) -> List[tuple]:
        """
        Identify slowest tasks.

        Args:
            top_n: Number of slowest tasks to return

        Returns:
            List of (task_name, duration) tuples sorted by duration
        """
        sorted_tasks = sorted(self.task_timings.items(), key=lambda x: x[1], reverse=True)
        return sorted_tasks[:top_n]

    def get_summary(self) -> Dict[str, Any]:
        """
        Get execution summary.

        Returns:
            Dict with detailed metrics
        """
        total_duration = sum(self.task_timings.values())
        success_rate = self.success_count / self.task_count if self.task_count > 0 else 0

        bottlenecks = [task for task, _ in self.get_bottlenecks(3)]

        return {
            "total_duration": round(total_duration, 2),
            "tasks_executed": self.task_count,
            "tasks_succeeded": self.success_count,
            "tasks_failed": self.failure_count,
            "success_rate": round(success_rate * 100, 1),
            "average_task_duration": round(
                total_duration / self.task_count if self.task_count > 0 else 0, 2
            ),
            "slowest_tasks": bottlenecks,
            "task_timings": {k: round(v, 2) for k, v in self.task_timings.items()},
        }

    def get_timing_report(self) -> str:
        """
        Get human-readable timing report.

        Returns:
            Formatted string with timing breakdown
        """
        lines = ["Task Timing Report", "=" * 50]

        for task, duration in sorted(self.task_timings.items(), key=lambda x: x[1], reverse=True):
            status = self.task_status.get(task, "unknown")
            status_icon = "✓" if status == "success" else "✗"
            lines.append(f"{status_icon} {task:30s} {duration:7.2f}s")

        total = sum(self.task_timings.values())
        lines.append("=" * 50)
        lines.append(f"Total: {total:.2f}s ({self.success_count}/{self.task_count} succeeded)")

        return "\n".join(lines)

    def get_performance_metrics(self) -> Dict[str, float]:
        """
        Get key performance metrics.

        Returns:
            Dict with various performance KPIs
        """
        total_duration = sum(self.task_timings.values())
        task_count = len(self.task_timings)

        return {
            "total_execution_time": round(total_duration, 2),
            "average_task_time": round(total_duration / task_count if task_count > 0 else 0, 2),
            "fastest_task_time": round(
                min(self.task_timings.values()) if self.task_timings else 0, 2
            ),
            "slowest_task_time": round(
                max(self.task_timings.values()) if self.task_timings else 0, 2
            ),
            "task_count": task_count,
            "success_rate": round(
                (self.success_count / self.task_count * 100) if self.task_count > 0 else 0, 1
            ),
        }

    def reset(self) -> None:
        """Reset all metrics."""
        self.task_timings = {}
        self.task_start_times = {}
        self.task_status = {}
        self.task_count = 0
        self.success_count = 0
        self.failure_count = 0
        self.started_at = datetime.now().isoformat()
