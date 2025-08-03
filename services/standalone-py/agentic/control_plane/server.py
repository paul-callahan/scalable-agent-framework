"""
Control plane service module.

This module provides the ControlPlaneService using in-memory message broker
for orchestration and routing of execution envelopes. This is a service module
for use by the main standalone runner, not a standalone application.
"""

import asyncio
from typing import Optional

from ..core.logging import configure_logging, get_logger
from ..message_bus import InMemoryBroker
from .service import ControlPlaneService


async def serve(port: int = 8082, log_level: str = "INFO", tenant_id: str = "default",
                broker: Optional[InMemoryBroker] = None) -> ControlPlaneService:
    """
    Create and start the control plane service.
    
    Args:
        port: Port for the health check server (unused in standalone mode)
        log_level: Logging level
        tenant_id: Tenant identifier
        broker: Shared in-memory broker (required for standalone mode)
        
    Returns:
        Started ControlPlaneService instance
    """
    # Configure logging
    configure_logging(log_level=log_level)
    logger = get_logger(__name__)
    
    # Use provided broker or create new one for testing
    if broker is None:
        broker = InMemoryBroker()
    
    # Create control plane service
    control_plane_service = ControlPlaneService(
        broker=broker
    )
    
    # Add some default guardrails for demonstration
    control_plane_service.add_guardrail(tenant_id, {
        'type': 'rate_limit',
        'enabled': True,
        'blocking': True,
        'max_requests': 100,
        'window_seconds': 60
    })
    
    control_plane_service.add_guardrail(tenant_id, {
        'type': 'content_filter',
        'enabled': True,
        'blocking': True,
        'blocked_keywords': ['malicious', 'harmful']
    })
    
    # Start the control plane service
    await control_plane_service.start(tenant_id=tenant_id)
    
    logger.info(f"Control plane service started successfully")
    
    return control_plane_service 