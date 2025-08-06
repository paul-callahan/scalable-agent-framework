"""
Task executor service implementation.

This module implements the TaskExecutorService that consumes from controlled task execution queues,
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
from agentic_common.kafka_utils import get_controlled_task_executions_topic


class TaskExecutorService:
    """
    Task executor service implementation.
    
    Handles task execution by consuming from controlled execution queues and publishing
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
    
    async def _execute_task(self, task_type: str, execution_id: str) -> task_pb2.TaskExecution:
        """
        Execute a task and return the result.
        
        Args:
            task_type: Task type identifier
            execution_id: Execution identifier
            
        Returns:
            TaskExecution protobuf message with results
        """
        try:
            # Get task handler
            task_handler = self.task_registry.get(task_type)
            
            if not task_handler:
                self.logger.warning(f"No handler registered for task type: {task_type}. Returning failed execution.")
                # Create failed TaskExecution
                task_execution = task_pb2.TaskExecution()
                task_execution.header.exec_id = execution_id
                task_execution.header.tenant_id = "default"
                task_execution.header.status = common_pb2.EXECUTION_STATUS_FAILED
                task_execution.header.created_at = datetime.utcnow().isoformat()
                
                # Create error result
                error_result = task_pb2.TaskResult()
                error_result.error_message = f"No handler registered for task type: {task_type}"
                task_execution.result.CopyFrom(error_result)
                
                return task_execution
            
            # Execute task with empty parameters
            self.logger.debug(f"Executing task {task_type} with execution ID {execution_id}")
            result = task_handler({})
            
            # Create TaskResult
            task_result = task_pb2.TaskResult()
            
            if isinstance(result, dict):
                # Handle dictionary result
                if "error" in result:
                    task_result.error_message = str(result["error"])
                else:
                    # Serialize result as protobuf Any message
                    from google.protobuf import struct_pb2, any_pb2
                    # Convert dict to protobuf Struct
                    struct_value = struct_pb2.Struct()
                    for key, value in result.items():
                        struct_value.fields[key].string_value = str(value)
                    
                    # Pack into Any message
                    any_message = any_pb2.Any()
                    any_message.Pack(struct_value)
                    task_result.inline_data.CopyFrom(any_message)
            else:
                # Handle simple result as protobuf Any message
                from google.protobuf import struct_pb2, any_pb2
                string_value = struct_pb2.Value()
                string_value.string_value = str(result)
                
                any_message = any_pb2.Any()
                any_message.Pack(string_value)
                task_result.inline_data.CopyFrom(any_message)
            
            # Create TaskExecution
            task_execution = task_pb2.TaskExecution()
            task_execution.header.exec_id = execution_id
            task_execution.header.tenant_id = "default"  # Could be extracted from context
            task_execution.header.status = common_pb2.EXECUTION_STATUS_SUCCEEDED
            task_execution.header.created_at = datetime.utcnow().isoformat()
            task_execution.result.CopyFrom(task_result)
            
            self._tasks_executed += 1
            self.logger.debug(f"Task {task_type} executed successfully: {execution_id}")
            
            return task_execution
            
        except Exception as e:
            self._tasks_failed += 1
            self.logger.error(f"Task execution failed for {task_type}: {e}")
            
            # Create failed TaskExecution
            task_execution = task_pb2.TaskExecution()
            task_execution.header.exec_id = execution_id
            task_execution.header.tenant_id = "default"
            task_execution.header.status = common_pb2.EXECUTION_STATUS_FAILED
            task_execution.header.created_at = datetime.utcnow().isoformat()
            
            # Create error result
            error_result = task_pb2.TaskResult()
            error_result.error_message = str(e)
            task_execution.result.CopyFrom(error_result)
            
            return task_execution
    
    async def _process_task_execution(self, message_bytes: bytes, tenant_id: str) -> None:
        """
        Process a task execution message from the queue.
        
        Args:
            message_bytes: Serialized TaskExecution protobuf message bytes
            tenant_id: Tenant identifier
        """
        try:
            # Deserialize the TaskExecution protobuf message
            task_execution = task_pb2.TaskExecution()
            task_execution.ParseFromString(message_bytes)
            
            execution_id = task_execution.header.exec_id
            status = task_execution.header.status
            
            self.logger.debug(f"Processing task execution: {execution_id}, status: {status}")
            
            if status == common_pb2.EXECUTION_STATUS_SUCCEEDED:
                # Extract task information and execute
                # Note: task_type is no longer available in protobuf
                # We'll use a default task type
                task_type = "default_task"  # Default task type
                
                # Execute the task
                task_execution = await self._execute_task(task_type, execution_id)
                
                # Serialize and publish to execution queue
                execution_topic = f"task-executions_{tenant_id}"
                execution_bytes = task_execution.SerializeToString()
                await self.broker.publish(execution_topic, execution_bytes)
                
                self.logger.debug(f"Published task execution result: {execution_id}")
            
            elif status == common_pb2.EXECUTION_STATUS_FAILED:
                # Handle failed task
                error_message = task_execution.result.error_message
                self.logger.warning(f"Task execution failed: {execution_id}, error: {error_message}")
                
                # Create failed TaskExecution for failed tasks
                failed_execution = task_pb2.TaskExecution()
                failed_execution.header.exec_id = execution_id
                failed_execution.header.tenant_id = tenant_id
                failed_execution.header.status = common_pb2.EXECUTION_STATUS_FAILED
                failed_execution.header.created_at = datetime.utcnow().isoformat()
                
                # Create error result
                error_result = task_pb2.TaskResult()
                error_result.error_message = error_message
                failed_execution.result.CopyFrom(error_result)
                
                # Serialize and publish to execution queue
                execution_topic = f"task-executions_{tenant_id}"
                execution_bytes = failed_execution.SerializeToString()
                await self.broker.publish(execution_topic, execution_bytes)
            
            self._messages_processed += 1
            
        except Exception as e:
            self._errors += 1
            self.logger.error(f"Error processing task execution: {e}")
            raise
    
    async def _consumer_loop(self, tenant_id: str) -> None:
        """
        Consumer loop for controlled task execution messages.
        
        Args:
            tenant_id: Tenant identifier
        """
        topic = get_controlled_task_executions_topic(tenant_id)
        self.logger.info(f"Starting controlled task execution consumer for topic: {topic}")
        
        try:
            async for message_bytes in self.broker.subscribe(topic):
                await self._process_task_execution(message_bytes, tenant_id)
        except asyncio.CancelledError:
            self.logger.info(f"Controlled task execution consumer cancelled for tenant: {tenant_id}")
        except Exception as e:
            self.logger.error(f"Controlled task execution consumer error for tenant {tenant_id}: {e}")
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