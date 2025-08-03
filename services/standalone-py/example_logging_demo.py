#!/usr/bin/env python3
"""
Example script demonstrating structured logging and graceful shutdown.

This script shows how to use the logging features in the agentic framework.
"""

import asyncio
import time
from typing import Optional

from agentic.core.logging import configure_logging, get_logger, log_request_response, log_metric, log_error


async def demo_logging():
    """Demonstrate structured logging functionality."""
    print("=== Structured Logging Demo ===")
    
    # Configure logging
    configure_logging(log_level="INFO", log_format="console")
    logger = get_logger(__name__)
    
    # Log some basic messages
    logger.info("Starting logging demo", service="agentic-framework")
    
    # Demonstrate request/response logging
    with log_request_response(
        logger,
        "demo_request",
        request_id="req-123",
        tenant_id="tenant-456",
        operation="test"
    ):
        # Simulate some work
        await asyncio.sleep(0.1)
        logger.info("Processing request", step="validation")
        await asyncio.sleep(0.1)
        logger.info("Processing request", step="execution")
        await asyncio.sleep(0.1)
    
    # Demonstrate error logging
    try:
        raise ValueError("This is a demo error")
    except Exception as e:
        log_error(logger, e, 
                 request_id="req-123",
                 tenant_id="tenant-456",
                 context={"operation": "demo"})
    
    # Demonstrate metrics logging
    log_metric(logger, "requests_per_second", 100.5, unit="req/s")
    log_metric(logger, "memory_usage", 512.0, unit="MB", tags={"component": "demo"})
    
    logger.info("Logging demo completed")


async def demo_graceful_shutdown():
    """Demonstrate graceful shutdown functionality."""
    print("\n=== Graceful Shutdown Demo ===")
    
    # Configure logging
    configure_logging(log_level="INFO", log_format="console")
    logger = get_logger(__name__)
    
    # Create shutdown event
    shutdown_event = asyncio.Event()
    
    # Simulate running service
    logger.info("Service is running...")
    
    # Simulate shutdown request after 2 seconds
    async def trigger_shutdown():
        await asyncio.sleep(2)
        logger.info("Triggering graceful shutdown")
        shutdown_event.set()
    
    # Run the shutdown trigger
    asyncio.create_task(trigger_shutdown())
    
    # Main service loop
    start_time = time.time()
    while not shutdown_event.is_set():
        uptime = time.time() - start_time
        logger.info("Service heartbeat", uptime=round(uptime, 2))
        await asyncio.sleep(0.5)
    
    logger.info("Graceful shutdown demo completed")


async def main():
    """Run all demos."""
    print("Agentic Framework - Logging Demo")
    print("=" * 50)
    
    # Run demos
    await demo_logging()
    await demo_graceful_shutdown()
    
    print("\nDemo completed!")


if __name__ == "__main__":
    asyncio.run(main()) 