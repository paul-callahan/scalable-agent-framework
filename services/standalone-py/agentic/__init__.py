"""
Agentic Framework - A scalable agent orchestration framework.

This package provides the core abstractions for building agentic applications:
- Task: Individual units of work
- Plan: Decision logic for task orchestration  
- AgentGraph: Immutable graph templates
- AgentLifetime: Runtime execution instances
"""

from .core.task import Task, DeprecatedTaskExecutor
from .core.plan import Plan, DeprecatedPlanExecutor
from .core.graph import AgentGraph
from .core.lifetime import AgentLifetime
from .core.edge import Edge

# Re-export key protobuf types for convenience
from .pb import task_pb2, plan_pb2, common_pb2

# Re-export message bus components
from .message_bus import InMemoryBroker

# Re-export service classes
from .data_plane.service import DataPlaneService
from .control_plane.service import ControlPlaneService
from .executors.task_executor import TaskExecutorService
from .executors.plan_executor import PlanExecutorService

__version__ = "0.1.0"
__all__ = [
    "Task",
    "Plan", 
    "DeprecatedTaskExecutor",
    "DeprecatedPlanExecutor",
    "AgentGraph",
    "AgentLifetime",
    "Edge",
    "InMemoryBroker",
    "DataPlaneService",
    "ControlPlaneService",
    "TaskExecutorService",
    "PlanExecutorService",
] 