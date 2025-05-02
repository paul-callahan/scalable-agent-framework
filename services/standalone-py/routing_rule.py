from dataclasses import dataclass


@dataclass
class RoutingRule:
    """Defines a condition and the corresponding next task"""
    
    # Condition expression (e.g., JSONPath, simple boolean)
    condition: str
    
    # Next task ID if condition is true
    next_task_id: str
    
    # Priority of this rule (higher numbers = higher priority)
    priority: int
    
    # Description of the rule
    description: str
    
    def __post_init__(self):
        """Validate routing rule after initialization"""
        if not self.condition:
            raise ValueError("condition cannot be empty")
        if not self.next_task_id:
            raise ValueError("next_task_id cannot be empty")
        if self.priority < 0:
            raise ValueError("priority cannot be negative") 