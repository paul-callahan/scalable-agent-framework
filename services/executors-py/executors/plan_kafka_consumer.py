"""
Kafka consumer for handling PlanInput messages.
Listens to plan-inputs-{tenantId} topic and filters by plan_name key.
"""

import asyncio
from typing import Optional

import aiokafka
import structlog

from agentic_common.pb import PlanInput, PlanExecution, PlanResult
from .plan_kafka_producer import PlanExecutionProducer
from .plan_executor import PlanExecutor


class PlanInputConsumer:
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
        self.consumer = consumer
        self.tenant_id = tenant_id
        self.plan_name = plan_name
        self.plan_executor = plan_executor
        self.producer = producer

        self.logger = structlog.get_logger(__name__)

        # Consumer state
        self._running = False
        self._consumer_task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        """Start the Kafka consumer."""
        if self._running:
            self.logger.warning("Consumer is already running")
            return

        topics = await self.consumer.topics()
        self.logger.info(
            "Starting PlanInput consumer",
            topic=topics,
            # group_id=self.consumer.group_id,
            plan_name=self.plan_name
        )

        try:
            # Start consumer task
            self._consumer_task = asyncio.create_task(self._consume_messages())
            self._running = True

            self.logger.info("PlanInput consumer started successfully")

        except Exception as e:
            self.logger.error("Failed to start PlanInput consumer", error=str(e), exc_info=True)
            await self.stop()
            raise

    async def stop(self) -> None:
        """Stop the Kafka consumer."""
        if not self._running:
            self.logger.warning("Consumer is not running")
            return

        self.logger.info("Stopping PlanInput consumer")
        self._running = False

        # Cancel consumer task
        if self._consumer_task:
            self._consumer_task.cancel()
            try:
                await self._consumer_task
            except asyncio.CancelledError:
                pass
            self._consumer_task = None

        # Stop Kafka consumer
        if self.consumer:
            await self.consumer.stop()
            self.consumer = None

        self.logger.info("PlanInput consumer stopped")

    async def _consume_messages(self) -> None:
        """Consume messages from Kafka topic."""
        self.logger.info("_consume_messages() started")
        
        if not self.consumer:
            self.logger.warning("No consumer available, exiting _consume_messages")
            return

        try:
            self.logger.info("Starting to iterate over consumer messages")
            async for message in self.consumer:
                self.logger.info(f"Received message: {message}")
                if not self._running:
                    self.logger.info("Consumer stopped, breaking message loop")
                    break

                await self._process_message(message)

        except asyncio.CancelledError:
            self.logger.info("Consumer task cancelled")
        except Exception as e:
            self.logger.error("Error in consumer task", error=str(e), exc_info=True)
        finally:
            self.logger.info("_consume_messages() finished")

    async def _process_message(self, message: aiokafka.ConsumerRecord) -> None:
        """Process a single Kafka message."""
        try:
            # Check if message key matches our plan_name
            if message.key != self.plan_name:
                self.logger.debug(
                    "Skipping message - key mismatch",
                    message_key=message.key,
                    expected_key=self.plan_name
                )
                return

            # Deserialize PlanInput
            plan_input = message.value
            if not plan_input:
                self.logger.warning("Received null message value")
                return

            self.logger.info(
                "Processing PlanInput message",
                plan_name=plan_input.plan_name,
                tenant_id=self.tenant_id,
                message_offset=message.offset
            )

            # Execute plan
            plan_execution = await self.plan_executor.execute_plan(plan_input)

            # Publish result
            await self.producer.publish_plan_execution(plan_execution)

            self.logger.info(
                "Successfully processed PlanInput message",
                plan_name=plan_input.plan_name,
                message_offset=message.offset
            )

        except Exception as e:
            self.logger.error(
                "Error processing PlanInput message",
                error=str(e),
                message_offset=message.offset,
                exc_info=True
            )

            # Create error PlanExecution
            try:
                import uuid
                from datetime import datetime
                from agentic_common.pb import ExecutionHeader, ExecutionStatus

                # Create ExecutionHeader
                header = ExecutionHeader(
                    name=self.plan_name,
                    exec_id=str(uuid.uuid4()),
                    tenant_id=self.tenant_id,
                    created_at=datetime.utcnow().isoformat(),
                    status=ExecutionStatus.EXECUTION_STATUS_FAILED
                )

                error_execution = PlanExecution(
                    header=header,
                    parent_task_exec_ids=[],
                    result=PlanResult(
                        error_message=str(e)
                    ),
                    parent_task_names=[]
                )
                await self.producer.publish_plan_execution(error_execution)
            except Exception as publish_error:
                self.logger.error(
                    "Failed to publish error PlanExecution",
                    error=str(publish_error),
                    exc_info=True
                )

    def is_healthy(self) -> bool:
        """Check if the consumer is healthy."""
        return (
                self._running and
                self.consumer is not None and
                self._consumer_task is not None and
                not self._consumer_task.done()
        )
