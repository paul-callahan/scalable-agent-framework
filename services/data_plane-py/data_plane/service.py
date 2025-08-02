"""
Main data plane service orchestrator.

This module implements the main data plane service orchestrator that coordinates
Kafka consumer, database operations, Kafka producer, and FastAPI server with
graceful shutdown handling and health check integration.
"""

import asyncio
import signal
from typing import Optional

from fastapi import FastAPI
from structlog import get_logger
from uvicorn import Config, Server

from agentic_common.health import (
    HealthCheck,
    create_database_health_check,
    create_kafka_health_check,
    create_service_health_check,
)
from .api import create_data_plane_app
from .database import get_database_manager
from .kafka_consumer import DataPlaneConsumer
from .kafka_producer import DataPlaneProducer

logger = get_logger(__name__)


class DataPlaneService:
    """
    Main data plane service orchestrator.
    
    Coordinates Kafka consumer, database operations, Kafka producer,
    and FastAPI server with graceful shutdown handling.
    """
    
    def __init__(self, host: str = "0.0.0.0", port: int = 8000):
        """
        Initialize the data plane service.
        
        Args:
            host: Host to bind the server to
            port: Port to bind the server to
        """
        self.host = host
        self.port = port
        self.health_check = HealthCheck()
        self.consumer = DataPlaneConsumer()
        self.producer = DataPlaneProducer()
        self.app: Optional[FastAPI] = None
        self.server: Optional[Server] = None
        self.running = False
        
    async def start(self) -> None:
        """Start the data plane service."""
        try:
            logger.info("Starting data plane service")
            
            # Initialize database
            db_mgr = await get_database_manager()
            await db_mgr.create_tables()
            
            # Add health checks
            self.health_check.add_health_check(
                create_database_health_check(db_mgr)
            )
            self.health_check.add_health_check(
                create_kafka_health_check(self.producer)
            )
            self.health_check.add_health_check(
                create_service_health_check("data-plane")
            )
            
            # Start Kafka components
            await self.producer.start()
            await self.consumer.start()
            
            # Create FastAPI app
            self.app = create_data_plane_app(
                health_check=self.health_check,
                consumer=self.consumer,
                producer=self.producer,
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
            logger.info("Data plane service started", 
                       host=self.host,
                       port=self.port)
            
        except Exception as e:
            logger.error("Failed to start data plane service", error=str(e))
            await self.stop()
            raise
    
    async def stop(self) -> None:
        """Stop the data plane service."""
        logger.info("Stopping data plane service")
        self.running = False
        
        try:
            # Stop Kafka components
            await self.consumer.stop()
            await self.producer.stop()
            
            # Stop FastAPI server
            if self.server:
                self.server.should_exit = True
            
            # Close database connections
            db_mgr = await get_database_manager()
            await db_mgr.close()
            
            logger.info("Data plane service stopped")
            
        except Exception as e:
            logger.error("Error stopping data plane service", error=str(e))
    
    async def run(self) -> None:
        """Run the data plane service."""
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
            logger.error("Data plane service error", error=str(e))
            raise
        
        finally:
            # Cancel consumer task
            if 'consumer_task' in locals():
                consumer_task.cancel()
                try:
                    await consumer_task
                except asyncio.CancelledError:
                    pass
    
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
            # Check database
            db_mgr = await get_database_manager()
            db_healthy = await db_mgr.health_check()
            
            # Check Kafka producer
            producer_healthy = await self.producer.health_check()
            
            # Check consumer
            consumer_healthy = self.consumer.running
            
            return db_healthy and producer_healthy and consumer_healthy
            
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
        }


async def main():
    """Main entry point for the data plane service."""
    import os
    
    # Setup logging
    from agentic_common.logging_config import setup_logging
    setup_logging()
    
    # Get configuration from environment
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    
    # Create and run service
    service = DataPlaneService(host=host, port=port)
    
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