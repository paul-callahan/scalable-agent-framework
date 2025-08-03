"""
Standalone main entry point for the agentic framework.

This module provides a single entry point for running all four services (DataPlane, 
ControlPlane, TaskExecutor, PlanExecutor) concurrently in a single process using 
an in-memory message broker, mirroring the Java microservices architecture.
"""

import asyncio
import signal
import sys
from typing import Optional

from .core.logging import configure_logging, get_logger
from .message_bus import InMemoryBroker
from .data_plane.service import DataPlaneService
from .control_plane.service import ControlPlaneService
from .executors.task_executor import TaskExecutorService
from .executors.plan_executor import PlanExecutorService


async def run_standalone(log_level: str = "INFO", 
                        db_path: str = "agentic_data.db", tenant_id: str = "default") -> None:
    """
    Run all four services (DataPlane, ControlPlane, TaskExecutor, PlanExecutor) concurrently.
    
    Args:
        log_level: Logging level
        db_path: Path to the SQLite database file
        tenant_id: Tenant identifier
    """
    # Configure logging
    configure_logging(log_level=log_level)
    logger = get_logger(__name__)
    
    # Create shared in-memory broker
    broker = InMemoryBroker()
    
    # Create shutdown event for graceful shutdown
    shutdown_event = asyncio.Event()
    
    # Create all four services
    data_plane_service = DataPlaneService(
        broker=broker,
        db_path=db_path
    )
    
    control_plane_service = ControlPlaneService(
        broker=broker
    )
    
    task_executor_service = TaskExecutorService(
        broker=broker
    )
    
    plan_executor_service = PlanExecutorService(
        broker=broker
    )
    
    # Add some default guardrails for demonstration
    control_plane_service.add_guardrail(tenant_id, {
        'type': 'rate_limit',
        'enabled': True,
        'blocking': True,
        'max_requests': 100,
        'window_seconds': 60
    })
    
    control_plane_service.add_guardrail(tenant_id, {
        'type': 'content_filter',
        'enabled': True,
        'blocking': True,
        'blocked_keywords': ['malicious', 'harmful']
    })
    
    # Register some default task and plan handlers for demonstration
    def mock_task_handler(parameters: dict) -> dict:
        """Mock task handler for demonstration."""
        return {
            "result": f"Mock task executed with parameters: {parameters}",
            "status": "completed",
            "metadata": {
                "handler": "mock",
                "timestamp": "2024-01-01T00:00:00Z"
            }
        }
    
    def mock_plan_handler(parameters: dict, input_task_id: str) -> dict:
        """Mock plan handler for demonstration."""
        return {
            "next_task_ids": [f"mock_task_{input_task_id}_next"],
            "metadata": {
                "handler": "mock",
                "input_task_id": input_task_id,
                "timestamp": "2024-01-01T00:00:00Z"
            },
            "confidence": 0.8
        }
    
    task_executor_service.register_task("mock_task", mock_task_handler)
    plan_executor_service.register_plan("mock_plan", mock_plan_handler)
    
    # Setup signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, initiating shutdown")
        shutdown_event.set()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Start all four services concurrently
        logger.info("Starting standalone agentic framework with all four services")
        
        # Start services
        await asyncio.gather(
            data_plane_service.start(tenant_id=tenant_id),
            control_plane_service.start(tenant_id=tenant_id),
            task_executor_service.start(tenant_id=tenant_id),
            plan_executor_service.start(tenant_id=tenant_id)
        )
        
        logger.info("Standalone agentic framework started successfully")
        logger.info("All services running: DataPlane, ControlPlane, TaskExecutor, PlanExecutor")
        
        # Keep the services running until shutdown is requested
        while not shutdown_event.is_set():
            await asyncio.sleep(1)
            
    except Exception as e:
        logger.error(f"Error in standalone services: {e}")
        raise
    finally:
        # Stop all four services
        logger.info("Stopping standalone services")
        await asyncio.gather(
            data_plane_service.stop(),
            control_plane_service.stop(),
            task_executor_service.stop(),
            plan_executor_service.stop(),
            return_exceptions=True
        )
        await broker.shutdown()
        logger.info("Standalone agentic framework stopped")


def main():
    """Main entry point for the standalone agentic framework."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Standalone Agentic Framework")
    parser.add_argument("--log-level", default="INFO", help="Logging level")
    parser.add_argument("--db-path", default="agentic_data.db", help="Database file path")
    parser.add_argument("--tenant-id", default="default", help="Tenant identifier")
    
    args = parser.parse_args()
    
    try:
        asyncio.run(run_standalone(
            log_level=args.log_level,
            db_path=args.db_path,
            tenant_id=args.tenant_id
        ))
    except KeyboardInterrupt:
        print("\nShutdown requested by user")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 