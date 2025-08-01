"""
Plan base class for the agentic framework.

Plans represent decision logic for task orchestration. They take TaskResults as input
and return PlanResults with next_task_ids to determine which tasks to execute next.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional

from ..pb import plan_pb2


class Plan(ABC):
    """
    Base class for all plans in the agentic framework.

    Plans implement decision logic for task orchestration. They take TaskResults
    as input and return PlanResults with next_task_ids to determine which tasks
    to execute next.
    """

    @abstractmethod
    async def plan(self, lastResult: "TaskResult") -> "PlanResult":
        """
        Execute the planning logic based on the last task result.

        Args:
            lastResult: Result from the previous task execution

        Returns:
            PlanResult containing the next task IDs to execute
        """
        pass


class PlanResult:
    """
    Result of a plan execution.

    Contains the next task IDs to execute and optional metadata about the planning
    decision.
    """

    def __init__(
        self,
        next_task_ids: List[str],
        metadata: Optional[Dict[str, str]] = None,
        error_message: Optional[str] = None,
        confidence: float = 1.0
    ):
        """
        Initialize a PlanResult.

        Args:
            next_task_ids: List of task IDs to execute next
            metadata: Optional metadata about the planning decision
            error_message: Optional error message if planning failed
            confidence: Planning confidence score (0.0 to 1.0)
        """
        self.next_task_ids = next_task_ids
        self.metadata = metadata or {}
        self.error_message = error_message
        self.confidence = max(0.0, min(1.0, confidence))  # Clamp to [0, 1]

    def to_protobuf(self) -> "plan_pb2.PlanResult":
        """
        Convert this result to a PlanResult protobuf message.

        Returns:
            PlanResult protobuf message
        """
        return plan_pb2.PlanResult(
            next_task_ids=self.next_task_ids,
            metadata=self.metadata,
            error_message=self.error_message or "",
            confidence=self.confidence
        )

    @classmethod
    def from_protobuf(cls, proto: "plan_pb2.PlanResult") -> "PlanResult":
        """
        Create a PlanResult from a protobuf message.

        Args:
            proto: PlanResult protobuf message

        Returns:
            PlanResult instance
        """
        return cls(
            next_task_ids=list(proto.next_task_ids),
            metadata=dict(proto.metadata),
            error_message=proto.error_message if proto.error_message else None,
            confidence=proto.confidence
        )