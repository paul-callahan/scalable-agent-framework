"""
Plan base class for the agentic framework.

Plans represent decision logic for task orchestration. They take TaskResults as input
and return PlanResults with next_task_names to determine which tasks to execute next.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Set
from pathlib import Path

from agentic_common.pb import plan_pb2


class DeprecatedPlanExecutor(ABC):
    """
    DEPRECATED: Base class for all plans in the agentic framework.
    
    This class is deprecated and will be removed in a future version.
    Use the new Plan data class for graph structure instead.
    
    Plans implement decision logic for task orchestration. They take TaskResults
    as input and return PlanResults with next_task_names to determine which tasks
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


class Plan:
    """
    Represents a plan in the agent graph specification.
    
    A plan is a node in the agent graph that processes results from upstream tasks
    and produces a plan result that can be consumed by downstream tasks. Each plan
    has a unique name and is associated with a Python subproject directory containing
    the plan implementation.
    
    The plan's Python subproject should contain:
    - A plan.py file with a plan(upstream_results: List[TaskResult]) -> PlanResult function
    - A requirements.txt file listing dependencies
    
    Plans can have multiple upstream tasks feeding into them, and can feed into
    multiple downstream tasks, forming a flexible graph structure.
    """
    
    def __init__(self, name: str, label: str, plan_source: Path, upstream_task_ids: Set[str]):
        """
        Initialize a Plan.
        
        Args:
            name: The unique identifier for this plan
            label: The human-readable label for this plan
            plan_source: Path to the Python subproject directory containing the plan implementation
            upstream_task_ids: Set of task IDs that feed into this plan
            
        Raises:
            ValueError: If validation fails
        """
        if not name or not name.strip():
            raise ValueError("Plan name cannot be null or empty")
        if plan_source is None:
            raise ValueError("Plan source cannot be null")
        if upstream_task_ids is None:
            upstream_task_ids = set()
            
        self.name = name
        self.label = label
        self.plan_source = plan_source
        self.upstream_task_ids = upstream_task_ids
    
    @classmethod
    def of(cls, name: str, plan_source: Path) -> "Plan":
        """
        Creates a new Plan with the specified name and source directory.
        
        Args:
            name: The plan name
            plan_source: The plan source directory
            
        Returns:
            A new Plan with no upstream tasks
        """
        return cls(name, name, plan_source, set())
    
    @classmethod
    def of_with_upstream(cls, name: str, plan_source: Path, upstream_task_ids: Set[str]) -> "Plan":
        """
        Creates a new Plan with the specified name, source directory, and upstream tasks.
        
        Args:
            name: The plan name
            plan_source: The plan source directory
            upstream_task_ids: The upstream task IDs
            
        Returns:
            A new Plan
        """
        return cls(name, name, plan_source, upstream_task_ids)
    
    def with_upstream_task(self, task_id: str) -> "Plan":
        """
        Returns a new Plan with an additional upstream task.
        
        Args:
            task_id: The task ID to add as upstream
            
        Returns:
            A new Plan with the additional upstream task
        """
        new_upstream_tasks = set(self.upstream_task_ids)
        new_upstream_tasks.add(task_id)
        return Plan(self.name, self.label, self.plan_source, new_upstream_tasks)
    
    def with_upstream_tasks(self, task_ids: Set[str]) -> "Plan":
        """
        Returns a new Plan with the specified upstream tasks.
        
        Args:
            task_ids: The task IDs to set as upstream
            
        Returns:
            A new Plan with the specified upstream tasks
        """
        return Plan(self.name, self.label, self.plan_source, set(task_ids))
    
    def __eq__(self, other):
        if not isinstance(other, Plan):
            return False
        return (self.name == other.name and 
                self.label == other.label and 
                self.plan_source == other.plan_source and 
                self.upstream_task_ids == other.upstream_task_ids)
    
    def __hash__(self):
        return hash((self.name, self.label, self.plan_source, tuple(sorted(self.upstream_task_ids))))
    
    def __repr__(self):
        return f"Plan(name='{self.name}', label='{self.label}', plan_source={self.plan_source}, upstream_task_ids={self.upstream_task_ids})"


class PlanResult:
    """
    Result of a plan execution.

    Contains the next task IDs to execute and optional metadata about the planning
    decision.
    """

    def __init__(
        self,
        next_task_names: List[str],
        error_message: Optional[str] = None
    ):
        """
        Initialize a PlanResult.

        Args:
            next_task_names: List of task names to execute next
            error_message: Optional error message if planning failed
        """
        self.next_task_names = next_task_names
        self.error_message = error_message

    def to_protobuf(self) -> "plan_pb2.PlanResult":
        """
        Convert this result to a PlanResult protobuf message.

        Returns:
            PlanResult protobuf message
        """
        return plan_pb2.PlanResult(
            next_task_names=self.next_task_names,
            error_message=self.error_message or ""
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
            next_task_names=list(proto.next_task_names),
            error_message=proto.error_message if proto.error_message else None
        )