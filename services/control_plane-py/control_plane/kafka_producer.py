"""
Kafka producer for control plane microservice.

This module implements Kafka producer for routing approved executions
to executor topics using aiokafka==0.11.0 with proper error handling
and retry logic.
"""

import json
from typing import Any, Dict, Optional

from aiokafka import AIOKafkaProducer
from structlog import get_logger

from agentic_common.kafka_utils import (
    create_kafka_producer,
    get_plan_inputs_topic,
    get_task_inputs_topic,
)
from agentic_common.logging_config import log_kafka_message
from agentic_common.pb import TaskExecution, PlanExecution, PlanInput, TaskInput
from agentic_common import ProtobufUtils

logger = get_logger(__name__)


class ControlPlaneProducer:
    """
    Kafka producer for the control plane service.
    
    Publishes approved executions to executor topics after
    guardrail evaluation and routing decisions.
    """
    
    def __init__(self):
        """Initialize the producer."""
        self.producer: Optional[AIOKafkaProducer] = None
        
    async def start(self) -> None:
        """Start the Kafka producer."""
        try:
            self.producer = await create_kafka_producer(
                client_id="control-plane-producer",
            )
            await self.producer.start()
            
            logger.info("Control plane producer started")
            
        except Exception as e:
            logger.error("Failed to start control plane producer", error=str(e))
            raise
    
    async def stop(self) -> None:
        """Stop the Kafka producer."""
        if self.producer:
            await self.producer.stop()
            await self.producer.close()
            logger.info("Control plane producer stopped")
    
    async def publish_plan_input(
        self,
        tenant_id: str,
        plan_input: PlanInput,
        **kwargs
    ) -> None:
        """
        Publish PlanInput to plan-inputs topic.
        
        Args:
            tenant_id: Tenant identifier
            plan_input: PlanInput protobuf message
            **kwargs: Additional metadata
        """
        if not self.producer:
            raise RuntimeError("Producer not initialized")
        
        try:
            topic = get_plan_inputs_topic(tenant_id)
            
            # Serialize protobuf message using consistent utilities
            message_bytes = ProtobufUtils.serialize_plan_input(plan_input)
            
            # Send message with plan_name as key for ordering
            plan_name = plan_input.plan_name
            await self.producer.send_and_wait(
                topic=topic,
                key=plan_name.encode('utf-8'),
                value=message_bytes,
            )
            
            # Log message sent
            log_kafka_message(
                logger=logger,
                topic=topic,
                partition=0,  # Will be set by Kafka
                offset=0,     # Will be set by Kafka
                message_size=len(message_bytes),
                tenant_id=tenant_id,
                execution_id=plan_input.input_id,
            )
            
            logger.info("PlanInput published to plan-inputs", 
                       input_id=plan_input.input_id,
                       plan_name=plan_name,
                       tenant_id=tenant_id)
            
        except Exception as e:
            logger.error("Failed to publish PlanInput", 
                        plan_input=plan_input,
                        tenant_id=tenant_id,
                        error=str(e))
            raise
    
    async def publish_task_input(
        self,
        tenant_id: str,
        task_input: TaskInput,
        **kwargs
    ) -> None:
        """
        Publish TaskInput to task-inputs topic.
        
        Args:
            tenant_id: Tenant identifier
            task_input: TaskInput protobuf message
            **kwargs: Additional metadata
        """
        if not self.producer:
            raise RuntimeError("Producer not initialized")
        
        try:
            topic = get_task_inputs_topic(tenant_id)
            
            # Serialize protobuf message using consistent utilities
            message_bytes = ProtobufUtils.serialize_task_input(task_input)
            
            # Send message with task_name as key for ordering
            task_name = task_input.task_name
            await self.producer.send_and_wait(
                topic=topic,
                key=task_name.encode('utf-8'),
                value=message_bytes,
            )
            
            # Log message sent
            log_kafka_message(
                logger=logger,
                topic=topic,
                partition=0,  # Will be set by Kafka
                offset=0,     # Will be set by Kafka
                message_size=len(message_bytes),
                tenant_id=tenant_id,
                execution_id=task_input.input_id,
            )
            
            logger.info("TaskInput published to task-inputs", 
                       input_id=task_input.input_id,
                       task_name=task_name,
                       tenant_id=tenant_id)
            
        except Exception as e:
            logger.error("Failed to publish TaskInput", 
                        task_input=task_input,
                        tenant_id=tenant_id,
                        error=str(e))
            raise
    
    async def publish_plan_execution(
        self,
        tenant_id: str,
        plan_execution: PlanExecution,
        **kwargs
    ) -> None:
        """
        Publish PlanExecution by creating TaskInput messages for next tasks.
        
        Examines PlanExecution.result.next_task_names, creates TaskInput messages,
        and publishes them to task-inputs topics.
        
        Args:
            tenant_id: Tenant identifier
            plan_execution: PlanExecution protobuf message
            **kwargs: Additional metadata
        """
        if not self.producer:
            raise RuntimeError("Producer not initialized")
        
        try:
            # Extract next_task_names from PlanExecution.result
            next_task_names = []
            if plan_execution.result and plan_execution.result.next_task_names:
                next_task_names = list(plan_execution.result.next_task_names)
            
            if not next_task_names:
                logger.info("No next tasks found in plan execution", 
                           execution_id=plan_execution.header.exec_id,
                           tenant_id=tenant_id)
                return
            
            logger.info("Found next tasks in plan execution", 
                       execution_id=plan_execution.header.exec_id,
                       tenant_id=tenant_id,
                       next_task_names=next_task_names)
            
            # Create TaskInput messages for each task
            for task_name in next_task_names:
                task_input = TaskInput(
                    input_id=f"task-input-{task_name}-{plan_execution.header.exec_id}",
                    task_name=task_name,
                    plan_execution=plan_execution
                )
                
                # Publish TaskInput to task-inputs topic
                await self.publish_task_input(tenant_id, task_input, **kwargs)
            
            logger.info("Successfully published TaskInput messages for plan execution", 
                       execution_id=plan_execution.header.exec_id,
                       tenant_id=tenant_id,
                       task_count=len(next_task_names))
            
        except Exception as e:
            logger.error("Failed to publish TaskInputs", 
                        plan_execution=plan_execution,
                        tenant_id=tenant_id,
                        error=str(e))
            raise
    
    async def publish_execution_result(
        self,
        tenant_id: str,
        execution_data: Dict[str, Any],
        **kwargs
    ) -> None:
        """
        Publish execution result based on type.
        
        Args:
            tenant_id: Tenant identifier
            execution_data: Execution data
            **kwargs: Additional metadata
        """
        execution_type = execution_data.get("type")
        
        if execution_type == "task":
            # Implement Next Plan Prep logic for task executions
            await self._publish_task_execution_with_next_plan_prep(tenant_id, execution_data, **kwargs)
        elif execution_type == "plan":
            await self.publish_plan_execution(tenant_id, execution_data, **kwargs)
        else:
            logger.warning("Unknown execution type for publishing", 
                          execution_type=execution_type,
                          execution_id=execution_data.get("execution_id"))
    
    async def _publish_task_execution_with_next_plan_prep(
        self,
        tenant_id: str,
        execution_data: Dict[str, Any],
        **kwargs
    ) -> None:
        """
        Implement Next Plan Prep logic for task executions.
        
        When execution_type is 'task', examine the TaskExecution, look up the next plan 
        in the graph (stub implementation), create a PlanInput message containing the 
        original TaskExecution plus the determined plan name, and publish it using 
        publish_plan_input.
        
        Args:
            tenant_id: Tenant identifier
            execution_data: Task execution data
            **kwargs: Additional metadata
        """
        try:
            # Extract TaskExecution from the execution data
            # Note: This assumes execution_data contains a TaskExecution protobuf or dict representation
            task_execution = self._extract_task_execution(execution_data)
            
            if not task_execution:
                logger.error("Failed to extract TaskExecution from execution data", 
                           execution_data=execution_data,
                           tenant_id=tenant_id)
                return
            
            # Look up the next plan in the graph (stub implementation)
            next_plan_name = self._lookup_next_plan_in_graph(task_execution, tenant_id)
            
            # Create PlanInput message containing the original TaskExecution plus the determined plan name
            plan_input = PlanInput(
                input_id=task_execution.header.exec_id,
                plan_name=next_plan_name,
                task_executions=[task_execution]
            )
            
            # Publish using publish_plan_input
            await self.publish_plan_input(tenant_id, plan_input, **kwargs)
            
            logger.info("TaskExecution processed with Next Plan Prep logic", 
                       execution_id=task_execution.header.exec_id,
                       tenant_id=tenant_id,
                       next_plan_name=next_plan_name)
            
        except Exception as e:
            logger.error("Failed to process task execution with Next Plan Prep", 
                        execution_data=execution_data,
                        tenant_id=tenant_id,
                        error=str(e))
            raise
    
    def _extract_task_execution(self, execution_data: Dict[str, Any]) -> Optional[TaskExecution]:
        """
        Extract TaskExecution from execution data.
        
        Args:
            execution_data: Execution data dictionary
            
        Returns:
            TaskExecution protobuf object or None if extraction fails
        """
        try:
            # Handle case where execution_data is already a TaskExecution protobuf
            if isinstance(execution_data, TaskExecution):
                return execution_data
            
            # Handle case where execution_data is a dict representation
            if isinstance(execution_data, dict):
                # This is a stub implementation - in a real scenario, you would
                # deserialize the TaskExecution from the dict representation
                # For now, we'll create a minimal TaskExecution for demonstration
                
                # Extract basic fields from the dict
                execution_id = execution_data.get("execution_id", "unknown")
                task_name = execution_data.get("name", "unknown")
                
                # Create a minimal TaskExecution (this is a stub - real implementation
                # would properly deserialize the protobuf)
                task_execution = TaskExecution()
                task_execution.header.exec_id = execution_id
                task_execution.header.name = task_name
                task_execution.header.tenant_id = execution_data.get("tenant_id", "default")
                task_execution.header.created_at = self._get_current_timestamp()
                
                # Add result if available
                if "result" in execution_data:
                    # This would need proper protobuf deserialization in real implementation
                    pass
                
                return task_execution
            
            logger.warning("Unsupported execution_data type for TaskExecution extraction", 
                          type=type(execution_data))
            return None
            
        except Exception as e:
            logger.error("Failed to extract TaskExecution", 
                        execution_data=execution_data,
                        error=str(e))
            return None
    
    def _lookup_next_plan_in_graph(self, task_execution: TaskExecution, tenant_id: str) -> str:
        """
        Look up the next Plan in the graph based on TaskExecution.
        
        Args:
            task_execution: TaskExecution to examine
            tenant_id: Tenant identifier
            
        Returns:
            Name of the next plan in the graph path
        """
        # TODO: Implement actual graph lookup logic
        # This should examine the TaskExecution and determine the next plan in the graph
        # For now, return a stub implementation
        
        logger.debug("Looking up next plan in graph for task execution", 
                   execution_id=task_execution.header.exec_id,
                   tenant_id=tenant_id,
                   task_name=task_execution.header.name)
        
        # Stub implementation - replace with actual graph lookup
        # This could involve:
        # 1. Loading the agent graph for the tenant
        # 2. Examining the task_execution.header.name to identify the current task
        # 3. Looking up outgoing edges from this task to find the next plan
        # 4. Returning the plan name
        
        # For now, return a predictable stub name based on the task name
        task_name = task_execution.header.name
        if task_name:
            return f"next-plan-after-{task_name}"
        else:
            return "next-plan-stub"
    
    def _get_current_timestamp(self) -> str:
        """
        Get current timestamp in ISO format.
        
        Returns:
            ISO timestamp string
        """
        from datetime import datetime
        return datetime.utcnow().isoformat() + "Z"
    
    async def health_check(self) -> bool:
        """
        Perform producer health check.
        
        Returns:
            True if producer is healthy, False otherwise
        """
        try:
            if not self.producer:
                return False
            
            # Check if producer is connected
            return (self.producer._sender._sender_task and 
                   not self.producer._sender._sender_task.done())
            
        except Exception as e:
            logger.error("Producer health check failed", error=str(e))
            return False 