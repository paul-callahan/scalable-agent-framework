from dataclasses import dataclass
from typing import Dict, Optional
from .timestamp import Timestamp


@dataclass
class AgentLifetime:
    """One runtime instance of an AgentGraph executing to completion"""
    
    # Unique lifetime identifier
    lifetime_id: str
    
    # Reference to the AgentGraph template
    graph_id: str
    
    # Graph version used for this lifetime
    graph_version: str
    
    # Lifetime status
    status: str
    
    # Start timestamp
    started_at: Timestamp
    
    # End timestamp
    ended_at: Optional[Timestamp]
    
    # Input data for the lifetime
    input_data: str
    
    # Output data from the lifetime
    output_data: Optional[str]
    
    # Lifetime metadata
    metadata: Dict[str, str]
    
    # Tenant identifier for multitenant support
    tenant_id: str
    
    def __post_init__(self):
        """Validate lifetime after initialization"""
        if not self.lifetime_id:
            raise ValueError("lifetime_id cannot be empty")
        if not self.graph_id:
            raise ValueError("graph_id cannot be empty")
        if not self.graph_version:
            raise ValueError("graph_version cannot be empty")
        if not self.status:
            raise ValueError("status cannot be empty")
        if not self.tenant_id:
            raise ValueError("tenant_id cannot be empty") 