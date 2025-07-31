"""
FastAPI health check utilities for agentic microservices.

This module provides FastAPI health check endpoints following Kubernetes
health check patterns and return proper HTTP status codes with JSON responses.
"""

import asyncio
import time
from typing import Any, Callable, Dict, List, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from structlog import get_logger

logger = get_logger(__name__)


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    uptime_seconds: float
    timestamp: float
    details: Optional[Dict[str, Any]] = None


class HealthCheck:
    """
    Health check service for FastAPI applications.
    
    Provides health check endpoints and graceful shutdown capabilities.
    """
    
    def __init__(self):
        """Initialize the health check service."""
        self._start_time = time.time()
        self._health_status = "healthy"
        self._readiness_status = "ready"
        self._metrics: Dict[str, Any] = {}
        self._health_checks: List[Callable[[], bool]] = []
        self._readiness_checks: List[Callable[[], bool]] = []
        
    def set_health_status(self, status: str) -> None:
        """
        Set the health status of the service.
        
        Args:
            status: Health status ("healthy", "unhealthy", "degraded")
        """
        self._health_status = status
        logger.info("Health status updated", status=status)
    
    def set_readiness_status(self, status: str) -> None:
        """
        Set the readiness status of the service.
        
        Args:
            status: Readiness status ("ready", "not_ready")
        """
        self._readiness_status = status
        logger.info("Readiness status updated", status=status)
    
    def add_health_check(self, check: Callable[[], bool]) -> None:
        """
        Add a health check function.
        
        Args:
            check: Function that returns True if healthy, False otherwise
        """
        self._health_checks.append(check)
    
    def add_readiness_check(self, check: Callable[[], bool]) -> None:
        """
        Add a readiness check function.
        
        Args:
            check: Function that returns True if ready, False otherwise
        """
        self._readiness_checks.append(check)
    
    def update_metric(self, name: str, value: Any) -> None:
        """
        Update a metric value.
        
        Args:
            name: Metric name
            value: Metric value
        """
        self._metrics[name] = value
    
    def get_health_info(self) -> Dict[str, Any]:
        """
        Get current health information.
        
        Returns:
            Dictionary with health status and metrics
        """
        uptime = time.time() - self._start_time
        
        # Run health checks
        health_details = {}
        all_healthy = True
        
        for check in self._health_checks:
            try:
                is_healthy = check()
                health_details[check.__name__] = "healthy" if is_healthy else "unhealthy"
                if not is_healthy:
                    all_healthy = False
            except Exception as e:
                health_details[check.__name__] = f"error: {str(e)}"
                all_healthy = False
        
        # Update overall health status
        if not all_healthy:
            self._health_status = "unhealthy"
        
        return {
            "status": self._health_status,
            "uptime_seconds": round(uptime, 2),
            "metrics": self._metrics.copy(),
            "timestamp": time.time(),
            "details": health_details,
        }
    
    def get_readiness_info(self) -> Dict[str, Any]:
        """
        Get current readiness information.
        
        Returns:
            Dictionary with readiness status and details
        """
        uptime = time.time() - self._start_time
        
        # Run readiness checks
        readiness_details = {}
        all_ready = True
        
        for check in self._readiness_checks:
            try:
                is_ready = check()
                readiness_details[check.__name__] = "ready" if is_ready else "not_ready"
                if not is_ready:
                    all_ready = False
            except Exception as e:
                readiness_details[check.__name__] = f"error: {str(e)}"
                all_ready = False
        
        # Update overall readiness status
        if not all_ready:
            self._readiness_status = "not_ready"
        
        return {
            "status": self._readiness_status,
            "uptime_seconds": round(uptime, 2),
            "timestamp": time.time(),
            "details": readiness_details,
        }


def create_health_router(health_check: HealthCheck) -> APIRouter:
    """
    Create a FastAPI router with health check endpoints.
    
    Args:
        health_check: HealthCheck instance
        
    Returns:
        FastAPI router with health endpoints
    """
    router = APIRouter(prefix="/health", tags=["health"])
    
    @router.get("/live", response_model=HealthResponse)
    async def liveness_probe():
        """
        Liveness probe endpoint.
        
        Returns 200 if the service is alive, 503 if not.
        """
        health_info = health_check.get_health_info()
        
        if health_info["status"] == "healthy":
            return HealthResponse(**health_info)
        else:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service is unhealthy"
            )
    
    @router.get("/ready", response_model=HealthResponse)
    async def readiness_probe():
        """
        Readiness probe endpoint.
        
        Returns 200 if the service is ready to receive traffic, 503 if not.
        """
        readiness_info = health_check.get_readiness_info()
        
        if readiness_info["status"] == "ready":
            return HealthResponse(**readiness_info)
        else:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service is not ready"
            )
    
    @router.get("/metrics")
    async def metrics():
        """
        Metrics endpoint.
        
        Returns current service metrics.
        """
        health_info = health_check.get_health_info()
        return {
            "metrics": health_info["metrics"],
            "uptime_seconds": health_info["uptime_seconds"],
            "timestamp": health_info["timestamp"],
        }
    
    return router


# Common health check functions
def create_database_health_check(db_session_factory) -> Callable[[], bool]:
    """
    Create a database health check function.
    
    Args:
        db_session_factory: Database session factory
        
    Returns:
        Health check function
    """
    def check_database() -> bool:
        try:
            # Try to execute a simple query
            session = db_session_factory()
            session.execute("SELECT 1")
            session.close()
            return True
        except Exception as e:
            logger.error("Database health check failed", error=str(e))
            return False
    
    return check_database


def create_kafka_health_check(producer) -> Callable[[], bool]:
    """
    Create a Kafka health check function.
    
    Args:
        producer: Kafka producer instance
        
    Returns:
        Health check function
    """
    def check_kafka() -> bool:
        try:
            # Check if producer is connected
            return producer._sender._sender_task and not producer._sender._sender_task.done()
        except Exception as e:
            logger.error("Kafka health check failed", error=str(e))
            return False
    
    return check_kafka


def create_service_health_check(service_name: str) -> Callable[[], bool]:
    """
    Create a basic service health check function.
    
    Args:
        service_name: Name of the service
        
    Returns:
        Health check function
    """
    def check_service() -> bool:
        try:
            # Basic service check - can be extended with service-specific logic
            return True
        except Exception as e:
            logger.error(f"{service_name} health check failed", error=str(e))
            return False
    
    return check_service 