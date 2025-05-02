from dataclasses import dataclass
from typing import Dict, Optional
from .duration import Duration


@dataclass
class TaskConfiguration:
    """Task-specific settings and parameters"""
    
    # Configuration data as JSON string
    config_json: str
    
    # Timeout for task execution
    timeout: Optional[Duration]
    
    # Retry configuration
    max_retries: int
    
    # Resource limits
    resource_limits: Dict[str, str]
    
    def __post_init__(self):
        """Validate configuration after initialization"""
        if self.max_retries < 0:
            raise ValueError("max_retries cannot be negative") 