"""
Control plane microservice for agentic framework.

This service consumes execution references from the data plane, evaluates
guardrails, and routes approved executions to appropriate executor topics
based on the next tasks/plans to execute.
"""

from .service import ControlPlaneService
from .guardrails import GuardrailEngine
from .router import ExecutionRouter

__all__ = ["ControlPlaneService", "GuardrailEngine", "ExecutionRouter"]

__version__ = "0.1.0" 