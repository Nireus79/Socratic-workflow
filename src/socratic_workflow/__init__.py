from __future__ import annotations

"""
Socratic Workflow - Workflow Definition and Management

Extracted from Socrates v1.3.3

Provides workflow definition, path enumeration, and cost/risk calculation
for optimized project phase navigation.

Main Components:
    - WorkflowDefinition: Complete workflow structure with nodes and edges
    - WorkflowNode: Individual workflow step/decision point
    - WorkflowEdge: Transition between workflow nodes
    - WorkflowPath: Complete path through workflow with metrics
    - WorkflowApprovalRequest: Request for workflow execution approval
    - WorkflowExecutionState: State tracking during workflow execution
    - PathDecisionStrategy: Strategy for selecting optimal paths
    - WorkflowNodeType: Types of workflow nodes
"""

from .workflow import (
    PathDecisionStrategy,
    WorkflowApprovalRequest,
    WorkflowDefinition,
    WorkflowEdge,
    WorkflowExecutionState,
    WorkflowNode,
    WorkflowNodeType,
    WorkflowPath,
)

__version__ = "0.1.3"
__all__ = [
    "WorkflowDefinition",
    "WorkflowNode",
    "WorkflowEdge",
    "WorkflowPath",
    "WorkflowApprovalRequest",
    "WorkflowExecutionState",
    "WorkflowNodeType",
    "PathDecisionStrategy",
]
