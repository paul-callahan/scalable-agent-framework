"""
Kafka consumer for executor microservice.

This module implements Kafka consumer for executor topics using
aiokafka==0.11.0. Subscribe to task-results_* and plan-results_* topics
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


class ExecutorConsumer:
    """
    Kafka consumer for the executor service.
    
    Consumes TaskResult and PlanResult messages from executor topics and
    processes them through task and plan execution.
    """
    
    def __init__(self, group_id: str = "executor-group"):
        """
        Initialize the consumer.
        
        Args:
            group_id: Kafka consumer group ID
        """
        self.group_id = group_id
        self.consumer: Optional[AIOKafkaConsumer] = None
        self.running = False
        self.task_processor = None
        self.plan_processor = None
        
    def set_task_processor(self, processor):
        """
        Set the task processor callback.
        
        Args:
            processor: Function to process task messages
        """
        self.task_processor = processor
        
    def set_plan_processor(self, processor):
        """
        Set the plan processor callback.
        
        Args:
            processor: Function to process plan messages
        """
        self.plan_processor = processor
        
    async def start(self) -> None:
        """Start the Kafka consumer."""
        try:
            # Create consumer for executor topics
            topics = [
                "task-results_*",  # Pattern for tenant-specific topics
                "plan-results_*",  # Pattern for tenant-specific topics
            ]
            
            self.consumer = await create_kafka_consumer(
                topics=topics,
                group_id=self.group_id,
                client_id="executor-consumer",
            )
            
            await self.consumer.start()
            self.running = True
            
            logger.info("Executor consumer started", 
                       group_id=self.group_id,
                       topics=topics)
            
        except Exception as e:
            logger.error("Failed to start executor consumer", error=str(e))
            raise
    
    async def stop(self) -> None:
        """Stop the Kafka consumer."""
        if self.consumer:
            self.running = False
            await self.consumer.stop()
            await self.consumer.close()
            logger.info("Executor consumer stopped")
    
    async def consume_messages(self) -> None:
        """Consume messages from Kafka topics."""
        if not self.consumer:
            raise RuntimeError("Consumer not initialized")
        
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
            
            # Determine message type and route to appropriate processor
            if message.topic.startswith("task-results_"):
                if self.task_processor:
                    await self.task_processor(message_data)
                else:
                    logger.warning("No task processor set")
                    
            elif message.topic.startswith("plan-results_"):
                if self.plan_processor:
                    await self.plan_processor(message_data)
                else:
                    logger.warning("No plan processor set")
                    
            else:
                logger.warning("Unknown topic", topic=message.topic)
            
        except json.JSONDecodeError as e:
            logger.error("Failed to decode JSON message", 
                        topic=message.topic,
                        error=str(e))
        except Exception as e:
            logger.error("Failed to process executor message", 
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