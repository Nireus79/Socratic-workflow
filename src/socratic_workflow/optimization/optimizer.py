"""
Workflow Optimizer - Pure algorithmic engine for workflow path optimization.

Enumerates all workflow paths, calculates metrics (cost, risk, quality), and
selects the optimal path based on configurable strategies.

This module is domain-agnostic and works with any workflow definition.
"""

import logging
from typing import List

from socratic_workflow.models import PathDecisionStrategy, WorkflowPath, WorkflowDefinition
from socratic_workflow.optimization.cost_calculator import CostCalculator
from socratic_workflow.optimization.path_finder import PathFinder
from socratic_workflow.optimization.risk_calculator import RiskCalculator

logger = logging.getLogger(__name__)


class WorkflowOptimizer:
    """Orchestrates workflow optimization including path enumeration and selection"""

    def __init__(self):
        """Initialize optimizer with calculation components"""
        self.path_finder_class = PathFinder
        self.cost_calculator = CostCalculator()
        self.risk_calculator = RiskCalculator()

        logger.debug("WorkflowOptimizer initialized")

    def optimize_workflow(
        self,
        workflow: WorkflowDefinition,
        context: dict = None,
        strategy: PathDecisionStrategy = PathDecisionStrategy.BALANCED,
        requested_by: str = "system",
    ) -> dict:
        """
        Main entry point for workflow optimization.

        Enumerates all paths, calculates metrics, selects optimal path,
        and returns optimization result.

        Args:
            workflow: WorkflowDefinition to optimize
            context: Optional context dictionary for cost/risk calculations
            strategy: PathDecisionStrategy to use for selection
            requested_by: User/agent requesting optimization

        Returns:
            Dict with all paths and recommendation

        Raises:
            ValueError: If workflow is invalid or no paths found
        """
        logger.info(
            f"Starting workflow optimization for {workflow.id} "
            f"using strategy {strategy.value if hasattr(strategy, 'value') else strategy}"
        )

        # Step 1: Find all paths
        logger.debug("Step 1: Enumerating workflow paths")
        all_paths = self._find_all_paths(workflow)

        if not all_paths:
            logger.error(f"No paths found for workflow {workflow.id}")
            raise ValueError(f"Workflow {workflow.id} has no valid paths")

        logger.info(f"Found {len(all_paths)} paths for workflow")

        # Step 2: Calculate metrics for each path
        logger.debug("Step 2: Calculating metrics for each path")
        all_paths = self._calculate_path_metrics(all_paths, workflow, context or {})

        # Step 3: Select optimal path
        logger.debug("Step 3: Selecting optimal path")
        recommended_path = self._select_optimal_path(all_paths, strategy)

        # Step 4: Return optimization result
        logger.debug("Step 4: Creating optimization result")

        logger.info(
            f"Workflow optimization complete. "
            f"Recommended path: {recommended_path.id} "
            f"(cost: {recommended_path.total_cost} tokens, "
            f"risk: {recommended_path.risk_score:.1f}%)"
        )

        return {
            "workflow_id": workflow.id,
            "all_paths": [self._path_to_dict(p) for p in all_paths],
            "recommended_path": self._path_to_dict(recommended_path),
            "strategy": strategy.value if hasattr(strategy, 'value') else str(strategy),
            "requested_by": requested_by,
            "status": "optimized",
        }

    def _find_all_paths(self, workflow: WorkflowDefinition) -> List[WorkflowPath]:
        """
        Find all valid paths through workflow graph.

        Args:
            workflow: WorkflowDefinition

        Returns:
            List of WorkflowPath objects

        Raises:
            ValueError: If workflow is invalid
        """
        if not workflow.start_node:
            raise ValueError("Workflow must have a start_node")

        if not workflow.end_nodes:
            raise ValueError("Workflow must have end_nodes")

        finder = self.path_finder_class(workflow)
        return finder.find_all_paths()

    def _calculate_path_metrics(
        self, paths: List[WorkflowPath], workflow: WorkflowDefinition, context: dict
    ) -> List[WorkflowPath]:
        """
        Calculate cost, risk, and quality metrics for all paths.

        Args:
            paths: List of paths to evaluate
            workflow: WorkflowDefinition
            context: Context dictionary for calculations

        Returns:
            Updated paths with calculated metrics
        """
        for path in paths:
            # Calculate cost
            cost_metrics = self.cost_calculator.calculate_path_cost(path, workflow)
            path.total_cost = cost_metrics["total_tokens"]
            path.cost_usd = cost_metrics.get("total_cost_usd", 0.0)

            # Calculate risk
            risk_metrics = self.risk_calculator.calculate_path_risk(path, workflow, context)
            path.risk_score = risk_metrics["risk_score"]
            path.incompleteness_risk = risk_metrics.get("incompleteness_risk", 0.0)
            path.complexity_risk = risk_metrics.get("complexity_risk", 0.0)
            path.rework_probability = risk_metrics.get("rework_probability", 0.0)

            # Calculate quality and ROI
            path.quality_score = self._calculate_quality_score(path)
            path.expected_gain = self._calculate_expected_gain(path)
            path.roi_score = self._calculate_roi(path, cost_metrics["total_tokens"], path.expected_gain)

            logger.debug(
                f"Path {path.id}: {path.total_cost} tokens, "
                f"risk={path.risk_score:.1f}, quality={path.quality_score:.1f}, "
                f"roi={path.roi_score:.2f}"
            )

        return paths

    def _select_optimal_path(self, paths: List[WorkflowPath], strategy) -> WorkflowPath:
        """
        Select best path based on strategy.

        Strategies:
        - MINIMIZE_COST: Lowest token count
        - MINIMIZE_RISK: Lowest risk score
        - BALANCED: 50% cost, 30% risk, 20% quality
        - MAXIMIZE_QUALITY: Highest quality score
        - USER_CHOICE: Return first (user will choose)

        Args:
            paths: List of evaluated paths
            strategy: Selection strategy

        Returns:
            Recommended WorkflowPath
        """
        if not paths:
            raise ValueError("Cannot select from empty path list")

        strategy_str = strategy.value if hasattr(strategy, 'value') else str(strategy).lower()

        if "minimize_cost" in strategy_str or strategy_str == "minimize_cost":
            return min(paths, key=lambda p: p.total_cost)

        elif "minimize_risk" in strategy_str or strategy_str == "minimize_risk":
            return min(paths, key=lambda p: p.risk_score)

        elif "maximize_quality" in strategy_str or strategy_str == "maximize_quality":
            return max(paths, key=lambda p: p.quality_score)

        elif "balanced" in strategy_str or strategy_str == "balanced":
            # Normalize metrics and combine: 50% cost, 30% risk, 20% quality
            scores = []
            for path in paths:
                normalized_cost = self._normalize_value(
                    path.total_cost, [p.total_cost for p in paths], invert=True
                )
                normalized_risk = self._normalize_value(
                    path.risk_score, [p.risk_score for p in paths], invert=True
                )
                normalized_quality = self._normalize_value(
                    path.quality_score, [p.quality_score for p in paths]
                )

                combined_score = (
                    (normalized_cost * 0.5) + (normalized_risk * 0.3) + (normalized_quality * 0.2)
                )

                scores.append((path, combined_score))
                logger.debug(
                    f"Path {path.id} balanced score: {combined_score:.3f} "
                    f"(cost={normalized_cost:.3f}, risk={normalized_risk:.3f}, "
                    f"quality={normalized_quality:.3f})"
                )

            # Select path with highest combined score
            best_path = max(scores, key=lambda x: x[1])[0]
            return best_path

        else:  # USER_CHOICE or default
            return paths[0]

    def _calculate_quality_score(self, path: WorkflowPath) -> float:
        """
        Calculate quality score for a path.

        Quality = coverage + depth - risk
        Higher is better.

        Args:
            path: WorkflowPath to score

        Returns:
            Quality score (0-100)
        """
        # Base quality from coverage
        coverage_quality = 100.0 - getattr(path, 'incompleteness_risk', 0)

        # Depth/complexity adds quality
        complexity_quality = getattr(path, 'complexity_risk', 0) * 0.5

        # Risk reduces quality
        risk_penalty = getattr(path, 'risk_score', 0) * 0.3

        quality = coverage_quality + complexity_quality - risk_penalty
        quality = max(0.0, min(100.0, quality))  # Clamp to 0-100

        return quality

    def _calculate_expected_gain(self, path: WorkflowPath) -> float:
        """
        Estimate expected gain/value from this path.

        Args:
            path: WorkflowPath

        Returns:
            Expected gain (0-100)
        """
        # Paths with better coverage gain more value
        coverage_gain = (100.0 - getattr(path, 'incompleteness_risk', 0)) * 0.7

        # Paths with good complexity gain more
        complexity_gain = min(30.0, getattr(path, 'complexity_risk', 0) * 0.3)

        expected_gain = coverage_gain + complexity_gain
        expected_gain = min(100.0, expected_gain)

        return expected_gain

    def _calculate_roi(self, path: WorkflowPath, tokens: int, gain: float) -> float:
        """
        Calculate ROI (return on investment) for a path.

        ROI = gain / tokens (points per token)

        Args:
            path: WorkflowPath
            tokens: Token cost
            gain: Expected gain

        Returns:
            ROI score (higher is better)
        """
        if tokens == 0:
            return 0.0

        roi = gain / (tokens / 1000.0)  # Points per 1000 tokens
        return round(roi, 2)

    @staticmethod
    def _normalize_value(value: float, all_values: List[float], invert: bool = False) -> float:
        """
        Normalize a value to 0-1 range based on min/max of all values.

        Args:
            value: Value to normalize
            all_values: All values for computing min/max
            invert: If True, invert (1 - normalized) for "lower is better" metrics

        Returns:
            Normalized value (0-1)
        """
        if not all_values:
            return 0.5

        min_val = min(all_values)
        max_val = max(all_values)

        if max_val == min_val:
            normalized = 0.5
        else:
            normalized = (value - min_val) / (max_val - min_val)

        if invert:
            normalized = 1.0 - normalized

        return normalized

    @staticmethod
    def _path_to_dict(path: WorkflowPath) -> dict:
        """Convert WorkflowPath to dictionary for serialization"""
        return {
            "id": path.id,
            "nodes": getattr(path, 'nodes', []),
            "edges": getattr(path, 'edges', []),
            "total_cost": getattr(path, 'total_cost', 0),
            "risk_score": getattr(path, 'risk_score', 0.0),
            "quality_score": getattr(path, 'quality_score', 0.0),
            "roi_score": getattr(path, 'roi_score', 0.0),
            "expected_gain": getattr(path, 'expected_gain', 0.0),
        }
