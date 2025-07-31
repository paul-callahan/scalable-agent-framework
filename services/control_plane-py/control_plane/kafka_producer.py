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

from agentic_common.kafka_utils import create_kafka_producer
from agentic_common.logging_config import log_kafka_message

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
    
    async def publish_task_result(
        self,
        tenant_id: str,
        task_result: Dict[str, Any],
        **kwargs
    ) -> None:
        """
        Publish TaskResult to plan-results topic.
        
        Args:
            tenant_id: Tenant identifier
            task_result: TaskResult data
            **kwargs: Additional metadata
        """
        if not self.producer:
            raise RuntimeError("Producer not initialized")
        
        try:
            topic = f"plan-results_{tenant_id}"
            
            # Add metadata to message
            message = {
                **task_result,
                "tenant_id": tenant_id,
                "timestamp": self._get_current_timestamp(),
                **kwargs
            }
            
            # Serialize message
            message_bytes = json.dumps(message).encode('utf-8')
            
            # Send message with execution_id as key for ordering
            execution_id = task_result.get("execution_id", "unknown")
            await self.producer.send_and_wait(
                topic=topic,
                key=execution_id.encode('utf-8'),
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
                execution_id=execution_id,
            )
            
            logger.info("TaskResult published to plan-results", 
                       execution_id=execution_id,
                       tenant_id=tenant_id)
            
        except Exception as e:
            logger.error("Failed to publish TaskResult", 
                        task_result=task_result,
                        tenant_id=tenant_id,
                        error=str(e))
            raise
    
    async def publish_plan_result(
        self,
        tenant_id: str,
        plan_result: Dict[str, Any],
        **kwargs
    ) -> None:
        """
        Publish PlanResult to task-results topic.
        
        Args:
            tenant_id: Tenant identifier
            plan_result: PlanResult data
            **kwargs: Additional metadata
        """
        if not self.producer:
            raise RuntimeError("Producer not initialized")
        
        try:
            topic = f"task-results_{tenant_id}"
            
            # Add metadata to message
            message = {
                **plan_result,
                "tenant_id": tenant_id,
                "timestamp": self._get_current_timestamp(),
                **kwargs
            }
            
            # Serialize message
            message_bytes = json.dumps(message).encode('utf-8')
            
            # Send message with execution_id as key for ordering
            execution_id = plan_result.get("execution_id", "unknown")
            await self.producer.send_and_wait(
                topic=topic,
                key=execution_id.encode('utf-8'),
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
                execution_id=execution_id,
            )
            
            logger.info("PlanResult published to task-results", 
                       execution_id=execution_id,
                       tenant_id=tenant_id)
            
        except Exception as e:
            logger.error("Failed to publish PlanResult", 
                        plan_result=plan_result,
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
            await self.publish_task_result(tenant_id, execution_data, **kwargs)
        elif execution_type == "plan":
            await self.publish_plan_result(tenant_id, execution_data, **kwargs)
        else:
            logger.warning("Unknown execution type for publishing", 
                          execution_type=execution_type,
                          execution_id=execution_data.get("execution_id"))
    
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