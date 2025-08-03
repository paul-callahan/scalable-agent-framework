"""
Data plane service module.

This module provides the DataPlaneService using in-memory message broker
for persistence of execution records to storage. This is a service module
for use by the main standalone runner, not a standalone application.
"""

import asyncio
from typing import Optional

from ..core.logging import configure_logging, get_logger
from ..message_bus import InMemoryBroker
from .service import DataPlaneService


async def serve(port: int = 8081, log_level: str = "INFO", db_path: str = "agentic_data.db", 
                tenant_id: str = "default", broker: Optional[InMemoryBroker] = None) -> DataPlaneService:
    """
    Create and start the data plane service.
    
    Args:
        port: Port for the health check server (unused in standalone mode)
        log_level: Logging level
        db_path: Path to the SQLite database file
        tenant_id: Tenant identifier
        broker: Shared in-memory broker (required for standalone mode)
        
    Returns:
        Started DataPlaneService instance
    """
    # Configure logging
    configure_logging(log_level=log_level)
    logger = get_logger(__name__)
    
    # Use provided broker or create new one for testing
    if broker is None:
        broker = InMemoryBroker()
    
    # Create data plane service
    data_plane_service = DataPlaneService(
        broker=broker,
        db_path=db_path
    )
    
    # Start the data plane service
    await data_plane_service.start(tenant_id=tenant_id)
    
    logger.info(f"Data plane service started successfully")
    
    return data_plane_service 