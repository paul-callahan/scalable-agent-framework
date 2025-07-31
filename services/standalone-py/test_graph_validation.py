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