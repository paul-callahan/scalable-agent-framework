from dataclasses import dataclass
from typing import Dict
from .edge_configuration import EdgeConfiguration


@dataclass
class Edge:
    """Logical link between Tasks and Plans"""
    
    # Unique edge identifier
    edge_id: str
    
    # Source node ID
    source_node_id: str
    
    # Target node ID
    target_node_id: str
    
    # Edge type (NORMAL, PARALLEL, JOIN, FINAL)
    edge_type: str
    
    # Edge configuration
    configuration: EdgeConfiguration
    
    # Edge metadata
    metadata: Dict[str, str]
    
    def __post_init__(self):
        """Validate edge after initialization"""
        if not self.edge_id:
            raise ValueError("edge_id cannot be empty")
        if not self.source_node_id:
            raise ValueError("source_node_id cannot be empty")
        if not self.target_node_id:
            raise ValueError("target_node_id cannot be empty")
        if not self.edge_type:
            raise ValueError("edge_type cannot be empty")
        if self.edge_type not in ["NORMAL", "PARALLEL", "JOIN", "FINAL"]:
            raise ValueError("edge_type must be one of: NORMAL, PARALLEL, JOIN, FINAL") 