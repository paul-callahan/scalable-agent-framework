"""
Task base class for the agentic framework.

Tasks represent individual units of work that can be executed by the framework.
Each task takes the result of the previous plan and returns a TaskResult.
"""

import json
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Union

from ..pb import task_pb2
from google.protobuf import any_pb2

# PlanResult is imported as a string type annotation to avoid circular imports


class Task(ABC):
    """
    Base class for all tasks in the agentic framework.

    Tasks are individual units of work that can be executed. Each task
    takes the result of the previous plan and returns a TaskResult.
    """

    @abstractmethod
    async def execute(self, lastResult: "PlanResult") -> "TaskResult":
        """
        Execute the task based on the last plan result.

        Args:
            lastResult: Result from the previous plan execution

        Returns:
            TaskResult containing the execution output
        """
        pass


class TaskResult:
    """
    Result of a task execution.

    Contains either inline data or a URI reference to external storage,
    along with metadata about the result.
    """

    def __init__(
        self,
        data: Optional[Union[Any, str]] = None,
        mime_type: str = "application/json",
        size_bytes: int = 0,
        error_message: Optional[str] = None
    ):
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

    def to_protobuf(self) -> "task_pb2.TaskResult":
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
                    from google.protobuf import struct_pb2
                    error_struct = struct_pb2.Value()
                    error_struct.string_value = json.dumps(error_data)
                    any_msg.Pack(error_struct)
                    result.inline_data.CopyFrom(any_msg)
                    result.mime_type = "application/json"
                    result.error_message = f"Data serialization failed: {str(e)}"

        return result

    @classmethod
    def from_protobuf(cls, proto: "task_pb2.TaskResult") -> "TaskResult":
        """
        Create a TaskResult from a protobuf message.

        Args:
            proto: TaskResult protobuf message

        Returns:
            TaskResult instance
        """
        data = None
        if proto.HasField("inline_data"):
            data = proto.inline_data
        elif proto.HasField("uri"):
            data = proto.uri

        return cls(
            data=data,
            mime_type=proto.mime_type,
            size_bytes=proto.size_bytes,
            error_message=proto.error_message if proto.error_message else None
        )