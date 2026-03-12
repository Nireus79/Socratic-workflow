"""
Socratic Workflow - Production-grade workflow orchestration system.

Provides workflow definition, execution, cost tracking, and performance analytics.
"""

from .analytics import MetricsCollector
from .cost import CostTracker
from .workflow import SimpleTask, Task, Workflow, WorkflowEngine, WorkflowResult

__version__ = "0.1.0"

__all__ = [
    # Workflow
    "Workflow",
    "WorkflowEngine",
    "WorkflowResult",
    "Task",
    "SimpleTask",
    # Cost tracking
    "CostTracker",
    # Analytics
    "MetricsCollector",
]
