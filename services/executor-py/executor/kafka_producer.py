"""
Kafka producer for executor microservice.

This module implements Kafka producer for emitting execution results
using aiokafka==0.11.0 with proper error handling and retry logic.
"""

import json
from typing import Any, Dict, Optional

from aiokafka import AIOKafkaProducer
from structlog import get_logger

from agentic_common.kafka_utils import create_kafka_producer
from agentic_common.logging_config import log_kafka_message

logger = get_logger(__name__)


class ExecutorProducer:
    """
    Kafka producer for the executor service.
    
    Publishes TaskExecution and PlanExecution messages to data plane
    topics after task and plan execution.
    """
    
    def __init__(self):
        """Initialize the producer."""
        self.producer: Optional[AIOKafkaProducer] = None
        
    async def start(self) -> None:
        """Start the Kafka producer."""
        try:
            self.producer = await create_kafka_producer(
                client_id="executor-producer",
            )
            await self.producer.start()
            
            logger.info("Executor producer started")
            
        except Exception as e:
            logger.error("Failed to start executor producer", error=str(e))
            raise
    
    async def stop(self) -> None:
        """Stop the Kafka producer."""
        if self.producer:
            await self.producer.stop()
            await self.producer.close()
            logger.info("Executor producer stopped")
    
    async def publish_task_execution(
        self,
        tenant_id: str,
        task_execution: Dict[str, Any],
        **kwargs
    ) -> None:
        """
        Publish TaskExecution to data plane.
        
        Args:
            tenant_id: Tenant identifier
            task_execution: TaskExecution data
            **kwargs: Additional metadata
        """
        if not self.producer:
            raise RuntimeError("Producer not initialized")
        
        try:
            topic = f"task-executions_{tenant_id}"
            
            # Add metadata to message
            message = {
                **task_execution,
                "tenant_id": tenant_id,
                "timestamp": self._get_current_timestamp(),
                **kwargs
            }
            
            # Serialize message
            message_bytes = json.dumps(message).encode('utf-8')
            
            # Send message with execution_id as key for ordering
            execution_id = task_execution.get("execution_id", "unknown")
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
            
            logger.info("TaskExecution published", 
                       execution_id=execution_id,
                       tenant_id=tenant_id,
                       task_type=task_execution.get("task_type"))
            
        except Exception as e:
            logger.error("Failed to publish TaskExecution", 
                        task_execution=task_execution,
                        tenant_id=tenant_id,
                        error=str(e))
            raise
    
    async def publish_plan_execution(
        self,
        tenant_id: str,
        plan_execution: Dict[str, Any],
        **kwargs
    ) -> None:
        """
        Publish PlanExecution to data plane.
        
        Args:
            tenant_id: Tenant identifier
            plan_execution: PlanExecution data
            **kwargs: Additional metadata
        """
        if not self.producer:
            raise RuntimeError("Producer not initialized")
        
        try:
            topic = f"plan-executions_{tenant_id}"
            
            # Add metadata to message
            message = {
                **plan_execution,
                "tenant_id": tenant_id,
                "timestamp": self._get_current_timestamp(),
                **kwargs
            }
            
            # Serialize message
            message_bytes = json.dumps(message).encode('utf-8')
            
            # Send message with execution_id as key for ordering
            execution_id = plan_execution.get("execution_id", "unknown")
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
            
            logger.info("PlanExecution published", 
                       execution_id=execution_id,
                       tenant_id=tenant_id,
                       plan_type=plan_execution.get("plan_type"))
            
        except Exception as e:
            logger.error("Failed to publish PlanExecution", 
                        plan_execution=plan_execution,
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