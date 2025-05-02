from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod


class StateStore(ABC):
    """Abstract base class for append-only persistence of execution records"""
    
    @abstractmethod
    def store_task_execution(self, tenant_id: str, execution_data: Dict[str, Any]) -> str:
        """Store a task execution record"""
        pass
    
    @abstractmethod
    def store_plan_execution(self, tenant_id: str, execution_data: Dict[str, Any]) -> str:
        """Store a plan execution record"""
        pass
    
    @abstractmethod
    def get_task_execution(self, tenant_id: str, execution_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a task execution record"""
        pass
    
    @abstractmethod
    def get_plan_execution(self, tenant_id: str, execution_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a plan execution record"""
        pass
    
    @abstractmethod
    def list_executions_for_lifetime(self, tenant_id: str, lifetime_id: str) -> List[Dict[str, Any]]:
        """List all executions for a specific lifetime"""
        pass


class InMemoryStateStore(StateStore):
    """In-memory implementation of StateStore for testing"""
    
    def __init__(self):
        """Initialize in-memory storage"""
        self.task_executions: Dict[str, Dict[str, Any]] = {}
        self.plan_executions: Dict[str, Dict[str, Any]] = {}
    
    def store_task_execution(self, tenant_id: str, execution_data: Dict[str, Any]) -> str:
        """Store a task execution record"""
        execution_id = execution_data.get("execution_id")
        if not execution_id:
            raise ValueError("execution_id is required")
        
        key = f"{tenant_id}:{execution_id}"
        self.task_executions[key] = execution_data
        return execution_id
    
    def store_plan_execution(self, tenant_id: str, execution_data: Dict[str, Any]) -> str:
        """Store a plan execution record"""
        execution_id = execution_data.get("execution_id")
        if not execution_id:
            raise ValueError("execution_id is required")
        
        key = f"{tenant_id}:{execution_id}"
        self.plan_executions[key] = execution_data
        return execution_id
    
    def get_task_execution(self, tenant_id: str, execution_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a task execution record"""
        key = f"{tenant_id}:{execution_id}"
        return self.task_executions.get(key)
    
    def get_plan_execution(self, tenant_id: str, execution_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a plan execution record"""
        key = f"{tenant_id}:{execution_id}"
        return self.plan_executions.get(key)
    
    def list_executions_for_lifetime(self, tenant_id: str, lifetime_id: str) -> List[Dict[str, Any]]:
        """List all executions for a specific lifetime"""
        # Implementation would filter by lifetime_id
        # For MVP, return all executions for tenant
        return list(self.task_executions.values()) + list(self.plan_executions.values()) 