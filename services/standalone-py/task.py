from dataclasses import dataclass
from typing import Dict, Any, Optional
from .task_configuration import TaskConfiguration


@dataclass
class Task:
    """Node that performs work (API call, DB query, computation)"""
    
    # Unique identifier for the task
    task_id: str
    
    # Type of task (e.g., "api_call", "db_query", "computation")
    task_type: str
    
    # Task-specific configuration and parameters
    configuration: TaskConfiguration
    
    # Tenant identifier for multitenant support
    tenant_id: str
    
    # Metadata about the task
    metadata: Dict[str, str]
    
    def __post_init__(self):
        """Validate task after initialization"""
        if not self.task_id:
            raise ValueError("task_id cannot be empty")
        if not self.task_type:
            raise ValueError("task_type cannot be empty")
        if not self.tenant_id:
            raise ValueError("tenant_id cannot be empty") 