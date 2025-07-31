"""
Plan base class for the agentic framework.

Plans represent decision logic for task orchestration. They take TaskResults as input
and return PlanResults with next_task_ids to determine which tasks to execute next.
"""

import json
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

try:
    from ..pb import plan_pb2, common_pb2
    from .task import TaskResult
except ImportError:
    # Protobuf files not yet generated
    pass


class Plan(ABC):
    """
    Base class for all plans in the agentic framework.
    
    Plans implement decision logic for task orchestration. They take TaskResults
    as input and return PlanResults with next_task_ids to determine which tasks
    to execute next.
    """
    
    def __init__(self, tenant_id: str, plan_type: str, parameters: Optional[Dict[str, Any]] = None):
        """
        Initialize a new Plan.
        
        Args:
            tenant_id: Tenant identifier for multi-tenancy
            plan_type: Type identifier for this plan
            parameters: Optional parameters for plan execution
        """
        self.tenant_id = tenant_id
        self.plan_type = plan_type
        self.parameters = parameters or {}
        self.id = str(uuid.uuid4())
    
    @abstractmethod
    async def execute(self, task_result: TaskResult, context: Optional[Dict[str, Any]] = None) -> 'PlanResult':
        """
        Execute the plan and return a result with next task IDs.
        
        Args:
            task_result: Result from the input task that triggered this plan
            context: Optional execution context
            
        Returns:
            PlanResult containing the next task IDs to execute
        """
        pass
    
    def to_protobuf(self) -> 'plan_pb2.PlanExecution':
        """
        Convert this plan to a PlanExecution protobuf message.
        
        Returns:
            PlanExecution protobuf message
        """
        header = common_pb2.ExecutionHeader(
            id=self.id,
            tenant_id=self.tenant_id,
            status=common_pb2.EXECUTION_STATUS_PENDING,
            created_at=datetime.utcnow().isoformat(),
            attempt=1,
            iteration_idx=0
        )
        
        return plan_pb2.PlanExecution(
            header=header,
            plan_type=self.plan_type,
            parameters=json.dumps(self.parameters)
        )
    
    @classmethod
    @abstractmethod
    def from_protobuf(cls, proto: 'plan_pb2.PlanExecution') -> 'Plan':
        """
        Create a Plan from a PlanExecution protobuf message.
        
        Args:
            proto: PlanExecution protobuf message
            
        Returns:
            Plan instance
        """
        pass
    
    def serialize(self) -> Dict[str, Any]:
        """
        Serialize the plan to a dictionary.
        
        Returns:
            Dictionary representation of the plan
        """
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'plan_type': self.plan_type,
            'parameters': self.parameters
        }
    
    @classmethod
    @abstractmethod
    def deserialize(cls, data: Dict[str, Any]) -> 'Plan':
        """
        Deserialize a plan from a dictionary.
        
        Args:
            data: Dictionary representation of the plan
            
        Returns:
            Plan instance
        """
        pass


class PlanResult:
    """
    Result of a plan execution.
    
    Contains the next task IDs to execute and optional metadata about the planning
    decision.
    """
    
    def __init__(self, 
                 next_task_ids: List[str],
                 metadata: Optional[Dict[str, str]] = None,
                 error_message: Optional[str] = None,
                 confidence: float = 1.0):
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
    
    def to_protobuf(self) -> 'plan_pb2.PlanResult':
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
    def from_protobuf(cls, proto: 'plan_pb2.PlanResult') -> 'PlanResult':
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