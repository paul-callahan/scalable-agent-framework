"""
Protobuf utilities for consistent serialization and deserialization.

This module provides utilities for consistent protobuf message handling
across all Python microservices in the agentic framework.
"""

import json
from typing import Any, Dict, Optional, Union
from datetime import datetime

from .pb import TaskExecution, PlanExecution, PlanInput, TaskInput, TaskResult, PlanResult, ExecutionHeader


class ProtobufUtils:
    """
    Utilities for consistent protobuf message handling.
    
    Provides methods for serialization, deserialization, and validation
    of protobuf messages across all Python services.
    """
    
    @staticmethod
    def serialize_task_execution(task_execution: TaskExecution) -> bytes:
        """
        Serialize TaskExecution protobuf message to bytes.
        
        Args:
            task_execution: TaskExecution protobuf message
            
        Returns:
            Serialized bytes
            
        Raises:
            ValueError: If serialization fails
        """
        try:
            return task_execution.SerializeToString()
        except Exception as e:
            raise ValueError(f"Failed to serialize TaskExecution: {e}")
    
    @staticmethod
    def deserialize_task_execution(message_bytes: bytes) -> TaskExecution:
        """
        Deserialize bytes to TaskExecution protobuf message.
        
        Args:
            message_bytes: Serialized protobuf message bytes
            
        Returns:
            TaskExecution protobuf message
            
        Raises:
            ValueError: If deserialization fails
        """
        try:
            task_execution = TaskExecution()
            task_execution.ParseFromString(message_bytes)
            return task_execution
        except Exception as e:
            raise ValueError(f"Failed to deserialize TaskExecution: {e}")
    
    @staticmethod
    def serialize_plan_input(plan_input: PlanInput) -> bytes:
        """
        Serialize PlanInput protobuf message to bytes.
        
        Args:
            plan_input: PlanInput protobuf message
            
        Returns:
            Serialized bytes
            
        Raises:
            ValueError: If serialization fails
        """
        try:
            return plan_input.SerializeToString()
        except Exception as e:
            raise ValueError(f"Failed to serialize PlanInput: {e}")
    
    @staticmethod
    def deserialize_plan_input(message_bytes: bytes) -> PlanInput:
        """
        Deserialize bytes to PlanInput protobuf message.
        
        Args:
            message_bytes: Serialized protobuf message bytes
            
        Returns:
            PlanInput protobuf message
            
        Raises:
            ValueError: If deserialization fails
        """
        try:
            plan_input = PlanInput()
            plan_input.ParseFromString(message_bytes)
            return plan_input
        except Exception as e:
            raise ValueError(f"Failed to deserialize PlanInput: {e}")
    
    @staticmethod
    def serialize_task_input(task_input: TaskInput) -> bytes:
        """
        Serialize TaskInput protobuf message to bytes.
        
        Args:
            task_input: TaskInput protobuf message
            
        Returns:
            Serialized bytes
            
        Raises:
            ValueError: If serialization fails
        """
        try:
            return task_input.SerializeToString()
        except Exception as e:
            raise ValueError(f"Failed to serialize TaskInput: {e}")
    
    @staticmethod
    def deserialize_task_input(message_bytes: bytes) -> TaskInput:
        """
        Deserialize bytes to TaskInput protobuf message.
        
        Args:
            message_bytes: Serialized protobuf message bytes
            
        Returns:
            TaskInput protobuf message
            
        Raises:
            ValueError: If deserialization fails
        """
        try:
            task_input = TaskInput()
            task_input.ParseFromString(message_bytes)
            return task_input
        except Exception as e:
            raise ValueError(f"Failed to deserialize TaskInput: {e}")
    
    @staticmethod
    def serialize_plan_execution(plan_execution: PlanExecution) -> bytes:
        """
        Serialize PlanExecution protobuf message to bytes.
        
        Args:
            plan_execution: PlanExecution protobuf message
            
        Returns:
            Serialized bytes
            
        Raises:
            ValueError: If serialization fails
        """
        try:
            return plan_execution.SerializeToString()
        except Exception as e:
            raise ValueError(f"Failed to serialize PlanExecution: {e}")
    
    @staticmethod
    def deserialize_plan_execution(message_bytes: bytes) -> PlanExecution:
        """
        Deserialize bytes to PlanExecution protobuf message.
        
        Args:
            message_bytes: Serialized protobuf message bytes
            
        Returns:
            PlanExecution protobuf message
            
        Raises:
            ValueError: If deserialization fails
        """
        try:
            plan_execution = PlanExecution()
            plan_execution.ParseFromString(message_bytes)
            return plan_execution
        except Exception as e:
            raise ValueError(f"Failed to deserialize PlanExecution: {e}")
    
    @staticmethod
    def create_execution_header(
        execution_id: str,
        tenant_id: str,
        status: int,
        graph_id: str = "",
        lifetime_id: str = "",
        attempt: int = 1,
        iteration_idx: int = 0,
        edge_taken: str = ""
    ) -> ExecutionHeader:
        """
        Create a consistent ExecutionHeader protobuf message.
        
        Args:
            execution_id: Unique execution identifier
            tenant_id: Tenant identifier
            status: Execution status enum value
            graph_id: Graph identifier
            lifetime_id: Lifetime identifier
            attempt: Execution attempt number
            iteration_idx: Current iteration index
            edge_taken: ID of the edge that led to this execution
            
        Returns:
            ExecutionHeader protobuf message
        """
        header = ExecutionHeader()
        header.exec_id = execution_id
        header.tenant_id = tenant_id
        header.status = status
        header.graph_id = graph_id
        header.lifetime_id = lifetime_id
        header.attempt = attempt
        header.iteration_idx = iteration_idx
        header.edge_taken = edge_taken
        header.created_at = datetime.utcnow().isoformat() + "Z"
        return header
    
    @staticmethod
    def create_task_result(
        error_message: str = "",
        inline_data: Optional[Dict[str, Any]] = None,
        external_data_uri: str = "",
        external_data_metadata: Optional[Dict[str, str]] = None
    ) -> TaskResult:
        """
        Create a consistent TaskResult protobuf message.
        
        Args:
            error_message: Error message if execution failed
            inline_data: Inline data dictionary
            external_data_uri: URI reference to external data
            external_data_metadata: Metadata for external data
            
        Returns:
            TaskResult protobuf message
        """
        result = TaskResult()
        result.error_message = error_message
        
        if inline_data:
            # Convert dictionary to protobuf Any field
            from google.protobuf import any_pb2, struct_pb2
            any_msg = any_pb2.Any()
            
            # Create a Value message to hold the JSON data
            value_msg = struct_pb2.Value()
            value_msg.string_value = json.dumps(inline_data)
            any_msg.Pack(value_msg)
            result.inline_data.CopyFrom(any_msg)
        elif external_data_uri:
            # Create external data structure
            external_data = result.external_data
            external_data.uri = external_data_uri
            if external_data_metadata:
                external_data.metadata.update(external_data_metadata)
        
        return result
    
    @staticmethod
    def create_plan_result(
        next_task_names: Optional[list] = None,
        error_message: str = "",
        upstream_tasks_results: Optional[list] = None
    ) -> PlanResult:
        """
        Create a consistent PlanResult protobuf message.
        
        Args:
            next_task_names: List of next task names
            error_message: Error message if planning failed
            upstream_tasks_results: List of upstream TaskResult objects
            
        Returns:
            PlanResult protobuf message
        """
        result = PlanResult()
        result.error_message = error_message
        
        if next_task_names:
            result.next_task_names.extend(next_task_names)
        
        if upstream_tasks_results:
            result.upstream_tasks_results.extend(upstream_tasks_results)
        
        return result
    
    @staticmethod
    def validate_task_execution(task_execution: TaskExecution) -> bool:
        """
        Validate TaskExecution protobuf message.
        
        Args:
            task_execution: TaskExecution protobuf message
            
        Returns:
            True if valid, False otherwise
        """
        try:
            # Check required fields
            if not task_execution.header.exec_id:
                return False
            if not task_execution.header.tenant_id:
                return False
            
            return True
        except Exception:
            return False
    
    @staticmethod
    def validate_plan_execution(plan_execution: PlanExecution) -> bool:
        """
        Validate PlanExecution protobuf message.
        
        Args:
            plan_execution: PlanExecution protobuf message
            
        Returns:
            True if valid, False otherwise
        """
        try:
            # Check required fields
            if not plan_execution.header.exec_id:
                return False
            if not plan_execution.header.tenant_id:
                return False
            
            return True
        except Exception:
            return False
    
    @staticmethod
    def extract_task_result_data(task_result: TaskResult) -> Optional[Dict[str, Any]]:
        """
        Extract task result data from protobuf message.
        
        Args:
            task_result: TaskResult protobuf message
            
        Returns:
            Dictionary with result data or None
        """
        if task_result.HasField("inline_data"):
            try:
                # Convert Any protobuf to dictionary
                from google.protobuf import struct_pb2
                value_msg = struct_pb2.Value()
                task_result.inline_data.Unpack(value_msg)
                data = json.loads(value_msg.string_value)
                return {
                    "type": "inline",
                    "data": data,
                }
            except Exception:
                return None
        elif task_result.HasField("external_data"):
            external_data = task_result.external_data
            return {
                "type": "external",
                "uri": external_data.uri,
                "metadata": dict(external_data.metadata),
            }
        else:
            return None
    
    @staticmethod
    def extract_plan_result_data(plan_result: PlanResult) -> Dict[str, Any]:
        """
        Extract plan result data from protobuf message.
        
        Args:
            plan_result: PlanResult protobuf message
            
        Returns:
            Dictionary with result data
        """
        return {
            "next_task_names": list(plan_result.next_task_names),
            "error_message": plan_result.error_message,
        }
    
    @staticmethod
    def to_json_safe_dict(protobuf_message) -> Dict[str, Any]:
        """
        Convert protobuf message to JSON-safe dictionary.
        
        Args:
            protobuf_message: Protobuf message
            
        Returns:
            JSON-safe dictionary
        """
        try:
            # Use protobuf's built-in JSON serialization
            from google.protobuf.json_format import MessageToDict
            return MessageToDict(protobuf_message, including_default_value_fields=True)
        except Exception as e:
            # Fallback to manual conversion
            try:
                return MessageToDict(protobuf_message)
            except Exception as e2:
                raise ValueError(f"Failed to convert protobuf to JSON-safe dict: {e}, fallback: {e2}")
    
    @staticmethod
    def from_json_safe_dict(data: Dict[str, Any], message_class) -> Any:
        """
        Convert JSON-safe dictionary to protobuf message.
        
        Args:
            data: JSON-safe dictionary
            message_class: Protobuf message class
            
        Returns:
            Protobuf message
        """
        try:
            # Use protobuf's built-in JSON deserialization
            from google.protobuf.json_format import ParseDict
            return ParseDict(data, message_class())
        except Exception as e:
            raise ValueError(f"Failed to convert JSON-safe dict to protobuf: {e}") 