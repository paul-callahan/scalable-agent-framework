"""
AgentGraph class for the agentic framework.

AgentGraph represents an immutable graph template that defines the structure
of tasks and plans, along with their connections and flow control.
"""

import json
import uuid
from typing import Any, Dict, List, Optional, Set, Union

from .edge import Edge, EdgeType
from .task import Task
from .plan import Plan


class AgentGraph:
    """
    Immutable graph template for agent orchestration.
    
    AgentGraph defines the structure of tasks and plans, along with their
    connections and flow control. It includes semantic versioning and validation.
    """
    
    def __init__(self, 
                 tenant_id: str,
                 nodes: Dict[str, Union[Task, Plan]],
                 edges: List[Edge],
                 version: str = "1.0.0",
                 metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize a new AgentGraph.
        
        Args:
            tenant_id: Tenant identifier for multi-tenancy
            nodes: Dictionary mapping node IDs to Task/Plan instances
            edges: List of Edge instances defining connections
            version: Semantic version of the graph
            metadata: Optional metadata for the graph
        """
        self.tenant_id = tenant_id
        self.nodes = nodes
        self.edges = edges
        self.version = version
        self.metadata = metadata or {}
        self.id = str(uuid.uuid4())
        
        # Validate the graph structure
        self._validate()
    
    def _validate(self) -> None:
        """
        Validate the graph structure.
        
        Raises:
            ValueError: If the graph is invalid
        """
        # Check for empty graph
        if not self.nodes:
            raise ValueError("Graph cannot be empty - must contain at least one node")
        
        if not self.edges:
            raise ValueError("Graph cannot be empty - must contain at least one edge")
        
        # Check for minimum viable graph structure
        self._validate_minimum_structure()
        
        # Check that all edges reference valid nodes
        node_ids = set(self.nodes.keys())
        for edge in self.edges:
            if edge.source_id not in node_ids:
                raise ValueError(f"Edge source {edge.source_id} not found in nodes")
            if edge.target_id not in node_ids:
                raise ValueError(f"Edge target {edge.target_id} not found in nodes")
        
        # Check for cycles (improved cycle detection)
        if self._has_cycles():
            raise ValueError("Graph contains cycles")
    
    def _validate_minimum_structure(self) -> None:
        """
        Validate that the graph has a minimum viable structure.
        
        A minimum viable graph should have:
        1. At least one start node (node with no incoming edges)
        2. At least one end node (node with no outgoing edges)
        3. All nodes should be reachable from start nodes
        4. All nodes should be able to reach end nodes
        5. No isolated nodes (no incoming and no outgoing edges)
        6. No dead-end paths (nodes that are not end nodes and cannot reach any end node)
        
        Raises:
            ValueError: If the graph doesn't meet minimum structure requirements
        """
        start_nodes = self.get_start_nodes()
        end_nodes = self.get_end_nodes()
        
        if not start_nodes:
            raise ValueError("Graph must have at least one start node (node with no incoming edges)")
        
        if not end_nodes:
            raise ValueError("Graph must have at least one end node (node with no outgoing edges)")
        
        # Check for isolated nodes
        isolated_nodes = self._get_isolated_nodes()
        if isolated_nodes:
            raise ValueError(f"Graph contains isolated nodes (no incoming or outgoing edges): {isolated_nodes}")
        
        # Check that all nodes are reachable from start nodes
        reachable_nodes = self._get_reachable_nodes(start_nodes)
        unreachable_nodes = set(self.nodes.keys()) - reachable_nodes
        if unreachable_nodes:
            raise ValueError(f"Nodes {unreachable_nodes} are not reachable from any start node")
        
        # Check that all nodes can reach end nodes
        nodes_that_reach_ends = self._get_nodes_that_reach_targets(end_nodes)
        nodes_that_cant_reach_ends = set(self.nodes.keys()) - nodes_that_reach_ends
        if nodes_that_cant_reach_ends:
            raise ValueError(f"Nodes {nodes_that_cant_reach_ends} cannot reach any end node")
        
        # Check for dead-end paths: nodes that are not end nodes and cannot reach any end node
        dead_end_nodes = []
        for node_id in self.nodes:
            if node_id in end_nodes:
                continue
            # For each node, see if it can reach any end node
            reachable_from_node = self._get_reachable_nodes([node_id])
            if not (set(end_nodes) & reachable_from_node):
                dead_end_nodes.append(node_id)
        if dead_end_nodes:
            raise ValueError(f"Nodes {dead_end_nodes} are dead ends (cannot reach any end node and are not end nodes themselves)")
    
    def _get_reachable_nodes(self, start_nodes: List[str]) -> Set[str]:
        """
        Get all nodes reachable from the given start nodes using BFS.
        
        Args:
            start_nodes: List of starting node IDs
            
        Returns:
            Set of reachable node IDs
        """
        reachable = set(start_nodes)
        queue = list(start_nodes)
        
        while queue:
            current = queue.pop(0)
            for edge in self.edges:
                if edge.source_id == current and edge.target_id not in reachable:
                    reachable.add(edge.target_id)
                    queue.append(edge.target_id)
        
        return reachable
    
    def _get_nodes_that_reach_targets(self, target_nodes: List[str]) -> Set[str]:
        """
        Get all nodes that can reach the given target nodes using reverse BFS.
        
        Args:
            target_nodes: List of target node IDs
            
        Returns:
            Set of node IDs that can reach the targets
        """
        can_reach = set(target_nodes)
        queue = list(target_nodes)
        
        while queue:
            current = queue.pop(0)
            for edge in self.edges:
                if edge.target_id == current and edge.source_id not in can_reach:
                    can_reach.add(edge.source_id)
                    queue.append(edge.source_id)
        
        return can_reach
    
    def _has_cycles(self) -> bool:
        """
        Check if the graph contains cycles using improved DFS with self-loop detection.
        
        This improved algorithm handles:
        - Self-loops (edges from a node to itself)
        - Complex cycle patterns
        - Multiple cycles in the same graph
        
        Returns:
            True if cycles are found, False otherwise
        """
        # First, check for self-loops
        for edge in self.edges:
            if edge.source_id == edge.target_id:
                return True
        
        # Use DFS with recursion stack for cycle detection
        visited = set()
        rec_stack = set()
        
        def dfs(node_id: str, path: List[str]) -> bool:
            """
            DFS function to detect cycles.
            
            Args:
                node_id: Current node being visited
                path: Current path from root to this node
                
            Returns:
                True if a cycle is found, False otherwise
            """
            if node_id in rec_stack:
                # Found a back edge - cycle detected
                cycle_start = path.index(node_id)
                cycle_path = path[cycle_start:] + [node_id]
                return True
            
            if node_id in visited:
                return False
            
            visited.add(node_id)
            rec_stack.add(node_id)
            path.append(node_id)
            
            # Get all outgoing edges from current node
            outgoing_edges = [edge for edge in self.edges if edge.source_id == node_id]
            
            for edge in outgoing_edges:
                if dfs(edge.target_id, path):
                    return True
            
            # Backtrack
            rec_stack.remove(node_id)
            path.pop()
            return False
        
        # Check each connected component
        for node_id in self.nodes:
            if node_id not in visited:
                if dfs(node_id, []):
                    return True
        
        return False
    
    def _get_cycle_path(self) -> Optional[List[str]]:
        """
        Get the path of a cycle if one exists.
        
        Returns:
            List of node IDs forming a cycle, or None if no cycle exists
        """
        visited = set()
        rec_stack = set()
        
        def dfs(node_id: str, path: List[str]) -> Optional[List[str]]:
            if node_id in rec_stack:
                cycle_start = path.index(node_id)
                return path[cycle_start:] + [node_id]
            
            if node_id in visited:
                return None
            
            visited.add(node_id)
            rec_stack.add(node_id)
            path.append(node_id)
            
            outgoing_edges = [edge for edge in self.edges if edge.source_id == node_id]
            
            for edge in outgoing_edges:
                cycle_path = dfs(edge.target_id, path)
                if cycle_path:
                    return cycle_path
            
            rec_stack.remove(node_id)
            path.pop()
            return None
        
        for node_id in self.nodes:
            if node_id not in visited:
                cycle_path = dfs(node_id, [])
                if cycle_path:
                    return cycle_path
        
        return None
    
    def get_graph_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive statistics about the graph structure.
        
        Returns:
            Dictionary containing graph statistics
        """
        start_nodes = self.get_start_nodes()
        end_nodes = self.get_end_nodes()
        isolated_nodes = self._get_isolated_nodes()
        
        # Calculate in-degree and out-degree for each node
        in_degree = {}
        out_degree = {}
        for node_id in self.nodes:
            in_degree[node_id] = len(self.get_incoming_edges(node_id))
            out_degree[node_id] = len(self.get_outgoing_edges(node_id))
        
        # Find nodes with highest in/out degree
        max_in_degree = max(in_degree.values()) if in_degree else 0
        max_out_degree = max(out_degree.values()) if out_degree else 0
        
        nodes_with_max_in = [node_id for node_id, degree in in_degree.items() if degree == max_in_degree]
        nodes_with_max_out = [node_id for node_id, degree in out_degree.items() if degree == max_out_degree]
        
        return {
            'total_nodes': len(self.nodes),
            'total_edges': len(self.edges),
            'start_nodes': start_nodes,
            'end_nodes': end_nodes,
            'isolated_nodes': isolated_nodes,
            'in_degree_stats': {
                'max_in_degree': max_in_degree,
                'nodes_with_max_in_degree': nodes_with_max_in,
                'all_in_degrees': in_degree
            },
            'out_degree_stats': {
                'max_out_degree': max_out_degree,
                'nodes_with_max_out_degree': nodes_with_max_out,
                'all_out_degrees': out_degree
            },
            'edge_type_distribution': self._get_edge_type_distribution(),
            'node_type_distribution': self._get_node_type_distribution()
        }
    
    def _get_isolated_nodes(self) -> List[str]:
        """
        Get nodes that have no incoming or outgoing edges.
        
        Returns:
            List of isolated node IDs
        """
        connected_nodes = set()
        for edge in self.edges:
            connected_nodes.add(edge.source_id)
            connected_nodes.add(edge.target_id)
        
        return [node_id for node_id in self.nodes if node_id not in connected_nodes]
    
    def _get_edge_type_distribution(self) -> Dict[str, int]:
        """
        Get the distribution of edge types in the graph.
        
        Returns:
            Dictionary mapping edge types to their counts
        """
        distribution = {}
        for edge in self.edges:
            edge_type = edge.edge_type.value
            distribution[edge_type] = distribution.get(edge_type, 0) + 1
        return distribution
    
    def _get_node_type_distribution(self) -> Dict[str, int]:
        """
        Get the distribution of node types in the graph.
        
        Returns:
            Dictionary mapping node types to their counts
        """
        task_count = 0
        plan_count = 0
        
        for node in self.nodes.values():
            if isinstance(node, Task):
                task_count += 1
            elif isinstance(node, Plan):
                plan_count += 1
        
        return {
            'tasks': task_count,
            'plans': plan_count
        }
    
    def validate_graph_properties(self) -> Dict[str, bool]:
        """
        Validate various graph properties and return results.
        
        Returns:
            Dictionary mapping property names to validation results
        """
        start_nodes = self.get_start_nodes()
        end_nodes = self.get_end_nodes()
        isolated_nodes = self._get_isolated_nodes()
        
        return {
            'has_start_nodes': len(start_nodes) > 0,
            'has_end_nodes': len(end_nodes) > 0,
            'has_isolated_nodes': len(isolated_nodes) > 0,
            'is_connected': len(isolated_nodes) == 0,
            'has_cycles': self._has_cycles(),
            'all_nodes_reachable': len(self._get_reachable_nodes(start_nodes)) == len(self.nodes) if start_nodes else False,
            'all_nodes_can_reach_ends': len(self._get_nodes_that_reach_targets(end_nodes)) == len(self.nodes) if end_nodes else False
        }
    
    def get_detailed_validation_report(self) -> Dict[str, Any]:
        """
        Get a detailed validation report with specific issues found.
        
        Returns:
            Dictionary containing detailed validation information
        """
        report = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'statistics': self.get_graph_statistics(),
            'properties': self.validate_graph_properties()
        }
        
        # Check for empty graph
        if not self.nodes:
            report['is_valid'] = False
            report['errors'].append("Graph is empty - no nodes defined")
        
        if not self.edges:
            report['is_valid'] = False
            report['errors'].append("Graph is empty - no edges defined")
        
        # Check for cycles
        if self._has_cycles():
            report['is_valid'] = False
            cycle_path = self._get_cycle_path()
            if cycle_path:
                report['errors'].append(f"Graph contains cycle: {' -> '.join(cycle_path)}")
            else:
                report['errors'].append("Graph contains cycles")
        
        # Check for isolated nodes
        isolated_nodes = self._get_isolated_nodes()
        if isolated_nodes:
            report['warnings'].append(f"Isolated nodes found: {isolated_nodes}")
        
        # Check for unreachable nodes
        start_nodes = self.get_start_nodes()
        if start_nodes:
            reachable_nodes = self._get_reachable_nodes(start_nodes)
            unreachable_nodes = set(self.nodes.keys()) - reachable_nodes
            if unreachable_nodes:
                report['errors'].append(f"Unreachable nodes: {unreachable_nodes}")
        
        # Check for nodes that can't reach ends
        end_nodes = self.get_end_nodes()
        if end_nodes:
            nodes_that_reach_ends = self._get_nodes_that_reach_targets(end_nodes)
            nodes_that_cant_reach_ends = set(self.nodes.keys()) - nodes_that_reach_ends
            if nodes_that_cant_reach_ends:
                report['errors'].append(f"Nodes that cannot reach any end node: {nodes_that_cant_reach_ends}")
        
        return report
    
    def get_start_nodes(self) -> List[str]:
        """
        Get the starting nodes (nodes with no incoming edges).
        
        Returns:
            List of node IDs that are starting points
        """
        incoming_edges = set()
        for edge in self.edges:
            incoming_edges.add(edge.target_id)
        
        return [node_id for node_id in self.nodes if node_id not in incoming_edges]
    
    def get_end_nodes(self) -> List[str]:
        """
        Get the ending nodes (nodes with no outgoing edges).
        
        Returns:
            List of node IDs that are ending points
        """
        outgoing_edges = set()
        for edge in self.edges:
            outgoing_edges.add(edge.source_id)
        
        return [node_id for node_id in self.nodes if node_id not in outgoing_edges]
    
    def get_outgoing_edges(self, node_id: str) -> List[Edge]:
        """
        Get all outgoing edges from a node.
        
        Args:
            node_id: ID of the source node
            
        Returns:
            List of outgoing edges
        """
        return [edge for edge in self.edges if edge.source_id == node_id]
    
    def get_incoming_edges(self, node_id: str) -> List[Edge]:
        """
        Get all incoming edges to a node.
        
        Args:
            node_id: ID of the target node
            
        Returns:
            List of incoming edges
        """
        return [edge for edge in self.edges if edge.target_id == node_id]
    
    def get_node(self, node_id: str) -> Optional[Union[Task, Plan]]:
        """
        Get a node by ID.
        
        Args:
            node_id: ID of the node to retrieve
            
        Returns:
            Task or Plan instance, or None if not found
        """
        return self.nodes.get(node_id)
    
    def serialize(self) -> Dict[str, Any]:
        """
        Serialize the graph to a dictionary.
        
        Note: Since Task and Plan classes are simplified abstract base classes,
        only the graph structure and metadata can be serialized, not the actual
        task/plan implementations.
        
        Returns:
            Dictionary representation of the graph structure
        """
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'version': self.version,
            'metadata': self.metadata,
            'nodes': {
                node_id: {
                    'type': 'task' if isinstance(node, Task) else 'plan',
                    'class_name': node.__class__.__name__
                }
                for node_id, node in self.nodes.items()
            },
            'edges': [edge.serialize() for edge in self.edges]
        }
    
    @classmethod
    def deserialize(cls, data: Dict[str, Any], node_registry: Dict[str, Union[Task, Plan]]) -> 'AgentGraph':
        """
        Deserialize a graph from a dictionary.
        
        Note: Since Task and Plan classes are simplified abstract base classes,
        you must provide a node_registry mapping node IDs to actual Task/Plan instances.
        
        Args:
            data: Dictionary representation of the graph structure
            node_registry: Dictionary mapping node IDs to Task/Plan instances
            
        Returns:
            AgentGraph instance
            
        Raises:
            ValueError: If node_registry doesn't contain all required nodes
        """
        # Validate that all nodes are provided in the registry
        required_nodes = set(data['nodes'].keys())
        provided_nodes = set(node_registry.keys())
        
        if required_nodes != provided_nodes:
            missing = required_nodes - provided_nodes
            extra = provided_nodes - required_nodes
            error_msg = []
            if missing:
                error_msg.append(f"Missing nodes in registry: {missing}")
            if extra:
                error_msg.append(f"Extra nodes in registry: {extra}")
            raise ValueError("; ".join(error_msg))
        
        # Validate node types match
        for node_id, node_data in data['nodes'].items():
            node = node_registry[node_id]
            expected_type = node_data['type']
            actual_type = 'task' if isinstance(node, Task) else 'plan'
            if expected_type != actual_type:
                raise ValueError(f"Node {node_id} type mismatch: expected {expected_type}, got {actual_type}")
        
        # Reconstruct edges
        edges = [Edge.deserialize(edge_data) for edge_data in data['edges']]
        
        graph = cls(
            tenant_id=data['tenant_id'],
            nodes=node_registry,
            edges=edges,
            version=data['version'],
            metadata=data.get('metadata', {})
        )
        graph.id = data['id']
        return graph
    
    def __repr__(self) -> str:
        """String representation of the graph."""
        return f"AgentGraph(id={self.id}, nodes={len(self.nodes)}, edges={len(self.edges)})" 
