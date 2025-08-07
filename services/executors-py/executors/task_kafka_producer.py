"""
Kafka producer for publishing TaskExecution messages.
Publishes to task-executions-{tenantId} topic with task_name as key.
"""

import asyncio
from typing import Optional

import aiokafka
import structlog

from agentic_common.pb import TaskExecution, TaskResult


class TaskExecutionProducer:
    """
    Kafka producer for TaskExecution messages.
    
    This producer:
    - Publishes to task-executions-{tenantId} topic
    - Uses task_name as message key for partitioning
    - Serializes TaskExecution protobuf messages
    - Handles errors and logging
    """
    
    def __init__(
        self,
        bootstrap_servers: str,
        tenant_id: str,
        task_name: str,
    ):
        self.bootstrap_servers = bootstrap_servers
        self.tenant_id = tenant_id
        self.task_name = task_name
        
        self.logger = structlog.get_logger(__name__)
        
        # Kafka producer
        self.producer: Optional[aiokafka.AIOKafkaProducer] = None
        self.topic = f"task-executions-{tenant_id}"
        
        # Producer state
        self._running = False
    
    async def start(self) -> None:
        """Start the Kafka producer."""
        if self._running:
            self.logger.warning("Producer is already running")
            return
        
        self.logger.info(
            "Starting TaskExecution producer",
            topic=self.topic,
            task_name=self.task_name
        )
        
        try:
            # Create Kafka producer
            self.producer = aiokafka.AIOKafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                key_serializer=lambda k: k.encode("utf-8") if k else None,
                value_serializer=lambda v: v.SerializeToString() if v else None,
                acks="all",  # Wait for all replicas
                retry_backoff_ms=100,
            )
            
            await self.producer.start()
            self._running = True
            
            self.logger.info("TaskExecution producer started successfully")
            
        except Exception as e:
            self.logger.error("Failed to start TaskExecution producer", error=str(e), exc_info=True)
            await self.stop()
            raise
    
    async def stop(self) -> None:
        """Stop the Kafka producer."""
        if not self._running:
            self.logger.warning("Producer is not running")
            return
        
        self.logger.info("Stopping TaskExecution producer")
        self._running = False
        
        if self.producer:
            await self.producer.stop()
            self.producer = None
        
        self.logger.info("TaskExecution producer stopped")
    
    async def publish_task_execution(self, task_execution: TaskExecution) -> None:
        """Publish a TaskExecution message to Kafka."""
        if not self._running or not self.producer:
            raise RuntimeError("Producer is not running")
        
        try:
            self.logger.info(
                "Publishing TaskExecution",
                task_name=task_execution.header.name,
                tenant_id=task_execution.header.tenant_id,
                error_message=task_execution.result.error_message if task_execution.result else ""
            )
            
            # Send message
            future = await self.producer.send_and_wait(
                topic=self.topic,
                key=self.task_name,
                value=task_execution
            )
            
            self.logger.info(
                "Successfully published TaskExecution",
                task_name=task_execution.header.name,
                topic=self.topic,
                partition=future.partition,
                offset=future.offset
            )
            
        except Exception as e:
            self.logger.error(
                "Failed to publish TaskExecution",
                error=str(e),
                task_name=task_execution.header.name,
                exc_info=True
            )
            raise
    
    def is_healthy(self) -> bool:
        """Check if the producer is healthy."""
        return self._running and self.producer is not None 