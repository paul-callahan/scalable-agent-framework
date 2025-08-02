"""
Data plane microservice for agentic framework.

This service consumes TaskExecution and PlanExecution messages from Kafka,
persists them to Postgres using SQLAlchemy, and republishes lightweight
references to the control plane topics.
"""

from .service import DataPlaneService

__all__ = ["DataPlaneService"]

__version__ = "0.1.0" 