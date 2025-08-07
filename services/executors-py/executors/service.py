"""
Main service class for the executors-py microservice.
Manages the lifecycle of either a PlanExecutor or TaskExecutor as a pure Kafka consumer/producer service.
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
from .task_kafka_consumer import TaskInputConsumer
from .task_kafka_producer import TaskExecutionProducer
from .task_executor import TaskExecutor


class ExecutorService:
    """
    Main service class for the executors-py microservice.
    
    This service is a base framework for creating individual PlanExecutors and TaskExecutors.
    It can be configured to run as either:
    - A PlanExecutor: consumes plan-inputs, executes plans, publishes plan-executions
    - A TaskExecutor: consumes task-inputs, executes tasks, publishes task-executions
    
    Configuration is single-mode: either plan parameters OR task parameters, not both.
    """
    
    def __init__(
        self,
        tenant_id: str,
        plan_name: Optional[str] = None,
        plan_path: Optional[str] = None,
        plan_timeout: int = 300,
        task_name: Optional[str] = None,
        task_path: Optional[str] = None,
        task_timeout: int = 300,
        kafka_bootstrap_servers: str = "localhost:9092",
        kafka_group_id: Optional[str] = None,
    ):
        self.tenant_id = tenant_id
        self.plan_name = plan_name
        self.plan_path = plan_path
        self.plan_timeout = plan_timeout
        self.task_name = task_name
        self.task_path = task_path
        self.task_timeout = task_timeout
        self.kafka_bootstrap_servers = kafka_bootstrap_servers
        self.kafka_group_id = kafka_group_id or f"executors-{tenant_id}"
        
        self.logger = structlog.get_logger(__name__)
        
        # Validate configuration - must be either PlanExecutor OR TaskExecutor, not both
        self._validate_configuration()
        
        # Determine execution mode
        self.is_plan_executor = bool(plan_name and plan_path)
        self.is_task_executor = bool(task_name and task_path)
        
        # Service components
        self.plan_consumer: Optional[PlanInputConsumer] = None
        self.plan_producer: Optional[PlanExecutionProducer] = None
        self.plan_executor: Optional[PlanExecutor] = None
        self.task_consumer: Optional[TaskInputConsumer] = None
        self.task_producer: Optional[TaskExecutionProducer] = None
        self.task_executor: Optional[TaskExecutor] = None
        
        # Service state
        self._running = False
        self._startup_event = asyncio.Event()
        self._shutdown_event = asyncio.Event()
    
    def _validate_configuration(self) -> None:
        """Validate that the service is configured for exactly one execution mode."""
        has_plan_config = bool(self.plan_name and self.plan_path)
        has_task_config = bool(self.task_name and self.task_path)
        
        if not has_plan_config and not has_task_config:
            raise ValueError(
                "Service must be configured for either PlanExecutor or TaskExecutor mode. "
                "Provide either (plan_name, plan_path) or (task_name, task_path)."
            )
        
        if has_plan_config and has_task_config:
            raise ValueError(
                "Service cannot be configured for both PlanExecutor and TaskExecutor modes. "
                "Provide either (plan_name, plan_path) OR (task_name, task_path), not both."
            )
    
    async def start(self) -> None:
        """Start the executor service in the configured mode."""
        if self._running:
            self.logger.warning("Service is already running")
            return
        
        mode = "PlanExecutor" if self.is_plan_executor else "TaskExecutor"
        self.logger.info(f"Starting {mode} service")
        
        try:
            if self.is_plan_executor:
                await self._start_plan_executor()
            else:
                await self._start_task_executor()
            
            self._running = True
            self._startup_event.set()
            self.logger.info(f"{mode} service started successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to start {mode} service", error=str(e), exc_info=True)
            await self.stop()
            raise
    
    async def _start_plan_executor(self) -> None:
        """Initialize and start PlanExecutor components."""
        # Initialize plan executor
        self.plan_executor = PlanExecutor(
            plan_path=self.plan_path,
            plan_name=self.plan_name,
            timeout=self.plan_timeout
        )
        await self.plan_executor.load_plan()
        
        # Initialize plan Kafka producer
        self.plan_producer = PlanExecutionProducer(
            bootstrap_servers=self.kafka_bootstrap_servers,
            tenant_id=self.tenant_id,
            plan_name=self.plan_name
        )
        await self.plan_producer.start()
        
        # Initialize plan Kafka consumer
        self.plan_consumer = PlanInputConsumer(
            bootstrap_servers=self.kafka_bootstrap_servers,
            group_id=self.kafka_group_id,
            tenant_id=self.tenant_id,
            plan_name=self.plan_name,
            plan_executor=self.plan_executor,
            producer=self.plan_producer
        )
        await self.plan_consumer.start()
    
    async def _start_task_executor(self) -> None:
        """Initialize and start TaskExecutor components."""
        # Initialize task executor
        self.task_executor = TaskExecutor(
            task_path=self.task_path,
            task_name=self.task_name,
            timeout=self.task_timeout
        )
        await self.task_executor.load_task()
        
        # Initialize task Kafka producer
        self.task_producer = TaskExecutionProducer(
            bootstrap_servers=self.kafka_bootstrap_servers,
            tenant_id=self.tenant_id,
            task_name=self.task_name
        )
        await self.task_producer.start()
        
        # Initialize task Kafka consumer
        self.task_consumer = TaskInputConsumer(
            bootstrap_servers=self.kafka_bootstrap_servers,
            group_id=self.kafka_group_id,
            tenant_id=self.tenant_id,
            task_name=self.task_name,
            task_executor=self.task_executor,
            producer=self.task_producer
        )
        await self.task_consumer.start()
    
    async def stop(self) -> None:
        """Stop the executor service."""
        if not self._running:
            self.logger.warning("Service is not running")
            return
        
        mode = "PlanExecutor" if self.is_plan_executor else "TaskExecutor"
        self.logger.info(f"Stopping {mode} service")
        self._running = False
        self._shutdown_event.set()
        
        # Stop components in reverse order
        if self.is_task_executor:
            if self.task_consumer:
                await self.task_consumer.stop()
                self.task_consumer = None
            
            if self.task_producer:
                await self.task_producer.stop()
                self.task_producer = None
            
            if self.task_executor:
                await self.task_executor.cleanup()
                self.task_executor = None
        else:
            if self.plan_consumer:
                await self.plan_consumer.stop()
                self.plan_consumer = None
            
            if self.plan_producer:
                await self.plan_producer.stop()
                self.plan_producer = None
            
            if self.plan_executor:
                await self.plan_executor.cleanup()
                self.plan_executor = None
        
        self.logger.info(f"{mode} service stopped")
    
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
            if self.is_task_executor:
                # Check task components
                if self.task_consumer and not self.task_consumer.is_healthy():
                    return False
                
                if self.task_producer and not self.task_producer.is_healthy():
                    return False
                
                if self.task_executor and not self.task_executor.is_healthy():
                    return False
            else:
                # Check plan components
                if self.plan_consumer and not self.plan_consumer.is_healthy():
                    return False
                
                if self.plan_producer and not self.plan_producer.is_healthy():
                    return False
                
                if self.plan_executor and not self.plan_executor.is_healthy():
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error("Health check failed", error=str(e))
            return False 