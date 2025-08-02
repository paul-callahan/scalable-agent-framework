"""
Task and plan registry for executor microservice.

This module implements task and plan registry for dynamic class loading.
Includes functionality to register Task and Plan subclasses, load classes
dynamically from module paths, and validate that classes implement the
correct interfaces.
"""

import importlib
import inspect
from typing import Any, Dict, Optional, Type

from structlog import get_logger

from agentic.core.task import Task
from agentic.core.plan import Plan

logger = get_logger(__name__)


class TaskRegistry:
    """
    Registry for Task classes.
    
    Maps task_type strings to concrete Task classes and provides
    functionality to register and load Task subclasses dynamically.
    """
    
    def __init__(self):
        """Initialize the task registry."""
        self._tasks: Dict[str, Type[Task]] = {}
        self._task_modules: Dict[str, str] = {}
    
    def register_task(self, task_type: str, task_class: Type[Task]) -> None:
        """
        Register a Task class.
        
        Args:
            task_type: Unique identifier for the task type
            task_class: Task class to register
        """
        if not inspect.isclass(task_class):
            raise ValueError(f"task_class must be a class, got {type(task_class)}")
        
        if not issubclass(task_class, Task):
            raise ValueError(f"task_class must inherit from Task, got {task_class}")
        
        self._tasks[task_type] = task_class
        logger.info("Task registered", task_type=task_type, class_name=task_class.__name__)
    
    def register_task_from_module(self, task_type: str, module_path: str, class_name: str) -> None:
        """
        Register a Task class from a module path.
        
        Args:
            task_type: Unique identifier for the task type
            module_path: Python module path (e.g., "myapp.tasks")
            class_name: Name of the Task class in the module
        """
        try:
            module = importlib.import_module(module_path)
            task_class = getattr(module, class_name)
            self.register_task(task_type, task_class)
            self._task_modules[task_type] = f"{module_path}.{class_name}"
            
        except ImportError as e:
            logger.error("Failed to import task module", 
                        task_type=task_type,
                        module_path=module_path,
                        error=str(e))
            raise
        except AttributeError as e:
            logger.error("Failed to find task class in module", 
                        task_type=task_type,
                        module_path=module_path,
                        class_name=class_name,
                        error=str(e))
            raise
    
    def get_task_class(self, task_type: str) -> Optional[Type[Task]]:
        """
        Get a Task class by type.
        
        Args:
            task_type: Task type identifier
            
        Returns:
            Task class or None if not found
        """
        return self._tasks.get(task_type)
    
    def create_task(self, task_type: str, **kwargs) -> Optional[Task]:
        """
        Create a Task instance by type.
        
        Args:
            task_type: Task type identifier
            **kwargs: Arguments to pass to task constructor
            
        Returns:
            Task instance or None if not found
        """
        task_class = self.get_task_class(task_type)
        if task_class:
            try:
                return task_class(**kwargs)
            except Exception as e:
                logger.error("Failed to create task instance", 
                            task_type=task_type,
                            error=str(e))
                return None
        return None
    
    def list_task_types(self) -> list[str]:
        """
        List all registered task types.
        
        Returns:
            List of task type identifiers
        """
        return list(self._tasks.keys())
    
    def is_task_registered(self, task_type: str) -> bool:
        """
        Check if a task type is registered.
        
        Args:
            task_type: Task type identifier
            
        Returns:
            True if task type is registered
        """
        return task_type in self._tasks
    
    def get_registry_info(self) -> Dict[str, Any]:
        """
        Get registry information.
        
        Returns:
            Dictionary with registry information
        """
        return {
            "task_types": list(self._tasks.keys()),
            "task_modules": self._task_modules.copy(),
            "total_tasks": len(self._tasks),
        }


class PlanRegistry:
    """
    Registry for Plan classes.
    
    Maps plan_type strings to concrete Plan classes and provides
    functionality to register and load Plan subclasses dynamically.
    """
    
    def __init__(self):
        """Initialize the plan registry."""
        self._plans: Dict[str, Type[Plan]] = {}
        self._plan_modules: Dict[str, str] = {}
    
    def register_plan(self, plan_type: str, plan_class: Type[Plan]) -> None:
        """
        Register a Plan class.
        
        Args:
            plan_type: Unique identifier for the plan type
            plan_class: Plan class to register
        """
        if not inspect.isclass(plan_class):
            raise ValueError(f"plan_class must be a class, got {type(plan_class)}")
        
        if not issubclass(plan_class, Plan):
            raise ValueError(f"plan_class must inherit from Plan, got {plan_class}")
        
        self._plans[plan_type] = plan_class
        logger.info("Plan registered", plan_type=plan_type, class_name=plan_class.__name__)
    
    def register_plan_from_module(self, plan_type: str, module_path: str, class_name: str) -> None:
        """
        Register a Plan class from a module path.
        
        Args:
            plan_type: Unique identifier for the plan type
            module_path: Python module path (e.g., "myapp.plans")
            class_name: Name of the Plan class in the module
        """
        try:
            module = importlib.import_module(module_path)
            plan_class = getattr(module, class_name)
            self.register_plan(plan_type, plan_class)
            self._plan_modules[plan_type] = f"{module_path}.{class_name}"
            
        except ImportError as e:
            logger.error("Failed to import plan module", 
                        plan_type=plan_type,
                        module_path=module_path,
                        error=str(e))
            raise
        except AttributeError as e:
            logger.error("Failed to find plan class in module", 
                        plan_type=plan_type,
                        module_path=module_path,
                        class_name=class_name,
                        error=str(e))
            raise
    
    def get_plan_class(self, plan_type: str) -> Optional[Type[Plan]]:
        """
        Get a Plan class by type.
        
        Args:
            plan_type: Plan type identifier
            
        Returns:
            Plan class or None if not found
        """
        return self._plans.get(plan_type)
    
    def create_plan(self, plan_type: str, **kwargs) -> Optional[Plan]:
        """
        Create a Plan instance by type.
        
        Args:
            plan_type: Plan type identifier
            **kwargs: Arguments to pass to plan constructor
            
        Returns:
            Plan instance or None if not found
        """
        plan_class = self.get_plan_class(plan_type)
        if plan_class:
            try:
                return plan_class(**kwargs)
            except Exception as e:
                logger.error("Failed to create plan instance", 
                            plan_type=plan_type,
                            error=str(e))
                return None
        return None
    
    def list_plan_types(self) -> list[str]:
        """
        List all registered plan types.
        
        Returns:
            List of plan type identifiers
        """
        return list(self._plans.keys())
    
    def is_plan_registered(self, plan_type: str) -> bool:
        """
        Check if a plan type is registered.
        
        Args:
            plan_type: Plan type identifier
            
        Returns:
            True if plan type is registered
        """
        return plan_type in self._plans
    
    def get_registry_info(self) -> Dict[str, Any]:
        """
        Get registry information.
        
        Returns:
            Dictionary with registry information
        """
        return {
            "plan_types": list(self._plans.keys()),
            "plan_modules": self._plan_modules.copy(),
            "total_plans": len(self._plans),
        }


class RegistryManager:
    """
    Manager for both task and plan registries.
    
    Provides a unified interface for managing both task and plan registries.
    """
    
    def __init__(self):
        """Initialize the registry manager."""
        self.task_registry = TaskRegistry()
        self.plan_registry = PlanRegistry()
    
    def register_task(self, task_type: str, task_class: Type[Task]) -> None:
        """Register a task class."""
        self.task_registry.register_task(task_type, task_class)
    
    def register_plan(self, plan_type: str, plan_class: Type[Plan]) -> None:
        """Register a plan class."""
        self.plan_registry.register_plan(plan_type, plan_class)
    
    def register_task_from_module(self, task_type: str, module_path: str, class_name: str) -> None:
        """Register a task class from module."""
        self.task_registry.register_task_from_module(task_type, module_path, class_name)
    
    def register_plan_from_module(self, plan_type: str, module_path: str, class_name: str) -> None:
        """Register a plan class from module."""
        self.plan_registry.register_plan_from_module(plan_type, module_path, class_name)
    
    def get_task_class(self, task_type: str) -> Optional[Type[Task]]:
        """Get a task class."""
        return self.task_registry.get_task_class(task_type)
    
    def get_plan_class(self, plan_type: str) -> Optional[Type[Plan]]:
        """Get a plan class."""
        return self.plan_registry.get_plan_class(plan_type)
    
    def create_task(self, task_type: str, **kwargs) -> Optional[Task]:
        """Create a task instance."""
        return self.task_registry.create_task(task_type, **kwargs)
    
    def create_plan(self, plan_type: str, **kwargs) -> Optional[Plan]:
        """Create a plan instance."""
        return self.plan_registry.create_plan(plan_type, **kwargs)
    
    def get_registry_info(self) -> Dict[str, Any]:
        """
        Get combined registry information.
        
        Returns:
            Dictionary with combined registry information
        """
        return {
            "tasks": self.task_registry.get_registry_info(),
            "plans": self.plan_registry.get_registry_info(),
        } 