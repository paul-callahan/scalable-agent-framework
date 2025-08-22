"""
Kafka producer for publishing PlanExecution messages.
Publishes to plan-executions-{tenantId} topic with plan_name as key.
"""

import asyncio
from typing import Optional

import aiokafka
import structlog

from agentic_common.pb import PlanExecution, PlanResult
from .base_execution_producer import BaseExecutionProducer


class PlanExecutionProducer(BaseExecutionProducer):
    """
    Kafka producer for PlanExecution messages.
    
    This producer:
    - Publishes to plan-executions-{tenantId} topic
    - Uses plan_name as message key for partitioning
    - Serializes PlanExecution protobuf messages
    - Handles errors and logging
    """
    
    def __init__(
        self,
        producer: aiokafka.AIOKafkaProducer,
        tenant_id: str,
        plan_name: str,
    ):
        topic = f"plan-executions-{tenant_id}"
        super().__init__(
            producer=producer,
            tenant_id=tenant_id,
            executor_name=plan_name,
            topic=topic,
            label="PlanExecution",
        )
    
    async def start(self) -> None:
        await super().start()
    
    async def stop(self) -> None:
        await super().stop()
    
    async def publish_plan_execution(self, plan_execution: PlanExecution) -> None:
        await self.publish_execution(plan_execution)
    

    
    def is_healthy(self) -> bool:
        """Check if the producer is healthy."""
        return self._running and self.producer is not None 