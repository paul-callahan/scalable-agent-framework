"""
Main entry point for data plane microservice.

This module provides the main entry point for the data plane service that
loads configuration from environment variables, initializes logging, creates
database connections, starts Kafka consumers/producers, and runs the FastAPI
server using uvicorn==0.30.1.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from agentic_common.logging_config import setup_logging
from data_plane.service import DataPlaneService


async def main():
    """Main entry point for the data plane service."""
    # Setup logging
    setup_logging()
    
    # Get configuration from environment variables
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    
    # Database configuration
    os.environ.setdefault("DB_HOST", "localhost")
    os.environ.setdefault("DB_PORT", "5432")
    os.environ.setdefault("DB_NAME", "agentic")
    os.environ.setdefault("DB_USER", "agentic")
    os.environ.setdefault("DB_PASSWORD", "agentic")
    
    # Kafka configuration
    os.environ.setdefault("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    os.environ.setdefault("KAFKA_CLIENT_ID", "data-plane")
    os.environ.setdefault("KAFKA_GROUP_ID", "data-plane-group")
    
    # Logging configuration
    os.environ.setdefault("LOG_LEVEL", "INFO")
    os.environ.setdefault("LOG_FORMAT", "json")
    
    # Create and run service
    service = DataPlaneService(host=host, port=port)
    
    try:
        await service.start()
        await service.run()
        
    except KeyboardInterrupt:
        print("Received keyboard interrupt, shutting down...")
        
    except Exception as e:
        print(f"Service error: {e}")
        sys.exit(1)
        
    finally:
        await service.stop()


if __name__ == "__main__":
    asyncio.run(main()) 