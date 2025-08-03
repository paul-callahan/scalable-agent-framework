"""
Executor microservice for agentic framework.

This service consumes TaskResult and PlanResult messages, executes the
corresponding Task or Plan classes, and emits new TaskExecution or
PlanExecution messages back to the data plane.
"""

from .service import ExecutorService
from .registry import TaskRegistry, PlanRegistry
from .task_executor import TaskExecutor
from .plan_executor import PlanExecutor

__all__ = [
    "ExecutorService",
    "TaskRegistry", 
    "PlanRegistry",
    "TaskExecutor",
    "PlanExecutor",
]

__version__ = "0.1.0" 