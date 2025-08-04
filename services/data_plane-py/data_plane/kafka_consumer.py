"""
Kafka consumer for data plane microservice.

This module implements Kafka consumer for TaskExecution and PlanExecution
topics using aiokafka==0.11.0 with manual commit after successful
database persistence.
"""

import asyncio
from typing import Optional

from aiokafka import AIOKafkaConsumer
from aiokafka.errors import KafkaError
from structlog import get_logger

from agentic_common.kafka_utils import create_kafka_consumer
from agentic_common.logging_config import log_kafka_message
from agentic_common import ProtobufUtils
from .database import get_async_session
from .models import PlanExecution, TaskExecution

logger = get_logger(__name__)


class DataPlaneConsumer:
    """
    Kafka consumer for the data plane service.
    
    Consumes TaskExecution and PlanExecution messages and persists them
    to the database.
    """
    
    def __init__(self, group_id: str = "data-plane-group"):
        """
        Initialize the consumer.
        
        Args:
            group_id: Kafka consumer group ID
        """
        self.group_id = group_id
        self.consumer: Optional[AIOKafkaConsumer] = None
        self.running = False
        
    async def start(self) -> None:
        """Start the Kafka consumer."""
        try:
            # Create consumer for task and plan execution topics
            topics = [
                "task-executions_*",  # Pattern for tenant-specific topics
                "plan-executions_*",  # Pattern for tenant-specific topics
            ]
            
            self.consumer = await create_kafka_consumer(
                topics=topics,
                group_id=self.group_id,
                client_id="data-plane-consumer",
            )
            
            await self.consumer.start()
            self.running = True
            
            logger.info("Data plane consumer started", 
                       group_id=self.group_id,
                       topics=topics)
            
        except Exception as e:
            logger.error("Failed to start data plane consumer", error=str(e))
            raise
    
    async def stop(self) -> None:
        """Stop the Kafka consumer."""
        if self.consumer:
            self.running = False
            await self.consumer.stop()
            await self.consumer.close()
            logger.info("Data plane consumer stopped")
    
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
        
        # Determine message type based on topic
        if message.topic.startswith("task-executions_"):
            await self._process_task_execution(message)
        elif message.topic.startswith("plan-executions_"):
            await self._process_plan_execution(message)
        else:
            logger.warning("Unknown topic", topic=message.topic)
    
    async def _process_task_execution(self, message) -> None:
        """
        Process TaskExecution message.
        
        Args:
            message: Kafka message containing TaskExecution
        """
        try:
            # Deserialize protobuf message using consistent utilities
            task_execution = ProtobufUtils.deserialize_task_execution(message.value)
            
            # Extract tenant_id from topic
            tenant_id = message.topic.split("_", 1)[1]
            
            # Persist to database
            async for session in get_async_session():
                db_task = TaskExecution(
                    id=task_execution.header.id,
                    parent_id=task_execution.header.parent_id or None,
                    graph_id=task_execution.header.graph_id,
                    lifetime_id=task_execution.header.lifetime_id,
                    tenant_id=tenant_id,
                    attempt=task_execution.header.attempt,
                    iteration_idx=task_execution.header.iteration_idx,
                    created_at=task_execution.header.created_at,
                    status=task_execution.header.status.name,
                    edge_taken=task_execution.header.edge_taken or None,
                    task_type=task_execution.task_type,
                    result_data=self._extract_task_result_data(task_execution.result),
                    result_mime_type=task_execution.result.mime_type or None,
                    result_size_bytes=task_execution.result.size_bytes or None,
                    error_message=task_execution.result.error_message or None,
                )
                
                session.add(db_task)
                await session.commit()
                
                logger.info("TaskExecution persisted", 
                           execution_id=task_execution.header.id,
                           tenant_id=tenant_id,
                           task_type=task_execution.task_type)
                
        except Exception as e:
            logger.error("Failed to process TaskExecution", 
                        execution_id=getattr(task_execution, 'header', {}).get('id', 'unknown'),
                        error=str(e))
            raise
    
    async def _process_plan_execution(self, message) -> None:
        """
        Process PlanExecution message.
        
        Args:
            message: Kafka message containing PlanExecution
        """
        try:
            # Deserialize protobuf message using consistent utilities
            plan_execution = ProtobufUtils.deserialize_plan_execution(message.value)
            
            # Extract tenant_id from topic
            tenant_id = message.topic.split("_", 1)[1]
            
            # Persist to database
            async for session in get_async_session():
                db_plan = PlanExecution(
                    id=plan_execution.header.id,
                    parent_id=plan_execution.header.parent_id or None,
                    graph_id=plan_execution.header.graph_id,
                    lifetime_id=plan_execution.header.lifetime_id,
                    tenant_id=tenant_id,
                    attempt=plan_execution.header.attempt,
                    iteration_idx=plan_execution.header.iteration_idx,
                    created_at=plan_execution.header.created_at,
                    status=plan_execution.header.status.name,
                    edge_taken=plan_execution.header.edge_taken or None,
                    plan_type=plan_execution.plan_type,
                    input_task_id=plan_execution.input_task_id or None,
                    result_next_task_ids=list(plan_execution.result.next_task_ids),
                    result_metadata=dict(plan_execution.result.metadata),
                    error_message=plan_execution.result.error_message or None,
                    confidence=plan_execution.result.confidence or None,
                )
                
                session.add(db_plan)
                await session.commit()
                
                logger.info("PlanExecution persisted", 
                           execution_id=plan_execution.header.id,
                           tenant_id=tenant_id,
                           plan_type=plan_execution.plan_type)
                
        except Exception as e:
            logger.error("Failed to process PlanExecution", 
                        execution_id=getattr(plan_execution, 'header', {}).get('id', 'unknown'),
                        error=str(e))
            raise
    
    def _extract_task_result_data(self, task_result) -> Optional[dict]:
        """
        Extract task result data from protobuf.
        
        Args:
            task_result: TaskResult protobuf message
            
        Returns:
            Dictionary with result data or None
        """
        if task_result.HasField("inline_data"):
            # Convert Any protobuf to dictionary
            return {
                "type": "inline",
                "data": task_result.inline_data,
            }
        elif task_result.HasField("uri"):
            return {
                "type": "uri",
                "uri": task_result.uri,
            }
        else:
            return None 