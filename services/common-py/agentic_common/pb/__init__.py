"""
Protobuf message imports for agentic common package.

This module re-exports all protobuf generated classes from locally generated
protobuf files. Generate the protobuf files using scripts/gen_proto.sh.

This centralizes protobuf imports so microservices don't need to manage
proto generation individually.
"""

# Import all protobuf generated classes from local files
try:
    from .common_pb2 import ExecutionHeader, ExecutionStatus, TaskExecution, TaskResult,  PlanExecution, PlanResult, PlanInput, TaskInput
except ImportError as e:
    raise e
    # raise ImportError(
    #     "No protobuf files found. Please generate them using:\n"
    #     "./scripts/gen_proto.sh"
    # ) from e

__all__ = [
    # Common protobuf messages
    "ExecutionHeader",
    "ExecutionStatus",
    # Task-related protobuf messages
    "TaskExecution",
    "TaskResult",
    "TaskInput",
    # Plan-related protobuf messages
    "PlanExecution",
    "PlanResult",
    "PlanInput",
] 