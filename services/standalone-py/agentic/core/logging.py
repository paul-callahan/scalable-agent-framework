"""
Shared logging configuration for the agentic framework.

This module provides structured logging using structlog with request/response
logging, error tracking, and basic metrics.
"""

import logging
import sys
import time
from contextlib import contextmanager
from typing import Any, Dict, Optional

import structlog
from structlog.types import FilteringBoundLogger


def configure_logging(
    log_level: str = "INFO",
    log_format: str = "json",
    include_timestamp: bool = True,
    include_process_id: bool = True,
    include_thread_id: bool = True,
) -> None:
    """
    Configure structured logging for the application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Output format ("json" or "console")
        include_timestamp: Whether to include timestamps
        include_process_id: Whether to include process ID
        include_thread_id: Whether to include thread ID
    """
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
    logger.info("Request started", 
                method=method_name,
                request_id=request_id,
                tenant_id=tenant_id,
                **kwargs)
    
    try:
        yield
        duration = time.time() - start_time
        logger.info("Request completed", 
                    method=method_name,
                    request_id=request_id,
                    tenant_id=tenant_id,
                    duration_ms=round(duration * 1000, 2),
                    status="success")
        
    except Exception as e:
        duration = time.time() - start_time
        logger.error("Request failed", 
                    method=method_name,
                    request_id=request_id,
                    tenant_id=tenant_id,
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
) -> None:
    """
    Log a metric for monitoring.
    
    Args:
        logger: Logger instance
        metric_name: Name of the metric
        value: Metric value
        unit: Optional unit (e.g., "ms", "bytes", "count")
        tags: Optional tags for the metric
    """
    logger.info("Metric recorded", 
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
    logger.error("Error occurred", 
                error_type=type(error).__name__,
                error_message=str(error),
                request_id=request_id,
                tenant_id=tenant_id,
                **(context or {}),
                exc_info=True) 