"""
Edge class for the agentic framework.

Edges represent the logical links between Tasks and Plans in the graph configuration.
They define the flow control and conditional logic for graph traversal.
"""

from enum import Enum
from typing import Any, Callable, Dict, Optional


class EdgeType(Enum):
    """Types of edges in the agent graph."""
    NORMAL = "normal"
    PARALLEL = "parallel"
    JOIN = "join"
    FINAL = "final"


class Edge:
    """
    Represents an edge between nodes in an AgentGraph.
    
    Edges define the logical links between Tasks and Plans, including
    conditional logic for edge traversal and flow control.
    """
    
    def __init__(self, 
                 source_id: str,
                 target_id: str,
                 edge_type: EdgeType = EdgeType.NORMAL,
                 condition: Optional[Callable[[Dict[str, Any]], bool]] = None,
                 metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize a new Edge.
        
        Args:
            source_id: ID of the source node
            target_id: ID of the target node
            edge_type: Type of edge (NORMAL, PARALLEL, JOIN, FINAL)
            condition: Optional conditional function for edge traversal
            metadata: Optional metadata for the edge
        """
        self.source_id = source_id
        self.target_id = target_id
        self.edge_type = edge_type
        self.condition = condition
        self.metadata = metadata or {}
    
    def should_traverse(self, context: Dict[str, Any]) -> bool:
        """
        Determine if this edge should be traversed based on the context.
        
        Args:
            context: Execution context containing task results and metadata
            
        Returns:
            True if the edge should be traversed, False otherwise
        """
        if self.condition is None:
            return True
        
        try:
            return self.condition(context)
        except Exception:
            # If condition evaluation fails, don't traverse
            return False
    
    def serialize(self) -> Dict[str, Any]:
        """
        Serialize the edge to a dictionary.
        
        Returns:
            Dictionary representation of the edge
        """
        return {
            'source_id': self.source_id,
            'target_id': self.target_id,
            'edge_type': self.edge_type.value,
            'metadata': self.metadata
        }
    
    @classmethod
    def deserialize(cls, data: Dict[str, Any]) -> 'Edge':
        """
        Deserialize an edge from a dictionary.
        
        Args:
            data: Dictionary representation of the edge
            
        Returns:
            Edge instance
        """
        return cls(
            source_id=data['source_id'],
            target_id=data['target_id'],
            edge_type=EdgeType(data['edge_type']),
            metadata=data.get('metadata', {})
        )
    
    def __repr__(self) -> str:
        """String representation of the edge."""
        return f"Edge({self.source_id} -> {self.target_id}, type={self.edge_type.value})"
    
    def __eq__(self, other: Any) -> bool:
        """Equality comparison for edges."""
        if not isinstance(other, Edge):
            return False
        return (self.source_id == other.source_id and
                self.target_id == other.target_id and
                self.edge_type == other.edge_type)
    
    def __hash__(self) -> int:
        """Hash for edge objects."""
        return hash((self.source_id, self.target_id, self.edge_type)) 