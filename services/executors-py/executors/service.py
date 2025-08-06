"""
Main service class for the executors-py microservice.
Manages the lifecycle of the plan executor as a pure Kafka consumer/producer service.
"""

import asyncio
import importlib.util
import os
import sys
from typing import Optional

import structlog

from .plan_kafka_consumer import PlanInputConsumer
from .plan_kafka_producer import PlanExecutionProducer
from .plan_executor import PlanExecutor


class PlanExecutorService:
    """
    Main service class for the executors-py microservice.
    
    This service is a pure Kafka consumer/producer that:
    - Loads user-supplied plan.py files dynamically
    - Listens to plan-inputs-{tenantId} topic
    - Executes plans with timeout handling
    - Publishes results to plan-executions-{tenantId} topic
    """
    
    def __init__(
        self,
        tenant_id: str,
        plan_name: str,
        plan_path: str,
        plan_timeout: int = 300,
        kafka_bootstrap_servers: str = "localhost:9092",
        kafka_group_id: Optional[str] = None,
    ):
        self.tenant_id = tenant_id
        self.plan_name = plan_name
        self.plan_path = plan_path
        self.plan_timeout = plan_timeout
        self.kafka_bootstrap_servers = kafka_bootstrap_servers
        self.kafka_group_id = kafka_group_id or f"executors-{tenant_id}"
        
        self.logger = structlog.get_logger(__name__)
        
        # Service components
        self.consumer: Optional[PlanInputConsumer] = None
        self.producer: Optional[PlanExecutionProducer] = None
        self.plan_executor: Optional[PlanExecutor] = None
        
        # Service state
        self._running = False
        self._startup_event = asyncio.Event()
        self._shutdown_event = asyncio.Event()
    
    async def start(self) -> None:
        """Start the executors service."""
        if self._running:
            self.logger.warning("Service is already running")
            return
        
        self.logger.info("Starting executors service")
        
        try:
            # Initialize plan executor
            self.plan_executor = PlanExecutor(
                plan_path=self.plan_path,
                plan_name=self.plan_name,
                timeout=self.plan_timeout
            )
            await self.plan_executor.load_plan()
            
            # Initialize Kafka producer
            self.producer = PlanExecutionProducer(
                bootstrap_servers=self.kafka_bootstrap_servers,
                tenant_id=self.tenant_id,
                plan_name=self.plan_name
            )
            await self.producer.start()
            
            # Initialize Kafka consumer
            self.consumer = PlanInputConsumer(
                bootstrap_servers=self.kafka_bootstrap_servers,
                group_id=self.kafka_group_id,
                tenant_id=self.tenant_id,
                plan_name=self.plan_name,
                plan_executor=self.plan_executor,
                producer=self.producer
            )
            await self.consumer.start()
            
            self._running = True
            self._startup_event.set()
            self.logger.info("Executors service started successfully")
            
        except Exception as e:
            self.logger.error("Failed to start executors service", error=str(e), exc_info=True)
            await self.stop()
            raise
    
    async def stop(self) -> None:
        """Stop the executors service."""
        if not self._running:
            self.logger.warning("Service is not running")
            return
        
        self.logger.info("Stopping executors service")
        self._running = False
        self._shutdown_event.set()
        
        # Stop components in reverse order
        if self.consumer:
            await self.consumer.stop()
            self.consumer = None
        
        if self.producer:
            await self.producer.stop()
            self.producer = None
        
        if self.plan_executor:
            await self.plan_executor.cleanup()
            self.plan_executor = None
        
        self.logger.info("Executors service stopped")
    
    async def wait_for_startup(self, timeout: Optional[float] = None) -> None:
        """Wait for the service to start up."""
        await asyncio.wait_for(self._startup_event.wait(), timeout=timeout)
    
    async def wait_for_shutdown(self, timeout: Optional[float] = None) -> None:
        """Wait for the service to shut down."""
        await asyncio.wait_for(self._shutdown_event.wait(), timeout=timeout)
    
    @property
    def is_running(self) -> bool:
        """Check if the service is running."""
        return self._running
    
    async def health_check(self) -> bool:
        """Perform a health check on the service."""
        if not self._running:
            return False
        
        try:
            # Check if consumer is healthy
            if self.consumer and not self.consumer.is_healthy():
                return False
            
            # Check if producer is healthy
            if self.producer and not self.producer.is_healthy():
                return False
            
            # Check if plan executor is healthy
            if self.plan_executor and not self.plan_executor.is_healthy():
                return False
            
            return True
            
        except Exception as e:
            self.logger.error("Health check failed", error=str(e))
            return False 