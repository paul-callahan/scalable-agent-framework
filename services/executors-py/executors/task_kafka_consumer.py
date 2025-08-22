"""
Kafka consumer for handling TaskInput messages.
Listens to task-inputs-{tenantId} topic and filters by task_name key.
"""

import asyncio
from typing import Optional

import aiokafka

from agentic_common.pb import TaskInput, TaskExecution, TaskResult, ExecutionHeader, ExecutionStatus
from .task_kafka_producer import TaskExecutionProducer
from .task_executor import TaskExecutor
from .base_input_consumer import BaseInputConsumer


class TaskInputConsumer(BaseInputConsumer):
    """
    Kafka consumer for TaskInput messages.
    
    This consumer:
    - Listens to task-inputs-{tenantId} topic
    - Filters messages by task_name key (configured via environment)
    - Deserializes TaskInput protobuf messages
    - Calls task execution logic
    - Handles errors and message acknowledgment
    """
    
    def __init__(
        self,
        consumer: aiokafka.AIOKafkaConsumer,
        tenant_id: str,
        task_name: str,
        task_executor: TaskExecutor,
        producer: TaskExecutionProducer,
        **_kwargs,
    ):
        super().__init__(consumer=consumer, tenant_id=tenant_id, executor_name=task_name)
        self.task_executor = task_executor
        self.producer = producer
    
    # Start/stop are inherited from BaseInputConsumer for symmetry with PlanInputConsumer
    
    async def _execute(self, input_message: TaskInput) -> TaskExecution:
        return await self.task_executor.execute_task(input_message)

    async def _publish(self, execution_message: TaskExecution) -> None:
        await self.producer.publish_task_execution(execution_message)

    def _build_error_execution(self, error_message: str) -> TaskExecution:
        import uuid
        from datetime import datetime

        header = ExecutionHeader(
            name=self.executor_name,
            exec_id=str(uuid.uuid4()),
            tenant_id=self.tenant_id,
            created_at=datetime.utcnow().isoformat(),
            status=ExecutionStatus.EXECUTION_STATUS_FAILED,
        )
        return TaskExecution(
            header=header,
            parent_plan_exec_id="",
            result=TaskResult(error_message=error_message),
            parent_plan_name="",
        )