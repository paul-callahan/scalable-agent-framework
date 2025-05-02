from dataclasses import dataclass
from typing import Optional
from .join_configuration import JoinConfiguration


@dataclass
class EdgeConfiguration:
    """Edge-specific settings"""
    
    # Condition expression for conditional edges
    condition: Optional[str]
    
    # Priority for edge selection
    priority: int
    
    # Join configuration for JOIN edges
    join_config: Optional[JoinConfiguration]
    
    def __post_init__(self):
        """Validate edge configuration after initialization"""
        if self.priority < 0:
            raise ValueError("priority cannot be negative") 