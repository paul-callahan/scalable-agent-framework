"""
Kafka consumer for control plane microservice.

This module implements Kafka consumer for control plane topics using
aiokafka==0.11.0. Subscribe to task-control_* and plan-control_* topics
using pattern matching.
"""

import asyncio
import json
from typing import Optional

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
                "task-control_*",  # Pattern for tenant-specific topics
                "plan-control_*",  # Pattern for tenant-specific topics
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
            # Deserialize JSON message
            message_data = json.loads(message.value.decode('utf-8'))
            
            # Extract tenant_id from topic
            tenant_id = message.topic.split("_", 1)[1]
            
            # Add tenant_id to message data
            message_data["tenant_id"] = tenant_id
            
            # Determine execution type from topic
            if message.topic.startswith("task-control_"):
                message_data["type"] = "task"
            elif message.topic.startswith("plan-control_"):
                message_data["type"] = "plan"
            else:
                logger.warning("Unknown topic", topic=message.topic)
                return
            
            # Process message through the processor
            if self.message_processor:
                await self.message_processor(message_data)
            
        except json.JSONDecodeError as e:
            logger.error("Failed to decode JSON message", 
                        topic=message.topic,
                        error=str(e))
        except Exception as e:
            logger.error("Failed to process control message", 
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