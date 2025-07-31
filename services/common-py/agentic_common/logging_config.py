"""
Structured logging configuration for agentic microservices.

This module provides structured logging using structlog==24.1.0 with
JSON formatting for production, human-readable formatting for development,
correlation ID support, and tenant ID context.
"""

import logging
import os
import sys
import time
from contextlib import contextmanager
from typing import Any, Dict, Optional

import structlog
from structlog.types import FilteringBoundLogger


def setup_logging(
    log_level: Optional[str] = None,
    log_format: Optional[str] = None,
    include_timestamp: bool = True,
    include_process_id: bool = True,
    include_thread_id: bool = True,
) -> None:
    """
    Setup structured logging for microservices.
    
    Args:
        log_level: Logging level (defaults to LOG_LEVEL env var or "INFO")
        log_format: Output format (defaults to LOG_FORMAT env var or "json")
        include_timestamp: Whether to include timestamps
        include_process_id: Whether to include process ID
        include_thread_id: Whether to include thread ID
    """
    # Get configuration from environment variables
    if log_level is None:
        log_level = os.getenv("LOG_LEVEL", "INFO")
    
    if log_format is None:
        log_format = os.getenv("LOG_FORMAT", "json")
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )
    
    # Configure structlog processors
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
    ]
    
    if include_timestamp:
        processors.append(structlog.processors.TimeStamper(fmt="iso"))
    
    if include_process_id:
        processors.append(structlog.stdlib.add_log_level_number)
    
    if include_thread_id:
        processors.append(structlog.processors.CallsiteParameterAdder(
            [structlog.processors.CallsiteParameter.FILENAME,
             structlog.processors.CallsiteParameter.FUNC_NAME,
             structlog.processors.CallsiteParameter.LINENO]
        ))
    
    # Add correlation ID and tenant ID support
    processors.append(structlog.processors.CallsiteParameterAdder(
        [structlog.processors.CallsiteParameter.FILENAME,
         structlog.processors.CallsiteParameter.FUNC_NAME,
         structlog.processors.CallsiteParameter.LINENO]
    ))
    
    # Add exception info for errors
    processors.extend([
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ])
    
    # Add final formatting
    if log_format == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())
    
    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> FilteringBoundLogger:
    """
    Get a structured logger instance.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Configured structlog logger
    """
    return structlog.get_logger(name)


def bind_logger(
    logger: FilteringBoundLogger,
    correlation_id: Optional[str] = None,
    tenant_id: Optional[str] = None,
    service_name: Optional[str] = None,
    **kwargs: Any,
) -> FilteringBoundLogger:
    """
    Bind additional context to a logger.
    
    Args:
        logger: Logger instance
        correlation_id: Optional correlation ID for request tracing
        tenant_id: Optional tenant ID
        service_name: Optional service name
        **kwargs: Additional context to bind
        
    Returns:
        Logger with bound context
    """
    bound_logger = logger
    
    if correlation_id:
        bound_logger = bound_logger.bind(correlation_id=correlation_id)
    
    if tenant_id:
        bound_logger = bound_logger.bind(tenant_id=tenant_id)
    
    if service_name:
        bound_logger = bound_logger.bind(service_name=service_name)
    
    for key, value in kwargs.items():
        bound_logger = bound_logger.bind(**{key: value})
    
    return bound_logger


@contextmanager
def log_request_response(
    logger: FilteringBoundLogger,
    method_name: str,
    request_id: Optional[str] = None,
    tenant_id: Optional[str] = None,
    **kwargs: Any,
):
    """
    Context manager for logging request/response with timing and metrics.
    
    Args:
        logger: Logger instance
        method_name: Name of the method being called
        request_id: Optional request ID for correlation
        tenant_id: Optional tenant ID
        **kwargs: Additional context to log
    """
    start_time = time.time()
    bound_logger = bind_logger(logger, correlation_id=request_id, tenant_id=tenant_id)
    
    bound_logger.info("Request started", 
                      method=method_name,
                      **kwargs)
    
    try:
        yield
        duration = time.time() - start_time
        bound_logger.info("Request completed", 
                          method=method_name,
                          duration_ms=round(duration * 1000, 2),
                          status="success")
        
    except Exception as e:
        duration = time.time() - start_time
        bound_logger.error("Request failed", 
                          method=method_name,
                          duration_ms=round(duration * 1000, 2),
                          status="error",
                          error_type=type(e).__name__,
                          error_message=str(e))
        raise


def log_metric(
    logger: FilteringBoundLogger,
    metric_name: str,
    value: float,
    unit: Optional[str] = None,
    tags: Optional[Dict[str, str]] = None,
    tenant_id: Optional[str] = None,
) -> None:
    """
    Log a metric for monitoring.
    
    Args:
        logger: Logger instance
        metric_name: Name of the metric
        value: Metric value
        unit: Optional unit (e.g., "ms", "bytes", "count")
        tags: Optional tags for the metric
        tenant_id: Optional tenant ID
    """
    bound_logger = bind_logger(logger, tenant_id=tenant_id)
    bound_logger.info("Metric recorded", 
                      metric_name=metric_name,
                      value=value,
                      unit=unit,
                      **(tags or {}))


def log_error(
    logger: FilteringBoundLogger,
    error: Exception,
    context: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None,
    tenant_id: Optional[str] = None,
) -> None:
    """
    Log an error with structured context.
    
    Args:
        logger: Logger instance
        error: The exception that occurred
        context: Optional additional context
        request_id: Optional request ID for correlation
        tenant_id: Optional tenant ID
    """
    bound_logger = bind_logger(logger, correlation_id=request_id, tenant_id=tenant_id)
    bound_logger.error("Error occurred", 
                       error_type=type(error).__name__,
                       error_message=str(error),
                       **(context or {}),
                       exc_info=True)


def log_kafka_message(
    logger: FilteringBoundLogger,
    topic: str,
    partition: int,
    offset: int,
    message_size: int,
    tenant_id: Optional[str] = None,
    **kwargs: Any,
) -> None:
    """
    Log Kafka message processing.
    
    Args:
        logger: Logger instance
        topic: Kafka topic name
        partition: Kafka partition
        offset: Message offset
        message_size: Size of the message in bytes
        tenant_id: Optional tenant ID
        **kwargs: Additional context
    """
    bound_logger = bind_logger(logger, tenant_id=tenant_id)
    bound_logger.info("Kafka message processed",
                      topic=topic,
                      partition=partition,
                      offset=offset,
                      message_size=message_size,
                      **kwargs)


def log_database_operation(
    logger: FilteringBoundLogger,
    operation: str,
    table: str,
    duration_ms: float,
    tenant_id: Optional[str] = None,
    **kwargs: Any,
) -> None:
    """
    Log database operation.
    
    Args:
        logger: Logger instance
        operation: Database operation (SELECT, INSERT, UPDATE, DELETE)
        table: Database table name
        duration_ms: Operation duration in milliseconds
        tenant_id: Optional tenant ID
        **kwargs: Additional context
    """
    bound_logger = bind_logger(logger, tenant_id=tenant_id)
    bound_logger.info("Database operation completed",
                      operation=operation,
                      table=table,
                      duration_ms=duration_ms,
                      **kwargs) 