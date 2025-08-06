"""
Kafka producer for publishing PlanExecution messages.
Publishes to plan-executions-{tenantId} topic with plan_name as key.
"""

import asyncio
from typing import Optional

import aiokafka
import structlog

from agentic_common.pb import PlanExecution, PlanResult


class PlanExecutionProducer:
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
        bootstrap_servers: str,
        tenant_id: str,
        plan_name: str,
    ):
        self.bootstrap_servers = bootstrap_servers
        self.tenant_id = tenant_id
        self.plan_name = plan_name
        
        self.logger = structlog.get_logger(__name__)
        
        # Kafka producer
        self.producer: Optional[aiokafka.AIOKafkaProducer] = None
        self.topic = f"plan-executions-{tenant_id}"
        
        # Producer state
        self._running = False
    
    async def start(self) -> None:
        """Start the Kafka producer."""
        if self._running:
            self.logger.warning("Producer is already running")
            return
        
        self.logger.info(
            "Starting PlanExecution producer",
            topic=self.topic,
            plan_name=self.plan_name
        )
        
        try:
            # Create Kafka producer
            self.producer = aiokafka.AIOKafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                key_serializer=lambda k: k.encode("utf-8") if k else None,
                value_serializer=lambda v: v.SerializeToString() if v else None,
                acks="all",  # Wait for all replicas
                retries=3,
                max_in_flight_requests_per_connection=1,
            )
            
            await self.producer.start()
            self._running = True
            
            self.logger.info("PlanExecution producer started successfully")
            
        except Exception as e:
            self.logger.error("Failed to start PlanExecution producer", error=str(e), exc_info=True)
            await self.stop()
            raise
    
    async def stop(self) -> None:
        """Stop the Kafka producer."""
        if not self._running:
            self.logger.warning("Producer is not running")
            return
        
        self.logger.info("Stopping PlanExecution producer")
        self._running = False
        
        if self.producer:
            await self.producer.stop()
            self.producer = None
        
        self.logger.info("PlanExecution producer stopped")
    
    async def publish_plan_execution(self, plan_execution: PlanExecution) -> None:
        """Publish a PlanExecution message to Kafka."""
        if not self._running or not self.producer:
            raise RuntimeError("Producer is not running")
        
        try:
            self.logger.info(
                "Publishing PlanExecution",
                plan_name=plan_execution.header.name,
                tenant_id=plan_execution.header.tenant_id,
                error_message=plan_execution.result.error_message if plan_execution.result else ""
            )
            
            # Send message
            future = await self.producer.send_and_wait(
                topic=self.topic,
                key=self.plan_name,
                value=plan_execution
            )
            
            self.logger.info(
                "Successfully published PlanExecution",
                plan_name=plan_execution.plan_name,
                topic=self.topic,
                partition=future.partition,
                offset=future.offset
            )
            
        except Exception as e:
            self.logger.error(
                "Failed to publish PlanExecution",
                error=str(e),
                plan_name=plan_execution.plan_name,
                exc_info=True
            )
            raise
    

    
    def is_healthy(self) -> bool:
        """Check if the producer is healthy."""
        return self._running and self.producer is not None 