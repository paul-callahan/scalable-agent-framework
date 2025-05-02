from dataclasses import dataclass
from typing import List, Dict
from .graph_metadata import GraphMetadata
from .graph_node import GraphNode
from .edge import Edge


@dataclass
class AgentGraph:
    """Immutable graph template with semantic versioning"""
    
    # Unique identifier for the graph
    graph_id: str
    
    # Semantic version of the graph
    version: str
    
    # Graph metadata
    metadata: GraphMetadata
    
    # All nodes in the graph (Tasks and Plans)
    nodes: List[GraphNode]
    
    # All edges connecting the nodes
    edges: List[Edge]
    
    # Entry point node ID
    entry_node_id: str
    
    # Exit point node IDs
    exit_node_ids: List[str]
    
    # Tenant identifier for multitenant support
    tenant_id: str
    
    def __post_init__(self):
        """Validate graph after initialization"""
        if not self.graph_id:
            raise ValueError("graph_id cannot be empty")
        if not self.version:
            raise ValueError("version cannot be empty")
        if not self.entry_node_id:
            raise ValueError("entry_node_id cannot be empty")
        if not self.tenant_id:
            raise ValueError("tenant_id cannot be empty")
        if not self.nodes:
            raise ValueError("nodes cannot be empty")
        if not self.edges:
            raise ValueError("edges cannot be empty") 