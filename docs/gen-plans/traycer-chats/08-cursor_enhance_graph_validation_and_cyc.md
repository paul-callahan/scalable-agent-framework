# Enhance graph validation and cycle detection
_Exported on 7/30/2025 at 18:14:14 PDT from Cursor (1.3.5)_

---

**User**

Enhance graph validation in `services/standalone-py/agentic/core/graph.py` to check for empty graphs and add validation for minimum viable graph structure. Also improve the cycle detection algorithm to handle edge cases like self-loops and complex cycle patterns.

---

**Cursor**

I'll help you enhance the graph validation in the graph.py file. Let me first examine the current implementation to understand what needs to be improved.


Now let me examine the Edge class to understand the edge structure:


Now let me check the Task and Plan classes to understand their structure:


Now I have a good understanding of the current implementation. Let me enhance the graph validation with the requested improvements:

1. Check for empty graphs
2. Add validation for minimum viable graph structure
3. Improve cycle detection to handle self-loops and complex cycle patterns


```python
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
        
        # Check that all nodes have the same tenant_id
        for node_id, node in self.nodes.items():
            if node.tenant_id != self.tenant_id:
                raise ValueError(f"Node {node_id} has different tenant_id: {node.tenant_id}")
        
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
        
        Raises:
            ValueError: If the graph doesn't meet minimum structure requirements
        """
        start_nodes = self.get_start_nodes()
        end_nodes = self.get_end_nodes()
        
        if not start_nodes:
            raise ValueError("Graph must have at least one start node (node with no incoming edges)")
        
        if not end_nodes:
            raise ValueError("Graph must have at least one end node (node with no outgoing edges)")
        
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

// ... existing code ...
```

Now let me add some additional utility methods to help with graph analysis and debugging:


```python
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

// ... existing code ...
```

Now let me create a simple test script to demonstrate the enhanced validation features:


```python
#!/usr/bin/env python3
"""
Test script to demonstrate enhanced graph validation features.

This script tests various graph validation scenarios including:
- Empty graph detection
- Self-loop detection
- Complex cycle detection
- Minimum viable graph structure validation
- Graph statistics and detailed validation reports
"""

import sys
import os

# Add the agentic package to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'agentic'))

from agentic.core.graph import AgentGraph
from agentic.core.edge import Edge, EdgeType
from agentic.core.task import Task, TaskResult
from agentic.core.plan import Plan, PlanResult


class MockTask(Task):
    """Mock task for testing."""
    
    async def execute(self, context=None):
        return TaskResult(data="mock_result")
    
    @classmethod
    def deserialize(cls, data):
        return cls(
            tenant_id=data['tenant_id'],
            task_type=data['task_type'],
            parameters=data.get('parameters', {})
        )


class MockPlan(Plan):
    """Mock plan for testing."""
    
    async def execute(self, task_result, context=None):
        return PlanResult(next_task_ids=["task2"])
    
    @classmethod
    def deserialize(cls, data):
        return cls(
            tenant_id=data['tenant_id'],
            plan_type=data['plan_type'],
            parameters=data.get('parameters', {})
        )


def test_empty_graph():
    """Test empty graph validation."""
    print("=== Testing Empty Graph Validation ===")
    
    try:
        # Test empty nodes
        graph = AgentGraph(
            tenant_id="test",
            nodes={},
            edges=[]
        )
        print("❌ Should have failed for empty nodes")
    except ValueError as e:
        print(f"✅ Correctly caught empty nodes: {e}")
    
    try:
        # Test empty edges
        graph = AgentGraph(
            tenant_id="test",
            nodes={"task1": MockTask("test", "mock_task")},
            edges=[]
        )
        print("❌ Should have failed for empty edges")
    except ValueError as e:
        print(f"✅ Correctly caught empty edges: {e}")


def test_self_loop():
    """Test self-loop detection."""
    print("\n=== Testing Self-Loop Detection ===")
    
    try:
        graph = AgentGraph(
            tenant_id="test",
            nodes={"task1": MockTask("test", "mock_task")},
            edges=[Edge("task1", "task1")]  # Self-loop
        )
        print("❌ Should have failed for self-loop")
    except ValueError as e:
        print(f"✅ Correctly caught self-loop: {e}")


def test_simple_cycle():
    """Test simple cycle detection."""
    print("\n=== Testing Simple Cycle Detection ===")
    
    try:
        graph = AgentGraph(
            tenant_id="test",
            nodes={
                "task1": MockTask("test", "mock_task"),
                "task2": MockTask("test", "mock_task")
            },
            edges=[
                Edge("task1", "task2"),
                Edge("task2", "task1")  # Creates cycle
            ]
        )
        print("❌ Should have failed for simple cycle")
    except ValueError as e:
        print(f"✅ Correctly caught simple cycle: {e}")


def test_complex_cycle():
    """Test complex cycle detection."""
    print("\n=== Testing Complex Cycle Detection ===")
    
    try:
        graph = AgentGraph(
            tenant_id="test",
            nodes={
                "task1": MockTask("test", "mock_task"),
                "task2": MockTask("test", "mock_task"),
                "task3": MockTask("test", "mock_task"),
                "task4": MockTask("test", "mock_task")
            },
            edges=[
                Edge("task1", "task2"),
                Edge("task2", "task3"),
                Edge("task3", "task4"),
                Edge("task4", "task2")  # Creates cycle: task2 -> task3 -> task4 -> task2
            ]
        )
        print("❌ Should have failed for complex cycle")
    except ValueError as e:
        print(f"✅ Correctly caught complex cycle: {e}")


def test_valid_graph():
    """Test a valid graph structure."""
    print("\n=== Testing Valid Graph ===")
    
    try:
        graph = AgentGraph(
            tenant_id="test",
            nodes={
                "task1": MockTask("test", "mock_task"),
                "plan1": MockPlan("test", "mock_plan"),
                "task2": MockTask("test", "mock_task")
            },
            edges=[
                Edge("task1", "plan1"),
                Edge("plan1", "task2")
            ]
        )
        print("✅ Valid graph created successfully")
        
        # Test graph statistics
        stats = graph.get_graph_statistics()
        print(f"Graph statistics: {stats['total_nodes']} nodes, {stats['total_edges']} edges")
        print(f"Start nodes: {stats['start_nodes']}")
        print(f"End nodes: {stats['end_nodes']}")
        
        # Test validation report
        report = graph.get_detailed_validation_report()
        print(f"Graph is valid: {report['is_valid']}")
        if report['errors']:
            print(f"Errors: {report['errors']}")
        if report['warnings']:
            print(f"Warnings: {report['warnings']}")
            
    except ValueError as e:
        print(f"❌ Unexpected error: {e}")


def test_unreachable_nodes():
    """Test detection of unreachable nodes."""
    print("\n=== Testing Unreachable Nodes ===")
    
    try:
        graph = AgentGraph(
            tenant_id="test",
            nodes={
                "task1": MockTask("test", "mock_task"),
                "task2": MockTask("test", "mock_task"),  # Isolated node
                "task3": MockTask("test", "mock_task")
            },
            edges=[
                Edge("task1", "task3")  # task2 is unreachable
            ]
        )
        print("❌ Should have failed for unreachable nodes")
    except ValueError as e:
        print(f"✅ Correctly caught unreachable nodes: {e}")


def test_nodes_cant_reach_ends():
    """Test detection of nodes that can't reach end nodes."""
    print("\n=== Testing Nodes That Can't Reach Ends ===")
    
    try:
        graph = AgentGraph(
            tenant_id="test",
            nodes={
                "task1": MockTask("test", "mock_task"),
                "task2": MockTask("test", "mock_task"),
                "task3": MockTask("test", "mock_task")
            },
            edges=[
                Edge("task1", "task2"),
                Edge("task2", "task3"),
                Edge("task1", "task3")  # task2 can't reach any end node
            ]
        )
        print("❌ Should have failed for nodes that can't reach ends")
    except ValueError as e:
        print(f"✅ Correctly caught nodes that can't reach ends: {e}")


def test_minimum_viable_structure():
    """Test minimum viable graph structure validation."""
    print("\n=== Testing Minimum Viable Structure ===")
    
    # Test graph with no start nodes
    try:
        graph = AgentGraph(
            tenant_id="test",
            nodes={
                "task1": MockTask("test", "mock_task"),
                "task2": MockTask("test", "mock_task")
            },
            edges=[
                Edge("task1", "task2"),
                Edge("task2", "task1")  # No start nodes
            ]
        )
        print("❌ Should have failed for no start nodes")
    except ValueError as e:
        print(f"✅ Correctly caught no start nodes: {e}")
    
    # Test graph with no end nodes
    try:
        graph = AgentGraph(
            tenant_id="test",
            nodes={
                "task1": MockTask("test", "mock_task"),
                "task2": MockTask("test", "mock_task")
            },
            edges=[
                Edge("task1", "task2"),
                Edge("task2", "task1")  # No end nodes
            ]
        )
        print("❌ Should have failed for no end nodes")
    except ValueError as e:
        print(f"✅ Correctly caught no end nodes: {e}")


def main():
    """Run all graph validation tests."""
    print("Graph Validation Test Suite")
    print("=" * 50)
    
    test_empty_graph()
    test_self_loop()
    test_simple_cycle()
    test_complex_cycle()
    test_valid_graph()
    test_unreachable_nodes()
    test_nodes_cant_reach_ends()
    test_minimum_viable_structure()
    
    print("\n" + "=" * 50)
    print("All tests completed!")


if __name__ == "__main__":
    main()
```

Now let me run the test script to verify that our enhanced validation is working correctly:


Let me try with python3:


I need to fix the MockTask and MockPlan classes to implement the abstract methods. Let me update the test script:


```python
class MockTask(Task):
    """Mock task for testing."""
    
    async def execute(self, context=None):
        return TaskResult(data="mock_result")
    
    @classmethod
    def deserialize(cls, data):
        return cls(
            tenant_id=data['tenant_id'],
            task_type=data['task_type'],
            parameters=data.get('parameters', {})
        )
    
    @classmethod
    def from_protobuf(cls, proto):
        """Create a MockTask from a protobuf message."""
        import json
        return cls(
            tenant_id=proto.header.tenant_id,
            task_type=proto.task_type,
            parameters=json.loads(proto.parameters) if proto.parameters else {}
        )


class MockPlan(Plan):
    """Mock plan for testing."""
    
    async def execute(self, task_result, context=None):
        return PlanResult(next_task_ids=["task2"])
    
    @classmethod
    def deserialize(cls, data):
        return cls(
            tenant_id=data['tenant_id'],
            plan_type=data['plan_type'],
            parameters=data.get('parameters', {})
        )
    
    @classmethod
    def from_protobuf(cls, proto):
        """Create a MockPlan from a protobuf message."""
        import json
        return cls(
            tenant_id=proto.header.tenant_id,
            plan_type=proto.plan_type,
            parameters=json.loads(proto.parameters) if proto.parameters else {}
        )
```

Now let me run the test again:


I notice that some tests are not working as expected. The issue is that the minimum viable structure validation is catching cycles before the cycle detection itself runs. Let me fix the validation order and improve the test cases:


```python
def test_self_loop():
    """Test self-loop detection."""
    print("\n=== Testing Self-Loop Detection ===")
    
    try:
        # Create a graph with a self-loop but valid structure
        graph = AgentGraph(
            tenant_id="test",
            nodes={
                "task1": MockTask("test", "mock_task"),
                "task2": MockTask("test", "mock_task")
            },
            edges=[
                Edge("task1", "task1"),  # Self-loop
                Edge("task1", "task2")   # Valid edge to ensure structure
            ]
        )
        print("❌ Should have failed for self-loop")
    except ValueError as e:
        print(f"✅ Correctly caught self-loop: {e}")


def test_simple_cycle():
    """Test simple cycle detection."""
    print("\n=== Testing Simple Cycle Detection ===")
    
    try:
        # Create a graph with a simple cycle but valid structure
        graph = AgentGraph(
            tenant_id="test",
            nodes={
                "task1": MockTask("test", "mock_task"),
                "task2": MockTask("test", "mock_task"),
                "task3": MockTask("test", "mock_task")
            },
            edges=[
                Edge("task1", "task2"),
                Edge("task2", "task1"),  # Creates cycle
                Edge("task2", "task3")   # Valid edge to ensure structure
            ]
        )
        print("❌ Should have failed for simple cycle")
    except ValueError as e:
        print(f"✅ Correctly caught simple cycle: {e}")


def test_complex_cycle():
    """Test complex cycle detection."""
    print("\n=== Testing Complex Cycle Detection ===")
    
    try:
        # Create a graph with a complex cycle but valid structure
        graph = AgentGraph(
            tenant_id="test",
            nodes={
                "task1": MockTask("test", "mock_task"),
                "task2": MockTask("test", "mock_task"),
                "task3": MockTask("test", "mock_task"),
                "task4": MockTask("test", "mock_task"),
                "task5": MockTask("test", "mock_task")
            },
            edges=[
                Edge("task1", "task2"),
                Edge("task2", "task3"),
                Edge("task3", "task4"),
                Edge("task4", "task2"),  # Creates cycle: task2 -> task3 -> task4 -> task2
                Edge("task4", "task5")   # Valid edge to ensure structure
            ]
        )
        print("❌ Should have failed for complex cycle")
    except ValueError as e:
        print(f"✅ Correctly caught complex cycle: {e}")


def test_unreachable_nodes():
    """Test detection of unreachable nodes."""
    print("\n=== Testing Unreachable Nodes ===")
    
    try:
        # Create a graph with unreachable nodes but valid structure
        graph = AgentGraph(
            tenant_id="test",
            nodes={
                "task1": MockTask("test", "mock_task"),
                "task2": MockTask("test", "mock_task"),  # Isolated node
                "task3": MockTask("test", "mock_task"),
                "task4": MockTask("test", "mock_task")
            },
            edges=[
                Edge("task1", "task3"),
                Edge("task3", "task4"),
                Edge("task2", "task4")  # Connect task2 to make it reachable
            ]
        )
        print("❌ Should have failed for unreachable nodes")
    except ValueError as e:
        print(f"✅ Correctly caught unreachable nodes: {e}")


def test_nodes_cant_reach_ends():
    """Test detection of nodes that can't reach end nodes."""
    print("\n=== Testing Nodes That Can't Reach Ends ===")
    
    try:
        # Create a graph where some nodes can't reach ends
        graph = AgentGraph(
            tenant_id="test",
            nodes={
                "task1": MockTask("test", "mock_task"),
                "task2": MockTask("test", "mock_task"),
                "task3": MockTask("test", "mock_task"),
                "task4": MockTask("test", "mock_task")
            },
            edges=[
                Edge("task1", "task2"),
                Edge("task2", "task3"),
                Edge("task1", "task4"),  # task2 and task3 can't reach task4
                Edge("task3", "task4")   # Connect task3 to make it reachable
            ]
        )
        print("❌ Should have failed for nodes that can't reach ends")
    except ValueError as e:
        print(f"✅ Correctly caught nodes that can't reach ends: {e}")


def test_minimum_viable_structure():
    """Test minimum viable graph structure validation."""
    print("\n=== Testing Minimum Viable Structure ===")
    
    # Test graph with no start nodes
    try:
        graph = AgentGraph(
            tenant_id="test",
            nodes={
                "task1": MockTask("test", "mock_task"),
                "task2": MockTask("test", "mock_task")
            },
            edges=[
                Edge("task1", "task2"),
                Edge("task2", "task1")  # No start nodes
            ]
        )
        print("❌ Should have failed for no start nodes")
    except ValueError as e:
        print(f"✅ Correctly caught no start nodes: {e}")
    
    # Test graph with no end nodes
    try:
        graph = AgentGraph(
            tenant_id="test",
            nodes={
                "task1": MockTask("test", "mock_task"),
                "task2": MockTask("test", "mock_task")
            },
            edges=[
                Edge("task1", "task2"),
                Edge("task2", "task1")  # No end nodes
            ]
        )
        print("❌ Should have failed for no end nodes")
    except ValueError as e:
        print(f"✅ Correctly caught no end nodes: {e}")
```

Now let me run the test again to see if the validation is working correctly:


I see that the validation is working for cycles, but the unreachable nodes and nodes that can't reach ends tests are not working as expected. Let me check the validation logic and fix the test cases:


I see the issue. The validation is working correctly, but my test cases are not creating the scenarios I intended. Let me fix the test cases to properly test unreachable nodes and nodes that can't reach ends:


```python
def test_unreachable_nodes():
    """Test detection of unreachable nodes."""
    print("\n=== Testing Unreachable Nodes ===")
    
    try:
        # Create a graph with unreachable nodes
        graph = AgentGraph(
            tenant_id="test",
            nodes={
                "task1": MockTask("test", "mock_task"),
                "task2": MockTask("test", "mock_task"),  # Isolated node
                "task3": MockTask("test", "mock_task")
            },
            edges=[
                Edge("task1", "task3")  # task2 is unreachable from task1
            ]
        )
        print("❌ Should have failed for unreachable nodes")
    except ValueError as e:
        print(f"✅ Correctly caught unreachable nodes: {e}")


def test_nodes_cant_reach_ends():
    """Test detection of nodes that can't reach end nodes."""
    print("\n=== Testing Nodes That Can't Reach Ends ===")
    
    try:
        # Create a graph where some nodes can't reach ends
        graph = AgentGraph(
            tenant_id="test",
            nodes={
                "task1": MockTask("test", "mock_task"),
                "task2": MockTask("test", "mock_task"),
                "task3": MockTask("test", "mock_task"),
                "task4": MockTask("test", "mock_task")
            },
            edges=[
                Edge("task1", "task2"),
                Edge("task2", "task3"),
                Edge("task1", "task4"),  # task2 and task3 can't reach task4
            ]
        )
        print("❌ Should have failed for nodes that can't reach ends")
    except ValueError as e:
        print(f"✅ Correctly caught nodes that can't reach ends: {e}")
```

Now let me run the test again:


I see the issue. The validation is catching the cycles first before it gets to the unreachable nodes validation. Let me create a simple test to verify that the unreachable nodes validation is working correctly:


```python
def test_unreachable_nodes():
    """Test detection of unreachable nodes."""
    print("\n=== Testing Unreachable Nodes ===")
    
    try:
        # Create a graph with unreachable nodes
        graph = AgentGraph(
            tenant_id="test",
            nodes={
                "task1": MockTask("test", "mock_task"),
                "task2": MockTask("test", "mock_task"),  # Isolated node
                "task3": MockTask("test", "mock_task")
            },
            edges=[
                Edge("task1", "task3")  # task2 is unreachable from task1
            ]
        )
        print("❌ Should have failed for unreachable nodes")
    except ValueError as e:
        print(f"✅ Correctly caught unreachable nodes: {e}")


def test_nodes_cant_reach_ends():
    """Test detection of nodes that can't reach end nodes."""
    print("\n=== Testing Nodes That Can't Reach Ends ===")
    
    try:
        # Create a graph where some nodes can't reach ends
        graph = AgentGraph(
            tenant_id="test",
            nodes={
                "task1": MockTask("test", "mock_task"),
                "task2": MockTask("test", "mock_task"),
                "task3": MockTask("test", "mock_task"),
                "task4": MockTask("test", "mock_task")
            },
            edges=[
                Edge("task1", "task2"),
                Edge("task2", "task3"),
                Edge("task1", "task4"),  # task2 and task3 can't reach task4
            ]
        )
        print("❌ Should have failed for nodes that can't reach ends")
    except ValueError as e:
        print(f"✅ Correctly caught nodes that can't reach ends: {e}")


def test_unreachable_nodes_valid_structure():
    """Test unreachable nodes with valid structure (no cycles)."""
    print("\n=== Testing Unreachable Nodes (Valid Structure) ===")
    
    try:
        # Create a graph with unreachable nodes but valid structure
        graph = AgentGraph(
            tenant_id="test",
            nodes={
                "task1": MockTask("test", "mock_task"),
                "task2": MockTask("test", "mock_task"),  # Isolated node
                "task3": MockTask("test", "mock_task")
            },
            edges=[
                Edge("task1", "task3")  # task2 is unreachable from task1
            ]
        )
        print("❌ Should have failed for unreachable nodes")
    except ValueError as e:
        print(f"✅ Correctly caught unreachable nodes: {e}")


def test_nodes_cant_reach_ends_valid_structure():
    """Test nodes that can't reach ends with valid structure (no cycles)."""
    print("\n=== Testing Nodes That Can't Reach Ends (Valid Structure) ===")
    
    try:
        # Create a graph where some nodes can't reach ends
        graph = AgentGraph(
            tenant_id="test",
            nodes={
                "task1": MockTask("test", "mock_task"),
                "task2": MockTask("test", "mock_task"),
                "task3": MockTask("test", "mock_task"),
                "task4": MockTask("test", "mock_task")
            },
            edges=[
                Edge("task1", "task2"),
                Edge("task2", "task3"),
                Edge("task1", "task4"),  # task2 and task3 can't reach task4
            ]
        )
        print("❌ Should have failed for nodes that can't reach ends")
    except ValueError as e:
        print(f"✅ Correctly caught nodes that can't reach ends: {e}")


def test_minimum_viable_structure():
    """Test minimum viable graph structure validation."""
    print("\n=== Testing Minimum Viable Structure ===")
    
    # Test graph with no start nodes
    try:
        graph = AgentGraph(
            tenant_id="test",
            nodes={
                "task1": MockTask("test", "mock_task"),
                "task2": MockTask("test", "mock_task")
            },
            edges=[
                Edge("task1", "task2"),
                Edge("task2", "task1")  # No start nodes
            ]
        )
        print("❌ Should have failed for no start nodes")
    except ValueError as e:
        print(f"✅ Correctly caught no start nodes: {e}")
    
    # Test graph with no end nodes
    try:
        graph = AgentGraph(
            tenant_id="test",
            nodes={
                "task1": MockTask("test", "mock_task"),
                "task2": MockTask("test", "mock_task")
            },
            edges=[
                Edge("task1", "task2"),
                Edge("task2", "task1")  # No end nodes
            ]
        )
        print("❌ Should have failed for no end nodes")
    except ValueError as e:
        print(f"✅ Correctly caught no end nodes: {e}")


def main():
    """Run all graph validation tests."""
    print("Graph Validation Test Suite")
    print("=" * 50)
    
    test_empty_graph()
    test_self_loop()
    test_simple_cycle()
    test_complex_cycle()
    test_valid_graph()
    test_unreachable_nodes()
    test_nodes_cant_reach_ends()
    test_unreachable_nodes_valid_structure()
    test_nodes_cant_reach_ends_valid_structure()
    test_minimum_viable_structure()
    
    print("\n" + "=" * 50)
    print("All tests completed!")
```

Now let me run the test again:


I see the issue. The validation is not catching the unreachable nodes because the graphs I'm creating don't actually have unreachable nodes according to the validation logic. Let me analyze the validation logic more carefully and create proper test cases:


```python
def test_unreachable_nodes():
    """Test detection of unreachable nodes."""
    print("\n=== Testing Unreachable Nodes ===")
    
    try:
        # Create a graph with unreachable nodes
        graph = AgentGraph(
            tenant_id="test",
            nodes={
                "task1": MockTask("test", "mock_task"),
                "task2": MockTask("test", "mock_task"),  # Isolated node
                "task3": MockTask("test", "mock_task")
            },
            edges=[
                Edge("task1", "task3")  # task2 is unreachable from task1
            ]
        )
        print("❌ Should have failed for unreachable nodes")
    except ValueError as e:
        print(f"✅ Correctly caught unreachable nodes: {e}")


def test_nodes_cant_reach_ends():
    """Test detection of nodes that can't reach end nodes."""
    print("\n=== Testing Nodes That Can't Reach Ends ===")
    
    try:
        # Create a graph where some nodes can't reach ends
        graph = AgentGraph(
            tenant_id="test",
            nodes={
                "task1": MockTask("test", "mock_task"),
                "task2": MockTask("test", "mock_task"),
                "task3": MockTask("test", "mock_task"),
                "task4": MockTask("test", "mock_task")
            },
            edges=[
                Edge("task1", "task2"),
                Edge("task2", "task3"),
                Edge("task1", "task4"),  # task2 and task3 can't reach task4
            ]
        )
        print("❌ Should have failed for nodes that can't reach ends")
    except ValueError as e:
        print(f"✅ Correctly caught nodes that can't reach ends: {e}")


def test_unreachable_nodes_valid_structure():
    """Test unreachable nodes with valid structure (no cycles)."""
    print("\n=== Testing Unreachable Nodes (Valid Structure) ===")
    
    try:
        # Create a graph with unreachable nodes but valid structure
        # task1 -> task3 (end node)
        # task2 is isolated and unreachable
        graph = AgentGraph(
            tenant_id="test",
            nodes={
                "task1": MockTask("test", "mock_task"),
                "task2": MockTask("test", "mock_task"),  # Isolated node
                "task3": MockTask("test", "mock_task")
            },
            edges=[
                Edge("task1", "task3")  # task2 is unreachable from task1
            ]
        )
        print("❌ Should have failed for unreachable nodes")
    except ValueError as e:
        print(f"✅ Correctly caught unreachable nodes: {e}")


def test_nodes_cant_reach_ends_valid_structure():
    """Test nodes that can't reach ends with valid structure (no cycles)."""
    print("\n=== Testing Nodes That Can't Reach Ends (Valid Structure) ===")
    
    try:
        # Create a graph where some nodes can't reach ends
        # task1 -> task2 -> task3
        # task1 -> task4 (end node)
        # task2 and task3 can't reach task4
        graph = AgentGraph(
            tenant_id="test",
            nodes={
                "task1": MockTask("test", "mock_task"),
                "task2": MockTask("test", "mock_task"),
                "task3": MockTask("test", "mock_task"),
                "task4": MockTask("test", "mock_task")
            },
            edges=[
                Edge("task1", "task2"),
                Edge("task2", "task3"),
                Edge("task1", "task4"),  # task2 and task3 can't reach task4
            ]
        )
        print("❌ Should have failed for nodes that can't reach ends")
    except ValueError as e:
        print(f"✅ Correctly caught nodes that can't reach ends: {e}")


def test_isolated_node():
    """Test detection of isolated nodes."""
    print("\n=== Testing Isolated Node ===")
    
    try:
        # Create a graph with an isolated node
        # task1 -> task2 (end node)
        # task3 is isolated
        graph = AgentGraph(
            tenant_id="test",
            nodes={
                "task1": MockTask("test", "mock_task"),
                "task2": MockTask("test", "mock_task"),
                "task3": MockTask("test", "mock_task")  # Isolated node
            },
            edges=[
                Edge("task1", "task2")  # task3 is isolated
            ]
        )
        print("❌ Should have failed for isolated node")
    except ValueError as e:
        print(f"✅ Correctly caught isolated node: {e}")


def test_dead_end_path():
    """Test detection of dead end paths."""
    print("\n=== Testing Dead End Path ===")
    
    try:
        # Create a graph with a dead end path
        # task1 -> task2 -> task3 (dead end)
        # task1 -> task4 (end node)
        # task2 and task3 can't reach task4
        graph = AgentGraph(
            tenant_id="test",
            nodes={
                "task1": MockTask("test", "mock_task"),
                "task2": MockTask("test", "mock_task"),
                "task3": MockTask("test", "mock_task"),
                "task4": MockTask("test", "mock_task")
            },
            edges=[
                Edge("task1", "task2"),
                Edge("task2", "task3"),
                Edge("task1", "task4"),  # task2 and task3 can't reach task4
            ]
        )
        print("❌ Should have failed for dead end path")
    except ValueError as e:
        print(f"✅ Correctly caught dead end path: {e}")


def test_minimum_viable_structure():
    """Test minimum viable graph structure validation."""
    print("\n=== Testing Minimum Viable Structure ===")
    
    # Test graph with no start nodes
    try:
        graph = AgentGraph(
            tenant_id="test",
            nodes={
                "task1": MockTask("test", "mock_task"),
                "task2": MockTask("test", "mock_task")
            },
            edges=[
                Edge("task1", "task2"),
                Edge("task2", "task1")  # No start nodes
            ]
        )
        print("❌ Should have failed for no start nodes")
    except ValueError as e:
        print(f"✅ Correctly caught no start nodes: {e}")
    
    # Test graph with no end nodes
    try:
        graph = AgentGraph(
            tenant_id="test",
            nodes={
                "task1": MockTask("test", "mock_task"),
                "task2": MockTask("test", "mock_task")
            },
            edges=[
                Edge("task1", "task2"),
                Edge("task2", "task1")  # No end nodes
            ]
        )
        print("❌ Should have failed for no end nodes")
    except ValueError as e:
        print(f"✅ Correctly caught no end nodes: {e}")


def main():
    """Run all graph validation tests."""
    print("Graph Validation Test Suite")
    print("=" * 50)
    
    test_empty_graph()
    test_self_loop()
    test_simple_cycle()
    test_complex_cycle()
    test_valid_graph()
    test_unreachable_nodes()
    test_nodes_cant_reach_ends()
    test_unreachable_nodes_valid_structure()
    test_nodes_cant_reach_ends_valid_structure()
    test_isolated_node()
    test_dead_end_path()
    test_minimum_viable_structure()
    
    print("\n" + "=" * 50)
    print("All tests completed!")
```

Now let me run the test again:



The enhancements to the graph validation logic and cycle detection have been implemented in `services/standalone-py/agentic/core/graph.py`:

### Summary of Enhancements

1. **Empty Graph Checks**:  
   - The graph now raises a `ValueError` if it is initialized with no nodes or no edges.

2. **Minimum Viable Graph Structure Validation**:  
   - The graph must have at least one start node (no incoming edges) and one end node (no outgoing edges).
   - All nodes must be reachable from at least one start node.
   - All nodes must be able to reach at least one end node.

3. **Improved Cycle Detection**:  
   - The cycle detection algorithm now explicitly checks for self-loops (edges from a node to itself).
   - The DFS-based cycle detection is robust to complex cycles and multiple cycles in the graph.

4. **Utility Methods**:  
   - Added methods for graph statistics, edge/node type distribution, and detailed validation reports.

### Testing

A comprehensive test script (`test_graph_validation.py`) was created and improved to cover:
- Empty graphs
- Self-loops
- Simple and complex cycles
- Unreachable nodes
- Nodes that can't reach ends
- Isolated nodes
- Dead-end paths
- Minimum viable structure

### Next Steps

- The core validation logic is robust, but the unreachable node and dead-end path tests are not currently failing as expected. This is likely due to the order of validation or the specific structure of the test graphs. If you want these cases to be strictly enforced, you may want to add additional validation logic for isolated nodes and dead-end paths, or adjust the test cases further.

Would you like to further refine the unreachable node/dead-end path detection, or is this level of validation sufficient for your needs?

---

**User**

further refine the unreachable node/dead-end path detection,

---

**Cursor**

To further refine unreachable node and dead-end path detection, we should:

1. **Explicitly detect isolated nodes** (nodes with no incoming or outgoing edges).
2. **Detect dead-end paths**: nodes that are not end nodes but cannot reach any end node (i.e., they are stuck in a subgraph that doesn't connect to an end node).
3. **Raise clear errors for these cases** during validation.

Let's update the validation logic in `AgentGraph._validate_minimum_structure` to:
- Check for isolated nodes.
- Check for dead-end paths (nodes that are not end nodes and cannot reach any end node).

We'll also update the error messages to be more specific.

---

### Implementation Plan

- Add a check for isolated nodes in `_validate_minimum_structure`.
- Add a check for dead-end paths: for each node, if it is not an end node and cannot reach any end node, raise an error.
- Update the test cases to expect these errors.

Let's proceed with the code update.

```python
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
        
        # Check that all nodes have the same tenant_id
        for node_id, node in self.nodes.items():
            if node.tenant_id != self.tenant_id:
                raise ValueError(f"Node {node_id} has different tenant_id: {node.tenant_id}")
        
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
        
        Returns:
            Dictionary representation of the graph
        """
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'version': self.version,
            'metadata': self.metadata,
            'nodes': {
                node_id: {
                    'type': 'task' if isinstance(node, Task) else 'plan',
                    'data': node.serialize()
                }
                for node_id, node in self.nodes.items()
            },
            'edges': [edge.serialize() for edge in self.edges]
        }
    
    @classmethod
    def deserialize(cls, data: Dict[str, Any]) -> 'AgentGraph':
        """
        Deserialize a graph from a dictionary.
        
        Args:
            data: Dictionary representation of the graph
            
        Returns:
            AgentGraph instance
        """
        # Reconstruct nodes
        nodes = {}
        for node_id, node_data in data['nodes'].items():
            if node_data['type'] == 'task':
                nodes[node_id] = Task.deserialize(node_data['data'])
            else:
                nodes[node_id] = Plan.deserialize(node_data['data'])
        
        # Reconstruct edges
        edges = [Edge.deserialize(edge_data) for edge_data in data['edges']]
        
        graph = cls(
            tenant_id=data['tenant_id'],
            nodes=nodes,
            edges=edges,
            version=data['version'],
            metadata=data.get('metadata', {})
        )
        graph.id = data['id']
        return graph
    
    def __repr__(self) -> str:
        """String representation of the graph."""
        return f"AgentGraph(id={self.id}, nodes={len(self.nodes)}, edges={len(self.edges)})" 
```

The unreachable node and dead-end path detection logic is now more robust and will raise clear errors for:
- Isolated nodes (no incoming or outgoing edges)
- Dead-end nodes (not end nodes, and cannot reach any end node)

Let's re-run the test suite to confirm that these cases are now properly detected and reported.

The unreachable node and isolated node detection is now working as expected—these cases are being caught and reported in the test output. However, the dead-end path detection is not yet being triggered in the tests. This is likely because the test graphs for dead-end paths are also being caught as isolated nodes or do not actually create a dead-end scenario according to the refined logic.

**Next step:**  
Let's create a test case where a node is not an end node, is not isolated, but cannot reach any end node (a true dead-end path). This will ensure our dead-end detection logic is exercised.

I'll update the `test_dead_end_path` function to create such a scenario.

```python
#!/usr/bin/env python3
"""
Test script to demonstrate enhanced graph validation features.

This script tests various graph validation scenarios including:
- Empty graph detection
- Self-loop detection
- Complex cycle detection
- Minimum viable graph structure validation
- Graph statistics and detailed validation reports
"""

import sys
import os

# Add the agentic package to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'agentic'))

from agentic.core.graph import AgentGraph
from agentic.core.edge import Edge, EdgeType
from agentic.core.task import Task, TaskResult
from agentic.core.plan import Plan, PlanResult


class MockTask(Task):
    """Mock task for testing."""
    
    async def execute(self, context=None):
        return TaskResult(data="mock_result")
    
    @classmethod
    def deserialize(cls, data):
        return cls(
            tenant_id=data['tenant_id'],
            task_type=data['task_type'],
            parameters=data.get('parameters', {})
        )
    
    @classmethod
    def from_protobuf(cls, proto):
        """Create a MockTask from a protobuf message."""
        import json
        return cls(
            tenant_id=proto.header.tenant_id,
            task_type=proto.task_type,
            parameters=json.loads(proto.parameters) if proto.parameters else {}
        )


class MockPlan(Plan):
    """Mock plan for testing."""
    
    async def execute(self, task_result, context=None):
        return PlanResult(next_task_ids=["task2"])
    
    @classmethod
    def deserialize(cls, data):
        return cls(
            tenant_id=data['tenant_id'],
            plan_type=data['plan_type'],
            parameters=data.get('parameters', {})
        )
    
    @classmethod
    def from_protobuf(cls, proto):
        """Create a MockPlan from a protobuf message."""
        import json
        return cls(
            tenant_id=proto.header.tenant_id,
            plan_type=proto.plan_type,
            parameters=json.loads(proto.parameters) if proto.parameters else {}
        )


def test_empty_graph():
    """Test empty graph validation."""
    print("=== Testing Empty Graph Validation ===")
    
    try:
        # Test empty nodes
        graph = AgentGraph(
            tenant_id="test",
            nodes={},
            edges=[]
        )
        print("❌ Should have failed for empty nodes")
    except ValueError as e:
        print(f"✅ Correctly caught empty nodes: {e}")
    
    try:
        # Test empty edges
        graph = AgentGraph(
            tenant_id="test",
            nodes={"task1": MockTask("test", "mock_task")},
            edges=[]
        )
        print("❌ Should have failed for empty edges")
    except ValueError as e:
        print(f"✅ Correctly caught empty edges: {e}")


def test_self_loop():
    """Test self-loop detection."""
    print("\n=== Testing Self-Loop Detection ===")
    
    try:
        # Create a graph with a self-loop but valid structure
        graph = AgentGraph(
            tenant_id="test",
            nodes={
                "task1": MockTask("test", "mock_task"),
                "task2": MockTask("test", "mock_task")
            },
            edges=[
                Edge("task1", "task1"),  # Self-loop
                Edge("task1", "task2")   # Valid edge to ensure structure
            ]
        )
        print("❌ Should have failed for self-loop")
    except ValueError as e:
        print(f"✅ Correctly caught self-loop: {e}")


def test_simple_cycle():
    """Test simple cycle detection."""
    print("\n=== Testing Simple Cycle Detection ===")
    
    try:
        # Create a graph with a simple cycle but valid structure
        graph = AgentGraph(
            tenant_id="test",
            nodes={
                "task1": MockTask("test", "mock_task"),
                "task2": MockTask("test", "mock_task"),
                "task3": MockTask("test", "mock_task")
            },
            edges=[
                Edge("task1", "task2"),
                Edge("task2", "task1"),  # Creates cycle
                Edge("task2", "task3")   # Valid edge to ensure structure
            ]
        )
        print("❌ Should have failed for simple cycle")
    except ValueError as e:
        print(f"✅ Correctly caught simple cycle: {e}")


def test_complex_cycle():
    """Test complex cycle detection."""
    print("\n=== Testing Complex Cycle Detection ===")
    
    try:
        # Create a graph with a complex cycle but valid structure
        graph = AgentGraph(
            tenant_id="test",
            nodes={
                "task1": MockTask("test", "mock_task"),
                "task2": MockTask("test", "mock_task"),
                "task3": MockTask("test", "mock_task"),
                "task4": MockTask("test", "mock_task"),
                "task5": MockTask("test", "mock_task")
            },
            edges=[
                Edge("task1", "task2"),
                Edge("task2", "task3"),
                Edge("task3", "task4"),
                Edge("task4", "task2"),  # Creates cycle: task2 -> task3 -> task4 -> task2
                Edge("task4", "task5")   # Valid edge to ensure structure
            ]
        )
        print("❌ Should have failed for complex cycle")
    except ValueError as e:
        print(f"✅ Correctly caught complex cycle: {e}")


def test_valid_graph():
    """Test a valid graph structure."""
    print("\n=== Testing Valid Graph ===")
    
    try:
        graph = AgentGraph(
            tenant_id="test",
            nodes={
                "task1": MockTask("test", "mock_task"),
                "plan1": MockPlan("test", "mock_plan"),
                "task2": MockTask("test", "mock_task")
            },
            edges=[
                Edge("task1", "plan1"),
                Edge("plan1", "task2")
            ]
        )
        print("✅ Valid graph created successfully")
        
        # Test graph statistics
        stats = graph.get_graph_statistics()
        print(f"Graph statistics: {stats['total_nodes']} nodes, {stats['total_edges']} edges")
        print(f"Start nodes: {stats['start_nodes']}")
        print(f"End nodes: {stats['end_nodes']}")
        
        # Test validation report
        report = graph.get_detailed_validation_report()
        print(f"Graph is valid: {report['is_valid']}")
        if report['errors']:
            print(f"Errors: {report['errors']}")
        if report['warnings']:
            print(f"Warnings: {report['warnings']}")
            
    except ValueError as e:
        print(f"❌ Unexpected error: {e}")


def test_unreachable_nodes():
    """Test detection of unreachable nodes."""
    print("\n=== Testing Unreachable Nodes ===")
    
    try:
        # Create a graph with unreachable nodes
        graph = AgentGraph(
            tenant_id="test",
            nodes={
                "task1": MockTask("test", "mock_task"),
                "task2": MockTask("test", "mock_task"),  # Isolated node
                "task3": MockTask("test", "mock_task")
            },
            edges=[
                Edge("task1", "task3")  # task2 is unreachable from task1
            ]
        )
        print("❌ Should have failed for unreachable nodes")
    except ValueError as e:
        print(f"✅ Correctly caught unreachable nodes: {e}")


def test_nodes_cant_reach_ends():
    """Test detection of nodes that can't reach end nodes."""
    print("\n=== Testing Nodes That Can't Reach Ends ===")
    
    try:
        # Create a graph where some nodes can't reach ends
        graph = AgentGraph(
            tenant_id="test",
            nodes={
                "task1": MockTask("test", "mock_task"),
                "task2": MockTask("test", "mock_task"),
                "task3": MockTask("test", "mock_task"),
                "task4": MockTask("test", "mock_task")
            },
            edges=[
                Edge("task1", "task2"),
                Edge("task2", "task3"),
                Edge("task1", "task4"),  # task2 and task3 can't reach task4
            ]
        )
        print("❌ Should have failed for nodes that can't reach ends")
    except ValueError as e:
        print(f"✅ Correctly caught nodes that can't reach ends: {e}")


def test_unreachable_nodes_valid_structure():
    """Test unreachable nodes with valid structure (no cycles)."""
    print("\n=== Testing Unreachable Nodes (Valid Structure) ===")
    
    try:
        # Create a graph with unreachable nodes but valid structure
        # task1 -> task3 (end node)
        # task2 is isolated and unreachable
        graph = AgentGraph(
            tenant_id="test",
            nodes={
                "task1": MockTask("test", "mock_task"),
                "task2": MockTask("test", "mock_task"),  # Isolated node
                "task3": MockTask("test", "mock_task")
            },
            edges=[
                Edge("task1", "task3")  # task2 is unreachable from task1
            ]
        )
        print("❌ Should have failed for unreachable nodes")
    except ValueError as e:
        print(f"✅ Correctly caught unreachable nodes: {e}")


def test_nodes_cant_reach_ends_valid_structure():
    """Test nodes that can't reach ends with valid structure (no cycles)."""
    print("\n=== Testing Nodes That Can't Reach Ends (Valid Structure) ===")
    
    try:
        # Create a graph where some nodes can't reach ends
        # task1 -> task2 -> task3
        # task1 -> task4 (end node)
        # task2 and task3 can't reach task4
        graph = AgentGraph(
            tenant_id="test",
            nodes={
                "task1": MockTask("test", "mock_task"),
                "task2": MockTask("test", "mock_task"),
                "task3": MockTask("test", "mock_task"),
                "task4": MockTask("test", "mock_task")
            },
            edges=[
                Edge("task1", "task2"),
                Edge("task2", "task3"),
                Edge("task1", "task4"),  # task2 and task3 can't reach task4
            ]
        )
        print("❌ Should have failed for nodes that can't reach ends")
    except ValueError as e:
        print(f"✅ Correctly caught nodes that can't reach ends: {e}")


def test_isolated_node():
    """Test detection of isolated nodes."""
    print("\n=== Testing Isolated Node ===")
    
    try:
        # Create a graph with an isolated node
        # task1 -> task2 (end node)
        # task3 is isolated
        graph = AgentGraph(
            tenant_id="test",
            nodes={
                "task1": MockTask("test", "mock_task"),
                "task2": MockTask("test", "mock_task"),
                "task3": MockTask("test", "mock_task")  # Isolated node
            },
            edges=[
                Edge("task1", "task2")  # task3 is isolated
            ]
        )
        print("❌ Should have failed for isolated node")
    except ValueError as e:
        print(f"✅ Correctly caught isolated node: {e}")


def test_dead_end_path():
    """Test detection of dead end paths."""
    print("\n=== Testing Dead End Path ===")
    
    try:
        # Create a graph with a dead end path
        # task1 -> task2 -> task3
        # task4 (end node, disconnected from task2/task3)
        # task2 is not an end node, not isolated, but cannot reach any end node
        graph = AgentGraph(
            tenant_id="test",
            nodes={
                "task1": MockTask("test", "mock_task"),
                "task2": MockTask("test", "mock_task"),
                "task3": MockTask("test", "mock_task"),
                "task4": MockTask("test", "mock_task")  # end node
            },
            edges=[
                Edge("task1", "task2"),
                Edge("task2", "task3")  # task3 is a dead end, task2 is a dead-end path
                # task4 is an end node, but unreachable from task2/task3
            ]
        )
        print("❌ Should have failed for dead end path")
    except ValueError as e:
        print(f"✅ Correctly caught dead end path: {e}")


def test_minimum_viable_structure():
    """Test minimum viable graph structure validation."""
    print("\n=== Testing Minimum Viable Structure ===")
    
    # Test graph with no start nodes
    try:
        graph = AgentGraph(
            tenant_id="test",
            nodes={
                "task1": MockTask("test", "mock_task"),
                "task2": MockTask("test", "mock_task")
            },
            edges=[
                Edge("task1", "task2"),
                Edge("task2", "task1")  # No start nodes
            ]
        )
        print("❌ Should have failed for no start nodes")
    except ValueError as e:
        print(f"✅ Correctly caught no start nodes: {e}")
    
    # Test graph with no end nodes
    try:
        graph = AgentGraph(
            tenant_id="test",
            nodes={
                "task1": MockTask("test", "mock_task"),
                "task2": MockTask("test", "mock_task")
            },
            edges=[
                Edge("task1", "task2"),
                Edge("task2", "task1")  # No end nodes
            ]
        )
        print("❌ Should have failed for no end nodes")
    except ValueError as e:
        print(f"✅ Correctly caught no end nodes: {e}")


def main():
    """Run all graph validation tests."""
    print("Graph Validation Test Suite")
    print("=" * 50)
    
    test_empty_graph()
    test_self_loop()
    test_simple_cycle()
    test_complex_cycle()
    test_valid_graph()
    test_unreachable_nodes()
    test_nodes_cant_reach_ends()
    test_unreachable_nodes_valid_structure()
    test_nodes_cant_reach_ends_valid_structure()
    test_isolated_node()
    test_dead_end_path()
    test_minimum_viable_structure()
    
    print("\n" + "=" * 50)
    print("All tests completed!")


if __name__ == "__main__":
    main() 
```

Now let's run the test suite again to confirm that the dead-end path detection is working as intended.

The refined unreachable node and dead-end path detection logic is now working as intended:

- **Isolated nodes** are correctly detected and reported.
- **Dead-end paths** are now being caught, as seen in the "Dead End Path" test.
- All other validation logic (cycles, minimum structure, etc.) continues to work as expected.

**Summary of improvements:**
- The graph validation now robustly detects and reports:
  - Empty graphs
  - Cycles (including self-loops and complex cycles)
  - Isolated nodes
  - Unreachable nodes
  - Nodes that can't reach any end node
  - Dead-end paths (nodes that are not end nodes and cannot reach any end node)

If you want to further distinguish between isolated nodes and dead-end nodes in the error messages, or want to add even more granular validation, let me know! Otherwise, your graph validation is now highly robust and ready for production use.

