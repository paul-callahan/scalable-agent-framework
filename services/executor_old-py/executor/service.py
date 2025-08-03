"""
Main executor service orchestrator.

This module implements the main executor service orchestrator that coordinates
Kafka consumers for both task and plan results, manages the task/plan registry,
handles execution routing, manages Kafka producers, and runs the FastAPI server.
"""

import asyncio
import signal
from typing import Optional

from fastapi import FastAPI
from structlog import get_logger
from uvicorn import Config, Server

from agentic_common.health import (
    HealthCheck,
    create_kafka_health_check,
    create_service_health_check,
)
from .api import create_executor_app
from .kafka_consumer import ExecutorConsumer
from .kafka_producer import ExecutorProducer
from .registry import RegistryManager
from .task_executor import TaskExecutor
from .plan_executor import PlanExecutor

logger = get_logger(__name__)


class ExecutorService:
    """
    Main executor service orchestrator.
    
    Coordinates Kafka consumers for both task and plan results, manages
    the task/plan registry, handles execution routing, manages Kafka
    producers, and runs the FastAPI server.
    """
    
    def __init__(self, host: str = "0.0.0.0", port: int = 8000):
        """
        Initialize the executor service.
        
        Args:
            host: Host to bind the server to
            port: Port to bind the server to
        """
        self.host = host
        self.port = port
        self.health_check = HealthCheck()
        self.consumer = ExecutorConsumer()
        self.producer = ExecutorProducer()
        self.registry_manager = RegistryManager()
        self.task_executor = TaskExecutor(self.registry_manager.task_registry)
        self.plan_executor = PlanExecutor(self.registry_manager.plan_registry)
        self.app: Optional[FastAPI] = None
        self.server: Optional[Server] = None
        self.running = False
        
    async def start(self) -> None:
        """Start the executor service."""
        try:
            logger.info("Starting executor service")
            
            # Add health checks
            self.health_check.add_health_check(
                create_kafka_health_check(self.producer)
            )
            self.health_check.add_health_check(
                create_service_health_check("executor")
            )
            
            # Start Kafka components
            await self.producer.start()
            await self.consumer.start()
            
            # Set up message processors
            self.consumer.set_task_processor(self._process_task_message)
            self.consumer.set_plan_processor(self._process_plan_message)
            
            # Create FastAPI app
            self.app = create_executor_app(
                health_check=self.health_check,
                consumer=self.consumer,
                producer=self.producer,
                registry_manager=self.registry_manager,
                task_executor=self.task_executor,
                plan_executor=self.plan_executor,
            )
            
            # Start FastAPI server
            config = Config(
                app=self.app,
                host=self.host,
                port=self.port,
                log_level="info",
            )
            self.server = Server(config)
            
            # Set up signal handlers for graceful shutdown
            for sig in (signal.SIGTERM, signal.SIGINT):
                signal.signal(sig, self._signal_handler)
            
            self.running = True
            logger.info("Executor service started", 
                       host=self.host,
                       port=self.port)
            
        except Exception as e:
            logger.error("Failed to start executor service", error=str(e))
            await self.stop()
            raise
    
    async def stop(self) -> None:
        """Stop the executor service."""
        logger.info("Stopping executor service")
        self.running = False
        
        try:
            # Stop Kafka components
            await self.consumer.stop()
            await self.producer.stop()
            
            # Stop FastAPI server
            if self.server:
                self.server.should_exit = True
            
            logger.info("Executor service stopped")
            
        except Exception as e:
            logger.error("Error stopping executor service", error=str(e))
    
    async def run(self) -> None:
        """Run the executor service."""
        if not self.server:
            raise RuntimeError("Service not started")
        
        try:
            # Start consumer in background
            consumer_task = asyncio.create_task(
                self.consumer.consume_messages()
            )
            
            # Start FastAPI server
            await self.server.serve()
            
        except Exception as e:
            logger.error("Executor service error", error=str(e))
            raise
        
        finally:
            # Cancel consumer task
            if 'consumer_task' in locals():
                consumer_task.cancel()
                try:
                    await consumer_task
                except asyncio.CancelledError:
                    pass
    
    async def _process_task_message(self, message_data: dict) -> None:
        """
        Process task message from Kafka.
        
        Args:
            message_data: Message data from Kafka
        """
        try:
            execution_id = message_data.get("execution_id")
            tenant_id = message_data.get("tenant_id")
            task_type = message_data.get("task_type")
            
            logger.info("Processing task message", 
                       execution_id=execution_id,
                       tenant_id=tenant_id,
                       task_type=task_type)
            
            # Create PlanResult from message data
            from agentic.core.plan import PlanResult
            plan_result = PlanResult(
                next_task_ids=message_data.get("next_task_ids", []),
                metadata=message_data.get("metadata", {}),
                error_message=message_data.get("error_message"),
                confidence=message_data.get("confidence", 1.0),
            )
            
            # Execute task
            execution_data = await self.task_executor.execute_task(
                task_type=task_type,
                plan_result=plan_result,
                execution_id=execution_id,
                tenant_id=tenant_id,
            )
            
            if execution_data:
                # Publish task execution
                await self.producer.publish_task_execution(
                    tenant_id=tenant_id,
                    task_execution=execution_data,
                )
            
        except Exception as e:
            logger.error("Failed to process task message", 
                        message_data=message_data,
                        error=str(e))
            raise
    
    async def _process_plan_message(self, message_data: dict) -> None:
        """
        Process plan message from Kafka.
        
        Args:
            message_data: Message data from Kafka
        """
        try:
            execution_id = message_data.get("execution_id")
            tenant_id = message_data.get("tenant_id")
            plan_type = message_data.get("plan_type")
            
            logger.info("Processing plan message", 
                       execution_id=execution_id,
                       tenant_id=tenant_id,
                       plan_type=plan_type)
            
            # Create TaskResult from message data
            from agentic.core.task import TaskResult
            task_result = TaskResult(
                data=message_data.get("result_data"),
                mime_type=message_data.get("mime_type", "application/json"),
                size_bytes=message_data.get("size_bytes", 0),
                error_message=message_data.get("error_message"),
            )
            
            # Execute plan
            execution_data = await self.plan_executor.execute_plan(
                plan_type=plan_type,
                task_result=task_result,
                execution_id=execution_id,
                tenant_id=tenant_id,
            )
            
            if execution_data:
                # Publish plan execution
                await self.producer.publish_plan_execution(
                    tenant_id=tenant_id,
                    plan_execution=execution_data,
                )
            
        except Exception as e:
            logger.error("Failed to process plan message", 
                        message_data=message_data,
                        error=str(e))
            raise
    
    def _signal_handler(self, signum, frame) -> None:
        """
        Handle shutdown signals.
        
        Args:
            signum: Signal number
            frame: Current stack frame
        """
        signal_name = signal.Signals(signum).name
        logger.info("Received shutdown signal", signal=signal_name)
        
        # Schedule shutdown
        asyncio.create_task(self.stop())
    
    async def health_check_async(self) -> bool:
        """
        Perform async health check.
        
        Returns:
            True if service is healthy, False otherwise
        """
        try:
            # Check Kafka producer
            producer_healthy = await self.producer.health_check()
            
            # Check consumer
            consumer_healthy = self.consumer.running
            
            # Check registry
            registry_healthy = len(self.task_executor.get_available_task_types()) >= 0
            
            return producer_healthy and consumer_healthy and registry_healthy
            
        except Exception as e:
            logger.error("Health check failed", error=str(e))
            return False
    
    def get_status(self) -> dict:
        """
        Get service status.
        
        Returns:
            Dictionary with service status
        """
        return {
            "running": self.running,
            "host": self.host,
            "port": self.port,
            "consumer": {
                "running": self.consumer.running,
                "group_id": self.consumer.group_id,
            },
            "producer": {
                "initialized": self.producer.producer is not None,
            },
            "registry": {
                "total_tasks": len(self.task_executor.get_available_task_types()),
                "total_plans": len(self.plan_executor.get_available_plan_types()),
            },
        }
    
    def register_task(self, task_type: str, task_class) -> None:
        """
        Register a task class.
        
        Args:
            task_type: Task type identifier
            task_class: Task class to register
        """
        self.registry_manager.register_task(task_type, task_class)
    
    def register_plan(self, plan_type: str, plan_class) -> None:
        """
        Register a plan class.
        
        Args:
            plan_type: Plan type identifier
            plan_class: Plan class to register
        """
        self.registry_manager.register_plan(plan_type, plan_class)


async def main():
    """Main entry point for the executor service."""
    import os
    
    # Setup logging
    from agentic_common.logging_config import setup_logging
    setup_logging()
    
    # Get configuration from environment
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    
    # Create and run service
    service = ExecutorService(host=host, port=port)
    
    try:
        await service.start()
        await service.run()
        
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
        
    except Exception as e:
        logger.error("Service error", error=str(e))
        raise
        
    finally:
        await service.stop()


if __name__ == "__main__":
    asyncio.run(main()) 