from dataclasses import dataclass
from typing import List, Optional
from .routing_rule import RoutingRule
from .duration import Duration


@dataclass
class PlanConfiguration:
    """Plan-specific rules, conditions, and routing logic"""
    
    # Configuration data as JSON string
    config_json: str
    
    # Routing rules and conditions
    routing_rules: List[RoutingRule]
    
    # Default next task if no rules match
    default_next_task: Optional[str]
    
    # Timeout for plan execution
    timeout: Optional[Duration]
    
    def __post_init__(self):
        """Validate configuration after initialization"""
        if not self.routing_rules:
            raise ValueError("routing_rules cannot be empty") 