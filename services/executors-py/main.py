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

from executors.service import ExecutorService, ExecutorMode


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

    # Unified executor variables used for both plan and task modes
    executor_name = get_required_env_var("EXECUTOR_NAME")
    executor_path = get_required_env_var("EXECUTOR_PATH")
    executor_timeout = int(get_optional_env_var("EXECUTOR_TIMEOUT", "300"))  # 5 minutes default
    
    # Kafka configuration
    kafka_bootstrap_servers = get_optional_env_var("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    agent_graph_id = get_required_env_var("AGENT_GRAPH_ID")
    # Group id is derived; no env override
    kafka_group_id = f"{agent_graph_id}-{executor_name}"
    
    # Runtime selection: EXECUTOR_MODE=plan|task
    executor_mode_str = get_required_env_var("EXECUTOR_MODE").strip().lower()
    if executor_mode_str not in ("plan", "task"):
        print("Error: EXECUTOR_MODE must be 'plan' or 'task'", file=sys.stderr)
        sys.exit(1)
    exec_mode = ExecutorMode.PLAN if executor_mode_str == "plan" else ExecutorMode.TASK

    logger.info(
        "Configuration loaded",
        mode=exec_mode,
        tenant_id=tenant_id,
        executor_name=executor_name,
        executor_path=executor_path,
        executor_timeout=executor_timeout,
        kafka_bootstrap_servers=kafka_bootstrap_servers,
        kafka_group_id=kafka_group_id,
    )

    service = ExecutorService(
        tenant_id=tenant_id,
        mode=exec_mode,
        executor_name=executor_name,
        executor_path=executor_path,
        executor_timeout=executor_timeout,
        kafka_bootstrap_servers=kafka_bootstrap_servers,
        kafka_group_id=kafka_group_id,
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