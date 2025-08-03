"""
Protobuf message imports for agentic microservices.

This module re-exports all protobuf generated classes from locally generated
protobuf files. Generate the protobuf files using scripts/gen_proto.sh.

This centralizes protobuf imports so microservices don't need to manage
proto generation individually.
"""

# Import all protobuf generated classes from local files
try:
    from .common_pb2 import ExecutionHeader
    from .task_pb2 import TaskExecution, TaskResult
    from .plan_pb2 import PlanExecution, PlanResult
except ImportError:
    raise ImportError(
        "No protobuf files found. Please generate them using:\n"
        "./scripts/gen_proto.sh"
    )

__all__ = [
    # Common protobuf messages
    "ExecutionHeader",
    # Task-related protobuf messages
    "TaskExecution",
    "TaskResult",
    # Plan-related protobuf messages
    "PlanExecution",
    "PlanResult",
] 