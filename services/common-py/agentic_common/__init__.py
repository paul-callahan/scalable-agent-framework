"""
Common utilities for agentic microservices.

This package provides shared functionality used across all microservices including:
- Protobuf message imports
- Kafka topic naming utilities
- Logging configuration
- FastAPI health check utilities
"""

from .kafka_utils import (
    get_plan_control_topic,
    get_plan_execution_topic,
    get_plan_results_topic,
    get_task_control_topic,
    get_task_execution_topic,
    get_task_results_topic,
)
from .health import create_health_router
from .logging_config import setup_logging

__all__ = [
    # Kafka utilities
    "get_task_execution_topic",
    "get_task_results_topic",
    "get_plan_execution_topic",
    "get_plan_results_topic",
    "get_task_control_topic",
    "get_plan_control_topic",
    # Health check utilities
    "create_health_router",
    # Logging utilities
    "setup_logging",
]

__version__ = "0.1.0" 