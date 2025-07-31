#!/usr/bin/env python3
"""
Example script demonstrating structured logging, health checks, and graceful shutdown.

This script shows how to use the logging and health check features in the agentic framework.
"""

import asyncio
import time
from typing import Optional

from agentic.core.logging import configure_logging, get_logger, log_request_response, log_metric, log_error
from agentic.core.health import HealthCheckService


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


async def demo_health_checks():
    """Demonstrate health check functionality."""
    print("\n=== Health Check Demo ===")
    
    # Configure logging
    configure_logging(log_level="INFO", log_format="console")
    logger = get_logger(__name__)
    
    # Create health service
    health_service = HealthCheckService(logger)
    
    # Add some metrics
    health_service.update_metric("total_requests", 100)
    health_service.update_metric("error_rate", 0.05)
    health_service.update_metric("response_time_ms", 150.5)
    
    # Get health info
    health_info = health_service.get_health_info()
    print(f"Health Status: {health_info['status']}")
    print(f"Uptime: {health_info['uptime_seconds']} seconds")
    print(f"Metrics: {health_info['metrics']}")
    
    # Simulate some activity
    for i in range(3):
        health_service.update_metric("total_requests", 100 + i * 10)
        health_service.update_metric("response_time_ms", 150.5 + i * 5)
        
        health_info = health_service.get_health_info()
        print(f"Updated metrics: {health_info['metrics']}")
        
        await asyncio.sleep(1)
    
    # Change health status
    health_service.set_health_status("degraded")
    health_info = health_service.get_health_info()
    print(f"Health Status (degraded): {health_info['status']}")
    
    logger.info("Health check demo completed")


async def demo_graceful_shutdown():
    """Demonstrate graceful shutdown functionality."""
    print("\n=== Graceful Shutdown Demo ===")
    
    # Configure logging
    configure_logging(log_level="INFO", log_format="console")
    logger = get_logger(__name__)
    
    # Create health service
    health_service = HealthCheckService(logger)
    
    # Add shutdown handlers
    def cleanup_database():
        logger.info("Cleaning up database connections")
        time.sleep(0.1)  # Simulate cleanup work
    
    def cleanup_cache():
        logger.info("Cleaning up cache")
        time.sleep(0.1)  # Simulate cleanup work
    
    health_service.add_shutdown_handler(cleanup_database)
    health_service.add_shutdown_handler(cleanup_cache)
    
    # Simulate running service
    logger.info("Service is running...")
    
    # Simulate shutdown request after 2 seconds
    async def trigger_shutdown():
        await asyncio.sleep(2)
        logger.info("Triggering graceful shutdown")
        health_service.request_shutdown()
    
    # Run the shutdown trigger
    asyncio.create_task(trigger_shutdown())
    
    # Main service loop
    while not health_service.is_shutdown_requested():
        logger.info("Service heartbeat", uptime=health_service.get_health_info()["uptime_seconds"])
        await asyncio.sleep(0.5)
    
    logger.info("Graceful shutdown demo completed")


async def main():
    """Run all demos."""
    print("Agentic Framework - Logging and Health Check Demo")
    print("=" * 50)
    
    # Run demos
    await demo_logging()
    await demo_health_checks()
    await demo_graceful_shutdown()
    
    print("\nDemo completed!")


if __name__ == "__main__":
    asyncio.run(main()) 