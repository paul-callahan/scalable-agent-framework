"""
In-memory message broker implementation.

This module provides an in-memory message broker that replaces Kafka
functionality using asyncio.Queue objects while preserving protobuf serialization.
"""

import asyncio
import fnmatch
import logging
from typing import AsyncIterator, Dict, Set

from ..core.logging import get_logger


class InMemoryBroker:
    """
    In-memory message broker using asyncio.Queue objects.
    
    Provides topic-based message routing with support for wildcard subscriptions
    and protobuf serialization boundaries.
    """
    
    def __init__(self):
        """Initialize the broker with empty topic queues."""
        self._queues: Dict[str, asyncio.Queue] = {}
        self._subscribers: Dict[str, Set[asyncio.Queue]] = {}
        self.logger = get_logger(__name__)
        
        # Metrics
        self._messages_published = 0
        self._messages_delivered = 0
        self._errors = 0
    
    def get_queue(self, topic: str) -> asyncio.Queue:
        """
        Get or create a queue for the specified topic.
        
        Args:
            topic: Topic name
            
        Returns:
            asyncio.Queue for the topic
        """
        if topic not in self._queues:
            self._queues[topic] = asyncio.Queue()
            self.logger.debug(f"Created queue for topic: {topic}")
        
        return self._queues[topic]
    
    async def publish(self, topic: str, message_bytes: bytes) -> None:
        """
        Publish a serialized message to a topic.
        
        Args:
            topic: Topic name
            message_bytes: Serialized protobuf message bytes
        """
        try:
            queue = self.get_queue(topic)
            await queue.put(message_bytes)
            self._messages_published += 1
            
            # Handle wildcard subscriptions
            await self._publish_to_wildcards(topic, message_bytes)
            
            self.logger.debug(f"Published message to topic {topic}, size: {len(message_bytes)} bytes")
            
        except Exception as e:
            self._errors += 1
            self.logger.error(f"Error publishing to topic {topic}: {e}")
            raise
    
    async def _publish_to_wildcards(self, topic: str, message_bytes: bytes) -> None:
        """
        Publish message to all matching wildcard subscribers.
        
        Args:
            topic: Original topic name
            message_bytes: Serialized message bytes
        """
        for pattern, subscribers in self._subscribers.items():
            if fnmatch.fnmatch(topic, pattern):
                for subscriber_queue in subscribers:
                    try:
                        await subscriber_queue.put(message_bytes)
                        self._messages_delivered += 1
                    except Exception as e:
                        self._errors += 1
                        self.logger.error(f"Error delivering to wildcard subscriber {pattern}: {e}")
    
    async def subscribe(self, topic: str) -> AsyncIterator[bytes]:
        """
        Subscribe to messages from a topic.
        
        Args:
            topic: Topic name (supports wildcards like 'task-control_*')
            
        Yields:
            Serialized protobuf message bytes
        """
        queue = self.get_queue(topic)
        
        # Handle wildcard subscriptions
        if '*' in topic or '?' in topic:
            if topic not in self._subscribers:
                self._subscribers[topic] = set()
            self._subscribers[topic].add(queue)
            self.logger.debug(f"Added wildcard subscriber for pattern: {topic}")
        
        self.logger.debug(f"Subscribed to topic: {topic}")
        
        try:
            while True:
                message_bytes = await queue.get()
                self._messages_delivered += 1
                self.logger.debug(f"Delivered message from topic {topic}, size: {len(message_bytes)} bytes")
                yield message_bytes
        except asyncio.CancelledError:
            self.logger.debug(f"Subscription cancelled for topic: {topic}")
            raise
        except Exception as e:
            self._errors += 1
            self.logger.error(f"Error in subscription for topic {topic}: {e}")
            raise
    
    def get_metrics(self) -> Dict[str, int]:
        """
        Get broker metrics.
        
        Returns:
            Dictionary of metric names and values
        """
        return {
            "messages_published": self._messages_published,
            "messages_delivered": self._messages_delivered,
            "errors": self._errors,
            "active_topics": len(self._queues),
            "wildcard_subscribers": len(self._subscribers)
        }
    
    async def shutdown(self) -> None:
        """Gracefully shutdown the broker."""
        self.logger.info("Shutting down in-memory broker")
        
        # Clear all queues
        for topic, queue in self._queues.items():
            while not queue.empty():
                try:
                    queue.get_nowait()
                except asyncio.QueueEmpty:
                    break
        
        self._queues.clear()
        self._subscribers.clear()
        
        self.logger.info("In-memory broker shutdown complete") 