"""
Health check and graceful shutdown utilities for the agentic framework.

This module provides health check endpoints and graceful shutdown handlers
for gRPC servers.
"""

import asyncio
import signal
import threading
import time
from contextlib import asynccontextmanager
from typing import Any, Callable, Dict, List, Optional

import grpc
from structlog.types import FilteringBoundLogger

from .logging import get_logger


class HealthCheckService:
    """
    Health check service for gRPC servers.
    
    Provides health check endpoints and graceful shutdown capabilities.
    """
    
    def __init__(self, logger: Optional[FilteringBoundLogger] = None):
        """
        Initialize the health check service.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger or get_logger(__name__)
        self._shutdown_event = threading.Event()
        self._shutdown_handlers: List[Callable[[], None]] = []
        self._health_status = "healthy"
        self._start_time = time.time()
        self._metrics: Dict[str, Any] = {}
        
        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def add_shutdown_handler(self, handler: Callable[[], None]) -> None:
        """
        Add a shutdown handler to be called during graceful shutdown.
        
        Args:
            handler: Function to call during shutdown
        """
        self._shutdown_handlers.append(handler)
        self.logger.info("Shutdown handler added", handler_name=handler.__name__)
    
    def set_health_status(self, status: str) -> None:
        """
        Set the health status of the service.
        
        Args:
            status: Health status ("healthy", "unhealthy", "degraded")
        """
        self._health_status = status
        self.logger.info("Health status updated", status=status)
    
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
        return {
            "status": self._health_status,
            "uptime_seconds": round(uptime, 2),
            "metrics": self._metrics.copy(),
            "timestamp": time.time(),
        }
    
    def is_shutdown_requested(self) -> bool:
        """
        Check if shutdown has been requested.
        
        Returns:
            True if shutdown is requested
        """
        return self._shutdown_event.is_set()
    
    def request_shutdown(self) -> None:
        """
        Request graceful shutdown of the service.
        """
        self.logger.info("Shutdown requested")
        self._shutdown_event.set()
    
    def _signal_handler(self, signum: int, frame) -> None:
        """
        Handle shutdown signals.
        
        Args:
            signum: Signal number
            frame: Current stack frame
        """
        signal_name = signal.Signals(signum).name
        self.logger.info("Received shutdown signal", signal=signal_name)
        self.request_shutdown()
    
    async def graceful_shutdown(self, server: grpc.Server, timeout: float = 30.0) -> None:
        """
        Perform graceful shutdown of the gRPC server.
        
        Args:
            server: gRPC server instance
            timeout: Shutdown timeout in seconds
        """
        self.logger.info("Starting graceful shutdown", timeout=timeout)
        
        # Set health status to shutting down
        self.set_health_status("shutting_down")
        
        # Call shutdown handlers
        for handler in self._shutdown_handlers:
            try:
                handler()
                self.logger.info("Shutdown handler completed", handler_name=handler.__name__)
            except Exception as e:
                self.logger.error("Shutdown handler failed", 
                                handler_name=handler.__name__, 
                                error=str(e))
        
        # Stop accepting new requests
        self.logger.info("Stopping server from accepting new requests")
        server.stop(grace=timeout)
        
        # Wait for server to stop
        try:
            await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(None, server.wait_for_termination),
                timeout=timeout
            )
            self.logger.info("Server stopped successfully")
        except asyncio.TimeoutError:
            self.logger.warning("Server shutdown timed out, forcing termination")
            server.stop(grace=0)
        
        self.set_health_status("stopped")
        self.logger.info("Graceful shutdown completed")


class HealthCheckServicer:
    """
    gRPC health check servicer implementation.
    
    Provides health check endpoints for monitoring.
    """
    
    def __init__(self, health_service: HealthCheckService):
        """
        Initialize the health check servicer.
        
        Args:
            health_service: Health check service instance
        """
        self.health_service = health_service
        self.logger = get_logger(__name__)
    
    def Check(self, request, context):
        """
        Health check endpoint.
        
        Args:
            request: Health check request
            context: gRPC context
            
        Returns:
            Health check response
        """
        try:
            health_info = self.health_service.get_health_info()
            
            # Create a simple health response
            # In a real implementation, you'd use the proper health check protobuf
            response = {
                "status": health_info["status"],
                "uptime_seconds": health_info["uptime_seconds"],
                "timestamp": health_info["timestamp"],
            }
            
            self.logger.debug("Health check requested", 
                            status=health_info["status"],
                            uptime=health_info["uptime_seconds"])
            
            return response
            
        except Exception as e:
            self.logger.error("Health check failed", error=str(e))
            context.abort(grpc.StatusCode.INTERNAL, "Health check failed")
    
    def Watch(self, request, context):
        """
        Health check watch endpoint for streaming health updates.
        
        Args:
            request: Health check request
            context: gRPC context
            
        Yields:
            Health check responses
        """
        try:
            while not self.health_service.is_shutdown_requested():
                health_info = self.health_service.get_health_info()
                
                response = {
                    "status": health_info["status"],
                    "uptime_seconds": health_info["uptime_seconds"],
                    "timestamp": health_info["timestamp"],
                }
                
                yield response
                
                # Wait before next health check
                import time
                time.sleep(5)
                
        except Exception as e:
            self.logger.error("Health check watch failed", error=str(e))
            context.abort(grpc.StatusCode.INTERNAL, "Health check watch failed")


@asynccontextmanager
async def managed_server(
    server: grpc.Server,
    health_service: HealthCheckService,
    port: int,
    logger: Optional[FilteringBoundLogger] = None,
):
    """
    Context manager for managing a gRPC server with health checks and graceful shutdown.
    
    Args:
        server: gRPC server instance
        health_service: Health check service instance
        port: Port to bind the server to
        logger: Optional logger instance
        
    Yields:
        Tuple of (server, health_service)
    """
    log = logger or get_logger(__name__)
    
    try:
        # Start the server
        server.add_insecure_port(f'[::]:{port}')
        server.start()
        log.info("Server started", port=port)
        
        yield server, health_service
        
    except Exception as e:
        log.error("Failed to start server", port=port, error=str(e))
        raise
        
    finally:
        # Graceful shutdown
        await health_service.graceful_shutdown(server) 