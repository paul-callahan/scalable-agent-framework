from dataclasses import dataclass
from typing import Dict, List
from .plan_configuration import PlanConfiguration


@dataclass
class Plan:
    """Node that selects the next Task based on rules or prior state"""
    
    # Unique identifier for the plan
    plan_id: str
    
    # Type of plan (e.g., "conditional", "routing", "decision")
    plan_type: str
    
    # Plan-specific configuration and routing rules
    configuration: PlanConfiguration
    
    # Tenant identifier for multitenant support
    tenant_id: str
    
    # Metadata about the plan
    metadata: Dict[str, str]
    
    def __post_init__(self):
        """Validate plan after initialization"""
        if not self.plan_id:
            raise ValueError("plan_id cannot be empty")
        if not self.plan_type:
            raise ValueError("plan_type cannot be empty")
        if not self.tenant_id:
            raise ValueError("tenant_id cannot be empty") 