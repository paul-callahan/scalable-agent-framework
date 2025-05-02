from dataclasses import dataclass
from typing import Optional
from .duration import Duration


@dataclass
class JoinConfiguration:
    """Defines how multiple parallel paths should join"""
    
    # Join strategy (ALL, ANY, MAJORITY, etc.)
    join_strategy: str
    
    # Minimum number of inputs required
    min_inputs: int
    
    # Maximum number of inputs allowed
    max_inputs: int
    
    # Timeout for join operation
    timeout: Optional[Duration]
    
    def __post_init__(self):
        """Validate join configuration after initialization"""
        if not self.join_strategy:
            raise ValueError("join_strategy cannot be empty")
        if self.min_inputs < 0:
            raise ValueError("min_inputs cannot be negative")
        if self.max_inputs < self.min_inputs:
            raise ValueError("max_inputs cannot be less than min_inputs") 