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
import aiokafka
from enum import Enum

from .plan_kafka_consumer import PlanInputConsumer
from .plan_kafka_producer import PlanExecutionProducer
from .plan_executor import PlanExecutor
from .task_kafka_consumer import TaskInputConsumer
from .task_kafka_producer import TaskExecutionProducer
from .task_executor import TaskExecutor
from .base_input_consumer import BaseInputConsumer
from .base_execution_producer import BaseExecutionProducer


class ExecutorMode(Enum):
	PLAN = "plan"
	TASK = "task"


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
		mode: ExecutorMode,
		executor_name: str,
		executor_path: str,
		executor_timeout: int,
		kafka_bootstrap_servers: str = "localhost:9092",
		kafka_group_id: Optional[str] = None,
	):
		self.tenant_id = tenant_id
		self.kafka_bootstrap_servers = kafka_bootstrap_servers
		self.kafka_group_id = kafka_group_id or f"executors-{tenant_id}"
		self.logger = structlog.get_logger(__name__)
		self.mode = mode
		# Unified executor fields
		self.executor_name = executor_name
		self.executor_path = executor_path
		self.executor_timeout = executor_timeout
		# Validate configuration now that fields are set
		self._validate_configuration(mode)
		# Service components (guaranteed to be initialized during start when running)
		self.input_consumer: BaseInputConsumer  # set in start()
		self.execution_producer: BaseExecutionProducer  # set in start()
		self.plan_executor: Optional[PlanExecutor] = None
		self.task_executor: Optional[TaskExecutor] = None
		# Internal Kafka clients for Task mode when injected
		self._task_producer_client: Optional[aiokafka.AIOKafkaProducer] = None
		self._task_consumer_client: Optional[aiokafka.AIOKafkaConsumer] = None
		
		# Service state
		self._running = False
		self._startup_event = asyncio.Event()
		self._shutdown_event = asyncio.Event()
	
	def _validate_configuration(self, mode: ExecutorMode) -> None:
		"""Validate that the service is configured for exactly one execution mode."""
		# Require non-empty executor fields
		if not (self.executor_name and self.executor_path):
			raise ValueError(
				"Service must be configured for either PlanExecutor or TaskExecutor mode. "
				"Provide either (plan_name, plan_path) or (task_name, task_path)."
			)
	
	async def start(self) -> None:
		"""Start the executor service in the configured mode."""
		if self._running:
			self.logger.warning("Service is already running")
			return
		
		self.logger.info(f"Starting {self.mode} executor service")
		
		try:
			if self.mode is ExecutorMode.PLAN:
				await self._start_plan_executor()
			else:
				await self._start_task_executor()
			
			self._running = True
			self._startup_event.set()
			self.logger.info(f"{self.mode} executor service started successfully")
			
		except Exception as e:
			self.logger.error(f"Failed to start {self.mode} executor service", error=str(e), exc_info=True)
			await self.stop()
			raise
	
	async def _start_plan_executor(self) -> None:
		"""Initialize and start PlanExecutor components."""
		# Initialize plan executor
		self.plan_executor = PlanExecutor(
			plan_path=self.executor_path,
			plan_name=self.executor_name,
			timeout=self.executor_timeout
		)
		await self.plan_executor.load_plan()
		
		# Create Kafka producer
		from agentic_common.pb import PlanExecution
		producer = aiokafka.AIOKafkaProducer(
			bootstrap_servers=self.kafka_bootstrap_servers,
			key_serializer=lambda k: k.encode("utf-8") if k else None,
			value_serializer=lambda v: v.SerializeToString() if v else None,
			acks="all",  # Wait for all replicas
			retry_backoff_ms=100,
		)
		await producer.start()
		
		# Initialize plan Kafka producer
		self.execution_producer = PlanExecutionProducer(
			producer=producer,
			tenant_id=self.tenant_id,
			plan_name=self.executor_name
		)
		await self.execution_producer.start()
		
		# Create Kafka consumer
		from agentic_common.pb import PlanInput
		topic = f"plan-inputs-{self.tenant_id}"
		consumer = aiokafka.AIOKafkaConsumer(
			topic,
			bootstrap_servers=self.kafka_bootstrap_servers,
			group_id=self.kafka_group_id,
			auto_offset_reset="earliest",
			enable_auto_commit=True,
			auto_commit_interval_ms=1000,
			key_deserializer=lambda k: k.decode("utf-8") if k else None,
			value_deserializer=lambda v: PlanInput.FromString(v) if v else None,
		)
		await consumer.start()
		
		# Initialize plan Kafka consumer
		self.input_consumer = PlanInputConsumer(
			consumer=consumer,
			tenant_id=self.tenant_id,
			plan_name=self.executor_name,
			plan_executor=self.plan_executor,
			producer=self.execution_producer
		)
		await self.input_consumer.start()
	
	async def _start_task_executor(self) -> None:
		"""Initialize and start TaskExecutor components."""
		# Initialize task executor
		self.task_executor = TaskExecutor(
			task_path=self.executor_path,
			task_name=self.executor_name,
			timeout=self.executor_timeout
		)
		await self.task_executor.load_task()
		
		# Initialize task Kafka producer (create in service and inject)
		self._task_producer_client = aiokafka.AIOKafkaProducer(
			bootstrap_servers=self.kafka_bootstrap_servers,
			key_serializer=lambda k: k.encode("utf-8") if k else None,
			value_serializer=lambda v: v.SerializeToString() if v else None,
			acks="all",
			retry_backoff_ms=100,
		)
		await self._task_producer_client.start()
		self.execution_producer = TaskExecutionProducer(
			bootstrap_servers=self.kafka_bootstrap_servers,
			tenant_id=self.tenant_id,
			task_name=self.executor_name,
			producer=self._task_producer_client,
		)
		await self.execution_producer.start()
		
		# Initialize task Kafka consumer (create in service and inject)
		from agentic_common.pb import TaskInput
		self._task_consumer_client = aiokafka.AIOKafkaConsumer(
			f"task-inputs-{self.tenant_id}",
			bootstrap_servers=self.kafka_bootstrap_servers,
			group_id=self.kafka_group_id,
			auto_offset_reset="earliest",
			enable_auto_commit=True,
			auto_commit_interval_ms=1000,
			key_deserializer=lambda k: k.decode("utf-8") if k else None,
			value_deserializer=lambda v: TaskInput.FromString(v) if v else None,
		)
		await self._task_consumer_client.start()
		self.input_consumer = TaskInputConsumer(
			consumer=self._task_consumer_client,
			tenant_id=self.tenant_id,
			task_name=self.executor_name,
			task_executor=self.task_executor,
			producer=self.execution_producer,
		)
		await self.input_consumer.start()
	
	async def stop(self) -> None:
		"""Stop the executor service."""
		if not self._running:
			self.logger.warning("Service is not running")
			return
		
		self.logger.info(f"Stopping {self.mode} executor service")
		self._running = False
		self._shutdown_event.set()
		
		# Stop components in reverse order
		# Common components
		await self.input_consumer.stop()
		await self.execution_producer.stop()
		# Mode-specific components
		if self.mode is ExecutorMode.TASK:
			# Stop injected Kafka clients for task mode
			if self._task_consumer_client:
				try:
					await self._task_consumer_client.stop()
				finally:
					self._task_consumer_client = None
			if self._task_producer_client:
				try:
					await self._task_producer_client.stop()
				finally:
					self._task_producer_client = None
			if self.task_executor:
				await self.task_executor.cleanup()
				self.task_executor = None
		else:
			if self.plan_executor:
				await self.plan_executor.cleanup()
		
		self.logger.info(f"{self.mode} executor service stopped")
	
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
			if self.input_consumer and not self.input_consumer.is_healthy():
				return False
			if self.execution_producer and not self.execution_producer.is_healthy():
				return False
			if self.mode is ExecutorMode.TASK:
				return bool(self.task_executor and self.task_executor.is_healthy())
			else:
				return bool(self.plan_executor and self.plan_executor.is_healthy())
		except Exception as e:
			self.logger.error("Health check failed", error=str(e))
			return False