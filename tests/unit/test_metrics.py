"""Tests for MetricsCollector."""

import time

from socratic_workflow.analytics import MetricsCollector


class TestMetricsCollector:
    """Test MetricsCollector class."""

    def test_collector_creation(self):
        """Test collector can be created."""
        collector = MetricsCollector()
        assert collector.task_count == 0
        assert collector.success_count == 0
        assert collector.failure_count == 0

    def test_track_single_task(self):
        """Test tracking a single task."""
        collector = MetricsCollector()

        collector.track_task_start("task1")
        time.sleep(0.01)
        collector.track_task_end("task1", success=True)

        assert collector.task_count == 1
        assert collector.success_count == 1
        assert collector.failure_count == 0
        assert "task1" in collector.task_timings
        assert collector.task_timings["task1"] > 0.01

    def test_track_multiple_tasks(self):
        """Test tracking multiple tasks."""
        collector = MetricsCollector()

        for i in range(3):
            collector.track_task_start(f"task{i}")
            time.sleep(0.01)
            collector.track_task_end(f"task{i}", success=True)

        assert collector.task_count == 3
        assert collector.success_count == 3

    def test_track_failed_task(self):
        """Test tracking failed tasks."""
        collector = MetricsCollector()

        collector.track_task_start("success")
        collector.track_task_end("success", success=True)

        collector.track_task_start("failure")
        collector.track_task_end("failure", success=False)

        assert collector.task_count == 2
        assert collector.success_count == 1
        assert collector.failure_count == 1

    def test_get_task_duration(self):
        """Test getting task duration."""
        collector = MetricsCollector()

        collector.track_task_start("task1")
        time.sleep(0.01)
        collector.track_task_end("task1", success=True)

        duration = collector.get_task_duration("task1")
        assert duration is not None
        assert duration >= 0.01

    def test_get_task_duration_nonexistent(self):
        """Test getting duration of nonexistent task."""
        collector = MetricsCollector()
        duration = collector.get_task_duration("nonexistent")
        assert duration is None

    def test_get_bottlenecks(self):
        """Test identifying bottleneck tasks."""
        collector = MetricsCollector()

        # Create tasks with different durations
        for i in range(5):
            collector.track_task_start(f"task{i}")
            time.sleep(0.01 * (i + 1))
            collector.track_task_end(f"task{i}", success=True)

        bottlenecks = collector.get_bottlenecks(3)

        # Should return slowest 3 tasks
        assert len(bottlenecks) <= 3
        # Should be sorted by duration descending
        if len(bottlenecks) > 1:
            assert bottlenecks[0][1] >= bottlenecks[1][1]

    def test_get_summary(self):
        """Test summary generation."""
        collector = MetricsCollector()

        collector.track_task_start("task1")
        collector.track_task_end("task1", success=True)

        collector.track_task_start("task2")
        collector.track_task_end("task2", success=False)

        summary = collector.get_summary()

        assert "total_duration" in summary
        assert "tasks_executed" in summary
        assert "tasks_succeeded" in summary
        assert "tasks_failed" in summary
        assert "success_rate" in summary
        assert summary["tasks_executed"] == 2
        assert summary["tasks_succeeded"] == 1
        assert summary["tasks_failed"] == 1

    def test_success_rate_calculation(self):
        """Test success rate calculation."""
        collector = MetricsCollector()

        # 3 successes, 1 failure = 75%
        collector.track_task_start("t1")
        collector.track_task_end("t1", success=True)

        collector.track_task_start("t2")
        collector.track_task_end("t2", success=True)

        collector.track_task_start("t3")
        collector.track_task_end("t3", success=True)

        collector.track_task_start("t4")
        collector.track_task_end("t4", success=False)

        summary = collector.get_summary()
        assert summary["success_rate"] == 75.0

    def test_timing_report(self):
        """Test timing report generation."""
        collector = MetricsCollector()

        collector.track_task_start("task1")
        time.sleep(0.01)
        collector.track_task_end("task1", success=True)

        report = collector.get_timing_report()

        assert isinstance(report, str)
        assert "task1" in report
        assert "succeeded" in report or "Task Timing" in report

    def test_performance_metrics(self):
        """Test performance metrics."""
        collector = MetricsCollector()

        collector.track_task_start("slow")
        time.sleep(0.02)
        collector.track_task_end("slow", success=True)

        collector.track_task_start("fast")
        time.sleep(0.01)
        collector.track_task_end("fast", success=True)

        metrics = collector.get_performance_metrics()

        assert "total_execution_time" in metrics
        assert "average_task_time" in metrics
        assert "fastest_task_time" in metrics
        assert "slowest_task_time" in metrics
        assert "task_count" in metrics
        assert "success_rate" in metrics

        # Slowest should be > fastest
        assert metrics["slowest_task_time"] > metrics["fastest_task_time"]

    def test_reset(self):
        """Test resetting metrics."""
        collector = MetricsCollector()

        collector.track_task_start("task1")
        collector.track_task_end("task1", success=True)

        assert collector.task_count == 1

        collector.reset()

        assert collector.task_count == 0
        assert collector.success_count == 0
        assert collector.failure_count == 0
        assert len(collector.task_timings) == 0

    def test_no_tasks_summary(self):
        """Test summary with no tasks."""
        collector = MetricsCollector()
        summary = collector.get_summary()

        assert summary["tasks_executed"] == 0
        assert summary["success_rate"] == 0

    def test_track_unstarted_task_end(self):
        """Test ending task that wasn't started."""
        collector = MetricsCollector()

        # Should not crash, just ignore
        collector.track_task_end("nonexistent", success=True)

        assert collector.task_count == 0
