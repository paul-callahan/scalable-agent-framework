"""
Kafka producer for data plane microservice.

This module implements Kafka producer for republishing execution references
to control plane topics using aiokafka==0.11.0 with proper error handling
and retry logic.
"""

import json
from typing import Optional

from aiokafka import AIOKafkaProducer
from structlog import get_logger

from agentic_common.kafka_utils import create_kafka_producer
from agentic_common.logging_config import log_kafka_message

logger = get_logger(__name__)


class DataPlaneProducer:
    """
    Kafka producer for the data plane service.
    
    Republishes lightweight execution references to control plane topics
    after successful database persistence.
    """
    
    def __init__(self):
        """Initialize the producer."""
        self.producer: Optional[AIOKafkaProducer] = None
        
    async def start(self) -> None:
        """Start the Kafka producer."""
        try:
            self.producer = await create_kafka_producer(
                client_id="data-plane-producer",
            )
            await self.producer.start()
            
            logger.info("Data plane producer started")
            
        except Exception as e:
            logger.error("Failed to start data plane producer", error=str(e))
            raise
    
    async def stop(self) -> None:
        """Stop the Kafka producer."""
        if self.producer:
            await self.producer.stop()
            await self.producer.close()
            logger.info("Data plane producer stopped")
    
    async def publish_task_control_reference(
        self,
        tenant_id: str,
        execution_id: str,
        task_type: str,
        status: str,
        **kwargs
    ) -> None:
        """
        Publish task control reference to control plane.
        
        Args:
            tenant_id: Tenant identifier
            execution_id: Task execution ID
            task_type: Type of task
            status: Execution status
            **kwargs: Additional metadata
        """
        if not self.producer:
            raise RuntimeError("Producer not initialized")
        
        try:
            topic = f"persisted-task-executions_{tenant_id}"
            
            # Create lightweight reference message
            message = {
                "execution_id": execution_id,
                "task_type": task_type,
                "status": status,
                "tenant_id": tenant_id,
                "timestamp": self._get_current_timestamp(),
                **kwargs
            }
            
            # Serialize message
            message_bytes = json.dumps(message).encode('utf-8')
            
            # Send message with execution_id as key for ordering
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
            
            logger.info("Task control reference published", 
                       execution_id=execution_id,
                       tenant_id=tenant_id,
                       task_type=task_type)
            
        except Exception as e:
            logger.error("Failed to publish task control reference", 
                        execution_id=execution_id,
                        tenant_id=tenant_id,
                        error=str(e))
            raise
    
    async def publish_persisted_plan_executions_reference(
        self,
        tenant_id: str,
        execution_id: str,
        plan_type: str,
        status: str,
        **kwargs
    ) -> None:
        """
        Publish persisted plan executions reference to control plane.
        
        Args:
            tenant_id: Tenant identifier
            execution_id: Plan execution ID
            plan_type: Type of plan
            status: Execution status
            **kwargs: Additional metadata
        """
        if not self.producer:
            raise RuntimeError("Producer not initialized")
        
        try:
            topic = f"persisted-plan-executions_{tenant_id}"
            
            # Create lightweight reference message
            message = {
                "execution_id": execution_id,
                "plan_type": plan_type,
                "status": status,
                "tenant_id": tenant_id,
                "timestamp": self._get_current_timestamp(),
                **kwargs
            }
            
            # Serialize message
            message_bytes = json.dumps(message).encode('utf-8')
            
            # Send message with execution_id as key for ordering
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
            
            logger.info("Persisted plan executions reference published", 
                       execution_id=execution_id,
                       tenant_id=tenant_id,
                       plan_type=plan_type)
            
        except Exception as e:
            logger.error("Failed to publish persisted plan executions reference", 
                        execution_id=execution_id,
                        tenant_id=tenant_id,
                        error=str(e))
            raise
    
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