"""
Task base class for the agentic framework.

Tasks represent individual units of work that can be executed by the framework.
Each task has a tenant_id and implements an execute method that returns a TaskResult.
"""

import json
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, Optional, Union

try:
    from ..pb import task_pb2, common_pb2
    from google.protobuf import any_pb2
except ImportError:
    # Protobuf files not yet generated
    pass


class Task(ABC):
    """
    Base class for all tasks in the agentic framework.
    
    Tasks are individual units of work that can be executed. They have a tenant_id
    for multi-tenancy and implement an execute method that returns a TaskResult.
    """
    
    def __init__(self, tenant_id: str, task_type: str, parameters: Optional[Dict[str, Any]] = None):
        """
        Initialize a new Task.
        
        Args:
            tenant_id: Tenant identifier for multi-tenancy
            task_type: Type identifier for this task
            parameters: Optional parameters for task execution
        """
        self.tenant_id = tenant_id
        self.task_type = task_type
        self.parameters = parameters or {}
        self.id = str(uuid.uuid4())
    
    @abstractmethod
    async def execute(self, context: Optional[Dict[str, Any]] = None) -> 'TaskResult':
        """
        Execute the task and return a result.
        
        Args:
            context: Optional execution context
            
        Returns:
            TaskResult containing the execution output
        """
        pass
    
    def to_protobuf(self) -> 'task_pb2.TaskExecution':
        """
        Convert this task to a TaskExecution protobuf message.
        
        Returns:
            TaskExecution protobuf message
        """
        header = common_pb2.ExecutionHeader(
            id=self.id,
            tenant_id=self.tenant_id,
            status=common_pb2.EXECUTION_STATUS_PENDING,
            created_at=datetime.utcnow().isoformat(),
            attempt=1,
            iteration_idx=0
        )
        
        return task_pb2.TaskExecution(
            header=header,
            task_type=self.task_type,
            parameters=json.dumps(self.parameters)
        )
    
    @classmethod
    @abstractmethod
    def from_protobuf(cls, proto: 'task_pb2.TaskExecution') -> 'Task':
        """
        Create a Task from a TaskExecution protobuf message.
        
        Args:
            proto: TaskExecution protobuf message
            
        Returns:
            Task instance
        """
        pass
    
    def serialize(self) -> Dict[str, Any]:
        """
        Serialize the task to a dictionary.
        
        Returns:
            Dictionary representation of the task
        """
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'task_type': self.task_type,
            'parameters': self.parameters
        }
    
    @classmethod
    @abstractmethod
    def deserialize(cls, data: Dict[str, Any]) -> 'Task':
        """
        Deserialize a task from a dictionary.
        
        Args:
            data: Dictionary representation of the task
            
        Returns:
            Task instance
        """
        pass


class TaskResult:
    """
    Result of a task execution.
    
    Contains either inline data or a URI reference to external storage,
    along with metadata about the result.
    """
    
    def __init__(self, 
                 data: Optional[Union[Any, str]] = None,
                 mime_type: str = "application/json",
                 size_bytes: int = 0,
                 error_message: Optional[str] = None):
        """
        Initialize a TaskResult.
        
        Args:
            data: Result data (inline object or URI string)
            mime_type: MIME type of the result data
            size_bytes: Size of the result data in bytes
            error_message: Optional error message if execution failed
        """
        self.data = data
        self.mime_type = mime_type
        self.size_bytes = size_bytes
        self.error_message = error_message
    
    def to_protobuf(self) -> 'task_pb2.TaskResult':
        """
        Convert this result to a TaskResult protobuf message.
        
        Returns:
            TaskResult protobuf message
        """
        result = task_pb2.TaskResult(
            mime_type=self.mime_type,
            size_bytes=self.size_bytes,
            error_message=self.error_message or ""
        )
        
        if isinstance(self.data, str):
            # URI reference
            result.uri = self.data
        elif self.data is not None:
            # Inline data
            any_msg = any_pb2.Any()
            try:
                any_msg.Pack(self.data)
                result.inline_data.CopyFrom(any_msg)
            except Exception as e:
                # Fallback to JSON serialization if protobuf packing fails
                try:
                    json_data = json.dumps(self.data)
                    # Create a simple protobuf message with JSON data
                    from google.protobuf import struct_pb2
                    json_struct = struct_pb2.Value()
                    json_struct.string_value = json_data
                    any_msg.Pack(json_struct)
                    result.inline_data.CopyFrom(any_msg)
                    # Update MIME type to indicate JSON fallback
                    result.mime_type = "application/json"
                except Exception as json_error:
                    # If JSON serialization also fails, store error information
                    error_data = {
                        "error": "Serialization failed",
                        "original_error": str(e),
                        "json_error": str(json_error),
                        "data_type": type(self.data).__name__
                    }
                    error_struct = struct_pb2.Value()
                    error_struct.string_value = json.dumps(error_data)
                    any_msg.Pack(error_struct)
                    result.inline_data.CopyFrom(any_msg)
                    result.mime_type = "application/json"
                    result.error_message = f"Data serialization failed: {str(e)}"
        
        return result
    
    @classmethod
    def from_protobuf(cls, proto: 'task_pb2.TaskResult') -> 'TaskResult':
        """
        Create a TaskResult from a protobuf message.
        
        Args:
            proto: TaskResult protobuf message
            
        Returns:
            TaskResult instance
        """
        data = None
        if proto.HasField('inline_data'):
            data = proto.inline_data
        elif proto.HasField('uri'):
            data = proto.uri
        
        return cls(
            data=data,
            mime_type=proto.mime_type,
            size_bytes=proto.size_bytes,
            error_message=proto.error_message if proto.error_message else None
        ) 