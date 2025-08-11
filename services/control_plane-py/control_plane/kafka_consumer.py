"""
Kafka consumer for control plane microservice.

This module implements Kafka consumer for control plane topics using
aiokafka==0.11.0. Subscribe to persisted-task-executions-* and persisted-plan-executions-* topics
using pattern matching.
"""

import asyncio
from typing import Optional

from agentic_common.pb import TaskExecution, PlanExecution
from agentic_common import ProtobufUtils

from aiokafka import AIOKafkaConsumer
from structlog import get_logger

from agentic_common.kafka_utils import create_kafka_consumer
from agentic_common.logging_config import log_kafka_message

logger = get_logger(__name__)


class ControlPlaneConsumer:
    """
    Kafka consumer for the control plane service.
    
    Consumes execution references from control plane topics and
    processes them through guardrail evaluation and routing.
    """
    
    def __init__(self, group_id: str = "control-plane-group"):
        """
        Initialize the consumer.
        
        Args:
            group_id: Kafka consumer group ID
        """
        self.group_id = group_id
        self.consumer: Optional[AIOKafkaConsumer] = None
        self.running = False
        self.message_processor = None
        
    def set_message_processor(self, processor):
        """
        Set the message processor callback.
        
        Args:
            processor: Function to process messages
        """
        self.message_processor = processor
        
    async def start(self) -> None:
        """Start the Kafka consumer."""
        try:
            # Create consumer for control plane topics
            topics = [
                "persisted-task-executions-*",  # Pattern for tenant-specific topics
                "persisted-plan-executions-*",  # Pattern for tenant-specific topics
            ]
            
            self.consumer = await create_kafka_consumer(
                topics=topics,
                group_id=self.group_id,
                client_id="control-plane-consumer",
            )
            
            await self.consumer.start()
            self.running = True
            
            logger.info("Control plane consumer started", 
                       group_id=self.group_id,
                       topics=topics)
            
        except Exception as e:
            logger.error("Failed to start control plane consumer", error=str(e))
            raise
    
    async def stop(self) -> None:
        """Stop the Kafka consumer."""
        if self.consumer:
            self.running = False
            await self.consumer.stop()
            await self.consumer.close()
            logger.info("Control plane consumer stopped")
    
    async def consume_messages(self) -> None:
        """Consume messages from Kafka topics."""
        if not self.consumer:
            raise RuntimeError("Consumer not initialized")
        
        if not self.message_processor:
            raise RuntimeError("Message processor not set")
        
        try:
            async for message in self.consumer:
                if not self.running:
                    break
                
                try:
                    await self._process_message(message)
                    await self.consumer.commit()
                    
                except Exception as e:
                    logger.error("Failed to process message", 
                               topic=message.topic,
                               partition=message.partition,
                               offset=message.offset,
                               error=str(e))
                    # Don't commit on error to allow retry
                    
        except Exception as e:
            logger.error("Consumer error", error=str(e))
            raise
    
    async def _process_message(self, message) -> None:
        """
        Process a single Kafka message.
        
        Args:
            message: Kafka message
        """
        # Log message processing
        log_kafka_message(
            logger=logger,
            topic=message.topic,
            partition=message.partition,
            offset=message.offset,
            message_size=len(message.value),
        )
        
        try:
            # Extract tenant_id from topic
            tenant_id = message.topic.split("_", 1)[1]
            
            # Determine execution type from topic and deserialize protobuf
            if message.topic.startswith("persisted-task-executions-"):
                task_execution = ProtobufUtils.deserialize_task_execution(message.value)
                message_data = {
                    "type": "task",
                    "tenant_id": tenant_id,
                    "task_execution": task_execution
                }
            elif message.topic.startswith("persisted-plan-executions-"):
                plan_execution = ProtobufUtils.deserialize_plan_execution(message.value)
                message_data = {
                    "type": "plan", 
                    "tenant_id": tenant_id,
                    "plan_execution": plan_execution
                }
            else:
                logger.warning("Unknown topic", topic=message.topic)
                return
            
            # Process message through the processor
            if self.message_processor:
                await self.message_processor(message_data)
            
        except Exception as e:
            logger.error("Failed to deserialize protobuf message", 
                        topic=message.topic,
                        error=str(e))
            raise
    
    async def health_check(self) -> bool:
        """
        Perform consumer health check.
        
        Returns:
            True if consumer is healthy, False otherwise
        """
        try:
            return self.running and self.consumer is not None
        except Exception as e:
            logger.error("Consumer health check failed", error=str(e))
            return False 