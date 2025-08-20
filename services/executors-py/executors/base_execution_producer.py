"""
Base Kafka producer for publishing protobuf execution messages.
Provides shared lifecycle, publishing, and health-check logic.
"""

from typing import Optional, Any

import aiokafka
import structlog


class BaseExecutionProducer:
    """
    Base Kafka producer implementing common logic for plan/task producers.

    Subclasses should expose domain-specific publish_* wrappers that delegate to
    publish_execution().
    """

    def __init__(
        self,
        *,
        producer: aiokafka.AIOKafkaProducer,
        tenant_id: str,
        executor_name: str,
        topic: str,
        label: str,
    ) -> None:
        self.producer: Optional[aiokafka.AIOKafkaProducer] = producer
        self.tenant_id = tenant_id
        self.executor_name = executor_name
        self.topic = topic
        self.label = label

        self.logger = structlog.get_logger(__name__)
        self._running = False

    async def start(self) -> None:
        if self._running:
            self.logger.warning("Producer is already running", label=self.label)
            return
        # Underlying producer is managed by the service
        self._running = True
        self.logger.info(f"{self.label} producer started successfully", topic=self.topic)

    async def stop(self) -> None:
        if not self._running:
            self.logger.warning("Producer is not running", label=self.label)
            return
        self._running = False
        if self.producer:
            await self.producer.stop()
            self.producer = None
        self.logger.info(f"{self.label} producer stopped", topic=self.topic)

    async def publish_execution(self, message: Any) -> None:
        if not self._running or not self.producer:
            raise RuntimeError("Producer is not running")
        # Send with executor_name as key; value is the protobuf message (serializer set in service)
        future = await self.producer.send_and_wait(
            topic=self.topic,
            key=self.executor_name,
            value=message,
        )
        self.logger.info(
            f"{self.label} published",
            topic=self.topic,
            partition=future.partition,
            offset=future.offset,
        )

    def is_healthy(self) -> bool:
        return self._running and self.producer is not None


