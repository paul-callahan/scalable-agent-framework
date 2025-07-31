"""
Control plane service package for the agentic framework.

This package contains the control plane service implementation that handles
orchestration and routing of execution envelopes.
"""

from .server import ControlPlaneService

__all__ = ["ControlPlaneService"] 