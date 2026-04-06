"""
Socratic Workflow - Production-grade workflow orchestration system.

Provides workflow definition, execution, cost tracking, and performance analytics.
"""

from .analytics import MetricsCollector
from .cost import CostTracker
from .workflow import SimpleTask, Task, Workflow, WorkflowEngine, WorkflowResult
from .workflow_templates import WorkflowTemplate, WorkflowTemplateLibrary

__version__ = "0.1.0"

__all__ = [
    # Workflow
    "Workflow",
    "WorkflowEngine",
    "WorkflowResult",
    "Task",
    "SimpleTask",
    # Workflow Templates
    "WorkflowTemplate",
    "WorkflowTemplateLibrary",
    # Cost tracking
    "CostTracker",
    # Analytics
    "MetricsCollector",
]
