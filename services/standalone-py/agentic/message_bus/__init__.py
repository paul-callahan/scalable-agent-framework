"""
Message bus package for in-memory message routing.

This package provides an in-memory message broker that replaces Kafka
functionality using asyncio.Queue objects while preserving protobuf serialization.
"""

from .broker import InMemoryBroker

__all__ = ["InMemoryBroker"] 