"""Workflow Path Finder - DFS-based algorithm to enumerate all valid workflow paths."""

import logging
from typing import Any, Dict, List, Set, Tuple

logger = logging.getLogger(__name__)


class PathFinder:
    """Find all valid paths through a workflow graph using DFS"""

    def __init__(self, workflow):
        """Initialize path finder with a workflow definition."""
        self.workflow = workflow
        self.adjacency_list = self._build_adjacency_list()
        logger.debug(
            f"PathFinder initialized for workflow {getattr(workflow, 'id', 'unknown')} "
            f"with {len(getattr(workflow, 'nodes', {}))} nodes"
        )

    def find_all_paths(self) -> List[Any]:
        """Find all valid paths from start node to any end node using DFS."""
        logger.debug(
            f"Finding all paths from '{getattr(self.workflow, 'start_node', None)}' "
            f"to {getattr(self.workflow, 'end_nodes', [])}"
        )

        all_paths: List[Any] = []
        start_node = getattr(self.workflow, "start_node", None)
        end_nodes = getattr(self.workflow, "end_nodes", [])

        if not start_node or not end_nodes:
            logger.warning("Workflow missing start or end nodes")
            return all_paths

        for end_node in end_nodes:
            paths = self._dfs_paths(
                current=start_node,
                target=end_node,
                visited=set(),
                current_path_nodes=[],
                current_path_edges=[],
            )
            all_paths.extend(paths)

        # Convert raw paths to WorkflowPath-like objects
        workflow_paths = [self._create_path(nodes, edges) for nodes, edges in all_paths]

        logger.info(f"Path enumeration complete: {len(workflow_paths)} paths found")

        return workflow_paths

    def _dfs_paths(
        self,
        current: str,
        target: str,
        visited: Set[str],
        current_path_nodes: List[str],
        current_path_edges: List[str],
    ) -> List[Tuple[List[str], List[str]]]:
        """Recursively find all paths from current node to target using DFS."""
        visited.add(current)
        current_path_nodes.append(current)

        logger.debug(f"DFS at node {current}")

        if current == target:
            logger.debug(f"Found complete path: {current_path_nodes}")
            return [(list(current_path_nodes), list(current_path_edges))]

        all_paths = []
        neighbors = self.adjacency_list.get(current, [])

        for neighbor_id, edge_id in neighbors:
            if neighbor_id not in visited:
                new_visited = visited.copy()
                new_edges = current_path_edges + [edge_id]
                paths = self._dfs_paths(
                    current=neighbor_id,
                    target=target,
                    visited=new_visited,
                    current_path_nodes=list(current_path_nodes),
                    current_path_edges=new_edges,
                )
                all_paths.extend(paths)

        return all_paths

    def _build_adjacency_list(self) -> Dict[str, List[Tuple[str, str]]]:
        """Build adjacency list representation of the graph."""
        adjacency_list: Dict[str, List[Tuple[str, str]]] = {}
        edges = getattr(self.workflow, "edges", [])

        for edge in edges:
            from_node = getattr(edge, "from_node", "")
            to_node = getattr(edge, "to_node", "")

            if from_node not in adjacency_list:
                adjacency_list[from_node] = []

            adjacency_list[from_node].append((to_node, f"{from_node}-{to_node}"))
            logger.debug(f"Edge: {from_node} -> {to_node}")

        logger.debug(f"Built adjacency list with {len(adjacency_list)} nodes")
        return adjacency_list

    def _create_path(self, nodes: List[str], edges: List[str]):
        """Create a path object from node and edge lists."""
        path_id = f"path_{len(nodes)}nodes"

        # Create a simple path object
        class WorkflowPath:
            def __init__(self, path_id, nodes, edges):
                self.id = path_id
                self.nodes = nodes
                self.edges = edges
                self.total_cost = 0
                self.risk_score = 0.0
                self.quality_score = 0.0
                self.roi_score = 0.0
                self.expected_gain = 0.0
                self.incompleteness_risk = 0.0
                self.complexity_risk = 0.0
                self.rework_probability = 0.0

        return WorkflowPath(path_id, nodes, edges)
