"""
Base Kafka consumer for handling protobuf input messages.
Provides shared lifecycle, filtering, execution, and publishing behavior.
"""

import asyncio
from typing import Optional, Any

import aiokafka
import structlog


class BaseInputConsumer:
    """
    Base Kafka consumer implementing common logic for plan/task consumers.

    Subclasses must implement:
    - _execute(input_message) -> execution_message
    - _publish(execution_message) -> None
    - _build_error_execution(error_message: str) -> execution_message
    """

    def __init__(
        self,
        *,
        consumer: aiokafka.AIOKafkaConsumer,
        tenant_id: str,
        executor_name: str,
    ):
        self.consumer = consumer
        self.tenant_id = tenant_id
        self.executor_name = executor_name

        self.logger = structlog.get_logger(__name__)

        # Consumer state
        self._running = False
        self._consumer_task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        """Start the Kafka consumer."""
        if self._running:
            self.logger.warning("Consumer is already running")
            return

        try:
            self._consumer_task = asyncio.create_task(self._consume_messages())
            self._running = True
            self.logger.info("Input consumer started successfully", executor_name=self.executor_name)
        except Exception as e:
            self.logger.error("Failed to start input consumer", error=str(e), exc_info=True)
            await self.stop()
            raise

    async def stop(self) -> None:
        """Stop the Kafka consumer."""
        if not self._running:
            self.logger.warning("Consumer is not running")
            return

        self.logger.info("Stopping input consumer", executor_name=self.executor_name)
        self._running = False

        if self._consumer_task:
            self._consumer_task.cancel()
            try:
                await self._consumer_task
            except asyncio.CancelledError:
                pass
            self._consumer_task = None

        if self.consumer:
            await self.consumer.stop()
            self.consumer = None

        self.logger.info("Input consumer stopped", executor_name=self.executor_name)

    async def _consume_messages(self) -> None:
        """Consume messages from Kafka."""
        if not self.consumer:
            self.logger.warning("No consumer available, exiting _consume_messages")
            return

        try:
            async for message in self.consumer:
                if not self._running:
                    break
                await self._process_message(message)
        except asyncio.CancelledError:
            self.logger.info("Consumer task cancelled")
        except Exception as e:
            self.logger.error("Error in consumer task", error=str(e), exc_info=True)

    async def _process_message(self, message: aiokafka.ConsumerRecord) -> None:
        """Process a single Kafka message (shared logic)."""
        try:
            # Filter by executor name in message key
            if message.key != self.executor_name:
                self.logger.debug(
                    "Skipping message - key mismatch",
                    message_key=message.key,
                    expected_key=self.executor_name,
                )
                return

            input_message: Any = message.value
            if not input_message:
                self.logger.warning("Received null message value")
                return

            self.logger.info(
                "Processing input message",
                executor_name=self.executor_name,
                tenant_id=self.tenant_id,
                message_offset=message.offset,
            )

            execution = await self._execute(input_message)
            await self._publish(execution)

            self.logger.info(
                "Successfully processed input message",
                executor_name=self.executor_name,
                message_offset=message.offset,
            )

        except Exception as e:
            self.logger.error(
                "Error processing input message",
                error=str(e),
                message_offset=message.offset,
                exc_info=True,
            )
            try:
                error_execution = self._build_error_execution(str(e))
                await self._publish(error_execution)
            except Exception as publish_error:
                self.logger.error(
                    "Failed to publish error execution",
                    error=str(publish_error),
                    exc_info=True,
                )

    async def _execute(self, input_message: Any):  # pragma: no cover - abstract
        raise NotImplementedError

    async def _publish(self, execution_message: Any):  # pragma: no cover - abstract
        raise NotImplementedError

    def _build_error_execution(self, error_message: str):  # pragma: no cover - abstract
        raise NotImplementedError

    def is_healthy(self) -> bool:
        """Check if the consumer is healthy."""
        return (
            self._running
            and self.consumer is not None
            and self._consumer_task is not None
            and not self._consumer_task.done()
        )


