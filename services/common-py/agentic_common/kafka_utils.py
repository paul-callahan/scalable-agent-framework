"""
Kafka utilities for agentic microservices.

This module provides Kafka topic naming functions and producer/consumer
factory functions with common configuration using aiokafka==0.11.0.
"""

import os
from typing import Optional

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from aiokafka.errors import KafkaError


def get_task_execution_topic(tenant_id: str) -> str:
    """Get the task execution topic name for a tenant."""
    return f"task-executions_{tenant_id}"


def get_task_results_topic(tenant_id: str) -> str:
    """Get the task results topic name for a tenant."""
    return f"task-results_{tenant_id}"


def get_plan_execution_topic(tenant_id: str) -> str:
    """Get the plan execution topic name for a tenant."""
    return f"tenant_tenant_plan-executions_{tenant_id}"


def get_plan_results_topic(tenant_id: str) -> str:
    """Get the plan results topic name for a tenant."""
    return f"tenant_tenant_plan-results_{tenant_id}"


def get_persisted_task_executions_topic(tenant_id: str) -> str:
    """Get the persisted task executions topic name for a tenant."""
    return f"persisted-task-executions_{tenant_id}"


def get_plan_control_topic(tenant_id: str) -> str:
    """Get the plan control topic name for a tenant."""
    return f"tenant_tenant_plan-control_{tenant_id}"


async def create_kafka_producer(
    bootstrap_servers: Optional[str] = None,
    client_id: Optional[str] = None,
    **kwargs
) -> AIOKafkaProducer:
    """
    Create a Kafka producer with common configuration.
    
    Args:
        bootstrap_servers: Kafka bootstrap servers (defaults to KAFKA_BOOTSTRAP_SERVERS env var)
        client_id: Client ID for the producer (defaults to KAFKA_CLIENT_ID env var)
        **kwargs: Additional configuration options
        
    Returns:
        Configured AIOKafkaProducer instance
    """
    if bootstrap_servers is None:
        bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    
    if client_id is None:
        client_id = os.getenv("KAFKA_CLIENT_ID", "agentic-producer")
    
    config = {
        "bootstrap_servers": bootstrap_servers,
        "client_id": client_id,
        "acks": "all",  # Wait for all in-sync replicas
        "retries": 3,
        "retry_backoff_ms": 1000,
        "compression_type": "gzip",
        "max_request_size": 1048576,  # 1MB
        "request_timeout_ms": 30000,
        "delivery_timeout_ms": 120000,
        **kwargs
    }
    
    return AIOKafkaProducer(**config)


async def create_kafka_consumer(
    topics: list[str],
    group_id: Optional[str] = None,
    bootstrap_servers: Optional[str] = None,
    client_id: Optional[str] = None,
    **kwargs
) -> AIOKafkaConsumer:
    """
    Create a Kafka consumer with common configuration.
    
    Args:
        topics: List of topics to subscribe to
        group_id: Consumer group ID (defaults to KAFKA_GROUP_ID env var)
        bootstrap_servers: Kafka bootstrap servers (defaults to KAFKA_BOOTSTRAP_SERVERS env var)
        client_id: Client ID for the consumer (defaults to KAFKA_CLIENT_ID env var)
        **kwargs: Additional configuration options
        
    Returns:
        Configured AIOKafkaConsumer instance
    """
    if bootstrap_servers is None:
        bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    
    if client_id is None:
        client_id = os.getenv("KAFKA_CLIENT_ID", "agentic-consumer")
    
    if group_id is None:
        group_id = os.getenv("KAFKA_GROUP_ID", "agentic-group")
    
    config = {
        "bootstrap_servers": bootstrap_servers,
        "client_id": client_id,
        "group_id": group_id,
        "auto_offset_reset": "earliest",
        "enable_auto_commit": False,  # Manual commit for better control
        "max_poll_records": 100,
        "max_poll_interval_ms": 300000,  # 5 minutes
        "session_timeout_ms": 30000,
        "heartbeat_interval_ms": 3000,
        "request_timeout_ms": 30000,
        "fetch_max_wait_ms": 500,
        "fetch_min_bytes": 1,
        "fetch_max_bytes": 52428800,  # 50MB
        **kwargs
    }
    
    consumer = AIOKafkaConsumer(*topics, **config)
    return consumer


def get_kafka_config() -> dict:
    """
    Get common Kafka configuration from environment variables.
    
    Returns:
        Dictionary with Kafka configuration
    """
    return {
        "bootstrap_servers": os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
        "client_id": os.getenv("KAFKA_CLIENT_ID", "agentic"),
        "group_id": os.getenv("KAFKA_GROUP_ID", "agentic-group"),
    }


class KafkaError(Exception):
    """Custom exception for Kafka-related errors."""
    pass 