"""
Data plane service package for the agentic framework.

This package contains the data plane service implementation that handles
persistence of execution records.
"""

from .server import DataPlaneService

__all__ = ["DataPlaneService"] 