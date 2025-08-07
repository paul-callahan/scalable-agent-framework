"""
Kafka consumer for handling TaskInput messages.
Listens to task-inputs-{tenantId} topic and filters by task_name key.
"""

import asyncio
from typing import Optional

import aiokafka
import structlog

from agentic_common.pb import TaskInput, TaskExecution, TaskResult
from .task_kafka_producer import TaskExecutionProducer
from .task_executor import TaskExecutor


class TaskInputConsumer:
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
        bootstrap_servers: str,
        group_id: str,
        tenant_id: str,
        task_name: str,
        task_executor: TaskExecutor,
        producer: TaskExecutionProducer,
    ):
        self.bootstrap_servers = bootstrap_servers
        self.group_id = group_id
        self.tenant_id = tenant_id
        self.task_name = task_name
        self.task_executor = task_executor
        self.producer = producer
        
        self.logger = structlog.get_logger(__name__)
        
        # Kafka consumer
        self.consumer: Optional[aiokafka.AIOKafkaConsumer] = None
        self.topic = f"task-inputs-{tenant_id}"
        
        # Consumer state
        self._running = False
        self._consumer_task: Optional[asyncio.Task] = None
    
    async def start(self) -> None:
        """Start the Kafka consumer."""
        if self._running:
            self.logger.warning("Consumer is already running")
            return
        
        self.logger.info(
            "Starting TaskInput consumer",
            topic=self.topic,
            group_id=self.group_id,
            task_name=self.task_name
        )
        
        try:
            # Create Kafka consumer
            self.consumer = aiokafka.AIOKafkaConsumer(
                self.topic,
                bootstrap_servers=self.bootstrap_servers,
                group_id=self.group_id,
                auto_offset_reset="earliest",
                enable_auto_commit=True,
                auto_commit_interval_ms=1000,
                key_deserializer=lambda k: k.decode("utf-8") if k else None,
                value_deserializer=lambda v: TaskInput.FromString(v) if v else None,
            )
            
            await self.consumer.start()
            
            # Start consumer task
            self._consumer_task = asyncio.create_task(self._consume_messages())
            self._running = True
            
            self.logger.info("TaskInput consumer started successfully")
            
        except Exception as e:
            self.logger.error("Failed to start TaskInput consumer", error=str(e), exc_info=True)
            await self.stop()
            raise
    
    async def stop(self) -> None:
        """Stop the Kafka consumer."""
        if not self._running:
            self.logger.warning("Consumer is not running")
            return
        
        self.logger.info("Stopping TaskInput consumer")
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
        
        self.logger.info("TaskInput consumer stopped")
    
    async def _consume_messages(self) -> None:
        """Consume messages from Kafka topic."""
        if not self.consumer:
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
        """Process a single Kafka message."""
        try:
            # Check if message key matches our task_name
            if message.key != self.task_name:
                self.logger.debug(
                    "Skipping message - key mismatch",
                    message_key=message.key,
                    expected_key=self.task_name
                )
                return
            
            # Deserialize TaskInput
            task_input = message.value
            if not task_input:
                self.logger.warning("Received null message value")
                return
            
            self.logger.info(
                "Processing TaskInput message",
                task_name=task_input.task_name,
                tenant_id=self.tenant_id,
                message_offset=message.offset
            )
            
            # Execute task
            task_execution = await self.task_executor.execute_task(task_input)
            
            # Publish result
            await self.producer.publish_task_execution(task_execution)
            
            self.logger.info(
                "Successfully processed TaskInput message",
                task_name=task_input.task_name,
                message_offset=message.offset
            )
            
        except Exception as e:
            self.logger.error(
                "Error processing TaskInput message",
                error=str(e),
                message_offset=message.offset,
                exc_info=True
            )
            
            # Create error TaskExecution
            try:
                import uuid
                from datetime import datetime
                from agentic_common.pb import ExecutionHeader, ExecutionStatus
                
                # Create ExecutionHeader
                header = ExecutionHeader(
                    name=self.task_name,
                    exec_id=str(uuid.uuid4()),
                    tenant_id=self.tenant_id,
                    created_at=datetime.utcnow().isoformat(),
                    status=ExecutionStatus.EXECUTION_STATUS_FAILED
                )
                
                error_execution = TaskExecution(
                    header=header,
                    parent_plan_exec_id="",
                    result=TaskResult(
                        error_message=str(e)
                    ),
                    parent_plan_name=""
                )
                await self.producer.publish_task_execution(error_execution)
            except Exception as publish_error:
                self.logger.error(
                    "Failed to publish error TaskExecution",
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