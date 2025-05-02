from dataclasses import dataclass
from typing import Dict, Union
from .task import Task
from .plan import Plan


@dataclass
class GraphNode:
    """Union type that can contain either a Task or Plan"""
    
    # Unique node identifier
    node_id: str
    
    # Node type (task or plan)
    node_type: str
    
    # The actual node content
    node: Union[Task, Plan]
    
    # Node metadata
    metadata: Dict[str, str]
    
    def __post_init__(self):
        """Validate graph node after initialization"""
        if not self.node_id:
            raise ValueError("node_id cannot be empty")
        if not self.node_type:
            raise ValueError("node_type cannot be empty")
        if self.node_type not in ["task", "plan"]:
            raise ValueError("node_type must be 'task' or 'plan'")
        if not self.node:
            raise ValueError("node cannot be None") 