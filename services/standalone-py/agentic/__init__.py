"""
Agentic Framework - A scalable agent orchestration framework.

This package provides the core abstractions for building agentic applications:
- Task: Individual units of work
- Plan: Decision logic for task orchestration  
- AgentGraph: Immutable graph templates
- AgentLifetime: Runtime execution instances
"""

from .core.task import Task
from .core.plan import Plan
from .core.graph import AgentGraph
from .core.lifetime import AgentLifetime
from .core.edge import Edge

# Re-export key protobuf types for convenience
try:
    from .pb import task_pb2, plan_pb2, common_pb2, services_pb2
    from .pb import task_pb2_grpc, plan_pb2_grpc, services_pb2_grpc
except ImportError:
    # Protobuf files not yet generated
    pass

__version__ = "0.1.0"
__all__ = [
    "Task",
    "Plan", 
    "AgentGraph",
    "AgentLifetime",
    "Edge",
] 