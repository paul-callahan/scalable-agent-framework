"""
Task executor service implementation.

This module implements the TaskExecutorService that consumes from task result queues,
processes task execution requests, and publishes completed results back to execution queues.
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, Optional, Callable, Any

from ..message_bus import InMemoryBroker
from ..pb import task_pb2, common_pb2
from ..core.logging import get_logger, log_metric, log_error


class TaskExecutorService:
    """
    Task executor service implementation.
    
    Handles task execution by consuming from result queues and publishing
    completed task executions back to execution queues.
    """
    
    def __init__(self, broker: InMemoryBroker):
        """
        Initialize the task executor service.
        
        Args:
            broker: In-memory message broker
        """
        self.broker = broker
        self.logger = get_logger(__name__)
        
        # Task registry for available task implementations
        self.task_registry: Dict[str, Callable] = {}
        
        # Initialize metrics
        self._tasks_executed = 0
        self._tasks_failed = 0
        self._messages_processed = 0
        self._errors = 0
        
        # Service state
        self._running = False
        self._consumer_task: Optional[asyncio.Task] = None
    
    def register_task(self, task_type: str, task_handler: Callable) -> None:
        """
        Register a task handler for a specific task type.
        
        Args:
            task_type: Task type identifier
            task_handler: Function to handle task execution
        """
        self.task_registry[task_type] = task_handler
        self.logger.info(f"Registered task handler for type: {task_type}")
    
    def _get_default_task_handler(self, task_type: str) -> Callable:
        """
        Get a default task handler for unknown task types.
        
        Args:
            task_type: Task type identifier
            
        Returns:
            Default task handler function
        """
        def default_handler(parameters: str) -> Dict[str, Any]:
            """Default task handler that returns a mock result."""
            return {
                "result": f"Mock result for task type: {task_type}",
                "status": "completed",
                "metadata": {
                    "task_type": task_type,
                    "handler": "default",
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
        
        return default_handler
    
    async def _execute_task(self, task_type: str, parameters: str, execution_id: str) -> task_pb2.TaskExecution:
        """
        Execute a task and return the result.
        
        Args:
            task_type: Task type identifier
            parameters: Task parameters (JSON string)
            execution_id: Execution identifier
            
        Returns:
            TaskExecution protobuf message with results
        """
        try:
            # Get task handler
            task_handler = self.task_registry.get(task_type, self._get_default_task_handler(task_type))
            
            # Parse parameters
            try:
                params_dict = json.loads(parameters) if parameters else {}
            except json.JSONDecodeError:
                params_dict = {"raw_parameters": parameters}
            
            # Execute task
            self.logger.debug(f"Executing task {task_type} with execution ID {execution_id}")
            result = task_handler(params_dict)
            
            # Create TaskResult
            task_result = task_pb2.TaskResult()
            
            if isinstance(result, dict):
                # Handle dictionary result
                if "error" in result:
                    task_result.error_message = str(result["error"])
                    task_result.mime_type = "text/plain"
                else:
                    # Serialize result as JSON
                    result_json = json.dumps(result)
                    # Create a proper Any message with JSON data
                    from google.protobuf import struct_pb2
                    json_struct = struct_pb2.Value()
                    json_struct.string_value = result_json
                    task_result.inline_data.Pack(json_struct)
                    task_result.mime_type = "application/json"
                    task_result.size_bytes = len(result_json.encode('utf-8'))
            else:
                # Handle simple result
                result_str = str(result)
                # Create a proper Any message with string data
                from google.protobuf import struct_pb2
                string_value = struct_pb2.Value()
                string_value.string_value = result_str
                task_result.inline_data.Pack(string_value)
                task_result.mime_type = "text/plain"
                task_result.size_bytes = len(result_str.encode('utf-8'))
            
            # Create TaskExecution
            task_execution = task_pb2.TaskExecution()
            task_execution.header.id = execution_id
            task_execution.header.tenant_id = "default"  # Could be extracted from context
            task_execution.header.status = common_pb2.EXECUTION_STATUS_SUCCEEDED
            task_execution.header.created_at = datetime.utcnow().isoformat()
            task_execution.task_type = task_type
            task_execution.parameters = parameters
            task_execution.result.CopyFrom(task_result)
            
            self._tasks_executed += 1
            self.logger.debug(f"Task {task_type} executed successfully: {execution_id}")
            
            return task_execution
            
        except Exception as e:
            self._tasks_failed += 1
            self.logger.error(f"Task execution failed for {task_type}: {e}")
            
            # Create failed TaskExecution
            task_execution = task_pb2.TaskExecution()
            task_execution.header.id = execution_id
            task_execution.header.tenant_id = "default"
            task_execution.header.status = common_pb2.EXECUTION_STATUS_FAILED
            task_execution.header.created_at = datetime.utcnow().isoformat()
            task_execution.task_type = task_type
            task_execution.parameters = parameters
            
            # Create error result
            error_result = task_pb2.TaskResult()
            error_result.error_message = str(e)
            error_result.mime_type = "text/plain"
            task_execution.result.CopyFrom(error_result)
            
            return task_execution
    
    async def _process_task_result(self, message_bytes: bytes, tenant_id: str) -> None:
        """
        Process a task result message from the queue.
        
        Args:
            message_bytes: Serialized result message bytes
            tenant_id: Tenant identifier
        """
        try:
            # Deserialize the message
            result_data = json.loads(message_bytes.decode('utf-8'))
            
            execution_id = result_data.get('execution_id', '')
            status = result_data.get('status', '')
            
            self.logger.debug(f"Processing task result: {execution_id}, status: {status}")
            
            if status == 'approved':
                # Extract task information and execute
                task_type = result_data.get('task_type', 'unknown')
                parameters = result_data.get('parameters', '{}')
                
                # Execute the task
                task_execution = await self._execute_task(task_type, parameters, execution_id)
                
                # Serialize and publish to execution queue
                execution_topic = f"task-executions_{tenant_id}"
                execution_bytes = task_execution.SerializeToString()
                await self.broker.publish(execution_topic, execution_bytes)
                
                self.logger.debug(f"Published task execution result: {execution_id}")
            
            elif status == 'rejected':
                # Handle rejected task
                reason = result_data.get('reason', 'Unknown reason')
                self.logger.warning(f"Task execution rejected: {execution_id}, reason: {reason}")
                
                # Create failed TaskExecution for rejected tasks
                task_execution = task_pb2.TaskExecution()
                task_execution.header.id = execution_id
                task_execution.header.tenant_id = tenant_id
                task_execution.header.status = common_pb2.EXECUTION_STATUS_FAILED
                task_execution.header.created_at = datetime.utcnow().isoformat()
                task_execution.task_type = result_data.get('task_type', 'unknown')
                task_execution.parameters = result_data.get('parameters', '{}')
                
                # Create error result
                error_result = task_pb2.TaskResult()
                error_result.error_message = f"Task rejected: {reason}"
                error_result.mime_type = "text/plain"
                task_execution.result.CopyFrom(error_result)
                
                # Serialize and publish to execution queue
                execution_topic = f"task-executions_{tenant_id}"
                execution_bytes = task_execution.SerializeToString()
                await self.broker.publish(execution_topic, execution_bytes)
            
            self._messages_processed += 1
            
        except Exception as e:
            self._errors += 1
            self.logger.error(f"Error processing task result: {e}")
            raise
    
    async def _consumer_loop(self, tenant_id: str) -> None:
        """
        Consumer loop for task result messages.
        
        Args:
            tenant_id: Tenant identifier
        """
        topic = f"task-results_{tenant_id}"
        self.logger.info(f"Starting task result consumer for topic: {topic}")
        
        try:
            async for message_bytes in self.broker.subscribe(topic):
                await self._process_task_result(message_bytes, tenant_id)
        except asyncio.CancelledError:
            self.logger.info(f"Task result consumer cancelled for tenant: {tenant_id}")
        except Exception as e:
            self.logger.error(f"Task result consumer error for tenant {tenant_id}: {e}")
            raise
    
    async def start(self, tenant_id: str = "default") -> None:
        """
        Start the task executor service.
        
        Args:
            tenant_id: Tenant identifier
        """
        if self._running:
            self.logger.warning("Task executor service is already running")
            return
        
        self._running = True
        self.logger.info("Starting task executor service")
        
        # Start consumer task
        self._consumer_task = asyncio.create_task(self._consumer_loop(tenant_id))
        
        self.logger.info("Task executor service started successfully")
    
    async def stop(self) -> None:
        """Stop the task executor service."""
        if not self._running:
            return
        
        self.logger.info("Stopping task executor service")
        self._running = False
        
        # Cancel consumer task
        if self._consumer_task:
            self._consumer_task.cancel()
            try:
                await self._consumer_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("Task executor service stopped")
    
    def get_metrics(self) -> dict:
        """
        Get service metrics.
        
        Returns:
            Dictionary of metric names and values
        """
        return {
            "tasks_executed": self._tasks_executed,
            "tasks_failed": self._tasks_failed,
            "messages_processed": self._messages_processed,
            "errors": self._errors,
            "registered_tasks": len(self.task_registry),
            "running": self._running
        } 