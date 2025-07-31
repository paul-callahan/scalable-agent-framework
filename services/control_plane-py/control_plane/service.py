"""
Main control plane service orchestrator.

This module implements the main control plane service orchestrator that coordinates
Kafka consumer, guardrail evaluation, routing decisions, Kafka producer, and
FastAPI server with graceful shutdown handling.
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
from .api import create_control_plane_app
from .guardrails import GuardrailEngine
from .kafka_consumer import ControlPlaneConsumer
from .kafka_producer import ControlPlaneProducer
from .router import ExecutionRouter

logger = get_logger(__name__)


class ControlPlaneService:
    """
    Main control plane service orchestrator.
    
    Coordinates Kafka consumer, guardrail evaluation, routing decisions,
    Kafka producer, and FastAPI server with graceful shutdown handling.
    """
    
    def __init__(self, host: str = "0.0.0.0", port: int = 8000):
        """
        Initialize the control plane service.
        
        Args:
            host: Host to bind the server to
            port: Port to bind the server to
        """
        self.host = host
        self.port = port
        self.health_check = HealthCheck()
        self.consumer = ControlPlaneConsumer()
        self.producer = ControlPlaneProducer()
        self.guardrail_engine = GuardrailEngine()
        self.router = ExecutionRouter()
        self.app: Optional[FastAPI] = None
        self.server: Optional[Server] = None
        self.running = False
        
    async def start(self) -> None:
        """Start the control plane service."""
        try:
            logger.info("Starting control plane service")
            
            # Add health checks
            self.health_check.add_health_check(
                create_kafka_health_check(self.producer)
            )
            self.health_check.add_health_check(
                create_service_health_check("control-plane")
            )
            
            # Start Kafka components
            await self.producer.start()
            await self.consumer.start()
            
            # Set up message processor
            self.consumer.set_message_processor(self._process_execution_message)
            
            # Create FastAPI app
            self.app = create_control_plane_app(
                health_check=self.health_check,
                consumer=self.consumer,
                producer=self.producer,
                guardrail_engine=self.guardrail_engine,
                router=self.router,
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
            logger.info("Control plane service started", 
                       host=self.host,
                       port=self.port)
            
        except Exception as e:
            logger.error("Failed to start control plane service", error=str(e))
            await self.stop()
            raise
    
    async def stop(self) -> None:
        """Stop the control plane service."""
        logger.info("Stopping control plane service")
        self.running = False
        
        try:
            # Stop Kafka components
            await self.consumer.stop()
            await self.producer.stop()
            
            # Stop FastAPI server
            if self.server:
                self.server.should_exit = True
            
            logger.info("Control plane service stopped")
            
        except Exception as e:
            logger.error("Error stopping control plane service", error=str(e))
    
    async def run(self) -> None:
        """Run the control plane service."""
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
            logger.error("Control plane service error", error=str(e))
            raise
        
        finally:
            # Cancel consumer task
            if 'consumer_task' in locals():
                consumer_task.cancel()
                try:
                    await consumer_task
                except asyncio.CancelledError:
                    pass
    
    async def _process_execution_message(self, message_data: dict) -> None:
        """
        Process execution message from Kafka.
        
        Args:
            message_data: Message data from Kafka
        """
        try:
            execution_id = message_data.get("execution_id")
            tenant_id = message_data.get("tenant_id")
            execution_type = message_data.get("type")
            
            logger.info("Processing execution message", 
                       execution_id=execution_id,
                       tenant_id=tenant_id,
                       execution_type=execution_type)
            
            # Evaluate guardrails
            guardrail_result = self.guardrail_engine.evaluate_execution(message_data)
            
            if not guardrail_result.passed:
                logger.warning("Execution failed guardrail evaluation", 
                              execution_id=execution_id,
                              violations=[v.to_dict() for v in guardrail_result.violations])
                return
            
            # Route execution
            target_topics = self.router.route_execution(message_data, tenant_id)
            
            if not target_topics:
                logger.warning("No target topics found for execution", 
                              execution_id=execution_id,
                              execution_type=execution_type)
                return
            
            # Publish to target topics
            for topic in target_topics:
                await self.producer.publish_execution_result(tenant_id, message_data)
            
            logger.info("Execution processed successfully", 
                       execution_id=execution_id,
                       tenant_id=tenant_id,
                       target_topics=target_topics)
            
        except Exception as e:
            logger.error("Failed to process execution message", 
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
            
            # Check guardrail engine
            guardrail_healthy = len(self.guardrail_engine.get_policies()) > 0
            
            return producer_healthy and consumer_healthy and guardrail_healthy
            
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
            "guardrail_engine": {
                "policies_loaded": len(self.guardrail_engine.get_policies()) > 0,
            },
        }


async def main():
    """Main entry point for the control plane service."""
    import os
    
    # Setup logging
    from agentic_common.logging_config import setup_logging
    setup_logging()
    
    # Get configuration from environment
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    
    # Create and run service
    service = ControlPlaneService(host=host, port=port)
    
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