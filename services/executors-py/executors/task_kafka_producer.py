"""
Kafka producer for publishing TaskExecution messages.
Publishes to task-executions-{tenantId} topic with task_name as key.
"""

import asyncio
from typing import Optional

import aiokafka
import structlog

from agentic_common.pb import TaskExecution, TaskResult
from .base_execution_producer import BaseExecutionProducer


class TaskExecutionProducer(BaseExecutionProducer):
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
        producer: aiokafka.AIOKafkaProducer,
    ):
        self.bootstrap_servers = bootstrap_servers
        topic = f"task-executions-{tenant_id}"
        super().__init__(
            producer=producer,
            tenant_id=tenant_id,
            executor_name=task_name,
            topic=topic,
            label="TaskExecution",
        )
        self.task_name = task_name
    
    async def start(self) -> None:
        await super().start()
    
    async def stop(self) -> None:
        await super().stop()
    
    async def publish_task_execution(self, task_execution: TaskExecution) -> None:
        await self.publish_execution(task_execution)
    
    def is_healthy(self) -> bool:
        """Check if the producer is healthy."""
        return self._running and self.producer is not None 