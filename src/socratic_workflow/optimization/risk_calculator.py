"""Workflow Risk Calculator - Multi-dimensional risk assessment for workflow paths."""

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class RiskCalculator:
    """Calculate comprehensive risk assessment for workflow paths"""

    # Risk component weights (must sum to 1.0)
    INCOMPLETENESS_WEIGHT = 0.4
    COMPLEXITY_WEIGHT = 0.3
    REWORK_WEIGHT = 0.3

    def __init__(self):
        """Initialize risk calculator"""
        logger.debug("RiskCalculator initialized")

    def calculate_path_risk(
        self, path: Any, workflow: Any, context: Optional[Dict[Any, Any]] = None
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive risk score for a workflow path.

        Args:
            path: WorkflowPath to assess
            workflow: WorkflowDefinition containing node metadata
            context: Optional context dictionary

        Returns:
            Dict with risk metrics
        """
        context = context or {}
        logger.debug(f"Calculating risk for path {getattr(path, 'id', 'unknown')}")

        incompleteness_risk = self._calculate_incompleteness_risk(path, workflow, context)
        complexity_risk = self._calculate_complexity_risk(path, workflow)
        rework_risk = self._calculate_rework_probability(
            path, workflow, context, incompleteness_risk
        )

        risk_score = (
            (incompleteness_risk * self.INCOMPLETENESS_WEIGHT)
            + (complexity_risk * self.COMPLEXITY_WEIGHT)
            + (rework_risk * self.REWORK_WEIGHT)
        )

        logger.info(
            f"Path risk: overall={risk_score:.1f}, incompleteness={incompleteness_risk:.1f}, "
            f"complexity={complexity_risk:.1f}, rework={rework_risk:.1f}"
        )

        return {
            "risk_score": risk_score,
            "incompleteness_risk": incompleteness_risk,
            "complexity_risk": complexity_risk,
            "rework_probability": rework_risk,
            "missing_categories": [],
        }

    def _calculate_incompleteness_risk(self, path: Any, workflow: Any, context: dict) -> float:
        """Calculate incompleteness risk (coverage gaps)."""
        # Estimate based on path length and coverage metadata
        try:
            nodes = getattr(path, "nodes", [])
            total_nodes = len(getattr(workflow, "nodes", {}))

            if total_nodes == 0:
                return 0.0

            coverage = len(nodes) / total_nodes * 100
            incompleteness = max(0, 100 - coverage)

            return incompleteness
        except Exception as e:
            logger.error(f"Error calculating incompleteness risk: {e}")
            return 50.0

    def _calculate_complexity_risk(self, path: Any, workflow: Any) -> float:
        """Calculate complexity risk (technical difficulty)."""
        complexity_score = 0.0
        question_count = 0

        nodes = getattr(path, "nodes", [])
        workflow_nodes = getattr(workflow, "nodes", {})

        for node_id in nodes:
            if isinstance(workflow_nodes, dict) and node_id in workflow_nodes:
                node = workflow_nodes[node_id]
                node_type = getattr(
                    getattr(node, "node_type", None), "value", str(getattr(node, "node_type", ""))
                )

                if node_type == "question_set" or "question" in str(node_type).lower():
                    question_count += 1
                    complexity_score += 20.0
                elif node_type == "analysis" or "analysis" in str(node_type).lower():
                    complexity_score += 30.0
                elif node_type == "validation" or "validation" in str(node_type).lower():
                    complexity_score += 15.0

        complexity_risk = min(100.0, complexity_score)
        logger.debug(f"Complexity risk: {complexity_risk:.1f}%")

        return complexity_risk

    def _calculate_rework_probability(
        self, path: Any, workflow: Any, context: dict, incompleteness_risk: float
    ) -> float:
        """Calculate rework probability."""
        rework_base = incompleteness_risk * 0.8

        nodes = getattr(path, "nodes", [])
        path_length = len(nodes)
        length_risk = min(20.0, path_length * 2)

        rework_probability = min(100.0, rework_base + length_risk)

        logger.debug(
            f"Rework probability: base={rework_base:.1f}%, length={length_risk:.1f}% = {rework_probability:.1f}%"
        )

        return rework_probability
