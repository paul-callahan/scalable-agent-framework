"""
Task execution logic for executor microservice.

This module implements task execution logic. Consumes PlanResult messages
from task-results_{tenant_id} topics, looks up the corresponding Task class
from the registry, executes the task with the PlanResult as input, and
emits TaskExecution messages.
"""

import json
from typing import Any, Dict, Optional

from structlog import get_logger

from agentic.core.task import DeprecatedTaskExecutor, TaskResult
from agentic.core.plan import PlanResult
from .registry import TaskRegistry

logger = get_logger(__name__)


class TaskExecutor:
    """
    Task executor for the executor service.
    
    Handles task execution by looking up DeprecatedTaskExecutor classes from the registry,
    executing them with PlanResult input, and producing TaskExecution messages.
    """
    
    def __init__(self, task_registry: TaskRegistry):
        """
        Initialize the task executor.
        
        Args:
            task_registry: Task registry instance
        """
        self.task_registry = task_registry
    
    async def execute_task(
        self,
        task_type: str,
        plan_result: PlanResult,
        execution_id: str,
        tenant_id: str,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        Execute a task with the given plan result.
        
        Args:
            task_type: Type of task to execute
            plan_result: PlanResult to use as input
            execution_id: Unique execution identifier
            tenant_id: Tenant identifier
            **kwargs: Additional arguments for task creation
            
        Returns:
            TaskExecution data or None if execution failed
        """
        try:
            logger.info("Starting task execution", 
                       task_type=task_type,
                       execution_id=execution_id,
                       tenant_id=tenant_id)
            
            # Look up task class from registry
            task_class = self.task_registry.get_task_class(task_type)
            if not task_class:
                logger.error("Task type not found in registry", 
                            task_type=task_type,
                            execution_id=execution_id)
                return None
            
            # Create task instance
            task = self.task_registry.create_task(task_type, **kwargs)
            if not task:
                logger.error("Failed to create task instance", 
                            task_type=task_type,
                            execution_id=execution_id)
                return None
            
            # Execute task
            task_result = await task.execute(plan_result)
            
            if not isinstance(task_result, TaskResult):
                logger.error("Task did not return TaskResult", 
                            task_type=task_type,
                            execution_id=execution_id,
                            result_type=type(task_result))
                return None
            
            # Convert to protobuf
            task_result_proto = task_result.to_protobuf()
            
            # Create execution data
            execution_data = {
                "execution_id": execution_id,
                "task_type": task_type,
                "tenant_id": tenant_id,
                "result": {
                    "data": self._extract_task_result_data(task_result),
                    "mime_type": task_result.mime_type,
                    "size_bytes": task_result.size_bytes,
                    "error_message": task_result.error_message,
                },
                "status": "SUCCEEDED" if not task_result.error_message else "FAILED",
            }
            
            logger.info("Task execution completed", 
                       task_type=task_type,
                       execution_id=execution_id,
                       status=execution_data["status"])
            
            return execution_data
            
        except Exception as e:
            logger.error("Task execution failed", 
                        task_type=task_type,
                        execution_id=execution_id,
                        error=str(e))
            
            # Return error execution data
            return {
                "execution_id": execution_id,
                "task_type": task_type,
                "tenant_id": tenant_id,
                "result": {
                    "data": None,
                    "mime_type": "application/json",
                    "size_bytes": 0,
                    "error_message": str(e),
                },
                "status": "FAILED",
            }
    
    def _extract_task_result_data(self, task_result: TaskResult) -> Optional[Dict[str, Any]]:
        """
        Extract task result data for serialization.
        
        Args:
            task_result: TaskResult instance
            
        Returns:
            Dictionary with result data or None
        """
        if task_result.data is None:
            return None
        
        if isinstance(task_result.data, str):
            # URI reference
            return {
                "type": "uri",
                "uri": task_result.data,
            }
        else:
            # Inline data - try to serialize
            try:
                if hasattr(task_result.data, 'to_dict'):
                    return {
                        "type": "inline",
                        "data": task_result.data.to_dict(),
                    }
                elif hasattr(task_result.data, '__dict__'):
                    return {
                        "type": "inline",
                        "data": task_result.data.__dict__,
                    }
                else:
                    return {
                        "type": "inline",
                        "data": str(task_result.data),
                    }
            except Exception as e:
                logger.warning("Failed to serialize task result data", error=str(e))
                return {
                    "type": "inline",
                    "data": str(task_result.data),
                }
    
    def validate_task_type(self, task_type: str) -> bool:
        """
        Validate that a task type is registered.
        
        Args:
            task_type: Task type to validate
            
        Returns:
            True if task type is valid
        """
        return self.task_registry.is_task_registered(task_type)
    
    def get_available_task_types(self) -> list[str]:
        """
        Get list of available task types.
        
        Returns:
            List of registered task types
        """
        return self.task_registry.list_task_types()
    
    def get_task_info(self, task_type: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a task type.
        
        Args:
            task_type: Task type identifier
            
        Returns:
            Task information or None if not found
        """
        task_class = self.task_registry.get_task_class(task_type)
        if not task_class:
            return None
        
        return {
            "task_type": task_type,
            "class_name": task_class.__name__,
            "module": task_class.__module__,
            "doc": task_class.__doc__,
        } 