#!/usr/bin/env python3
"""
Main entry point for the executors-py microservice.
A pure Kafka consumer/producer service for plan execution.
"""

import asyncio
import os
import sys
from typing import Optional

import structlog

from executors.service import PlanExecutorService


def setup_logging() -> None:
    """Configure structured logging."""
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_required_env_var(name: str) -> str:
    """Get a required environment variable or exit with error."""
    value = os.getenv(name)
    if not value:
        print(f"Error: Required environment variable {name} is not set", file=sys.stderr)
        sys.exit(1)
    return value


def get_optional_env_var(name: str, default: str) -> str:
    """Get an optional environment variable with default."""
    return os.getenv(name, default)


async def main() -> None:
    """Main async function to run the executors service."""
    setup_logging()
    logger = structlog.get_logger(__name__)
    
    logger.info("Starting executors-py microservice")
    
    # Load configuration from environment variables
    tenant_id = get_required_env_var("TENANT_ID")
    plan_name = get_required_env_var("PLAN_NAME")
    plan_path = get_required_env_var("PLAN_PATH")
    plan_timeout = int(get_optional_env_var("PLAN_TIMEOUT", "300"))  # 5 minutes default
    
    # Kafka configuration
    kafka_bootstrap_servers = get_optional_env_var("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    kafka_group_id = get_optional_env_var("KAFKA_GROUP_ID", f"executors-{tenant_id}")
    
    logger.info(
        "Configuration loaded",
        tenant_id=tenant_id,
        plan_name=plan_name,
        plan_path=plan_path,
        plan_timeout=plan_timeout,
        kafka_bootstrap_servers=kafka_bootstrap_servers,
        kafka_group_id=kafka_group_id
    )
    
    # Create and start the service
    service = PlanExecutorService(
        tenant_id=tenant_id,
        plan_name=plan_name,
        plan_path=plan_path,
        plan_timeout=plan_timeout,
        kafka_bootstrap_servers=kafka_bootstrap_servers,
        kafka_group_id=kafka_group_id
    )
    
    try:
        await service.start()
        logger.info("Executors service started successfully")
        
        # Keep the service running
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    except Exception as e:
        logger.error("Service error", error=str(e), exc_info=True)
    finally:
        await service.stop()
        logger.info("Executors service stopped")


if __name__ == "__main__":
    asyncio.run(main()) 