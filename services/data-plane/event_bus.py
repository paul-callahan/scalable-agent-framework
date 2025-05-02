from dataclasses import dataclass
from typing import Dict, Any, List, Callable
from abc import ABC, abstractmethod
import asyncio


class EventBus(ABC):
    """Abstract base class for publishing execution events to Control Plane"""
    
    @abstractmethod
    async def publish_task_execution(self, tenant_id: str, execution_data: Dict[str, Any]) -> None:
        """Publish a task execution event"""
        pass
    
    @abstractmethod
    async def publish_plan_execution(self, tenant_id: str, execution_data: Dict[str, Any]) -> None:
        """Publish a plan execution event"""
        pass
    
    @abstractmethod
    async def publish_reference(self, tenant_id: str, reference_data: Dict[str, Any]) -> None:
        """Publish a lightweight reference message"""
        pass


class InMemoryEventBus(EventBus):
    """In-memory implementation of EventBus for testing"""
    
    def __init__(self):
        """Initialize in-memory event bus"""
        self.task_execution_subscribers: List[Callable] = []
        self.plan_execution_subscribers: List[Callable] = []
        self.reference_subscribers: List[Callable] = []
    
    async def publish_task_execution(self, tenant_id: str, execution_data: Dict[str, Any]) -> None:
        """Publish a task execution event"""
        event = {
            "type": "task_execution",
            "tenant_id": tenant_id,
            "data": execution_data
        }
        
        # Notify all subscribers
        for subscriber in self.task_execution_subscribers:
            await subscriber(event)
    
    async def publish_plan_execution(self, tenant_id: str, execution_data: Dict[str, Any]) -> None:
        """Publish a plan execution event"""
        event = {
            "type": "plan_execution",
            "tenant_id": tenant_id,
            "data": execution_data
        }
        
        # Notify all subscribers
        for subscriber in self.plan_execution_subscribers:
            await subscriber(event)
    
    async def publish_reference(self, tenant_id: str, reference_data: Dict[str, Any]) -> None:
        """Publish a lightweight reference message"""
        event = {
            "type": "reference",
            "tenant_id": tenant_id,
            "data": reference_data
        }
        
        # Notify all subscribers
        for subscriber in self.reference_subscribers:
            await subscriber(event)
    
    def subscribe_to_task_executions(self, callback: Callable) -> None:
        """Subscribe to task execution events"""
        self.task_execution_subscribers.append(callback)
    
    def subscribe_to_plan_executions(self, callback: Callable) -> None:
        """Subscribe to plan execution events"""
        self.plan_execution_subscribers.append(callback)
    
    def subscribe_to_references(self, callback: Callable) -> None:
        """Subscribe to reference events"""
        self.reference_subscribers.append(callback) 