"""
HTTP health check server for the agentic framework.

This module provides HTTP endpoints for health checks and metrics
that can be used alongside the gRPC services.
"""

import asyncio
import json
import signal
import threading
from typing import Any, Dict, Optional

import aiohttp
from aiohttp import web
from structlog.types import FilteringBoundLogger

from .logging import get_logger


class HTTPHealthServer:
    """
    HTTP health check server.
    
    Provides HTTP endpoints for health checks and metrics.
    """
    
    def __init__(self, health_service, port: int = 8080, logger: Optional[FilteringBoundLogger] = None):
        """
        Initialize the HTTP health server.
        
        Args:
            health_service: Health check service instance
            port: Port to bind the HTTP server to
            logger: Optional logger instance
        """
        self.health_service = health_service
        self.port = port
        self.logger = logger or get_logger(__name__)
        self.app = web.Application()
        self._setup_routes()
        self._shutdown_event = threading.Event()
        
        # Register signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _setup_routes(self):
        """Setup HTTP routes."""
        self.app.router.add_get('/health', self._health_check)
        self.app.router.add_get('/health/ready', self._ready_check)
        self.app.router.add_get('/health/live', self._live_check)
        self.app.router.add_get('/metrics', self._metrics)
        self.app.router.add_get('/', self._root)
    
    def _signal_handler(self, signum: int, frame):
        """Handle shutdown signals."""
        signal_name = signal.Signals(signum).name
        self.logger.info("Received shutdown signal", signal=signal_name)
        self._shutdown_event.set()
    
    async def _health_check(self, request):
        """Health check endpoint."""
        try:
            health_info = self.health_service.get_health_info()
            
            if health_info["status"] == "healthy":
                status_code = 200
            elif health_info["status"] == "degraded":
                status_code = 200  # Still responding but with warnings
            else:
                status_code = 503  # Service unavailable
            
            return web.json_response(health_info, status=status_code)
            
        except Exception as e:
            self.logger.error("Health check failed", error=str(e))
            return web.json_response(
                {"error": "Health check failed", "status": "unhealthy"},
                status=503
            )
    
    async def _ready_check(self, request):
        """Readiness check endpoint."""
        try:
            health_info = self.health_service.get_health_info()
            
            # For readiness, we check if the service is ready to accept requests
            if health_info["status"] in ["healthy", "degraded"]:
                return web.json_response({"status": "ready"}, status=200)
            else:
                return web.json_response({"status": "not_ready"}, status=503)
                
        except Exception as e:
            self.logger.error("Readiness check failed", error=str(e))
            return web.json_response({"status": "not_ready"}, status=503)
    
    async def _live_check(self, request):
        """Liveness check endpoint."""
        try:
            health_info = self.health_service.get_health_info()
            
            # For liveness, we just check if the service is running
            if health_info["status"] != "stopped":
                return web.json_response({"status": "alive"}, status=200)
            else:
                return web.json_response({"status": "dead"}, status=503)
                
        except Exception as e:
            self.logger.error("Liveness check failed", error=str(e))
            return web.json_response({"status": "dead"}, status=503)
    
    async def _metrics(self, request):
        """Metrics endpoint."""
        try:
            health_info = self.health_service.get_health_info()
            
            # Format metrics in a simple JSON structure
            metrics = {
                "uptime_seconds": health_info["uptime_seconds"],
                "status": health_info["status"],
                "metrics": health_info["metrics"],
                "timestamp": health_info["timestamp"]
            }
            
            return web.json_response(metrics)
            
        except Exception as e:
            self.logger.error("Metrics endpoint failed", error=str(e))
            return web.json_response({"error": "Failed to get metrics"}, status=500)
    
    async def _root(self, request):
        """Root endpoint with basic info."""
        return web.json_response({
            "service": "agentic-framework-health",
            "version": "0.1.0",
            "endpoints": {
                "health": "/health",
                "ready": "/health/ready", 
                "live": "/health/live",
                "metrics": "/metrics"
            }
        })
    
    async def start(self):
        """Start the HTTP health server."""
        runner = web.AppRunner(self.app)
        await runner.setup()
        
        site = web.TCPSite(runner, '0.0.0.0', self.port)
        await site.start()
        
        self.logger.info("HTTP health server started", port=self.port)
        
        # Keep running until shutdown is requested
        while not self._shutdown_event.is_set():
            await asyncio.sleep(1)
        
        # Graceful shutdown
        self.logger.info("Shutting down HTTP health server")
        await runner.cleanup()
    
    def run(self):
        """Run the HTTP health server."""
        asyncio.run(self.start())


def start_health_server(health_service, port: int = 8080, logger: Optional[FilteringBoundLogger] = None):
    """
    Start the HTTP health server in a separate thread.
    
    Args:
        health_service: Health check service instance
        port: Port to bind the HTTP server to
        logger: Optional logger instance
    """
    server = HTTPHealthServer(health_service, port, logger)
    
    # Run in a separate thread
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    
    return server 