"""
Kafka consumer for handling PlanInput messages.
Listens to plan-inputs-{tenantId} topic and filters by plan_name key.
"""

import asyncio
from typing import Optional

import aiokafka
import structlog

from agentic_common.pb import PlanInput, PlanExecution, PlanResult, ExecutionHeader, ExecutionStatus
from .plan_kafka_producer import PlanExecutionProducer
from .plan_executor import PlanExecutor
from .base_input_consumer import BaseInputConsumer


class PlanInputConsumer(BaseInputConsumer):
    """
    Kafka consumer for PlanInput messages.
    
    This consumer:
    - Listens to plan-inputs-{tenantId} topic
    - Filters messages by plan_name key (configured via environment)
    - Deserializes PlanInput protobuf messages
    - Calls plan execution logic
    - Handles errors and message acknowledgment
    """

    def __init__(
        self,
        consumer: aiokafka.AIOKafkaConsumer,
        tenant_id: str,
        plan_name: str,
        plan_executor: PlanExecutor,
        producer: PlanExecutionProducer,
    ):
        super().__init__(consumer=consumer, tenant_id=tenant_id, executor_name=plan_name)
        self.plan_executor = plan_executor
        self.producer = producer

    async def _execute(self, input_message: PlanInput) -> PlanExecution:
        return await self.plan_executor.execute_plan(input_message)

    async def _publish(self, execution_message: PlanExecution) -> None:
        await self.producer.publish_plan_execution(execution_message)

    def _build_error_execution(self, error_message: str) -> PlanExecution:
        import uuid
        from datetime import datetime

        header = ExecutionHeader(
            name=self.executor_name,
            exec_id=str(uuid.uuid4()),
            tenant_id=self.tenant_id,
            created_at=datetime.utcnow().isoformat(),
            status=ExecutionStatus.EXECUTION_STATUS_FAILED,
        )
        return PlanExecution(
            header=header,
            parent_task_exec_ids=[],
            result=PlanResult(error_message=error_message),
            parent_task_names=[],
        )
